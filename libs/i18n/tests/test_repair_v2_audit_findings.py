"""The CORE-1973 / CORE-1972 v2 repair script, on fixture databases.

Pins the contract of ``scripts/repair_v2_audit_findings.py``:

* the starred ``except*`` mirror is inserted with provenance and a computed
  verdict, and its canon row materializes;
* an audit-corrected cell replaces its migration-era ``machine`` canon row
  wholesale, at ``experimental``, preserving the v1 decision timestamp;
* a canon row someone has since moved off ``machine`` refuses;
* the backfill flips a stamped ``min_interpreter_ok`` on a 3.13-only-XID
  rendering without touching its canon row, and the freeze triggers are back
  in place afterwards;
* drift between a stored verdict and the recomputation refuses before any
  write;
* a second run is a reported no-op;
* every decider on the repaired canon maps to a published export role;
* on a rebuild from current v1 (the real migration and rung correction), the
  step completes without refusing or duplicating an option, reproduces the
  repaired copy's option uids and rungs, and never demotes a correction
  someone has already ratified above ``machine``.

Fixtures monkeypatch the script's cell lists — the real lists are the audit
scope; the contract under test does not depend on their size.

The fixture-backed tests run on CPython 3.13 or later only. The fixture seeds
the Sinhala ZWJ rendering under canon, and the canon triggers accept it only
where the running interpreter reads U+200D as an identifier character
(Unicode 15.1). The script recomputes every verdict with the running
interpreter, so its contract is defined on the 3.13 toolchain. The library
alias test and the rebuild tests that do not use that fixture run everywhere.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

from legesher_i18n.db import schema_v2
from legesher_i18n.db.schema_v2 import apply_schema_v2, option_uid
from legesher_i18n.surface_validation import (
    VALIDATOR_VERSION,
    allowed_format_chars_for,
    allowed_scripts_for,
    validate_surface,
)
from scripts import repair_v2_audit_findings as repair
from tests.interpreter_gaps import NEWER_IDENTIFIER_SAMPLES
from scripts.correct_canon_review_rung import correct
from scripts.export_canon import map_decider_role
from scripts.migrate_to_v2 import migrate

#: One cell per phase keeps the fixture legible: da exercises the except*
#: mirror, tr the correction, si the ZWJ backfill flip.
DA_STARLESS = "undtiden"
DA_STARRED = "undtiden*"
TR_JUNK = "theglobalvariables"
TR_CORRECT = "küreseldeğişkenler"
SI_ZWJ = "අසත්‍ය"  # virama + ZWJ conjunct: identifier-legal only on 3.13+

V1_ROWS = (
    ("except*", "da", DA_STARRED, "2026-08-16 10:00:00", "CORE-1839 mirror"),
    ("globals", "tr", TR_CORRECT, "2026-08-17 23:21:42", "2026-08-18 data audit"),
    ("false", "si", SI_ZWJ, "2026-02-09 09:27:36", "migration"),
)


def _seed_validation(
    conn: sqlite3.Connection,
    uid: str,
    surface: str,
    term: str,
    subtag: str,
    *,
    version: str = "py-identifier-v2",
) -> None:
    """A stored verdict as the migration left it: computed columns real,
    ``min_interpreter_ok`` a schema-default stamp."""
    verdict = validate_surface(
        surface, term, allowed_scripts_for(subtag), allowed_format_chars_for(subtag)
    )
    conn.execute(
        "INSERT INTO option_validations (option_uid, validator_version,"
        " identifier_valid, nfkc_stable, nfkc_delta_class, script_consistent,"
        " collides_en_keyword, min_interpreter_ok, format_chars_clean)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
        (
            uid,
            version,
            int(verdict.identifier_valid),
            int(verdict.nfkc_stable),
            verdict.nfkc_delta_class,
            int(verdict.script_consistent),
            int(verdict.collides_en_keyword),
            int(verdict.format_chars_clean),
        ),
    )


def _seed_option(
    conn: sqlite3.Connection,
    slug: str,
    locale: str,
    surface: str,
    subtag: str,
    *,
    canon_status: str | None = None,
) -> str:
    # Unscoped, as the migration mints every v1-derived option.
    uid = option_uid(slug, locale, surface)
    concept_id = conn.execute(
        "SELECT id FROM concepts WHERE slug = ?", (slug,)
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO options (uid, concept_id, locale, surface_form)"
        " VALUES (?, ?, ?, ?)",
        (uid, concept_id, locale, surface),
    )
    _seed_validation(conn, uid, surface, slug, subtag)
    if canon_status is not None:
        conn.execute(
            "INSERT INTO canon_selections (concept_id, locale,"
            " programming_language, option_uid, surface_form, status,"
            " decided_by, decision_reason, source_file)"
            " VALUES (?, ?, 'python', ?, ?, ?, 'automated', 'migration',"
            " 'libs/i18n/canon/' || ? || '.toml')",
            (concept_id, locale, uid, surface, canon_status, locale),
        )
    return uid


@pytest.fixture
def dbs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """A v2 fixture in the audit's pre-repair shape, and its v1 mirror."""
    if sys.version_info < (3, 13):
        pytest.skip(
            "the si ZWJ fixture is canon-eligible only on CPython 3.13+ "
            "(Unicode 15.1); the repair's contract is defined there"
        )
    monkeypatch.setattr(repair, "EXCEPT_STAR_LOCALES", ("da",))
    monkeypatch.setattr(repair, "CORRECTED_CELLS", (("tr", "globals"),))

    v2_path = tmp_path / "translations_v2.db"
    conn = sqlite3.connect(v2_path)
    conn.execute("PRAGMA foreign_keys = ON")
    apply_schema_v2(conn)
    conn.execute(
        "INSERT INTO programming_languages (code, name, status)"
        " VALUES ('python', 'Python', 'shipping')"
    )
    for tag, name in (("da", "Danish"), ("tr", "Turkish"), ("si", "Sinhala")):
        conn.execute(
            "INSERT INTO locales (tag, language_subtag, name, native_name,"
            " direction, in_registry) VALUES (?, ?, ?, ?, 'ltr', 1)",
            (tag, tag, name, name),
        )
    for slug in ("except*", "globals", "false"):
        conn.execute(
            "INSERT INTO concepts (slug, definition_en, category)"
            " VALUES (?, 'fixture', 'keyword')",
            (slug,),
        )
    _seed_option(conn, "except*", "da", DA_STARLESS, "da")
    _seed_option(conn, "globals", "tr", TR_JUNK, "tr", canon_status="machine")
    _seed_option(conn, "false", "si", SI_ZWJ, "si", canon_status="machine")
    # A '*'-scoped dunder: the term spells '__import__', the slug spells it
    # '--import--'. The backfill must validate against the TERM — treating
    # the slug's dashes as structural affixes would flag every rendering as
    # drift and refuse the run.
    conn.execute(
        "INSERT INTO concepts (slug, definition_en, category)"
        " VALUES ('--import--', 'fixture', 'builtin')"
    )
    concept = conn.execute(
        "SELECT id FROM concepts WHERE slug = '--import--'"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO terms (concept_id, programming_language, name, category)"
        " VALUES (?, 'python', '__import__', 'builtin_func')",
        (concept,),
    )
    dunder_uid = option_uid("--import--", "da", "importer")
    conn.execute(
        "INSERT INTO options (uid, concept_id, locale, surface_form)"
        " VALUES (?, ?, 'da', 'importer')",
        (dunder_uid, concept),
    )
    _seed_validation(conn, dunder_uid, "importer", "__import__", "da")
    conn.commit()
    conn.close()

    v1_path = tmp_path / "translations.db"
    v1 = sqlite3.connect(v1_path)
    v1.executescript(
        "CREATE TABLE terms (id INTEGER PRIMARY KEY, name TEXT NOT NULL);"
        "CREATE TABLE selected_translations (id INTEGER PRIMARY KEY,"
        " term_id INTEGER NOT NULL, language_code TEXT NOT NULL,"
        " translation TEXT NOT NULL, selected_at TEXT NOT NULL,"
        " selected_by TEXT, selection_reason TEXT);"
    )
    for term_id, (name, locale, surface, at, reason) in enumerate(V1_ROWS, 1):
        v1.execute("INSERT INTO terms (id, name) VALUES (?, ?)", (term_id, name))
        v1.execute(
            "INSERT INTO selected_translations (term_id, language_code,"
            " translation, selected_at, selection_reason) VALUES (?, ?, ?, ?, ?)",
            (term_id, locale, surface, at, reason),
        )
    v1.commit()
    v1.close()
    return v2_path, v1_path


