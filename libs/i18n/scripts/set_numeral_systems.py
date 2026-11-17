#!/usr/bin/env python3
"""Fill each language's numeral system and decimal separator in translations.db.

The ``languages`` table held ``numeral_system`` in a house vocabulary
(``western_arabic``, ``arabic_indic``, ``devanagari``, ...) that was neither a
CLDR identifier nor complete: Urdu was recorded as Arabic-Indic though it
writes Extended Arabic-Indic, and Persian, Burmese, Kannada and fifteen other
languages had no value. This script replaces those values with CLDR
identifiers and fills the ``decimal_separator`` column (added by
``TranslationDatabase`` on open).

It changes only what predates the identifiers: a ``numeral_system`` that is
empty or in the old vocabulary, and an empty ``decimal_separator``. A value
already written as a CLDR identifier, or as an allowed separator, is left as
recorded, so a later deliberate edit survives a second run. A row the script
cannot fill (a language missing from the table below, or a value it does not
recognise) stops the run before anything is written, and names the row.

The table is CLDR 46's ``native`` numbering system for each published locale
when that system is a Unicode decimal-digit block, and ``latn`` otherwise:
Amharic, Japanese, Korean and Sinhala, whose CLDR native system is ``latn``,
and Chinese, whose native numerals (``〇一二三``, CLDR ``hanidec``) are not
decimal digits Python reads. The separator is CLDR's decimal symbol for the
native system (U+066B for Arabic, Persian and Urdu), and ``.`` for a language
that writes ASCII digits, the mark a numeric literal in code uses.

Run it on a database that predates the identifiers, then regenerate the
registry with ``legesher_i18n/scripts/generate_languages.py``. A new language
does not come through here: give its row a CLDR identifier and a separator
when you add it. ``--dry-run`` opens the database read-only and prints what
would change.

Usage:
    uv run --no-sync python libs/i18n/scripts/set_numeral_systems.py [--db PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from legesher_i18n.db import TranslationDatabase, default_db_path
from legesher_i18n.numerals import (
    DECIMAL_SEPARATORS,
    LATIN,
    is_known_numeral_system,
)

#: Every published language's numeral system, as the registry should hold it.
NUMERAL_SYSTEMS: dict[str, str] = {
    "am": LATIN,
    "ar": "arab",
    "bn": "beng",
    "bs": LATIN,
    "ca": LATIN,
    "cs": LATIN,
    "cy": LATIN,
    "da": LATIN,
    "de": LATIN,
    "el": LATIN,
    "en": LATIN,
    "es": LATIN,
    "fa": "arabext",
    "fi": LATIN,
    "fr": LATIN,
    "ga": LATIN,
    "gd": LATIN,
    "gl": LATIN,
    "gu": "gujr",
    "he": LATIN,
    "hi": "deva",
    "hr": LATIN,
    "hu": LATIN,
    "id": LATIN,
    "it": LATIN,
    "ja": LATIN,
    "kn": "knda",
    "ko": LATIN,
    "lv": LATIN,
    "mk": LATIN,
    "ml": "mlym",
    "mn": LATIN,
    "ms": LATIN,
    "my": "mymr",
    "ne": "deva",
    "nl": LATIN,
    "no": LATIN,
    "pl": LATIN,
    "pt": LATIN,
    "ro": LATIN,
    "ru": LATIN,
    "si": LATIN,
    "sr": LATIN,
    "su": LATIN,
    "sv": LATIN,
    "sw": LATIN,
    "te": "telu",
    "th": "thai",
    "tl": LATIN,
    "tr": LATIN,
    "uk": LATIN,
    "ur": "arabext",
    "uz": LATIN,
    "vi": LATIN,
    "xh": LATIN,
    "zh": LATIN,
}

#: Language code to its decimal separator, where it is not ``.``.
SEPARATORS: dict[str, str] = {
    "ar": "٫",  # ARABIC DECIMAL SEPARATOR
    "fa": "٫",
    "ur": "٫",
}

#: The values the column held before CLDR identifiers. ``thai`` was in that
#: vocabulary too, and is also the CLDR identifier, so it is kept as it is.
LEGACY_VALUES = frozenset(
    {
        "western_arabic",
        "arabic_indic",
        "devanagari",
        "bengali",
        "gujarati",
        "malayalam",
        "telugu",
        "western",
        "latin",
    }
)


@dataclass(frozen=True)
class Row:
    """One language's values as recorded and as they should be written."""

    code: str
    old_system: str | None
    new_system: str | None
    old_separator: str | None
    new_separator: str | None

    @property
    def changed(self) -> bool:
        return (self.old_system, self.old_separator) != (
            self.new_system,
            self.new_separator,
        )

    @property
    def unresolved(self) -> bool:
        return self.new_system is None or self.new_separator is None


