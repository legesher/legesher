"""The dangling-selection repair and its provenance round-trip (CORE-2079).

``selected_translations`` held 14 rows whose selected value existed in no
candidate row, which made ``migrate_to_v2.py`` refuse the build. These tests
pin the repair script's contract on fixture databases — never the real one:

* a dangling selection gets its candidate row back, with the dedicated
  ``selection-repair`` source and the sibling row's word_type/word_form;
* a re-run is a reported no-op (idempotent), and every triple — all 14 of
  the real list included — prints a disposition; nothing is silent;
* a triple whose selection is missing or selects a different value refuses
  the WHOLE run with nothing written;
* the SOURCE_MAP round-trip: the migration refuses the dangling fixture,
  accepts it after the repair, and publishes the restored row with
  provenance ``legesher`` while the private detail says ``selection-repair``.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.migrate_to_v2 import (
    CONTRIBUTOR_IDENTITY_MAP,
    SUPERSEDED_BY_REVIEW,
    migrate,
)
from scripts.repair_dangling_selections import (
    REPAIR_CREATED_BY,
    REPAIR_SOURCE,
    REPAIRS,
    Repair,
    apply_repairs,
    main,
    plan_repairs,
)

#: One synthetic dangle, exercising the same machinery as the real 14.
DANGLE = Repair("break", "python", "ur", "توڑ_مرمت", "test fixture")


@pytest.fixture(autouse=True)
def _no_identity_maps() -> Iterator[None]:
    """Run the migration with empty identity maps.

    The fixture rows are all ``legesher``-kind (``yaml-import`` /
    ``selection-repair``), which never resolve an identity — pinned here so
    a data-home checkout on the developer machine cannot leak real labels
    into the run.
    """
    saved_ids = dict(CONTRIBUTOR_IDENTITY_MAP)
    saved_superseded = dict(SUPERSEDED_BY_REVIEW)
    CONTRIBUTOR_IDENTITY_MAP.clear()
    SUPERSEDED_BY_REVIEW.clear()
    yield
    CONTRIBUTOR_IDENTITY_MAP.clear()
    CONTRIBUTOR_IDENTITY_MAP.update(saved_ids)
    SUPERSEDED_BY_REVIEW.clear()
    SUPERSEDED_BY_REVIEW.update(saved_superseded)


def _build_v1(path: Path) -> sqlite3.Connection:
    """A minimal v1 database with one term, one candidate, one selection."""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE languages (
            code TEXT PRIMARY KEY, name TEXT, native_name TEXT, bcp47 TEXT,
            direction TEXT, numeral_system TEXT, has_case_distinction INTEGER,
            status TEXT, in_registry INTEGER, script TEXT
        );
        CREATE TABLE terms (
            id INTEGER PRIMARY KEY, name TEXT, programming_language TEXT NOT NULL,
            category TEXT, subcategory TEXT, description TEXT, version_added TEXT
        );
        CREATE TABLE translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, term_id INTEGER,
            language_code TEXT, translation TEXT, source TEXT, created_by TEXT,
            model_version TEXT, word_type TEXT, word_form TEXT, confidence TEXT,
            model_rationale TEXT, created_at TEXT, updated_at TEXT,
            UNIQUE(term_id, language_code, source, translation)
        );
        CREATE TABLE selected_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, term_id INTEGER,
            language_code TEXT, translation TEXT, selected_by TEXT,
            selected_at TEXT, selection_reason TEXT
        );
        INSERT INTO languages
            (code, name, native_name, bcp47, direction, has_case_distinction,
             status, in_registry)
        VALUES ('ur', 'Urdu', 'اردو', 'ur', 'rtl', 0, 'experimental', 1);
        INSERT INTO terms (id, name, programming_language, category)
        VALUES (3, 'break', 'python', 'keyword');
        INSERT INTO translations
            (term_id, language_code, translation, source, created_by,
             word_type, word_form, created_at)
        VALUES (3, 'ur', 'توڑ', 'yaml-import', 'yaml-import',
                'verb', 'imperative', '2026-03-19T00:00:00');
        INSERT INTO selected_translations
            (term_id, language_code, translation, selected_by, selected_at)
        VALUES (3, 'ur', 'توڑ_مرمت', 'CORE-2079-test', '2026-08-18T00:00:00');
        """
    )
    conn.commit()
    return conn


