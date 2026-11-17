#!/usr/bin/env python3
"""Write each language's numeral system and decimal separator into translations.db.

The ``languages`` table held ``numeral_system`` in a house vocabulary
(``western_arabic``, ``arabic_indic``, ``devanagari``, ...) that was neither a
CLDR identifier nor complete: Urdu was recorded as Arabic-Indic though it
writes Extended Arabic-Indic, and Persian, Burmese and sixteen other languages
had no value. This script replaces every value with the CLDR identifier of the
locale's native numbering system and fills the ``decimal_separator`` column
(added by ``TranslationDatabase`` on open).

The values are CLDR 46's ``native`` numbering system for each locale and the
decimal symbol CLDR gives that locale with it. A language not named below
writes ASCII digits: ``latn`` and ``.``. That includes Amharic, Japanese,
Korean and Sinhala, whose CLDR native system is ``latn``, and Chinese, whose
native numerals (``一二三``, CLDR ``hanidec``) are not Unicode decimal digits:
its programs are written with ASCII digits.

Run it on a database that predates the identifiers, then regenerate the
registry with ``legesher_i18n/scripts/generate_languages.py``. Idempotent: a
second run changes nothing. ``--dry-run`` prints the changes and writes
nothing.

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
from legesher_i18n.numerals import LATIN, is_known_numeral_system

#: Language code to the CLDR identifier of its native numbering system, for
#: every language whose native system is not ``latn``.
NATIVE_NUMERAL_SYSTEMS: dict[str, str] = {
    "ar": "arab",
    "bn": "beng",
    "fa": "arabext",
    "gu": "gujr",
    "hi": "deva",
    "kn": "knda",
    "ml": "mlym",
    "my": "mymr",
    "ne": "deva",
    "te": "telu",
    "th": "thai",
    "ur": "arabext",
}

#: Language code to its decimal separator, where it is not ``.``.
DECIMAL_SEPARATORS: dict[str, str] = {
    "ar": "٫",  # ARABIC DECIMAL SEPARATOR
    "fa": "٫",
    "ur": "٫",
}


@dataclass(frozen=True)
class Change:
    """One language's values before and after."""

    code: str
    old_system: str | None
    new_system: str
    old_separator: str | None
    new_separator: str

    @property
    def changed(self) -> bool:
        return (self.old_system, self.old_separator) != (
            self.new_system,
            self.new_separator,
        )


def plan(conn: sqlite3.Connection) -> list[Change]:
    """The values every row of ``languages`` should hold, against what it holds.

    Reads a database whose ``languages`` table predates ``decimal_separator``
    as having none, so a dry run needs no schema change.
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(languages)")}
    separator = "decimal_separator" if "decimal_separator" in columns else "NULL"
    rows = conn.execute(
        f"SELECT code, numeral_system, {separator} FROM languages ORDER BY code"  # noqa: S608
    ).fetchall()
    return [
        Change(
            code=code,
            old_system=old_system,
            new_system=NATIVE_NUMERAL_SYSTEMS.get(code, LATIN),
            old_separator=old_separator,
            new_separator=DECIMAL_SEPARATORS.get(code, "."),
        )
        for code, old_system, old_separator in rows
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write each language's numeral system and decimal "
        "separator into translations.db."
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
        help="Print the changes without writing them.",
    )
    args = parser.parse_args(argv)

    for code, system in NATIVE_NUMERAL_SYSTEMS.items():
        if not is_known_numeral_system(system):
            print(f"ERROR: {code}: unknown numeral system {system!r}", file=sys.stderr)
            return 1

    db_path = args.db if args.db is not None else default_db_path()
    if not Path(db_path).exists():
        # Opening a missing path would create an empty database.
        print(f"ERROR: no database at {db_path}", file=sys.stderr)
        return 1
    if not args.dry_run:
        # Opening through TranslationDatabase adds the decimal_separator column
        # to a database that predates it.
        TranslationDatabase(db_path=str(db_path)).close()

    conn = sqlite3.connect(str(db_path))
    try:
        changes = plan(conn)
        pending = [c for c in changes if c.changed]
        for c in pending:
            print(
                f"{c.code}: numeral_system {c.old_system!r} -> {c.new_system!r}, "
                f"decimal_separator {c.old_separator!r} -> {c.new_separator!r}"
            )
        if args.dry_run:
            print(f"Dry run: {len(pending)} of {len(changes)} languages would change.")
            return 0
        with conn:
            for c in pending:
                conn.execute(
                    "UPDATE languages SET numeral_system = ?, decimal_separator = ?, "
                    "updated_at = datetime('now') WHERE code = ?",
                    (c.new_system, c.new_separator, c.code),
                )
    finally:
        conn.close()
    print(f"Updated {len(pending)} of {len(changes)} languages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
