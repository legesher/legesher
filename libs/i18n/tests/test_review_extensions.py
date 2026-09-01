"""Validation suite for the review-intake extensions (CORE-1538).

Covers the intake layer folded into ``schema_v2.sql``: review sessions +
junctions, session rankings, option annotations, expansions, commentary +
moderation split, style ratifications, ``import_sources``, the identity
deltas (``credit_preference`` / ``email``), the intake views, and the
content-addressed uid helpers in ``schema_v2.py``.

Same doctrine as ``test_schema_v2.py``: every append-only rule is exercised
on UPDATE *and* DELETE (and ``INSERT OR REPLACE``, which without
``PRAGMA recursive_triggers`` slips past ``BEFORE DELETE`` triggers), and the
uid formulae are pinned with literal golden vectors — if a refactor changes a
digest, a test fails with the exact value that moved.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import (
    annotation_uid,
    apply_schema_v2,
    bundle_digest,
    commentary_uid,
    expansion_uid,
    session_uid,
    style_uid,
)

# Readable fixed ids (shapes satisfy the CHECKs; values are arbitrary hex).
C_A = "c_" + "a" * 16
C_B = "c_" + "b" * 16
C_C = "c_" + "c" * 16
OPT1 = "opt_" + "1" * 24  # elif candidate: ورنہ_اگر
OPT2 = "opt_" + "2" * 24  # elif candidate: وگرنہ
OPT3 = "opt_" + "3" * 24  # break candidate: توڑو
SES1 = "ses_" + "1" * 24
SES2 = "ses_" + "2" * 24
SES3 = "ses_" + "3" * 24


def dig_for(ses: str) -> str:
    """A bundle_digest consistent with the uid = 'ses_' || digest[:24] CHECK."""
    return ses[4:] + "e" * 40


@pytest.fixture()
def db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    apply_schema_v2(conn)
    yield conn
    conn.close()


@pytest.fixture()
def seeded(db: sqlite3.Connection) -> sqlite3.Connection:
    db.executescript(
        f"""
        INSERT INTO programming_languages(code, name, status)
            VALUES ('python','Python','shipping');
        INSERT INTO locales(tag, language_subtag, name, native_name, direction, in_registry)
            VALUES ('ur','ur','Urdu','اردو','rtl',1);
        INSERT INTO concepts(slug, definition_en, category) VALUES
            ('elif-compound','otherwise-if in a conditional chain','control_flow'),
            ('break-loop','exit the nearest loop','control_flow');
        INSERT INTO terms(concept_id, programming_language, name, category)
            VALUES (1,'python','elif','keyword'), (2,'python','break','keyword');
        INSERT INTO contributors(id, current_rung) VALUES
            ('{C_A}','native_verified'), ('{C_B}','native_verified'), ('{C_C}','contributor');
        INSERT INTO options(uid, concept_id, locale, programming_language, surface_form) VALUES
            ('{OPT1}', 1, 'ur', NULL, 'ورنہ_اگر'),
            ('{OPT2}', 1, 'ur', NULL, 'وگرنہ'),
            ('{OPT3}', 2, 'ur', NULL, 'توڑو');
        INSERT INTO option_validations(option_uid, validator_version, identifier_valid,
            nfkc_stable, script_consistent, format_chars_clean) VALUES
            ('{OPT1}','audit-v1',1,1,1,1), ('{OPT2}','audit-v1',1,1,1,1),
            ('{OPT3}','audit-v1',1,1,1,1);
        INSERT INTO endorsements(uid, option_uid, contributor_id, method, rung_at_endorsement) VALUES
            ('end_{"1" * 24}','{OPT1}','{C_A}','portal','native_verified'),
            ('end_{"2" * 24}','{OPT2}','{C_A}','portal','native_verified'),
            ('end_{"3" * 24}','{OPT1}','{C_B}','portal','native_verified');
        INSERT INTO review_sessions(uid, contributor_id, locale, track, method, kit_version,
            rung_at_session, bundle_digest) VALUES
            ('{SES1}','{C_A}','ur','reserved_words','portal','kit-1','native_verified','{dig_for(SES1)}'),
            ('{SES2}','{C_A}','ur','reserved_words','portal','kit-1','native_verified','{dig_for(SES2)}');
        """
    )
    return db


def one(db: sqlite3.Connection, sql: str) -> tuple:
    rows = db.execute(sql).fetchall()
    assert len(rows) == 1, f"expected one row, got {rows!r}"
    return rows[0]


# ---------------------------------------------------------------------------
# uid helpers — golden vectors (FROZEN once sessions are published)
# ---------------------------------------------------------------------------


def test_review_uid_golden_vectors() -> None:
    bundle = b'{"bundle":1}'
    assert bundle_digest(bundle) == (
        "7710c630a727d03b70a53a2c12394c034b50b5834151f9c7d751e439bed08b4c"
    )
    ses = session_uid(bundle)
    assert ses == "ses_7710c630a727d03b70a53a2c"
    # session uid and stored digest verify each other by construction
    assert ses == "ses_" + bundle_digest(bundle)[:24]
    assert annotation_uid(ses, OPT1, C_A, "transliteration") == (
        "ann_a403aeb6fd52c7ea34bfc21f"
    )
    assert expansion_uid(ses, OPT1, C_A, "ورنہ اگر") == "exp_fbb432c0d35dc9d740ef6d46"
    assert (
        commentary_uid(
            ses,
            C_A,
            "elif-compound",
            "ur",
            "word_formation",
            "underscore joins read naturally",
        )
        == "com_d5c73f9ea1d80266a22d6de8"
    )
    assert style_uid(ses, C_A, "ur", "constants_strategy") == (
        "sty_a35c0737a364973d7341cf46"
    )


def test_expansion_uid_is_nfc_stable() -> None:
    ses = session_uid(b"x")
    # Genuinely different byte sequences for the same text: U+0622 (alef with
    # madda) vs U+0627 U+0653 (alef + combining madda), which NFC composes.
    nfc = "آب"
    nfd = "آب"
    assert nfc != nfd
    assert expansion_uid(ses, OPT1, C_A, nfc) == expansion_uid(ses, OPT1, C_A, nfd)


def test_review_uids_reject_separator() -> None:
    ses = session_uid(b"x")
    with pytest.raises(ValueError):
        annotation_uid(ses, OPT1, C_A, "trans\x1fliteration")
    with pytest.raises(ValueError):
        style_uid(ses, C_A, "ur\x1f", "constants_strategy")
    # commentary body may contain anything — it is hashed before joining
    assert commentary_uid(ses, C_A, None, "ur", "general", "a\x1fb").startswith("com_")


# ---------------------------------------------------------------------------
# rankings
# ---------------------------------------------------------------------------


def rank(db: sqlite3.Connection, ses: str, concept: int, opt: str, rk: int) -> None:
    db.execute(
        "INSERT INTO session_rankings(session_uid, concept_id, locale,"
        " programming_language, option_uid, rank) VALUES (?, ?, 'ur', NULL, ?, ?)",
        (ses, concept, opt, rk),
    )


def test_ranking_requires_live_endorsement(seeded: sqlite3.Connection) -> None:
    rank(seeded, SES1, 1, OPT1, 1)  # C_A endorsed OPT1 — allowed
    seeded.execute(
        "INSERT INTO review_sessions(uid, contributor_id, locale, track, method,"
        " kit_version, rung_at_session, bundle_digest) VALUES"
        f" ('{SES3}','{C_C}','ur','reserved_words','portal','kit-1','contributor','{dig_for(SES3)}')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="rank only options"):
        rank(seeded, SES3, 1, OPT1, 1)  # C_C never endorsed anything


def test_ranking_slot_and_option_uniqueness(seeded: sqlite3.Connection) -> None:
    rank(seeded, SES1, 1, OPT1, 1)
    with pytest.raises(sqlite3.IntegrityError):  # rank 1 slot reused
        rank(seeded, SES1, 1, OPT2, 1)
    rank(seeded, SES1, 1, OPT2, 2)
    with pytest.raises(sqlite3.IntegrityError):  # same option ranked twice
        rank(seeded, SES1, 1, OPT2, 3)


def test_ranking_must_match_concept(seeded: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="does not render"):
        rank(seeded, SES1, 2, OPT1, 1)  # OPT1 renders elif, not break


def test_rankings_are_append_only(seeded: sqlite3.Connection) -> None:
    rank(seeded, SES1, 1, OPT1, 1)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("UPDATE session_rankings SET rank = 2")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM session_rankings")
    # INSERT OR REPLACE is an UPDATE wearing a trench coat: the implicit
    # DELETE must hit the BEFORE DELETE trigger (recursive_triggers is ON).
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute(
            "INSERT OR REPLACE INTO session_rankings(session_uid, concept_id,"
            " locale, programming_language, option_uid, rank)"
            f" VALUES ('{SES1}', 1, 'ur', NULL, '{OPT1}', 5)"
        )


def test_latest_rankings_supersession(seeded: sqlite3.Connection) -> None:
    rank(seeded, SES1, 1, OPT1, 1)
    rank(seeded, SES1, 1, OPT2, 2)
    rank(seeded, SES2, 1, OPT2, 1)  # later sitting, same contributor
    seeded.execute(
        "UPDATE review_sessions SET status='accepted' WHERE uid IN (?, ?)", (SES1, SES2)
    )
    rows = seeded.execute(
        f"SELECT option_uid, rank FROM latest_rankings"
        f" WHERE contributor_id='{C_A}' AND concept_id=1 ORDER BY rank"
    ).fetchall()
    assert rows == [(OPT2, 1)]  # only the latest accepted session counts


# ---------------------------------------------------------------------------
# sessions
# ---------------------------------------------------------------------------


def test_session_workflow_columns_mutable_evidence_frozen(
    seeded: sqlite3.Connection,
) -> None:
    seeded.execute(
        f"UPDATE review_sessions SET status='accepted', verification_report='{{}}' WHERE uid='{SES1}'"
    )
    with pytest.raises(sqlite3.IntegrityError, match="terminal"):
        seeded.execute(
            f"UPDATE review_sessions SET status='submitted' WHERE uid='{SES1}'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute(
            f"UPDATE review_sessions SET kit_version='kit-2' WHERE uid='{SES2}'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM review_sessions")


def test_session_shape_checks(seeded: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):  # uid must be ses_ + 24 hex
        seeded.execute(
            "INSERT INTO review_sessions(uid, contributor_id, locale, track, method,"
            f" kit_version, rung_at_session, bundle_digest) VALUES ('ses_NOTHEX','{C_A}',"
            f"'ur','reserved_words','portal','k','contributor','{'d' * 64}')"
        )
    with pytest.raises(sqlite3.IntegrityError):  # style sessions are locale-wide
        seeded.execute(
            "INSERT INTO review_sessions(uid, contributor_id, locale, track,"
            " programming_language, method, kit_version, rung_at_session, bundle_digest)"
            f" VALUES ('ses_{'4' * 24}','{C_A}','ur','style_profile','python','portal',"
            f"'k','contributor','{dig_for('ses_' + '4' * 24)}')"
        )


def test_bundle_digest_shape_and_uid_binding(seeded: sqlite3.Connection) -> None:
    ses = "ses_" + "7" * 24
    insert = (
        "INSERT INTO review_sessions(uid, contributor_id, locale, track, method,"
        " kit_version, rung_at_session, bundle_digest)"
        f" VALUES ('{ses}','{C_A}','ur','reserved_words','portal','k','contributor', ?)"
    )
    # Every character must be hex, not just the first (GLOB '[0-9a-f]*' only
    # anchors position 1 — the historical gap this test pins shut).
    with pytest.raises(sqlite3.IntegrityError):
        seeded.execute(insert, ("7" + "Z" * 63,))
    # A well-formed digest that is not the uid's pre-image is a forgery.
    with pytest.raises(sqlite3.IntegrityError):
        seeded.execute(insert, ("d" * 64,))
    seeded.execute(insert, (dig_for(ses),))


# ---------------------------------------------------------------------------
# annotations / expansions / commentary / style
# ---------------------------------------------------------------------------


def test_session_rejected_is_terminal(seeded: sqlite3.Connection) -> None:
    seeded.execute(f"UPDATE review_sessions SET status='rejected' WHERE uid='{SES1}'")
    with pytest.raises(sqlite3.IntegrityError, match="terminal"):
        seeded.execute(
            f"UPDATE review_sessions SET status='submitted' WHERE uid='{SES1}'"
        )


def test_insert_or_replace_blocked_on_sessions(seeded: sqlite3.Connection) -> None:
    # TEXT-PK tables must resist the same trench-coat UPDATE as the rankings:
    # the implicit DELETE hits the no-delete trigger (recursive_triggers ON).
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute(
            "INSERT OR REPLACE INTO review_sessions(uid, contributor_id, locale,"
            " track, method, kit_version, rung_at_session, bundle_digest)"
            f" VALUES ('{SES1}','{C_A}','ur','reserved_words','portal','kit-9',"
            f"'native_verified','{dig_for(SES1)}')"
        )


def test_session_options_junction(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        "INSERT INTO session_options(session_uid, option_uid, elicited)"
        f" VALUES ('{SES1}','{OPT1}','blind')"
    )
    with pytest.raises(sqlite3.IntegrityError):  # elicited vocabulary is closed
        seeded.execute(
            "INSERT INTO session_options(session_uid, option_uid, elicited)"
            f" VALUES ('{SES1}','{OPT2}','guessed')"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("UPDATE session_options SET elicited='quick'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM session_options")


def test_session_endorsements_frozen_and_no_delete(
    seeded: sqlite3.Connection,
) -> None:
    seeded.execute(
        "INSERT INTO session_endorsements(session_uid, endorsement_uid)"
        f" VALUES ('{SES1}','end_{'1' * 24}')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute(f"UPDATE session_endorsements SET session_uid='{SES2}'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM session_endorsements")


def test_expansion_triggers_and_checks(seeded: sqlite3.Connection) -> None:
    e1 = "exp_" + "1" * 24
    with pytest.raises(
        sqlite3.IntegrityError, match="does not match the session contributor"
    ):
        seeded.execute(  # SES1 belongs to C_A, not C_B
            "INSERT INTO option_expansions(uid, option_uid, contributor_id,"
            f" session_uid, expansion) VALUES ('{e1}','{OPT1}','{C_B}','{SES1}','x')"
        )
    with pytest.raises(sqlite3.IntegrityError):  # empty expansion
        seeded.execute(
            "INSERT INTO option_expansions(uid, option_uid, contributor_id, expansion)"
            f" VALUES ('{e1}','{OPT1}','{C_A}','')"
        )
    seeded.execute(
        "INSERT INTO option_expansions(uid, option_uid, contributor_id, session_uid,"
        f" expansion) VALUES ('{e1}','{OPT1}','{C_A}','{SES1}','ورنہ اگر')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute(f"UPDATE option_expansions SET expansion='y' WHERE uid='{e1}'")
    seeded.execute(
        f"UPDATE option_expansions SET retracted_at=datetime('now') WHERE uid='{e1}'"
    )
    with pytest.raises(sqlite3.IntegrityError, match="cannot be reversed"):
        seeded.execute(
            f"UPDATE option_expansions SET retracted_at=NULL WHERE uid='{e1}'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM option_expansions")


def test_annotations_and_commentary_no_delete(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        "INSERT INTO option_annotations(uid, option_uid, contributor_id, kind)"
        f" VALUES ('ann_{'5' * 24}','{OPT1}','{C_A}','regional')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM option_annotations")
    com = "com_" + "5" * 24
    with pytest.raises(
        sqlite3.IntegrityError, match="does not match the session contributor"
    ):
        seeded.execute(  # commentary claiming someone else's session
            "INSERT INTO concept_commentary(uid, contributor_id, session_uid,"
            f" concept_id, locale, topic, body) VALUES ('{com}','{C_B}','{SES1}',"
            "1,'ur','general','x')"
        )
    seeded.execute(
        "INSERT INTO concept_commentary(uid, contributor_id, concept_id, locale,"
        f" topic, body) VALUES ('{com}','{C_B}',1,'ur','general','x')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM concept_commentary")


def test_message_endorsements_smoke(seeded: sqlite3.Connection) -> None:
    # DEFERRED/inert track, but the DDL ships now — pin it before anything
    # depends on it (one insert, the once-per-contributor index, append-only).
    seeded.execute(
        "INSERT INTO message_templates(implementation, key, template_en)"
        " VALUES ('cpython','ZeroDivisionError.division_by_zero','division by zero')"
    )
    seeded.execute(
        "INSERT INTO message_translations(template_id, locale, template)"
        " VALUES (1,'ur','صفر سے تقسیم')"
    )
    men = "men_" + "1" * 24
    seeded.execute(
        "INSERT INTO message_endorsements(uid, message_translation_id,"
        f" contributor_id, method, rung_at_endorsement) VALUES ('{men}',1,'{C_A}',"
        "'portal','native_verified')"
    )
    with pytest.raises(sqlite3.IntegrityError):  # once per contributor while live
        seeded.execute(
            "INSERT INTO message_endorsements(uid, message_translation_id,"
            f" contributor_id, method, rung_at_endorsement) VALUES"
            f" ('men_{'2' * 24}',1,'{C_A}','portal','native_verified')"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute(
            f"UPDATE message_endorsements SET method='survey' WHERE uid='{men}'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM message_endorsements")


def test_email_rejects_control_whitespace(seeded: sqlite3.Connection) -> None:
    # LIKE '% %' only covers U+0020; the tab/newline family needs the char()
    # guards this test pins (the comment above the CHECK promised them).
    for bad in ("a\tb@c.io", "a\nb@c.io", "a\rb@c.io"):
        with pytest.raises(sqlite3.IntegrityError):
            seeded.execute(
                f"INSERT INTO contributor_identities(contributor_id, email)"
                f" VALUES ('{C_B}', ?)",
                (bad,),
            )


def test_annotation_one_live_per_kind_and_retraction(
    seeded: sqlite3.Connection,
) -> None:
    a1 = "ann_" + "1" * 24
    seeded.execute(
        "INSERT INTO option_annotations(uid, option_uid, contributor_id, session_uid, kind)"
        f" VALUES ('{a1}','{OPT1}','{C_A}','{SES1}','coined_neologism')"
    )
    with pytest.raises(sqlite3.IntegrityError):  # duplicate live vote
        seeded.execute(
            "INSERT INTO option_annotations(uid, option_uid, contributor_id, kind)"
            f" VALUES ('ann_{'2' * 24}','{OPT1}','{C_A}','coined_neologism')"
        )
    seeded.execute(
        f"UPDATE option_annotations SET retracted_at = datetime('now') WHERE uid='{a1}'"
    )
    with pytest.raises(sqlite3.IntegrityError, match="cannot be reversed"):
        seeded.execute(
            f"UPDATE option_annotations SET retracted_at = NULL WHERE uid='{a1}'"
        )
    # retraction frees the slot
    seeded.execute(
        "INSERT INTO option_annotations(uid, option_uid, contributor_id, kind)"
        f" VALUES ('ann_{'3' * 24}','{OPT1}','{C_A}','coined_neologism')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute(
            f"UPDATE option_annotations SET kind='regional' WHERE uid='{a1}'"
        )


def test_commentary_is_append_only_but_moderation_is_not(
    seeded: sqlite3.Connection,
) -> None:
    com = "com_" + "1" * 24
    seeded.execute(
        "INSERT INTO concept_commentary(uid, contributor_id, session_uid, concept_id,"
        f" locale, topic, body) VALUES ('{com}','{C_A}','{SES1}',1,'ur','word_formation','x')"
    )
    seeded.execute(
        f"INSERT INTO commentary_moderation(commentary_uid, status) VALUES ('{com}','published')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("UPDATE concept_commentary SET body='y'")
    seeded.execute(
        "UPDATE commentary_moderation SET status='withheld'"
    )  # derived: mutable


def test_style_one_live_vote(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        "INSERT INTO style_ratifications(uid, contributor_id, session_uid, locale, field, value)"
        f" VALUES ('sty_{'1' * 24}','{C_A}','{SES1}','ur','constants_strategy','marker_affix')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        seeded.execute(
            "INSERT INTO style_ratifications(uid, contributor_id, locale, field, value)"
            f" VALUES ('sty_{'2' * 24}','{C_A}','ur','constants_strategy','positional')"
        )


# ---------------------------------------------------------------------------
# identity deltas
# ---------------------------------------------------------------------------


def test_identity_email_and_credit_checks(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        "INSERT INTO contributor_identities(contributor_id, source_key, display_name,"
        f" email, credit_preference) VALUES ('{C_A}','gh:a','مدیحہ','a@example.org','name')"
    )
    for bad in ("not-an-email", "a@@b.co", "a b@c.io"):
        with pytest.raises(sqlite3.IntegrityError):
            seeded.execute(
                f"INSERT INTO contributor_identities(contributor_id, email) VALUES ('{C_B}', ?)",
                (bad,),
            )
    with pytest.raises(sqlite3.IntegrityError):  # unknown preference
        seeded.execute(
            f"INSERT INTO contributor_identities(contributor_id, credit_preference) VALUES ('{C_B}','public')"
        )
    with pytest.raises(sqlite3.IntegrityError):  # name credit needs a name
        seeded.execute(
            f"INSERT INTO contributor_identities(contributor_id, credit_preference) VALUES ('{C_B}','name')"
        )
    with pytest.raises(sqlite3.IntegrityError):  # handle credit needs a handle
        seeded.execute(
            f"INSERT INTO contributor_identities(contributor_id, credit_preference) VALUES ('{C_B}','handle')"
        )
    seeded.execute(
        f"INSERT INTO contributor_identities(contributor_id) VALUES ('{C_B}')"
    )
    assert one(
        seeded,
        f"SELECT credit_preference FROM contributor_identities WHERE contributor_id='{C_B}'",
    ) == ("anonymous",)


# ---------------------------------------------------------------------------
# import sources
# ---------------------------------------------------------------------------


def test_import_sources_redistribution_needs_license(db: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO import_sources(id, kind, name, redistributable)"
            " VALUES ('initiative:hedy','initiative','Hedy',1)"
        )
    db.execute(
        "INSERT INTO import_sources(id, kind, name, license_spdx, redistributable)"
        " VALUES ('initiative:universalpython','initiative','UniversalPython','Apache-2.0',1)"
    )
    db.execute(
        "INSERT INTO import_sources(id, kind, name)"
        " VALUES ('initiative:hedy','initiative','Hedy')"  # reference-only default
    )


# ---------------------------------------------------------------------------
# views
# ---------------------------------------------------------------------------


def test_promotion_mirrors_the_canon_gate(seeded: sqlite3.Connection) -> None:
    # OPT1: two native endorsers, validations green -> both flags up.
    assert one(
        seeded,
        f"SELECT reviewed_eligible, canon_eligible FROM option_promotion_status WHERE option_uid='{OPT1}'",
    ) == (1, 1)
    # OPT2: one endorser -> canon-eligible but not reviewed-eligible.
    assert one(
        seeded,
        f"SELECT reviewed_eligible, canon_eligible FROM option_promotion_status WHERE option_uid='{OPT2}'",
    ) == (0, 1)
    # sara-am-only is the ONE tolerated NFKC instability (CORE-1514); 'other' blocks.
    seeded.execute(
        f"UPDATE option_validations SET nfkc_stable=0, nfkc_delta_class='sara-am-only' WHERE option_uid='{OPT3}'"
    )
    assert one(
        seeded,
        f"SELECT canon_eligible FROM option_promotion_status WHERE option_uid='{OPT3}'",
    ) == (1,)
    seeded.execute(
        f"UPDATE option_validations SET nfkc_delta_class='other' WHERE option_uid='{OPT3}'"
    )
    assert one(
        seeded,
        f"SELECT canon_eligible FROM option_promotion_status WHERE option_uid='{OPT3}'",
    ) == (0,)


def test_second_endorsement_queue(seeded: sqlite3.Connection) -> None:
    assert seeded.execute(
        "SELECT option_uid FROM second_endorsement_queue"
    ).fetchall() == [(OPT2,)]


def test_terminology_export_picks_most_attested_expansion(
    seeded: sqlite3.Connection,
) -> None:
    seeded.executescript(
        f"""
        INSERT INTO option_expansions(uid, option_uid, contributor_id, session_uid, expansion)
        VALUES ('exp_{"1" * 24}','{OPT1}','{C_A}','{SES1}','ورنہ اگر'),
               ('exp_{"2" * 24}','{OPT1}','{C_B}',NULL,'ورنہ اگر'),
               ('exp_{"3" * 24}','{OPT1}','{C_C}',NULL,'متبادل');
        """
    )
    assert one(
        seeded, "SELECT expansion FROM terminology_export WHERE surface_form='ورنہ_اگر'"
    ) == ("ورنہ اگر",)


def test_transliteration_preference_counts(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        "INSERT INTO option_annotations(uid, option_uid, contributor_id, kind)"
        f" VALUES ('ann_{'9' * 24}','{OPT2}','{C_B}','transliteration')"
    )
    assert one(
        seeded,
        "SELECT live_options, options_tagged_translit, endorsements_on_translit FROM transliteration_preference WHERE locale='ur'",
    ) == (3, 1, 1)


def test_ranking_locale_must_match_session(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        "INSERT INTO locales(tag, language_subtag, name, native_name, in_registry)"
        " VALUES ('es','es','Spanish','Español',1)"
    )
    seeded.execute(
        "INSERT INTO review_sessions(uid, contributor_id, locale, track, method,"
        f" kit_version, rung_at_session, bundle_digest) VALUES"
        f" ('ses_{'6' * 24}','{C_A}','es','reserved_words','portal','kit-1','native_verified','{dig_for('ses_' + '6' * 24)}')"
    )
    with pytest.raises(
        sqlite3.IntegrityError, match="does not match the session locale"
    ):
        rank(seeded, "ses_" + "6" * 24, 1, OPT1, 1)  # ur ranking under an es session


def test_session_endorsement_link_must_match_contributor(
    seeded: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="different contributor"):
        seeded.execute(  # end_3 belongs to C_B; SES1 belongs to C_A
            f"INSERT INTO session_endorsements(session_uid, endorsement_uid)"
            f" VALUES ('{SES1}','end_{'3' * 24}')"
        )
    seeded.execute(  # C_A's own endorsement links fine
        f"INSERT INTO session_endorsements(session_uid, endorsement_uid)"
        f" VALUES ('{SES1}','end_{'1' * 24}')"
    )


def test_session_linked_rows_must_match_contributor(seeded: sqlite3.Connection) -> None:
    with pytest.raises(
        sqlite3.IntegrityError, match="does not match the session contributor"
    ):
        seeded.execute(  # annotation claims SES1 (C_A's) but is authored by C_B
            "INSERT INTO option_annotations(uid, option_uid, contributor_id, session_uid, kind)"
            f" VALUES ('ann_{'7' * 24}','{OPT1}','{C_B}','{SES1}','regional')"
        )
    with pytest.raises(
        sqlite3.IntegrityError, match="does not match the session contributor"
    ):
        seeded.execute(
            "INSERT INTO style_ratifications(uid, contributor_id, session_uid, locale, field, value)"
            f" VALUES ('sty_{'7' * 24}','{C_B}','{SES1}','ur','word_boundaries','underscore')"
        )
    seeded.execute(  # session-less rows carry no such claim
        "INSERT INTO option_annotations(uid, option_uid, contributor_id, kind)"
        f" VALUES ('ann_{'8' * 24}','{OPT1}','{C_B}','regional')"
    )


def test_verification_report_frozen_after_terminal(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        f"UPDATE review_sessions SET status='returned', verification_report='r1' WHERE uid='{SES1}'"
    )
    seeded.execute(
        f"UPDATE review_sessions SET verification_report='r2' WHERE uid='{SES1}'"
    )  # not terminal
    seeded.execute(
        f"UPDATE review_sessions SET status='accepted', verification_report='final' WHERE uid='{SES2}'"
    )
    with pytest.raises(
        sqlite3.IntegrityError, match="frozen once the session is terminal"
    ):
        seeded.execute(
            f"UPDATE review_sessions SET verification_report='tampered' WHERE uid='{SES2}'"
        )
    with pytest.raises(
        sqlite3.IntegrityError, match="frozen once the session is terminal"
    ):
        seeded.execute(
            f"UPDATE review_sessions SET notes='tampered' WHERE uid='{SES2}'"
        )


def test_latest_rankings_drops_retracted_endorsements(
    seeded: sqlite3.Connection,
) -> None:
    rank(seeded, SES1, 1, OPT1, 1)
    rank(seeded, SES1, 1, OPT2, 2)
    seeded.execute(f"UPDATE review_sessions SET status='accepted' WHERE uid='{SES1}'")
    seeded.execute(
        f"UPDATE endorsements SET retracted_at = datetime('now') WHERE uid='end_{'1' * 24}'"
    )
    rows = seeded.execute(
        f"SELECT option_uid FROM latest_rankings WHERE contributor_id='{C_A}' AND concept_id=1"
    ).fetchall()
    assert rows == [(OPT2,)]  # OPT1's ranking is stranded evidence, not input


def test_pack_promotion_counts_native_reviewers(seeded: sqlite3.Connection) -> None:
    seeded.execute(f"UPDATE review_sessions SET status='accepted' WHERE uid='{SES1}'")
    seeded.execute(
        "INSERT INTO review_sessions(uid, contributor_id, locale, track, method,"
        f" kit_version, rung_at_session, bundle_digest, status) VALUES"
        f" ('ses_{'5' * 24}','{C_C}','ur','reserved_words','portal','kit-1','contributor','{dig_for('ses_' + '5' * 24)}','accepted')"
    )
    assert one(
        seeded,
        "SELECT native_reviewers, total_reviewers FROM pack_promotion_status"
        " WHERE locale='ur' AND programming_language='python'",
    ) == (1, 2)  # C_A counts as native; C_C does not


# ---------------------------------------------------------------------------
# interim moderation / quarantine (CORE-1828; verdict shape shared with
# CORE-1797). Quarantine is an EXPLICIT verdict written by the importer for
# community-sourced options — absence of a screening row means "predates the
# intake path" and changes nothing, so the published corpus stays stable.
# ---------------------------------------------------------------------------


def screen(
    db: sqlite3.Connection,
    opt: str,
    verdict: str,
    by: str = "madi",
    version: str = "manual-interim-v1",
    note: str | None = None,
) -> None:
    db.execute(
        "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
        " screen_version, note) VALUES (?, ?, ?, ?, ?)",
        (opt, verdict, by, version, note),
    )


def test_screenings_are_append_only(seeded: sqlite3.Connection) -> None:
    screen(seeded, OPT1, "quarantined", by="importer")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("UPDATE option_screenings SET verdict='cleared'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        seeded.execute("DELETE FROM option_screenings")


def test_screening_vocabulary_and_auditability(seeded: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):  # vocabulary is closed
        screen(seeded, OPT1, "approved")
    with pytest.raises(sqlite3.IntegrityError):  # anonymous clearing is unauditable
        screen(seeded, OPT1, "cleared", by="")


def test_latest_screening_verdict_wins(seeded: sqlite3.Connection) -> None:
    screen(seeded, OPT1, "quarantined", by="importer")
    screen(seeded, OPT1, "cleared", note="import ritual 2026-08-11")
    assert one(
        seeded,
        f"SELECT verdict, screened_by FROM option_screening_status"
        f" WHERE option_uid='{OPT1}'",
    ) == ("cleared", "madi")


def test_quarantined_option_is_invisible_to_rankings(
    seeded: sqlite3.Connection,
) -> None:
    # Before: OPT1 stands first for elif (two native endorsements).
    assert one(
        seeded, f"SELECT standing FROM option_standings WHERE option_uid='{OPT1}'"
    ) == (1,)
    screen(seeded, OPT1, "quarantined", by="importer")
    for view in ("option_standings", "option_promotion_status", "terminology_export"):
        assert (
            seeded.execute(
                f"SELECT 1 FROM {view} WHERE surface_form='ورنہ_اگر'"  # nosec B608
            ).fetchall()
            == []
        ), view
    # The un-screened sibling now stands first — a quarantined row does not
    # compete — and the maintainer lens still sees the quarantined one.
    assert one(
        seeded, f"SELECT standing FROM option_standings WHERE option_uid='{OPT2}'"
    ) == (1,)
    assert one(
        seeded, f"SELECT verdict FROM quarantine_queue WHERE option_uid='{OPT1}'"
    ) == ("quarantined",)


def test_clearing_restores_visibility(seeded: sqlite3.Connection) -> None:
    screen(seeded, OPT1, "quarantined", by="importer")
    screen(seeded, OPT1, "cleared")
    assert one(
        seeded, f"SELECT standing FROM option_standings WHERE option_uid='{OPT1}'"
    ) == (1,)
    assert seeded.execute("SELECT 1 FROM quarantine_queue").fetchall() == []


def test_held_is_quarantine_too(seeded: sqlite3.Connection) -> None:
    # OPT2 sits in the second-endorsement queue while unscreened…
    assert seeded.execute(
        "SELECT option_uid FROM second_endorsement_queue"
    ).fetchall() == [(OPT2,)]
    screen(seeded, OPT2, "held", by="importer", note="needs a second look")
    assert (
        seeded.execute(
            f"SELECT 1 FROM option_standings WHERE option_uid='{OPT2}'"
        ).fetchall()
        == []
    )
    assert (
        seeded.execute("SELECT option_uid FROM second_endorsement_queue").fetchall()
        == []
    )


def test_canon_refuses_quarantined_option(seeded: sqlite3.Connection) -> None:
    screen(seeded, OPT1, "quarantined", by="importer")
    canon_insert = (
        "INSERT INTO canon_selections(concept_id, locale, option_uid,"
        f" surface_form, source_file) VALUES (1, 'ur', '{OPT1}', 'ورنہ_اگر',"
        " 'libs/i18n/canon/ur.toml')"
    )
    with pytest.raises(sqlite3.IntegrityError, match="quarantined"):
        seeded.execute(canon_insert)
    screen(seeded, OPT1, "cleared")
    seeded.execute(canon_insert)


def test_rejected_is_withheld_like_quarantine(seeded: sqlite3.Connection) -> None:
    # 'rejected' is the moderation verdict the intake runbook documents. The
    # predicate is `<> 'cleared'`, so it needs no per-verdict plumbing.
    screen(seeded, OPT1, "rejected", note="slur")
    assert (
        seeded.execute(
            f"SELECT 1 FROM option_standings WHERE option_uid='{OPT1}'"
        ).fetchall()
        == []
    )
    assert one(
        seeded, f"SELECT verdict FROM option_withheld WHERE option_uid='{OPT1}'"
    ) == ("rejected",)
    with pytest.raises(sqlite3.IntegrityError, match="quarantined"):
        seeded.execute(
            "INSERT INTO canon_selections(concept_id, locale, option_uid,"
            f" surface_form, source_file) VALUES (1,'ur','{OPT1}','ورنہ_اگر',"
            " 'libs/i18n/canon/ur.toml')"
        )


def test_an_unknown_verdict_is_refused(seeded: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        screen(seeded, OPT1, "approved")


def test_a_canon_selected_option_cannot_be_withheld_in_place(
    seeded: sqlite3.Connection,
) -> None:
    # The mirror of trg_canon_no_quarantined_option, previously untested.
    screen(seeded, OPT1, "cleared")
    seeded.execute(
        "INSERT INTO canon_selections(concept_id, locale, option_uid,"
        f" surface_form, source_file) VALUES (1,'ur','{OPT1}','ورنہ_اگر',"
        " 'libs/i18n/canon/ur.toml')"
    )
    for verdict in ("quarantined", "held", "rejected"):
        with pytest.raises(sqlite3.IntegrityError, match="canon-selected"):
            screen(seeded, OPT1, verdict)


def test_intake_views_can_be_added_to_a_database_that_predates_them(
    db: sqlite3.Connection,
) -> None:
    """A carried-forward operational database has no screening objects.

    `migrate_to_v2.py` rebuilds from scratch, but the intake ritual carries the
    previous database copy forward to keep its clearing verdicts — so the
    screening table and views must be installable onto a database built before
    they existed, or every gate and the corpus export fail with
    `no such table: option_withheld`.

    The pre-branch state is simulated by dropping exactly those objects from a
    current schema, which is what a database built at origin/main looks like.
    """
    from legesher_i18n.db.schema_v2 import ensure_intake_screening

    for view in ("option_withheld", "option_screening_status"):
        db.execute(f"DROP VIEW {view}")  # nosec B608 - fixed names
    db.execute("DROP TABLE option_screenings")
    with pytest.raises(sqlite3.OperationalError, match="option_withheld"):
        db.execute("SELECT 1 FROM option_withheld")

    for _ in range(2):  # idempotent: safe to call on every connection
        ensure_intake_screening(db)

    db.executescript(
        """
        INSERT INTO locales(tag, language_subtag, name, native_name, in_registry)
            VALUES ('ur','ur','Urdu','اردو',1);
        INSERT INTO concepts(slug, definition_en, category)
            VALUES ('elif-compound','x','control_flow');
        INSERT INTO options(uid, concept_id, locale, surface_form)
            VALUES ('opt_"""
        + "9" * 24
        + """', 1, 'ur', 'x');
        """
    )
    opt = "opt_" + "9" * 24
    assert db.execute("SELECT COUNT(*) FROM option_withheld").fetchone() == (0,)
    db.execute(
        "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
        " screen_version) VALUES (?, 'quarantined', 'importer', 'v1')",
        (opt,),
    )
    assert db.execute(
        "SELECT verdict FROM option_withheld WHERE option_uid = ?", (opt,)
    ).fetchone() == ("quarantined",)
    # The append-only trigger came back with the table, not just the view.
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE option_screenings SET verdict='cleared'")


