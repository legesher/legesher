"""set_numeral_systems.py: CLDR identifiers and separators into the languages table."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.language_registry import get_active_language_codes
from legesher_i18n.numerals import is_known_numeral_system
from scripts.set_numeral_systems import (
    DECIMAL_SEPARATORS,
    NATIVE_NUMERAL_SYSTEMS,
    main,
)

#: Rows as the working database held them before CLDR identifiers.
_LEGACY = [
    ("ar", "arabic_indic"),
    ("ur", "arabic_indic"),
    ("fa", None),
    ("my", None),
    ("hi", "devanagari"),
    ("zh", "western_arabic"),
    ("es", "western_arabic"),
    ("am", None),
]


def _legacy_db(path: Path, *, with_separator_column: bool) -> Path:
    """A languages table shaped like the one before this change."""
    conn = sqlite3.connect(path)
    separator = "decimal_separator TEXT," if with_separator_column else ""
    conn.execute(
        "CREATE TABLE languages (code TEXT PRIMARY KEY, name TEXT NOT NULL, "
        "native_name TEXT NOT NULL, numeral_system TEXT, "
        f"{separator} updated_at TEXT)"
    )
    for code, system in _LEGACY:
        conn.execute(
            "INSERT INTO languages (code, name, native_name, numeral_system) "
            "VALUES (?, ?, ?, ?)",
            (code, code, code, system),
        )
    conn.commit()
    conn.close()
    return path


def _values(path: Path) -> dict[str, tuple[str, str]]:
    conn = sqlite3.connect(path)
    try:
        return {
            code: (system, separator)
            for code, system, separator in conn.execute(
                "SELECT code, numeral_system, decimal_separator FROM languages"
            )
        }
    finally:
        conn.close()


def test_every_named_system_is_known() -> None:
    for code, system in NATIVE_NUMERAL_SYSTEMS.items():
        assert is_known_numeral_system(system), (code, system)
    assert set(DECIMAL_SEPARATORS) <= set(NATIVE_NUMERAL_SYSTEMS)


def test_every_named_language_is_published() -> None:
    # A mistyped code would leave the real language at latn without a word.
    published = set(get_active_language_codes())
    assert set(NATIVE_NUMERAL_SYSTEMS) <= published
    assert set(DECIMAL_SEPARATORS) <= published


def test_replaces_the_legacy_vocabulary(tmp_path: Path) -> None:
    db = _legacy_db(tmp_path / "t.db", with_separator_column=False)
    assert main(["--db", str(db)]) == 0
    assert _values(db) == {
        "ar": ("arab", "٫"),
        "ur": ("arabext", "٫"),
        "fa": ("arabext", "٫"),
        "my": ("mymr", "."),
        "hi": ("deva", "."),
        "zh": ("latn", "."),
        "es": ("latn", "."),
        "am": ("latn", "."),
    }


def test_second_run_changes_nothing(tmp_path: Path, capsys) -> None:
    db = _legacy_db(tmp_path / "t.db", with_separator_column=True)
    assert main(["--db", str(db)]) == 0
    before = db.read_bytes()
    capsys.readouterr()
    assert main(["--db", str(db)]) == 0
    assert "Updated 0 of 8 languages." in capsys.readouterr().out
    assert db.read_bytes() == before


@pytest.mark.parametrize("with_separator_column", [True, False])
def test_dry_run_writes_nothing(
    tmp_path: Path, capsys, with_separator_column: bool
) -> None:
    db = _legacy_db(tmp_path / "t.db", with_separator_column=with_separator_column)
    before = db.read_bytes()
    assert main(["--db", str(db), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "ur: numeral_system 'arabic_indic' -> 'arabext'" in out
    assert "Dry run: 8 of 8 languages would change." in out
    assert db.read_bytes() == before


def test_missing_database_is_not_created(tmp_path: Path) -> None:
    missing = tmp_path / "absent" / "translations.db"
    assert main(["--db", str(missing)]) != 0
    assert not missing.exists()
