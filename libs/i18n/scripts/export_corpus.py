"""Export the CORPUS layer of a v2 translations database to Parquet (CORE-1505).

Read-only with respect to the source database. Writes one Parquet file per
Hugging Face dataset config into ``<out>/data/``, a dataset card to
``<out>/README.md``, and a reconciliation ledger to ``<out>/reconciliation.json``.

The publish surface is the CORPUS layer and nothing else:

    concepts, terms, options (+ cached validations, + aggregated provenance
    sources), endorsements, contributors

Two tables are NEVER exported, and the script is built to fail loudly rather
than trust the reader (CORE-1502):

* ``contributor_identities`` -- the only way back from an opaque ``c_<hex>`` id
  to a person. :data:`NEVER_EXPORT` is asserted against every config's SQL
  before a single row is read.
* ``canon_selections`` -- the maintainer decision. The canon lives in the
  monorepo as PR-reviewable text; the community corpus must never imply that
  publishing it is on the table.

Columns are audited too: after writing, every Parquet file is re-opened and the
export aborts if any column in :data:`FORBIDDEN_COLUMNS` survived. Belt (SQL
never selects them) and suspenders (the files prove it).

Counts are DERIVED, never stored: no config carries an endorsement-count
column. The reconciliation ledger recomputes the total from the exported
``endorsements`` rows and cross-checks it against the ``endorsement_counts``
view, so a consumer can always reproduce the headline number from the rows.

Usage:
    uv run python scripts/export_corpus.py --db build/translations_v2.db \\
                                           --out build/hf-corpus \\
                                           [--target-repo legesher/translations] \\
                                           [--push --governance-signoff CORE-1502]

``--push`` is double-gated: it requires ``--governance-signoff CORE-1502`` AND
``LEGESHER_HF_PUSH_APPROVED=1`` in the environment, and it refuses BEFORE
anything is written or any network library is imported. The first push freezes
every published key forever, so it is a governance act, not a script flag.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

#: Tables that must never appear in a published config, under any name, ever.
#:
#: ``contributor_identities`` is the pre-image of the opaque contributor ids --
#: the ONLY way back from ``c_<hex>`` to a person (CORE-1502). ``canon_selections``
#: is the maintainer decision, which lives in the monorepo as reviewable text
#: and is not community data. :func:`_assert_configs_avoid_private_tables` scans
#: every config's SQL against this set before a single row is read.
NEVER_EXPORT: frozenset[str] = frozenset({"contributor_identities", "canon_selections"})

#: Column names that must not survive into any written Parquet file.
#:
#: * ``source_detail`` -- v1 reviewer labels with real first names ride in this
#:   column (``zh_reviewer_review``, ``ur_reviewer_review``, ...); only ``source`` is safe.
#: * ``source_key`` / ``display_name`` -- contributor_identities columns; their
#:   presence anywhere means the private table leaked.
#: * ``comment`` -- endorsement free text; may carry PII (CORE-1502 decision).
FORBIDDEN_COLUMNS: frozenset[str] = frozenset(
    {"source_detail", "source_key", "display_name", "comment"}
)

#: The governance ticket whose sign-off gates the first (and every) HF push.
GOVERNANCE_TICKET = "CORE-1502"

#: Environment variable that must be ``1`` for ``--push`` to proceed. A CLI
#: flag alone is one typo away from a publish; the env var makes the push a
#: deliberate two-key turn.
PUSH_ENV_VAR = "LEGESHER_HF_PUSH_APPROVED"

DEFAULT_TARGET_REPO = "legesher/translations"

#: One SELECT per dataset config. Rules the SQL below obeys:
#:
#: * Internal AUTOINCREMENT ids (``concepts.id``, ``terms.id``) never leave the
#:   database -- the public keys are ``concepts.slug`` and the content-addressed
#:   ``opt_``/``end_``/``c_`` uids.
#: * ``option_provenance.source_detail`` is NOT selected: it carries v1 reviewer
#:   labels containing real first names (CORE-1505). Only the closed ``source``
#:   vocabulary is exported, aggregated per option into a ``sources`` list.
#: * ``endorsements.comment`` is NOT selected: free text offered next to a vote
#:   may carry PII (a name, an email, an @-handle), so publish-or-strip is a
#:   CORE-1502 governance decision and the default is strip.
#: * Every query carries a total ORDER BY so re-exporting the same database
#:   yields byte-identical Parquet files.
CONFIG_SQL: dict[str, str] = {
    "concepts": """
        SELECT slug, definition_en, definition_source, category, pattern_class,
               notes, created_at, updated_at
        FROM concepts
        ORDER BY slug
    """,
    "terms": """
        SELECT c.slug AS concept_slug, t.programming_language, t.name,
               t.category, t.subcategory, t.version_added, t.version_removed,
               t.usage_note, t.doc_url, t.export_role, t.created_at, t.updated_at
        FROM terms t
        JOIN concepts c ON c.id = t.concept_id
        ORDER BY t.programming_language, t.name, c.slug
    """,
    "options": """
        SELECT o.uid AS option_uid, c.slug AS concept_slug, o.locale,
               o.programming_language, o.pl_scope, o.surface_form,
               o.first_seen_at, o.withdrawn_at,
               v.identifier_valid, v.nfkc_stable, v.script_consistent,
               v.collides_en_keyword, v.min_interpreter_ok,
               v.validator_version, v.checked_at
        FROM options o
        JOIN concepts c ON c.id = o.concept_id
        LEFT JOIN option_validations v ON v.option_uid = o.uid
        ORDER BY o.uid
    """,
    "endorsements": """
        SELECT uid, option_uid, contributor_id, method, rung_at_endorsement,
               created_at, retracted_at
        FROM endorsements
        ORDER BY uid
    """,
    "contributors": """
        SELECT id, current_rung, joined_at
        FROM contributors
        ORDER BY id
    """,
}

#: The provenance aggregation feeding the ``options.sources`` list column.
#: DISTINCT + sorted: the list answers "what kinds of source attested this
#: rendering", not "how many rows" -- row-level provenance stays private
#: because its ``source_detail`` cannot be published (see above).
PROVENANCE_SOURCES_SQL = """
    SELECT DISTINCT option_uid, source
    FROM option_provenance
    ORDER BY option_uid, source
