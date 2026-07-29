#!/usr/bin/env python3
"""Smoke-test the review-intake extensions in the committed schema_v2.sql.

The doc-02 DDL is folded into schema_v2.sql; 02-review-extensions.sql remains
the annotated rationale. Superseded by tests/test_review_extensions.py — kept
as the proposal-side artifact.
"""

import pathlib
import sqlite3
import sys

_HERE = pathlib.Path(__file__).resolve()
SCHEMA = (_HERE.parents[4] / "legesher_i18n" / "db" / "schema_v2.sql").read_text()

print("sqlite runtime:", sqlite3.sqlite_version)
db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys = ON")

results = []


def check(name, fn, expect_fail=None):
    """expect_fail: None = must succeed; str = must raise containing str."""
    try:
        fn()
        ok = expect_fail is None
        detail = (
            ""
            if ok
            else f"UNEXPECTED SUCCESS (wanted failure containing {expect_fail!r})"
        )
    except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
        if expect_fail is not None and expect_fail in str(e):
            ok, detail = True, ""
        else:
            ok, detail = False, f"raised: {e}"
    results.append((ok, name, detail))


# ---- 0. DDL loads ----------------------------------------------------------
check(
    "schema_v2.sql loads (review extensions folded in)",
    lambda: db.executescript(SCHEMA),
)
check(
    "review-intake tables present",
    lambda: db.execute(
        "SELECT 1 FROM review_sessions, session_rankings, option_annotations LIMIT 0"
    ),
)
db.execute("PRAGMA foreign_keys = ON")  # executescript resets/commits; re-assert

# ---- 1. seeds --------------------------------------------------------------
H16a, H16b, H16c = "a" * 16, "b" * 16, "c" * 16
OPT1, OPT2, OPT3 = "opt_" + "1" * 24, "opt_" + "2" * 24, "opt_" + "3" * 24
SES1, SES2 = "ses_" + "1" * 24, "ses_" + "2" * 24


def dig_for(ses):
    """bundle_digest consistent with the uid = 'ses_' || digest[:24] CHECK."""
    return ses[4:] + "e" * 40


def seed():
    db.executescript(f"""
    INSERT INTO programming_languages(code, name, status) VALUES ('python','Python','shipping');
    INSERT INTO locales(tag, language_subtag, name, native_name, direction, in_registry)
        VALUES ('ur','ur','Urdu','اردو','rtl',1);
    INSERT INTO concepts(slug, definition_en, category) VALUES
        ('elif-compound','otherwise-if in a conditional chain','control_flow'),
        ('break-loop','exit the nearest loop','control_flow');
    INSERT INTO terms(concept_id, programming_language, name, category)
        VALUES (1,'python','elif','keyword'), (2,'python','break','keyword');
    INSERT INTO contributors(id, current_rung) VALUES
        ('c_{H16a}','native_verified'), ('c_{H16b}','native_verified'), ('c_{H16c}','contributor');
    INSERT INTO options(uid, concept_id, locale, programming_language, surface_form) VALUES
        ('{OPT1}', 1, 'ur', NULL, 'ورنہ_اگر'),
        ('{OPT2}', 1, 'ur', NULL, 'وگرنہ'),
        ('{OPT3}', 2, 'ur', NULL, 'توڑو');
    INSERT INTO option_validations(option_uid, validator_version, identifier_valid,
        nfkc_stable, script_consistent) VALUES
        ('{OPT1}','audit-v1',1,1,1), ('{OPT2}','audit-v1',1,1,1), ('{OPT3}','audit-v1',1,1,1);
    INSERT INTO endorsements(uid, option_uid, contributor_id, method, rung_at_endorsement) VALUES
        ('end_{"1" * 24}','{OPT1}','c_{H16a}','portal','native_verified'),
        ('end_{"2" * 24}','{OPT2}','c_{H16a}','portal','native_verified'),
        ('end_{"3" * 24}','{OPT1}','c_{H16b}','portal','native_verified');
    INSERT INTO review_sessions(uid, contributor_id, locale, track, method, kit_version,
        rung_at_session, bundle_digest) VALUES
        ('{SES1}','c_{H16a}','ur','reserved_words','portal','kit-1','native_verified','{dig_for(SES1)}'),
        ('{SES2}','c_{H16a}','ur','reserved_words','portal','kit-1','native_verified','{dig_for(SES2)}');
    """)


check("seed data inserts", seed)

# ---- 2. endorsement invariants (committed, sanity) -------------------------
check(
    "double endorsement blocked",
    lambda: db.execute(
        f"INSERT INTO endorsements(uid, option_uid, contributor_id, method, rung_at_endorsement) VALUES ('end_{'4' * 24}','{OPT1}','c_{H16a}','portal','native_verified')"
    ),
    expect_fail="UNIQUE",
)