class TestRepair:
    def test_repairs_a_dangling_selection(self, tmp_path: Path) -> None:
        conn = _build_v1(tmp_path / "v1.db")
        dispositions = plan_repairs(conn, (DANGLE,))
        assert [d.action for d in dispositions] == ["insert"]
        assert apply_repairs(conn, dispositions) == 1
        row = conn.execute(
            "SELECT source, created_by, word_type, word_form, confidence, "
            "model_version, created_at, updated_at FROM translations "
            "WHERE translation = ?",
            (DANGLE.value,),
        ).fetchone()
        assert row[:2] == (REPAIR_SOURCE, REPAIR_CREATED_BY)
        # word_type/word_form mirror the sibling candidate; the assertion
        # columns (confidence, model_version) stay NULL — the repair asserts
        # nothing about the value, it restores a selection-layer choice.
        assert row[2:6] == ("verb", "imperative", None, None)
        assert row[6] and row[7]  # timestamps written explicitly

    def test_rerun_is_a_reported_noop(self, tmp_path: Path) -> None:
        conn = _build_v1(tmp_path / "v1.db")
        apply_repairs(conn, plan_repairs(conn, (DANGLE,)))
        before = conn.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
        dispositions = plan_repairs(conn, (DANGLE,))
        assert [d.action for d in dispositions] == ["noop"]
        assert apply_repairs(conn, dispositions) == 0
        assert conn.execute("SELECT COUNT(*) FROM translations").fetchone()[0] == before

    def test_selection_pointing_elsewhere_refuses_run(self, tmp_path: Path) -> None:
        db = tmp_path / "v1.db"
        conn = _build_v1(db)
        conn.execute(
            "UPDATE selected_translations SET translation = 'توڑ' WHERE term_id = 3"
        )
        conn.commit()
        conn.close()
        assert main(["--db", str(db)]) == 1
        check = sqlite3.connect(db)
        assert (
            check.execute(
                "SELECT COUNT(*) FROM translations WHERE source = ?",
                (REPAIR_SOURCE,),
            ).fetchone()[0]
            == 0
        )

    def test_missing_selection_refuses(self, tmp_path: Path) -> None:
        conn = _build_v1(tmp_path / "v1.db")
        conn.execute("DELETE FROM selected_translations")
        conn.commit()
        dispositions = plan_repairs(conn, (DANGLE,))
        assert [d.action for d in dispositions] == ["refuse"]
        assert "no selection row" in dispositions[0].detail

    def test_every_real_triple_gets_a_printed_disposition(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """All 14 shipped triples run against a fixture holding every dangle."""
        db = tmp_path / "v1.db"
        conn = _build_v1(db)
        term_ids: dict[tuple[str, str], int] = {}
        next_id = 100
        for repair in REPAIRS:
            key = (repair.term, repair.programming_language)
            if key not in term_ids:
                term_ids[key] = next_id
                conn.execute(
                    "INSERT INTO terms (id, name, programming_language, category) "
                    "VALUES (?, ?, ?, 'keyword')",
                    (next_id, repair.term, repair.programming_language),
                )
                next_id += 1
            conn.execute(
                "INSERT INTO languages (code, name, in_registry) "
                "SELECT ?, ?, 1 WHERE NOT EXISTS "
                "(SELECT 1 FROM languages WHERE code = ?)",
                (repair.locale, repair.locale, repair.locale),
            )
            conn.execute(
                "INSERT INTO selected_translations "
                "(term_id, language_code, translation) VALUES (?, ?, ?)",
                (term_ids[key], repair.locale, repair.value),
            )
        conn.commit()
        conn.close()
        assert main(["--db", str(db)]) == 0
        out = capsys.readouterr().out
        for repair in REPAIRS:
            assert f"{repair.term}/{repair.locale}" in out
        assert out.count("REPAIRED:") == len(REPAIRS)
        assert "14 candidate row(s) inserted" in out

    def test_repairs_list_is_the_root_caused_fourteen(self) -> None:
        assert len(REPAIRS) == 14
        assert sum(r.term == "except*" for r in REPAIRS) == 9
        assert all(r.value.endswith("*") for r in REPAIRS if r.term == "except*")


class TestSourceMapRoundTrip:
    def test_migration_refuses_then_accepts_and_maps_provenance(
        self, tmp_path: Path
    ) -> None:
        """End-to-end: dangling v1 refuses; repaired v1 migrates; the restored
        row publishes ``legesher`` while the private detail says
        ``selection-repair``."""
        v1 = tmp_path / "v1.db"
        conn = _build_v1(v1)

        with pytest.raises(SystemExit, match="selected value not present"):
            migrate(v1, tmp_path / "v2-refused.db", salt="test-salt")

        apply_repairs(conn, plan_repairs(conn, (DANGLE,)))
        conn.close()

        migrate(v1, tmp_path / "v2.db", salt="test-salt")
        v2 = sqlite3.connect(tmp_path / "v2.db")
        source, detail, contributor = v2.execute(
            "SELECT p.source, p.source_detail, p.contributor_id "
            "FROM option_provenance p JOIN options o ON o.uid = p.option_uid "
            "WHERE o.surface_form = ?",
            (DANGLE.value,),
        ).fetchone()
        assert (source, detail) == ("legesher", REPAIR_SOURCE)
        assert contributor is None  # a repair label must never mint a person
