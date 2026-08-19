"""The automated submission moderation gate (CORE-1797).

Boundary doctrine, from the ticket's gate design:

* every attack class the safety screen names is caught and ESCALATES
  (``held``) — homoglyph/confusable, bidi/invisible injection, wordlist hit,
  spam heuristics, rate limit; the gate never auto-rejects
* an option the gate withholds is invisible to rankings, other reviewers'
  views, and the corpus export — the CORE-1828 ``option_withheld`` predicate,
  unchanged
* trust tiering: a maintainer-verified stored rung fast-paths a CLEAN option
  to ``cleared``; it never skips a screen, and a bundle's self-claimed rung
  never counts
* the three open sub-decisions are config flags with conservative defaults:
  quarantine fully hidden, verdicts private, escalation to maintainers +
  certified rung-4s
* ``option_flags`` stays the post-hoc report channel and feeds re-screening
"""

from __future__ import annotations

import copy
import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from legesher_i18n.cli import cli
from legesher_i18n.db.schema_v2 import (
    apply_schema_v2,
    contributor_id,
    option_uid,
)
from legesher_i18n.intake.moderation import (
    AUTO_SCREEN_VERSION,
    AUTO_SCREENED_BY,
    LinguistOpinion,
    ModerationConfig,
    ModerationGate,
    OfflineLinguistReview,
    escalation_recipients,
    quarantined_uids_visible_to,
    skeleton,
)
from legesher_i18n.intake.pipeline import BundleImporter

SALT = "moderation-test-salt"
REVIEWER = "uk-reviewer"
REVIEWER_ID = contributor_id(REVIEWER, salt=SALT)

# Pre-seeded, honestly-Cyrillic community option ("друк") — the established
# word a homoglyph twin will try to impersonate.
ESTABLISHED = "друк"
OPT_ESTABLISHED = option_uid("break-loop", "uk", ESTABLISHED)

#: All-Cyrillic homoglyph of the English keyword ``pass``:
#: U+0440 U+0430 U+0455 U+0455 — script-consistent for Ukrainian, valid as an
#: identifier, NFKC-stable, and visually indistinguishable from the keyword.
KEYWORD_SPOOF = "раѕѕ"

#: ``друк`` with its Cyrillic ``р`` swapped for Latin ``p`` — a homoglyph twin
#: of the established option above.
TWIN_SPOOF = "дpук"


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "moderation.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    conn.executescript(
        f"""
        INSERT INTO programming_languages(code, name, status)
            VALUES ('python','Python','shipping');
        INSERT INTO locales(tag, language_subtag, name, native_name, direction, in_registry)
            VALUES ('uk','uk','Ukrainian','українська','ltr',1);
        INSERT INTO concepts(slug, definition_en, category) VALUES
            ('pass-noop','do nothing','control_flow'),
            ('break-loop','exit the nearest loop','control_flow');
        INSERT INTO terms(concept_id, programming_language, name, category)
            VALUES (1,'python','pass','keyword'), (2,'python','break','keyword');
        INSERT INTO options(uid, concept_id, locale, programming_language, surface_form)
            VALUES ('{OPT_ESTABLISHED}', 2, 'uk', NULL, '{ESTABLISHED}');
        INSERT INTO option_provenance(option_uid, source, contributor_id)
            VALUES ('{OPT_ESTABLISHED}', 'community', NULL);
        INSERT INTO option_validations(option_uid, validator_version, identifier_valid,
            nfkc_stable, script_consistent) VALUES ('{OPT_ESTABLISHED}','audit-v1',1,1,1);
        """
    )
    conn.commit()
    conn.close()
    return path


def make_bundle(surface: str, concept: str = "pass-noop", **overrides: object) -> dict:
    bundle = {
        "bundle_version": "1.0",
        "kit_version": "v2@2026-08-11+abc123",
        "locale": "uk",
        "track": "reserved_words",
        "contributor": {
            "source_key": REVIEWER,
            "claimed_rung": "native_claimed",
            "consent": {"consent_version": "1.0", "credit_preference": "handle"},
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
                "concept": concept,
                "blind": {
                    "surface_form": surface,
                    "word_form": "noun",
                    "established_term": "established",
                    "rationale": "common word",
                },
                "endorsements": [],
                "ranking": [surface],
                "flags": [],
            }
        ],
        "session": {"started_at": "2026-08-15T09:00:00Z", "durations_ms": {}},
    }
    bundle.update(copy.deepcopy(overrides))  # type: ignore[arg-type]
    return bundle