def test_ensure_intake_screening_leaves_a_current_database_alone(
    seeded: sqlite3.Connection,
) -> None:
    from legesher_i18n.db.schema_v2 import ensure_intake_screening

    screen(seeded, OPT1, "cleared")
    ensure_intake_screening(seeded)
    assert one(
        seeded, f"SELECT verdict FROM option_screening_status WHERE option_uid='{OPT1}'"
    ) == ("cleared",)


# ---------------------------------------------------------------------------
# The carried-forward database, reproduced honestly (CORE-1838)
# ---------------------------------------------------------------------------
#
# The test above simulates the old database by dropping the three objects
# CORE-1828 ADDED. That is only half of what the branch did: it also rewrote
# the views and triggers that CONSUME the screening verdict. A database
# carried forward from before the branch has those consumers in their OLD,
# unfiltered form -- so dropping-only leaves the consumers already correct and
# cannot see whether the upgrade repairs them.
#
# This fixture reproduces both halves, and derives the "old" consumer bodies
# from the shipped DDL rather than hardcoding them, so the day someone moves
# the filter the fixture fails loudly instead of quietly becoming a no-op.

#: The screening filter as the shipped views spell it. Deleting the clause from
#: a view body yields exactly that view as it stood before CORE-1828.
_SCREENING_FILTER = re.compile(
    r"\s*(?:WHERE|AND)\s+NOT EXISTS\s*\(\s*SELECT 1 FROM option_withheld.*?\)",
    re.DOTALL,
)

