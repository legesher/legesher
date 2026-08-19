#!/usr/bin/env python
"""Move human-touched canon selections off the ``machine`` rung.

``status = 'machine'`` is defined as "auto-picked, unreviewed". Two populations
in ``canon_selections`` carry it and should not:

**Renderings a person endorsed.** Hundreds of canon-selected options carry live
endorsements — most of them the recovered review history from the community
that built ``legesher-translations``, where contributors voted on renderings
long before this database existed. Those endorsements attach to the specific
option that was later selected as canon, so they are evidence about *this
word*, not merely about the concept. Labelling them ``machine`` erases the
contribution outright: it tells a reader nobody looked, when in fact a
community did.

**Renderings a native reviewer decided.** A speaker of the language corrected
the word directly.

Both move to ``experimental``, not to ``reviewed``. One informed opinion is
real without being a consensus, and these endorsements sit at contributor rung
rather than verified native sign-off. Whether many contributor endorsements can
ever compound into ``reviewed`` is the open ladder question, and it is not this
script's to answer.

The two axes stay separate: the rung says how much review a rendering has, and
the published ``decided_by`` role says who made the last call.

## Why this is a delete-and-reinsert rather than an UPDATE

``trg_canon_no_update`` forbids every UPDATE to ``canon_selections``,
unconditionally, because the canon is meant to be a loaded projection of
``libs/i18n/canon/<locale>.toml`` — replaced wholesale on each load, never
edited in place. The trigger's own message says to edit the text file and
reload.

**Those files have never existed in git history**, so the sanctioned path is
not available and the direct path is refused. The schema anticipates the shape
of the fix even so: *"DELETE stays open: it is half of 'replace wholesale'."*
So this replaces the affected rows wholesale — delete, then re-insert — which
also re-runs every INSERT trigger against them. Re-validation is a feature
here, not a cost: if any of these options has since been withdrawn or
quarantined, the re-insert fails loudly instead of quietly restoring a row
that no longer holds.

``decided_at`` is preserved. The timestamp records when the reviewer made the
call, not when we corrected our bookkeeping about it.

## Re-appliability

Screening verdicts already have this property — they live only in
``option_screenings`` and a from-scratch rebuild loses them. This correction is
the same class: it is not in the migration, so a rebuilt database needs it
re-applied. That is why it is a script rather than a one-off statement, and
why it is idempotent.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

#: Reviewer handles are matched by SHAPE, not enumerated. The raw values are
#: people's names and this file is public, so listing them here would put
#: contributor identities in source -- the same reasoning as
#: ``export_canon.HANDLE_PATTERN``, which this deliberately mirrors.
#:
#: ``EXCLUDED_DECIDERS`` is what keeps the shape honest: ``quality_review``
#: fits the pattern but is a maintainer quality pass rather than a person, and
#: promoting its rows would overstate how much native review exists.
HANDLE_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*_review$", re.IGNORECASE)

#: Handle-shaped values that are process labels, not people.
EXCLUDED_DECIDERS: frozenset[str] = frozenset({"quality_review"})

#: Where those rows belong. NOT ``reviewed`` — see the module docstring.
TARGET_STATUS = "experimental"

#: The rung they are wrongly recorded at.
SOURCE_STATUS = "machine"

#: Every column of ``canon_selections`` that carries data, in insert order.
#: ``id`` is excluded deliberately: it is an AUTOINCREMENT surrogate that never
#: leaves the database, so a new one is harmless. ``pl_scope`` is excluded
#: because it is a STORED generated column and cannot be written.
CARRIED_COLUMNS: tuple[str, ...] = (
    "concept_id",
    "locale",
    "programming_language",
    "option_uid",
    "surface_form",
    "status",
    "identity_ok",
    "decided_by",
    "decided_at",
    "decision_reason",
    "source_file",
    "source_revision",
)


def correct(conn: sqlite3.Connection, *, dry_run: bool = False) -> dict[str, int]:
    """Replace the native-review rows at the correct rung.

    Returns:
        Counts keyed ``found`` / ``moved`` / ``already_correct``.
    """
    # `pl_scope` is selected but never re-inserted: it is a STORED generated
    # column, so it cannot be written, but it is half of the UNIQUE key the
    # delete below has to match.
    #
    # `endorsed` is the load-bearing half of the predicate. A rendering that a
    # real person put their name behind is not "auto-picked, unreviewed" no
    # matter how it was first drafted -- and the endorsement attaches to THIS
    # option, not merely to the concept, so it is evidence about this word.
    rows = [
        row
        for row in conn.execute(
            f"SELECT {', '.join(CARRIED_COLUMNS)}, pl_scope, "
            "EXISTS (SELECT 1 FROM endorsements e "
            "        WHERE e.option_uid = canon_selections.option_uid "
            "          AND e.retracted_at IS NULL) AS endorsed "
            "FROM canon_selections ORDER BY locale, concept_id"
        )
        if row["endorsed"]
        or (
            row["decided_by"]
            and HANDLE_PATTERN.match(row["decided_by"])
            and row["decided_by"] not in EXCLUDED_DECIDERS
        )
    ]

    already = sum(1 for row in rows if row["status"] == TARGET_STATUS)
    stale = [row for row in rows if row["status"] == SOURCE_STATUS]
    other = [row for row in rows if row["status"] not in (TARGET_STATUS, SOURCE_STATUS)]
    if other:
        raise SystemExit(
            f"REFUSED: {len(other)} native-review row(s) sit at a rung this "
            f"script does not expect ({sorted({r['status'] for r in other})}). "
            "Someone else has moved them; decide deliberately rather than "
            "letting this script overwrite that."
        )

    if dry_run:
        # Report what WOULD move. A dry run that always says zero is worse
        # than no dry run: it reads as "nothing to do" and is trusted as one.
        return {"found": len(rows), "moved": len(stale), "already_correct": already}
    if not stale:
        return {"found": len(rows), "moved": 0, "already_correct": already}

    columns = ", ".join(CARRIED_COLUMNS)
    marks = ", ".join("?" for _ in CARRIED_COLUMNS)
    status_at = CARRIED_COLUMNS.index("status")

    with conn:  # one transaction: either every row moves or none does
        for row in stale:
            # Keyed on the table's actual UNIQUE constraint
            # (concept_id, locale, pl_scope). Keying on option_uid instead
            # would be wrong: one option can be canon under more than one
            # target — `if` in Arabic is canon for both python and javascript
            # with the identical uid — so an option_uid predicate would delete
            # both rows and the loop would restore only one.
            deleted = conn.execute(
                "DELETE FROM canon_selections WHERE concept_id = ? "
                "AND locale = ? AND pl_scope = ?",
                (row["concept_id"], row["locale"], row["pl_scope"]),
            ).rowcount
            if deleted != 1:
                raise SystemExit(
                    f"REFUSED: deleting the canon row for concept "
                    f"{row['concept_id']} / {row['locale']} / {row['pl_scope']} "
                    f"removed {deleted} rows, expected exactly 1. Nothing is "
                    "committed; investigate before retrying."
                )
            # By name, not by row order: the SELECT carries pl_scope as an
            # extra trailing column, so positional unpacking would misalign.
            values = [row[column] for column in CARRIED_COLUMNS]
            values[status_at] = TARGET_STATUS
            # The INSERT triggers re-check every canon invariant here. A
            # failure means something about this option changed since it was
            # selected, and it should stop the run.
            conn.execute(
                f"INSERT INTO canon_selections ({columns}) VALUES ({marks})",
                values,
            )

    return {"found": len(rows), "moved": len(stale), "already_correct": already}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would move without writing",
    )
    args = parser.parse_args(argv)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        result = correct(conn, dry_run=args.dry_run)
    finally:
        conn.close()

    verb = "would move" if args.dry_run else "moved"
    print(
        f"native-review rows found: {result['found']}; {verb}: {result['moved']}; "
        f"already at {TARGET_STATUS}: {result['already_correct']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