"""

#: Base table behind each config, for the row-count reconciliation.
CONFIG_BASE_TABLE: dict[str, str] = {
    "concepts": "concepts",
    "terms": "terms",
    "options": "options",
    "endorsements": "endorsements",
    "contributors": "contributors",
}

#: The PINNED Arrow schema of every config, as (column, kind) pairs.
#:
#: Inference (``pa.table(dict)``) types each column from the data it happens to
#: hold, so a column that is all-NULL in one export (``withdrawn_at`` before the
#: first withdrawal, the validation columns before the first validator run)
#: ships as Arrow type ``null`` and silently flips to a real type the moment
#: data arrives -- schema drift across HF revisions of the same dataset.
#: Declaring the schema also makes the export byte-identical across data
#: states, not just across re-runs of one state.
#:
#: Kinds: ``string`` (ids, text, and ISO-8601 timestamps -- SQLite stores them
#: as TEXT and the corpus publishes them verbatim), ``bool`` (the validation
#: flags; SQLite stores 0/1, the published type is a real boolean), and
#: ``list<string>`` (the aggregated provenance ``sources``). No config
#: currently carries a genuine integer column -- the endorsement count is
#: derived, never stored, by design.
#:
#: CONFIG_SQL and this map must change together; the export refuses on drift.
CONFIG_SCHEMA: dict[str, list[tuple[str, str]]] = {
    "concepts": [
        ("slug", "string"),
        ("definition_en", "string"),
        ("definition_source", "string"),
        ("category", "string"),
        ("pattern_class", "string"),
        ("notes", "string"),
        ("created_at", "string"),
        ("updated_at", "string"),
    ],
    "terms": [
        ("concept_slug", "string"),
        ("programming_language", "string"),
        ("name", "string"),
        ("category", "string"),
        ("subcategory", "string"),
        ("version_added", "string"),
        ("version_removed", "string"),
        ("usage_note", "string"),
        ("doc_url", "string"),
        ("export_role", "string"),
        ("created_at", "string"),
        ("updated_at", "string"),
    ],
    "options": [
        ("option_uid", "string"),
        ("concept_slug", "string"),
        ("locale", "string"),
        ("programming_language", "string"),
        ("pl_scope", "string"),
        ("surface_form", "string"),
        ("first_seen_at", "string"),
        ("withdrawn_at", "string"),
        ("identifier_valid", "bool"),
        ("nfkc_stable", "bool"),
        ("script_consistent", "bool"),
        ("collides_en_keyword", "bool"),
        ("min_interpreter_ok", "bool"),
        ("validator_version", "string"),
        ("checked_at", "string"),
        ("sources", "list<string>"),
    ],
    "endorsements": [
        ("uid", "string"),
        ("option_uid", "string"),
        ("contributor_id", "string"),
        ("method", "string"),
        ("rung_at_endorsement", "string"),
        ("created_at", "string"),
        ("retracted_at", "string"),
    ],
    "contributors": [
        ("id", "string"),
        ("current_rung", "string"),
        ("joined_at", "string"),
    ],
}

#: Well-formedness floor for ``options.locale``: language[-Script][-REGION] in
#: RFC 5646 canonical casing (lowercase language, Titlecase script, UPPERCASE
#: region or 3-digit UN M.49), mirroring the CHECK constraint on ``locales.tag``.
#: This is SYNTAX only -- registry-level validation (is ``qq`` a real language?)
#: arrives when CORE-1500's ``legesher_i18n/bcp47.py`` validator merges; until
#: then this regex is the export-side floor.
BCP47_WELL_FORMED = re.compile(r"^[a-z]{2,3}(-[A-Z][a-z]{3})?(-([A-Z]{2}|[0-9]{3}))?$")

#: The dataset card. YAML header first (configs + license placeholder), then
#: the contract prose: what the corpus is, what is deliberately NOT in it, and
#: why the counts are derivable. This file IS the public promise, so it states
#: the privacy posture in full.
DATASET_CARD = """\
---
# License is a governance decision, not an engineering one: placeholder
# pending CORE-1502 sign-off.
license: other
configs:
  - config_name: concepts
    data_files:
      - split: train
        path: data/concepts.parquet
  - config_name: terms
    data_files:
      - split: train
        path: data/terms.parquet
  - config_name: options
    data_files:
      - split: train
        path: data/options.parquet
  - config_name: endorsements
    data_files:
      - split: train
        path: data/endorsements.parquet
  - config_name: contributors
    data_files:
      - split: train
        path: data/contributors.parquet
