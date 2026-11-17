"""set_numeral_systems.py: CLDR identifiers and separators into the languages table."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.language_registry import (
    get_active_language_codes,
    get_decimal_separator,
    get_numeral_system,
)
from legesher_i18n.numerals import DECIMAL_SEPARATORS, is_known_numeral_system
from scripts.set_numeral_systems import NUMERAL_SYSTEMS, SEPARATORS, main

#: Rows as the working database held them before CLDR identifiers.
_LEGACY = [
    ("ar", "arabic_indic"),
    ("ur", "arabic_indic"),
    ("fa", None),
    ("my", None),
    ("kn", None),
    ("hi", "devanagari"),
    ("th", "thai"),
    ("zh", "western_arabic"),
    ("es", "western_arabic"),
    ("am", None),
]


def _legacy_db(path: Path, *, with_separator_column: bool, extra=()) -> Path:
    """A languages table shaped like the one before this change."""
    conn = sqlite3.connect(path)
    separator = "decimal_separator TEXT," if with_separator_column else ""
    conn.execute(
        "CREATE TABLE languages (code TEXT PRIMARY KEY, name TEXT NOT NULL, "
        "native_name TEXT NOT NULL, numeral_system TEXT, "
        f"{separator} updated_at TEXT)"
    )
    for code, system, *rest in [*_LEGACY, *extra]:
        conn.execute(
            "INSERT INTO languages (code, name, native_name, numeral_system) "
            "VALUES (?, ?, ?, ?)",
            (code, code, code, system),
        )
        if rest:
            conn.execute(
                "UPDATE languages SET decimal_separator = ? WHERE code = ?",
                (rest[0], code),
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


def test_table_agrees_with_the_registry() -> None:
    # The table is the migration's record of the languages published when it
    # ran; a language added since is given its values by hand, not here.
    published = set(get_active_language_codes())
    assert set(NUMERAL_SYSTEMS) <= published
    for code in NUMERAL_SYSTEMS:
        assert is_known_numeral_system(NUMERAL_SYSTEMS[code]), code
        assert NUMERAL_SYSTEMS[code] == get_numeral_system(code), code
        assert SEPARATORS.get(code, ".") == get_decimal_separator(code), code
    assert set(SEPARATORS.values()) <= DECIMAL_SEPARATORS


def test_replaces_the_legacy_vocabulary(tmp_path: Path) -> None:
    db = _legacy_db(tmp_path / "t.db", with_separator_column=False)
    assert main(["--db", str(db)]) == 0
    assert _values(db) == {
        "ar": ("arab", "٫"),
        "ur": ("arabext", "٫"),
        "fa": ("arabext", "٫"),
        "my": ("mymr", "."),
        "kn": ("knda", "."),
        "hi": ("deva", "."),
        "th": ("thai", "."),
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
    assert "Updated 0 of 10 languages." in capsys.readouterr().out
    assert db.read_bytes() == before


def test_a_recorded_identifier_is_left_alone(tmp_path: Path, capsys) -> None:
    # A value already written as a CLDR identifier is someone's decision,
    # even where this script's table says otherwise.
    db = _legacy_db(tmp_path / "t.db", with_separator_column=True)
    assert main(["--db", str(db)]) == 0
    conn = sqlite3.connect(db)
    conn.execute("UPDATE languages SET numeral_system = 'arab' WHERE code = 'ur'")
    conn.commit()
    conn.close()
    capsys.readouterr()
    assert main(["--db", str(db)]) == 0
    out = capsys.readouterr().out
    assert "ur: numeral_system 'arab' left as recorded" in out
    assert _values(db)["ur"] == ("arab", "٫")


@pytest.mark.parametrize(
    ("extra", "named"),
    [
        # A language added later, with no value: the script cannot know it.
        ([("ta", None)], "ta"),
        # The same with its separator already recorded: the numeral system
        # alone must stop the run.
        ([("ta", None, ".")], "ta"),
        # A value outside both vocabularies.
        ([("ta", "tamil")], "ta"),
    ],
)
def test_unfillable_row_stops_the_run_before_writing(
    tmp_path: Path, capsys, extra, named: str
) -> None:
    db = _legacy_db(tmp_path / "t.db", with_separator_column=True, extra=extra)
    before = db.read_bytes()
    assert main(["--db", str(db)]) == 1
    err = capsys.readouterr().err
    assert f"ERROR: {named}:" in err
    assert "Nothing was written." in err
    assert db.read_bytes() == before


def test_disallowed_separator_stops_the_run(tmp_path: Path, capsys) -> None:
    db = _legacy_db(tmp_path / "t.db", with_separator_column=True)
    conn = sqlite3.connect(db)
    # U+066C is the Arabic thousands separator, the likeliest typo for U+066B.
    conn.execute("UPDATE languages SET decimal_separator = '٬' WHERE code = 'ar'")
    conn.commit()
    conn.close()
    assert main(["--db", str(db)]) == 1
    assert "ERROR: ar:" in capsys.readouterr().err


@pytest.mark.parametrize("with_separator_column", [True, False])
def test_dry_run_writes_nothing(
    tmp_path: Path, capsys, with_separator_column: bool
) -> None:
    db = _legacy_db(tmp_path / "t.db", with_separator_column=with_separator_column)
    before = db.read_bytes()
    assert main(["--db", str(db), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "ur: numeral_system 'arabic_indic' -> 'arabext'" in out
    # Thai already holds its CLDR identifier; its separator is still filled.
    assert "th: numeral_system 'thai' -> 'thai', decimal_separator None -> '.'" in out
    assert "Dry run: 10 of 10 languages would change." in out
    assert db.read_bytes() == before


def test_dry_run_leaves_an_unflushed_write_ahead_log_alone(tmp_path: Path) -> None:
    # Both working databases run in WAL mode. A snapshot taken while a writer
    # is open carries committed frames in the -wal file; a read-write
    # connection that closed last would fold them into the main file.
    live = _legacy_db(tmp_path / "live.db", with_separator_column=True)
    holder = sqlite3.connect(live)
    holder.execute("PRAGMA journal_mode=WAL")
    holder.execute("UPDATE languages SET name = 'Arabic' WHERE code = 'ar'")
    holder.commit()
    snapshot = tmp_path / "snap"
    snapshot.mkdir()
    for suffix in ("", "-wal", "-shm"):
        shutil.copy(f"{live}{suffix}", snapshot / f"t.db{suffix}")
    holder.close()
    db = snapshot / "t.db"
    assert (snapshot / "t.db-wal").stat().st_size > 0
    # Any reader updates the shared-memory index (-shm); the data lives in
    # the main file and the log, and neither may change.
    data = {name: (snapshot / name).read_bytes() for name in ("t.db", "t.db-wal")}
    assert main(["--db", str(db), "--dry-run"]) == 0
    assert {name: (snapshot / name).read_bytes() for name in data} == data


def test_missing_database_is_not_created(tmp_path: Path) -> None:
    missing = tmp_path / "absent" / "translations.db"
    assert main(["--db", str(missing)]) != 0
    assert not missing.exists()