# ---- 3. ranking invariants -------------------------------------------------
check(
    "ranking of endorsed option inserts",
    lambda: db.execute(
        f"INSERT INTO session_rankings(session_uid, concept_id, locale, programming_language, option_uid, rank) VALUES ('{SES1}',1,'ur',NULL,'{OPT1}',1)"
    ),
)
check(
    "non-endorser session inserts",
    lambda: db.execute(f"""INSERT INTO review_sessions(uid, contributor_id, locale, track, method, kit_version, rung_at_session, bundle_digest)
                             VALUES ('ses_{"3" * 24}','c_{H16c}','ur','reserved_words','portal','kit-1','contributor','{dig_for("ses_" + "3" * 24)}')"""),
)
check(
    "ranking without endorsement blocked",
    lambda: db.execute(
        f"INSERT INTO session_rankings(session_uid, concept_id, locale, programming_language, option_uid, rank) VALUES ('ses_{'3' * 24}',1,'ur',NULL,'{OPT1}',1)"
    ),
    expect_fail="rank only options",
)
check(
    "rank slot collision blocked (rank 1 reused in same session/concept)",
    lambda: db.execute(
        f"INSERT INTO session_rankings(session_uid, concept_id, locale, programming_language, option_uid, rank) VALUES ('{SES1}',1,'ur',NULL,'{OPT2}',1)"
    ),
    expect_fail="UNIQUE",
)
check(
    "second rank slot inserts",
    lambda: db.execute(
        f"INSERT INTO session_rankings(session_uid, concept_id, locale, programming_language, option_uid, rank) VALUES ('{SES1}',1,'ur',NULL,'{OPT2}',2)"
    ),
)
check(
    "mis-keyed ranking blocked (OPT3 renders break, not elif)",
    lambda: db.execute(
        f"INSERT INTO session_rankings(session_uid, concept_id, locale, programming_language, option_uid, rank) VALUES ('{SES1}',2,'ur',NULL,'{OPT1}',1)"
    ),
    expect_fail="does not render",
)
check(
    "ranking UPDATE blocked (append-only)",
    lambda: db.execute(
        f"UPDATE session_rankings SET rank = 3 WHERE session_uid='{SES1}' AND option_uid='{OPT1}'"
    ),
    expect_fail="append-only",
)
check(
    "ranking DELETE blocked",
    lambda: db.execute("DELETE FROM session_rankings"),
    expect_fail="append-only",
)

# ---- 4. session mutability -------------------------------------------------
check(
    "session status submitted->accepted allowed",
    lambda: db.execute(
        f"UPDATE review_sessions SET status='accepted', verification_report='{{}}' WHERE uid='{SES1}'"
    ),
)
check(
    "session accepted->submitted blocked (terminal)",
    lambda: db.execute(
        f"UPDATE review_sessions SET status='submitted' WHERE uid='{SES1}'"
    ),
    expect_fail="terminal",
)
check(
    "session evidence column frozen (locale)",
    lambda: db.execute(f"UPDATE review_sessions SET locale='ur' WHERE uid='{SES2}'"),
    expect_fail="append-only",
)
check(
    "session DELETE blocked",
    lambda: db.execute(f"DELETE FROM review_sessions WHERE uid='{SES2}'"),
    expect_fail="append-only",
)

# ---- 5. annotations --------------------------------------------------------
ANN1 = "ann_" + "1" * 24
check(
    "annotation inserts",
    lambda: db.execute(
        f"INSERT INTO option_annotations(uid, option_uid, contributor_id, session_uid, kind) VALUES ('{ANN1}','{OPT1}','c_{H16a}','{SES1}','coined_neologism')"
    ),
)
check(
    "duplicate live annotation blocked",
    lambda: db.execute(
        f"INSERT INTO option_annotations(uid, option_uid, contributor_id, kind) VALUES ('ann_{'2' * 24}','{OPT1}','c_{H16a}','coined_neologism')"
    ),
    expect_fail="UNIQUE",
)
check(
    "annotation retract allowed",
    lambda: db.execute(
        f"UPDATE option_annotations SET retracted_at = datetime('now') WHERE uid='{ANN1}'"
    ),
)
check(
    "annotation un-retract blocked",
    lambda: db.execute(
        f"UPDATE option_annotations SET retracted_at = NULL WHERE uid='{ANN1}'"
    ),
    expect_fail="cannot be reversed",
)
check(
    "re-annotation after retraction allowed (slot freed)",
    lambda: db.execute(
        f"INSERT INTO option_annotations(uid, option_uid, contributor_id, kind) VALUES ('ann_{'3' * 24}','{OPT1}','c_{H16a}','coined_neologism')"
    ),
)
check(
    "annotation kind frozen",
    lambda: db.execute(
        f"UPDATE option_annotations SET kind='regional' WHERE uid='{ANN1}'"
    ),
    expect_fail="append-only",
)

