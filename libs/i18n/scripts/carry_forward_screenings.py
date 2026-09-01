#!/usr/bin/env python
"""Carry the intake layer forward into a freshly rebuilt v2 database (CORE-2052).

``migrate_to_v2.py`` rebuilds v2 from the v1 source, and the intake layer is
not reconstructible from v1: the community wrote it straight into v2. That is
more than the screening verdicts this script was first scoped to (CORE-1828's
``option_screenings``) — the intake importer INSERTs the community options
themselves directly into ``options``, with their provenance, validations,
endorsements, contributors, review sessions and commentary. Verified against
the durable copy: 672 of the 691 screened options do not exist in v1 at all,
so a rebuild followed by a verdicts-only carry-forward has nothing to attach
the verdicts to. The replay path the intake-moderation runbook once described
(re-import the archived payloads) has no archive behind it — the durable data
home has never held one — so this script carries the layer itself, wholesale.

## What travels, table by table

**Carried wholesale** — tables the migration never writes, so every row in
them is intake-layer and a fresh build holds none (verified against the
migration's insert sites): ``review_sessions``, ``session_options``,
``session_endorsements``, ``session_rankings``, ``option_annotations``,
``option_expansions``, ``option_flags``, ``concept_commentary``,
``commentary_moderation``, ``style_ratifications``.

**Carried by difference** — tables both the migration and the intake path
write; only rows the rebuild did not reproduce travel:

* ``options`` — screened uids absent from the target, gated: every one must
  carry exclusively ``community`` provenance in the source. A missing option
  with any other provenance came from v1 and its absence means the rebuild
  DROPPED it — that refuses the run rather than being papered over.
* ``option_provenance`` — rows for carried options, plus ``community`` rows
  on options that do exist (a community re-attestation of a v1 word lives
  only in v2). Content-diffed; the surrogate id is dropped on insert.
* ``option_validations`` — rows for carried options only. Validations of
  options the rebuild reproduced are consciously NOT carried: the rebuild
  re-validates every option with the current validator, and that fresher
  verdict wins. Every carried row (here and everywhere) is inserted by the
  SOURCE's column list, so a column the target's schema added later takes
  the target's declared default — for a validation verdict that is NULL,
  "never scanned", which the canon gate refuses exactly like a failure;
  nothing is ever invented as a pass. Upgrading the scratch source copy
  first (above) avoids even that, by computing the real verdicts.
* ``endorsements`` — source uids absent from the target. The endorsement uid
  formula is frozen (golden vectors), so a v1-derived endorsement rebuilds to
  the identical uid and is never duplicated; what remains missing is
  intake-written.
* ``contributors`` / ``contributor_identities`` — ids absent from the target
  (contributor ids are salted digests, stable across rebuilds under the same
  salt — which is why the salt-fingerprint gate below exists).
* ``option_screenings`` — last, rows keyed and ORDERED by their original ids,
  because the verdict semantics are latest-row-wins; renumbering could flip a
  live verdict while every count still reconciles.

**Consciously excluded** — ``canon_selections`` (the maintainer decision
layer: re-derived by the migration and ``correct_canon_review_rung.py``, per
the corpus publish runbook); the reference layer (concepts, terms, locales,
programming languages, rungs — maintainer-curated and rebuilt from v1; a gap
there REFUSES rather than being filled in); ``import_sources`` (nothing
writes it yet — it gets a carry policy when something does); and the messages
partition, which is re-seeded from catalogs with fresh integer keys — a
source with ``message_endorsements`` rows refuses outright, because those
rows point at integer ids that do not survive a re-seed.

Unscreened options present in the source but absent from the target are v1
drift (the durable copy is a snapshot; v1 moves on) — out of scope here, and
surfaced by the runbook's count verification instead. But if a carried row
references such an option, the FK pre-flight below refuses and names it.

Integer concept ids are internal and renumber across rebuilds, so every
carried ``concept_id`` is remapped through the concept SLUG; a slug the
target does not know refuses the run.

## Refusals (all fail-closed, all before any write)

* no ``option_screenings`` table on either side (a v1 file, or a pre-1828 v2)
* screening-schema version mismatch — there is no stored schema version
  number, so the version IS the DDL: a fingerprint over the normalized
  ``sqlite_master`` entries of the screening object set, taken to a
  fixpoint (an object joins when its DDL names any object already in the
  set, transitively). The fingerprint sees renames and body rewrites
  anywhere in that reference chain; semantic drift that leaves every DDL
  string untouched is beyond any fingerprint's reach. The fingerprint is
  deliberately NOT scoped down to ride out known upgrades (CORE-2029 moved
  ``option_standings`` and ``option_promotion_status`` under it): a durable
  copy that predates an upgrade is brought current by copying it to a
  SCRATCH file and running ``schema_v2.ensure_intake_screening`` on the
  copy — never on the durable original — which also computes real verdicts
  for any column the upgrade backfills, so carried rows arrive whole
  rather than defaulted. The runbook's carry step does exactly this.
* contributor-salt fingerprint mismatch (``build_meta``) — under different
  salts every contributor id differs and the diff would duplicate all of
  them; rebuild with the escrowed salt instead
* a source table referencing options / contributors / sessions /
  endorsements that this script has no carry policy for (schema grew —
  extend the script, deliberately)
* a source column the target lacks (the target must be at or ahead of the
  source's schema for every carried table)
* a missing option that is not exclusively community-sourced (see above)
* a carried row referencing an option, contributor, session, endorsement,
  concept slug, locale, programming language, or rung that exists on
  neither side of the carry
* a keyed row whose content DIFFERS between source and target at the same
  key — the two databases have diverged; decide deliberately
* target screening history that conflicts with the source's (same id,
  different row) or interleaves it (an id below the source's high-water
  mark that the source does not have)
* a non-cleared verdict to be inserted for an option the target has
  canon-selected — that would trip
  ``trg_screenings_no_quarantine_while_canon`` mid-transaction; pull the
  option from the canon and reload first, per the trigger's own doctrine

Idempotent: a target that already holds everything is a reported no-op, and
verdicts appended in the source since the last carry travel as a delta.
Later local verdicts in the target (above the source's high-water mark) do
not disturb a no-op.

The source is opened read-only at the SQLite level, and nothing in this
script can write to it. It is expected to be an upgraded SCRATCH COPY of the
durable database (see the fingerprint bullet above) — the durable original
in the private data home is never the ``--source`` and is never written.

Usage:
    cd libs/i18n
    cp "$LEGESHER_DATA_REPO/db/translations_v2.db" build/carry-source.db
    uv run python -c "
    from legesher_i18n.db.schema_v2 import connect, ensure_intake_screening
    ensure_intake_screening(connect('build/carry-source.db'))"
    uv run python scripts/carry_forward_screenings.py \\
        --source build/carry-source.db \\
        --target build/translations_v2.db [--dry-run]

Exit status is 0 on a completed copy, a clean dry run, or an idempotent
no-op; every refusal exits 1 with a ``REFUSED:`` message.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legesher_i18n.db.schema_v2 import SCREENING_ROOTS, connect  # noqa: E402

#: Every column of ``option_screenings``, in insert order — INCLUDING ``id``.
#: The AUTOINCREMENT surrogate is deliberately carried: latest-id-wins is the
#: verdict semantics, so the ids are load-bearing history, not bookkeeping.
SCREENING_COLUMNS: tuple[str, ...] = (
    "id",
    "option_uid",
    "verdict",
    "screened_by",
    "screen_version",
    "note",
    "screened_at",
)

#: The verdict vocabulary, in the CHECK-constraint order, so count reports
#: always print every column even when a verdict has zero rows.
VERDICTS: tuple[str, ...] = ("cleared", "quarantined", "held", "rejected")

#: Tables only the intake pipeline writes — the migration's insert sites were
#: audited table by table. A fresh rebuild holds zero rows in any of them, so
#: the whole table is intake layer and travels. Listed in FK insert order.
INTAKE_ONLY_TABLES: tuple[str, ...] = (
    "review_sessions",
    "session_options",
    "session_endorsements",
    "session_rankings",
    "option_annotations",
    "option_expansions",
    "option_flags",
    "concept_commentary",
    "commentary_moderation",
    "style_ratifications",
)

#: Tables whose rows CANNOT be carried (integer FKs into a partition the
#: rebuild re-seeds with fresh keys). Rows here refuse the run.
REFUSE_IF_POPULATED: tuple[str, ...] = ("message_endorsements",)

#: Option-referencing tables with a deliberate no-carry policy (the decision
#: layer — see the module docstring). The completeness guard treats these as
#: handled; anything else referencing options refuses.
EXCLUDED_OPTION_CONSUMERS: frozenset[str] = frozenset({"canon_selections"})

#: Tables whose carried rows hold an internal integer concept id that must be
#: remapped through the concept slug (ids renumber across rebuilds).
CONCEPT_REMAPPED: frozenset[str] = frozenset(
    {"options", "session_rankings", "concept_commentary"}
)

#: Tables whose single-column INTEGER ``id`` is an internal surrogate: it is
#: dropped on insert and rows are diffed by content. ``option_screenings`` is
#: NOT here — its id is semantics (see SCREENING_COLUMNS).
SURROGATE_ID_TABLES: frozenset[str] = frozenset({"option_provenance", "option_flags"})

#: Columns EXCLUDED from the source-vs-target divergence comparison, per
#: table: the migration re-stamps these with ``datetime('now')`` on every
#: rebuild (verified against its insert statements), so a difference there is
#: build noise, not divergence. Nothing else qualifies — a retraction, a
#: consent change or a rung move IS divergence, and refuses. Endorsement
#: ``created_at`` is NOT here on purpose: it is an input to the frozen uid
#: formula and the migration carries it verbatim from v1.
COMPARE_IGNORED: dict[str, frozenset[str]] = {
    "contributors": frozenset({"joined_at"}),
}

#: Insert order for the whole carry: parents before children, verdicts last.
CARRY_ORDER: tuple[str, ...] = (
    "contributors",
    "contributor_identities",
    "options",
    "option_provenance",
    "option_validations",
    "endorsements",
    *INTAKE_ONLY_TABLES,
    "option_screenings",
)


def _normalize_ddl(sql: str) -> str:
    """Strip comments and collapse whitespace so doc churn is not drift."""
    return re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", sql)).strip()


def screening_schema_fingerprint(
    conn: sqlite3.Connection,
) -> tuple[str, dict[tuple[str, str], str]]:
    """Fingerprint a database's screening-schema version.

    Starts from :data:`legesher_i18n.db.schema_v2.SCREENING_ROOTS` and takes
    the object set to a FIXPOINT: an object joins when it sits on a root
    table, or its DDL mentions the name of any object already in the set.
    Transitivity is the point — ``option_promotion_status`` reads the verdict
    only through ``option_standings``, and a one-hop set would let a rewrite
    of it slide through unfingerprinted.

    The fingerprint covers exactly this reference chain: any rename or DDL
    rewrite inside it changes the version. It does NOT see drift that leaves
    every DDL string untouched, and does not claim to.

    Returns:
        ``(fingerprint, objects)`` — a 12-hex digest over the sorted,
        normalized DDL, and the ``(type, name) -> normalized sql`` map behind
        it (for naming exactly which objects differ in a refusal).
    """
    rows = conn.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE sql IS NOT NULL ORDER BY type, name"
    ).fetchall()
    members = set(SCREENING_ROOTS)
    chosen: dict[tuple[str, str], str] = {}
    changed = True
    while changed:
        changed = False
        for kind, name, tbl_name, sql in rows:
            if (kind, name) in chosen:
                continue
            if (
                tbl_name in members
                or name in members
                or any(member in sql for member in members)
            ):
                chosen[(kind, name)] = _normalize_ddl(sql)
                members.add(name)
                changed = True
    blob = "\x1f".join(
        f"{kind}|{name}|{chosen[(kind, name)]}" for kind, name in sorted(chosen)
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12], chosen


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    """The table's real (non-generated) columns, in declared order."""
    return [
        row[1]
        for row in conn.execute(f"PRAGMA table_xinfo({table})")
        if row[6] == 0  # hidden: 2/3 are generated columns, never insertable
    ]


