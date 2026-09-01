#!/usr/bin/env python3
"""Add a locale to EXISTING message templates (CORE-1850).

``seed_message_templates.py`` seeds templates and their translations together
and is append-once by design: a database already carrying rows for a seed's
``(implementation, version_added)`` pair is refused, because a reworded
message must become a new row rather than silently invalidate an existing
translation. That guard leaves no path for the other legitimate operation —
adding a LANGUAGE to templates that already exist. Inventing a new
``version_added`` for it would be a lie (the templates did not change), and a
direct INSERT skips every validation the seeder exists to perform.

This script is that path. It inserts ONLY into ``message_translations``,
against template rows that are already present, and reuses the seeder's
validation rather than reimplementing it:

- **placeholder parity** — every ``{name}`` in a translation is declared in
  its template's ``placeholders`` and vice versa, after stripping ``{{ }}``
  escapes. The load-bearing check: a translation that renders ``{name}`` as
  ``{nom}`` breaks substitution silently, and the failure only surfaces in a
  learner's traceback;
- **no bidi control characters** in stored strings (isolation of interpolated
  values is a render-time concern);
- **locale exists** — in ``locales`` on a v2 build, in ``languages`` on the
  operational v1 file (which predates ``locales``); never created here as a
  side effect;
- **complete coverage** — the addition names every ``(key, version_added)``
  template row of the implementation exactly once, version-tiered rewordings
  included. All-or-nothing: a locale is either fully present or absent, never
  half-written;
- **idempotence** — re-running an addition whose rows are already stored
  identically is an explicit no-op. Stored rows matching the addition are
  kept (their review ``status`` belongs to the review process and is not
  compared) and only missing rows are inserted, so a locale completed
  before a later version tier was seeded can catch up; a stored row whose
  TEMPLATE differs refuses the whole run, and nothing is ever duplicated
  (``UNIQUE (template_id, locale)`` backs this at the schema level).

Translations enter at the ``machine`` review rung unless the entry says
otherwise, same as the seeder.

Addition file format::

    {
      "implementation": "cpython",
      "locale": "fr",
      "source": "claude_agent",            // provenance (CORE-1881), required
      "model_version": "claude-...",       // optional
      "created_by": "generate_messages.py",// optional
      "translations": [
        {"key": "ZeroDivisionError.division_by_zero", "version_added": "3.10",
         "template": "division par zéro", "status": "machine"},
        ...
      ]
    }

Provenance is per addition, recorded on every inserted row; an addition
without a ``source`` is refused — renderings do not enter unattributed.

Usage:
    python add_message_locale.py --db path/to/translations.db \
        --file path/to/fr_addition.json [--dry-run]

After a real run, finish with the durable-home push (libs/i18n/CLAUDE.md,
"Durable home & sync ritual") — an unpushed database change exists only on
one workstation.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from legesher_i18n.db.schema_v2 import connect  # noqa: E402

try:  # imported as part of the `scripts` package (tests)
    from .seed_message_templates import (
        ALLOWED_STATUSES,
        bidi_controls,
        missing_locales,
        probe_database,
        used_placeholders,
    )
except ImportError:  # run as a script: the scripts dir itself is sys.path[0]
    from seed_message_templates import (  # noqa: E402
        ALLOWED_STATUSES,
        bidi_controls,
        missing_locales,
        probe_database,
        used_placeholders,
    )


def _template_rows(
    connection: sqlite3.Connection, implementation: str
) -> dict[tuple[str, str | None], dict]:
    """The implementation's template rows, keyed by ``(key, version_added)``."""
    rows = connection.execute(
        "SELECT id, key, version_added, placeholders FROM message_templates "
        "WHERE implementation = ?",
        (implementation,),
    ).fetchall()
    return {
        (key, version_added): {
            "id": row_id,
            "declared": {p["name"] for p in json.loads(placeholders_json or "[]")},
        }
        for row_id, key, version_added, placeholders_json in rows
    }


def _validate_shape(addition: dict) -> list[str]:
    """Structural problems with the addition file; empty means well-formed."""
    problems = [
        f"addition file has no {field!r} field"
        for field in ("implementation", "locale", "source", "translations")
        if field not in addition
    ]
    if "source" in addition:
        source = addition["source"]
        # Presence is not attribution: a null/blank source would store the
        # exact NULL the provenance migration reserves for pre-migration rows.
        if not isinstance(source, str) or not source.strip():
            problems.append(
                f"'source' must be a non-empty string, got {source!r} — "
                "renderings do not enter unattributed"
            )
    for index, entry in enumerate(addition.get("translations") or []):
        for field in ("key", "template"):
            if not isinstance(entry.get(field), str):
                problems.append(f"translations[{index}] has no {field!r} string")
    return problems


