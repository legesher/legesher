"""Tests for the CORE-1371 Arabic-curation recorder (record_js_ar_terms.py)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from legesher_i18n.db.database import TranslationDatabase

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
SEEDER = SCRIPTS_DIR / "seed_js_terms.py"
RECORDER = SCRIPTS_DIR / "record_js_ar_terms.py"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def prepare_db(db_path: Path) -> None:
    """Seed the JS inventory, the ar registry row, and the python term."""
    assert run_script(SEEDER, "--db-path", str(db_path)).returncode == 0
    db = TranslationDatabase(db_path=str(db_path))
    try:
        register_ar(db)
        db.get_or_create_term(
            name="while", programming_language="python", category="keyword"
        )
    finally:
        db.close()


def register_ar(db: TranslationDatabase) -> None:
    """Insert the ``ar`` registry row a fresh test DB lacks.

    The real translations.db carries the registry-seeded languages table
    (CORE-611); tests recreate the minimum the recorder requires.
    """
    conn = db._get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO languages (code, name, native_name, direction)"
        " VALUES ('ar', 'Arabic', 'العربية', 'rtl')"
    )
    conn.commit()


class TestRecorder:
    def test_dry_run_gates_pass_and_write_nothing(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        result = run_script(RECORDER, "--db-path", str(db_path), "--dry-run")
        assert result.returncode == 0, result.stderr
        assert "Pre-flight gates passed for 62 terms" in result.stdout
        db = TranslationDatabase(db_path=str(db_path))
        try:
            assert db.get_all_selected(language_code="ar") == []
        finally:
            db.close()

    def test_records_selections_and_python_correction(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        prepare_db(db_path)
        result = run_script(RECORDER, "--db-path", str(db_path))
        assert result.returncode == 0, result.stderr
        db = TranslationDatabase(db_path=str(db_path))
        try:
            js_terms = db.get_terms(programming_language="javascript")
            selected = {
                s["term_id"]: s["translation"]
                for s in db.get_all_selected(language_code="ar")
            }
            js_selected = [t for t in js_terms if t["id"] in selected]
            assert len(js_selected) == 62
            by_cat: dict[str, list[str]] = {}
            for t in js_selected:
                by_cat.setdefault(t["category"], []).append(selected[t["id"]])
            assert {k: len(v) for k, v in by_cat.items()} == {
                "keyword": 17,
                "builtin": 16,
                "member": 29,
            }
            # Rule 2: in-partition uniqueness straight from the DB
            for values in by_cat.values():
                assert len(values) == len(set(values))
            # Cross-target correction applied to the python row
            py_while = db.get_term_by_name("while", programming_language="python")
            assert selected[py_while["id"]] == "طالما"
            # Provenance on the suggestion pool
            suggestions = db.get_translations(language_code="ar", source="claude_agent")
            assert all(s["model_version"] == "claude-fable-5" for s in suggestions)
            assert all(s["model_rationale"] for s in suggestions)
        finally:
            db.close()

    def test_second_run_is_idempotent(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        prepare_db(db_path)
        assert run_script(RECORDER, "--db-path", str(db_path)).returncode == 0
        db = TranslationDatabase(db_path=str(db_path))
        try:
            before = len(db.get_translations(language_code="ar"))
        finally:
            db.close()
        second = run_script(RECORDER, "--db-path", str(db_path))
        assert second.returncode == 0, second.stderr
        db = TranslationDatabase(db_path=str(db_path))
        try:
            assert len(db.get_translations(language_code="ar")) == before
            selected = db.get_all_selected(language_code="ar")
            assert len(selected) == 63  # 62 js + 1 python correction
        finally:
            db.close()

    def test_unregistered_language_fails_loudly(self, tmp_path: Path) -> None:
        result = run_script(RECORDER, "--db-path", str(tmp_path / "empty.db"))
        assert result.returncode != 0
        assert "not in the languages registry" in result.stderr

    def test_unseeded_db_fails_loudly(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        db = TranslationDatabase(db_path=str(db_path))
        try:
            register_ar(db)
        finally:
            db.close()
        result = run_script(RECORDER, "--db-path", str(db_path))
        assert result.returncode != 0
        assert "not seeded" in result.stderr

    def test_missing_python_term_fails_loudly(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        assert run_script(SEEDER, "--db-path", str(db_path)).returncode == 0
        db = TranslationDatabase(db_path=str(db_path))
        try:
            register_ar(db)
        finally:
            db.close()
        result = run_script(RECORDER, "--db-path", str(db_path))
        assert result.returncode != 0
        assert "not found for correction" in result.stderr