def _query(path: Path, sql: str, *params: object) -> list[sqlite3.Row]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def test_repair_lands_all_three_phases(dbs: tuple[Path, Path]) -> None:
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0

    starred = _query(
        v2,
        "SELECT o.uid, v.min_interpreter_ok, v.validator_version"
        " FROM options o JOIN option_validations v ON v.option_uid = o.uid"
        " WHERE o.surface_form = ?",
        DA_STARRED,
    )
    assert len(starred) == 1
    canon = _query(
        v2,
        "SELECT surface_form, status, decided_by FROM canon_selections cs"
        " JOIN concepts c ON c.id = cs.concept_id WHERE c.slug = 'except*'",
    )
    assert [(r["surface_form"], r["status"]) for r in canon] == [
        (DA_STARRED, "machine")
    ]
    provenance = _query(
        v2,
        "SELECT source, source_detail FROM option_provenance WHERE option_uid = ?",
        starred[0]["uid"],
    )
    assert ("legesher", repair.SOURCE_DETAIL) in {
        (r["source"], r["source_detail"]) for r in provenance
    }

    corrected = _query(
        v2,
        "SELECT surface_form, status, decided_at, decision_reason"
        " FROM canon_selections cs JOIN concepts c ON c.id = cs.concept_id"
        " WHERE c.slug = 'globals'",
    )[0]
    assert corrected["surface_form"] == TR_CORRECT
    assert corrected["status"] == "experimental"
    assert corrected["decided_at"] == "2026-08-17 23:21:42"
    junk_still_evidence = _query(
        v2, "SELECT withdrawn_at FROM options WHERE surface_form = ?", TR_JUNK
    )
    assert len(junk_still_evidence) == 1  # superseded, never erased

    zwj = _query(
        v2,
        "SELECT v.min_interpreter_ok, v.validator_version FROM option_validations"
        " v JOIN options o ON o.uid = v.option_uid WHERE o.surface_form = ?",
        SI_ZWJ,
    )[0]
    assert zwj["min_interpreter_ok"] == 0
    assert zwj["validator_version"] == VALIDATOR_VERSION
    zwj_canon = _query(
        v2,
        "SELECT status FROM canon_selections cs JOIN concepts c ON"
        " c.id = cs.concept_id WHERE c.slug = 'false'",
    )
    assert [r["status"] for r in zwj_canon] == ["machine"]  # untouched

    stale = _query(
        v2,
        "SELECT COUNT(*) AS n FROM option_validations WHERE validator_version <> ?",
        VALIDATOR_VERSION,
    )[0]["n"]
    assert stale == 0
    triggers = {
        r["name"]
        for r in _query(
            v2,
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND name"
            " LIKE 'trg_validations_%'",
        )
    }
    assert "trg_validations_frozen_under_canon" in triggers
    assert "trg_validations_no_delete_under_canon" in triggers