def importer(db_path: Path, **kwargs: object) -> BundleImporter:
    kwargs.setdefault("moderation", ModerationGate(ModerationConfig()))
    return BundleImporter(db_path, salt=SALT, **kwargs)  # type: ignore[arg-type]


def q(db_path: Path, sql: str, *args: object) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return rows


def verdict_of(db_path: Path, uid: str) -> tuple:
    rows = q(
        db_path,
        "SELECT verdict, screened_by, screen_version, note"
        " FROM option_screening_status WHERE option_uid = ?",
        uid,
    )
    assert rows, f"no screening verdict recorded for {uid}"
    return rows[0]


def promote(db_path: Path, rung: str, cid: str = REVIEWER_ID) -> None:
    """Maintainer act: store a verified rung for the contributor."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO contributors(id, current_rung) VALUES (?, ?)"
        " ON CONFLICT(id) DO UPDATE SET current_rung = excluded.current_rung",
        (cid, rung),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# the attack classes, one by one — each caught, each ESCALATED, none rejected
# ---------------------------------------------------------------------------


def test_bidi_control_in_surface_is_held(db_path: Path) -> None:
    result = importer(db_path).import_bundle(make_bundle("тест\u202eабв"))
    assert result.status == "accepted"  # evidence ingests; visibility does not
    (uid,) = result.created_options
    verdict, by, version, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert (by, version) == (AUTO_SCREENED_BY, AUTO_SCREEN_VERSION)
    assert "bidi control U+202E" in note
    assert result.option_verdicts[uid] == "held"
    assert result.needs_human_eyes


def test_invisible_character_in_surface_is_held(db_path: Path) -> None:
    # U+034F COMBINING GRAPHEME JOINER: renders as nothing, isidentifier-True,
    # NFKC-stable, script Inherited — every mechanical gate passes it.
    result = importer(db_path).import_bundle(make_bundle("тест\u034fове"))
    (uid,) = result.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert "invisible/format character U+034F" in note


def test_confusable_keyword_spoof_is_held(db_path: Path) -> None:
    """All-Cyrillic ``раѕѕ`` passes every mechanical gate and spells ``pass``."""
    result = importer(db_path).import_bundle(make_bundle(KEYWORD_SPOOF))
    (uid,) = result.created_options
    # The mechanical suite really did pass it — that is why the gate exists.
    assert q(
        db_path,
        "SELECT identifier_valid, nfkc_stable, script_consistent,"
        " collides_en_keyword FROM option_validations WHERE option_uid = ?",
        uid,
    ) == [(1, 1, 1, 0)]
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert "'pass'" in note and "homoglyph" in note


def test_homoglyph_twin_of_established_option_is_held(db_path: Path) -> None:
    result = importer(db_path).import_bundle(
        make_bundle(TWIN_SPOOF, concept="break-loop")
    )
    (uid,) = result.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert OPT_ESTABLISHED in note and "homoglyph twin" in note


def test_wordlist_hit_on_surface_is_held(db_path: Path, tmp_path: Path) -> None:
    wordlists = tmp_path / "wordlists"
    wordlists.mkdir()
    (wordlists / "uk.txt").write_text("# private list\nдурень\n", encoding="utf-8")
    gate = ModerationGate(ModerationConfig(wordlist_dir=wordlists))
    result = importer(db_path, moderation=gate).import_bundle(make_bundle("дурень"))
    (uid,) = result.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert "wordlist hit" in note and "never a verdict" in note


def test_wordlist_matching_is_word_boundary_aware() -> None:
    """`ass` on a list must not flag `class` — the substring trap is real."""
    gate = ModerationGate(ModerationConfig())
    gate._wordlists["en"] = frozenset({"ass"})
    assert gate._wordlist_findings("class", "en") == []
    assert gate._wordlist_findings("pass_holder", "en") == []
    assert gate._wordlist_findings("dumb_ass", "en") != []
    assert gate._wordlist_findings("ass", "en") != []


def test_spam_heuristics_hold_absurd_surfaces(db_path: Path) -> None:
    run = importer(db_path).import_bundle(make_bundle("б" * 8))
    (uid,) = run.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert "spam heuristic" in note

    long = importer(db_path).import_bundle(
        make_bundle("довгеслово" * 5, concept="break-loop")
    )
    (uid2,) = long.created_options
    verdict2, _, _, note2 = verdict_of(db_path, uid2)
    assert verdict2 == "held"
    assert "spam heuristic" in note2


def test_rate_limit_escalates_everything_the_session_mints(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO contributors(id, current_rung) VALUES (?, 'contributor')",
        (REVIEWER_ID,),
    )
    for i in range(5):
        digest = f"{i:x}" * 64  # distinct in the uid-bearing first 24 chars
        conn.execute(
            "INSERT INTO review_sessions(uid, contributor_id, locale, track,"
            " method, kit_version, rung_at_session, bundle_digest, status)"
            " VALUES (?, ?, 'uk', 'reserved_words', 'portal', 'v2',"
            " 'contributor', ?, 'accepted')",
            (f"ses_{digest[:24]}", REVIEWER_ID, digest),
        )
    conn.commit()
    conn.close()

    result = importer(db_path).import_bundle(make_bundle("злива"))
    (uid,) = result.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert "rate limit" in note


def test_linguist_concern_is_held_and_offline_default_blocks_nothing(
    db_path: Path,
) -> None:
    class Concerned:
        def review(self, surface: str, locale: str, concept_slug: str):
            return LinguistOpinion("concern", "reads as a slur in dialect X")

    gate = ModerationGate(ModerationConfig(), linguist=Concerned())
    result = importer(db_path, moderation=gate).import_bundle(make_bundle("слово"))
    (uid,) = result.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert "linguist review raised a concern" in note

    # The offline default records its absence and blocks nothing.
    offline = importer(db_path).import_bundle(
        make_bundle("слово", concept="break-loop")
    )
    (uid2,) = offline.created_options
    verdict2, _, _, note2 = verdict_of(db_path, uid2)
    assert verdict2 == "quarantined"
    assert "linguist model screen not configured" in note2
    assert OfflineLinguistReview().review("x", "uk", "y").opinion == "unavailable"


# ---------------------------------------------------------------------------
# quarantine/held exclusion — rankings, other views, corpus export predicate
# ---------------------------------------------------------------------------


def test_withheld_options_are_excluded_from_rankings_views_and_export(
    db_path: Path,
) -> None:
    held = importer(db_path).import_bundle(make_bundle(KEYWORD_SPOOF))
    quarantined = importer(db_path).import_bundle(
        make_bundle("слово", concept="break-loop")
    )
    (held_uid,) = held.created_options
    (quar_uid,) = quarantined.created_options
    assert verdict_of(db_path, held_uid)[0] == "held"
    assert verdict_of(db_path, quar_uid)[0] == "quarantined"

    for uid in (held_uid, quar_uid):
        # Invisible to standings (rankings and everything built on them)…
        assert q(
            db_path, "SELECT COUNT(*) FROM option_standings WHERE option_uid=?", uid
        ) == [(0,)]
        # …to the terminology/reviewer lens…
        assert q(
            db_path,
            "SELECT COUNT(*) FROM terminology_export t JOIN options o"
            " ON o.surface_form = t.surface_form AND o.locale = t.locale"
            " WHERE o.uid = ?",
            uid,
        ) == [(0,)]
        # …and withheld from the corpus export by the one predicate the
        # exporter queries (option_withheld; see scripts/export_corpus.py).
        assert q(
            db_path, "SELECT COUNT(*) FROM option_withheld WHERE option_uid=?", uid
        ) == [(1,)]
    # The established, unscreened option is untouched (pre-intake default).
    assert q(
        db_path,
        "SELECT COUNT(*) FROM option_standings WHERE option_uid=?",
        OPT_ESTABLISHED,
    ) == [(1,)]


# ---------------------------------------------------------------------------
# trust tiering — fast path by STORED rung, never unscreened, claims don't count
# ---------------------------------------------------------------------------


def test_certified_stored_rung_fast_paths_a_clean_option(db_path: Path) -> None:
    promote(db_path, "certified")
    result = importer(db_path).import_bundle(make_bundle("слово"))
    (uid,) = result.created_options
    verdict, by, version, note = verdict_of(db_path, uid)
    assert verdict == "cleared"
    assert (by, version) == (AUTO_SCREENED_BY, AUTO_SCREEN_VERSION)
    assert "fast path" in note
    # Cleared means competing: visible in standings immediately.
    assert q(
        db_path, "SELECT COUNT(*) FROM option_standings WHERE option_uid=?", uid
    ) == [(1,)]
    assert result.option_verdicts[uid] == "cleared"
    # The contributor reply says so honestly.
    assert "released them immediately" in result.reply_text()


def test_fast_path_is_never_unscreened(db_path: Path) -> None:
    """A certified submitter's homoglyph spoof is HELD, not cleared."""
    promote(db_path, "certified")
    result = importer(db_path).import_bundle(make_bundle(KEYWORD_SPOOF))
    (uid,) = result.created_options
    assert verdict_of(db_path, uid)[0] == "held"