#: Objects CORE-1828 introduced. `option_screenings` covers its index and its
#: triggers too (they carry it as `tbl_name`).
_SCREENING_ADDED = (
    "option_screenings",
    "option_screening_status",
    "option_withheld",
    "quarantine_queue",
    "trg_canon_no_quarantined_option",
)


@pytest.fixture()
def carried_forward(seeded: sqlite3.Connection) -> sqlite3.Connection:
    """`seeded`, rewound to the schema as it stood before CORE-1828."""
    consumers = seeded.execute(
        "SELECT name, sql FROM sqlite_master WHERE type = 'view'"
        " AND sql LIKE '%option_withheld%' AND name <> 'option_withheld'"
    ).fetchall()
    # The branch filtered two views; if that count moves, this fixture is
    # describing a schema that no longer exists.
    assert {name for name, _ in consumers} == {"option_standings", "terminology_export"}

    for name, sql in consumers:
        unfiltered, swaps = _SCREENING_FILTER.subn("", sql)
        assert swaps == 1, f"no screening filter found in {name}: {sql}"
        seeded.execute(f"DROP VIEW {name}")  # nosec B608 - name from sqlite_master
        seeded.execute(unfiltered)

    dropped = seeded.execute(
        "SELECT name, type FROM sqlite_master"
        " WHERE tbl_name = 'option_screenings' OR name IN (?, ?, ?, ?)",
        _SCREENING_ADDED[1:],
    ).fetchall()
    for name, kind in dropped:
        if kind != "index" or name.startswith(
            "idx_"
        ):  # implicit indexes go with the table
            seeded.execute(f"DROP {kind.upper()} IF EXISTS {name}")  # nosec B608
    seeded.commit()

    with pytest.raises(sqlite3.OperationalError, match="option_withheld"):
        seeded.execute("SELECT 1 FROM option_withheld")
    return seeded


