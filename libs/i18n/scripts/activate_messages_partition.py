#!/usr/bin/env python3
"""Activate the messages partition in an existing translations database (CORE-1679).

Schema v2 ships ``message_templates`` / ``message_translations`` /
``message_endorsements`` as DEFERRED — created inert in a fresh v2 build, and
absent from the operational v1 ``translations.db``. This migration creates the
three tables (with their indexes and append-only triggers) in an existing
database, so the messages track can go live ahead of the v2 cutover.

Safety posture, in the order the schema reference establishes it:

- The messages partition is explicitly EXCLUDED from the HF corpus one-way
  door: nothing here is publish-frozen. Publishing message translations stays
  gated on ``message_translations`` gaining content-addressed keys (see
  ``message_endorsements`` in ``docs/schema-v2-reference.md``).
- The DDL is never re-declared here: :func:`messages_partition_ddl` reads it
  back from ``schema_v2.sql`` via a throwaway in-memory build, so this script
  cannot drift from the schema.
- Idempotent: a database that already carries all three tables is a no-op
  (reported, exit 0). A database carrying only SOME of them is an ambiguous
  state and is refused.
- Additive only: no existing table, row, index, or trigger is touched.
- **v2-cutover gap**: ``scripts/migrate_to_v2.py`` does NOT carry the
  partition's rows into a v2 build — a v2 build re-seeds them from the
  catalog seed files via ``seed_message_templates.py``. The migration
  refuses a source carrying message rows unless the operator acknowledges
  this with ``--acknowledge-message-rows-not-migrated``.

Foreign keys: on the operational v1 file the partition's FK targets
(``locales``, ``concepts``, ``contributors``, ``review_sessions``,
``review_rungs``) do not exist. SQLite resolves FK targets at DML time and
enforcement is per-connection, so the tables create cleanly; writers to the
partition on a v1 database must keep ``PRAGMA foreign_keys`` OFF on their
connection and validate locales against ``languages`` themselves (the seeder
does exactly that).

Usage:
    python scripts/activate_messages_partition.py --db legesher_i18n/db/translations.db
    python scripts/activate_messages_partition.py --db ... --dry-run
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from legesher_i18n.db.schema_v2 import (  # noqa: E402
    MESSAGE_PARTITION_TABLES,
    messages_partition_ddl,
)


def existing_partition_tables(connection: sqlite3.Connection) -> set[str]:
    """The subset of the partition's tables already present in the database."""
    placeholders = ",".join("?" * len(MESSAGE_PARTITION_TABLES))
    rows = connection.execute(
        "SELECT name FROM sqlite_master "  # nosec B608 - placeholder count only
        f"WHERE type = 'table' AND name IN ({placeholders})",
        MESSAGE_PARTITION_TABLES,
    ).fetchall()
    return {row[0] for row in rows}


def activate(db_path: Path, *, dry_run: bool = False) -> list[str]:
    """Create the messages partition in ``db_path`` if it is not there yet.

    Args:
        db_path: An existing translations database (v1 operational file or a
            v2 build).
        dry_run: Validate and report, write nothing.

    Returns:
        The DDL statements that were applied (empty list when the partition
        was already active).

    Raises:
        SystemExit: if the database is missing, or carries a partial
            partition (ambiguous state — restore from git or finish by hand).
    """
    if not db_path.exists():
        raise SystemExit(f"database not found: {db_path}")

    # Plain connection on purpose: see the module docstring — the partition's
    # FK targets are absent on the v1 operational file, and enabling
    # foreign_keys here would make every future INSERT on this connection fail.
    connection = sqlite3.connect(db_path)
    # DDL autocommits under the sqlite3 module's legacy transaction handling,
    # which would make --dry-run a lie; manage the transaction explicitly.
    connection.isolation_level = None
    try:
        present = existing_partition_tables(connection)
        if present == set(MESSAGE_PARTITION_TABLES):
            print(f"messages partition already active in {db_path} — nothing to do")
            return []
        if present:
            raise SystemExit(
                f"partial messages partition in {db_path}: found {sorted(present)}, "
                f"expected none or all of {sorted(MESSAGE_PARTITION_TABLES)} — refusing "
                "to guess; restore the database from git and re-run"
            )

        statements = messages_partition_ddl()
        connection.execute("BEGIN")
        for statement in statements:
            connection.execute(statement)
        if dry_run:
            connection.execute("ROLLBACK")
        else:
            connection.execute("COMMIT")
        return statements
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="existing translations database to migrate",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="validate and simulate; write nothing"
    )
    args = parser.parse_args()

    statements = activate(args.db, dry_run=args.dry_run)
    if statements:
        mode = "DRY RUN — rolled back" if args.dry_run else "committed"
        tables = sum(
            1 for s in statements if s.lstrip().upper().startswith("CREATE TABLE")
        )
        indexes = sum(1 for s in statements if "INDEX" in s.lstrip().upper()[:20])
        triggers = sum(
            1 for s in statements if s.lstrip().upper().startswith("CREATE TRIGGER")
        )
        print(
            f"{mode}: messages partition activated in {args.db} "
            f"({tables} tables, {indexes} indexes, {triggers} triggers)"
        )


if __name__ == "__main__":
    main()