def test_palochka_and_ka_confusables_cannot_fast_path(db_path: Path) -> None:
    """PR #161 review finding: U+04CF (palochka → l) and U+043A (ka → k) were
    missing from the confusable map, so an all-Cyrillic ``сӏаѕѕ`` from a
    stored rung-4 contributor would have fast-pathed straight to cleared."""
    promote(db_path, "certified")
    spoof = "сӏаѕѕ"  # с ӏ а ѕ ѕ — renders as `class`
    result = importer(db_path).import_bundle(make_bundle(spoof))
    (uid,) = result.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert "'class'" in note and "homoglyph" in note
    assert q(
        db_path, "SELECT COUNT(*) FROM option_standings WHERE option_uid=?", uid
    ) == [(0,)]


def test_mechanical_failure_never_fast_paths(db_path: Path) -> None:
    """Clean of safety findings but script-inconsistent: quarantine, not clear."""
    promote(db_path, "certified")
    # Latin-script word in a Cyrillic locale: script-inconsistent (mechanical
    # warn, ingests as evidence) and no safety finding of its own.
    result = importer(db_path).import_bundle(make_bundle("wordlike"))
    (uid,) = result.created_options
    verdict, _, _, note = verdict_of(db_path, uid)
    assert verdict == "quarantined"
    assert "mechanical gate failures" in note