# ---- 6. identity deltas ----------------------------------------------------
check(
    "identity with valid email + name preference inserts",
    lambda: db.execute(
        f"INSERT INTO contributor_identities(contributor_id, source_key, display_name, email, credit_preference) VALUES ('c_{H16a}','gh:someone','مدیحہ خان','someone@example.org','name')"
    ),
)
check(
    "bad email (no @) blocked",
    lambda: db.execute(
        f"INSERT INTO contributor_identities(contributor_id, email) VALUES ('c_{H16b}','not-an-email')"
    ),
    expect_fail="CHECK",
)
check(
    "bad email (double @) blocked",
    lambda: db.execute(
        f"INSERT INTO contributor_identities(contributor_id, email) VALUES ('c_{H16b}','a@@b.co')"
    ),
    expect_fail="CHECK",
)
check(
    "bad credit_preference blocked",
    lambda: db.execute(
        f"INSERT INTO contributor_identities(contributor_id, credit_preference) VALUES ('c_{H16b}','public')"
    ),
    expect_fail="CHECK",
)
check(
    "anonymous default identity inserts",
    lambda: db.execute(
        f"INSERT INTO contributor_identities(contributor_id) VALUES ('c_{H16b}')"
    ),
)


# ---- 7. views --------------------------------------------------------------
def q(sql):
    return db.execute(sql).fetchall()


check(
    "option_promotion_status: OPT1 reviewed_eligible (2 native endorsers)",
    lambda: (_ for _ in ()).throw(
        sqlite3.OperationalError(
            "wrong: "
            + repr(
                q(
                    f"SELECT reviewed_eligible, canon_eligible, native_verified_or_above FROM option_promotion_status WHERE option_uid='{OPT1}'"
                )
            )
        )
    )
    if q(
        f"SELECT reviewed_eligible, canon_eligible FROM option_promotion_status WHERE option_uid='{OPT1}'"
    )
    != [(1, 1)]
    else None,
)
check(
    "option_promotion_status: OPT2 not eligible (1 endorser)",
    lambda: None
    if q(
        f"SELECT reviewed_eligible FROM option_promotion_status WHERE option_uid='{OPT2}'"
    )
    == [(0,)]
    else (_ for _ in ()).throw(sqlite3.OperationalError("wrong")),
)
check(
    "second_endorsement_queue contains OPT2",
    lambda: None
    if q("SELECT option_uid FROM second_endorsement_queue") == [(OPT2,)]
    else (_ for _ in ()).throw(
        sqlite3.OperationalError(
            "wrong: " + repr(q("SELECT option_uid FROM second_endorsement_queue"))
        )
    ),
)


# sara-am carve-out: OPT3 nfkc_stable=0 delta sara-am-only -> canon_eligible 1;
# then delta 'other' -> 0
def sara_am():
    db.execute(
        f"UPDATE option_validations SET nfkc_stable=0, nfkc_delta_class='sara-am-only' WHERE option_uid='{OPT3}'"
    )
    a = q(
        f"SELECT canon_eligible FROM option_promotion_status WHERE option_uid='{OPT3}'"
    )
    db.execute(
        f"UPDATE option_validations SET nfkc_delta_class='other' WHERE option_uid='{OPT3}'"
    )
    b = q(
        f"SELECT canon_eligible FROM option_promotion_status WHERE option_uid='{OPT3}'"
    )
    if (a, b) != ([(1,)], [(0,)]):
        raise sqlite3.OperationalError(f"sara-am logic wrong: {a} {b}")


check("canon_eligible honors sara-am-only carve-out, blocks 'other'", sara_am)


# latest_rankings: SES2 (same contributor) re-ranks OPT2 first; accepted; wins.
def latest():
    db.execute(
        f"INSERT INTO session_rankings(session_uid, concept_id, locale, programming_language, option_uid, rank) VALUES ('{SES2}',1,'ur',NULL,'{OPT2}',1)"
    )
    db.execute(f"UPDATE review_sessions SET status='accepted' WHERE uid='{SES2}'")
    rows = q(
        f"SELECT option_uid, rank FROM latest_rankings WHERE contributor_id='c_{H16a}' AND concept_id=1 ORDER BY rank"
    )
    if rows != [(OPT2, 1)]:
        raise sqlite3.OperationalError("latest_rankings wrong: " + repr(rows))


