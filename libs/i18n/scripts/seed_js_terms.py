#!/usr/bin/env python3
"""Seed the JavaScript/JEJ term inventory into ``translations.db`` (CORE-1371).

The source of truth is the context corpus index (``context/javascript/
index.json``, CORE-1370/CORE-1571): one entry per term of the JEJ teaching
surface, category included. This script materializes that inventory as rows
in the ``terms`` table (``programming_language='javascript'``) so the
translation pipeline can run with ``--target javascript`` — the pipeline
refuses to invent term rows for non-python targets by design.

Safety properties (mirroring ``seed_message_templates.py``):

* Validates the corpus split (17 keywords / 16 builtins / 29 members = 62)
  before any write, so a drifted corpus fails loudly instead of seeding.
* Refuses to run when javascript terms already exist — revisions land by
  re-seeding into a fresh state deliberately, never by silent upsert.
* ``--dry-run`` prints the plan and touches nothing.
* Never touches python rows, and never writes translations — terms only.

Categories are stored as the corpus states them (``keyword`` / ``builtin`` /
``member``): target-neutral names, deliberately not overloading the
python-flavoured ``builtin_func``/``builtin_type`` split.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from legesher_i18n.db.database import TranslationDatabase  # noqa: E402

CORPUS_INDEX = Path(__file__).parent.parent / "context" / "javascript" / "index.json"

# The JEJ surface accounting this seeder refuses to drift from
# (Legesher-owned surface, CORE-1581/CORE-1571).
EXPECTED_SPLIT = {"keyword": 17, "builtin": 16, "member": 29}


def load_inventory(index_path: Path) -> list[dict]:
    """Read the corpus index and validate the surface split."""
    with open(index_path, encoding="utf-8") as fh:
        data = json.load(fh)

    documents = data["documents"]
    counts: dict[str, int] = {}
    for entry in documents:
        counts[entry["category"]] = counts.get(entry["category"], 0) + 1

    if counts != EXPECTED_SPLIT:
        raise SystemExit(
            f"corpus split {counts} != expected {EXPECTED_SPLIT} — "
            "the index and the JEJ surface have drifted; fix that first "
            "(the split expectation lives in this script and in "
            "@legesher/jej surface tests)."
        )
    return documents


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed JavaScript/JEJ terms into translations.db (CORE-1371)"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Database path (default: the packaged translations.db)",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=CORPUS_INDEX,
        help="Corpus index to seed from (default: context/javascript/index.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without writing",
    )
    args = parser.parse_args()

    documents = load_inventory(args.index_path)

    db = (
        TranslationDatabase(db_path=str(args.db_path))
        if args.db_path
        else TranslationDatabase()
    )
    try:
        existing = db.get_terms(programming_language="javascript")
        if existing:
            raise SystemExit(
                f"{len(existing)} javascript terms already seeded — refusing "
                'to re-seed. Inspect with: sqlite3 <db> "SELECT name, category '
                "FROM terms WHERE programming_language='javascript'\""
            )

        print(f"Seeding {len(documents)} javascript terms ({EXPECTED_SPLIT})")
        if args.dry_run:
            for entry in sorted(documents, key=lambda e: (e["category"], e["term"])):
                print(f"  [dry-run] {entry['category']:8} {entry['term']}")
            print("Dry run — nothing written.")
            return 0

        for entry in documents:
            db.get_or_create_term(
                name=entry["term"],
                programming_language="javascript",
                category=entry["category"],
            )

        seeded = db.get_terms(programming_language="javascript")
        assert len(seeded) == len(documents), "post-seed count mismatch"
        print(f"Seeded {len(seeded)} terms. Done.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
