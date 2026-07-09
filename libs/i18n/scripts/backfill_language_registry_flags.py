#!/usr/bin/env python3
"""One-time backfill: seed the DB language-registry columns from languages.json.

CORE-611. ``translations.db`` becomes the single source of truth for the
published language registry. Three sets of facts previously lived (partly or
wholly) only in ``languages.json`` and are copied into the DB here so the DB can
fully regenerate the json:

- ``in_registry`` — which languages are published. The json shipped a curated
  subset of the DB's languages, with no column encoding that choice. The
  published set is exactly the languages present in languages.json.
- ``has_case_distinction`` — per-language script metadata consumed by the prompt
  builder; it had no column in the DB.
- ``iso639_2`` / ``bcp47`` — present for every language in the json but NULL in
  the DB for ~half of them.

After this runs, ``generate_languages.py`` regenerates languages.json from the
DB with no data loss.

Idempotent: re-running sets the same values. Reads languages.json as the seed
source; safe to delete once the DB is the established source of truth.

Usage:
    uv run python libs/i18n/scripts/backfill_language_registry_flags.py
"""

import json
import sqlite3
from pathlib import Path

from legesher_i18n.db import TranslationDatabase

I18N_PKG = Path(__file__).resolve().parent.parent / "legesher_i18n"
LANGUAGES_JSON = I18N_PKG / "languages.json"
DB_PATH = I18N_PKG / "db" / "translations.db"


def main() -> int:
    languages = json.loads(LANGUAGES_JSON.read_text(encoding="utf-8"))["languages"]

    # Instantiate once so _init_db adds the has_case_distinction / in_registry
    # columns to the (pre-CORE-611) committed database before we write to them.
    TranslationDatabase().close()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        # Reset membership, then mark + seed the published set. Doing it in this
        # order (rather than a dynamic NOT IN clause) keeps the SQL static.
        conn.execute("UPDATE languages SET in_registry = 0")
        for code, meta in languages.items():
            conn.execute(
                "UPDATE languages SET "
                "iso639_2 = ?, bcp47 = ?, has_case_distinction = ?, "
                "in_registry = 1, updated_at = datetime('now') "
                "WHERE code = ?",
                (
                    meta["iso639_2"],
                    meta["bcp47"],
                    1 if meta["has_case_distinction"] else 0,
                    code,
                ),
            )
        conn.commit()

        published = conn.execute(
            "SELECT count(*) FROM languages WHERE in_registry = 1"
        ).fetchone()[0]
        total = conn.execute("SELECT count(*) FROM languages").fetchone()[0]
    finally:
        conn.close()

    print(f"Seeded {len(languages)} published languages from {LANGUAGES_JSON.name}")
    print(f"in_registry = 1: {published} / {total} total languages")
    if published != len(languages):
        print(
            "WARNING: some json languages were not found in the DB "
            f"({len(languages) - published} unmatched)"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