def _stamp_as_an_older_validator(v2: Path, sql: str | None = None) -> None:
    """Put every stamp back to an older validator, as a database written
    before the version moved carries it. ``sql`` runs under the same lifted
    freeze, for a test that also needs to edit a stored verdict."""
    conn = sqlite3.connect(v2)
    for name in schema_v2._VALIDATION_FREEZE_TRIGGERS:
        conn.execute(f"DROP TRIGGER IF EXISTS {name}")
    conn.execute("UPDATE option_validations SET validator_version = 'py-identifier-v3'")
    if sql is not None:
        conn.execute(sql)
    for kind, name, statement in schema_v2._fresh_schema_objects():
        if kind == "trigger" and name in schema_v2._VALIDATION_FREEZE_TRIGGERS:
            conn.execute(statement)
    conn.commit()
    conn.close()


def _stamps(v2: Path) -> list[str]:
    return [
        row[0]
        for row in _query(
            v2, "SELECT DISTINCT validator_version FROM option_validations"
        )
    ]


@pytest.mark.parametrize(
    "release",
    sorted(NEWER_IDENTIFIER_SAMPLES),
    ids=lambda release: f"{release[0]}.{release[1]}",
)
def test_the_backfill_flips_a_rendering_that_needs_any_newer_release(
    dbs: tuple[Path, Path], release: tuple[int, int]
) -> None:
    # The backfill read only the 3.13 table, so a rendering that needs 3.14
    # or 3.15 kept its schema-default "fine on 3.10".
    v2, v1 = dbs
    surface = f"glo{NEWER_IDENTIFIER_SAMPLES[release]}bal"
    conn = sqlite3.connect(v2)
    conn.execute("PRAGMA foreign_keys = ON")
    uid = _seed_option(conn, "globals", "da", surface, "da")
    conn.commit()
    conn.close()

    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    row = _query(
        v2,
        "SELECT min_interpreter_ok, validator_version FROM option_validations"
        " WHERE option_uid = ?",
        uid,
    )[0]
    assert row["min_interpreter_ok"] == 0
    assert row["validator_version"] == VALIDATOR_VERSION