def test_claimed_rung_never_fast_paths_a_first_time_contributor(
    db_path: Path,
) -> None:
    """No stored rung → rank 0 for the gate, whatever the bundle claims."""
    result = importer(db_path).import_bundle(make_bundle("слово"))
    (uid,) = result.created_options
    assert verdict_of(db_path, uid)[0] == "quarantined"


def test_low_stored_rung_stays_quarantined(db_path: Path) -> None:
    promote(db_path, "native_verified")  # rank 3 < fast_path_min_rank 4
    result = importer(db_path).import_bundle(make_bundle("слово"))
    (uid,) = result.created_options
    assert verdict_of(db_path, uid)[0] == "quarantined"


# ---------------------------------------------------------------------------
# the three open sub-decisions — config flags, conservative defaults
# ---------------------------------------------------------------------------


def test_conservative_defaults() -> None:
    config = ModerationConfig()
    assert config.quarantine_visibility == "hidden"
    assert config.export_verdicts is False
    assert config.escalation_policy == "maintainer_and_certified"
    assert config.fast_path_min_rank == 4


def test_from_env_overrides_without_a_rebuild() -> None:
    config = ModerationConfig.from_env(
        {
            "LEGESHER_MODERATION_QUARANTINE_VISIBILITY": "submitter_only",
            "LEGESHER_MODERATION_EXPORT_VERDICTS": "true",
            "LEGESHER_MODERATION_ESCALATION": "maintainer_only",
            "LEGESHER_MODERATION_FAST_PATH_MIN_RANK": "5",
        }
    )
    assert config.quarantine_visibility == "submitter_only"
    assert config.export_verdicts is True
    assert config.escalation_policy == "maintainer_only"
    assert config.fast_path_min_rank == 5
    assert ModerationConfig.from_env({}).quarantine_visibility == "hidden"
    with pytest.raises(ValueError):
        ModerationConfig.from_env({"LEGESHER_MODERATION_ESCALATION": "everyone"})
    with pytest.raises(ValueError):
        ModerationConfig(quarantine_visibility="public")


