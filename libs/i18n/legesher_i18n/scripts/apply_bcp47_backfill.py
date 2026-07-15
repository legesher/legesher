#!/usr/bin/env python3
"""Apply the reviewed BCP 47 backfill to ``languages.bcp47`` (CORE-1512).

This is promote slice 1 of the CORE-1500 → CORE-1512 plan: write the audited,
Madison-decided tags from ``db/migrations/bcp47_backfill.tsv`` into the one
column they belong to. It is deliberately the *narrowest possible* write:

* Only ``languages.bcp47`` is ever touched. No row is inserted or deleted; no
  other column and no other table is written. (Pack regeneration remains
  unsafe until CORE-1400 — this script has nothing to do with packs.)
* The committed TSV is the single input. Its values were validated against the
  vendored IANA registry when it was generated, and are re-validated here with
  :func:`legesher_i18n.bcp47.is_canonical` before anything is written — a
  hand-edited TSV that drifted from the registry fails before the first write.
* Dry-run by default. ``--apply`` performs the writes, in one transaction.
* Idempotent: rows whose ``bcp47`` already equals the proposed tag are
  reported and skipped, so re-running is a no-op.

Verification protocol (recorded in the CORE-1512 PR):

    sqlite3 translations.db .dump > before.sql
    uv run python libs/i18n/legesher_i18n/scripts/apply_bcp47_backfill.py --apply
    sqlite3 translations.db .dump > after.sql
    diff before.sql after.sql   # must show ONLY languages-table INSERT lines,
                                # differing ONLY in the bcp47 value

Usage:
    uv run python libs/i18n/legesher_i18n/scripts/apply_bcp47_backfill.py
    uv run python libs/i18n/legesher_i18n/scripts/apply_bcp47_backfill.py --apply
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
I18N_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(I18N_DIR.parent))

from legesher_i18n import bcp47  # noqa: E402

BACKFILL_TSV = I18N_DIR / "db" / "migrations" / "bcp47_backfill.tsv"
DB_PATH = I18N_DIR / "db" / "translations.db"


def load_proposals(tsv_path: Path = BACKFILL_TSV) -> dict[str, str]:
    """Read ``code -> proposed_tag`` from the committed proposal TSV.

    Raises:
        SystemExit: if the TSV is missing, a row still carries
            ``needs_review=yes`` (an undecided proposal must not be applied),
            or a proposed tag fails canonical validation against the vendored
            registry.
    """
    if not tsv_path.exists():
        raise SystemExit(
            f"{tsv_path} not found — regenerate with propose_bcp47_backfill.py"
        )
    proposals: dict[str, str] = {}
    with tsv_path.open(encoding="utf-8") as fh:
        rows = csv.DictReader(
            (line for line in fh if not line.startswith("#")), delimiter="\t"
        )
        for row in rows:
            code, tag = row["code"], row["proposed_tag"]
            if row["needs_review"] == "yes":
                raise SystemExit(
                    f"refusing to apply {code!r}: still flagged needs_review=yes. "
                    "Undecided proposals are not applied."
                )
            if not bcp47.is_canonical(tag):
                raise SystemExit(
                    f"refusing to apply {code!r} -> {tag!r}: not canonical against "
                    f"the vendored registry (snapshot {bcp47.registry_file_date()})"
                )
            proposals[code] = tag
    return proposals


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="perform the UPDATEs (default is a dry-run report)",
    )
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    args = parser.parse_args()

    proposals = load_proposals()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        db_rows = {
            row["code"]: row["bcp47"]
            for row in conn.execute("SELECT code, bcp47 FROM languages")
        }

        missing_in_db = sorted(set(proposals) - set(db_rows))
        missing_in_tsv = sorted(set(db_rows) - set(proposals))
        if missing_in_db or missing_in_tsv:
            raise SystemExit(
                "language set mismatch between TSV and DB — regenerate the "
                f"proposal first (TSV-only: {missing_in_db}, DB-only: {missing_in_tsv})"
            )

        changes = [
            (code, db_rows[code], tag)
            for code, tag in sorted(proposals.items())
            if db_rows[code] != tag
        ]
        unchanged = len(proposals) - len(changes)

        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"[{mode}] {len(changes)} to change, {unchanged} already correct:")
        for code, current, tag in changes:
            print(f"  {code:<4} {current or 'NULL':<8} -> {tag}")

        if args.apply and changes:
            with conn:  # one transaction; rolls back wholesale on any error
                for code, _, tag in changes:
                    conn.execute(
                        "UPDATE languages SET bcp47 = ? WHERE code = ?", (tag, code)
                    )
            # Post-write audit: the column now matches the TSV exactly.
            for row in conn.execute("SELECT code, bcp47 FROM languages"):
                if row["bcp47"] != proposals[row["code"]]:
                    raise SystemExit(
                        f"POST-WRITE MISMATCH on {row['code']!r} — investigate before "
                        "committing anything"
                    )
            print(f"Applied. All {len(proposals)} rows now match the TSV.")
        elif args.apply:
            print("Nothing to do — already applied.")
        else:
            print("Dry-run only. Re-run with --apply to write.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