def test_upgraded_database_hides_quarantined_options_from_standings(
    carried_forward: sqlite3.Connection,
) -> None:
    """Standings must stop ranking a quarantined option after the upgrade.

    The whole point of the screening verdict: an unscreened community
    submission does not COMPETE. A carried-forward database whose
    `option_standings` predates the filter keeps ranking it -- and everything
    built on standings (promotion status, the endorsement queue) inherits that.
    """
    from legesher_i18n.db.schema_v2 import ensure_intake_screening

    ensure_intake_screening(carried_forward)
    screen(carried_forward, OPT1, "quarantined", by="importer")

    ranked = {
        uid
        for (uid,) in carried_forward.execute("SELECT option_uid FROM option_standings")
    }
    assert OPT1 not in ranked
    assert OPT2 in ranked  # unscreened options are unaffected


def test_upgraded_database_hides_quarantined_options_from_terminology(
    carried_forward: sqlite3.Connection,
) -> None:
    """`terminology_export` feeds `legesher translate` prompt assembly.

    A quarantined submission surfacing as a term alternate is the same leak as
    exporting it, one layer further out.
    """
    from legesher_i18n.db.schema_v2 import ensure_intake_screening

    ensure_intake_screening(carried_forward)
    screen(carried_forward, OPT1, "quarantined", by="importer")

    alternates = {
        form
        for (form,) in carried_forward.execute(
            "SELECT surface_form FROM terminology_export"
        )
    }
    assert "ورنہ_اگر" not in alternates
    assert "وگرنہ" in alternates