def _validate_entries(
    entries: list[dict], templates: dict[tuple[str, str | None], dict]
) -> list[str]:
    """Human-readable problems with the addition's entries; empty means valid."""
    problems: list[str] = []

    identities = [(e["key"], e.get("version_added")) for e in entries]
    for identity in {i for i in identities if identities.count(i) > 1}:
        problems.append(f"duplicate entry for {identity} in the addition file")

    covered = set()
    for entry in entries:
        identity = (entry["key"], entry.get("version_added"))
        label = f"{identity[0]}@{identity[1]}"
        template = templates.get(identity)
        if template is None:
            problems.append(
                f"{label}: no such (key, version_added) template row — the "
                "addition targets existing templates only; new or reworded "
                "templates land through seed_message_templates.py"
            )
            continue
        covered.add(identity)

        status = entry.get("status", "machine")
        if status not in ALLOWED_STATUSES:
            problems.append(
                f"{label}: status {status!r} is not one of {ALLOWED_STATUSES}"
            )

        used = used_placeholders(entry["template"])
        if used != template["declared"]:
            problems.append(
                f"{label}: translation placeholders {sorted(used)} != "
                f"declared {sorted(template['declared'])}"
            )
        bad = bidi_controls(entry["template"])
        if bad:
            problems.append(f"{label}: translation stores bidi controls {bad}")

    for key, version_added in sorted(
        set(templates) - covered, key=lambda i: (i[0], i[1] or "")
    ):
        problems.append(
            f"{key}@{version_added}: template row not covered — a locale "
            "addition is all-or-nothing across the implementation's templates"
        )
    return problems


def add_locale(db_path: Path, addition: dict, *, dry_run: bool = False) -> int:
    """Insert one locale's translations against existing template rows.

    Args:
        addition: Parsed addition file (see the module docstring).
        dry_run: Validate and simulate; write nothing.

    Returns:
        Translations inserted — 0 when every row was already stored
        identically (the explicit no-op). Stored rows that match the
        addition are kept and only missing ones are inserted, so a locale
        completed before a later version tier was seeded can catch up.

    Raises:
        SystemExit: on any validation problem, an unknown locale, or
            stored rows for the locale whose template text differs from the
            addition. Stored ``status`` is deliberately NOT compared — once
            a row exists its review rung belongs to the review process, and
            a promotion must not make an identical re-run look like a
            revision.
    """
    shape_problems = _validate_shape(addition)
    if shape_problems:
        raise SystemExit(
            "addition malformed: "
            + f"{len(shape_problems)} problem(s)\n  - "
            + "\n  - ".join(shape_problems)
        )
    implementation = addition["implementation"]
    locale = addition["locale"]
    entries = addition["translations"]

    is_v2 = probe_database(db_path)
    connection = connect(db_path) if is_v2 else sqlite3.connect(db_path)
    try:
        missing = missing_locales(connection, is_v2, [locale])
        if missing:
            raise SystemExit(
                f"locale missing from the target database: {missing} — "
                "seed locales through the registry path first; this script "
                "never creates locales as a side effect"
            )

        templates = _template_rows(connection, implementation)
        if not templates:
            raise SystemExit(
                f"no message_templates rows for implementation "
                f"{implementation!r} in {db_path} — seed the catalog first "
                "(seed_message_templates.py)"
            )

        problems = _validate_entries(entries, templates)
        if problems:
            raise SystemExit(
                "addition invalid: "
                + f"{len(problems)} problem(s)\n  - "
                + "\n  - ".join(problems)
            )

        stored = {
            (key, version_added): template
            for key, version_added, template in connection.execute(
                "SELECT t.key, t.version_added, tr.template "
                "FROM message_translations tr "
                "JOIN message_templates t ON t.id = tr.template_id "
                "WHERE t.implementation = ? AND tr.locale = ?",
                (implementation, locale),
            )
        }
        desired = {
            (e["key"], e.get("version_added")): (
                e["template"],
                e.get("status", "machine"),
            )
            for e in entries
        }
        # Coverage guarantees desired spans every template row, so stored
        # (a subset of the template rows, by FK) is always a subset of
        # desired's identities. Stored rows whose TEMPLATE matches are kept
        # — their status belongs to the review process — and only missing
        # rows are inserted, so a locale completed before a later version
        # tier was seeded can catch up. Any template divergence is refused:
        # revisions are not locale additions.
        diverging = sorted(
            f"{key}@{version_added}"
            for (key, version_added), template in stored.items()
            if desired[(key, version_added)][0] != template
        )
        if diverging:
            raise SystemExit(
                f"locale '{locale}' already carries {len(stored)} "
                f"message_translations row(s) for {implementation!r} and "
                f"{len(diverging)} of them differ from the addition "
                f"({', '.join(diverging[:5])}) — refusing to guess; "
                "revisions are not locale additions"
            )
        missing = {i: v for i, v in desired.items() if i not in stored}
        if not missing:
            print(
                f"locale '{locale}' already carries all "
                f"{len(stored)} translations identically — nothing to do"
            )
            return 0

        inserted = 0
        for identity, (template, status) in missing.items():
            connection.execute(
                "INSERT INTO message_translations "
                "(template_id, locale, template, status, "
                " source, model_version, created_by) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    templates[identity]["id"],
                    locale,
                    template,
                    status,
                    addition["source"],
                    addition.get("model_version"),
                    addition.get("created_by"),
                ),
            )
            inserted += 1

        if dry_run:
            connection.rollback()
        else:
            connection.commit()
        return inserted
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", type=Path, required=True, help="translations database to write"
    )
    parser.add_argument(
        "--file", type=Path, required=True, help="locale-addition JSON file"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and simulate; write nothing"
    )
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"database not found: {args.db}")
    if not args.file.exists():
        raise SystemExit(f"addition file not found: {args.file}")

    addition = json.loads(args.file.read_text(encoding="utf-8"))
    inserted = add_locale(args.db, addition, dry_run=args.dry_run)
    mode = "DRY RUN — rolled back" if args.dry_run else "committed"
    if inserted:
        print(
            f"{mode}: {inserted} message_translations for locale "
            f"'{addition['locale']}' ({addition['implementation']})"
        )


if __name__ == "__main__":
    main()
