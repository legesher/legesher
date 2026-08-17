"""The six-stage review-bundle verification pipeline (CORE-1688).

Boundary doctrine, from the ticket's acceptance lines and the settled
decisions of 2026-08-11:

* a valid bundle ingests end-to-end; re-importing it changes ZERO rows
* semantic failures (ranking ⊄ endorsements, flag∩ranking, unknown concept)
  produce ``returned`` with an actionable report
* mechanical failures ingest as canon-ineligible EVIDENCE, never drop the
  session (the CORE-1400 reframe)
* everything a stranger submits lands quarantined until cleared (CORE-1828)
* consent rides every submission: no consent asserted → no identity minted
* the withdrawal tombstone rule (contributor-withdrawal-runbook.md): a bundle
  predating ``withdrawn_at`` writes evidence with no identity column; one
  postdating it stops and surfaces to a human — never decided in code
"""

from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db import schema_v2
from legesher_i18n.db.schema_v2 import (
    apply_schema_v2,
    contributor_id,
    option_uid,
    session_uid,
)
from legesher_i18n.intake.canonical import canonicalize
from legesher_i18n.intake.pipeline import BundleImporter

SALT = "intake-test-salt"
REVIEWER = "urdu-reviewer"
REVIEWER_ID = contributor_id(REVIEWER, salt=SALT)

