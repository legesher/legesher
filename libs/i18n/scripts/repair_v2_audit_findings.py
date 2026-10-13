#!/usr/bin/env python
"""Repair the 2026-08-18 audit's v2 corpus findings (CORE-1973, CORE-1972).

The audit left the corpus (v2) inconsistent with the selection layer (v1) in
three ways, and the intake ritual's carried-forward database means none of
them self-heals. Everything here is a superseding write with provenance —
options are append-only and content-addressed, so a correction is a NEW
option beside the old evidence, never an edit of it.

**Phase 1 — the nine ``except*`` mirrors.** For da/de/fi/hi/mk/pt/ru/te/th,
v2 holds only the migration-era star-less rendering (``legesher:yaml-import``
provenance, imported before the CORE-1839 mirror fix reached the packs),
which the term-aware identifier check rightly refuses forever. The starred v1
selection never became a v2 option, which is the whole v1↔v2 canon delta.
This phase inserts the starred mirror as a new option with a computed
verdict, and materializes its canon row.

Options are minted unscoped, exactly as the migration mints every v1-derived
option, so the uid this script writes is the uid a rebuild produces. On a
rebuild from current v1, which carries the starred mirrors as candidates,
the migration already materializes them and this phase finds nothing to do.

On the audit's "check the ingest path for where the ``*`` was stripped"
item: nothing strips today. The star-less forms are historical YAML values;
the migration imported what the packs then said. A re-ingest of a star-less
form dedupes onto the existing refused option (content-addressed uid) and
stays canon-ineligible, while the starred mirror is its own option — the
defect class cannot recur through the intake path.

**Phase 2 — the five audit-corrected selections.** th ``pow``/``global``,
hu ``classmethod``, tr ``globals``, ms ``locals`` were replaced in v1
(data-repo ``664bc45``) but the corpus still offers only the junk values
and its canon still ratifies them. This phase inserts the corrected
renderings with the v1 audit rationale as provenance, then replaces each
canon row wholesale (delete + insert — ``trg_canon_no_update`` forbids
in-place edits by design; precedent: ``correct_canon_review_rung.py``). The
replacement rung is ``experimental``: a deliberate maintainer decision, not
an auto-pick. ``decided_at`` carries the v1 ``selected_at`` — the timestamp
records when the call was made, not when the bookkeeping caught up. On a
rebuild the canon row already ratifies the correction, at the migration's
``machine`` rung; the phase lifts it to ``experimental``, so a rebuild
converges on the state a repaired copy holds.

**Phase 3 — the CORE-1972 validation backfill.** ``min_interpreter_ok`` was
only ever computed on the intake path; the migrated corpus took the schema
default, so a ``1`` reads "unchecked", not "checked and passed". This phase
recomputes the FULL verdict for every option at the current validator and:

* refuses the whole run if any already-computed column would flip — the
  stored verdicts are supposed to be v3-stable, and silent drift is exactly
  what the freeze triggers exist to prevent;
* writes the computed ``min_interpreter_ok`` and stamps
  ``validator_version`` / ``checked_at``. Filling a schema-default stamp
  with the first computed verdict is the ``ensure_format_char_net`` class of
  write, not a verdict flip, so the freeze triggers are dropped for the
  UPDATE and recreated from the shipped DDL, exactly as that upgrade does.

The v1 database is the source of truth for every surface this script writes:
the cell lists below are the audit scope, the values come from
``selected_translations`` at run time.

Idempotent: a re-run finds every option present, every canon row already
pointing at the corrected rendering, and every validation already stamped,
and reports a no-op. ``--dry-run`` executes the ENTIRE run — schema upgrade,
writes, verification — against a throwaway copy of the database, so the
report has full fidelity (triggers included) while the operational file is
never opened for writing.

Re-appliability: like the CORE-1985 rung correction, part of this is not in
the migration, so a from-scratch rebuild needs the script re-applied: the
migration leaves ``min_interpreter_ok`` at the schema default and the five
corrections at ``machine``. It is a step of the rebuild-integrity sequence in
``docs/corpus-publish-runbook.md`` section 1, run after the rung correction:
the order the durable database went through.

Interpreter: every verdict is recomputed with the running interpreter's
Unicode tables, and the durable verdicts were computed on CPython 3.13
(Unicode 15.1), the export toolchain's interpreter. Run this on 3.13 or
later. On 3.10 to 3.12 the options carrying a 3.13-only code point (18
today: 17 si U+200D, 1 ja U+30FB) read as identifier drift, and the run
refuses before writing.
"""

