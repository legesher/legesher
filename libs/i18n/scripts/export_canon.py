#!/usr/bin/env python
"""Export ``canon_selections`` as the ``legesher/language-canon`` dataset.

Three artifacts, three questions:

* corpus -- "what did anyone ever propose for this concept?"  (the evidence)
* canon  -- "which rendering is the decision, and how much review is behind
  it?"  (this script)
* packs  -- "what does ``import legesher`` actually give me?"  (developer-facing)

The canon publishes deliberately early. Every row carries a rung on the
maturity ladder and today essentially all of them sit at the bottom of it;
that is the point rather than a caveat, because the artifact's value is that
it grows in public as native review lands.

**This script never writes to the database.** It opens ``mode=ro`` so that
publishing can never mutate the thing it is publishing, and publishing the
canon does not make the canon writable from the Hub -- the write path is
unchanged and stays in the monorepo.

Three filters and one mapping stand between ``canon_selections`` and the
artifact; each is a decision, not a convenience, and each is documented at its
constant below.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any

_I18N_ROOT = Path(__file__).resolve().parent.parent

#: Dataset repo. The canon is the DECISION layer; ``legesher/language-corpus``
#: is the evidence behind it and ``legesher/language-packs`` is what actually
#: ships. Naming the three on that split is the point -- "canon" stopped being
#: a second name for the packs on 2026-08-19.
DEFAULT_TARGET_REPO = "legesher/language-canon"

#: Apache-2.0 (Madison, 2026-08-19). The canon is data today, but it is meant
#: to be consumed IN CODE later -- generated constants, vendored glossaries,
#: whatever the engine needs -- and a code licence removes the friction at that
#: boundary rather than leaving it to be discovered there.
#:
#: This deliberately differs from the corpus (CC-BY-4.0). Legesher holds the
#: compilation right on both, so licensing its own compilation differently is
#: ours to do; the corpus grant is what Legesher gives the public, not a
#: constraint on Legesher. The recorded counter-argument: Apache-2.0 is written
#: for software and says nothing about database rights, which CC BY 4.0 covers
#: explicitly. The call was made knowing that, on the code-reuse ground above.
DECLARED_LICENSE = "apache-2.0"

#: The governance decision covering contributor data in any published
#: artifact. The canon carries no contributor identity (see ROLE_BY_DECIDER)
#: but it is derived from work contributors did, so it sits under the same
#: sign-off rather than inventing a second one.
GOVERNANCE_TICKET = "CORE-1502"

#: Both keys of the two-key turn, matching the corpus exporter exactly. A CLI
#: flag alone is one typo away from a publish.
PUSH_ENV_VAR = "LEGESHER_HF_PUSH_APPROVED"
TARGET_OVERRIDE_ENV_VAR = "LEGESHER_HF_TARGET_OVERRIDE"

#: The single Python target. ``canon_selections.pl_scope`` is a real populated
#: column carrying 62 JavaScript rows, 46 of them JavaScript-ONLY concepts
#: (``const``, ``let``, ``typeof``, ``null``, ``new``, ``do``, ``bigint``, ...)
#: in Arabic and nothing else. It is unreviewed draft terminology that a
#: partner agreement keeps non-public, and it is the same set
#: ``yaml_exporter.py`` already drops for the packs.
#:
#: The remaining 16 are shared concepts (``if``, ``while``) whose JavaScript
#: row carries the identical ``option_uid`` and surface form as its Python
#: twin, so excluding them loses no information at all.
TARGET_PL_SCOPE = "python"

#: Ukrainian holds exactly six selections -- ``def``, ``print``, ``return``,
#: ``if``, ``str``, ``none`` -- every one of them ``language-showcase-draft``.
#: That is marketing demo material rather than canon, there is no shipped uk
#: pack behind it, and six cherry-picked words beside 51 locales at 183 rows
#: each reads as a broken language rather than an early one. Excluding it also
#: makes canon and packs agree at 51 locales, which is one less number to
#: explain.
EXCLUDED_LOCALES: frozenset[str] = frozenset({"uk"})

#: ``decided_by`` -> published role.
#:
#: The raw column cannot ship. It carries internal ticket ids on roughly 4,600
#: rows (a published file may never cite a ticket that is unresolvable to
#: everyone who can read it), one value with a ticket embedded in free prose,
#: and contributor handles in plaintext -- the same ``<firstname>_review``
#: family that ``export_corpus.FORBIDDEN_COLUMNS`` already refuses to publish
#: through ``source_detail``.
#:
#: The vocabulary is deliberately open: as review phases arrive this mapping
#: gains values. That is why an unmapped value is a hard failure rather than a
#: default -- see :func:`map_decider_role`.
ROLE_BY_DECIDER: dict[str, str] = {
    # Migration and backfill: the value was already in the shipped pack, or a
    # batch job put it there.
    "automated": "automated",
    "CORE-1400": "automated",
    "CORE-606": "automated",
    "core-1303": "automated",
    "core-1317": "automated",
    "collision_resolution": "automated",
    "quality_review": "automated",
    "core-710-agent-batches": "automated",
    # Agent-assisted curation. Mapped to `automated` rather than `maintainer`
    # on Madison's call (2026-08-19): in practice these were collision
    # resolution during in-session curation, not editorial judgement. It also
    # keeps the ratified bright line intact -- the canon is never
    # model-written, so no published role may imply that it was.
    "claude-code": "automated",
    "claude-fable-5": "automated",
    "term-screening remediation (claude-fable-5, CORE-1763)": "automated",
    # A maintainer-run script correction pass over non-Latin scripts. Machine
    # work, not native review, and mapped as such (Madison, 2026-08-19).
    "core-1318-native-fix": "automated",
}

#: Reviewer handles are matched by SHAPE, never enumerated.
#:
#: The raw values in this family are people's names. This file is public, so
#: listing them here would put contributor identities in source -- the exact
#: thing the published artifact goes to lengths to avoid, undone one import
#: statement away.
#:
#: Shape-matching is also the more correct rule. Enumerating names means a new
#: reviewer needs a code change before their work classifies, and the failure
#: mode when someone forgets is silent misclassification as ``automated`` --
#: which is precisely the bug this mapping was built around. Matching the shape
#: has neither problem: a reviewer nobody has seen before resolves correctly on
#: their first row.
#:
#: ROLE_BY_DECIDER is consulted FIRST, which is load-bearing: ``quality_review``
#: fits this shape but is a maintainer quality pass, not a person, and it maps
#: to ``automated`` up there. Process words that look like handles must stay
#: enumerated.
REVIEWER_HANDLE_ROLE = "native-reviewer"

#: Roles the artifact may contain. ``maintainer`` is defined and currently
#: unoccupied -- declared rather than omitted so a consumer reading the card
#: sees the shape of the vocabulary instead of inferring it from today's data.
PUBLISHED_ROLES: tuple[str, ...] = ("automated", "maintainer", "native-reviewer")

#: The rungs, bottom to top. ``status`` answers HOW MUCH REVIEW stands behind a
#: row; ``decided_by`` answers WHO made the last call. Keeping the two axes
#: separate is what lets an initial native reviewer appear in the artifact
#: without promoting anything: ``reviewed`` requires multiple voices, and one
#: reviewer never gets there alone.
LADDER: tuple[str, ...] = ("machine", "experimental", "reviewed", "official")

#: A contributor handle in the ``<name>_review`` family. Every such value is
#: mapped explicitly above; this pattern is the backstop that refuses a NEW
#: one rather than letting it ride into the artifact as a plaintext name.
HANDLE_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*_review$", re.IGNORECASE)

#: Any internal ticket reference. Applied to every published string cell, not
#: just to ``decided_by``: the rule is that no published file cites a ticket,
#: and a guard scoped to the column we happen to worry about is not that rule.
TICKET_PATTERN = re.compile(r"\b(?:CORE|HOME|LOCAL|PARTNER)-\d+\b", re.IGNORECASE)

#: One SELECT, one config. Total ORDER BY so re-exporting the same database
#: yields byte-identical Parquet.
CANON_SQL = """
SELECT
    c.slug                AS concept,
    c.category            AS category,
    cs.locale             AS locale,
    cs.option_uid         AS option_uid,
    cs.surface_form       AS surface_form,
    cs.status             AS status,
    cs.identity_ok        AS identity_ok,
    cs.decided_by         AS decided_by,
    cs.decided_at         AS decided_at