check("latest_rankings picks the most recent accepted session", latest)

check(
    "terminology_export runs + OPT1 row present",
    lambda: None
    if any(r[3] == "ورنہ_اگر" for r in q("SELECT * FROM terminology_export"))
    else (_ for _ in ()).throw(sqlite3.OperationalError("missing")),
)
check(
    "transliteration_preference runs",
    lambda: q("SELECT * FROM transliteration_preference"),
)
check(
    "pack_promotion_status runs (python x ur row)",
    lambda: None
    if q(
        "SELECT native_reviewers, total_reviewers FROM pack_promotion_status WHERE locale='ur' AND programming_language='python'"
    )
    == [(1, 1)]
    else (_ for _ in ()).throw(
        sqlite3.OperationalError(
            "wrong: " + repr(q("SELECT * FROM pack_promotion_status"))
        )
    ),
)

# ---- 8. junctions + expansions + commentary + style ------------------------
check(
    "session_options junction inserts + frozen",
    lambda: db.execute(
        f"INSERT INTO session_options(session_uid, option_uid, elicited) VALUES ('{SES1}','{OPT1}','blind')"
    ),
)
check(
    "session_options update blocked",
    lambda: db.execute("UPDATE session_options SET elicited='quick'"),
    expect_fail="append-only",
)
check(
    "expansion inserts",
    lambda: db.execute(
        f"INSERT INTO option_expansions(uid, option_uid, contributor_id, session_uid, expansion) VALUES ('exp_{'1' * 24}','{OPT1}','c_{H16a}','{SES1}','ورنہ اگر')"
    ),
)
check(
    "commentary inserts + moderation row",
    lambda: db.execute(
        f"INSERT INTO concept_commentary(uid, contributor_id, session_uid, concept_id, locale, topic, body) VALUES ('com_{'1' * 24}','c_{H16a}','{SES1}',1,'ur','word_formation','underscore joins read naturally')"
    )
    or db.execute(
        f"INSERT INTO commentary_moderation(commentary_uid, status) VALUES ('com_{'1' * 24}','published')"
    ),
)
check(
    "commentary body frozen",
    lambda: db.execute("UPDATE concept_commentary SET body='x'"),
    expect_fail="append-only",
)
check(
    "commentary moderation status mutable",
    lambda: db.execute("UPDATE commentary_moderation SET status='withheld'"),
)
check(
    "style ratification inserts + one-live-vote",
    lambda: db.execute(
        f"INSERT INTO style_ratifications(uid, contributor_id, session_uid, locale, field, value) VALUES ('sty_{'1' * 24}','c_{H16a}','{SES1}','ur','constants_strategy','marker_affix:ثابت_')"
    ),
)
check(
    "duplicate live style vote blocked",
    lambda: db.execute(
        f"INSERT INTO style_ratifications(uid, contributor_id, locale, field, value) VALUES ('sty_{'2' * 24}','c_{H16a}','ur','constants_strategy','positional')"
    ),
    expect_fail="UNIQUE",
)
check(
    "import_sources: redistributable without license blocked",
    lambda: db.execute(
        "INSERT INTO import_sources(id, kind, name, redistributable) VALUES ('initiative:hedy','initiative','Hedy',1)"
    ),
    expect_fail="CHECK",
)
check(
    "import_sources: reference-only row inserts",
    lambda: db.execute(
        "INSERT INTO import_sources(id, kind, name, license_spdx, redistributable) VALUES ('initiative:universalpython','initiative','UniversalPython','Apache-2.0',1)"
    ),
)
check(
    "session uid shape enforced",
    lambda: db.execute(
        f"INSERT INTO review_sessions(uid, contributor_id, locale, track, method, kit_version, rung_at_session, bundle_digest) VALUES ('ses_NOTHEX','c_{H16a}','ur','reserved_words','portal','k','contributor','{'d' * 64}')"
    ),
    expect_fail="CHECK",
)
check(
    "style session with PL blocked",
    lambda: db.execute(
        f"INSERT INTO review_sessions(uid, contributor_id, locale, track, programming_language, method, kit_version, rung_at_session, bundle_digest) VALUES ('ses_{'4' * 24}','c_{H16a}','ur','style_profile','python','portal','k','contributor','{dig_for('ses_' + '4' * 24)}')"
    ),
    expect_fail="CHECK",
)

# ---- report ---------------------------------------------------------------
fails = [r for r in results if not r[0]]
for ok, name, detail in results:
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else "  -> " + detail))
print(f"\n{len(results) - len(fails)}/{len(results)} passed")
sys.exit(1 if fails else 0)