from __future__ import annotations

import argparse
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

from legesher_i18n.db import schema_v2
from legesher_i18n.db.schema_v2 import (
    connect,
    ensure_intake_screening,
    is_identity_translation,
    normalize_surface_form,
    option_uid,
)
from legesher_i18n.schema_validator import SchemaValidator
from legesher_i18n.surface_validation import (
    VALIDATOR_VERSION,
    allowed_format_chars_for,
    allowed_scripts_for,
    validate_surface,
)

#: The audit's scope, not its data: surfaces are read from v1 at run time.
EXCEPT_STAR_TERM = "except*"
EXCEPT_STAR_LOCALES: tuple[str, ...] = (
    "da",
    "de",
    "fi",
    "hi",
    "mk",
    "pt",
    "ru",
    "te",
    "th",
)

#: (locale, term name) cells replaced in v1 by the 2026-08-18 audit
#: (data-repo ``664bc45``) and still junk in v2.
CORRECTED_CELLS: tuple[tuple[str, str], ...] = (
    ("th", "pow"),
    ("th", "global"),
    ("hu", "classmethod"),
    ("tr", "globals"),
    ("ms", "locals"),
)

#: The canon rows' scope. Options are NOT scoped: the migration mints every
#: v1-derived option with ``programming_language`` NULL (``pl_scope`` '*'),
#: and an option's uid is content-addressed over its scope, so minting these
#: python-scoped would give the same word a uid no rebuild reproduces.
PROGRAMMING_LANGUAGE = "python"

#: Every provenance row this script writes carries this detail, so the
#: repair is queryable as a cohort.
SOURCE_DETAIL = "core-1973-v2-repair"

#: The verdict columns that must NOT change under this script. Phase 3 is a
#: backfill of the stamped column, never a revalidation that flips computed
#: facts — drift here aborts the run before any write.
FROZEN_VERDICT_COLUMNS = (
    "identifier_valid",
    "nfkc_stable",
    "nfkc_delta_class",
    "script_consistent",
    "collides_en_keyword",
    "format_chars_clean",
)


class RepairRefused(SystemExit):
    """A fail-closed refusal. No repair row has been committed.

    The schema upgrade that runs when the file is opened
    (``ensure_intake_screening``) commits on its own, by design, before the
    repair's transaction starts; a refusal does not roll that back.
    """

    def __init__(self, message: str) -> None:
        super().__init__(f"REFUSED: {message} No repair row is committed; investigate.")


@dataclass
class Counts:
    """What one phase did (or, on a dry run, did to the throwaway copy)."""

    created_options: int = 0
    created_canon: int = 0
    replaced_canon: int = 0
    backfilled: int = 0
    already_correct: int = 0


def _v1_selected(v1: sqlite3.Connection, locale: str, term_name: str) -> sqlite3.Row:
    """The v1 selection for one (locale, term) cell — exactly one row."""
    rows = v1.execute(
        "SELECT s.translation, s.selected_at, s.selected_by, s.selection_reason"
        " FROM selected_translations s JOIN terms t ON t.id = s.term_id"
        " WHERE t.name = ? AND s.language_code = ?",
        (term_name, locale),
    ).fetchall()
    if len(rows) != 1:
        raise RepairRefused(
            f"v1 holds {len(rows)} selections for {locale}/{term_name}, expected"
            " exactly 1."
        )
    return rows[0]


def _concept_id(conn: sqlite3.Connection, slug: str) -> int:
    row = conn.execute("SELECT id FROM concepts WHERE slug = ?", (slug,)).fetchone()
    if row is None:
        raise RepairRefused(f"v2 has no concept with slug {slug!r}.")
    return row[0]


def _subtag(conn: sqlite3.Connection, locale: str) -> str:
    row = conn.execute(
        "SELECT language_subtag FROM locales WHERE tag = ?", (locale,)
    ).fetchone()
    if row is None:
        raise RepairRefused(f"v2 has no locale {locale!r} in the reference layer.")
    return row[0]


def _min_interpreter_ok(surface: str) -> bool:
    return not any(ch in SchemaValidator._XID_ONLY_FROM_CPYTHON_313 for ch in surface)


def _canon_eligible(verdict) -> bool:
    """Mirror of ``trg_canon_requires_valid_identifier``'s predicate."""
    return (
        verdict.identifier_valid
        and verdict.script_consistent
        and (verdict.nfkc_stable or verdict.nfkc_delta_class == "sara-am-only")
        and verdict.format_chars_clean
    )