def test_upgraded_database_has_the_maintainer_queue(
    carried_forward: sqlite3.Connection,
) -> None:
    """`legesher-i18n quarantine-queue` is the ritual's triage lens.

    Without the view the command dies with `no such table: quarantine_queue`
    on exactly the database the ritual carries forward.
    """
    from legesher_i18n.db.schema_v2 import ensure_intake_screening

    ensure_intake_screening(carried_forward)
    screen(carried_forward, OPT1, "quarantined", by="importer", note="new arrival")

    assert one(
        carried_forward,
        f"SELECT option_uid, verdict, note FROM quarantine_queue WHERE option_uid='{OPT1}'",
    ) == (OPT1, "quarantined", "new arrival")


def test_upgraded_database_refuses_canon_on_a_quarantined_option(
    carried_forward: sqlite3.Connection,
) -> None:
    """The canon guard is the one that would ship an unscreened word."""
    from legesher_i18n.db.schema_v2 import ensure_intake_screening

    ensure_intake_screening(carried_forward)
    screen(carried_forward, OPT1, "quarantined", by="importer")

    with pytest.raises(sqlite3.IntegrityError, match="quarantined"):
        carried_forward.execute(
            "INSERT INTO canon_selections(concept_id, locale, option_uid,"
            f" surface_form, source_file) VALUES (1,'ur','{OPT1}','ورنہ_اگر',"
            " 'libs/i18n/canon/ur.toml')"
        )


