"""The intake-layer carry-forward across a v2 rebuild (CORE-2052).

``migrate_to_v2.py`` rebuilds v2 from v1, and the intake layer is not
reconstructible from v1 — the importer writes community options, their
provenance, validations, endorsements, contributors, sessions, commentary and
screening verdicts straight into v2. These tests pin the contract of
``scripts/carry_forward_screenings.py`` on small fixture databases — never
the real ones:

* the carry is EXACT — community options travel with their whole closure,
  concept ids are remapped through slugs (they renumber across rebuilds),
  and screening rows keep their original ids so the latest-row-wins verdict
  semantics survive;
* a re-run is a reported no-op, verdicts appended in the source since the
  last carry travel as a delta, and later local verdicts in the target do
  not disturb a no-op;
* every refusal path refuses, before any write: a screening-schema version
  mismatch (stating both versions, transitively fingerprinted), a
  contributor-salt mismatch, a missing option that is absent from both the
  rebuild and the carried set, a target with a conflicting screening
  history, a non-cleared history for a canon-selected option, a source
  table the script has no carry policy for, messages-partition endorsements,
  and a reference-layer gap (an unregistered locale);
* ``--dry-run`` writes nothing.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import (
    apply_schema_v2,
    connect,
    option_uid,
)
from scripts.carry_forward_screenings import main, screening_schema_fingerprint

SALT_FP = "fp-test-0123456789ab"

OPT_V1 = option_uid("break-loop", "uk", "перерва")  # exists in v1 AND was screened
OPT_COMMUNITY = option_uid("pass-noop", "uk", "друк")  # intake-created, cleared
OPT_REJECTED = option_uid("pass-noop", "uk", "слово")  # intake-created, rejected

CONTRIB_V1 = "c_" + "a1" * 8
CONTRIB_NEW = "c_" + "b2" * 8
END_V1 = "end_" + "c3" * 12
END_NEW = "end_" + "d4" * 12
SESSION = "ses_" + "1a" * 12  # ses_ + digest[:24], enforced by CHECK
COMMENT = "com_" + "f6" * 12

#: The source screening history, in id order. OPT_V1 and OPT_COMMUNITY are
#: quarantined then cleared, OPT_REJECTED quarantined then rejected — so the
#: fixture exercises multi-event histories where the LATEST verdict differs
#: from the first.
SOURCE_HISTORY: tuple[tuple[int, str, str, str, str | None], ...] = (
    (1, OPT_V1, "quarantined", "importer", None),
    (2, OPT_COMMUNITY, "quarantined", "importer", None),
    (3, OPT_V1, "cleared", "madi", "import ritual 2026-08-18"),
    (4, OPT_COMMUNITY, "cleared", "madi", None),
    (5, OPT_REJECTED, "quarantined", "importer", None),
    (6, OPT_REJECTED, "rejected", "madi", "keyboard mash"),
)

#: Stamp for every fixture column the schema defaults to ``datetime('now')``.
#: Both databases must be byte-equal except for what a test changes on
#: purpose; a default taken at insert time differs whenever the two fixtures
#: straddle a second boundary, and the carry-forward rightly refuses a row
#: that differs at the same key (CORE-2537).
STAMP = "2026-02-02T00:00:00Z"

#: Tables the carry moves wholesale; used to assert the full closure landed.
INTAKE_ROWS_EXPECTED = {
    "review_sessions": 1,
    "session_options": 1,
    "session_endorsements": 1,
    "session_rankings": 1,
    "concept_commentary": 1,
    "commentary_moderation": 1,
}


def _build_base(
    path: Path,
    *,
    concepts_reversed: bool = False,
    joined_at: str = "2026-01-01T00:00:00Z",
) -> None:
    """Reference layer + the v1-derived rows both databases share.

    ``joined_at`` is parameterized because the real migration re-stamps it
    with ``datetime('now')`` on every rebuild — one test builds the target
    with a different value to pin that this is NOT treated as divergence.
    The endorsement ``created_at`` is fixed on both sides because the real
    migration carries it verbatim from v1 (it feeds the frozen uid formula).
    """
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    concepts = [
        ("break-loop", "exit the nearest loop"),
        ("pass-noop", "do nothing"),
    ]
    if concepts_reversed:  # integer concept ids differ between the two DBs
        concepts.reverse()
    conn.executescript(
        """
        INSERT INTO programming_languages(code, name, status)
            VALUES ('python','Python','shipping');
        INSERT INTO locales(tag, language_subtag, name, native_name, direction,
            in_registry) VALUES ('uk','uk','Ukrainian','українська','ltr',1);
        """
    )
    for slug, definition in concepts:
        conn.execute(
            "INSERT INTO concepts(slug, definition_en, category)"
            " VALUES (?, ?, 'control_flow')",
            (slug, definition),
        )
    conn.execute(
        "INSERT INTO build_meta(key, value) VALUES ('salt_fingerprint', ?)",
        (SALT_FP,),
    )
    # The v1-derived layer a rebuild reproduces: one contributor, one option
    # with provenance + validation, one endorsement.
    conn.execute(
        "INSERT INTO contributors(id, current_rung, joined_at)"
        " VALUES (?, 'contributor', ?)",
        (CONTRIB_V1, joined_at),
    )
    _add_option(conn, OPT_V1, "break-loop", "перерва", provenance="legesher")
    conn.execute(
        "INSERT INTO endorsements(uid, option_uid, contributor_id, method,"
        " rung_at_endorsement, created_at)"
        " VALUES (?, ?, ?, 'import', 'contributor', '2025-11-05T12:00:00Z')",
        (END_V1, OPT_V1, CONTRIB_V1),
    )
    conn.commit()
    conn.close()


def _add_option(
    conn: sqlite3.Connection,
    uid: str,
    slug: str,
    surface: str,
    *,
    provenance: str = "community",
) -> None:
    concept_id = conn.execute(
        "SELECT id FROM concepts WHERE slug = ?", (slug,)
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO options(uid, concept_id, locale, programming_language,"
        " surface_form, first_seen_at) VALUES (?, ?, 'uk', NULL, ?, ?)",
        (uid, concept_id, surface, STAMP),
    )
    conn.execute(
        "INSERT INTO option_provenance(option_uid, source, contributor_id,"
        " created_at) VALUES (?, ?, NULL, ?)",
        (uid, provenance, STAMP),
    )
    conn.execute(
        "INSERT INTO option_validations(option_uid, validator_version,"
        " identifier_valid, nfkc_stable, script_consistent, format_chars_clean,"
        " checked_at) VALUES (?, 'audit-v1', 1, 1, 1, 1, ?)",
        (uid, STAMP),
    )


def _add_intake_layer(path: Path) -> None:
    """The community rows only the intake path writes — source-side only."""
    conn = connect(path)
    conn.execute(
        "INSERT INTO contributors(id, current_rung, joined_at)"
        " VALUES (?, 'contributor', ?)",
        (CONTRIB_NEW, STAMP),
    )
    conn.execute(
        "INSERT INTO contributor_identities(contributor_id, source_key,"
        " consent_public_credit, credit_preference)"
        " VALUES (?, 'newcomer', 1, 'anonymous')",
        (CONTRIB_NEW,),
    )
    _add_option(conn, OPT_COMMUNITY, "pass-noop", "друк")
    _add_option(conn, OPT_REJECTED, "pass-noop", "слово")
    conn.execute(
        "INSERT INTO endorsements(uid, option_uid, contributor_id, method,"
        " rung_at_endorsement, created_at)"
        " VALUES (?, ?, ?, 'github', 'contributor', ?)",
        (END_NEW, OPT_COMMUNITY, CONTRIB_NEW, STAMP),
    )
    concept_id = conn.execute(
        "SELECT id FROM concepts WHERE slug = 'pass-noop'"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO review_sessions(uid, contributor_id, locale, track,"
        " method, kit_version, rung_at_session, bundle_digest, submitted_at)"
        " VALUES (?, ?, 'uk', 'reserved_words', 'github', 'v2@test',"
        " 'contributor', ?, ?)",
        (SESSION, CONTRIB_NEW, "1a" * 32, STAMP),
    )
    conn.execute(
        "INSERT INTO session_options(session_uid, option_uid, elicited)"
        " VALUES (?, ?, 'blind')",
        (SESSION, OPT_COMMUNITY),
    )
    conn.execute(
        "INSERT INTO session_endorsements(session_uid, endorsement_uid) VALUES (?, ?)",
        (SESSION, END_NEW),
    )
    conn.execute(
        "INSERT INTO session_rankings(session_uid, concept_id, locale,"
        " programming_language, option_uid, rank)"
        " VALUES (?, ?, 'uk', NULL, ?, 1)",
        (SESSION, concept_id, OPT_COMMUNITY),
    )
    conn.execute(
        "INSERT INTO concept_commentary(uid, contributor_id, session_uid,"
        " concept_id, locale, topic, body, created_at)"
        " VALUES (?, ?, ?, ?, 'uk', 'general', 'a note', ?)",
        (COMMENT, CONTRIB_NEW, SESSION, concept_id, STAMP),
    )
    conn.execute(
        "INSERT INTO commentary_moderation(commentary_uid, status)"
        " VALUES (?, 'pending')",
        (COMMENT,),
    )
    # screened_at pinned: two fixture builds straddling a clock tick must not
    # read as divergent histories.
    conn.executemany(
        "INSERT INTO option_screenings(id, option_uid, verdict, screened_by,"
        " screen_version, note, screened_at)"
        " VALUES (?, ?, ?, ?, 'manual-interim-v1', ?, '2026-08-18T09:00:00Z')",
        SOURCE_HISTORY,
    )
    conn.commit()
    conn.close()


def _rows(path: Path, table: str = "option_screenings") -> list[tuple]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        if table == "option_screenings":
            return conn.execute(
                "SELECT id, option_uid, verdict, screened_by, screen_version,"
                " note FROM option_screenings ORDER BY id"
            ).fetchall()
        return conn.execute(f"SELECT * FROM {table}").fetchall()  # nosec B608
    finally:
        conn.close()


def _count(path: Path, table: str) -> int:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # nosec B608
    finally:
        conn.close()


def _latest_verdicts(path: Path) -> dict[str, str]:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return dict(
            conn.execute("SELECT option_uid, verdict FROM option_screening_status")
        )
    finally:
        conn.close()


@pytest.fixture()
def source_db(tmp_path: Path) -> Path:
    path = tmp_path / "durable_v2.db"
    _build_base(path)
    _add_intake_layer(path)
    return path


@pytest.fixture()
def target_db(tmp_path: Path) -> Path:
    # Concepts inserted in the opposite order: same slugs, DIFFERENT integer
    # ids — the remap is exercised by every full-carry test.
    path = tmp_path / "fresh_v2.db"
    _build_base(path, concepts_reversed=True)
    return path


def _run(source: Path, target: Path, *extra: str) -> int:
    return main(["--source", str(source), "--target", str(target), *extra])


class TestFullCarry:
    def test_intake_layer_travels_whole(self, source_db, target_db, capsys):
        assert _run(source_db, target_db) == 0
        assert _rows(target_db) == _rows(source_db)
        assert _latest_verdicts(target_db) == {
            OPT_V1: "cleared",
            OPT_COMMUNITY: "cleared",
            OPT_REJECTED: "rejected",
        }
        for table, expected in INTAKE_ROWS_EXPECTED.items():
            assert _count(target_db, table) == expected, table
        assert _count(target_db, "options") == 3
        assert _count(target_db, "contributors") == 2
        assert _count(target_db, "contributor_identities") == 1
        assert _count(target_db, "endorsements") == 2
        out = capsys.readouterr().out
        assert "cleared 2  quarantined 3  held 0  rejected 1  total 6" in out
        assert "carried options: 2" in out
        assert "carried option_screenings: 6" in out

    def test_concept_ids_are_remapped_through_slugs(self, source_db, target_db):
        _run(source_db, target_db)
        conn = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True)
        slug = conn.execute(
            "SELECT c.slug FROM options o JOIN concepts c ON c.id = o.concept_id"
            " WHERE o.uid = ?",
            (OPT_COMMUNITY,),
        ).fetchone()[0]
        ranked_slug = conn.execute(
            "SELECT c.slug FROM session_rankings r JOIN concepts c"
            " ON c.id = r.concept_id WHERE r.option_uid = ?",
            (OPT_COMMUNITY,),
        ).fetchone()[0]
        conn.close()
        assert slug == "pass-noop"
        assert ranked_slug == "pass-noop"

    def test_rebuild_restamped_timestamps_are_not_divergence(self, source_db, tmp_path):
        # The migration writes contributors without joined_at, so every
        # rebuild re-stamps it with datetime('now'). That is build noise;
        # refusing on it would block every legitimate carry.
        target = tmp_path / "restamped.db"
        _build_base(target, concepts_reversed=True, joined_at="2026-09-01T09:00:00Z")
        assert _run(source_db, target) == 0
        assert _rows(target) == _rows(source_db)

    def test_source_is_not_written(self, source_db, target_db):
        before = {t: _rows(source_db, t) for t in ("options", "option_screenings")}
        _run(source_db, target_db)
        assert {t: _rows(source_db, t) for t in before} == before

    def test_dry_run_writes_nothing(self, source_db, target_db, capsys):
        assert _run(source_db, target_db, "--dry-run") == 0
        assert _rows(target_db) == []
        assert _count(target_db, "options") == 1
        assert "would be carried; nothing written" in capsys.readouterr().out


class TestIdempotency:
    def test_rerun_is_a_reported_noop(self, source_db, target_db, capsys):
        _run(source_db, target_db)
        capsys.readouterr()
        assert _run(source_db, target_db) == 0
        assert _rows(target_db) == _rows(source_db)
        out = capsys.readouterr().out
        assert "already carried forward" in out
        assert "nothing to do" in out

    def test_source_delta_travels_on_rerun(self, source_db, target_db, capsys):
        _run(source_db, target_db)
        conn = connect(source_db)
        conn.execute(
            "INSERT INTO option_screenings(id, option_uid, verdict, screened_by,"
            " screen_version, note) VALUES (7, ?, 'held', 'madi',"
            " 'manual-interim-v1', 'flagged after the fact')",
            (OPT_COMMUNITY,),
        )
        conn.commit()
        conn.close()
        capsys.readouterr()
        assert _run(source_db, target_db) == 0
        assert "carried option_screenings: 1" in capsys.readouterr().out
        assert _latest_verdicts(target_db)[OPT_COMMUNITY] == "held"

    def test_later_local_verdicts_do_not_disturb_the_noop(
        self, source_db, target_db, capsys
    ):
        _run(source_db, target_db)
        # A verdict recorded in the TARGET after the carry, above the source's
        # high-water mark, is a newer local event — not divergence.
        conn = connect(target_db)
        conn.execute(
            "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
            " screen_version, note) VALUES (?, 'cleared', 'madi',"
            " 'manual-interim-v1', 'native reviewer endorsed')",
            (OPT_COMMUNITY,),
        )
        conn.commit()
        conn.close()
        capsys.readouterr()
        assert _run(source_db, target_db) == 0
        assert "already carried forward" in capsys.readouterr().out
        assert len(_rows(target_db)) == len(SOURCE_HISTORY) + 1


class TestRefusals:
    def test_schema_version_mismatch_states_both_versions(self, source_db, target_db):
        conn = connect(target_db)
        conn.executescript(
            "DROP VIEW option_withheld;"
            "CREATE VIEW option_withheld AS"
            " SELECT option_uid, verdict FROM option_screening_status;"
        )
        conn.commit()
        src_fp, _ = screening_schema_fingerprint(
            sqlite3.connect(f"file:{source_db}?mode=ro", uri=True)
        )
        tgt_fp, _ = screening_schema_fingerprint(conn)
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        message = str(refusal.value)
        assert "REFUSED: screening-schema version mismatch" in message
        assert src_fp in message and tgt_fp in message
        assert "option_withheld" in message
        assert "scratch copy" in message.lower()
        assert _rows(target_db) == []

    def test_fingerprint_reaches_transitive_consumers(self, source_db, target_db):
        # The reviewer's attack on the one-hop set: option_promotion_status
        # reads the verdict only THROUGH option_standings. Gutting it must
        # change the version.
        conn = connect(target_db)
        conn.executescript(
            "DROP VIEW option_promotion_status;"
            "CREATE VIEW option_promotion_status AS"
            " SELECT uid AS option_uid, 1 AS canon_eligible FROM options;"
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        message = str(refusal.value)
        assert "REFUSED: screening-schema version mismatch" in message
        assert "option_promotion_status" in message

    def test_salt_fingerprint_mismatch_refuses(self, source_db, tmp_path):
        target = tmp_path / "wrong_salt.db"
        _build_base(target, concepts_reversed=True)
        conn = sqlite3.connect(target)
        conn.execute(
            "UPDATE build_meta SET value = 'fp-other' WHERE key = 'salt_fingerprint'"
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target)
        message = str(refusal.value)
        assert "contributor-salt fingerprint mismatch" in message
        assert SALT_FP in message and "fp-other" in message

    def test_missing_option_not_community_sourced_refuses(self, target_db, tmp_path):
        # A screened option absent from the target whose provenance says v1
        # ('legesher') — the rebuild DROPPED it; carrying would paper over a
        # migration bug.
        source = tmp_path / "dropped.db"
        _build_base(source)
        conn = connect(source)
        dropped = option_uid("pass-noop", "uk", "загублене")
        _add_option(conn, dropped, "pass-noop", "загублене", provenance="legesher")
        conn.execute(
            "INSERT INTO option_screenings(option_uid, verdict, screened_by,"
            " screen_version) VALUES (?, 'cleared', 'madi', 'manual-interim-v1')",
            (dropped,),
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source, target_db)
        message = str(refusal.value)
        assert "NOT exclusively community-sourced" in message
        assert dropped in message
        assert "absent from both" in message.lower()
        assert _rows(target_db) == []

    def test_conflicting_target_history_refuses(self, source_db, target_db):
        _add_intake_layer(target_db)  # same ids, but…
        conn = connect(target_db)
        conn.execute("DROP TRIGGER trg_screenings_append_only")
        conn.execute(
            "UPDATE option_screenings SET screened_by = 'someone-else' WHERE id = 3"
        )
        conn.commit()
        conn.close()
        # Reinstalling the trigger keeps the schema fingerprints equal.
        conn = connect(target_db)
        conn.execute(
            "CREATE TRIGGER trg_screenings_append_only "
            "BEFORE UPDATE ON option_screenings "
            "BEGIN SELECT RAISE(ABORT, 'option_screenings are append-only: "
            "write a new verdict'); END"
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        assert "conflicts with the source at id(s) 3" in str(refusal.value)

    def test_canon_selected_option_with_noncleared_history_refuses(
        self, source_db, target_db
    ):
        # OPT_V1 exists in the target and is canon-selected there; its source
        # history includes a quarantine event, whose replay would trip
        # trg_screenings_no_quarantine_while_canon mid-copy.
        conn = connect(target_db)
        conn.execute(
            "INSERT INTO canon_selections(concept_id, locale,"
            " programming_language, option_uid, surface_form, source_file)"
            " SELECT concept_id, locale, NULL, uid, surface_form,"
            " 'libs/i18n/canon/uk.toml' FROM options WHERE uid = ?",
            (OPT_V1,),
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        message = str(refusal.value)
        assert "canon-selected" in message and OPT_V1 in message
        assert _rows(target_db) == []

    def test_unknown_intake_table_refuses(self, source_db, target_db):
        conn = connect(source_db)
        conn.executescript(
            "CREATE TABLE side_notes ("
            " option_uid TEXT NOT NULL REFERENCES options(uid), body TEXT);"
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        message = str(refusal.value)
        assert "side_notes" in message and "no carry policy" in message

    def test_table_anchored_on_second_level_intake_table_refuses(
        self, source_db, target_db
    ):
        # The completeness guard anchors on EVERY carried table, not just the
        # four roots: a table FK-ing concept_commentary (itself carried, but
        # not a root) is intake layer just the same, and must refuse rather
        # than fall out of the rebuild.
        conn = connect(source_db)
        conn.executescript(
            "CREATE TABLE commentary_replies ("
            " commentary_uid TEXT NOT NULL REFERENCES concept_commentary(uid),"
            " body TEXT);"
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        message = str(refusal.value)
        assert "commentary_replies" in message and "no carry policy" in message

    def test_message_partition_endorsements_refuse(self, source_db, target_db):
        conn = connect(source_db)
        conn.executescript(
            """
            INSERT INTO message_templates(implementation, key, template_en)
                VALUES ('cpython', 'name-error', 'name {name} is not defined');
            INSERT INTO message_translations(template_id, locale, template, status)
                VALUES (1, 'uk', 'ім’я {name} не визначено', 'machine');
            """
        )
        conn.execute(
            "INSERT INTO message_endorsements(uid, message_translation_id,"
            " contributor_id, method, rung_at_endorsement)"
            " VALUES (?, 1, ?, 'github', 'contributor')",
            ("men_" + "a7" * 12, CONTRIB_NEW),
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        assert "message_endorsements" in str(refusal.value)

    def test_unregistered_locale_refuses(self, source_db, target_db):
        # A session in a locale the rebuilt reference layer does not know —
        # the 'fil' case. The reference layer is maintainer-curated, so the
        # gap is named, never filled.
        conn = connect(source_db)
        conn.execute(
            "INSERT INTO locales(tag, language_subtag, name, native_name,"
            " direction, in_registry) VALUES ('fil','fil','Filipino',"
            "'Filipino','ltr',1)"
        )
        conn.execute(
            "INSERT INTO review_sessions(uid, contributor_id, locale, track,"
            " method, kit_version, rung_at_session, bundle_digest)"
            " VALUES (?, ?, 'fil', 'reserved_words', 'github', 'v2@test',"
            " 'contributor', ?)",
            ("ses_" + "2b" * 12, CONTRIB_NEW, "2b" * 32),
        )
        conn.commit()
        conn.close()
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, target_db)
        message = str(refusal.value)
        assert "locale(s)" in message and "fil" in message
        assert "register these in the rebuilt database" in message

    def test_source_without_screening_table_refuses(self, tmp_path, target_db):
        bare = tmp_path / "not_v2.db"
        sqlite3.connect(bare).executescript("CREATE TABLE t (x);")
        with pytest.raises(SystemExit) as refusal:
            _run(bare, target_db)
        assert "no option_screenings table" in str(refusal.value)

    def test_missing_file_refuses(self, source_db, tmp_path):
        with pytest.raises(SystemExit) as refusal:
            _run(source_db, tmp_path / "nowhere.db")
        assert "does not exist" in str(refusal.value)