# Pre-seeded model candidate (arrived via the kit, not via this reviewer).
OPT_MODEL = option_uid("elif-compound", "ur", "وگرنہ")


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "intake.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    conn.executescript(
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
        INSERT INTO options(uid, concept_id, locale, programming_language, surface_form)
            VALUES ('{OPT_MODEL}', 1, 'ur', NULL, 'وگرنہ');
        INSERT INTO option_provenance(option_uid, source, source_detail, model_version)
            VALUES ('{OPT_MODEL}', 'model', 'aya', 'aya-101');
        INSERT INTO option_validations(option_uid, validator_version, identifier_valid,
            nfkc_stable, script_consistent) VALUES ('{OPT_MODEL}','audit-v1',1,1,1);
        """
    )
    conn.commit()
    conn.close()
    return path


def make_bundle(**overrides: object) -> dict:
    bundle = {
        "bundle_version": "1.0",
        "kit_version": "v2@2026-08-11+abc123",
        "locale": "ur",
        "track": "reserved_words",
        "contributor": {
            "source_key": REVIEWER,
            "claimed_rung": "native_claimed",
            "consent": {
                "consent_version": "1.0",
                "credit_preference": "handle",
            },
            "contact_captured": False,
        },
        "attestations": {
            "native_or_fluent": True,
            "original_work": True,
            "license_grant": "Apache-2.0",
            "coc_agreed": True,
            "dco": True,
            "research_use": True,
        },
        "responses": [
            {
                "concept": "elif-compound",
                "blind": {
                    "surface_form": "ورنہ_اگر",
                    "word_form": "conjunction_compound",
                    "established_term": "coined",
                    "rationale": "reads naturally in a conditional chain",
                    "self_annotations": ["coined_neologism"],
                },
                "endorsements": [
                    {"surface_form": "ورنہ_اگر", "annotations": [], "comment": None},
                    {
                        "surface_form": "وگرنہ",
                        "annotations": ["established_term"],
                        "comment": "the word my textbook used",
                    },
                ],
                "ranking": ["ورنہ_اگر", "وگرنہ"],
                "flags": [],
                "expansion": {
                    "for": "ورنہ_اگر",
                    "text": "ورنہ اگر",
                    "formation_note": "underscore joins the two words",
                },
                "commentary": [
                    {"topic": "word_formation", "body": "compounds join with _"}
                ],
            }
        ],
        "session": {"started_at": "2026-08-11T09:00:00Z", "durations_ms": {}},
    }
    bundle.update(copy.deepcopy(overrides))  # type: ignore[arg-type]
    return bundle


def importer(db_path: Path) -> BundleImporter:
    return BundleImporter(db_path, salt=SALT)


def counts(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    tables = [
        "review_sessions",
        "options",
        "endorsements",
        "session_options",
        "session_endorsements",
        "session_rankings",
        "option_annotations",
        "option_expansions",
        "concept_commentary",
        "option_screenings",
        "option_provenance",
        "contributors",
        "contributor_identities",
        "style_ratifications",
    ]
    out = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # nosec B608
        for t in tables
    }
    conn.close()
    return out


def q(db_path: Path, sql: str, *args: object) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# stage 6: a valid bundle ingests end-to-end
# ---------------------------------------------------------------------------


def test_valid_bundle_ingests_end_to_end(db_path: Path) -> None:
    bundle = make_bundle()
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "accepted"
    assert result.session_uid == session_uid(canonicalize(bundle))

    (status, report_json, rung) = q(
        db_path,
        "SELECT status, verification_report, rung_at_session"
        " FROM review_sessions WHERE uid=?",
        result.session_uid,
    )[0]
    assert status == "accepted"
    assert rung == "native_claimed"
    report = json.loads(report_json)
    assert [s["stage"] for s in report["stages"]] == [
        "schema",
        "conduct",
        "identity",
        "gates",
        "quality",
        "ingest",
    ]

    # The blind coinage became a NEW option with community provenance…
    new_opt = option_uid("elif-compound", "ur", "ورنہ_اگر")
    assert q(
        db_path, "SELECT source FROM option_provenance WHERE option_uid=?", new_opt
    ) == [("community",)]
    # …validated by the real validator suite…
    assert q(
        db_path,
        "SELECT identifier_valid, script_consistent FROM option_validations"
        " WHERE option_uid=?",
        new_opt,
    ) == [(1, 1)]
    # …and QUARANTINED by default (CORE-1828), while the pre-existing model
    # candidate the reviewer merely endorsed is untouched.
    assert q(
        db_path,
        "SELECT verdict, screened_by FROM option_screening_status WHERE option_uid=?",
        new_opt,
    ) == [("quarantined", "importer")]
    assert q(
        db_path,
        "SELECT COUNT(*) FROM option_screenings WHERE option_uid=?",
        OPT_MODEL,
    ) == [(0,)]

    # Both endorsements exist, linked to the session; blind is elicited=blind.
    assert q(
        db_path,
        "SELECT COUNT(*) FROM endorsements WHERE contributor_id=? AND retracted_at IS NULL",
        REVIEWER_ID,
    ) == [(2,)]
    assert q(
        db_path,
        "SELECT elicited FROM session_options WHERE option_uid=?",
        new_opt,
    ) == [("blind",)]
    assert q(
        db_path,
        "SELECT COUNT(*) FROM session_endorsements WHERE session_uid=?",
        result.session_uid,
    ) == [(2,)]

    # Ranking, annotations, expansion, commentary all landed.
    assert q(
        db_path,
        "SELECT option_uid, rank FROM session_rankings WHERE session_uid=? ORDER BY rank",
        result.session_uid,
    ) == [(new_opt, 1), (OPT_MODEL, 2)]
    assert q(
        db_path,
        "SELECT kind FROM option_annotations WHERE option_uid=? ORDER BY kind",
        OPT_MODEL,
    ) == [("established_term",)]
    assert q(
        db_path,
        "SELECT expansion FROM option_expansions WHERE option_uid=?",
        new_opt,
    ) == [("ورنہ اگر",)]
    assert q(
        db_path,
        "SELECT status FROM commentary_moderation",
    ) == [("pending",)]

    # Consent recorded at identity minting (decision 2026-08-11).
    assert q(
        db_path,
        "SELECT source_key, consent_version, credit_preference,"
        " consent_at IS NOT NULL, github_handle FROM contributor_identities"
        " WHERE contributor_id=?",
        REVIEWER_ID,
    ) == [(REVIEWER, "1.0", "handle", 1, REVIEWER)]


def test_reimport_is_a_zero_row_noop(db_path: Path) -> None:
    bundle = make_bundle()
    imp = importer(db_path)
    first = imp.import_bundle(bundle)
    assert first.status == "accepted"
    before = counts(db_path)

    again = imp.import_bundle(bundle)
    assert again.status == "duplicate"
    assert again.session_uid == first.session_uid
    assert counts(db_path) == before


# ---------------------------------------------------------------------------
# stage 1: semantic failures return the bundle with an actionable report
# ---------------------------------------------------------------------------


def test_ranking_outside_endorsements_is_returned(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["ranking"] = ["ورنہ_اگر", "توڑو"]
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "returned"
    schema_stage = result.report["stages"][0]
    assert schema_stage["status"] == "fail"
    assert any("توڑو" in str(d) for d in schema_stage["details"])
    # The session row records the return; no corpus rows were written.
    c = counts(db_path)
    assert c["review_sessions"] == 1
    assert c["options"] == 1  # the pre-seeded model candidate only
    assert c["endorsements"] == 0
    assert q(db_path, "SELECT status FROM review_sessions") == [("returned",)]


def test_flag_ranking_overlap_is_returned(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["flags"] = [
        {"surface_form": "وگرنہ", "reason": "transliteration", "comment": None}
    ]
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any(
        "flag" in str(d) and "rank" in str(d)
        for d in result.report["stages"][0]["details"]
    )


def test_unknown_concept_is_returned_with_the_slug_named(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["concept"] = "walrus-operator"
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any(
        "walrus-operator" in str(d) for d in result.report["stages"][0]["details"]
    )


def test_schema_invalid_bundle_is_returned(db_path: Path) -> None:
    bundle = make_bundle()
    del bundle["attestations"]
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any("attestations" in str(d) for d in result.report["stages"][0]["details"])
    assert counts(db_path)["endorsements"] == 0


def test_unknown_locale_is_returned_without_a_session_row(db_path: Path) -> None:
    bundle = make_bundle(locale="xx")
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert counts(db_path)["review_sessions"] == 0
    assert any("xx" in str(d) for d in result.report["stages"][0]["details"])


# ---------------------------------------------------------------------------
# stage 2: conduct screen escalates to a human, never auto-rejects
# ---------------------------------------------------------------------------


def test_pii_in_free_text_escalates_but_does_not_reject(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["commentary"] = [
        {"topic": "general", "body": "email me at someone@example.com for context"}
    ]
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "accepted"  # never auto-reject on a screen hit
    conduct = result.report["stages"][1]
    assert conduct["status"] == "warn"
    assert any("someone@example.com" in str(d) for d in conduct["details"])
    assert result.needs_human_eyes


def test_wordlist_hit_escalates(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["blind"]["rationale"] = "this badword reads naturally"
    result = BundleImporter(
        db_path, salt=SALT, conduct_wordlist=["badword"]
    ).import_bundle(bundle)
    assert result.status == "accepted"
    assert result.report["stages"][1]["status"] == "warn"
    assert result.needs_human_eyes


# ---------------------------------------------------------------------------
# stage 3: attestations, consent, and the withdrawal tombstone rule
# ---------------------------------------------------------------------------


def test_missing_dco_is_returned(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["attestations"]["dco"] = False
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any("dco" in str(d).lower() for d in result.report["stages"][2]["details"])


def test_no_consent_ingests_evidence_but_mints_no_identity(db_path: Path) -> None:
    bundle = make_bundle()
    del bundle["contributor"]["consent"]
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "accepted"
    c = counts(db_path)
    assert c["endorsements"] == 2
    assert c["contributor_identities"] == 0  # no consent -> no identity row
    assert any(
        "consent" in str(d).lower() for d in result.report["stages"][2]["details"]
    )


def test_withdrawn_replay_writes_evidence_without_identity(db_path: Path) -> None:
    conn = schema_v2.connect(db_path)
    conn.execute("INSERT INTO contributors(id) VALUES (?)", (REVIEWER_ID,))
    conn.execute(
        "INSERT INTO contributor_identities(contributor_id, withdrawn_at)"
        " VALUES (?, '2026-08-01')",
        (REVIEWER_ID,),
    )
    conn.commit()
    conn.close()

    bundle = make_bundle()
    bundle["session"]["started_at"] = "2026-07-15T12:00:00Z"  # predates withdrawal
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "accepted"
    assert result.withdrawn_replay
    assert counts(db_path)["endorsements"] == 2  # evidence written
    # The tombstone is untouched: every identity column still empty.
    assert q(
        db_path,
        "SELECT source_key, consent_version, withdrawn_at FROM contributor_identities"
        " WHERE contributor_id=?",
        REVIEWER_ID,
    ) == [(None, None, "2026-08-01")]


def test_withdrawn_postdating_bundle_halts_for_a_human(db_path: Path) -> None:
    conn = schema_v2.connect(db_path)
    conn.execute("INSERT INTO contributors(id) VALUES (?)", (REVIEWER_ID,))
    conn.execute(
        "INSERT INTO contributor_identities(contributor_id, withdrawn_at)"
        " VALUES (?, '2026-08-01')",
        (REVIEWER_ID,),
    )
    conn.commit()
    conn.close()
    before = counts(db_path)

    bundle = make_bundle()
    bundle["session"]["started_at"] = "2026-08-05T12:00:00Z"  # postdates
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "halted"
    assert counts(db_path) == before  # nothing written, not even a session
    assert "human" in result.report["stages"][2]["details"][0].lower()


def test_withdrawn_with_no_timestamp_halts_conservatively(db_path: Path) -> None:
    conn = schema_v2.connect(db_path)
    conn.execute("INSERT INTO contributors(id) VALUES (?)", (REVIEWER_ID,))
    conn.execute(
        "INSERT INTO contributor_identities(contributor_id, withdrawn_at)"
        " VALUES (?, '2026-08-01')",
        (REVIEWER_ID,),
    )
    conn.commit()
    conn.close()

    bundle = make_bundle()
    bundle["session"] = {"durations_ms": {}}
    assert importer(db_path).import_bundle(bundle).status == "halted"


# ---------------------------------------------------------------------------
# stage 4: mechanical failures ingest as canon-ineligible evidence
# ---------------------------------------------------------------------------


def test_mechanical_failure_ingests_canon_ineligible(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["endorsements"].append(
        {
            "surface_form": "غلط لفظ",
            "annotations": [],
            "comment": None,
        }  # space: invalid
    )
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "accepted"  # the ROW is blocked, never the session
    bad_opt = option_uid("elif-compound", "ur", "غلط لفظ")
    assert q(
        db_path,
        "SELECT identifier_valid FROM option_validations WHERE option_uid=?",
        bad_opt,
    ) == [(0,)]
    gates = result.report["stages"][3]
    assert any("غلط لفظ" in str(d) for d in gates["details"])


# ---------------------------------------------------------------------------
# stage 5: quality signals warn and never block
# ---------------------------------------------------------------------------


def test_quality_signals_are_warn_only(db_path: Path) -> None:
    bundle = make_bundle()
    result = importer(db_path).import_bundle(bundle)
    quality = result.report["stages"][4]
    assert quality["status"] in ("pass", "warn")
    assert result.status == "accepted"


# ---------------------------------------------------------------------------
# repeat sittings
# ---------------------------------------------------------------------------


def test_second_session_links_the_existing_live_endorsement(db_path: Path) -> None:
    imp = importer(db_path)
    assert imp.import_bundle(make_bundle()).status == "accepted"

    second = make_bundle()
    second["session"]["started_at"] = "2026-08-12T09:00:00Z"
    second["responses"][0]["ranking"] = ["وگرنہ", "ورنہ_اگر"]  # changed their mind
    result = imp.import_bundle(second)
    assert result.status == "accepted"

    # Still one live endorsement per option — the new session links the old row.
    assert q(
        db_path,
        "SELECT COUNT(*) FROM endorsements WHERE contributor_id=? AND retracted_at IS NULL",
        REVIEWER_ID,
    ) == [(2,)]
    assert q(
        db_path,
        "SELECT COUNT(*) FROM session_endorsements WHERE session_uid=?",
        result.session_uid,
    ) == [(2,)]


def test_style_answer_supersedes_the_previous_live_vote(db_path: Path) -> None:
    imp = importer(db_path)
    first = make_bundle(
        track="style_profile",
        programming_language=None,
        responses=[],
        style_answers=[
            {
                "field": "constants_strategy",
                "value": "marker_affix:ثابت_",
                "rationale": None,
            }
        ],
    )
    assert imp.import_bundle(first).status == "accepted"

    second = make_bundle(
        track="style_profile",
        programming_language=None,
        responses=[],
        style_answers=[
            {
                "field": "constants_strategy",
                "value": "positional",
                "rationale": "changed my mind",
            }
        ],
        session={"started_at": "2026-08-12T10:00:00Z", "durations_ms": {}},
    )
    assert imp.import_bundle(second).status == "accepted"

    live = q(
        db_path,
        "SELECT value FROM style_ratifications WHERE retracted_at IS NULL AND field='constants_strategy'",
    )
    assert live == [("positional",)]


# ---------------------------------------------------------------------------
# the reply the ritual posts back
# ---------------------------------------------------------------------------


def test_reply_names_uids_and_the_screening_honestly(db_path: Path) -> None:
    result = importer(db_path).import_bundle(make_bundle())
    reply = result.reply_text()
    assert result.session_uid in reply
    new_opt = option_uid("elif-compound", "ur", "ورنہ_اگر")
    assert new_opt in reply
    # Contributor-facing honesty (CORE-1828): screened by a human before visible.
    assert "screen" in reply.lower()


# ---------------------------------------------------------------------------
# review findings (2026-08-11): the salt guard, resumable returns, and the
# failure modes that used to escape as tracebacks
# ---------------------------------------------------------------------------


def test_the_public_dev_salt_is_refused(db_path: Path) -> None:
    # contributor_id is a PRIMARY KEY ingredient: minting live rows with the
    # public default salt forks every id, and --sync pushes the fork to the
    # durable home. migrate_to_v2 --publish guards this; so must intake.
    with pytest.raises(ValueError, match="salt"):
        BundleImporter(db_path, salt=schema_v2.DEFAULT_CONTRIBUTOR_SALT)
    # An explicit opt-out exists for fixtures and dry runs.
    BundleImporter(
        db_path, salt=schema_v2.DEFAULT_CONTRIBUTOR_SALT, allow_dev_salt=True
    )


def test_a_salt_mismatching_the_build_is_refused(db_path: Path) -> None:
    # build_meta records sha256(salt)[:16] of the salt that minted this DB's
    # ids. A different salt would mint ids that silently fork from it.
    conn = schema_v2.connect(db_path)
    conn.execute(
        "INSERT INTO build_meta(key, value) VALUES ('salt_fingerprint', ?)",
        (schema_v2.salt_fingerprint("a-completely-different-salt"),),
    )
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="salt_fingerprint"):
        BundleImporter(db_path, salt=SALT).import_bundle(make_bundle())


def test_a_salt_matching_the_build_is_accepted(db_path: Path) -> None:
    conn = schema_v2.connect(db_path)
    conn.execute(
        "INSERT INTO build_meta(key, value) VALUES ('salt_fingerprint', ?)",
        (schema_v2.salt_fingerprint(SALT),),
    )
    conn.commit()
    conn.close()
    assert importer(db_path).import_bundle(make_bundle()).status == "accepted"


def test_a_returned_bundle_can_be_reimported_once_the_cause_is_fixed(
    db_path: Path,
) -> None:
    # A `returned` session is NOT terminal (schema: only accepted/rejected
    # are). Re-submitting the identical bundle after registering the missing
    # concept must ingest it — not answer "already imported, thank you!".
    bundle = make_bundle()
    bundle["responses"][0]["concept"] = "while-loop"
    first = importer(db_path).import_bundle(bundle)
    assert first.status == "returned"

    conn = schema_v2.connect(db_path)
    conn.execute(
        "INSERT INTO concepts(slug, definition_en, category)"
        " VALUES ('while-loop','loop while a condition holds','control_flow')"
    )
    conn.execute(
        "INSERT INTO terms(concept_id, programming_language, name, category)"
        " VALUES ((SELECT id FROM concepts WHERE slug='while-loop'),"
        " 'python','while','keyword')"
    )
    conn.commit()
    conn.close()

    second = importer(db_path).import_bundle(bundle)
    assert second.status == "accepted"
    assert second.session_uid == first.session_uid  # same bytes, same identity
    assert counts(db_path)["review_sessions"] == 1  # resumed, not duplicated
    assert q(db_path, "SELECT status FROM review_sessions") == [("accepted",)]


def test_an_accepted_bundle_still_reports_duplicate(db_path: Path) -> None:
    imp = importer(db_path)
    assert imp.import_bundle(make_bundle()).status == "accepted"
    assert imp.import_bundle(make_bundle()).status == "duplicate"


def test_parse_notes_survive_a_duplicate_reimport(db_path: Path) -> None:
    """A re-run of the same bundle still reports what the parse noticed.

    The duplicate branch returns before the rest of the stage list is built,
    so notes raised on the way in would vanish on exactly the run a maintainer
    makes when re-checking an issue already imported (CORE-1838).
    """
    imp = importer(db_path)
    notes = ["unknown term `walrus`: no concept maps to it; line skipped"]

    assert imp.import_bundle(make_bundle(), parse_notes=notes).status == "accepted"
    again = imp.import_bundle(make_bundle(), parse_notes=notes)

    assert again.status == "duplicate"
    assert again.parse_notes == notes
    assert again.report["stages"] == [
        {"stage": "parse", "status": "warn", "details": notes}
    ]


def test_a_repeated_ranking_entry_is_returned_not_a_traceback(
    db_path: Path,
) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["ranking"] = ["ورنہ_اگر", "ورنہ_اگر"]
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any(
        "more than once" in str(d) for d in result.report["stages"][0]["details"]
    )


def test_two_responses_on_one_concept_are_returned(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"].append(dict(bundle["responses"][0]))
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any("twice" in str(d) for d in result.report["stages"][0]["details"])


def test_flagging_a_word_the_corpus_does_not_hold_is_returned(
    db_path: Path,
) -> None:
    # A flag is a report ABOUT a candidate the reviewer was shown. Minting the
    # word as a new option would record the REPORTER as its author, with
    # community provenance, and tell them "new option recorded".
    bundle = make_bundle()
    bundle["responses"][0]["flags"] = [
        {"surface_form": "بدلفظ", "reason": "offensive", "comment": "slur"}
    ]
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any("بدلفظ" in str(d) for d in result.report["stages"][0]["details"])
    assert counts(db_path)["options"] == 1  # only the pre-seeded candidate


def test_flagging_an_existing_option_is_recorded_without_authoring_it(
    db_path: Path,
) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["endorsements"] = [
        {"surface_form": "ورنہ_اگر", "annotations": [], "comment": None}
    ]
    bundle["responses"][0]["ranking"] = ["ورنہ_اگر"]
    bundle["responses"][0]["flags"] = [
        {
            "surface_form": "وگرنہ",
            "reason": "register_mismatch",
            "comment": "too formal",
        }
    ]
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "accepted"
    assert q(
        db_path, "SELECT reason FROM option_flags WHERE option_uid=?", OPT_MODEL
    ) == [("register_mismatch",)]
    # The flagger did not become a provenance author of the flagged word.
    assert q(
        db_path,
        "SELECT COUNT(*) FROM option_provenance WHERE option_uid=? AND source='community'",
        OPT_MODEL,
    ) == [(0,)]


def test_a_non_object_bundle_is_a_clean_value_error(db_path: Path) -> None:
    for payload in (b"[1, 2, 3]", b'"just a string"', b"null"):
        with pytest.raises(ValueError, match="JSON object"):
            importer(db_path).import_bundle(payload)


# ---------------------------------------------------------------------------
# second review (2026-08-12): mechanical gate coverage, the blind/elicited
# signal, identity authority, and consent immutability
# ---------------------------------------------------------------------------


def endorse_only(*surfaces: str) -> dict:
    """A bundle endorsing surfaces without ranking them (ranking ⊆ endorsements)."""
    bundle = make_bundle()
    bundle["responses"][0]["blind"] = None
    bundle["responses"][0]["endorsements"] = [
        {"surface_form": s, "annotations": [], "comment": None} for s in surfaces
    ]
    bundle["responses"][0]["ranking"] = []
    bundle["responses"][0]["expansion"] = None
    return bundle


def validation_row(db_path: Path, surface: str) -> tuple:
    return q(
        db_path,
        "SELECT identifier_valid, nfkc_stable, nfkc_delta_class, script_consistent,"
        " collides_en_keyword, min_interpreter_ok FROM option_validations"
        " WHERE option_uid = ?",
        option_uid("elif-compound", "ur", surface),
    )[0]


def test_every_mechanical_gate_signal_is_cached_on_the_row(db_path: Path) -> None:
    # All five verdicts the canon gate reads, each tripped by a real surface.
    # Previously only identifier_valid was exercised, so four of the five could
    # have been inverted or hard-coded without a test noticing.
    result = importer(db_path).import_bundle(
        endorse_only(
            "ﻻ",  # NFKC-unstable (Arabic ligature) -> delta_class 'other'
            "ورنہfor",  # Latin embedded in an Urdu pack -> script-inconsistent
            "class",  # shadows an English keyword
            "ورنہ‍اگر",  # ZWJ: identifier-valid only on CPython 3.13+
            "ورنہ_اگر",  # clean control
        )
    )
    assert result.status == "accepted"  # rows are blocked, the session never is

    assert validation_row(db_path, "ﻻ")[1:3] == (0, "other")
    assert validation_row(db_path, "ورنہfor")[3] == 0
    assert validation_row(db_path, "class")[4] == 1
    assert validation_row(db_path, "ورنہ‍اگر")[5] == 0
    assert validation_row(db_path, "ورنہ_اگر") == (1, 1, None, 1, 0, 1)

    # Each failing row is named in the report so the maintainer sees it.
    gates = result.report["stages"][3]
    for surface in ("ﻻ", "ورنہfor", "class"):
        assert any(surface in str(d) for d in gates["details"]), surface
    # The ZWJ case is reported through repr(), which escapes the format
    # character to ‍ — the only way an invisible character is legible in
    # a terminal report. Assert the escape, not the raw codepoint.
    #
    # The report names the offending CODEPOINT rather than a mnemonic: the
    # 3.13-only set is the full 5,674-character delta, not the ZWJ/ZWNJ pair the
    # message was originally written for, and "uses ZWJ/ZWNJ" is a false
    # description of U+30FB KATAKANA MIDDLE DOT (CORE-1905).
    assert any("U+200D" in str(d) and "\\u200d" in str(d) for d in gates["details"])


def test_canon_refuses_every_mechanically_invalid_row(db_path: Path) -> None:
    # The point of caching the verdicts: the canon gate acts on them.
    importer(db_path).import_bundle(endorse_only("ﻻ", "ورنہfor"))
    conn = schema_v2.connect(db_path)
    for surface in ("ﻻ", "ورنہfor"):
        uid = option_uid("elif-compound", "ur", surface)
        conn.execute(
            "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
            " screen_version) VALUES (?, 'cleared', 'madi', 'manual-interim-v1')",
            (uid,),
        )
        with pytest.raises(sqlite3.IntegrityError, match="identifier/NFKC/script"):
            conn.execute(
                "INSERT INTO canon_selections(concept_id, locale, option_uid,"
                " surface_form, source_file) VALUES (1,'ur',?,?, 'libs/i18n/canon/ur.toml')",
                (uid, surface),
            )
    conn.close()


def test_endorsing_an_existing_word_still_records_the_elicited_signal(
    db_path: Path,
) -> None:
    # session_options.elicited is the ONLY record of blind-vs-after_reveal
    # ordering — the research signal the structured flow exists to collect —
    # and endorsing a word the corpus already holds is the common case.
    bundle = make_bundle()
    bundle["responses"][0]["blind"] = {"surface_form": "وگرنہ"}  # already an option
    bundle["responses"][0]["endorsements"] = []
    bundle["responses"][0]["ranking"] = ["وگرنہ"]
    bundle["responses"][0]["expansion"] = None
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "accepted"
    assert result.created_options == []  # nothing new was minted
    assert q(
        db_path,
        "SELECT elicited FROM session_options WHERE session_uid = ? AND option_uid = ?",
        result.session_uid,
        OPT_MODEL,
    ) == [("blind",)]


def test_a_bundle_cannot_promote_an_existing_contributors_rung(
    db_path: Path,
) -> None:
    # current_rung is exported to the public corpus and weights endorsements
    # (native_claimed 2.0 vs contributor 1.0). Nothing binds source_key to the
    # submitter, so a bundle naming someone else must not move their rung.
    conn = schema_v2.connect(db_path)
    conn.execute(
        "INSERT INTO contributors(id, current_rung) VALUES (?, 'contributor')",
        (REVIEWER_ID,),
    )
    conn.commit()
    conn.close()

    result = importer(db_path).import_bundle(make_bundle())  # claims native_claimed
    assert result.status == "accepted"
    assert q(
        db_path, "SELECT current_rung FROM contributors WHERE id = ?", REVIEWER_ID
    ) == [("contributor",)]
    # The claim is still recorded as session evidence, just not as authority.
    assert q(
        db_path,
        "SELECT rung_at_session FROM review_sessions WHERE uid = ?",
        result.session_uid,
    ) == [("contributor",)]


def test_a_structurally_invalid_bundle_mints_no_contributor_row(
    db_path: Path,
) -> None:
    # contributors rows publish to the corpus and carry no quarantine filter,
    # so a malformed bundle naming a fabricated username must not create one.
    bundle = make_bundle()
    del bundle["attestations"]
    bundle["contributor"]["source_key"] = "fabricated-person"
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "returned"
    assert counts(db_path)["contributors"] == 0
    assert counts(db_path)["review_sessions"] == 0


def test_a_semantically_invalid_bundle_still_records_the_returned_session(
    db_path: Path,
) -> None:
    # A well-formed bundle that breaks a semantic rule is a real submission by
    # a real person: the return is worth recording so it can be resumed.
    bundle = make_bundle()
    bundle["responses"][0]["ranking"] = ["توڑو"]
    assert importer(db_path).import_bundle(bundle).status == "returned"
    assert counts(db_path)["review_sessions"] == 1


def test_consent_already_on_file_is_never_rewritten_by_a_bundle(
    db_path: Path,
) -> None:
    # A bundle can name any source_key. Overwriting a stored credit preference
    # would manufacture the record that later authorizes publishing someone's
    # name -- so consent is written once and changed only by a maintainer.
    conn = schema_v2.connect(db_path)
    conn.execute("INSERT INTO contributors(id) VALUES (?)", (REVIEWER_ID,))
    conn.execute(
        "INSERT INTO contributor_identities(contributor_id, source_key,"
        " consent_version, consent_at, credit_preference, consent_public_credit)"
        " VALUES (?, ?, 'oss-pre-notice', '2026-01-01', 'anonymous', 0)",
        (REVIEWER_ID, REVIEWER),
    )
    conn.commit()
    conn.close()

    bundle = make_bundle()
    bundle["contributor"]["consent"] = {
        "consent_version": "1.0",
        "credit_preference": "name",
        "credit_text": "Someone Else",
    }
    result = importer(db_path).import_bundle(bundle)

    assert result.status == "accepted"  # the words still land
    assert q(
        db_path,
        "SELECT consent_version, credit_preference, consent_public_credit,"
        " display_name FROM contributor_identities WHERE contributor_id = ?",
        REVIEWER_ID,
    ) == [("oss-pre-notice", "anonymous", 0, None)]
    assert any(
        "already on file" in str(d) for d in result.report["stages"][2]["details"]
    )


def test_a_returned_reply_cannot_be_shaped_by_the_submitter(db_path: Path) -> None:
    # Report details quote surface forms verbatim, and --reply posts them under
    # the maintainer's account. A submitter must not be able to inject markdown
    # into a comment we are signing.
    bundle = make_bundle()
    bundle["responses"][0]["ranking"] = ["`</code>\n\n## Fake heading\n- [x] done"]
    reply = importer(db_path).import_bundle(bundle).reply_text()
    bullets = [line for line in reply.splitlines() if line.startswith("- ")]
    assert bullets, reply
    for line in bullets:
        # One inline code span per finding: the payload renders as literal text
        # rather than as markdown structure in a comment we are signing.
        assert line.startswith("- `") and line.endswith("`"), line
        assert line.count("`") == 2, line
    # Nothing the submitter wrote can start a line, so no heading, list item or
    # task box of theirs is ever rendered as markup.
    assert not any(
        line.lstrip().startswith(("#", "* ", "> ")) for line in reply.splitlines()
    ), reply


def test_the_conduct_screen_flags_bidi_controls_and_credit_text(
    db_path: Path,
) -> None:
    # Bidi is the injection smell that matters most for the RTL locales this
    # path targets; credit_text is free text like any other.
    bundle = make_bundle()
    bundle["responses"][0]["commentary"] = [
        {"topic": "general", "body": "innocuous‮txet desrever"}
    ]
    bundle["contributor"]["consent"] = {
        "consent_version": "1.0",
        "credit_preference": "name",
        "credit_text": "Someone <someone@example.com>",
    }
    result = importer(db_path).import_bundle(bundle)
    conduct = result.report["stages"][1]
    assert conduct["status"] == "warn"
    assert any("bidi" in str(d) for d in conduct["details"])
    assert any("credit_text" in str(d) for d in conduct["details"])
    assert result.needs_human_eyes


def test_credit_preference_name_writes_the_display_name(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["contributor"]["consent"] = {
        "consent_version": "1.0",
        "credit_preference": "name",
        "credit_text": "مدیحہ خان",
    }
    assert importer(db_path).import_bundle(bundle).status == "accepted"
    assert q(
        db_path,
        "SELECT credit_preference, display_name, consent_public_credit"
        " FROM contributor_identities WHERE contributor_id = ?",
        REVIEWER_ID,
    ) == [("name", "مدیحہ خان", 1)]


def test_credit_preference_name_without_a_name_is_returned(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["contributor"]["consent"] = {
        "consent_version": "1.0",
        "credit_preference": "name",
    }
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any("credit_text" in str(d) for d in result.report["stages"][2]["details"])


def test_a_returned_session_can_be_returned_again(db_path: Path) -> None:
    # The resuming branch of _returned: a second attempt at a still-broken
    # bundle refreshes the report on the existing row rather than colliding.
    bundle = make_bundle()
    bundle["responses"][0]["ranking"] = ["توڑو"]
    imp = importer(db_path)
    first = imp.import_bundle(bundle)
    second = imp.import_bundle(bundle)
    assert first.status == second.status == "returned"
    assert counts(db_path)["review_sessions"] == 1
    assert q(db_path, "SELECT status FROM review_sessions") == [("returned",)]


def test_an_unregistered_programming_language_is_returned(db_path: Path) -> None:
    result = importer(db_path).import_bundle(make_bundle(programming_language="cobol"))
    assert result.status == "returned"
    assert any("cobol" in str(d) for d in result.report["stages"][0]["details"])


def test_a_style_profile_session_may_not_carry_a_programming_language(
    db_path: Path,
) -> None:
    bundle = make_bundle(
        track="style_profile", programming_language="python", responses=[]
    )
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any("locale-wide" in str(d) for d in result.report["stages"][0]["details"])


def test_an_expansion_must_attach_to_an_endorsed_word(db_path: Path) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["expansion"] = {"for": "توڑو", "text": "توڑ دو"}
    result = importer(db_path).import_bundle(bundle)
    assert result.status == "returned"
    assert any("expansion" in str(d) for d in result.report["stages"][0]["details"])


def test_ingest_is_atomic_when_a_row_is_refused(
    db_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The CLI tells the contributor "nothing was written (the ingest is one
    # transaction)". That promise had no test behind it.
    from legesher_i18n.intake import pipeline as mod

    real = mod.commentary_uid

    def explode(*args: object, **kwargs: object) -> str:
        raise sqlite3.IntegrityError("simulated failure late in ingest")

    monkeypatch.setattr(mod, "commentary_uid", explode)
    with pytest.raises(sqlite3.IntegrityError):
        importer(db_path).import_bundle(make_bundle())
    monkeypatch.setattr(mod, "commentary_uid", real)

    # Nothing survives the rollback — not the session, not the options it had
    # already inserted before the failure.
    after = counts(db_path)
    assert after["review_sessions"] == 0
    assert after["endorsements"] == 0
    assert after["options"] == 1  # only the pre-seeded model candidate
    assert after["option_screenings"] == 0


def test_quality_warns_on_a_coinage_with_no_established_sibling(
    db_path: Path,
) -> None:
    # Previously asserted only `status in ("pass", "warn")` — the two values the
    # stage can produce. This exercises the branch itself.
    bundle = make_bundle()
    bundle["responses"][0]["concept"] = "break-loop"
    bundle["responses"][0]["blind"] = {
        "surface_form": "توڑو",
        "established_term": "coined",
    }
    bundle["responses"][0]["endorsements"] = []
    bundle["responses"][0]["ranking"] = ["توڑو"]
    bundle["responses"][0]["expansion"] = None
    bundle["responses"][0]["commentary"] = []
    result = importer(db_path).import_bundle(bundle)
    quality = result.report["stages"][4]
    assert quality["status"] == "warn"
    assert any("second-reviewer queue" in str(d) for d in quality["details"])


def test_quality_suggests_the_cognate_annotation_on_an_identity_rendering(
    db_path: Path,
) -> None:
    bundle = make_bundle()
    bundle["responses"][0]["blind"] = None
    bundle["responses"][0]["endorsements"] = [
        {"surface_form": "elif", "annotations": [], "comment": None}
    ]
    bundle["responses"][0]["ranking"] = []
    bundle["responses"][0]["expansion"] = None
    result = importer(db_path).import_bundle(bundle)
    quality = result.report["stages"][4]
    assert quality["status"] == "warn"
    assert any("cognate_loanword" in str(d) for d in quality["details"])
    # A suggestion, never a mandate: the row still lands.
    assert result.status == "accepted"
