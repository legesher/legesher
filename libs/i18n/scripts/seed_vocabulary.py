#!/usr/bin/env python3
"""Seed the vocabulary partition's inventory and its English values (CORE-1396).

Two writes, both fully deterministic and both idempotent:

1. **The canonical inventory** — one ``vocabulary_entries`` row per slug in
   ``legesher_i18n/vocabulary_definitions.py``. That module is the single
   source of truth; this script only projects it into the database, so
   re-running after an inventory edit converges (entries are UPSERTed on
   ``(section, slug, programming_language)``) rather than forking.

2. **The ``en`` values** — English is *seeded, never generated*. A symbol's
   English name and a role's English idiom are already stated in the
   inventory; asking a model to produce them would be paying to reproduce a
   constant, and would introduce drift where there is none. They enter both
   the candidate pool (source ``canonical``) and the selection layer.

Every other locale comes from ``scripts/translate/generate_vocabulary.py``.

Read-only with respect to everything else: this script touches the three
``vocabulary_*`` / ``selected_vocabulary`` tables and nothing else. It never
writes a pack file — regeneration is a separate, deliberate step
(``scripts/export_packs.py``), because pack writes are authoritative.

Usage:
    python scripts/seed_vocabulary.py --db legesher_i18n/db/translations.db
    python scripts/seed_vocabulary.py --db ... --dry-run
    python scripts/seed_vocabulary.py --db ... --inventory-only

Remember the durable-home ritual afterwards (libs/i18n/CLAUDE.md): the
database is an untracked working copy, so an unpushed seed exists on one
workstation only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from legesher_i18n.db import TranslationDatabase  # noqa: E402
from legesher_i18n.vocabulary_definitions import (  # noqa: E402
    VOCABULARY_SECTIONS,
    english_values,
    inventory_for_section,
)

#: Provenance label for values that come from the inventory itself rather
#: than from a model or a reviewer. Distinct from every source in
#: ``selection.SOURCE_TRUST`` on purpose: those rank machine output against
#: human output, and this is neither — it is a constant.
CANONICAL_SOURCE = "canonical"

#: The language whose vocabulary is definitional rather than translated.
SEED_LANGUAGE = "en"


def seed_inventory(db: TranslationDatabase, *, dry_run: bool) -> dict[str, int]:
    """Project the canonical inventory into ``vocabulary_entries``."""
    counts: dict[str, int] = {}
    for section in VOCABULARY_SECTIONS:
        entries = inventory_for_section(section)
        counts[section] = len(entries)
        if dry_run:
            continue
        for position, entry in enumerate(entries):
            english = (
                entry.english_name if section == "symbols" else entry.english_value
            )
            db.get_or_create_vocabulary_entry(
                section=section,
                slug=entry.slug,
                english_value=english,
                role=entry.role,
                sort_order=position,
            )
    return counts


def seed_english(db: TranslationDatabase, *, dry_run: bool) -> int:
    """Record and select the English value for every inventory slug.

    Raises:
        RuntimeError: If the inventory has not been seeded yet — selecting
            a value for an entry that does not exist would fail row by row
            with a less useful message.
    """
    written = 0
    for section in VOCABULARY_SECTIONS:
        by_slug = {
            row["slug"]: row["id"] for row in db.get_vocabulary_entries(section=section)
        }
        for slug, value in english_values(section).items():
            entry_id = by_slug.get(slug)
            if entry_id is None:
                raise RuntimeError(
                    f"No vocabulary entry for {section}.{slug}; run the "
                    "inventory seed first (this script, without "
                    "--english-only)."
                )
            if dry_run:
                written += 1
                continue
            db.add_vocabulary_translation(
                entry_id=entry_id,
                language_code=SEED_LANGUAGE,
                value=value,
                source=CANONICAL_SOURCE,
                confidence="high",
                model_rationale=(
                    "English is the source language: this value IS the "
                    "canonical inventory entry, not a translation of it."
                ),
                created_by="seed_vocabulary.py",
            )
            # The publish gate runs inside set_selected_vocabulary, so a
            # bad inventory value fails here rather than at export time.
            db.set_selected_vocabulary(
                entry_id=entry_id,
                language_code=SEED_LANGUAGE,
                value=value,
                selected_by="seed_vocabulary.py",
                selection_reason="canonical-english",
            )
            written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--db",
        default=None,
        help="Path to translations.db (default: the package's resolved path)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be written; write nothing",
    )
    parser.add_argument(
        "--inventory-only",
        action="store_true",
        help="Seed vocabulary_entries but not the English values",
    )
    parser.add_argument(
        "--english-only",
        action="store_true",
        help="Seed the English values only (inventory must already exist)",
    )
    args = parser.parse_args(argv)

    if args.inventory_only and args.english_only:
        parser.error("--inventory-only and --english-only are mutually exclusive")

    with TranslationDatabase(db_path=args.db) as db:
        if not args.english_only:
            counts = seed_inventory(db, dry_run=args.dry_run)
            total = sum(counts.values())
            detail = ", ".join(f"{s}={n}" for s, n in counts.items())
            print(
                f"{'Would seed' if args.dry_run else 'Seeded'} {total} "
                f"inventory entries ({detail})"
            )

        if not args.inventory_only:
            written = seed_english(db, dry_run=args.dry_run)
            print(
                f"{'Would seed' if args.dry_run else 'Seeded'} {written} "
                f"'{SEED_LANGUAGE}' values"
            )

        coverage = db.get_vocabulary_coverage()
        if coverage:
            print("\nSelected-value coverage by language:")
            for language_code in sorted(coverage):
                per_section = coverage[language_code]
                detail = ", ".join(
                    f"{section}={per_section.get(section, 0)}"
                    for section in VOCABULARY_SECTIONS
                )
                print(f"  {language_code}: {detail}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
