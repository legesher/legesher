#!/usr/bin/env python3
"""Seed message_templates / message_translations from a catalog seed file.

The message tables shipped with the v2 schema deliberately empty ("created,
inert" — sentences with grammar, not vocabulary). This seeder is the designed
fill path for a catalog seed such as ``db/seeds/v8_jej_messages.json``
(CORE-1378): hand-curated templates keyed by (implementation, key,
version_added), with per-locale translations entering at the ``machine``
review rung.

Read-only with respect to everything else: it INSERTs only into the two
message tables, refuses to touch a database that already carries ANY row for
the seed's ``(implementation, version_added)`` pair — deliberately stricter
than per-key: partial prior seeds are ambiguous states — and never opens the
operational v1 ``translations.db`` (the v2 file is a build artifact until the
cutover gate passes).

Validation before any write:
- identity keys unique within the seed;
- placeholder parity: every ``{name}`` used in the English template and each
  translation is declared in ``placeholders`` (after stripping ``{{ }}``
  escapes), and vice versa;
- stored templates carry no bidi control characters — isolation of
  interpolated values is a render-time concern (see the ratified
  code-vs-display policy), stored strings stay clean and reviewable;
- every translation locale exists in ``locales`` (fail with instructions, do
  not create locales as a side effect).

Usage:
    python seed_message_templates.py --db path/to/translations_v2.db \
        [--seed path/to/seed.json] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from legesher_i18n.db.schema_v2 import connect  # noqa: E402

DEFAULT_SEED = (
    Path(__file__).parent.parent / "legesher_i18n" / "db" / "seeds" / "v8_jej_messages.json"
)

# Codepoints forbidden in STORED templates (render-time isolation only).
FORBIDDEN_BIDI = {
    0x2066, 0x2067, 0x2068, 0x2069,
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x200E, 0x200F, 0x061C,
}

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def used_placeholders(template: str) -> set[str]:
    """Placeholder names a template interpolates, ignoring ``{{ }}`` escapes."""
    stripped = template.replace("{{", "").replace("}}", "")
    return set(PLACEHOLDER.findall(stripped))


def validate_seed(seed: dict) -> list[str]:
    """Returns a list of human-readable problems; empty means valid."""
    problems: list[str] = []
    templates = seed.get("templates", [])
    keys = [t["key"] for t in templates]
    for key in {k for k in keys if keys.count(k) > 1}:
        problems.append(f"duplicate key in seed: {key}")

    for t in templates:
        declared = {p["name"] for p in t.get("placeholders", [])}
        surfaces = {"template_en": t["template_en"]} | {
            f"translations[{loc}]": tr["template"]
            for loc, tr in t.get("translations", {}).items()
        }
        for label, text in surfaces.items():
            used = used_placeholders(text)
            if used != declared:
                problems.append(
                    f"{t['key']}: {label} placeholders {sorted(used)} != declared {sorted(declared)}"
                )
            bad = [f"U+{ord(ch):04X}" for ch in text if ord(ch) in FORBIDDEN_BIDI]
            if bad:
                problems.append(f"{t['key']}: {label} stores bidi controls {bad}")
    return problems


def seed_database(db_path: Path, seed: dict, *, dry_run: bool = False) -> tuple[int, int]:
    """Inserts the seed; returns (templates_inserted, translations_inserted)."""
    implementation = seed["implementation"]
    version_added = seed["version_added"]
    templates = seed["templates"]

    # schema_v2.connect() is the stated contract for every v2 consumer: it
    # turns on foreign_keys AND recursive_triggers per-connection.
    connection = connect(db_path)
    try:
        locales_needed = sorted({loc for t in templates for loc in t.get("translations", {})})
        known: set[str] = set()
        if locales_needed:
            known = {
                row[0]
                for row in connection.execute(
                    # Only the placeholder COUNT is interpolated; values are
                    # bound parameters.
                    f"SELECT tag FROM locales WHERE tag IN ({','.join('?' * len(locales_needed))})",  # nosec B608
                    locales_needed,
                )
            }
        missing = [loc for loc in locales_needed if loc not in known]
        if missing:
            raise SystemExit(
                f"locales missing from the target database: {missing} — "
                "seed locales through the registry path first; this seeder "
                "never creates locales as a side effect"
            )

        existing = connection.execute(
            "SELECT key FROM message_templates WHERE implementation = ? AND version_added = ?",
            (implementation, version_added),
        ).fetchall()
        if existing:
            raise SystemExit(
                f"refusing to seed: {len(existing)} message_templates rows already exist "
                f"for ({implementation}, version_added={version_added}) — the seeder is "
                "append-once; revisions land as a new version_added"
            )

        inserted_templates = 0
        inserted_translations = 0
        for t in templates:
            cursor = connection.execute(
                "INSERT INTO message_templates "
                "(implementation, key, template_en, placeholders, version_added) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    implementation,
                    t["key"],
                    t["template_en"],
                    json.dumps(t.get("placeholders", []), ensure_ascii=False),
                    version_added,
                ),
            )
            inserted_templates += 1
            template_id = cursor.lastrowid
            for locale, tr in t.get("translations", {}).items():
                connection.execute(
                    "INSERT INTO message_translations (template_id, locale, template, status) "
                    "VALUES (?, ?, ?, ?)",
                    (template_id, locale, tr["template"], tr.get("status", "machine")),
                )
                inserted_translations += 1

        if dry_run:
            connection.rollback()
        else:
            connection.commit()
        return inserted_templates, inserted_translations
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True, help="v2 database file to seed")
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED, help="seed JSON file")
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and simulate; write nothing"
    )
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"database not found: {args.db} (build it with migrate_to_v2.py)")

    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    problems = validate_seed(seed)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        raise SystemExit(f"seed invalid: {len(problems)} problem(s)")

    templates, translations = seed_database(args.db, seed, dry_run=args.dry_run)
    mode = "DRY RUN — rolled back" if args.dry_run else "committed"
    print(
        f"{mode}: {templates} message_templates + {translations} message_translations "
        f"({seed['implementation']}, version_added={seed['version_added']})"
    )


if __name__ == "__main__":
    main()