def _ensure_option(
    conn: sqlite3.Connection,
    *,
    concept_id: int,
    slug: str,
    locale: str,
    surface: str,
    rationale: str,
    counts: Counts,
) -> str:
    """Insert the option, its computed verdict, and its provenance — each
    only when absent. Returns the option uid.

    The option is unscoped, as the migration mints it (see
    :data:`PROGRAMMING_LANGUAGE`)."""
    uid = option_uid(slug, locale, surface)

    if conn.execute("SELECT 1 FROM options WHERE uid = ?", (uid,)).fetchone() is None:
        conn.execute(
            "INSERT INTO options (uid, concept_id, locale, surface_form)"
            " VALUES (?, ?, ?, ?)",
            (uid, concept_id, locale, surface),
        )
        counts.created_options += 1
    else:
        counts.already_correct += 1

    if (
        conn.execute(
            "SELECT 1 FROM option_validations WHERE option_uid = ?", (uid,)
        ).fetchone()
        is None
    ):
        subtag = _subtag(conn, locale)
        verdict = validate_surface(
            surface,
            slug,
            allowed_scripts_for(subtag),
            allowed_format_chars_for(subtag),
        )
        conn.execute(
            "INSERT INTO option_validations (option_uid, validator_version,"
            " identifier_valid, nfkc_stable, nfkc_delta_class, script_consistent,"
            " collides_en_keyword, min_interpreter_ok, format_chars_clean)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                uid,
                VALIDATOR_VERSION,
                int(verdict.identifier_valid),
                int(verdict.nfkc_stable),
                verdict.nfkc_delta_class,
                int(verdict.script_consistent),
                int(verdict.collides_en_keyword),
                int(_min_interpreter_ok(surface)),
                int(verdict.format_chars_clean),
            ),
        )

    if (
        conn.execute(
            "SELECT 1 FROM option_provenance WHERE option_uid = ? AND source ="
            " 'legesher' AND source_detail = ?",
            (uid, SOURCE_DETAIL),
        ).fetchone()
        is None
    ):
        conn.execute(
            "INSERT INTO option_provenance (option_uid, source, source_detail,"
            " rationale) VALUES (?, 'legesher', ?, ?)",
            (uid, SOURCE_DETAIL, rationale),
        )
    return uid


def _canon_row(
    conn: sqlite3.Connection, concept_id: int, locale: str
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT option_uid, surface_form, status FROM canon_selections"
        " WHERE concept_id = ? AND locale = ? AND pl_scope = ?",
        (concept_id, locale, PROGRAMMING_LANGUAGE),
    ).fetchone()


def _insert_canon(
    conn: sqlite3.Connection,
    *,
    concept_id: int,
    locale: str,
    uid: str,
    surface: str,
    slug: str,
    status: str,
    decided_at: str | None,
    decision_reason: str,
) -> None:
    conn.execute(
        "INSERT INTO canon_selections (concept_id, locale, programming_language,"
        " option_uid, surface_form, status, identity_ok, decided_by, decided_at,"
        " decision_reason, source_file) VALUES"
        " (?, ?, ?, ?, ?, ?, ?, 'CORE-1973',"
        " COALESCE(?, datetime('now')), ?, ?)",
        (
            concept_id,
            locale,
            PROGRAMMING_LANGUAGE,
            uid,
            surface,
            status,
            int(is_identity_translation(slug, surface)),
            decided_at,
            decision_reason,
            f"libs/i18n/canon/{locale}.toml",
        ),
    )