def _pk_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    keyed = sorted((row[5], row[1]) for row in info if row[5])
    return [name for _, name in keyed]


def _fetch(
    conn: sqlite3.Connection, table: str, columns: list[str]
) -> list[dict[str, object]]:
    cursor = conn.execute(
        f"SELECT {', '.join(columns)} FROM {table}"  # nosec B608 - schema-derived names
    )
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _verdict_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts = dict.fromkeys(VERDICTS, 0)
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    return counts


def _screening_rows(conn: sqlite3.Connection) -> list[dict[str, object]]:
    cursor = conn.execute(
        f"SELECT {', '.join(SCREENING_COLUMNS)} "  # nosec B608 - static column list only
        "FROM option_screenings ORDER BY id"
    )
    return [dict(zip(SCREENING_COLUMNS, row)) for row in cursor.fetchall()]


def _report(label: str, rows: list[dict[str, object]]) -> str:
    counts = _verdict_counts(rows)
    cells = "  ".join(f"{verdict} {counts[verdict]}" for verdict in VERDICTS)
    return f"{label:<16} {cells}  total {len(rows)}"


def _require_screenings_table(conn: sqlite3.Connection, label: str, path: Path) -> None:
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'option_screenings'"
    ).fetchone():
        raise SystemExit(
            f"REFUSED: {label} database {path} has no option_screenings table — "
            "it is not a v2 database, or it predates the CORE-1828 screening "
            "schema (schema_v2.ensure_intake_screening installs it)."
        )