def test_quarantine_visibility_flag_governs_the_submitter_view(
    db_path: Path,
) -> None:
    result = importer(db_path).import_bundle(make_bundle("слово"))
    (uid,) = result.created_options
    conn = sqlite3.connect(db_path)
    try:
        hidden = ModerationConfig()
        greyed = ModerationConfig(quarantine_visibility="submitter_only")
        # Conservative default: nobody sees quarantine — not even the submitter.
        assert quarantined_uids_visible_to(conn, REVIEWER_ID, hidden) == []
        # Flipped: the submitter sees their OWN pending option…
        assert quarantined_uids_visible_to(conn, REVIEWER_ID, greyed) == [uid]
        # …other reviewers and anonymous viewers still see nothing.
        other = contributor_id("someone-else", salt=SALT)
        assert quarantined_uids_visible_to(conn, other, greyed) == []
        assert quarantined_uids_visible_to(conn, None, greyed) == []
    finally:
        conn.close()


def test_escalation_recipients_follow_the_policy_flag(db_path: Path) -> None:
    maintainer = contributor_id("madi", salt=SALT)
    certified = contributor_id("trusted-r4", salt=SALT)
    promote(db_path, "maintainer", maintainer)
    promote(db_path, "certified", certified)
    promote(db_path, "native_verified", REVIEWER_ID)
    conn = sqlite3.connect(db_path)
    try:
        both = escalation_recipients(conn, ModerationConfig())
        assert sorted([maintainer, certified]) == both
        only = escalation_recipients(
            conn, ModerationConfig(escalation_policy="maintainer_only")
        )
        assert only == [maintainer]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# option_flags feeds re-screening
# ---------------------------------------------------------------------------


def test_rescreen_flagged_pulls_a_visible_flagged_option_back(db_path: Path) -> None:
    promote(db_path, "certified")
    result = importer(db_path).import_bundle(make_bundle("слово"))
    (uid,) = result.created_options
    assert verdict_of(db_path, uid)[0] == "cleared"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO option_flags(option_uid, contributor_id, reason, note)"
        " VALUES (?, NULL, 'offensive', 'reads badly in dialect X')",
        (uid,),
    )
    conn.commit()
    conn.close()

    runner = CliRunner()
    dry = runner.invoke(cli, ["rescreen-flagged", "--dry-run", "--db", str(db_path)])
    assert dry.exit_code == 0, dry.output
    assert uid in dry.output and "dry run" in dry.output
    assert verdict_of(db_path, uid)[0] == "cleared"  # dry run wrote nothing

    wet = runner.invoke(cli, ["rescreen-flagged", "--db", str(db_path)])
    assert wet.exit_code == 0, wet.output
    verdict, by, version, note = verdict_of(db_path, uid)
    assert verdict == "held"
    assert (by, version) == (AUTO_SCREENED_BY, AUTO_SCREEN_VERSION)
    assert "offensive" in note
    # Withdrawn from rankings again, pending a human.
    assert q(
        db_path, "SELECT COUNT(*) FROM option_standings WHERE option_uid=?", uid
    ) == [(0,)]


# ---------------------------------------------------------------------------
# skeleton unit behaviour
# ---------------------------------------------------------------------------


def test_skeleton_folds_the_classic_attack_alphabet() -> None:
    assert skeleton(KEYWORD_SPOOF) == "pass"
    assert skeleton("i\u202ef") == "if"  # bidi control renders as nothing
    assert skeleton("ｉｆ") == "if"  # fullwidth folds via NFKC
    assert skeleton("друк") == skeleton(TWIN_SPOOF)
    assert skeleton("слово") != "pass"
    # PR #161 review finding: palochka (U+04CF; capital U+04C0 casefolds to
    # it) and Cyrillic ka (U+043A) are genuine UTS-39 confusables.
    assert skeleton("сӏаѕѕ") == "class"
    assert skeleton("сӀаѕѕ") == "class"  # capital palochka, via casefold
    assert skeleton("к") == "k"