def test_an_older_stamp_is_recomputed_and_restamped(dbs: tuple[Path, Path]) -> None:
    """The recompute after a validator-version change: every row, no verdict lost."""
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    before = _query(
        v2,
        "SELECT option_uid, min_interpreter_ok, identifier_valid, nfkc_stable,"
        " script_consistent, collides_en_keyword, format_chars_clean"
        " FROM option_validations ORDER BY option_uid",
    )
    assert len(before) > 3
    assert {row["min_interpreter_ok"] for row in before} == {0, 1}

    _stamp_as_an_older_validator(v2)

    results, _ = repair.run(v2, v1)
    assert results["backfill"].backfilled == len(before)
    after = _query(
        v2,
        "SELECT option_uid, min_interpreter_ok, identifier_valid, nfkc_stable,"
        " script_consistent, collides_en_keyword, format_chars_clean"
        " FROM option_validations ORDER BY option_uid",
    )
    assert [tuple(row) for row in after] == [tuple(row) for row in before]
    stamps = _query(v2, "SELECT DISTINCT validator_version FROM option_validations")
    assert [row[0] for row in stamps] == [VALIDATOR_VERSION]

    # And then it is settled: a third run writes nothing.
    results, _ = repair.run(v2, v1)
    assert results["backfill"].backfilled == 0


def _as_an_earlier_revision_repaired_it(v2: Path) -> None:
    """Move the starred mirror's canon row onto a python-scoped option id.

    An earlier revision of the script minted the mirror python-scoped, and a
    database it repaired still ratifies that id. The current script mints the
    unscoped id, finds canon on the other one, and refuses in phase 1.
    """
    conn = sqlite3.connect(v2)
    conn.execute("PRAGMA foreign_keys = ON")
    concept_id = conn.execute(
        "SELECT id FROM concepts WHERE slug = 'except*'"
    ).fetchone()[0]
    scoped = option_uid("except*", "da", DA_STARRED, "python")
    conn.execute(
        "INSERT INTO options (uid, concept_id, locale, surface_form,"
        " programming_language) VALUES (?, ?, 'da', ?, 'python')",
        (scoped, concept_id, DA_STARRED),
    )
    _seed_validation(
        conn, scoped, DA_STARRED, "except*", "da", version=VALIDATOR_VERSION
    )
    removed = conn.execute(
        "DELETE FROM canon_selections WHERE concept_id = ? AND locale = 'da'",
        (concept_id,),
    ).rowcount
    assert removed == 1
    conn.execute(
        "INSERT INTO canon_selections (concept_id, locale,"
        " programming_language, option_uid, surface_form, status,"
        " decided_by, decision_reason, source_file)"
        " VALUES (?, 'da', 'python', ?, ?, 'machine', 'automated',"
        " 'earlier revision', 'libs/i18n/canon/da.toml')",
        (concept_id, scoped, DA_STARRED),
    )
    conn.commit()
    conn.close()