FROM canon_selections cs
JOIN concepts c ON c.id = cs.concept_id
WHERE cs.pl_scope = :pl_scope
ORDER BY cs.locale, c.slug
"""

#: Columns the export writes, in order. ``decision_reason``, ``source_file``
#: and ``source_revision`` are deliberately absent this iteration:
#:
#: * ``decision_reason`` cites tickets on nearly every high-count value and
#:   needs a controlled vocabulary first.
#: * ``source_file`` names ``libs/i18n/canon/<locale>.toml`` on all 9,443 rows
#:   and that directory has never existed in git history. The schema presents
#:   the column as proof a row came from reviewed text; with no files behind
#:   it, publishing it would ship fabricated provenance.
#: * ``source_revision`` is empty on every row.
PUBLISHED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("concept", "string"),
    ("category", "string"),
    ("locale", "string"),
    ("option_uid", "string"),
    ("surface_form", "string"),
    ("status", "string"),
    ("identity_ok", "bool"),
    ("decided_by", "string"),
    ("decided_at", "string"),
)

#: The ``locales`` config: one row per language, its identity and its ladder
#: state. Answers "how far along is each language?" without downloading the
#: full canon.
#:
#: Every column here is a property of the LOCALE and varies across rows. The
#: language attributes live only here and the canon config joins on ``locale``
#: -- deliberately the opposite of the packs dataset, which denormalised
#: ``language_name`` / ``native_name`` / ``rtl`` / ``tier`` into 46,512
#: vocabulary rows and so has to update a locale's tier in two places.
#:
#: Pack tier is NOT here. It is a different ladder over a different thing --
#: a whole pack rather than one rendering -- and it lives in
#: ``legesher/language-packs``. Carrying it here would re-create exactly the
#: conflation the card warns readers about.
LOCALE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("locale", "string"),
    ("language_name", "string"),
    ("native_name", "string"),
    ("status", "string"),
    ("rtl", "bool"),
    ("decisions", "int"),
    ("machine", "int"),
    ("experimental", "int"),
    ("reviewed", "int"),
    ("official", "int"),
    ("native_reviewed", "int"),
)

#: Locale identity comes from the database's own ``locales`` table, not from
#: ``languages.json``. The two disagree on five of 51 tags -- the registry says
#: ``mn`` / ``no`` / ``sr`` / ``uz`` / ``zh`` where the canon rows say
#: ``mn-Cyrl`` / ``nb`` / ``sr-Cyrl`` / ``uz-Latn`` / ``zh-Hans`` -- and
#: ``no`` -> ``nb`` is a different language subtag rather than a stripped
#: script, so no mechanical rule reconciles them. The ``locales`` table is
#: keyed by the same tag ``canon_selections`` is, which makes the join exact
#: and needs no exception list.
LOCALES_SQL = """
SELECT tag, name, native_name, direction
FROM locales
WHERE tag IN ({placeholders})
ORDER BY tag
"""

#: The only files a push may upload. A stray bystander in the output directory
#: -- scratch notes, a copied translations_v2.db carrying
#: ``contributor_identities``, an editor swap file -- must never ride into the
#: dataset repo, where it would survive the later public flip.
PUSH_ALLOW_PATTERNS: tuple[str, ...] = (
    "README.md",
    "reconciliation.json",
    "data/*.parquet",
    "assets/*.png",
)


class ExportRefused(SystemExit):
    """Raised when a guard refuses to let the export continue."""


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Open the database read-only, with foreign keys on.

    ``foreign_keys`` is a PER-CONNECTION setting that SQLite defaults to OFF,
    so the schema's DDL-time pragma does not cover us.
    """
    if not db_path.exists():
        raise ExportRefused(f"database not found: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def map_decider_role(raw: str | None) -> str:
    """Map a raw ``decided_by`` value onto the published role vocabulary.

    Resolution order, and the order matters:

    1. An explicit entry in :data:`ROLE_BY_DECIDER`. Process labels come first
       so that ``quality_review`` -- which fits the handle shape but is a
       maintainer pass rather than a person -- cannot be read as a reviewer.
    2. The reviewer-handle SHAPE, which resolves a contributor without naming
       them in this file.
    3. Nothing. An unmapped value is a hard failure.

    Step 3 is the lesson rather than defensive habit. While this export was
    being scoped, a mapping built from the ten most common raw values silently
    dropped a single-row reviewer -- the only Urdu native review in the
    database -- into ``automated``, erasing the one thing the column exists to
    show. The corpus publish ate the same class of bug when an unmapped v1
    ``source`` label sailed through the migrate and shipped the wrong taxonomy.

    A default here is a silent data-loss bug wearing a sensible-looking hat.

    Raises:
        ExportRefused: if ``raw`` has no mapping and no recognised shape.
    """
    if raw is None:
        raise ExportRefused(
            "EXPORT REFUSED: a canon row has decided_by = NULL, which has no "
            "role mapping. Decide what it means and add it to ROLE_BY_DECIDER; "
            "do not let it default."
        )
    if raw in ROLE_BY_DECIDER:
        return ROLE_BY_DECIDER[raw]
    if HANDLE_PATTERN.match(raw):
        return REVIEWER_HANDLE_ROLE
    raise ExportRefused(
        f"EXPORT REFUSED: decided_by {raw!r} has no role mapping and does not "
        "look like a reviewer handle.\nAdd it to ROLE_BY_DECIDER deliberately. "
        "The export will not guess: an unmapped value bucketed into "
        "'automated' is how a contributor disappears from a published dataset."
    )


def build_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Read canon selections, apply the filters, and map roles.

    Returns:
        One dict per published row, in ``PUBLISHED_COLUMNS`` order.
    """
    cursor = conn.execute(CANON_SQL, {"pl_scope": TARGET_PL_SCOPE})
    rows: list[dict[str, Any]] = []
    for record in cursor:
        if record["locale"] in EXCLUDED_LOCALES:
            continue
        rows.append(
            {
                "concept": record["concept"],
                "category": record["category"],
                "locale": record["locale"],
                "option_uid": record["option_uid"],
                "surface_form": record["surface_form"],
                "status": record["status"],
                # SQLite has no bool; the schema constrains this to (0, 1) and
                # the artifact should say so in its type rather than making a
                # consumer guess whether 2 is possible.
                "identity_ok": bool(record["identity_ok"]),
                "decided_by": map_decider_role(record["decided_by"]),
                "decided_at": record["decided_at"],
            }
        )

    # Reconcile against a direct count of the same predicate. CANON_SQL joins
    # `concepts`, and an INNER JOIN drops any canon row whose concept_id has no
    # match -- silently, with no error and no gap in the output. A count that
    # does not reconcile means the artifact is missing decisions it should
    # carry, which is worse than an export that fails.
    marks = ", ".join("?" for _ in EXCLUDED_LOCALES)
    expected = conn.execute(
        f"SELECT count(*) FROM canon_selections WHERE pl_scope = ? "
        f"AND locale NOT IN ({marks})",
        (TARGET_PL_SCOPE, *sorted(EXCLUDED_LOCALES)),
    ).fetchone()[0]
    if len(rows) != expected:
        raise ExportRefused(
            f"EXPORT REFUSED: {expected} canon rows match the filters but only "
            f"{len(rows)} survived the concepts join. {expected - len(rows)} "
            "row(s) reference a concept that does not exist; publishing would "
            "silently omit them."
        )
    return rows


#: How a LANGUAGE's rung is derived from its renderings.
#:
#: The published unit is the language, not the word. A reader wants to know
#: whether Amharic's canon has been through review, not whether one Amharic
#: rendering has, and the per-rendering rung exists to make that answer
#: auditable rather than to be read directly.
#:
#: The rule, top down:
#:
#: * ``official``     -- every rendering is ``official``
#: * ``reviewed``     -- every rendering is ``reviewed`` or better
#: * ``experimental`` -- at least one rendering has had human input
#: * ``machine``      -- none has
#:
#: So ``experimental`` means *in progress* while ``reviewed`` and ``official``
#: mean *complete at that level*. A language does not stop being in progress
#: because its first word was endorsed, and it does not claim review it has
#: only partly had.
#:
#: The machine -> experimental threshold is deliberately "any", not a
#: percentage. Coverage thresholds belong to the review policy, which is still
#: open; asserting one here would invent it. When it lands, this is the single
#: place it changes.
def language_status(counts: dict[str, int]) -> str:
    """Return the rung for one language, given its per-rung rendering counts."""
    total = sum(counts[rung] for rung in LADDER)
    if total and counts["official"] == total:
        return "official"
    if total and counts["official"] + counts["reviewed"] == total:
        return "reviewed"
    if total - counts["machine"] > 0:
        return "experimental"
    return "machine"


def build_locale_rows(
    conn: sqlite3.Connection, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """One row per language: identity, and how far up the ladder it has come.

    The counts are DERIVED from the exported canon rows rather than queried
    separately, so the two configs cannot disagree: a number on the locales
    page is always a count of rows a consumer can see in the canon page.
    """
    locales = sorted({row["locale"] for row in rows})
    placeholders = ", ".join("?" for _ in locales)
    meta = {
        record["tag"]: record
        for record in conn.execute(
            LOCALES_SQL.format(placeholders=placeholders), locales
        )
    }
    missing = [locale for locale in locales if locale not in meta]
    if missing:
        raise ExportRefused(
            f"EXPORT REFUSED: {missing} carry canon decisions but have no row in "
            "the locales table, so the artifact would name a language it cannot "
            "describe."
        )

    tally: dict[str, dict[str, int]] = {
        locale: dict.fromkeys((*LADDER, "decisions", "native_reviewed"), 0)
        for locale in locales
    }
    for row in rows:
        counts = tally[row["locale"]]
        counts["decisions"] += 1
        counts[row["status"]] += 1
        if row["decided_by"] == "native-reviewer":
            counts["native_reviewed"] += 1

    return [
        {
            "locale": locale,
            "language_name": meta[locale]["name"],
            "native_name": meta[locale]["native_name"],
            "status": language_status(tally[locale]),
            "rtl": meta[locale]["direction"] == "rtl",
            "decisions": tally[locale]["decisions"],
            "machine": tally[locale]["machine"],
            "experimental": tally[locale]["experimental"],
            "reviewed": tally[locale]["reviewed"],
            "official": tally[locale]["official"],
            "native_reviewed": tally[locale]["native_reviewed"],
        }
        for locale in locales
    ]


def assert_no_leaked_identifiers(rows: list[dict[str, Any]]) -> None:
    """Refuse to write internal tickets or contributor handles.

    The role mapping already neutralises both in ``decided_by``. This checks
    every string cell in every column, because the promise is about the
    artifact rather than about one column, and a surface form or a concept
    slug is just as public.

    Raises:
        ExportRefused: on the first offending cell.
    """
    for index, row in enumerate(rows):
        for column, value in row.items():
            if not isinstance(value, str):
                continue
            if TICKET_PATTERN.search(value):
                raise ExportRefused(
                    f"EXPORT REFUSED: row {index} column {column!r} carries an "
                    f"internal ticket reference: {value!r}. No published file "
                    "may cite a ticket."
                )
            if column == "decided_by" and value not in PUBLISHED_ROLES:
                raise ExportRefused(
                    f"EXPORT REFUSED: row {index} has decided_by {value!r}, "
                    f"which is not one of {PUBLISHED_ROLES}."
                )
            if HANDLE_PATTERN.match(value):
                raise ExportRefused(
                    f"EXPORT REFUSED: row {index} column {column!r} carries "
                    f"what looks like a contributor handle: {value!r}."
                )


def assert_expected_shape(rows: list[dict[str, Any]]) -> None:
    """Refuse an export whose shape contradicts the release's own claims.

    Raises:
        ExportRefused: on an empty export, an unknown rung, or a locale that
            slipped past :data:`EXCLUDED_LOCALES`.
    """
    if not rows:
        raise ExportRefused(
            "EXPORT REFUSED: zero rows. Either the filters are wrong or the "
            "database is not the one you think it is."
        )
    for row in rows:
        if row["status"] not in LADDER:
            raise ExportRefused(
                f"EXPORT REFUSED: unknown rung {row['status']!r}. The ladder is "
                f"{LADDER}; a new rung is a card change, not a silent one."
            )
        if row["locale"] in EXCLUDED_LOCALES:
            raise ExportRefused(
                f"EXPORT REFUSED: excluded locale {row['locale']!r} survived "
                "the filter."
            )


def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the reconciliation ledger a consumer can recompute from the rows."""
    locales = sorted({row["locale"] for row in rows})
    by_rung: dict[str, int] = {rung: 0 for rung in LADDER}
    by_role: dict[str, int] = {role: 0 for role in PUBLISHED_ROLES}
    by_locale: dict[str, int] = {}
    for row in rows:
        by_rung[row["status"]] += 1
        by_role[row["decided_by"]] += 1
        by_locale[row["locale"]] = by_locale.get(row["locale"], 0) + 1
    return {
        "rows": len(rows),
        "locales": len(locales),
        "concepts": len({row["concept"] for row in rows}),
        "identity_ok": sum(1 for row in rows if row["identity_ok"]),
        "by_rung": by_rung,
        "by_role": by_role,
        "by_locale": by_locale,
        "filters": {
            "pl_scope": TARGET_PL_SCOPE,
            "excluded_locales": sorted(EXCLUDED_LOCALES),
        },
        "withheld_columns": [
            "decision_reason",
            "source_file",
            "source_revision",
            "programming_language",
        ],
    }


def _require_pyarrow() -> tuple[Any, Any]:
    """Import pyarrow lazily so every non-writing path runs without it."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:  # pragma: no cover - environment-dependent
        raise ExportRefused(
            "pyarrow is required to write Parquet. Install it with "
            "`uv pip install pyarrow`."
        ) from None
    return pa, pq


def _arrow_schema(pa: Any, columns: tuple[tuple[str, str], ...]) -> Any:
    """Pin the Arrow schema for one config.

    Inference types each column from the data it happens to hold, so a column
    that is all-NULL or all-False in one export and populated in the next
    would change type between revisions. A consumer's schema should not depend
    on which day they downloaded. This bites hardest on the ``locales`` config,
    where ``reviewed`` and ``official`` are all-zero today and will not stay
    that way.
    """
    kinds = {"string": pa.string(), "bool": pa.bool_(), "int": pa.int64()}
    return pa.schema([(name, kinds[kind]) for name, kind in columns])


#: Each config and the columns it pins.
CONFIGS: dict[str, tuple[tuple[str, str], ...]] = {
    "canon": PUBLISHED_COLUMNS,
    "locales": LOCALE_COLUMNS,
}

#: The only files the export writes into ``data/``.
WRITTEN_DATA_FILES: frozenset[str] = frozenset(
    f"{config}.parquet" for config in CONFIGS
)


def require_clean_data_dir(data_dir: Path) -> None:
    """Refuse to build on top of a directory holding files we did not write.

    ``PUSH_ALLOW_PATTERNS`` uploads ``data/*.parquet``, so a leftover from an
    earlier run -- a differently-named revision, a scratch copy -- would ride
    into the dataset repo beside the real file and survive the public flip.
    Writing ``canon.parquet`` overwrites only itself; it says nothing about
    what else is sitting next to it.

    Raises:
        ExportRefused: if the directory holds anything unexpected.
    """
    if not data_dir.exists():
        return
    strays = sorted(
        entry.name
        for entry in data_dir.iterdir()
        if entry.name not in WRITTEN_DATA_FILES
    )
    if strays:
        raise ExportRefused(
            f"EXPORT REFUSED: {data_dir} holds files this export does not write: "
            f"{strays}. Every *.parquet here is push-eligible, so a leftover "
            "would be published alongside the real one. Remove them or export "
            "to a clean directory."
        )


def write_parquet(out_dir: Path, config: str, rows: list[dict[str, Any]]) -> Path:
    """Write ``data/<config>.parquet`` against that config's pinned schema."""
    pa, pq = _require_pyarrow()
    data_dir = out_dir / "data"
    require_clean_data_dir(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    spec = CONFIGS[config]
    columns = {name: [row[name] for row in rows] for name, _ in spec}
    table = pa.table(columns, schema=_arrow_schema(pa, spec))
    path = data_dir / f"{config}.parquet"
    pq.write_table(table, path)
    return path


#: The card banner. Lives in the repo and is copied into the export, because
#: the card links it RELATIVELY -- a card whose image resolves only inside the
#: monorepo renders broken on the Hub, which is the one place it is read.
CARD_IMAGE_SOURCE = _I18N_ROOT / "assets" / "language-canon-card.png"
CARD_IMAGE_TARGET = Path("assets") / "language-canon-card.png"


def require_card_image() -> None:
    """Refuse to export without the banner the card links.

    Raises:
        ExportRefused: if the source image is missing.
    """
    if not CARD_IMAGE_SOURCE.is_file():
        raise ExportRefused(
            f"EXPORT REFUSED: the card banner is missing at {CARD_IMAGE_SOURCE}. "
            "The card links it relatively, so exporting without it publishes a "
            "page with a broken image at the top."
        )


def copy_card_image(out_dir: Path) -> None:
    """Copy the banner into the export, refusing any bystander beside it.

    Everything under ``assets/`` is push-eligible, so a stray image left in the
    output directory would publish alongside the real one.

    Raises:
        ExportRefused: if another image is already sitting there.
    """
    assets_dir = out_dir / CARD_IMAGE_TARGET.parent
    assets_dir.mkdir(parents=True, exist_ok=True)
    bystanders = sorted(
        path.name
        for path in assets_dir.iterdir()
        if path.name != CARD_IMAGE_TARGET.name
    )
    if bystanders:
        raise ExportRefused(
            f"EXPORT REFUSED: {assets_dir} holds files this export does not "
            f"write: {bystanders}. Everything under assets/ is published."
        )
    shutil.copyfile(CARD_IMAGE_SOURCE, out_dir / CARD_IMAGE_TARGET)


def render_card(
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    locale_rows: list[dict[str, Any]],
) -> str:
    """Render the dataset card.

    Follows the corpus card's flow -- what it is, languages, the substance,
    configs, licence -- so a reader moving between the two Legesher datasets
    finds the same shape rather than relearning where things are.

    Every count is taken from the exported rows rather than asserted, so the
    headline numbers are reproducible from what a consumer downloads.
    """
    locales = sorted(summary["by_locale"])
    lang_yaml = "\n".join(
        f"  - {subtag}"
        for subtag in sorted({locale.split("-")[0] for locale in locales})
    )
    language_rows = "\n".join(
        f"| `{row['locale']}` | {row['language_name']} | {row['native_name']} "
        f"| `{row['status']}` |"
        for row in locale_rows
    )
    by_status = {rung: 0 for rung in LADDER}
    for row in locale_rows:
        by_status[row["status"]] += 1
    status_summary = ", ".join(
        f"**{by_status[rung]}** at `{rung}`" for rung in LADDER if by_status[rung]
    )
    # Counted from the RUNG, not the role: a rendering the machine picked and a
    # person later endorsed is human-touched, and its role is still
    # `automated`. Reading the role here would report 32 where the truth is
    # hundreds, which is the exact erasure this rung correction fixed.
    human_touched = summary["by_rung"]["experimental"]
    human_locales = sum(1 for row in locale_rows if row["experimental"])
    return f"""---
license: {DECLARED_LICENSE}
tags:
  - multilingual
  - code
  - programming
  - localization
  - terminology
pretty_name: Legesher Language Canon
language:
{lang_yaml}
configs:
  - config_name: canon
    data_files:
      - split: train
        path: data/canon.parquet
  - config_name: locales
    data_files:
      - split: train
        path: data/locales.parquet
---

# Legesher language canon

![Legesher Language Canon]({CARD_IMAGE_TARGET.as_posix()})

## What this Canon is

A **centralized standard, created and curated by language communities**, for what
programming concepts are called in each natural language.

It holds language-specific renderings of programming keywords, builtins and
exceptions, and documents where each language stands in that process.

The language-canon builds on
[`legesher/language-corpus`](https://huggingface.co/datasets/legesher/language-corpus),
which gathers every rendering anyone has proposed. The corpus is the full
record of what has been suggested; the canon is the vocabulary that downstream
applications actually use.

Computer science as a global discipline is primarily based in English. A
developer who does not read English memorizes shapes rather than reading words
and connecting the terminology to related context. The hard part is not the
obvious vocabulary. It is the gray areas, where words are borrowed, created, or
derived from English (`elif` and `lambda` have no obvious answer in any
language), and settling them takes people who know a language's culture and the
stories woven into it, not only its grammar.

_Note: This is a **growing dataset**. A rendering here is the current answer,
not a final one, and each carries a rung recording how much review stands
behind it._

Renderings are keyed by content-addressed uids (`opt_` + 24 hex) shared with
the corpus, so an `option_uid` resolves there to every alternative proposed for
that concept and every endorsement attached to them.

## Languages

All {summary["locales"]} languages in this export, with where each one stands
on the maturity ladder. The primary-subtag rollup in the frontmatter is what
the Hub indexes for search; this is the full list, script subtags and all.

| Tag | Language | Native name | Status |
| --- | --- | --- | --- |
{language_rows}

Today: {status_summary}.

The `locales` config carries the same list with the counts behind each status,
so you can sort and filter it rather than read it.

## The maturity ladder

Without other global examples to build from, each language's canon starts
drafted from machines and prior art. From there native speakers move it up:
`experimental`, then `reviewed`, then `official`. Once a language reaches
`official`, its canon becomes a resource for the community it exists to serve.

**The rung belongs to the language.** Each rendering carries its own so the
label stays auditable, but what you should read is the language's status: a
language is `experimental` while it is in progress, and `reviewed` or
`official` only once every one of its words has got there.

### `machine`

Drafted, not decided. The vocabulary came from a machine draft or from prior
art, and nobody has weighed in on any of it yet.

It is not arbitrary. Every rendering clears mechanical checks before it can be
selected: it has to be a valid identifier in its language, stable under the
Unicode normalization the interpreter applies, and free of collisions with
other terms in its vocabulary. What nobody has asked is whether it is the right
word — whether a programmer who speaks the language would recognise it.

Treat the whole vocabulary as a proposal.

### `experimental`

Review has begun. At least one word has been chosen or endorsed by a person —
a maintainer curating a batch, a native speaker correcting a term, or a
contributor putting their name behind a rendering someone else proposed.

Most of the endorsements here predate this dataset: they are the review history
of the community that built Legesher's original translations, where
contributors voted on renderings word by word. An endorsement attaches to the
specific option that was later selected, so it is evidence about *this word*,
not about the concept in general.

A language stays here for as long as the work is under way, however far along
it is. The `locales` config carries the counts if you want to know how far.

### `reviewed`

Every word has been signed off by several native speakers, so the vocabulary
reflects agreement rather than one person's preference.

The risk with a single reviewer is not that they are wrong. It is that they are
unrepresentative — a regional form, a register that reads formal or childish
elsewhere, a loanword one community has absorbed and another rejects. More than
one voice is what makes a vocabulary a shared answer.

How many voices, and how varied, is still being defined. We would rather say so
than publish a threshold we have not set.

### `official`

Ratified in a convened session, and screened.

Screening is separate from accuracy. A rendering can be a correct translation
and still be the wrong word to ship: offensive in another register, unfortunate
beside a neighbouring term, or colliding with something it should not. A status
of `official` means both questions were asked of the whole vocabulary and
answered by people with standing to answer them.

A language community makes this decision, not a threshold.

### Where things stand today

{status_summary}.

Review has begun in {human_locales} languages, covering {human_touched:,} of
{summary["rows"]:,} renderings. No language has reached `reviewed`: that needs
every word signed off by more than one native speaker, and the threshold for
how many voices is still being defined.

We publish at this stage deliberately. A terminology set developed privately
and released once it is "ready" has already made every decision without the
people it is for. Publishing early makes the current state visible, citable
and arguable, while it is still genuinely open.

A language's status here describes its canon. It is not the same as the tier
of the language pack that ships from it.

## Configs

Two, joined on `locale`.

**`canon`** — one row per decision.

| Column | Meaning |
| --- | --- |
| `concept` | Language-neutral concept slug — what the construct *does* |
| `category` | Concept category: control flow, declaration, error handling, … |
| `locale` | BCP 47 language tag |
| `option_uid` | Content-addressed id of the chosen rendering; joins to the corpus |
| `surface_form` | The word itself |
| `status` | Rung on the maturity ladder |
| `identity_ok` | The rendering matches the English term **on purpose** |
| `decided_by` | Role that made the selection |
| `decided_at` | When the selection was made |

`identity_ok` marks a deliberate cognate or loanword — `stopiteration` in
Danish, `Lambda` in German. It does not mean "not translated yet"; without it
a reader could not tell a considered borrowing from an oversight.

**`locales`** — one row per language: `locale`, `language_name`,
`native_name`, `rtl`, `decisions`, a count at each rung, and
`native_reviewed`. Language attributes live only here, so a language is
described in exactly one place.

## Who decides, and how to take part

`decided_by` records the **role** that made a selection, never the person:
`automated` for migrations and batch jobs, `maintainer` for curation,
`native-reviewer` for a speaker of the language. Contributor identities are
not published in this dataset. Endorsements, attribution and withdrawal are
handled through
[`legesher/language-corpus`](https://huggingface.co/datasets/legesher/language-corpus),
which is the artifact that carries them.

The role answers a different question from the rung, and the two are
deliberately independent: `status` says **how much** review stands behind a
rendering, `decided_by` says **who** made the most recent call. A single
native reviewer is visible here without moving the rung, because their
judgement is real and is not yet a consensus.

This requires collaboration from people who do not just speak a language other
than English, but know its culture. If that is you, corrections, endorsements
and objections all move a rendering up the ladder, and disagreement is a
contribution rather than an obstacle.

## Licence and citation

Released under **Apache-2.0**. Legesher holds the compilation right in this
dataset and licenses it on those terms; the individual renderings arrive from
the corpus, whose own licence and attribution notices govern the contributed
parts.

```bibtex
@misc{{legesher_language_canon,
  title  = {{Legesher Language Canon}},
  author = {{Legesher}},
  year   = {{2026}},
  howpublished = {{\\url{{https://huggingface.co/datasets/{DEFAULT_TARGET_REPO}}}}}
}}
```
"""


def require_push_approval(governance_signoff: str | None) -> None:
    """Refuse to push without the governance sign-off AND the env approval.

    Runs BEFORE the export writes anything and BEFORE any network library is
    imported.

    Raises:
        ExportRefused: unless both keys are turned.
    """
    if governance_signoff != GOVERNANCE_TICKET:
        raise ExportRefused(
            f"--push requires --governance-signoff {GOVERNANCE_TICKET}. "
            "Publishing terminology under a community's name is a governance "
            "decision, not a scripting one."
        )
    if os.environ.get(PUSH_ENV_VAR) != "1":
        raise ExportRefused(
            f"--push requires {PUSH_ENV_VAR}=1 in the environment. The flag and "
            "the variable are deliberately two separate keys: a command-line "
            "typo must not be able to publish."
        )


def require_intended_target(target_repo: str) -> None:
    """Refuse to push anywhere but the canonical repo without a second key.

    Raises:
        ExportRefused: if the target is non-default and not repeated in
            :data:`TARGET_OVERRIDE_ENV_VAR`.
    """
    if target_repo == DEFAULT_TARGET_REPO:
        return
    if os.environ.get(TARGET_OVERRIDE_ENV_VAR) != target_repo:
        raise ExportRefused(
            f"PUSH REFUSED: --target-repo {target_repo!r} is not the canonical "
            f"{DEFAULT_TARGET_REPO!r}. A non-default destination must be "
            f"repeated verbatim in {TARGET_OVERRIDE_ENV_VAR} -- a typo must not "
            "be able to publish to the wrong namespace."
        )


def _require_hf_api() -> Any:
    """Import huggingface_hub lazily and return the ``HfApi`` class."""
    try:
        from huggingface_hub import HfApi
    except ImportError:  # pragma: no cover - environment-dependent
        raise ExportRefused(
            "huggingface_hub is required to push. Install it with "
            "`uv pip install huggingface_hub`, then `hf auth login`."
        ) from None
    return HfApi


def preflight_hub_auth() -> None:
    """Fail a push on missing Hub auth BEFORE the export runs.

    Without a preflight an unauthenticated run does all the export work and
    then dies mid-upload, leaving a fully-built artifact behind as if it were
    push-ready.

    Raises:
        ExportRefused: if the library is missing or the token is absent/bad.
    """
    hf_api = _require_hf_api()
    try:
        who = hf_api().whoami()
    except Exception as error:  # hub raises several exception types here
        raise ExportRefused(
            f"PUSH REFUSED: not authenticated to the Hugging Face Hub ({error}). "
            "Run `hf auth login` or set HF_TOKEN, then re-run."
        ) from None
    print(f"Hub auth ok: {who.get('name', '?')}")


def push_to_hub(out_dir: Path, target_repo: str) -> None:
    """Upload the exported canon to the Hugging Face Hub.

    Private-first, and this tool NEVER changes visibility. Going public is a
    separate deliberate action on the Hub, so no invocation of this script can
    accidentally publish. Note that ``private`` and ``gated`` are independent
    flags and a gated failure is invisible to a signed-in maintainer: verify a
    publish anonymously, never from the pushing session.
    """
    api = _require_hf_api()()
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
        allow_patterns=list(PUSH_ALLOW_PATTERNS),
        # A dataset repo's commit history is as public as its files, so the
        # message obeys the same rule they do: no internal ticket.
        commit_message="canon export",
    )
    print(f"Pushed {out_dir} -> {target_repo}")


def export_canon(db_path: Path, out_dir: Path) -> dict[str, Any]:
    """Build the canon artifact into ``out_dir``. Returns the ledger."""
    conn = connect_readonly(db_path)
    try:
        rows = build_rows(conn)
        assert_expected_shape(rows)
        assert_no_leaked_identifiers(rows)
        locale_rows = build_locale_rows(conn, rows)
    finally:
        conn.close()

    require_card_image()
    summary = summarise(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_parquet(out_dir, "canon", rows)
    write_parquet(out_dir, "locales", locale_rows)
    (out_dir / "README.md").write_text(
        render_card(summary, rows, locale_rows), encoding="utf-8"
    )
    (out_dir / "reconciliation.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    copy_card_image(out_dir)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--db",
        type=Path,
        default=_I18N_ROOT / "build" / "translations_v2.db",
        help="v2 database to read (opened read-only)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_I18N_ROOT / "build" / "hf-canon",
        help="export directory",
    )
    parser.add_argument("--push", action="store_true", help="upload to the Hub")
    parser.add_argument("--target-repo", default=DEFAULT_TARGET_REPO)
    parser.add_argument("--governance-signoff")
    args = parser.parse_args(argv)

    # Every push gate runs BEFORE the export writes a byte.
    if args.push:
        require_push_approval(args.governance_signoff)
        require_intended_target(args.target_repo)
        require_card_image()
        preflight_hub_auth()

    summary = export_canon(args.db, args.out)
    print(
        f"canon: {summary['rows']:,} rows, {summary['locales']} locales, "
        f"{summary['concepts']} concepts -> {args.out}"
    )
    for rung, count in summary["by_rung"].items():
        if count:
            print(f"  {rung:>13}: {count:,}")
    for role, count in summary["by_role"].items():
        if count:
            print(f"  {role:>13}: {count:,}")

    if args.push:
        push_to_hub(args.out, args.target_repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
