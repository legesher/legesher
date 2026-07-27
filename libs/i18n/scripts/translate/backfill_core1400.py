#!/usr/bin/env python3
"""CORE-1400 backfill: make selected_translations the complete, clean
canonical layer for pack regeneration.

What this script does (idempotent, in order):

1. **Terms-uniqueness migration** — rebuilds the ``terms`` table with
   ``UNIQUE(name, programming_language, category)`` (was
   ``UNIQUE(name, programming_language)``) so the same surface token can
   hold two pack slots. Term ids are preserved, so ``translations`` /
   ``selected_translations`` references stay valid.
2. **Dual-slot ``type`` term** — inserts the Python 3.12 soft-keyword
   ``type`` (PEP 695) as its own term row (category ``keyword``,
   ``version_added='3.12'``). 22 languages ship a 3.12 keyword value
   that differs from their 3.10 builtin ``type`` value; without a second
   term row those values are unrepresentable and a regen would destroy
   them.
3. **Canonical selection backfill** — for every ``(term, language)``
   slot in the 51 shipped packs, applies the documented selection rule
   (``docs/translation-selection.md``): the shipped pack value anchors,
   subject to the validity gate. Ensures a matching candidate row exists
   in ``translations`` (inserting ``source='yaml_pack'`` provenance rows
   where the pack value was never imported, e.g. the ``en`` identity
   values for ``self``/``cls``/``except*``) and a ``selected_translations``
   row for every slot. Existing selections that already match the pack
   are left untouched; a conflicting existing selection is an error.

The candidate pool (``translations``) is intentionally left dirty —
tolerating raw model output there is by design; the selection layer is
what must be clean.

Usage:

    uv run python scripts/translate/backfill_core1400.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import yaml

_SCRIPT_DIR = Path(__file__).resolve().parent
_I18N_ROOT = _SCRIPT_DIR.parent.parent
sys.path.insert(0, str(_I18N_ROOT))

from legesher_i18n.db import TranslationDatabase  # noqa: E402
from legesher_i18n.selection import select_canonical  # noqa: E402

# Pack YAML section -> acceptable term categories, in resolution order.
from legesher_i18n.term_definitions import (  # noqa: E402
    YAML_SECTION_CATEGORIES as SECTION_CATEGORIES,
)

DB_PATH = _I18N_ROOT / "legesher_i18n" / "db" / "translations.db"
PACKS_DIR = _I18N_ROOT / "language-packs" / "python"

SELECTED_BY = "CORE-1400"
SELECTION_REASON = "CORE-1400 canonical backfill: shipped-pack-value"


def migrate_terms_uniqueness(db_path: Path, dry_run: bool) -> bool:
    """Rebuild terms with UNIQUE(name, programming_language, category).

    Returns True if a migration was applied (False when already done).
    """
    conn = sqlite3.connect(db_path)
    try:
        (sql,) = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='terms'"
        ).fetchone()
        if "UNIQUE(name, programming_language, category)" in sql:
            print("terms uniqueness migration: already applied")
            return False
        if dry_run:
            print("terms uniqueness migration: WOULD apply (dry run)")
            return False

        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("BEGIN")
        conn.execute("""
            CREATE TABLE terms_core1400 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                programming_language TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                version_added TEXT,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(name, programming_language, category)
            )
            """)
        conn.execute("""
            INSERT INTO terms_core1400 (id, name, programming_language,
                category, subcategory, version_added, description,
                created_at, updated_at)
            SELECT id, name, programming_language, category, subcategory,
                version_added, description, created_at, updated_at
            FROM terms
            """)
        conn.execute("DROP TABLE terms")
        conn.execute("ALTER TABLE terms_core1400 RENAME TO terms")
        conn.execute("CREATE INDEX idx_terms_category ON terms(category)")
        conn.execute("CREATE INDEX idx_terms_lang ON terms(programming_language)")
        conn.commit()
        print("terms uniqueness migration: applied")
        return True
    finally:
        conn.close()


def load_pack_slots(lang: str) -> list[tuple[str, str, str]]:
    """Yield (section, term_name, value) slots for a language's packs.

    Later version files override earlier ones only for the SAME
    (section, term) slot; ``type`` in 3.12 ``keywords`` is a different
    slot from ``type`` in 3.10 ``builtins`` and both are returned.
    """
    pack_dir = PACKS_DIR / lang / f"legesher_i18n_python_{lang}" / "packs"
    slots: dict[tuple[str, str], str] = {}
    for version_file in sorted(pack_dir.glob("*.yml")):
        data = yaml.safe_load(version_file.read_text(encoding="utf-8")) or {}
        for section in SECTION_CATEGORIES:
            for key, value in (data.get(section) or {}).items():
                if value is None:  # placeholder comment keys
                    continue
                slots[(section, str(key))] = str(value)
    return [(section, term, value) for (section, term), value in slots.items()]


def pack_languages() -> list[str]:
    return sorted(
        d.name
        for d in PACKS_DIR.iterdir()
        if d.is_dir() and (d / f"legesher_i18n_python_{d.name}").exists()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    migrate_terms_uniqueness(args.db, args.dry_run)

    db = TranslationDatabase(db_path=str(args.db))

    # Step 2: dual-slot 'type' keyword term (PEP 695).
    if not args.dry_run:
        keyword_type_id = db.get_or_create_term(
            "type",
            "python",
            category="keyword",
            subcategory="soft_keyword",
            allow_duplicate_name=True,
        )
        conn = db._get_connection()
        conn.execute(
            "UPDATE terms SET version_added = '3.12', description = COALESCE("
            "description, 'Soft keyword for type alias statements (PEP 695); "
            "distinct pack slot from the type() builtin') WHERE id = ?",
            (keyword_type_id,),
        )
        conn.commit()
        print(f"keyword 'type' term id: {keyword_type_id}")

    # Resolve term ids per (section, name).
    conn = db._get_connection()
    term_rows = conn.execute(
        "SELECT id, name, category FROM terms WHERE programming_language='python'"
    ).fetchall()
    by_name: dict[str, list[tuple[int, str]]] = {}
    for tid, name, category in term_rows:
        by_name.setdefault(name, []).append((tid, category))

    stats = {
        "slots": 0,
        "selected_kept": 0,
        "selected_added": 0,
        "candidates_added": 0,
        "conflicts": 0,
        "invalid_pack_values": 0,
        "unresolved_terms": 0,
    }
    problems: list[str] = []

    for lang in pack_languages():
        for section, term, value in load_pack_slots(lang):
            stats["slots"] += 1

            # Resolve the term row for this slot.
            categories = SECTION_CATEGORIES[section]
            candidates_rows = [
                (tid, cat) for tid, cat in by_name.get(term, []) if cat in categories
            ]
            if len(candidates_rows) != 1:
                stats["unresolved_terms"] += 1
                problems.append(
                    f"{lang} {section}.{term}: expected exactly one term row, "
                    f"found {candidates_rows}"
                )
                continue
            term_id = candidates_rows[0][0]

            # The selection rule, pack value as anchor.
            pool = db.get_translations(term_id=term_id, language_code=lang)
            result = select_canonical(term, pool, pack_value=value)
            if result is None or result.translation != value:
                # Shipped value failed the gate — surface it, don't guess.
                stats["invalid_pack_values"] += 1
                problems.append(
                    f"{lang} {section}.{term}: shipped value {value!r} failed "
                    f"the validity gate (selection rule returned "
                    f"{result.translation if result else None!r})"
                )
                continue

            existing = db.get_selected(term_id, lang)
            if existing is not None:
                if existing["translation"] == value:
                    stats["selected_kept"] += 1
                    continue
                stats["conflicts"] += 1
                problems.append(
                    f"{lang} {section}.{term}: selected "
                    f"{existing['translation']!r} != pack {value!r}"
                )
                continue

            if args.dry_run:
                stats["selected_added"] += 1
                continue

            # Ensure a candidate row backs the selection (provenance).
            if not any(row["translation"] == value for row in pool):
                db.add_translation(
                    term_id=term_id,
                    language_code=lang,
                    translation=value,
                    source="yaml_pack",
                    created_by="CORE-1400",
                )
                stats["candidates_added"] += 1

            db.set_selected(
                term_id=term_id,
                language_code=lang,
                translation=value,
                selected_by=SELECTED_BY,
                selection_reason=SELECTION_REASON,
            )
            stats["selected_added"] += 1

    print("\n=== CORE-1400 backfill summary ===")
    for key, count in stats.items():
        print(f"  {key}: {count}")
    if problems:
        print("\n=== problems (no changes made for these slots) ===")
        for problem in problems:
            print(f"  {problem}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