---

# Legesher reserved-word translation corpus

> **Private-first.** Per the CORE-1502 decision (2026-07-14), this dataset
> launches as a **private** repo and goes public later, as a separate
> deliberate step once the remaining governance items land (license, consent
> flow, withdrawal policy). The export tooling creates the repo private and
> never flips visibility; the public release is a manual maintainer action.

## What this corpus is

A concept-centric corpus of reserved-word translations for programming
languages: every candidate rendering ("option") of a programming-language
concept in a human locale that anyone -- model, community member, maintainer,
import, or literature -- ever offered, together with every endorsement a
person attached to it. Options are keyed by content-addressed, stable uids
(`opt_` + 24 hex), so the corpus survives database rebuilds and re-exports
byte-identically.

Locales ride on `options.locale` as canonical-case BCP 47 tags; there is no
separate locales config.

## The corpus / canon split

This dataset is the **corpus**: the community evidence layer, append-only by
design. The **canon** -- which rendering Legesher actually ships per locale
(`canon_selections`) -- is a maintainer decision that lives in the monorepo as
PR-reviewable text and is **never published here**. Likewise
`contributor_identities`, the private mapping from opaque contributor ids to
people, is **never exported**; the export tooling hard-fails if either table
would ever be included.

## Configs

### `concepts`