def _refuse(reason: str) -> None:
    raise SystemExit(f"REFUSED: {reason}")


def _single_value(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> object:
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def _check_salt_fingerprints(
    source: sqlite3.Connection, target: sqlite3.Connection
) -> None:
    fingerprints = {}
    for label, conn in (("source", source), ("target", target)):
        fingerprints[label] = _single_value(
            conn, "SELECT value FROM build_meta WHERE key = 'salt_fingerprint'"
        )
        if not fingerprints[label]:
            _refuse(
                f"the {label} database records no contributor-salt fingerprint "
                "in build_meta — it was not produced by migrate_to_v2.py, and "
                "contributor ids cannot be trusted to line up."
            )
    if fingerprints["source"] != fingerprints["target"]:
        _refuse(
            "contributor-salt fingerprint mismatch — source build_meta says "
            f"{fingerprints['source']}, target says {fingerprints['target']}. "
            "Under different salts every contributor id differs, and the "
            "carry would duplicate all of them. Rebuild the target with the "
            "escrowed salt (the corpus publish runbook's build step)."
        )


def _check_schema_fingerprints(
    source: sqlite3.Connection, target: sqlite3.Connection
) -> None:
    src_fingerprint, src_objects = screening_schema_fingerprint(source)
    tgt_fingerprint, tgt_objects = screening_schema_fingerprint(target)
    if src_fingerprint == tgt_fingerprint:
        return
    differing = sorted(
        name
        for kind, name in (set(src_objects) | set(tgt_objects))
        if src_objects.get((kind, name)) != tgt_objects.get((kind, name))
    )
    _refuse(
        "screening-schema version mismatch — source is "
        f"{src_fingerprint}, target is {tgt_fingerprint} "
        f"(differing object(s): {', '.join(differing)}). Two databases "
        "that disagree about the screening schema must not exchange "
        "rows. If the source is a durable copy that predates a schema "
        "upgrade, bring a SCRATCH COPY of it current — never the durable "
        "original — and use the copy as --source: "
        "cp <durable> <scratch>; then run "
        "schema_v2.ensure_intake_screening on the scratch copy "
        "(corpus-publish-runbook.md section 1 shows the exact commands)."
    )


def _check_completeness(source: sqlite3.Connection) -> None:
    """Refuse a source whose schema grew past this script's carry policies."""
    handled = set(CARRY_ORDER) | EXCLUDED_OPTION_CONSUMERS | set(REFUSE_IF_POPULATED)
    anchors = {"options", "contributors", "review_sessions", "endorsements"}
    unknown = []
    for (table,) in source.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall():
        if table in handled or table.startswith("sqlite_"):
            continue
        if any(
            fk[2] in anchors
            for fk in source.execute(f"PRAGMA foreign_key_list({table})")
        ):
            unknown.append(table)
    if unknown:
        _refuse(
            f"source table(s) {', '.join(sorted(unknown))} reference the intake "
            "layer and this script has no carry policy for them — the schema "
            "has grown since CORE-2052. Extend the carry deliberately rather "
            "than letting those rows fall out of the rebuild."
        )


def _check_populated_refusals(source: sqlite3.Connection) -> None:
    for table in REFUSE_IF_POPULATED:
        if not _single_value(
            source,
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ):
            continue
        count_sql = f"SELECT COUNT(*) FROM {table}"  # nosec B608 - static table tuple
        count = _single_value(source, count_sql)
        if count:
            _refuse(
                f"the source holds {count} {table} row(s). The messages "
                "partition is re-seeded from catalogs with fresh integer "
                "keys, so these rows cannot be carried portably — resolve "
                "them deliberately (CORE-1679 / CORE-2052) before rebuilding."
            )


def _check_column_compat(
    source: sqlite3.Connection, target: sqlite3.Connection
) -> dict[str, list[str]]:
    """Every source column must exist in the target; returns source columns."""
    columns: dict[str, list[str]] = {}
    for table in CARRY_ORDER:
        if not _single_value(
            source,
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ):
            continue  # an older source without the table simply has no rows
        if not _single_value(
            target,
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ):
            _refuse(
                f"the target has no {table} table — it is not a current v2 "
                "build; rebuild it with the current schema first."
            )
        src_cols = _columns(source, table)
        missing = [c for c in src_cols if c not in set(_columns(target, table))]
        if missing:
            _refuse(
                f"target table {table} lacks source column(s) "
                f"{', '.join(missing)} — the target schema is BEHIND the "
                "source and cannot receive these rows; rebuild the target "
                "with the current schema."
            )
        columns[table] = src_cols
    return columns


def _keyed_plan(
    src_rows: list[dict[str, object]],
    tgt_rows: list[dict[str, object]],
    key_cols: list[str],
    table: str,
) -> list[dict[str, object]]:
    """Rows to carry for a naturally-keyed table; refuse on key divergence."""
    key = lambda row: tuple(row[c] for c in key_cols)  # noqa: E731
    ignored = COMPARE_IGNORED.get(table, frozenset())
    target_by_key = {key(row): row for row in tgt_rows}
    to_carry, diverged = [], []
    for row in src_rows:
        existing = target_by_key.get(key(row))
        if existing is None:
            to_carry.append(row)
        elif any(existing[c] != row[c] for c in row if c not in ignored):
            diverged.append(key(row))
    if diverged:
        shown = ", ".join(str(k if len(k) > 1 else k[0]) for k in diverged[:10])
        _refuse(
            f"{len(diverged)} {table} row(s) differ between source and target "
            f"at the same key ({shown}{'…' if len(diverged) > 10 else ''}) — "
            "the two databases have diverged; decide which is right before "
            "carrying anything."
        )
    return to_carry


def _content_plan(
    src_rows: list[dict[str, object]],
    tgt_rows: list[dict[str, object]],
    content_cols: list[str],
) -> list[dict[str, object]]:
    """Rows to carry for a surrogate-keyed table, diffed by full content."""
    content = lambda row: tuple(row[c] for c in content_cols)  # noqa: E731
    remaining = Counter(content(row) for row in tgt_rows)
    to_carry = []
    for row in src_rows:
        if remaining[content(row)] > 0:
            remaining[content(row)] -= 1
        else:
            to_carry.append(row)
    return to_carry


def carry_forward(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    """Plan and apply the intake-layer carry, or refuse.

    Returns:
        ``carried`` ({table: rows written}, all zero on a no-op or dry run),
        ``noop``, and the three screening snapshots for reporting:
        ``source_rows`` / ``before_rows`` / ``after_rows``.
    """
    _check_schema_fingerprints(source, target)
    _check_salt_fingerprints(source, target)
    _check_completeness(source)
    _check_populated_refusals(source)
    columns = _check_column_compat(source, target)

    src: dict[str, list[dict[str, object]]] = {
        table: _fetch(source, table, cols) for table, cols in columns.items()
    }
    tgt: dict[str, list[dict[str, object]]] = {
        table: _fetch(target, table, cols) for table, cols in columns.items()
    }
    for table in CARRY_ORDER:  # an older source without a table has no rows
        src.setdefault(table, [])
        tgt.setdefault(table, [])
    source_screenings = _screening_rows(source)
    before_screenings = _screening_rows(target)

    # -- concept remap: internal integer ids do not survive a rebuild --------
    # Applied to the SOURCE rows up front, so every later comparison (and the
    # eventual insert) speaks the target's ids. A slug the target does not
    # know refuses immediately: a target row cannot reference a concept the
    # target lacks, so any row carrying an unmapped slug would have to be
    # carried — and the reference layer is maintainer-curated, never filled
    # in here.
    src_slug = dict(source.execute("SELECT id, slug FROM concepts"))
    tgt_id = {
        slug: cid for cid, slug in target.execute("SELECT id, slug FROM concepts")
    }
    unmapped_slugs = set()
    for table in CONCEPT_REMAPPED:
        for row in src.get(table, []):
            concept_id = row.get("concept_id")
            if concept_id is None:
                continue
            slug = src_slug[concept_id]
            mapped = tgt_id.get(slug)
            if mapped is None:
                unmapped_slugs.add(slug)
            else:
                row["concept_id"] = mapped
    if unmapped_slugs:
        _refuse(
            "source rows reference concept slug(s) the target does not have: "
            f"{', '.join(sorted(unmapped_slugs))}. The reference layer is "
            "maintainer-curated and this script never fills it — register "
            "these in the rebuilt database first (or explain why the durable "
            "copy names them)."
        )

    # -- which options travel ------------------------------------------------
    target_options = {row["uid"] for row in tgt["options"]}
    screened = {row["option_uid"] for row in source_screenings}
    missing_screened = sorted(
        row["uid"]
        for row in src["options"]
        if row["uid"] in screened and row["uid"] not in target_options
    )
    prov_by_option: dict[object, set[object]] = {}
    for row in src["option_provenance"]:
        prov_by_option.setdefault(row["option_uid"], set()).add(row["source"])
    not_carryable = [
        uid
        for uid in missing_screened
        if prov_by_option.get(uid, set()) != {"community"}
    ]
    if not_carryable:
        _refuse(
            f"{len(not_carryable)} screened option(s) are absent from the "
            "target and are NOT exclusively community-sourced — they came "
            "from v1 and the rebuild dropped them, which is a migration bug "
            "to investigate, not a row to carry over it. Absent from both "
            "the rebuild and the carried set: " + ", ".join(map(str, not_carryable))
        )
    carried_options = set(missing_screened)

    # -- per-table carry plans ----------------------------------------------
    plan: dict[str, list[dict[str, object]]] = {}
    plan["options"] = [r for r in src["options"] if r["uid"] in carried_options]
    plan["option_provenance"] = _content_plan(
        [
            r
            for r in src["option_provenance"]
            if r["option_uid"] in carried_options or r["source"] == "community"
        ],
        tgt["option_provenance"],
        [c for c in columns["option_provenance"] if c != "id"],
    )
    plan["option_validations"] = [
        r for r in src["option_validations"] if r["option_uid"] in carried_options
    ]
    plan["endorsements"] = _keyed_plan(
        src["endorsements"], tgt["endorsements"], ["uid"], "endorsements"
    )
    plan["contributors"] = _keyed_plan(
        src["contributors"], tgt["contributors"], ["id"], "contributors"
    )
    plan["contributor_identities"] = _keyed_plan(
        src["contributor_identities"],
        tgt["contributor_identities"],
        ["contributor_id"],
        "contributor_identities",
    )
    for table in INTAKE_ONLY_TABLES:
        if table not in columns:
            plan[table] = []
        elif table in SURROGATE_ID_TABLES:
            plan[table] = _content_plan(
                src[table], tgt[table], [c for c in columns[table] if c != "id"]
            )
        else:
            key_cols = _pk_columns(source, table)
            if key_cols:
                plan[table] = _keyed_plan(src[table], tgt[table], key_cols, table)
            else:  # a rowid table with no natural key: diff by full content
                plan[table] = _content_plan(src[table], tgt[table], columns[table])

    # -- screenings: keyed and ordered by original id ------------------------
    source_ids = {row["id"] for row in source_screenings}
    target_by_id = {row["id"]: row for row in before_screenings}
    conflicts = [
        row["id"]
        for row in source_screenings
        if row["id"] in target_by_id and target_by_id[row["id"]] != row
    ]
    if conflicts:
        _refuse(
            f"target screening history conflicts with the source at id(s) "
            f"{', '.join(map(str, conflicts[:10]))}"
            f"{'…' if len(conflicts) > 10 else ''} — the two histories have "
            "diverged (a re-import before the carry-forward, most likely); "
            "rebuild and carry forward first, per the corpus publish runbook."
        )
    if source_screenings:
        max_source_id = source_screenings[-1]["id"]
        strays = sorted(
            rowid
            for rowid in target_by_id
            if rowid <= max_source_id and rowid not in source_ids
        )
        if strays:
            _refuse(
                "the target holds screening row(s) interleaved below the "
                f"source's high-water mark (id(s) "
                f"{', '.join(map(str, strays))}) that the source does not — "
                "the two histories have diverged; investigate before "
                "trusting either."
            )
    plan["option_screenings"] = [
        row for row in source_screenings if row["id"] not in target_by_id
    ]

    # -- reference pre-flight: name every gap, fill none ---------------------
    def _gap(kind: str, values: set) -> None:
        if values:
            shown = ", ".join(map(str, sorted(values)))
            _refuse(
                f"carried rows reference {kind} the target does not have: "
                f"{shown}. The reference layer is maintainer-curated and this "
                "script never fills it — register these in the rebuilt "
                "database first (or explain why the durable copy names them)."
            )

    target_locales = {t for (t,) in target.execute("SELECT tag FROM locales")}
    needed_locales = {
        row["locale"]
        for table, rows in plan.items()
        for row in rows
        if "locale" in row and row["locale"] is not None
    }
    _gap("locale(s)", needed_locales - target_locales)

    target_pls = {
        c for (c,) in target.execute("SELECT code FROM programming_languages")
    }
    needed_pls = {
        row["programming_language"]
        for rows in plan.values()
        for row in rows
        if row.get("programming_language") is not None
    }
    _gap("programming language(s)", needed_pls - target_pls)

    target_rungs = {r for (r,) in target.execute("SELECT rung FROM review_rungs")}
    needed_rungs = {
        row[col]
        for rows in plan.values()
        for row in rows
        for col in ("current_rung", "rung_at_endorsement", "rung_at_session")
        if row.get(col) is not None
    }
    _gap("review rung(s)", needed_rungs - target_rungs)

    # -- FK pre-flight: every carried reference must resolve post-carry ------
    def _unresolved(kind: str, refs: set, present: set, carried: set) -> None:
        gaps = refs - present - carried
        if gaps:
            shown = ", ".join(map(str, sorted(gaps)[:20]))
            _refuse(
                f"carried rows reference {kind} absent from both the rebuild "
                f"and the carried set ({len(gaps)}): {shown}"
                f"{'…' if len(gaps) > 20 else ''}. The rebuild dropped rows "
                "it should carry — investigate before retrying."
            )

    referenced_options = {
        row["option_uid"]
        for rows in plan.values()
        for row in rows
        if "option_uid" in row
    }
    _unresolved("option uid(s)", referenced_options, target_options, carried_options)

    carried_contributors = {row["id"] for row in plan["contributors"]}
    target_contributors = {row["id"] for row in tgt["contributors"]}
    referenced_contributors = {
        row["contributor_id"]
        for rows in plan.values()
        for row in rows
        if row.get("contributor_id") is not None
    }
    _unresolved(
        "contributor id(s)",
        referenced_contributors,
        target_contributors,
        carried_contributors,
    )

    carried_sessions = {row["uid"] for row in plan["review_sessions"]}
    target_sessions = {row["uid"] for row in tgt["review_sessions"]}
    referenced_sessions = {
        row["session_uid"]
        for rows in plan.values()
        for row in rows
        if row.get("session_uid") is not None
    }
    _unresolved(
        "session uid(s)", referenced_sessions, target_sessions, carried_sessions
    )

    carried_endorsements = {row["uid"] for row in plan["endorsements"]}
    target_endorsements = {row["uid"] for row in tgt["endorsements"]}
    referenced_endorsements = {
        row["endorsement_uid"] for row in plan["session_endorsements"]
    }
    _unresolved(
        "endorsement uid(s)",
        referenced_endorsements,
        target_endorsements,
        carried_endorsements,
    )

    # -- canon guard pre-flight (unchanged doctrine) --------------------------
    canon_uids = {
        uid
        for (uid,) in target.execute("SELECT DISTINCT option_uid FROM canon_selections")
    }
    conflicted = sorted(
        {
            row["option_uid"]
            for row in plan["option_screenings"]
            if row["verdict"] != "cleared" and row["option_uid"] in canon_uids
        }
    )
    if conflicted:
        _refuse(
            f"{len(conflicted)} option(s) with a non-cleared verdict to carry "
            "are canon-selected in the target — replaying them would trip "
            "trg_screenings_no_quarantine_while_canon. Pull them from the "
            "canon and reload first, so the demotion is a reviewed change "
            "(see the trigger's doctrine in schema_v2.sql). Conflicted: "
            + ", ".join(conflicted)
        )

    result = {
        "carried": {table: len(plan.get(table, [])) for table in CARRY_ORDER},
        "noop": False,
        "source_rows": source_screenings,
        "before_rows": before_screenings,
        "after_rows": before_screenings,
    }
    if not any(plan.get(table) for table in CARRY_ORDER):
        result["noop"] = True
        return result
    if dry_run:
        return result

    # -- apply, in one transaction -------------------------------------------
    try:
        with target:
            for table in CARRY_ORDER:
                rows = plan.get(table, [])
                if not rows:
                    continue
                cols = (
                    SCREENING_COLUMNS
                    if table == "option_screenings"
                    else tuple(
                        c
                        for c in columns[table]
                        if not (table in SURROGATE_ID_TABLES and c == "id")
                    )
                )
                marks = ", ".join("?" for _ in cols)
                for row in rows:
                    # concept_id was already remapped to the target's ids at
                    # fetch time, so the row inserts verbatim.
                    target.execute(
                        f"INSERT INTO {table} ({', '.join(cols)}) "  # nosec B608 - schema-derived names, parameterized values
                        f"VALUES ({marks})",
                        [row[col] for col in cols],
                    )
    except sqlite3.IntegrityError as error:
        _refuse(
            f"the target database refused a carried row ({error}). Nothing "
            "was committed; investigate before retrying."
        )

    after_screenings = _screening_rows(target)
    after_by_id = {row["id"]: row for row in after_screenings}
    if any(after_by_id.get(row["id"]) != row for row in source_screenings):
        _refuse(
            "post-copy verification failed — the target's screening history "
            "does not read back identical to the source's rows. The write "
            "was transactional, so investigate before re-running."
        )
    result["after_rows"] = after_screenings
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="the previous v2 database holding the intake layer (an upgraded "
        "scratch copy of the durable database — see the module docstring); "
        "opened read-only",
    )
    parser.add_argument(
        "--target",
        type=Path,
        required=True,
        help="the freshly rebuilt v2 database the intake layer moves into",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run every check and report what would be carried; write nothing",
    )
    args = parser.parse_args(argv)

    for label, path in (("source", args.source), ("target", args.target)):
        if not path.is_file():
            raise SystemExit(f"REFUSED: {label} database {path} does not exist")

    # Read-only at the SQLite level: even handed the durable original by
    # mistake, no code path in this script may be able to touch it.
    source = sqlite3.connect(f"file:{args.source}?mode=ro", uri=True)
    # The target goes through schema_v2.connect so every foreign key and
    # append-only trigger is actually enforced during the copy.
    target = connect(args.target)
    try:
        _require_screenings_table(source, "source", args.source)
        _require_screenings_table(target, "target", args.target)
        result = carry_forward(source, target, dry_run=args.dry_run)
    finally:
        source.close()
        target.close()

    print(_report("source", result["source_rows"]))
    print(_report("target (before)", result["before_rows"]))
    print(_report("target (after)", result["after_rows"]))
    carried = {t: n for t, n in result["carried"].items() if n}
    if result["noop"]:
        print(
            "already carried forward — the target holds the full intake "
            "layer; nothing to do"
        )
    elif args.dry_run:
        total = sum(carried.values())
        print(f"dry run — {total} row(s) would be carried; nothing written:")
        for table, count in carried.items():
            print(f"  {table}: {count}")
    else:
        for table, count in carried.items():
            print(f"carried {table}: {count}")
        print(
            "carry complete; next, re-run correct_canon_review_rung.py and "
            "verify counts against the durable copy "
            "(corpus-publish-runbook.md section 1)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
