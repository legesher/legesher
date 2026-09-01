#!/usr/bin/env python
"""Restore the 14 candidate rows behind dangling v1 selections (CORE-2079).

``selected_translations`` holds 14 rows whose selected value exists in no
``translations`` candidate row, so ``migrate_to_v2.py`` refuses the build
("selected value not present as an option"). Two repair classes, both cases
of a selection being fixed without its candidate:

* **Nine ``except*`` mirrors** — the CORE-1883 restore re-pointed the
  selections at the star-bearing mirror values after the CORE-1866 rebuild
  reverted them, but never restored the starred candidate rows themselves
  (sibling locales such as am/ar/bn/el kept theirs).
* **Five CORE-1905 replacements** — the 2026-08-18 data audit replaced
  audit-flagged selections (prompt residue, untranslated English) with real
  renderings without inserting matching candidate rows.

The repair is append-only: for each (term, locale, value) triple it verifies
the selection still selects exactly that value and that no candidate carries
it, then INSERTs the missing candidate row. Selections are never touched, so
pack output cannot change (``verify_pack_regen.py`` proves it after a run).

Column conventions of the inserted rows:

* ``source`` is the dedicated ``selection-repair`` value, mapped to the
  published ``legesher`` provenance bucket in ``migrate_to_v2.SOURCE_MAP`` —
  the public four-value vocabulary stays closed while the v1 provenance says
  what actually happened, rather than borrowing ``yaml-import`` for rows no
  YAML import produced. Precedent: ``core-1318-fix`` / ``core-1763-fix``.
* ``word_type`` / ``word_form`` are mirrored from the latest sibling
  candidate for the same (term, locale) — properties of the rendering, not
  of who asserted it.
* ``confidence`` / ``model_version`` / ``model_rationale`` are deliberately
  NULL: they are a source's own assertion about its value, and this repair
  asserts none — it restores a value the selection layer already chose
  (the ``core-1318-fix`` rows carry the same NULLs).

Fail-closed and idempotent: the whole run is planned before anything is
written. A triple whose candidate already exists is a reported no-op; a
triple whose selection is missing or selects a DIFFERENT value refuses the
entire run (the dangle this script was written for is not the state on
disk — investigate, do not insert). Every triple prints a disposition;
nothing is skipped silently.

Usage:
    cd libs/i18n
    uv run python scripts/repair_dangling_selections.py \\
        [--db legesher_i18n/db/translations.db]

Exit status 0 on a completed repair or a fully idempotent no-op; 1 on any
refusal (nothing written).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legesher_i18n.db.schema_v2 import normalize_surface_form  # noqa: E402

#: v1 ``translations.source`` for the restored rows. Must have a
#: ``migrate_to_v2.SOURCE_MAP`` entry (-> ``legesher``); the migration
#: hard-fails on an unmapped source, which pins the pairing in tests.
REPAIR_SOURCE = "selection-repair"

#: ``created_by`` label, following the fix-row register already in the data
#: (``core-1318-native-fix``, ``CORE-1839``). Not a person: it must never
#: resolve to a contributor, which holds because ``selection-repair``
#: classifies as ``legesher``, and only community-kind rows mint identities.
REPAIR_CREATED_BY = "selection-repair (CORE-2079)"


@dataclass(frozen=True)
class Repair:
    """One dangling selection: the candidate row to restore."""

    term: str
    programming_language: str
    locale: str
    value: str
    origin: str  # which repair class, for the disposition line


#: The 14 dangling selections (root-caused on CORE-2079, 2026-09-01). The
#: script re-verifies every one against the live database before writing —
#: this list records which dangles the repair is FOR, not a license to
#: insert regardless of state.
CORE_1883 = "CORE-1883 star-mirror restore"
CORE_1905 = "CORE-1905 audit replacement"
REPAIRS: tuple[Repair, ...] = (
    Repair("except*", "python", "da", "undtiden*", CORE_1883),
    Repair("except*", "python", "de", "abgesehenvon*", CORE_1883),
    Repair("except*", "python", "fi", "exceptiivi*", CORE_1883),
    Repair("except*", "python", "hi", "अपराधिक*", CORE_1883),
    Repair("except*", "python", "mk", "освен_ѕвезда*", CORE_1883),
    Repair("except*", "python", "pt", "exceptar*", CORE_1883),
    Repair("except*", "python", "ru", "кроме*", CORE_1883),
    Repair("except*", "python", "te", "మినహాయింపుగుంపు*", CORE_1883),
    Repair("except*", "python", "th", "เครื่องมือที่ใช้ในการเอาเป็น*", CORE_1883),
    Repair("pow", "python", "th", "ยกกำลัง", CORE_1905),
    Repair("global", "python", "th", "ส่วนกลาง", CORE_1905),
    Repair("classmethod", "python", "hu", "osztálymetódus", CORE_1905),
    Repair("globals", "python", "tr", "küreseldeğişkenler", CORE_1905),
    Repair("locals", "python", "ms", "pembolehubahsetempat", CORE_1905),
)


@dataclass(frozen=True)
class Disposition:
    """What the run decided for one triple."""

    repair: Repair
    action: str  # 'insert' | 'noop' | 'refuse'
    detail: str

    def line(self) -> str:
        label = {"insert": "REPAIRED", "noop": "SKIPPED", "refuse": "REFUSED"}[
            self.action
        ]
        r = self.repair
        return (
            f"{label}: {r.term}/{r.locale} -> {r.value!r} [{r.origin}] — {self.detail}"
        )


def plan_repairs(
    conn: sqlite3.Connection, repairs: tuple[Repair, ...] = REPAIRS
) -> list[Disposition]:
    """Verify every triple against the database and decide its disposition.

    Read-only. Refusals are dispositions too — the caller decides whether any
    ``refuse`` aborts the run (``main`` does; nothing is written past one).
    """
    dispositions: list[Disposition] = []
    for repair in repairs:
        term_row = conn.execute(
            "SELECT id FROM terms WHERE name = ? AND programming_language = ?",
            (repair.term, repair.programming_language),
        ).fetchall()
        if len(term_row) != 1:
            dispositions.append(
                Disposition(
                    repair,
                    "refuse",
                    f"expected exactly one {repair.programming_language} term "
                    f"named {repair.term!r}, found {len(term_row)}",
                )
            )
            continue
        term_id = term_row[0][0]

        selected = conn.execute(
            "SELECT translation FROM selected_translations "
            "WHERE term_id = ? AND language_code = ?",
            (term_id, repair.locale),
        ).fetchone()
        if selected is None:
            dispositions.append(
                Disposition(
                    repair,
                    "refuse",
                    "no selection row exists — the dangle this repair was "
                    "written for is not the state on disk; investigate",
                )
            )
            continue
        if selected[0] != repair.value:
            dispositions.append(
                Disposition(
                    repair,
                    "refuse",
                    f"the selection now selects {selected[0]!r}, not the "
                    "value this repair restores — re-root-cause before "
                    "inserting anything",
                )
            )
            continue

        # The same comparison the migration applies: a candidate whose
        # NFC-normalized surface matches the selection's already satisfies
        # the v2 build, so it makes the triple a no-op here too.
        want = normalize_surface_form(repair.value)
        candidates = conn.execute(
            "SELECT translation FROM translations "
            "WHERE term_id = ? AND language_code = ?",
            (term_id, repair.locale),
        ).fetchall()
        if any(normalize_surface_form(row[0]) == want for row in candidates):
            dispositions.append(
                Disposition(
                    repair,
                    "noop",
                    "a candidate row already carries this value — nothing "
                    "to restore (idempotent)",
                )
            )
            continue

        dispositions.append(
            Disposition(repair, "insert", f"candidate row missing (term_id {term_id})")
        )
    return dispositions


def apply_repairs(conn: sqlite3.Connection, dispositions: list[Disposition]) -> int:
    """Insert the planned candidate rows, in one transaction.

    Only ``insert`` dispositions write; the caller must have refused the run
    already if any disposition is a refusal.
    """
    inserted = 0
    with conn:
        for disposition in dispositions:
            if disposition.action != "insert":
                continue
            repair = disposition.repair
            term_id = conn.execute(
                "SELECT id FROM terms WHERE name = ? AND programming_language = ?",
                (repair.term, repair.programming_language),
            ).fetchone()[0]
            sibling = conn.execute(
                "SELECT word_type, word_form FROM translations "
                "WHERE term_id = ? AND language_code = ? "
                "ORDER BY id DESC LIMIT 1",
                (term_id, repair.locale),
            ).fetchone()
            word_type, word_form = sibling if sibling else (None, None)
            conn.execute(
                "INSERT INTO translations "
                "(term_id, language_code, translation, source, created_by, "
                " word_type, word_form, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
                (
                    term_id,
                    repair.locale,
                    repair.value,
                    REPAIR_SOURCE,
                    REPAIR_CREATED_BY,
                    word_type,
                    word_form,
                ),
            )
            inserted += 1
    return inserted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("legesher_i18n/db/translations.db"),
        help="the v1 database to repair (default: the packaged path, run "
        "from libs/i18n)",
    )
    args = parser.parse_args(argv)

    if not args.db.is_file():
        raise SystemExit(f"REFUSED: v1 database {args.db} does not exist")

    conn = sqlite3.connect(args.db)
    try:
        dispositions = plan_repairs(conn)
        refusals = [d for d in dispositions if d.action == "refuse"]
        if refusals:
            # Print EVERY disposition first — a refusal must not hide the
            # state of the other triples — then abort with nothing written.
            for disposition in dispositions:
                print(disposition.line())
            print(
                f"REFUSED: {len(refusals)} triple(s) do not match the "
                "root-caused state; nothing was written."
            )
            return 1
        inserted = apply_repairs(conn, dispositions)
        for disposition in dispositions:
            print(disposition.line())
        noops = sum(1 for d in dispositions if d.action == "noop")
        print(
            f"repair complete: {inserted} candidate row(s) inserted, "
            f"{noops} already present. Selections untouched — run "
            "scripts/verify_pack_regen.py to prove the packs did not move."
        )
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