def repair_except_star_mirrors(
    conn: sqlite3.Connection, v1: sqlite3.Connection
) -> Counts:
    """Phase 1: materialize the starred v1 mirrors and their canon rows."""
    counts = Counts()
    concept_id = _concept_id(conn, EXCEPT_STAR_TERM)
    for locale in EXCEPT_STAR_LOCALES:
        selected = _v1_selected(v1, locale, EXCEPT_STAR_TERM)
        surface = normalize_surface_form(selected["translation"])
        if not surface.endswith("*"):
            raise RepairRefused(
                f"v1's {locale}/{EXCEPT_STAR_TERM} selection {surface!r} does not"
                " carry the trailing '*'; the premise of this repair does not"
                " hold."
            )
        subtag = _subtag(conn, locale)
        verdict = validate_surface(
            surface,
            EXCEPT_STAR_TERM,
            allowed_scripts_for(subtag),
            allowed_format_chars_for(subtag),
        )
        if not _canon_eligible(verdict):
            raise RepairRefused(
                f"the starred mirror {surface!r} for {locale} fails mechanical"
                f" validation ({verdict}); it cannot be canon."
            )
        uid = _ensure_option(
            conn,
            concept_id=concept_id,
            slug=EXCEPT_STAR_TERM,
            locale=locale,
            surface=surface,
            rationale=(
                "CORE-1973: starred v1 mirror missing from the corpus"
                " (2026-08-18 audit item 1). v1 selection reason:"
                f" {selected['selection_reason']}"
            ),
            counts=counts,
        )
        existing = _canon_row(conn, concept_id, locale)
        if existing is None:
            _insert_canon(
                conn,
                concept_id=concept_id,
                locale=locale,
                uid=uid,
                surface=surface,
                slug=EXCEPT_STAR_TERM,
                status="machine",
                decided_at=selected["selected_at"],
                decision_reason=(
                    "CORE-1973: materialize the v1 starred except* selection"
                    " absent from v2 canon (2026-08-18 audit item 1)."
                ),
            )
            counts.created_canon += 1
        elif existing["option_uid"] != uid:
            same_word = existing["surface_form"] == surface
            raise RepairRefused(
                f"canon for {locale}/{EXCEPT_STAR_TERM} ratifies option"
                f" {existing['option_uid']} ({existing['surface_form']!r}), not"
                f" the v1 mirror's option {uid} ({surface!r})."
                + (
                    " Same word under a different option id: an earlier"
                    " revision of this script minted it python-scoped."
                    " Re-run against a pre-repair copy instead."
                    if same_word
                    else " Someone decided differently since the audit; decide"
                    " deliberately rather than letting this script overwrite it."
                )
            )
    return counts


def repair_corrected_selections(
    conn: sqlite3.Connection, v1: sqlite3.Connection
) -> Counts:
    """Phase 2: ingest the five audit corrections and replace their canon."""
    counts = Counts()
    for locale, term_name in CORRECTED_CELLS:
        selected = _v1_selected(v1, locale, term_name)
        surface = normalize_surface_form(selected["translation"])
        concept_id = _concept_id(conn, term_name)
        uid = _ensure_option(
            conn,
            concept_id=concept_id,
            slug=term_name,
            locale=locale,
            surface=surface,
            rationale=(
                "CORE-1973: 2026-08-18 audit correction carried from v1"
                f" (data-repo 664bc45). {selected['selection_reason']}"
            ),
            counts=counts,
        )
        existing = _canon_row(conn, concept_id, locale)
        if existing is None:
            raise RepairRefused(
                f"canon for {locale}/{term_name} is missing entirely; this"
                " phase replaces a junk row and cannot invent one."
            )
        if existing["option_uid"] == uid and existing["status"] != "machine":
            # Already ratified at experimental or above: a repaired copy, or
            # a later review. Nothing to do, and nothing is ever demoted.
            counts.already_correct += 1
            continue
        # A row above machine on a different word refuses. Any machine row,
        # whatever word it ratifies (the junk value on a pre-repair copy,
        # the correction itself on a rebuild), is replaced wholesale at
        # experimental with the correction.
        if existing["status"] != "machine":
            raise RepairRefused(
                f"canon for {locale}/{term_name} sits at rung"
                f" {existing['status']!r}; this script only replaces the"
                " migration-era machine rung."
            )
        deleted = conn.execute(
            "DELETE FROM canon_selections WHERE concept_id = ? AND locale = ?"
            " AND pl_scope = ?",
            (concept_id, locale, PROGRAMMING_LANGUAGE),
        ).rowcount
        if deleted != 1:
            raise RepairRefused(
                f"deleting canon for {locale}/{term_name} removed {deleted}"
                " rows, expected exactly 1."
            )
        _insert_canon(
            conn,
            concept_id=concept_id,
            locale=locale,
            uid=uid,
            surface=surface,
            slug=term_name,
            status="experimental",
            decided_at=selected["selected_at"],
            decision_reason=selected["selection_reason"],
        )
        counts.replaced_canon += 1
    return counts


