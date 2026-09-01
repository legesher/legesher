#!/usr/bin/env python3
"""Seed message_templates / message_translations from a catalog seed file.

The message tables shipped with the v2 schema deliberately empty ("created,
inert" — sentences with grammar, not vocabulary). This seeder is the designed
fill path for a catalog seed such as ``db/seeds/v8_jej_messages.json``
(CORE-1378): hand-curated templates keyed by (implementation, key,
version_added), with per-locale translations entering at the ``machine``
review rung.

Read-only with respect to everything else: it INSERTs only into the two
message tables and refuses to touch a database that already carries ANY row
for one of the seed's ``(implementation, version_added)`` pairs —
deliberately stricter than per-key: partial prior seeds are ambiguous states.

Validation before any write:
- identity keys unique within the seed — per ``(key, version_added)``, since a
  reworded message is a NEW row under the same key (CORE-1679: CPython 3.12
  rewordings must not invalidate 3.11's translations);
- placeholder parity: every ``{name}`` used in the English template and each
  translation is declared in ``placeholders`` (after stripping ``{{ }}``
  escapes), and vice versa;
- matcher discipline (when a template carries a ``matcher``): the regex
  compiles, is anchored at both ends, its NAMED groups are exactly the
  declared placeholders, and it round-trips its own English template — the
  template rendered with the placeholder examples must fullmatch and give
  every example back from its group;
- stored templates carry no bidi control characters — isolation of
  interpolated values is a render-time concern (see the ratified
  code-vs-display policy), stored strings stay clean and reviewable;
- every translation locale exists in ``locales`` — or, on the operational v1
  database (which predates ``locales``), in ``languages`` (fail with
  instructions, do not create locales as a side effect).

Since CORE-1679 the messages partition also lives in the operational
``translations.db`` (activated by ``activate_messages_partition.py``); this
seeder targets whichever database carries the partition. Per-template
``version_added`` / ``version_removed`` override the seed-level default, so
one catalog file can carry version-tiered rewordings.

Usage:
    python seed_message_templates.py --db path/to/translations.db \
        [--seed path/to/seed.json] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from legesher_i18n.db.schema_v2 import connect  # noqa: E402

try:  # imported as part of the `scripts` package (tests)
    from .add_message_provenance import PROVENANCE_COLUMNS
except ImportError:  # run as a script: the scripts dir itself is sys.path[0]
    from add_message_provenance import PROVENANCE_COLUMNS  # noqa: E402

DEFAULT_SEED = (
    Path(__file__).parent.parent
    / "legesher_i18n"
    / "db"
    / "seeds"
    / "v8_jej_messages.json"
)

# Codepoints forbidden in STORED templates (render-time isolation only).
FORBIDDEN_BIDI = {
    0x2066,
    0x2067,
    0x2068,
    0x2069,
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x200E,
    0x200F,
    0x061C,
}

PLACEHOLDER = re.compile(r"\{(\w+)\}")

#: The ``message_translations.status`` CHECK set, mirrored for callers that
#: validate input files before writing (``add_message_locale.py`` reports a
#: bad status as a named problem instead of a SQLite CHECK error).
ALLOWED_STATUSES = ("machine", "experimental", "reviewed", "official")


def used_placeholders(template: str) -> set[str]:
    """Placeholder names a template interpolates, ignoring ``{{ }}`` escapes."""
    stripped = template.replace("{{", "").replace("}}", "")
    return set(PLACEHOLDER.findall(stripped))


def bidi_controls(text: str) -> list[str]:
    """The forbidden bidi control codepoints ``text`` carries, as U+ labels."""
    return [f"U+{ord(ch):04X}" for ch in text if ord(ch) in FORBIDDEN_BIDI]


def _has_table(connection: sqlite3.Connection, name: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone()
        is not None
    )


def probe_database(db_path: Path) -> bool:
    """Check ``db_path`` is a translations database with an active partition.

    Returns:
        True when the database is a v2 build (carries ``locales``), False for
        the operational v1 file (carries ``languages``).

    Raises:
        SystemExit: if the database is missing (checked first — a bare
            ``sqlite3.connect`` would CREATE an empty file as a side
            effect), if the file is neither flavor, if the messages
            partition is not activated in it, or if the partition predates
            the provenance columns (CORE-1881) — the write paths record
            provenance and must not silently drop it.
    """
    if not db_path.exists():
        raise SystemExit(f"database not found: {db_path}")
    probe = sqlite3.connect(db_path)
    try:
        is_v2 = _has_table(probe, "locales")
        if not is_v2 and not _has_table(probe, "languages"):
            raise SystemExit(
                f"{db_path} has neither `locales` (v2) nor `languages` (v1) — "
                "not a translations database"
            )
        if not _has_table(probe, "message_templates"):
            raise SystemExit(
                f"{db_path} does not carry the messages partition — run "
                "activate_messages_partition.py first (v1) or rebuild the v2 artifact"
            )
        present = {
            row[1] for row in probe.execute("PRAGMA table_info(message_translations)")
        }
        missing_columns = [name for name in PROVENANCE_COLUMNS if name not in present]
        if missing_columns:
            raise SystemExit(
                f"message_translations in {db_path} predates the provenance "
                f"columns (missing {missing_columns}) — run "
                "scripts/add_message_provenance.py first; the write paths "
                "record provenance and will not silently drop it"
            )
    finally:
        probe.close()
    return is_v2


def missing_locales(
    connection: sqlite3.Connection, is_v2: bool, locales_needed: list[str]
) -> list[str]:
    """The subset of ``locales_needed`` the target database does not know.

    On a v2 build locales live in ``locales``; the operational v1 file
    predates that table, so validation falls back to ``languages``.
    """
    if not locales_needed:
        return []
    locale_sql = (
        "SELECT tag FROM locales WHERE tag IN ({})"
        if is_v2
        else "SELECT code FROM languages WHERE code IN ({})"
    )
    known = {
        row[0]
        for row in connection.execute(
            # Only the placeholder COUNT is interpolated; values are
            # bound parameters.
            locale_sql.format(",".join("?" * len(locales_needed))),  # nosec B608
            locales_needed,
        )
    }
    return [locale for locale in locales_needed if locale not in known]


def render_example(template: str, placeholders: list[dict]) -> str:
    """Substitute each declared placeholder's example into the template.

    Literal replacement, NOT ``str.format``: templates may legitimately carry
    stray braces (CPython's ``f-string: valid expression required before '}'``)
    that ``str.format`` would choke on.
    """
    rendered = template
    for p in placeholders:
        rendered = rendered.replace("{" + p["name"] + "}", p["example"])
    return rendered


def validate_matcher(t: dict) -> list[str]:
    """Matcher discipline for one template; empty list means valid."""
    matcher = t.get("matcher")
    if matcher is None:
        return []
    problems: list[str] = []
    try:
        rx = re.compile(matcher)
    except re.error as exc:
        return [f"{t['key']}: matcher does not compile: {exc}"]
    if not matcher.startswith("^") or not matcher.endswith("$"):
        problems.append(f"{t['key']}: matcher must be anchored (^...$): {matcher!r}")
    declared = {p["name"] for p in t.get("placeholders", [])}
    if set(rx.groupindex) != declared:
        problems.append(
            f"{t['key']}: matcher named groups {sorted(rx.groupindex)} "
            f"!= declared placeholders {sorted(declared)}"
        )
        return problems
    examples = {p["name"]: p["example"] for p in t.get("placeholders", [])}
    rendered = render_example(t["template_en"], t.get("placeholders", []))
    match = rx.fullmatch(rendered)
    if match is None:
        problems.append(
            f"{t['key']}: matcher does not fullmatch its own rendered "
            f"template_en example: {rendered!r}"
        )
    elif match.groupdict() != examples:
        problems.append(
            f"{t['key']}: matcher round-trip {match.groupdict()} != examples {examples}"
        )
    return problems


def template_version_added(t: dict, seed: dict) -> str:
    """A template's ``version_added``: its own, else the seed-level default."""
    return t.get("version_added", seed["version_added"])