def test_the_review_track_is_not_the_renamed_term_category() -> None:
    """``reserved_words`` names two unrelated things. Only one was renamed.

    CORE-2060 renamed the term category ``reserved_word`` and the pack section
    ``reserved_words`` to ``implicit_param`` / ``implicit_params``, because the
    section held ``self`` and ``cls`` while its name claimed the grammar
    reserved them.

    ``review_sessions.track`` uses the same spelling for something else
    entirely: which body of work a reviewer sat for, as opposed to error
    messages or the style profile. That is the BROAD sense of the phrase, it is
    correct, and it stays.

    This is not hypothetical. The rename sweep was line-scoped, and eight
    review-session fixtures spell the track inside a multi-line INSERT whose
    column list sits on an earlier line, so the sweep could not see the word
    ``track`` and rewrote all eight. The CHECK constraint caught it. This test
    is the cheaper alarm: it fails on a rename, not on a database write.
    """
    schema = (
        Path(__file__).resolve().parents[1] / "legesher_i18n" / "db" / "schema_v2.sql"
    ).read_text(encoding="utf-8")
    bundle = (
        Path(__file__).resolve().parents[1]
        / "legesher_i18n"
        / "intake"
        / "bundle_schema.json"
    ).read_text(encoding="utf-8")

    assert "CHECK (track IN ('reserved_words', 'messages', 'style_profile'))" in schema
    assert (
        '"track": { "enum": ["reserved_words", "messages", "style_profile"] }' in bundle
    )

    # ...and the term category really did move, so this test cannot pass by
    # nothing having happened.
    from legesher_i18n.term_definitions import TERM_TYPE_YAML_SECTIONS

    assert "implicit_param" in TERM_TYPE_YAML_SECTIONS
    assert "reserved_word" not in TERM_TYPE_YAML_SECTIONS
    assert TERM_TYPE_YAML_SECTIONS["implicit_param"] == "implicit_params"