`slug` (the public, frozen key), `definition_en`, `definition_source`,
`category`, `pattern_class`, `notes`, `created_at`, `updated_at`.

### `terms`

A concept's surface form in one programming language: `concept_slug`,
`programming_language`, `name`, `category`, `subcategory`, `version_added`,
`version_removed`, `usage_note`, `doc_url`, `export_role`, `created_at`,
`updated_at`.

### `options`

One candidate rendering of one concept in one locale: `option_uid`,
`concept_slug`, `locale`, `programming_language`, `pl_scope`, `surface_form`,
`first_seen_at`, `withdrawn_at`; the cached mechanical validation verdict
(`identifier_valid`, `nfkc_stable`, `script_consistent`,
`collides_en_keyword`, `min_interpreter_ok`, `validator_version`,
`checked_at`; null when unvalidated); and `sources`, the distinct provenance
kinds that attested the rendering (`model`, `community`, `maintainer`,
`import`, `literature`).

### `endorsements`

One row per endorsement event: `uid`, `option_uid`, `contributor_id`,
`method`, `rung_at_endorsement`, `created_at`, `retracted_at`.

### `contributors`

`id` (opaque `c_` + 16 hex), `current_rung`, `joined_at`.

## Counts are derived, never stored

No config carries an endorsement-count column. The count of an option is
`COUNT(*)` over its non-retracted `endorsements` rows -- recomputable by any
consumer from the published rows, which is what makes it auditable. The export
ships a `reconciliation.json` cross-checking the derived total against the
source database's `endorsement_counts` view.

## PII posture

* Contributor ids are opaque (`c_` + 16 hex, salted digests). They are never a
  name, email, or handle, and the mapping back to a person
  (`contributor_identities`) is never exported.
* Withdrawal (CORE-1502): the identity row is deleted; the contributor row and
  their endorsements remain. Counts survive, PII does not.
* `option_provenance.source_detail` is excluded: it carries v1 reviewer labels
  containing real first names. Only the closed `source` vocabulary is
  published, aggregated into `options.sources`.
* `endorsements.comment` is excluded: free text next to a vote may carry PII;
  publish-or-strip is a CORE-1502 decision and the default is strip.
* `option_flags` (moderation / harm reports) is excluded for now: it is a
  moderation signal about words and the people who flagged them, kept private
  until CORE-1502 settles a publication policy for it.

## Attribution