def validate_seed(seed: dict) -> list[str]:
    """Returns a list of human-readable problems; empty means valid."""
    problems: list[str] = []
    templates = seed.get("templates", [])
    identities = [(t["key"], template_version_added(t, seed)) for t in templates]
    for identity in {i for i in identities if identities.count(i) > 1}:
        problems.append(f"duplicate (key, version_added) in seed: {identity}")

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
            bad = bidi_controls(text)
            if bad:
                problems.append(f"{t['key']}: {label} stores bidi controls {bad}")
        for locale, tr in t.get("translations", {}).items():
            if "source" in tr:
                source = tr["source"]
                # An explicit-but-empty source would store the NULL the
                # provenance migration reserves for pre-migration rows.
                if not isinstance(source, str) or not source.strip():
                    problems.append(
                        f"{t['key']}: translations[{locale}] 'source' must be "
                        f"a non-empty string, got {source!r}"
                    )
        problems.extend(validate_matcher(t))
    return problems


def seed_database(
    db_path: Path, seed: dict, *, dry_run: bool = False
) -> tuple[int, int]:
    """Inserts the seed; returns (templates_inserted, translations_inserted)."""
    implementation = seed["implementation"]
    templates = seed["templates"]

    # A v2 build carries `locales` and gets the stated v2 connection contract
    # (foreign_keys + recursive_triggers ON). The operational v1 file carries
    # `languages` instead — its message-partition FK targets do not exist, so
    # the connection must keep foreign_keys OFF (SQLite resolves FK targets at
    # DML time) and locale validation happens against `languages` here.
    is_v2 = probe_database(db_path)

    connection = connect(db_path) if is_v2 else sqlite3.connect(db_path)
    try:
        locales_needed = sorted(
            {loc for t in templates for loc in t.get("translations", {})}
        )
        missing = missing_locales(connection, is_v2, locales_needed)
        if missing:
            raise SystemExit(
                f"locales missing from the target database: {missing} — "
                "seed locales through the registry path first; this seeder "
                "never creates locales as a side effect"
            )

        versions_in_seed = sorted({template_version_added(t, seed) for t in templates})
        for version in versions_in_seed:
            existing = connection.execute(
                "SELECT key FROM message_templates WHERE implementation = ? AND version_added = ?",
                (implementation, version),
            ).fetchall()
            if existing:
                raise SystemExit(
                    f"refusing to seed: {len(existing)} message_templates rows already exist "
                    f"for ({implementation}, version_added={version}) — the seeder is "
                    "append-once; revisions land as a new version_added"
                )

        inserted_templates = 0
        inserted_translations = 0
        for t in templates:
            cursor = connection.execute(
                "INSERT INTO message_templates "
                "(implementation, key, template_en, placeholders, matcher, "
                " version_added, version_removed) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    implementation,
                    t["key"],
                    t["template_en"],
                    json.dumps(t.get("placeholders", []), ensure_ascii=False),
                    t.get("matcher"),
                    template_version_added(t, seed),
                    t.get("version_removed"),
                ),
            )
            inserted_templates += 1
            template_id = cursor.lastrowid
            for locale, tr in t.get("translations", {}).items():
                connection.execute(
                    "INSERT INTO message_translations "
                    "(template_id, locale, template, status, "
                    " source, model_version, created_by) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        template_id,
                        locale,
                        tr["template"],
                        tr.get("status", "machine"),
                        # Provenance (CORE-1881): catalog seeds are curated
                        # files, so the row's origin is the seed itself
                        # unless the entry states otherwise.
                        tr.get("source", "seed"),
                        tr.get("model_version"),
                        "seed_message_templates.py",
                    ),
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
    parser.add_argument(
        "--db", type=Path, required=True, help="v2 database file to seed"
    )
    parser.add_argument(
        "--seed", type=Path, default=DEFAULT_SEED, help="seed JSON file"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and simulate; write nothing"
    )
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(
            f"database not found: {args.db} (build it with migrate_to_v2.py)"
        )

    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    problems = validate_seed(seed)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        raise SystemExit(f"seed invalid: {len(problems)} problem(s)")

    templates, translations = seed_database(args.db, seed, dry_run=args.dry_run)
    mode = "DRY RUN — rolled back" if args.dry_run else "committed"
    versions = sorted({template_version_added(t, seed) for t in seed["templates"]})
    print(
        f"{mode}: {templates} message_templates + {translations} message_translations "
        f"({seed['implementation']}, version_added={', '.join(versions)})"
    )


if __name__ == "__main__":
    main()