def backfill_min_interpreter(conn: sqlite3.Connection) -> Counts:
    """Phase 3: compute ``min_interpreter_ok`` corpus-wide (CORE-1972).

    Recomputes the full verdict for every option, refuses on drift in any
    already-computed column, and stamps the current validator version. The
    freeze triggers are dropped for the UPDATE and recreated from the shipped
    DDL — the ``ensure_format_char_net`` convention for filling a stamped
    column that predates its computation.
    """
    counts = Counts()
    orphans = conn.execute(
        "SELECT COUNT(*) FROM options o WHERE NOT EXISTS"
        " (SELECT 1 FROM option_validations v WHERE v.option_uid = o.uid)"
    ).fetchone()[0]
    if orphans:
        raise RepairRefused(
            f"{orphans} option(s) have no validation row at all; that is a"
            " different defect than the stamped column this backfill fills."
        )

    drift: list[str] = []
    updates: list[tuple[int, str]] = []
    rows = conn.execute(
        "SELECT v.option_uid, v.validator_version, v.min_interpreter_ok,"
        "       v.identifier_valid, v.nfkc_stable, v.nfkc_delta_class,"
        "       v.script_consistent, v.collides_en_keyword, v.format_chars_clean,"
        "       o.surface_form, o.locale, o.pl_scope, o.concept_id,"
        "       l.language_subtag,"
        # The term name carries the structural affixes the identifier check
        # mirrors, so it must be the TERM's spelling, not the concept slug —
        # a dunder's slug spells its underscores as dashes ('--import--'),
        # which would demand literal dashes on every rendering. Prefer the
        # option's own PL scope, then any term of the concept (a '*'-scoped
        # option has no matching PL row), and only then the slug (a concept
        # with no terms at all, where slug and term spelling coincide).
        "       COALESCE((SELECT t.name FROM terms t WHERE t.concept_id ="
        "                 o.concept_id AND t.programming_language = o.pl_scope"
        "                 ORDER BY t.id LIMIT 1),"
        "                (SELECT t.name FROM terms t WHERE t.concept_id ="
        "                 o.concept_id ORDER BY t.id LIMIT 1),"
        "                (SELECT c.slug FROM concepts c WHERE c.id ="
        "                 o.concept_id)) AS term_name"
        " FROM option_validations v"
        " JOIN options o ON o.uid = v.option_uid"
        " JOIN locales l ON l.tag = o.locale"
    ).fetchall()
    for row in rows:
        verdict = validate_surface(
            row["surface_form"],
            row["term_name"],
            allowed_scripts_for(row["language_subtag"]),
            allowed_format_chars_for(row["language_subtag"]),
        )
        computed = {
            "identifier_valid": int(verdict.identifier_valid),
            "nfkc_stable": int(verdict.nfkc_stable),
            "nfkc_delta_class": verdict.nfkc_delta_class,
            "script_consistent": int(verdict.script_consistent),
            "collides_en_keyword": int(verdict.collides_en_keyword),
            "format_chars_clean": int(verdict.format_chars_clean),
        }
        for column in FROZEN_VERDICT_COLUMNS:
            if row[column] != computed[column]:
                drift.append(
                    f"{row['option_uid']} ({row['locale']}/{row['term_name']}):"
                    f" {column} stored {row[column]!r}, computed"
                    f" {computed[column]!r}"
                )
        min_ok = int(_min_interpreter_ok(row["surface_form"]))
        if (
            row["validator_version"] != VALIDATOR_VERSION
            or row["min_interpreter_ok"] != min_ok
        ):
            updates.append((min_ok, row["option_uid"]))
        else:
            counts.already_correct += 1

    if drift:
        preview = "\n  ".join(drift[:20])
        raise RepairRefused(
            f"{len(drift)} stored verdict value(s) disagree with the"
            f" {VALIDATOR_VERSION} recomputation; this backfill only fills the"
            f" stamped column and must not paper over drift:\n  {preview}\n"
        )

    if updates:
        fresh = schema_v2._fresh_schema_objects()
        for name in schema_v2._VALIDATION_FREEZE_TRIGGERS:
            conn.execute(f"DROP TRIGGER IF EXISTS {name}")  # nosec B608
        conn.executemany(
            "UPDATE option_validations SET min_interpreter_ok = ?,"
            " validator_version = ?, checked_at = datetime('now')"
            " WHERE option_uid = ?",
            [(min_ok, VALIDATOR_VERSION, uid) for min_ok, uid in updates],
        )
        for kind, name, statement in fresh:
            if kind == "trigger" and name in schema_v2._VALIDATION_FREEZE_TRIGGERS:
                conn.execute(statement)
        counts.backfilled = len(updates)
    return counts