def _resolve(code: str, system: str | None, separator: str | None) -> Row:
    if system is None or system in LEGACY_VALUES:
        new_system = NUMERAL_SYSTEMS.get(code)
    elif is_known_numeral_system(system):
        new_system = system
    else:
        new_system = None
    if separator is None:
        new_separator = SEPARATORS.get(code, ".") if code in NUMERAL_SYSTEMS else None
    elif separator in DECIMAL_SEPARATORS:
        new_separator = separator
    else:
        new_separator = None
    return Row(code, system, new_system, separator, new_separator)


def plan(conn: sqlite3.Connection) -> list[Row]:
    """Every row of ``languages``, as recorded and as it should be written.

    Reads a database whose ``languages`` table predates ``decimal_separator``
    as having none, so a dry run needs no schema change.
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(languages)")}
    separator = "decimal_separator" if "decimal_separator" in columns else "NULL"
    rows = conn.execute(
        f"SELECT code, numeral_system, {separator} FROM languages ORDER BY code"  # noqa: S608
    ).fetchall()
    return [_resolve(code, system, sep) for code, system, sep in rows]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fill each language's numeral system and decimal "
        "separator in translations.db."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to translations.db (defaults to the working database).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Open the database read-only and print the changes.",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.db if args.db is not None else default_db_path())
    if not db_path.exists():
        # Opening a missing path would create an empty database.
        print(f"ERROR: no database at {db_path}", file=sys.stderr)
        return 1
    # The plan is read through a read-only connection: a read-write one that
    # closes last folds the write-ahead log into the main file, and a run that
    # stops on a row it cannot fill, or a dry run, must leave the file as it
    # found it.
    reader = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        rows = plan(reader)
    finally:
        reader.close()

    unresolved = [r for r in rows if r.unresolved]
    if unresolved:
        for r in unresolved:
            print(
                f"ERROR: {r.code}: cannot fill numeral_system "
                f"{r.old_system!r} / decimal_separator {r.old_separator!r}; "
                f"set its CLDR identifier and separator by hand",
                file=sys.stderr,
            )
        print("Nothing was written.", file=sys.stderr)
        return 1
    pending = [r for r in rows if r.changed]
    for r in pending:
        print(
            f"{r.code}: numeral_system {r.old_system!r} -> {r.new_system!r}, "
            f"decimal_separator {r.old_separator!r} -> {r.new_separator!r}"
        )
    for r in rows:
        if r.new_system != NUMERAL_SYSTEMS.get(r.code, r.new_system):
            print(
                f"{r.code}: numeral_system {r.new_system!r} left as recorded "
                f"(this script would write {NUMERAL_SYSTEMS[r.code]!r})"
            )
    if args.dry_run:
        print(f"Dry run: {len(pending)} of {len(rows)} languages would change.")
        return 0

    # Opening through TranslationDatabase adds the decimal_separator column to
    # a database that predates it.
    TranslationDatabase(db_path=str(db_path)).close()
    conn = sqlite3.connect(str(db_path))
    try:
        with conn:
            for r in pending:
                conn.execute(
                    "UPDATE languages SET numeral_system = ?, decimal_separator = ?, "
                    "updated_at = datetime('now') WHERE code = ?",
                    (r.new_system, r.new_separator, r.code),
                )
    finally:
        conn.close()
    print(f"Updated {len(pending)} of {len(rows)} languages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