def test_validations_only_recomputes_a_database_the_full_repair_refuses(
    dbs: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    _as_an_earlier_revision_repaired_it(v2)
    rows = _query(v2, "SELECT COUNT(*) FROM option_validations")[0][0]
    _stamp_as_an_older_validator(v2)
    # The refusal is the script's own, from the data: nothing is patched.
    with pytest.raises(repair.RepairRefused, match="minted it python-scoped"):
        repair.main(["--db", str(v2), "--v1-db", str(v1)])
    assert _stamps(v2) == ["py-identifier-v3"]
    capsys.readouterr()

    # No v1 database is needed, and the audit phases are never reached.
    assert repair.main(["--db", str(v2), "--validations-only"]) == 0
    summary = capsys.readouterr().out
    assert summary.startswith("validations only: ")
    assert f"{rows} validation row(s) stamped {VALIDATOR_VERSION}" in summary
    assert "(0 with a changed min_interpreter_ok" in summary
    assert _stamps(v2) == [VALIDATOR_VERSION]

    # Settled: nothing left to do.
    assert repair.main(["--db", str(v2), "--validations-only"]) == 0
    assert "0 validation row(s) stamped" in capsys.readouterr().out


def _freeze_triggers(v2: Path) -> set[str]:
    return {
        row[0]
        for row in _query(v2, "SELECT name FROM sqlite_master WHERE type = 'trigger'")
    } & set(schema_v2._VALIDATION_FREEZE_TRIGGERS)


def test_validations_only_leaves_the_freeze_in_force(dbs: tuple[Path, Path]) -> None:
    # The run lifts the freeze to write. Afterwards a canon-selected
    # validation can again be neither revalidated nor deleted.
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    _stamp_as_an_older_validator(v2)
    assert repair.main(["--db", str(v2), "--validations-only"]) == 0

    assert _freeze_triggers(v2) == set(schema_v2._VALIDATION_FREEZE_TRIGGERS)
    conn = sqlite3.connect(v2)
    try:
        (ratified,) = conn.execute(
            "SELECT option_uid FROM canon_selections ORDER BY option_uid LIMIT 1"
        ).fetchone()
        with pytest.raises(sqlite3.DatabaseError, match="canon-selected"):
            conn.execute(
                "UPDATE option_validations SET min_interpreter_ok ="
                " 1 - min_interpreter_ok WHERE option_uid = ?",
                (ratified,),
            )
        with pytest.raises(sqlite3.DatabaseError, match="canon-selected"):
            conn.execute(
                "DELETE FROM option_validations WHERE option_uid = ?", (ratified,)
            )
    finally:
        conn.close()


def test_validations_only_refuses_when_the_freeze_is_not_restored(
    dbs: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    # A schema that no longer ships the freeze triggers under these names
    # would leave the run with nothing to recreate. It must not commit a
    # database with the freeze gone.
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    _stamp_as_an_older_validator(v2)
    backfill = repair.backfill_min_interpreter

    def backfill_without_the_shipped_triggers(conn: sqlite3.Connection):
        shipped = schema_v2._fresh_schema_objects()
        monkeypatch.setattr(
            schema_v2,
            "_fresh_schema_objects",
            lambda: [
                entry
                for entry in shipped
                if entry[1] not in schema_v2._VALIDATION_FREEZE_TRIGGERS
            ],
        )
        try:
            return backfill(conn)
        finally:
            monkeypatch.setattr(schema_v2, "_fresh_schema_objects", lambda: shipped)

    monkeypatch.setattr(
        repair, "backfill_min_interpreter", backfill_without_the_shipped_triggers
    )
    with pytest.raises(repair.RepairRefused, match="freeze trigger .* is missing"):
        repair.main(["--db", str(v2), "--validations-only"])
    # Rolled back whole: the old stamps and the freeze are both still there.
    assert _stamps(v2) == ["py-identifier-v3"]
    assert _freeze_triggers(v2) == set(schema_v2._VALIDATION_FREEZE_TRIGGERS)


def test_validations_only_refuses_when_a_row_keeps_another_stamp(
    dbs: tuple[Path, Path],
) -> None:
    # A validation row the recompute cannot reach (its option is gone) keeps
    # its old stamp. "Every row carries the current validator" would then be
    # untrue, so the run refuses instead of committing.
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    _stamp_as_an_older_validator(v2)
    conn = sqlite3.connect(v2)
    conn.execute("PRAGMA foreign_keys = OFF")
    _seed_validation(
        conn, "no-such-option", "ord", "print", "da", version="py-identifier-v3"
    )
    conn.commit()
    conn.close()

    with pytest.raises(
        repair.RepairRefused, match="1 validation row.s. are not stamped"
    ):
        repair.main(["--db", str(v2), "--validations-only"])
    assert _stamps(v2) == ["py-identifier-v3"]


def test_validations_only_dry_run_writes_nothing(
    dbs: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    _stamp_as_an_older_validator(v2)
    before = v2.read_bytes()
    capsys.readouterr()

    assert repair.main(["--db", str(v2), "--validations-only", "--dry-run"]) == 0
    summary = capsys.readouterr().out
    assert summary.startswith("[dry-run, discarded] validations only: ")
    assert f"stamped {VALIDATOR_VERSION}" in summary
    assert v2.read_bytes() == before
    assert _stamps(v2) == ["py-identifier-v3"]


def test_validations_only_counts_a_verdict_that_changes(
    dbs: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    # The count the maintainer reads before the real run: how many rows are
    # more than a re-stamp.
    v2, v1 = dbs
    # A second rendering that needs a newer release, one canon does not
    # ratify, so the list below holds a marked row and an unmarked one.
    conn = sqlite3.connect(v2)
    conn.execute("PRAGMA foreign_keys = ON")
    _seed_option(conn, "globals", "si", SI_ZWJ, "si")
    conn.commit()
    conn.close()
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    not_ok = _query(
        v2, "SELECT COUNT(*) FROM option_validations WHERE min_interpreter_ok = 0"
    )[0][0]
    assert not_ok > 0
    # As the 3.13-only rule left a rendering that needs a newer release.
    _stamp_as_an_older_validator(
        v2, "UPDATE option_validations SET min_interpreter_ok = 1"
    )
    capsys.readouterr()

    assert repair.main(["--db", str(v2), "--validations-only"]) == 0
    report = capsys.readouterr().out
    assert f"({not_ok} with a changed min_interpreter_ok" in report
    # Each one is named, with the canon-selected ones marked: the write is
    # made with the freeze lifted, so it is the maintainer who reads it.
    changed = [line for line in report.splitlines() if line.startswith("  changed: ")]
    assert len(changed) == not_ok
    ratified = {row[0] for row in _query(v2, "SELECT option_uid FROM canon_selections")}
    for line in changed:
        assert "min_interpreter_ok 1 -> 0" in line
        uid = line.removeprefix("  changed: ").split(" ", 1)[0]
        assert line.endswith(", canon-selected") is (uid in ratified), line
    assert any(line.endswith(", canon-selected") for line in changed)
    assert any(not line.endswith(", canon-selected") for line in changed)
    assert (
        _query(
            v2, "SELECT COUNT(*) FROM option_validations WHERE min_interpreter_ok = 0"
        )[0][0]
        == not_ok
    )


def test_validations_only_refuses_when_another_stored_verdict_would_change(
    dbs: tuple[Path, Path],
) -> None:
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    _stamp_as_an_older_validator(
        v2, "UPDATE option_validations SET nfkc_stable = 1 - nfkc_stable"
    )
    rows = "SELECT * FROM option_validations ORDER BY option_uid"
    before = [tuple(row) for row in _query(v2, rows)]

    with pytest.raises(repair.RepairRefused, match="nfkc_stable"):
        repair.main(["--db", str(v2), "--validations-only"])
    # No row was written. (The file itself may differ: opening the database
    # re-creates its views and triggers, as every intake entry point does.)
    assert [tuple(row) for row in _query(v2, rows)] == before
    assert _stamps(v2) == ["py-identifier-v3"]


def test_the_full_repair_lists_the_verdicts_it_changed(
    dbs: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    # The same list on the full run: its backfill is the same write.
    v2, v1 = dbs
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    report = capsys.readouterr().out
    changed = [line for line in report.splitlines() if line.startswith("  changed: ")]
    not_ok = _query(
        v2, "SELECT COUNT(*) FROM option_validations WHERE min_interpreter_ok = 0"
    )[0][0]
    assert not_ok > 0
    assert len(changed) == not_ok
    assert all("min_interpreter_ok 1 -> 0" in line for line in changed)


def test_the_full_repair_still_needs_the_v1_database(dbs: tuple[Path, Path]) -> None:
    v2, _ = dbs
    with pytest.raises(SystemExit) as excinfo:
        repair.main(["--db", str(v2)])
    assert excinfo.value.code == 2


def test_second_run_is_a_noop(dbs: tuple[Path, Path]) -> None:
    v2, v1 = dbs
    repair.main(["--db", str(v2), "--v1-db", str(v1)])
    before = _query(
        v2,
        "SELECT (SELECT COUNT(*) FROM options) AS o,"
        " (SELECT COUNT(*) FROM canon_selections) AS c,"
        " (SELECT COUNT(*) FROM option_provenance) AS p",
    )[0]
    results, _ = repair.run(v2, v1)
    assert results["except_star"].created_options == 0
    assert results["except_star"].created_canon == 0
    assert results["corrections"].replaced_canon == 0
    assert results["backfill"].backfilled == 0
    after = _query(
        v2,
        "SELECT (SELECT COUNT(*) FROM options) AS o,"
        " (SELECT COUNT(*) FROM canon_selections) AS c,"
        " (SELECT COUNT(*) FROM option_provenance) AS p",
    )[0]
    assert tuple(before) == tuple(after)


def test_moved_canon_rung_refuses(dbs: tuple[Path, Path]) -> None:
    v2, v1 = dbs
    conn = sqlite3.connect(v2)
    conn.execute("PRAGMA recursive_triggers = ON")
    with conn:
        conn.execute("DELETE FROM canon_selections WHERE surface_form = ?", (TR_JUNK,))
        uid = option_uid("globals", "tr", TR_JUNK)
        concept = conn.execute(
            "SELECT id FROM concepts WHERE slug = 'globals'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO canon_selections (concept_id, locale,"
            " programming_language, option_uid, surface_form, status,"
            " decided_by, decision_reason, source_file) VALUES"
            " (?, 'tr', 'python', ?, ?, 'reviewed', 'native_review',"
            " 'someone signed off', 'libs/i18n/canon/tr.toml')",
            (concept, uid, TR_JUNK),
        )
    conn.close()

    with pytest.raises(SystemExit, match="REFUSED"):
        repair.main(["--db", str(v2), "--v1-db", str(v1)])
    untouched = _query(
        v2, "SELECT surface_form, status FROM canon_selections WHERE locale = 'tr'"
    )[0]
    assert (untouched["surface_form"], untouched["status"]) == (TR_JUNK, "reviewed")


def test_verdict_drift_refuses_before_writing(dbs: tuple[Path, Path]) -> None:
    v2, v1 = dbs
    conn = sqlite3.connect(v2)
    with conn:
        # A stored verdict that disagrees with recomputation: the star-less
        # form really is identifier-invalid, so claim the opposite.
        conn.execute(
            "UPDATE option_validations SET identifier_valid = 1 WHERE option_uid = ?",
            (option_uid("except*", "da", DA_STARLESS),),
        )
    conn.close()

    with pytest.raises(SystemExit, match="drift|disagree"):
        repair.main(["--db", str(v2), "--v1-db", str(v1)])
    stale = _query(
        v2,
        "SELECT COUNT(*) AS n FROM option_validations WHERE validator_version = ?",
        VALIDATOR_VERSION,
    )[0]["n"]
    assert stale == 0  # nothing was stamped


def test_repaired_canon_rows_are_exportable(dbs: tuple[Path, Path]) -> None:
    """Every decider on the repaired canon maps to a published role.

    ``export_canon`` refuses an unmapped ``decided_by`` outright, so a repair
    that writes a decider the export does not know leaves the canon
    unpublishable. Read from the repaired database, not a literal, so a new
    decider in the script fails here first.
    """
    v2_path, v1_path = dbs
    repair.run(v2_path, v1_path)
    conn = sqlite3.connect(v2_path)
    deciders = sorted(
        row[0]
        for row in conn.execute("SELECT DISTINCT decided_by FROM canon_selections")
    )
    conn.close()
    assert "CORE-1973" in deciders
    for decider in deciders:
        assert map_decider_role(decider) == "automated", decider


def test_subtag_policy_aliases_resolve_renamed_locales() -> None:
    """The reference layer's ``nb``/``fil`` subtags reach the ``no``/``tl``
    policies instead of default-denying (the CORE-1973 drift class)."""
    assert allowed_scripts_for("nb") == frozenset({"Latin"})
    assert allowed_scripts_for("fil") == frozenset({"Latin"})
    assert allowed_format_chars_for("nb") == frozenset()


def test_dry_run_writes_nothing(dbs: tuple[Path, Path]) -> None:
    v2, v1 = dbs
    before = v2.read_bytes()
    assert repair.main(["--db", str(v2), "--v1-db", str(v1), "--dry-run"]) == 0
    assert v2.read_bytes() == before


#: The v1 shape ``migrate_to_v2`` reads, reduced to the two audited cells as
#: current v1 holds them: the migration-era value AND the repaired candidate
#: (``source='selection-repair'``) side by side, the repaired one selected,
#: with the deciders v1 really records.
CURRENT_V1 = """
CREATE TABLE languages (code TEXT PRIMARY KEY, name TEXT, native_name TEXT,
    bcp47 TEXT, direction TEXT, numeral_system TEXT,
    has_case_distinction INTEGER, status TEXT, in_registry INTEGER, script TEXT);
CREATE TABLE terms (id INTEGER PRIMARY KEY, name TEXT,
    programming_language TEXT NOT NULL, category TEXT, subcategory TEXT,
    description TEXT, version_added TEXT);
CREATE TABLE translations (id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER, language_code TEXT, translation TEXT, source TEXT,
    created_by TEXT, model_version TEXT, word_type TEXT, word_form TEXT,
    confidence TEXT, model_rationale TEXT, created_at TEXT);
CREATE TABLE selected_translations (id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER, language_code TEXT, translation TEXT, selected_by TEXT,
    selected_at TEXT, selection_reason TEXT);
INSERT INTO languages (code, name, native_name, bcp47, direction,
    has_case_distinction, status, in_registry) VALUES
    ('da', 'Danish', 'Dansk', 'da', 'ltr', 1, 'experimental', 1),
    ('tr', 'Turkish', 'Türkçe', 'tr', 'ltr', 1, 'experimental', 1);
INSERT INTO terms (id, name, programming_language, category) VALUES
    (1, 'except*', 'python', 'keyword'), (2, 'globals', 'python', 'builtin_func');
"""


@pytest.fixture
def rebuilt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Runbook section 1 up to the repair: current v1, migrate, rung correction."""
    monkeypatch.setattr(repair, "EXCEPT_STAR_LOCALES", ("da",))
    monkeypatch.setattr(repair, "CORRECTED_CELLS", (("tr", "globals"),))
    v1_path = tmp_path / "rebuild_v1.db"
    v1 = sqlite3.connect(v1_path)
    v1.executescript(CURRENT_V1)
    v1.executemany(
        "INSERT INTO translations (term_id, language_code, translation, source,"
        " created_at) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "da", DA_STARLESS, "yaml-import", "2026-02-09T00:00:00"),
            (1, "da", DA_STARRED, "selection-repair", "2026-08-20T00:00:00"),
            (2, "tr", TR_JUNK, "yaml-import", "2026-02-09T00:00:00"),
            (2, "tr", TR_CORRECT, "selection-repair", "2026-08-20T00:00:00"),
        ],
    )
    v1.executemany(
        "INSERT INTO selected_translations (term_id, language_code, translation,"
        " selected_by, selected_at, selection_reason) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "da", DA_STARRED, "CORE-1839", "2026-08-16 10:00:00", "mirror"),
            (2, "tr", TR_CORRECT, "claude-fable-5", "2026-08-17 23:21:42", "audit"),
        ],
    )
    v1.commit()
    v1.close()
    v2_path = tmp_path / "rebuild_v2.db"
    migrate(v1_path, v2_path, salt="test-salt")
    conn = sqlite3.connect(v2_path)
    conn.row_factory = sqlite3.Row
    correct(conn)
    conn.commit()
    conn.close()
    return v2_path, v1_path


def _audited_canon(path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    """The two audited cells' canon, as (option uid, rung)."""
    return {
        (row["slug"], row["locale"]): (row["option_uid"], row["status"])
        for row in _query(
            path,
            "SELECT c.slug, cs.locale, cs.option_uid, cs.status"
            " FROM canon_selections cs JOIN concepts c ON c.id = cs.concept_id"
            " WHERE (c.slug, cs.locale) IN (VALUES ('except*', 'da'),"
            " ('globals', 'tr'))",
        )
    }


def test_the_runbook_step_completes_on_a_fresh_rebuild(
    rebuilt: tuple[Path, Path],
) -> None:
    """The rebuild-sequence step neither refuses nor duplicates an option.

    Current v1 already carries both audited cells, so the migration mints
    them. The repair must recognise those options as its own (same unscoped
    uid), lift the correction to ``experimental``, and leave every decider
    exportable.
    """
    v2, v1 = rebuilt
    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0

    assert _audited_canon(v2) == {
        ("except*", "da"): (option_uid("except*", "da", DA_STARRED), "machine"),
        ("globals", "tr"): (option_uid("globals", "tr", TR_CORRECT), "experimental"),
    }
    corrected = _query(v2, "SELECT uid FROM options WHERE surface_form = ?", TR_CORRECT)
    assert len(corrected) == 1, "the correction exists under two uids"
    for row in _query(v2, "SELECT DISTINCT decided_by FROM canon_selections"):
        assert map_decider_role(row["decided_by"]) == "automated", row["decided_by"]

    results, _ = repair.run(v2, v1)
    assert results["except_star"].created_options == 0
    assert results["corrections"].replaced_canon == 0
    assert results["backfill"].backfilled == 0


def test_a_rebuild_reproduces_the_durable_keys(
    dbs: tuple[Path, Path], rebuilt: tuple[Path, Path]
) -> None:
    """The repaired durable copy and a repaired rebuild agree on uid and rung.

    ``option_uid`` is the published key, so a rebuild that re-keys a repaired
    row would republish it under a different identity.
    """
    durable, durable_v1 = dbs
    rebuild, rebuild_v1 = rebuilt
    repair.main(["--db", str(durable), "--v1-db", str(durable_v1)])
    repair.main(["--db", str(rebuild), "--v1-db", str(rebuild_v1)])
    assert _audited_canon(durable) == _audited_canon(rebuild)


@pytest.mark.parametrize("status", ["experimental", "reviewed", "official"])
def test_a_ratified_correction_is_never_demoted(
    rebuilt: tuple[Path, Path], status: str
) -> None:
    """A correction already ratified above ``machine`` keeps its rung and decider."""
    v2, v1 = rebuilt
    conn = sqlite3.connect(v2)
    conn.execute("PRAGMA recursive_triggers = ON")
    with conn:
        concept = conn.execute(
            "SELECT id FROM concepts WHERE slug = 'globals'"
        ).fetchone()[0]
        conn.execute("DELETE FROM canon_selections WHERE locale = 'tr'")
        conn.execute(
            "INSERT INTO canon_selections (concept_id, locale,"
            " programming_language, option_uid, surface_form, status,"
            " decided_by, decision_reason, source_file) VALUES"
            " (?, 'tr', 'python', ?, ?, ?, 'someone_review', 'ratified',"
            " 'libs/i18n/canon/tr.toml')",
            (concept, option_uid("globals", "tr", TR_CORRECT), TR_CORRECT, status),
        )
    conn.close()

    assert repair.main(["--db", str(v2), "--v1-db", str(v1)]) == 0
    row = _query(
        v2,
        "SELECT surface_form, status, decided_by FROM canon_selections"
        " WHERE locale = 'tr'",
    )[0]
    assert tuple(row) == (TR_CORRECT, status, "someone_review")