# ---------------------------------------------------------------------------
# The carried-forward database, before the CORE-2029 format-char net
# ---------------------------------------------------------------------------
#
# Same doctrine as the CORE-1838 fixture above: the upgrade must be tested
# against a database that is missing BOTH halves — the column AND the
# format-aware consumer bodies — and the "old" bodies are derived from the
# shipped DDL by deleting exactly the clauses CORE-2029 added, so the day the
# spelling moves this fixture fails loudly instead of quietly testing nothing.

#: The CORE-2029 clauses as the shipped objects spell them.
_FORMAT_TRIGGER_CLAUSE = re.compile(r"\s*AND v\.format_chars_clean = 1")
_FORMAT_STANDINGS_LINE = re.compile(
    r"\s*COALESCE\(v\.format_chars_clean, 0\) AS format_chars_clean,"
)
_FORMAT_PROMOTION_CLAUSE = re.compile(r"\s*AND s\.format_chars_clean = 1")

OPT4 = "opt_" + "4" * 24  # break candidate carrying a terminal tatweel
#: `توڑو` + U+0640 — invisible elongation; identifier-valid, NFKC-stable,
#: Arabic-script, so every pre-CORE-2029 verdict column reads clean.
TATWEEL_SURFACE = "توڑوـ"


def _rewind_format_net(conn: sqlite3.Connection) -> None:
    """Rewind a current schema to its shape before the CORE-2029 net."""
    rewinds = (
        ("TRIGGER", "trg_canon_requires_valid_identifier", _FORMAT_TRIGGER_CLAUSE, 1),
        ("VIEW", "option_standings", _FORMAT_STANDINGS_LINE, 1),
        ("VIEW", "option_promotion_status", _FORMAT_PROMOTION_CLAUSE, 2),
    )
    for kind, name, pattern, expected in rewinds:
        (sql,) = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = ?", (name,)
        ).fetchone()
        rewound, swaps = pattern.subn("", sql)
        assert swaps == expected, f"format-net clause not found in {name}: {sql}"
        conn.execute(f"DROP {kind} {name}")  # nosec B608 - fixed names
        conn.execute(rewound)
    conn.execute("ALTER TABLE option_validations DROP COLUMN format_chars_clean")