def verify(conn: sqlite3.Connection, v1: sqlite3.Connection) -> list[str]:
    """The post-repair invariants. Returns human-readable failures."""
    failures: list[str] = []
    v1_count = v1.execute("SELECT COUNT(*) FROM selected_translations").fetchone()[0]
    v2_count = conn.execute("SELECT COUNT(*) FROM canon_selections").fetchone()[0]
    if v1_count != v2_count:
        failures.append(
            f"canon delta still open: v1 holds {v1_count} selections, v2 holds"
            f" {v2_count} canon rows."
        )
    concept_id = _concept_id(conn, EXCEPT_STAR_TERM)
    for locale in EXCEPT_STAR_LOCALES:
        row = _canon_row(conn, concept_id, locale)
        if row is None or not row["surface_form"].endswith("*"):
            failures.append(f"{locale}/{EXCEPT_STAR_TERM} canon row is not starred.")
    for locale, term_name in CORRECTED_CELLS:
        expected = normalize_surface_form(
            _v1_selected(v1, locale, term_name)["translation"]
        )
        row = _canon_row(conn, _concept_id(conn, term_name), locale)
        if row is None or row["surface_form"] != expected:
            failures.append(f"{locale}/{term_name} canon row is not the correction.")
    stale = conn.execute(
        "SELECT COUNT(*) FROM option_validations WHERE validator_version <> ?",
        (VALIDATOR_VERSION,),
    ).fetchone()[0]
    if stale:
        failures.append(f"{stale} validation row(s) still carry an old validator.")
    for name in schema_v2._VALIDATION_FREEZE_TRIGGERS:
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            (name,),
        ).fetchone()
        if present is None:
            failures.append(f"freeze trigger {name} is missing after the run.")
    return failures


def run(db_path: Path, v1_path: Path) -> tuple[dict[str, Counts], int]:
    """The whole repair against *db_path*, committed only if verification holds."""
    conn = connect(db_path)
    conn.row_factory = sqlite3.Row
    v1 = sqlite3.connect(f"file:{v1_path}?mode=ro", uri=True)
    v1.row_factory = sqlite3.Row
    try:
        # The carried-forward file may predate CORE-2029; every writable
        # consumer upgrades the file it opens. Commits on its own, by design.
        ensure_intake_screening(conn)

        conn.execute("BEGIN IMMEDIATE")
        try:
            results = {
                "except_star": repair_except_star_mirrors(conn, v1),
                "corrections": repair_corrected_selections(conn, v1),
                "backfill": backfill_min_interpreter(conn),
            }
            failures = verify(conn, v1)
            if failures:
                raise RepairRefused(
                    "post-repair verification failed:\n  " + "\n  ".join(failures)
                )
        except BaseException:
            conn.rollback()
            raise
        conn.commit()

        min_ok_zero = conn.execute(
            "SELECT COUNT(*) FROM option_validations WHERE min_interpreter_ok = 0"
        ).fetchone()[0]
        return results, min_ok_zero
    finally:
        v1.close()
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--db", type=Path, required=True, help="v2 corpus database")
    parser.add_argument(
        "--v1-db", type=Path, required=True, help="v1 selection database (read-only)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run everything against a throwaway copy and report",
    )
    args = parser.parse_args(argv)
    if not args.db.is_file():
        raise RepairRefused(f"no database at {args.db}.")
    if not args.v1_db.is_file():
        raise RepairRefused(f"no v1 database at {args.v1_db}.")

    if args.dry_run:
        with tempfile.TemporaryDirectory() as scratch:
            copy = Path(scratch) / args.db.name
            # The sqlite backup API, not a file copy: a WAL-mode database
            # with un-checkpointed pages would give a bare copyfile a stale
            # snapshot, and the dry-run report could then disagree with the
            # real run it exists to predict.
            source = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
            snapshot = sqlite3.connect(copy)
            try:
                source.backup(snapshot)
            finally:
                snapshot.close()
                source.close()
            results, min_ok_zero = run(copy, args.v1_db)
        prefix = "[dry-run, discarded] "
    else:
        results, min_ok_zero = run(args.db, args.v1_db)
        prefix = ""

    star, fixes, backfill = (
        results["except_star"],
        results["corrections"],
        results["backfill"],
    )
    print(
        f"{prefix}except* mirrors: {star.created_options} option(s) created,"
        f" {star.created_canon} canon row(s) materialized;"
        f" corrections: {fixes.created_options} option(s) created,"
        f" {fixes.replaced_canon} canon row(s) replaced;"
        f" backfill: {backfill.backfilled} validation row(s) stamped"
        f" {VALIDATOR_VERSION}, min_interpreter_ok=0 on"
        f" {min_ok_zero} option(s); verification passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
