#!/usr/bin/env python3
"""Add provenance columns to ``message_translations`` (CORE-1881).

The messages partition shipped without provenance: a rendering's row said
nothing about where it came from. This migration retrofits the three
columns the v2 schema now carries — ``source``, ``model_version``,
``created_by`` — onto a database whose partition predates them, so the
generation lane (``scripts/translate/generate_messages.py``) and the other
write paths can record provenance per rendering.

A carried-forward DB upgrade in the house sense: the consumers are repaired
with it, not just the schema — ``seed_message_templates.py`` and
``add_message_locale.py`` write the columns and REFUSE a database that does
not carry them (pointing here), rather than silently dropping provenance.

Semantics:

- **Additive and idempotent.** Only the missing columns among the three are
  added; a database that already carries all of them is a reported no-op. A
  partially-migrated database is completed, not refused — each ``ALTER
  TABLE ... ADD COLUMN`` is independent.
- **No backfill by default.** ``NULL`` means "not recorded", which is the
  truth for rows that predate the columns. When the operator KNOWS where
  every unattributed row came from (on the operational database, the
  catalog seeder was the only write path before this migration), pass
  ``--backfill-source seed`` to label them; the backfill touches only rows
  whose ``source`` is NULL, and stamps ``created_by`` with a backfill marker
  only where no writer is recorded, so the label stays distinguishable from
  write-time provenance.
- The messages partition stays outside the HF corpus one-way door; nothing
  here publishes.

Usage:
    python scripts/add_message_provenance.py --db legesher_i18n/db/translations.db
    python scripts/add_message_provenance.py --db ... --backfill-source seed
    python scripts/add_message_provenance.py --db ... --dry-run

Finish a real run with the durable-home push (libs/i18n/CLAUDE.md).
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

#: The columns this migration owns, in schema order. The single source of
#: truth for the set — the seeder's probe imports it, so a future fourth
#: column cannot be added here and missed there.
PROVENANCE_COLUMNS = ("source", "model_version", "created_by")

#: ``created_by`` marker for backfilled rows — write-time provenance names
#: the writing tool instead.
BACKFILL_MARKER = "add_message_provenance.py backfill"


def add_provenance(
    db_path: Path,
    *,
    backfill_source: str | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Add the missing provenance columns; optionally label NULL-source rows.

    Args:
        backfill_source: When set, rows whose ``source`` is NULL after the
            column additions get this label (and a backfill marker in
            ``created_by``). The operator asserts the origin; nothing is
            guessed.
        dry_run: Validate and simulate; write nothing.

    Returns:
        The column names that were added (empty when the schema already
        carried all three and no backfill applied).

    Raises:
        SystemExit: if the database is missing or does not carry the
            messages partition.
    """
    if not db_path.exists():
        raise SystemExit(f"database not found: {db_path}")

    connection = sqlite3.connect(db_path)
    # DDL autocommits under the sqlite3 module's legacy transaction
    # handling, which would make --dry-run a lie; manage explicitly (the
    # activate_messages_partition.py pattern).
    connection.isolation_level = None
    try:
        has_partition = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'message_translations'"
        ).fetchone()
        if has_partition is None:
            raise SystemExit(
                f"{db_path} does not carry the messages partition — run "
                "activate_messages_partition.py first (a fresh activation "
                "already includes the provenance columns)"
            )

        present = {
            row[1]
            for row in connection.execute("PRAGMA table_info(message_translations)")
        }
        missing = [name for name in PROVENANCE_COLUMNS if name not in present]

        connection.execute("BEGIN")
        for name in missing:
            connection.execute(
                # Column names come from PROVENANCE_COLUMNS, not input.
                f"ALTER TABLE message_translations ADD COLUMN {name} TEXT"  # nosec B608
            )

        backfilled = 0
        if backfill_source is not None:
            backfilled = connection.execute(
                # COALESCE: a row that already names its writer keeps it —
                # the marker only fills genuinely empty attribution.
                "UPDATE message_translations "
                "SET source = ?, created_by = COALESCE(created_by, ?) "
                "WHERE source IS NULL",
                (backfill_source, BACKFILL_MARKER),
            ).rowcount

        if dry_run:
            connection.execute("ROLLBACK")
        else:
            connection.execute("COMMIT")

        if not missing and backfilled == 0:
            print(
                f"message_translations in {db_path} already carries "
                f"{PROVENANCE_COLUMNS} — nothing to do"
            )
        return missing
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", type=Path, required=True, help="translations database to migrate"
    )
    parser.add_argument(
        "--backfill-source",
        default=None,
        help=(
            "label rows whose source is NULL with this value (operator "
            "asserts the origin — on the operational database, 'seed')"
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and simulate; write nothing"
    )
    args = parser.parse_args()

    added = add_provenance(
        args.db, backfill_source=args.backfill_source, dry_run=args.dry_run
    )
    mode = "DRY RUN — rolled back" if args.dry_run else "committed"
    if added:
        print(f"{mode}: added {', '.join(added)} to message_translations")
    if args.backfill_source is not None:
        print(f"{mode}: NULL-source rows labeled {args.backfill_source!r}")


if __name__ == "__main__":
    main()