The legacy community renderings originate from
[legesher/legesher-translations](https://github.com/legesher/legesher-translations)
(MIT, 149 contributors in its `.all-contributorsrc`). MIT permits relicensing
but requires the copyright and permission notice be retained; this card
carries that credit, and the affected rows are machine-identifiable in the
source database's provenance.
"""


def _require_pyarrow() -> tuple[Any, Any]:
    """Import pyarrow, or explain how to get it.

    pyarrow is a dev-group dependency (``uv sync`` brings it in), but the
    exporter should say so rather than stack-trace when run from a bare
    environment.

    Returns:
        The ``(pyarrow, pyarrow.parquet)`` modules.

    Raises:
        SystemExit: when pyarrow is not importable.
    """
    try:
        import pyarrow as pa  # type: ignore[import-untyped]
        import pyarrow.parquet as pq  # type: ignore[import-untyped]
    except ImportError as exc:
        raise SystemExit(
            "export_corpus requires pyarrow to write Parquet files.\n"
            "Install it with:  uv sync  (it is in the dev dependency group)\n"
            "or:               uv add --package legesher-i18n --dev pyarrow"
        ) from exc
    return pa, pq


def _assert_configs_avoid_private_tables() -> None:
    """Structural gate: no published config may mention a NEVER_EXPORT table.

    A word-boundary scan of the ENTIRE SQL text, deliberately NOT a FROM/JOIN
    parse. A parser is a bypass surface -- comma-joins
    (``FROM endorsements e, contributor_identities ci``), quoted names
    (``FROM "contributor_identities"``), and schema-qualified references
    (``main.canon_selections``) all slip past a FROM/JOIN regex -- while a
    refusal gate is allowed false positives: if a config ever legitimately
    needs the *word* ``canon_selections`` (even in a SQL comment), that is
    exactly the moment a human should re-read this gate.

    Runs before a single row is read.

    Raises:
        SystemExit: if any config's SQL mentions a private table.
    """
    queries = dict(CONFIG_SQL)
    queries["options.sources"] = PROVENANCE_SOURCES_SQL
    for name, sql in queries.items():
        mentioned = {
            table
            for table in NEVER_EXPORT
            if re.search(rf"\b{re.escape(table)}\b", sql, re.IGNORECASE)
        }
        if mentioned:
            raise SystemExit(
                f"EXPORT REFUSED: config {name!r} mentions private table(s) "
                f"{sorted(mentioned)}. contributor_identities and "
                "canon_selections are never published (CORE-1502)."
            )


def _assert_no_forbidden_columns(pq: Any, data_dir: Path) -> None:
    """Post-write audit: re-open every Parquet file and check its schema.

    The SQL never selects these columns, but the files are the artifact that
    actually leaves the machine, so the files are what get audited.

    Args:
        pq: The ``pyarrow.parquet`` module.
        data_dir: Directory holding the written ``*.parquet`` files.

    Raises:
        SystemExit: if any written file carries a forbidden column.
    """
    for parquet_path in sorted(data_dir.glob("*.parquet")):
        names = set(pq.ParquetFile(parquet_path).schema_arrow.names)
        leaked = names & FORBIDDEN_COLUMNS
        if leaked:
            # Fail loudly AND leave nothing: a poisoned artifact must not
            # survive its own refusal, or the next `upload_folder` run would
            # push the very file this gate exists to stop.
            parquet_path.unlink()
            raise SystemExit(
                f"EXPORT REFUSED: {parquet_path.name} carried forbidden "
                f"column(s) {sorted(leaked)} and has been deleted. "
                "source_detail/source_key/display_name/comment must never be "
                "published (CORE-1502 / CORE-1505)."
            )


def _render_dataset_card(conn: sqlite3.Connection) -> str:
    """The dataset card with the EXACT language list rendered from the DB.

    The card never claims a count it cannot prove: the locale list is queried
    from the very rows being exported (``options.locale``), so the card and
    the data cannot drift (Madison, 2026-07-14). Two renderings:

    * YAML ``language:`` header -- deduplicated primary language subtags, the
      shape the HF Hub indexes for search/filtering.
    * A ``## Languages`` section -- the full BCP 47 locale tags with their
      option counts, exact and reproducible.
    """
    rows = conn.execute(
        "SELECT locale, COUNT(*) AS n FROM options GROUP BY locale ORDER BY locale"
    ).fetchall()
    primaries = sorted({str(row["locale"]).split("-")[0] for row in rows})
    language_yaml = "language:\n" + "".join(f"  - {code}\n" for code in primaries)

    lines = [
        "## Languages",
        "",
        "Exact BCP 47 locale list carried by `options.locale` in this export",
        "(the primary-subtag rollup above is what the Hub indexes):",
        "",
        "| locale | options |",
        "| --- | ---: |",
    ]
    lines += [f"| {row['locale']} | {row['n']} |" for row in rows]
    section = "\n".join(lines) + "\n\n"

    card = DATASET_CARD.replace(
        "license: other\n", "license: other\n" + language_yaml, 1
    )
    return card.replace(
        "## The corpus / canon split", section + "## The corpus / canon split", 1
    )


def _require_clean_data_dir(data_dir: Path) -> None:
    """``<out>/data`` may hold no Parquet files but this run's own.

    Non-Parquet bystanders (a ``.gitkeep``, an editor swap file) are
    tolerated -- only ``*.parquet`` can ride into the dataset as data.

    ``--push`` uploads the DIRECTORY, so a stale Parquet file from an older
    run -- a renamed config, an abandoned experiment -- would ride along into
    the published dataset unnoticed. Unknown files refuse the export (a human
    decides what they were); the known config files are deleted up front, so
    every byte present after a successful run was written by that run.

    Args:
        data_dir: The ``<out>/data`` directory (already created).

    Raises:
        SystemExit: if the directory holds a Parquet file this exporter does
            not produce.
    """
    known = {f"{name}.parquet" for name in CONFIG_SQL}
    strays = sorted(
        path.name for path in data_dir.glob("*.parquet") if path.name not in known
    )
    if strays:
        raise SystemExit(
            f"EXPORT REFUSED: {data_dir} contains parquet file(s) not produced "
            f"by this exporter: {strays}. A stale artifact would ride along in "
            "the HF push; remove it or use a fresh --out directory."
        )
    for name in known:
        (data_dir / name).unlink(missing_ok=True)


def _arrow_schema(pa: Any, config: str) -> Any:
    """Build the pinned :data:`CONFIG_SCHEMA` for one config as a pa.schema."""
    kinds = {
        "string": pa.string(),
        "bool": pa.bool_(),
        "list<string>": pa.list_(pa.string()),
    }
    return pa.schema([(column, kinds[kind]) for column, kind in CONFIG_SCHEMA[config]])


def _require_well_formed_locales(conn: sqlite3.Connection) -> None:
    """Every published ``options.locale`` must be well-formed BCP 47.

    The locale tag is inside the frozen option uid, so a malformed or
    wrongly-cased tag published once is a permanent fork of that locale's
    corpus. The DB CHECK on ``locales.tag`` should make this unreachable; the
    export re-checks because the Parquet files are the one-way door.

    Args:
        conn: Read-only connection to the v2 database.

    Raises:
        SystemExit: listing every malformed tag found.
    """
    bad = [
        row["locale"]
        for row in conn.execute("SELECT DISTINCT locale FROM options ORDER BY locale")
        if not BCP47_WELL_FORMED.match(row["locale"])
    ]
    if bad:
        raise SystemExit(
            f"EXPORT REFUSED: malformed BCP 47 locale tag(s) in options: {bad}. "
            "Tags must be language[-Script][-REGION] in canonical casing "
            "('ar', 'zh-Hans', 'ar-EG', 'es-419'). Registry-level validation "
            "lands with CORE-1500's bcp47.py."
        )


def _sources_by_option(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """Aggregate provenance to a per-option list of distinct source kinds.

    Only ``option_provenance.source`` is read -- never ``source_detail``, which
    carries v1 reviewer labels with real first names (CORE-1505).

    Args:
        conn: Read-only connection to the v2 database.

    Returns:
        ``option_uid -> sorted distinct source values``.
    """
    sources: dict[str, list[str]] = {}
    for row in conn.execute(PROVENANCE_SOURCES_SQL):
        sources.setdefault(row["option_uid"], []).append(row["source"])
    return sources


def require_push_approval(governance_signoff: str | None) -> None:
    """Refuse to push without the CORE-1502 sign-off AND the env approval.

    Runs BEFORE the export writes anything and BEFORE any network library is
    imported: the first push freezes every published key (option uids,
    endorsement uids, contributor ids) forever, so it must be impossible to
    trip over.

    Args:
        governance_signoff: Value of ``--governance-signoff``.

    Raises:
        SystemExit: unless both keys are turned.
    """
    if governance_signoff != GOVERNANCE_TICKET:
        raise SystemExit(
            f"--push requires --governance-signoff {GOVERNANCE_TICKET}. The first "
            "HF push freezes the published keys and the license posture forever; "
            f"it is gated on the {GOVERNANCE_TICKET} governance decision, not on "
            "this script."
        )
    if os.environ.get(PUSH_ENV_VAR) != "1":
        raise SystemExit(
            f"--push requires {PUSH_ENV_VAR}=1 in the environment. The flag and "
            "the variable are deliberately two separate keys: a command-line "
            "typo must not be able to publish the corpus."
        )


def push_to_hub(out_dir: Path, target_repo: str) -> None:
    """Upload the exported corpus directory to the Hugging Face Hub.

    huggingface_hub is imported lazily so that every non-push code path works
    without the library installed and provably never touches the network stack.

    Args:
        out_dir: The export directory (``data/*.parquet`` + ``README.md``).
        target_repo: Dataset repo id, e.g. ``legesher/translations``.
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise SystemExit(
            "PUSH REFUSED: huggingface_hub is not installed. The push path "
            "needs it: `uv add --package legesher-i18n --dev huggingface_hub` "
            "(every non-push code path works without it)."
        ) from None

    api = HfApi()
    # Private-first (CORE-1502 decision, 2026-07-14): the repo is created
    # PRIVATE and this tool never changes visibility. Going public is a
    # separate, deliberate maintainer action on the Hub -- not a flag here,
    # so no invocation of this script can accidentally publish the corpus.
    api.create_repo(
        repo_id=target_repo,
        repo_type="dataset",
        private=True,
        exist_ok=True,
    )
    api.upload_folder(
        folder_path=str(out_dir),
        repo_id=target_repo,
        repo_type="dataset",
        commit_message=f"corpus export (CORE-1505, signed off via {GOVERNANCE_TICKET})",
    )
    print(f"Pushed {out_dir} -> {target_repo}")


def export_corpus(db_path: Path, out_dir: Path) -> dict[str, Any]:
    """Export the five corpus configs, the dataset card, and the ledger.

    Args:
        db_path: Path to a v2 database. Opened read-only.
        out_dir: Output directory; ``data/`` is created inside it.

    Returns:
        The reconciliation ledger (also written to
        ``<out>/reconciliation.json``).

    Raises:
        SystemExit: if the database does not exist, a config would read a
            private table, a stale artifact sits in the output directory, a
            forbidden column survives into a written file, a locale tag is
            malformed, or the row counts do not reconcile.
    """
    # Path check first: a missing --db should never surface as a pyarrow
    # installation complaint (review finding on PR #20).
    if not db_path.is_file():
        raise SystemExit(
            f"EXPORT REFUSED: no database at {db_path}. --db must point at an "
            "existing v2 translations database (build one with "
            "scripts/migrate_to_v2.py)."
        )

    pa, pq = _require_pyarrow()
    _assert_configs_avoid_private_tables()

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    _require_well_formed_locales(conn)

    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _require_clean_data_dir(data_dir)

    sources = _sources_by_option(conn)
    configs: dict[str, dict[str, int]] = {}
    active_endorsements = 0

    for name, sql in CONFIG_SQL.items():
        cursor = conn.execute(sql)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        table_data: dict[str, Any] = {
            column: [row[index] for row in rows] for index, column in enumerate(columns)
        }
        if name == "options":
            table_data["sources"] = [
                sources.get(uid, []) for uid in table_data["option_uid"]
            ]
            columns.append("sources")
        if name == "endorsements":
            active_endorsements = sum(
                1 for value in table_data["retracted_at"] if value is None
            )

        # The pinned schema is the corpus contract: SQL and CONFIG_SCHEMA must
        # change together, and silently shipping whatever the SELECT happened
        # to produce is exactly the drift the pin exists to prevent.
        schema_columns = [column for column, _ in CONFIG_SCHEMA[name]]
        if columns != schema_columns:
            raise SystemExit(
                f"EXPORT REFUSED: config {name!r} selects {columns} but its "
                f"pinned schema declares {schema_columns}. Update CONFIG_SQL "
                "and CONFIG_SCHEMA together."
            )
        # SQLite stores booleans as 0/1 INTEGERs; the published type is bool.
        for column, kind in CONFIG_SCHEMA[name]:
            if kind == "bool":
                table_data[column] = [
                    None if value is None else bool(value)
                    for value in table_data[column]
                ]

        table = pa.table(table_data, schema=_arrow_schema(pa, name))
        pq.write_table(table, data_dir / f"{name}.parquet")

        db_rows = conn.execute(
            f"SELECT COUNT(*) FROM {CONFIG_BASE_TABLE[name]}"  # noqa: S608 -- fixed map
        ).fetchone()[0]
        configs[name] = {"db_rows": db_rows, "parquet_rows": table.num_rows}

    _assert_no_forbidden_columns(pq, data_dir)

    view_sum = conn.execute(
        "SELECT COALESCE(SUM(endorsements), 0) FROM endorsement_counts"
    ).fetchone()[0]
    dataset_card = _render_dataset_card(conn)
    conn.close()

    ok = all(c["db_rows"] == c["parquet_rows"] for c in configs.values()) and (
        active_endorsements == view_sum
    )
    reconciliation: dict[str, Any] = {
        "configs": configs,
        "derived_endorsements": {
            "parquet_active_endorsements": active_endorsements,
            "endorsement_counts_view_sum": view_sum,
        },
        "ok": ok,
    }

    (out_dir / "README.md").write_text(dataset_card, encoding="utf-8")
    (out_dir / "reconciliation.json").write_text(
        json.dumps(reconciliation, indent=2) + "\n", encoding="utf-8"
    )

    width = max(len(name) for name in configs)
    print("Export reconciliation:")
    for name, count in configs.items():
        verdict = "ok" if count["db_rows"] == count["parquet_rows"] else "MISMATCH"
        print(
            f"  {name.ljust(width)}  db={count['db_rows']:>7,}  "
            f"parquet={count['parquet_rows']:>7,}  {verdict}"
        )
    print(
        f"  derived endorsements: parquet(active)={active_endorsements:,}  "
        f"endorsement_counts view={view_sum:,}  "
        f"{'ok' if active_endorsements == view_sum else 'MISMATCH'}"
    )

    if not ok:
        raise SystemExit(
            "EXPORT FAILED: reconciliation mismatch (see reconciliation.json). "
            "A published file that disagrees with its source database is a "
            "corrupted corpus, not a warning."
        )
    return reconciliation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", type=Path, required=True, help="v2 translations database (read-only)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="output directory (data/*.parquet, README.md, reconciliation.json)",
    )
    parser.add_argument(
        "--target-repo",
        default=DEFAULT_TARGET_REPO,
        help=f"Hugging Face dataset repo id (default: {DEFAULT_TARGET_REPO})",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help=(
            "upload the export to the Hub. Requires --governance-signoff "
            f"{GOVERNANCE_TICKET} AND {PUSH_ENV_VAR}=1; refuses BEFORE writing "
            "anything, because the first push freezes every published key."
        ),
    )
    parser.add_argument(
        "--governance-signoff",
        default=None,
        help=f"the governance ticket authorizing the push ({GOVERNANCE_TICKET})",
    )
    args = parser.parse_args(argv)

    # The push gate runs FIRST: a refused push must leave no artifact behind
    # and must never have imported a network library.
    if args.push:
        require_push_approval(args.governance_signoff)

    export_corpus(args.db, args.out)

    if args.push:
        push_to_hub(args.out, args.target_repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