@pytest.fixture()
def pre_format_net(seeded: sqlite3.Connection) -> sqlite3.Connection:
    """`seeded`, rewound to the schema as it stood before CORE-2029."""
    _rewind_format_net(seeded)

    # A payload option recorded UNDER the old regime: its validation row reads
    # spotless because the old validator measured nothing the payload trips.
    seeded.executescript(
        f"""
        INSERT INTO options(uid, concept_id, locale, programming_language, surface_form)
            VALUES ('{OPT4}', 2, 'ur', NULL, '{TATWEEL_SURFACE}');
        INSERT INTO option_validations(option_uid, validator_version, identifier_valid,
            nfkc_stable, script_consistent) VALUES ('{OPT4}','audit-v1',1,1,1);
        INSERT INTO canon_selections(concept_id, locale, option_uid, surface_form, source_file)
            VALUES (1, 'ur', '{OPT1}', 'ورنہ_اگر', 'libs/i18n/canon/ur.toml');
        """
    )
    seeded.commit()
    return seeded


def test_format_net_upgrade_backfills_by_running_the_scan(
    pre_format_net: sqlite3.Connection,
) -> None:
    """The column arrives COMPUTED, never stamped — including under canon.

    OPT1 is canon-selected, so the freeze triggers guard its validation row;
    the upgrade must still record its honest verdict, and the triggers must
    survive the upgrade intact.
    """
    from legesher_i18n.db.schema_v2 import ensure_format_char_net

    for _ in range(2):  # idempotent: safe to call on every connection
        ensure_format_char_net(pre_format_net)

    verdicts = dict(
        pre_format_net.execute(
            "SELECT option_uid, format_chars_clean FROM option_validations"
        )
    )
    assert verdicts == {OPT1: 1, OPT2: 1, OPT3: 1, OPT4: 0}
    with pytest.raises(sqlite3.IntegrityError, match="canon-selected"):
        pre_format_net.execute(
            "UPDATE option_validations SET identifier_valid = 0 WHERE option_uid = ?",
            (OPT1,),
        )


def test_upgraded_database_refuses_canon_on_a_format_char_payload(
    pre_format_net: sqlite3.Connection,
) -> None:
    """The canon guard is format-aware after the upgrade, and only then."""
    from legesher_i18n.db.schema_v2 import ensure_format_char_net

    ensure_format_char_net(pre_format_net)
    with pytest.raises(sqlite3.IntegrityError, match="format-char"):
        pre_format_net.execute(
            "INSERT INTO canon_selections(concept_id, locale, option_uid,"
            f" surface_form, source_file) VALUES (2,'ur','{OPT4}',"
            f" '{TATWEEL_SURFACE}', 'libs/i18n/canon/ur.toml')"
        )
    # A clean, freshly-backfilled option still ships.
    pre_format_net.execute(
        "INSERT INTO canon_selections(concept_id, locale, option_uid,"
        f" surface_form, source_file) VALUES (2,'ur','{OPT3}','توڑو',"
        " 'libs/i18n/canon/ur.toml')"
    )


def test_upgraded_promotion_status_reads_the_format_verdict(
    pre_format_net: sqlite3.Connection,
) -> None:
    """The maintainer lens must stop calling a payload canon-eligible."""
    from legesher_i18n.db.schema_v2 import ensure_format_char_net

    ensure_format_char_net(pre_format_net)
    eligible = dict(
        pre_format_net.execute(
            "SELECT option_uid, canon_eligible FROM option_promotion_status"
        )
    )
    assert eligible[OPT4] == 0
    assert eligible[OPT3] == 1


def test_an_aborted_upgrade_leaves_the_carried_forward_file_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The upgrade is ONE transaction: a crash mid-backfill undoes all of it.

    Before the fix, sqlite3's legacy autocommit committed the ALTER and the
    two freeze-trigger DROPs on their own while the backfill UPDATEs sat in an
    uncommitted transaction — so a crash mid-backfill left the FILE with the
    column added, nothing filled, and BOTH validation-freeze triggers durably
    absent: every canon-covered validation row freely mutable for any writer
    that opens the database raw (correct_canon_review_rung.py does). The
    surgery must be atomic: abort → the pre-upgrade state, whole.
    """
    from legesher_i18n import surface_validation
    from legesher_i18n.db import schema_v2 as schema_mod

    path = tmp_path / "carried.db"
    conn = schema_mod.connect(path)
    apply_schema_v2(conn)
    conn.executescript(
        f"""
        INSERT INTO locales(tag, language_subtag, name, native_name, in_registry)
            VALUES ('ur','ur','Urdu','اردو',1);
        INSERT INTO concepts(slug, definition_en, category)
            VALUES ('elif-compound','x','control_flow');
        INSERT INTO options(uid, concept_id, locale, surface_form) VALUES
            ('{OPT1}', 1, 'ur', 'ورنہ_اگر'), ('{OPT2}', 1, 'ur', 'وگرنہ');
        """
    )
    _rewind_format_net(conn)
    conn.executescript(
        f"""
        INSERT INTO option_validations(option_uid, validator_version, identifier_valid,
            nfkc_stable, script_consistent) VALUES
            ('{OPT1}','audit-v1',1,1,1), ('{OPT2}','audit-v1',1,1,1);
        """
    )
    conn.commit()

    calls = {"n": 0}
    real_scan = surface_validation.format_char_violations

    def crash_on_second_row(surface: str, allowed: frozenset[str]) -> list[str]:
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("simulated crash mid-backfill")
        return real_scan(surface, allowed)

    monkeypatch.setattr(
        surface_validation, "format_char_violations", crash_on_second_row
    )
    with pytest.raises(RuntimeError, match="mid-backfill"):
        schema_mod.ensure_format_char_net(conn)
    conn.close()  # what a killed process leaves behind: no commit

    reopened = schema_mod.connect(path)
    # The pre-upgrade state, whole: no column, no partial fill…
    columns = {
        row[1] for row in reopened.execute("PRAGMA table_info(option_validations)")
    }
    assert "format_chars_clean" not in columns
    # …BOTH freeze triggers present…
    triggers = {
        row[0]
        for row in reopened.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        )
    }
    assert {
        "trg_validations_frozen_under_canon",
        "trg_validations_no_delete_under_canon",
    } <= triggers
    # …and the canon guard still in its pre-upgrade body.
    (canon_trigger,) = reopened.execute(
        "SELECT sql FROM sqlite_master"
        " WHERE name = 'trg_canon_requires_valid_identifier'"
    ).fetchone()
    assert "format_chars_clean" not in canon_trigger

    # A clean re-run completes the upgrade from the intact base (the stub
    # crashes only on its second-ever call; these are calls three and four).
    schema_mod.ensure_format_char_net(reopened)
    verdicts = dict(
        reopened.execute(
            "SELECT option_uid, format_chars_clean FROM option_validations"
        )
    )
    assert verdicts == {OPT1: 1, OPT2: 1}
    reopened.close()
