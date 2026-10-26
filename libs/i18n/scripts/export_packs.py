#!/usr/bin/env python3
"""Export the shipped language packs as a pinned Hugging Face dataset (CORE-1043).

This is the CANON artifact: the words Legesher actually ships. Its counterpart,
``legesher/language-corpus`` (``export_corpus.py``), is the EVIDENCE layer --
every rendering anyone proposed, append-only, with endorsements attached. The
three answer different questions and must never be conflated:

* corpus -- "what did people offer, and who backed it?"  (researcher-facing)
* canon  -- "which rendering was chosen, and how reviewed is it?"
* packs  -- "what does `import legesher` actually give me?" (developer-facing)

``canon`` here means ``legesher/language-canon``, a separate dataset since
2026-08-19. Before that it was a second name for THIS artifact, which is why
older references to "the canon dataset" mean the packs.

The source is the YAML PACK TREE, never ``canon_selections`` (CORE-1913)
-------------------------------------------------------------------------
``canon_selections`` carries selections for targets other than Python -- 62
Arabic JavaScript rows, where ``programming_language`` is a real populated
column. Exporting from it would publish unreviewed Arabic JavaScript
terminology *labeled by target*, asserting a level of review that population
has not had (CORE-1913).

The pack tree cannot carry them: ``yaml_exporter.py`` drops every selection
whose ``programming_language`` is not NULL or ``python`` before a pack is
written, and Arabic is the only locale with JavaScript selections at all. So
this script reads the pack tree and nothing else for vocabulary, and
:func:`assert_python_only` re-proves that property on the way out rather than
trusting it. Belt (we never read the DB) and suspenders (the rows prove it).

The registry (``languages.json``) is read for locale metadata and the tier
stamp only -- names, script direction, and ``status``. It contributes no
vocabulary.

What "regenerable from the tag" means here
------------------------------------------
Every input is a tracked file, so a checkout of the same commit reproduces the
same rows. The JSON outputs and the manifest are byte-identical across
machines; Parquet embeds a ``created_by`` string naming the writer version, so
Parquet bytes are reproducible for a PINNED TOOLCHAIN, which the manifest
records. The manifest therefore carries a checksum per output file AND the
toolchain that produced it -- a claim a consumer can actually check, rather
than an unqualified "byte-identical" that quietly depends on a pyarrow
version.

Inheritance is resolved through the real loader
-----------------------------------------------
Packs for 3.11+ carry only a delta and ``extends:`` their base. A consumer
asking "what is `for` in Spanish on 3.12?" wants the RESOLVED answer, so each
(locale, version) is materialised through :class:`LanguagePackLoader` -- the same code
path the runtime uses -- rather than by re-implementing the merge here. Each row
records the version whose pack file supplied its value, so the delta structure
survives the flattening instead of being erased by it.

Nothing written here may cite an internal ticket. These files are read by
people outside the project, to whom a bare ``CORE-####`` is an unresolvable
reference; the test suite asserts it over every file the export writes, and
over the card branches this data does not currently render. The same rule
governs the Hub commit message, and a test now holds it (it used to be carried
by the runbook, because this artifact was pushed by hand).

Usage:
    uv run python scripts/export_packs.py --out build/hf-packs
    uv run python scripts/export_packs.py --out build/hf-packs --verify-deterministic
    uv run python scripts/export_packs.py --out build/hf-packs --push \\
        --governance-signoff CORE-1502

Pushing is gated, not free (CORE-2017)
--------------------------------------
This script pushed nothing until 2026-08-24, on the reasoning that publishing
is a governance act belonging to the release ticket rather than to a script
flag. That reasoning was right about the act and wrong about the mechanism: a
hand-push has no gates at all, and the consequence was a published artifact
that sat three revisions behind this file with nothing to notice. The rule the
runbook asked an operator to remember is now a set of refusals, matching
``export_canon.py`` and ``export_corpus.py``. Every one of them runs BEFORE the
export writes a byte, so a refused run leaves nothing on disk that could be
mistaken for push-ready:

* ``--governance-signoff`` and ``LEGESHER_HF_PUSH_APPROVED=1`` -- two separate
  keys, so a command-line typo cannot publish
* a non-default ``--target-repo`` repeated verbatim in the environment
* a clean worktree, because a pinned revision built over uncommitted changes
  cannot be reproduced from the commit its manifest names
* the ``language-packs-v<DATASET_VERSION>`` tag on that commit -- the one
  version string the Hub revision, the release ticket and the card share.
  Checked against the exact tag, not merely "is there a tag" or "does one start
  with the prefix": this repo tags releases ``v0.24.0`` and packs
  ``i18n-python-ar-v0.0.4``, neither of which names a revision of this dataset,
  and a stale ``language-packs-v*`` tag would let a build publish under a
  version it does not declare
* agreement between the declared compilation license and the packs' own
  ``metadata.license``, because both claims become public in the same revision
* Hub auth

Then ``--verify-deterministic`` turns itself on, and the push runs only after
it passes: a revision that does not reproduce is not one to pin consumers
against.

Visibility is NOT one of them. ``push_to_hub`` creates private and never
changes visibility, so no invocation of this script can publish a private
dataset -- going public stays a deliberate act on the Hub.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_I18N_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_I18N_ROOT))

from legesher_i18n.messages import _parse_version  # noqa: E402
from legesher_i18n.pack_loader import LanguagePackLoader  # noqa: E402
from legesher_i18n.term_definitions import (  # noqa: E402
    YAML_SECTION_CATEGORIES,
    classify_term,
)
from legesher_i18n.vocabulary_definitions import (  # noqa: E402
    VOCABULARY_SECTIONS,
    english_values,
    inventory_for_section,
)

PACKS_DIR = _I18N_ROOT / "language-packs" / "python"
REGISTRY = _I18N_ROOT / "legesher_i18n" / "languages.json"

#: Where a push goes unless a second key says otherwise.
DEFAULT_TARGET_REPO = "legesher/language-packs"

#: The card's banner image: source path in this repo, and the path it is
#: published at inside the dataset repo (the ``![](...)`` target in the card).
#: The card references it relatively, so the file has to ride along in the
#: export directory AND in :data:`PUSH_ALLOW_PATTERNS`. Same shape as the
#: corpus and canon banners, 1200x630.
CARD_IMAGE_SOURCE = (
    Path(__file__).resolve().parents[1] / "assets" / "language-packs-card.png"
)
CARD_IMAGE_TARGET = Path("assets") / "language-packs-card.png"

#: What the manifest records when ``git describe`` finds no tag on the commit.
UNTAGGED = "(untagged)"

#: This dataset's own version, and the single source of truth for it: the tag
#: a push demands, the version the card states, and the number the manifest
#: records all read it from here.
#:
#: Semantic, not date-based (2026-08-28). Every other tag family in this repo
#: is semver -- the monorepo ``v0.24.0``, ``vscode-v0.1.5``, the per-pack
#: ``i18n-python-ar-v0.0.4`` -- and this artifact was the lone exception.
#:
#: What each part means HERE, since a dataset is not a library:
#:
#: * major -- reserved. Below 1.0 it does not move at all
#: * minor -- new locales, new terms, a new interpreter version, a renamed
#:   column or category value, or a rewrite of the card's published prose.
#:   Below 1.0 this is where breaking changes land, which is the semver
#:   convention for 0.x and the reason 0.2.0 follows 0.1.0 rather than 1.0.0
#: * patch -- corrections to renderings this release already carried, or to
#:   the card's prose where no data file changes. 0.4.1 is the second kind:
#:   every one of the 56 hashed files was byte-identical to 0.4.0
#:
#: 0.5.0 is the minor kind: five new locales (uk, sw, ne, tl, xh) take the
#: dataset from 51 to 56, every row they add is new, and no existing row
#: changes. The schema is the one 0.4.0 froze.
#:
#: Deliberately NOT aligned to ``legesher-i18n``'s version, though the two look
#: like one product. That number tracks the library, and the pack data ships in
#: separately versioned distributions: aligning would move this version when
#: the content had not changed, and hold it still when it had. The linkage is
#: recorded instead -- see ``legesher_i18n`` in the manifest's toolchain block.
#:
#: Started at 0.1.0 rather than 1.0.0 because every locale is stamped
#: ``experimental`` with no native-speaker sign-off, and the schema is still
#: moving. A 0.x says usable-not-settled, which is what the card says in prose.
DATASET_VERSION = "0.5.0"

#: Tag shape a published revision is expected to carry, e.g.
#: ``language-packs-v0.1.0``. The one version string the Hub revision, the
#: release ticket and the card all say out loud.
TAG_PREFIX = "language-packs-v"

#: The exact tag a push demands. Prefix-plus-version rather than "some tag
#: starting with the prefix": the gate exists so a revision cannot claim a
#: version it does not have, and any-tag-with-the-prefix leaves exactly that
#: hole open.
RELEASE_TAG = f"{TAG_PREFIX}{DATASET_VERSION}"

#: The governance decision a push asserts has been taken. Shared verbatim with
#: ``export_canon.py`` and ``export_corpus.py``: one key turns all three, so a
#: maintainer does not have to remember which artifact wants which ticket.
GOVERNANCE_TICKET = "CORE-1502"

#: Second key for the sign-off, and second key for a non-default destination.
PUSH_ENV_VAR = "LEGESHER_HF_PUSH_APPROVED"
TARGET_OVERRIDE_ENV_VAR = "LEGESHER_HF_TARGET_OVERRIDE"

#: Exactly what an upload may carry. An allow-list rather than the whole
#: directory, because ``--out`` is an ordinary directory a maintainer can put
#: anything in: an editor swap file, a stray notebook, a `.DS_Store`. The
#: export rebuilds ``--out`` from scratch, but that says nothing about what a
#: later hand lands beside it before the push.
PUSH_ALLOW_PATTERNS: tuple[str, ...] = (
    "README.md",
    "manifest.json",
    "data/*.parquet",
    "json/*/*.json",
    # The card links its banner relatively, so the image has to be uploaded
    # with it or the dataset page shows a broken image.
    "assets/*.png",
)

#: Published columns, per config (CORE-1986, reshaped by CORE-2022). The row
#: dicts built in memory carry more than this on purpose -- the card and the
#: assertions read the fuller dicts -- so the published schema is a projection
#: applied at write time. Four configs, each answering one question:
#:
#: * ``locales`` -- who is this natural language?
#: * ``pl_terminology`` -- what does the programming language reserve, and on
#:   which of its versions?
#: * ``vocabulary`` -- what is it called in this natural language?
#: * ``packs`` -- how far along is this (natural language x target) pairing?
#:
#: ``category`` stays in the vocabulary key: ``type`` is rendered once as a
#: keyword and once as a builtin, and collapsing the key to (locale, target,
#: pl_version, source_term) would conflate two renderings that may differ.
#: ``target`` is a key column even while it is constant, because the join into
#: ``pl_terminology`` spans targets the moment a second one ships.
#:
#: There was an ``inherited`` boolean here until 0.3.0. It was not a fact about
#: the row; it was ``defined_at != pl_version`` restated, true on all 46,512
#: rows and false on none, and nothing outside this script ever read it. A
#: column a consumer can compute from the two beside it is a column that can
#: disagree with them.
#:
#: Rows stay RESOLVED -- one per (locale, target, version, category, term) --
#: and that is a decision, not an oversight. 79.8% of them repeat a rendering
#: their neighbour already carries, because only 18 of 9,384 keys render
#: differently across versions at all, so a delta form would be 4.9x smaller.
#: The multiplication buys the thing this config exists for: ``pl_version ==
#: '3.12'`` answers "what do I get on 3.12" with no join and no window
#: function. The parquet is the queryable form and the JSON is the loadable
#: one (CORE-2020), and 46,512 rows is a ratio, not a size problem.
VOCABULARY_COLUMNS: tuple[str, ...] = (
    "locale",
    "target",
    "pl_version",
    "category",
    "source_term",
    "translation",
    "defined_at",
)

#: Pure natural-language identity. ``tier`` and ``package_version`` moved to
#: ``packs`` (CORE-2022): both are properties of a (locale x target) pairing,
#: not of the language -- the moment a second target ships, Arabic-Python and
#: Arabic-JavaScript stop sharing either value.
LOCALE_COLUMNS: tuple[str, ...] = (
    "locale",
    "language_name",
    "native_name",
    "iso639_2",
    "bcp47",
    "rtl",
    "has_case_distinction",
)

#: The programming language's own terminology: one row per (target, category,
#: source_term), carrying the set of the target's versions the term is valid
#: for. No natural language appears in this config. ``subcategory`` is the
#: finer semantic kind (``keyword`` / ``builtin_func`` / ``builtin_type`` /
#: ``special_constant`` / ``exception`` / ``implicit_param``) from
#: ``term_definitions.py`` for term rows, and the message cluster for
#: ``messages`` rows. ``source_text`` is the English surface when the key is
#: not itself the text: a symbol's English name, a message's template.
PL_TERMINOLOGY_COLUMNS: tuple[str, ...] = (
    "target",
    "category",
    "subcategory",
    "source_term",
    "source_text",
    "glyph",
    "pl_versions",
)

#: The shipping unit and its state: one row per (locale, target) pairing.
#: ``package_version`` is the semver of that pairing's own distributable, so a
#: reader can line a Hub revision up against PyPI without guessing; ``tier`` is
#: the maturity of exactly this pairing.
PACKS_COLUMNS: tuple[str, ...] = (
    "locale",
    "target",
    "package_version",
    "tier",
    "pl_versions",
)

#: Interpreter versions each locale ships a pack for. Mirrors
#: ``verify_pack_regen.EXPECTED_VERSIONS``; the two must agree or the dataset
#: would claim a matrix the regen gate does not certify.
VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")

#: Pack sections, in the order a reader meets them. ``members`` is deliberately
#: absent: it is the MLCP partition for member-bearing targets such as
#: JavaScript (CORE-1372) and is empty for every Python pack. Exporting an
#: always-empty column would advertise a surface this artifact does not cover.
SECTIONS = ("keywords", "builtins", "exceptions", "implicit_params")

#: Every category family ``pl_terminology`` publishes, in the order a reader
#: meets them: the four translation sections, then the two vocabulary sections
#: (CORE-1396), then the error-message templates (CORE-1679). The vocabulary
#: sections and messages have no per-locale rows in ``vocabulary`` yet -- the
#: pack files do not carry the sections, and message translations are
#: publish-gated -- but the source-side inventory is target truth and ships
#: now, which is what makes the gap measurable instead of invisible.
CATEGORY_FAMILIES: tuple[str, ...] = (
    *SECTIONS,
    # Splatted from the canonical inventory, not spelled out: a section
    # registered in vocabulary_definitions.py must surface here (and fail the
    # blurb check) rather than silently missing from the config whose point
    # is making gaps measurable.
    *VOCABULARY_SECTIONS,
    "messages",
)

#: One line per category, for the card. Keyed by :data:`CATEGORY_FAMILIES` so a
#: partition added later cannot reach the card undescribed -- the render raises
#: rather than printing a bare name a reader cannot interpret.
#:
#: Each line says what the category holds and nothing else. The subcategories
#: and the term count beside it on the card are counted off the emitted rows,
#: so no figure lives here to go stale.
CATEGORY_BLURBS: dict[str, str] = {
    "keywords": (
        "The words the grammar reserves. A rendering cannot collide with "
        "anything else in the vocabulary. All are legal identifiers except "
        "`except*`, whose renderings carry the marker through."
    ),
    "builtins": (
        "Functions, types and constants available without importing anything: "
        "`print`, `dict`, `Ellipsis`."
    ),
    "exceptions": ("The error hierarchy, from `BaseException` down."),
    # Two entries, `self` and `cls`. Neither is reserved by the Python
    # grammar, which the section name says and this line corrects; the name
    # itself is CORE-2060.
    "implicit_params": (
        "`self` and `cls`. Conventional parameter names that Legesher treats "
        "deterministically, not words the grammar reserves."
    ),
    "symbols": (
        "What a symbol is called: `_` is *underscore* in English. Prose names, "
        "not identifiers."
    ),
    "variable_conventions": (
        "The idiomatic short name for a variable role: the loop counter, the "
        "throwaway, the accumulator."
    ),
    "messages": (
        "Error-message templates with named `{placeholders}`, and the "
        "traceback scaffolding that frames them."
    ),
}


def category_table(term_rows: list[dict[str, Any]]) -> str:
    """The card's category table, counted off the emitted terminology rows.

    Three columns are derived rather than written: the subcategories present,
    how many source terms the category carries, and nothing at all where a
    category has no subcategory. Writing any of them by hand is how a card
    outlives the data it describes.

    ``symbols`` and ``variable_conventions`` carry no subcategory -- they never
    pass through ``classify_term`` -- so their cell is an em-rule, not an
    invented kind. The table is deliberately not uniform, because the data is
    not.
    """
    per_category: dict[str, int] = {}
    subs: dict[str, set[str]] = {}
    for row in term_rows:
        family = row["category"]
        per_category[family] = per_category.get(family, 0) + 1
        if row.get("subcategory"):
            subs.setdefault(family, set()).add(row["subcategory"])

    lines = []
    for name in CATEGORY_FAMILIES:
        found = sorted(subs.get(name, ()))
        # Twenty message families listed in full would be a paragraph inside a
        # cell. The count is the useful fact there; the values ship in the
        # `subcategory` column for anyone who wants them.
        if name == "messages":
            kinds = f"{len(found)} message families"
        elif found:
            kinds = ", ".join(f"`{kind}`" for kind in found)
        else:
            kinds = "--"
        lines.append(
            f"| `{name}` | {kinds} | {per_category.get(name, 0)} "
            f"| {CATEGORY_BLURBS[name]} |"
        )
    return "\n".join(lines)


#: The only target this artifact covers. Asserted against every emitted row.
TARGET = "python"

#: The tracked catalog the ``messages`` category is built from (CORE-1679).
#: The seed file, not the database: the database is untracked (CORE-1794) and
#: an export input that is not a tracked file breaks "regenerable from the
#: tag". Only the English side is read -- the seed also carries ar/es
#: translations, and those stay out of ``vocabulary`` until the
#: content-addressed-key gate (CORE-1565) clears.
MESSAGES_SEED = _I18N_ROOT / "legesher_i18n" / "db" / "seeds" / "cpython_messages.json"

#: SPDX identifier declared for the published compilation. Matches the monorepo
#: LICENSE, ``libs/i18n/pyproject.toml``, every per-pack ``pyproject.toml``
#: files, and — since CORE-1043 — every pack's own ``metadata.license``.
#:
#: The in-pack field said ``MIT`` on all 255 files until then, contradicting the
#: distribution that shipped them. :func:`check_license_consistency` keeps the
#: two claims from drifting apart again: both are public, and a card asserting
#: one license over rows asserting another is not a discrepancy anyone should
#: find after the fact.
DECLARED_LICENSE = "apache-2.0"


def git_describe(repo: Path) -> dict[str, str]:
    """Return the source commit and tag, or explicit unknowns.

    Recorded in the manifest so a published revision names the tree it came
    from. A dirty tree is reported as such rather than silently pinned to the
    last commit -- a revision that cannot be reproduced from the named commit
    must say so.

    "git failed" and "tree is clean" must not collapse into the same answer.
    Both make ``git status --porcelain`` return no output, and the runbook
    treats ``clean`` as a precondition for publishing, so an export run outside
    a repository would otherwise certify itself.
    """

    def run(*args: str) -> tuple[bool, str]:
        try:
            out = subprocess.run(
                ["git", *args],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            return True, out.stdout.strip()
        except (subprocess.CalledProcessError, OSError):
            return False, ""

    commit_ok, commit = run("rev-parse", "HEAD")
    status_ok, status = run("status", "--porcelain")

    # `git describe --tags --exact-match` picks ONE tag arbitrarily when the
    # commit carries several, and this repo tags a lot: 49 tags, of which one
    # is a packs release and the rest are `v0.24.0`, `mcp-v0.1.0`,
    # `i18n-python-ar-v0.0.4` and so on. A release commit routinely carries
    # more than one, so asking for "the tag" would stamp whichever git
    # happened to return. Ask for the packs tag by name instead.
    _, points_at = run("tag", "--points-at", "HEAD")
    packs_tags = sorted(
        line.strip()
        for line in points_at.splitlines()
        if line.strip().startswith(TAG_PREFIX)
    )
    tag = packs_tags[-1] if packs_tags else ""

    if not (commit_ok and status_ok):
        worktree = "unknown (git unavailable)"
    else:
        worktree = "dirty" if status else "clean"

    return {
        "commit": commit if commit_ok else "unknown",
        "tag": tag or UNTAGGED,
        "worktree": worktree,
    }


def load_registry() -> dict[str, dict[str, Any]]:
    """Return the language registry keyed by locale code.

    ``languages.json`` is the registry that owns ``rtl``, ``status`` and the
    display names. It is the same source ``verify_pack_regen`` and
    ``audit_collisions`` treat as authoritative, so the dataset's locale set
    cannot disagree with the gate that certifies the packs.
    """
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return dict(data["languages"])


def pack_locales() -> list[str]:
    """Return locale codes that actually ship a pack tree on disk.

    A directory only counts when it carries the ``legesher_i18n_python_<code>``
    subtree, which is what makes it a pack rather than a stray directory --
    the pack tree also holds ``version-index.yml``, a FILE, and a plain
    directory listing counts it as one more locale. It is not one.
    """
    return sorted(
        d.name
        for d in PACKS_DIR.iterdir()
        if d.is_dir() and (d / f"legesher_i18n_python_{d.name}").exists()
    )


def reconcile_locales(registry: dict[str, Any], on_disk: list[str]) -> None:
    """Fail unless the registry and the pack tree name the same locales.

    Either direction is a publish-stopper. A registry locale with no pack is a
    locale the dataset would silently omit; a pack with no registry entry has
    no tier stamp, no display name, and no business being published. The
    ``uk`` stub -- six selection rows in the database, no pack tree, not in the
    registry -- is exactly the row this guard keeps out of a public artifact.
    """
    missing_packs = sorted(set(registry) - set(on_disk))
    unregistered = sorted(set(on_disk) - set(registry))
    if missing_packs or unregistered:
        raise SystemExit(
            "Registry and pack tree disagree, refusing to export.\n"
            f"  in languages.json with no pack tree: {missing_packs or 'none'}\n"
            f"  pack tree with no registry entry:    {unregistered or 'none'}"
        )


def build_rows(locales: list[str], registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Materialise one row per (locale, version, section, source term).

    Each (locale, version) is resolved through :class:`LanguagePackLoader`, so the
    ``translation`` column is the value the runtime would actually use --
    inheritance applied, not the raw delta. ``defined_at`` records the version
    whose pack file supplies the value SEEN ON THIS ROW, so the delta structure
    the pack tree encodes is still legible after flattening: a row inherits
    exactly when ``defined_at`` differs from ``pl_version``.

    A term may be defined more than once in a chain: Sinhala redefines 17 terms
    at 3.13 to their ZWJ conjunct forms (CORE-1318 script tiering), so ``True``
    is one value on 3.10 and a different one from 3.13 on. ``defined_at`` must
    therefore be the LATEST definition at or below the row's version -- taking
    the earliest would label the 3.13 row as coming from 3.10 while displaying
    a value 3.10 does not carry, which is a self-contradicting published row.

    ``enforce_min_interpreter=False`` because this inspects packs without
    running translated code: Sinhala's ZWJ conjuncts need a 3.13+ interpreter,
    and enforcing that here would refuse to export a pack that ships perfectly
    well.
    """
    loader = LanguagePackLoader()
    rows: list[dict[str, Any]] = []

    for locale in locales:
        meta = registry[locale]
        # Raw pack files, to learn where each term is DEFINED. The resolved
        # pack alone cannot say -- that is the information merging destroys.
        # Every version that defines a term is recorded, not just the first.
        defined_in: dict[tuple[str, str], list[str]] = {}
        for version in VERSIONS:
            raw_path = (
                PACKS_DIR
                / locale
                / f"legesher_i18n_python_{locale}"
                / "packs"
                / f"{version}.yml"
            )
            raw = _read_yaml(raw_path)
            for section in (*SECTIONS, *VOCABULARY_SECTIONS):
                for term in raw.get(section) or {}:
                    defined_in.setdefault((section, str(term)), []).append(version)

        def latest_definition(section: str, term: str, upto: str) -> str:
            """Version supplying this term's value at ``upto``.

            VERSIONS is ordered, so "latest at or below" is the last entry of
            the definition list that does not sort after ``upto``.
            """
            limit = VERSIONS.index(upto)
            candidates = [
                v
                for v in defined_in.get((section, term), ())
                if VERSIONS.index(v) <= limit
            ]
            return candidates[-1] if candidates else upto

        for version in VERSIONS:
            pack = loader.load(
                locale,
                target=TARGET,
                version=version,
                enforce_min_interpreter=False,
            )
            # Every family the pack format can carry, not only the term
            # sections: when a pack YAML gains a `symbols:` block, its
            # renderings must reach `vocabulary` -- the alternative is the
            # documented gap silently never closing, with shipped
            # translations excluded from the dataset and nothing reporting
            # it.
            for section in (*SECTIONS, *VOCABULARY_SECTIONS):
                entries: dict[str, str] = getattr(pack, section) or {}
                for term, translation in entries.items():
                    if translation is None:
                        continue
                    term = str(term)
                    origin = latest_definition(section, term, version)
                    rows.append(
                        {
                            "locale": locale,
                            "language_name": meta.get("name"),
                            "native_name": meta.get("native"),
                            "target": TARGET,
                            "pl_version": version,
                            "category": section,
                            "source_term": term,
                            "translation": str(translation),
                            "defined_at": origin,
                            "tier": meta.get("status"),
                            "rtl": bool(meta.get("rtl", False)),
                        }
                    )

    rows.sort(
        key=lambda r: (
            r["locale"],
            r["pl_version"],
            CATEGORY_FAMILIES.index(r["category"]),
            r["source_term"],
        )
    )
    return rows


def _read_yaml(path: Path) -> dict[str, Any]:
    import yaml

    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def build_packs_rows(
    locales: list[str],
    registry: dict[str, Any],
    rows: list[dict[str, Any]],
    package_versions: dict[str, str],
) -> list[dict[str, Any]]:
    """One row per (locale, target) pairing: the shipping unit and its state.

    This is the grain progress lives at. ``tier`` and ``package_version`` were
    per-locale columns while Python was the only target; they are per-pairing
    facts, and this config gives them the key they actually vary on.

    ``pl_versions`` is DERIVED from the pairing's own vocabulary rows, not
    stamped from the module constant: a per-pairing column fed by a
    dataset-global constant is the ``pack_versions`` smell CORE-1986 removed,
    and a pack covering a partial slice becomes representable the day one
    exists. (Today every pairing covers all of :data:`VERSIONS`; the
    exporter's uniformity assertion guarantees it.)
    """
    covered: dict[str, set[str]] = {}
    for row in rows:
        covered.setdefault(row["locale"], set()).add(row["pl_version"])
    # pack_locales() is sorted and target is single, so input order is the
    # published order.
    return [
        {
            "locale": locale,
            "target": TARGET,
            "package_version": package_versions[locale],
            "tier": registry[locale].get("status"),
            "pl_versions": sorted(covered.get(locale, ()), key=VERSIONS.index),
        }
        for locale in locales
    ]


def _subcategory_for(section: str, term: str, earliest: str) -> str:
    """The finer semantic kind of a term, constrained to its section.

    Classified at the EARLIEST version the (section, term) pairing is valid
    for, which is what makes ``type`` come out right twice: at 3.10 it is a
    ``builtin_type`` (its builtins-section row), and at 3.12 -- the earliest
    version of its keywords-section row -- ``classify_term`` calls it a
    ``keyword``. Classifying both rows at one fixed version would mislabel one
    of them.

    Refuses a classification outside the section's allowed kinds rather than
    publishing it: that disagreement means ``term_definitions.py`` and the
    pack tree have drifted, which is an alarm, not a value.
    """
    kind = classify_term(term, earliest)
    allowed = YAML_SECTION_CATEGORIES[section]
    if kind not in allowed:
        raise SystemExit(
            f"pl_terminology: {term!r} in section {section!r} classifies as "
            f"{kind!r}, which the section does not admit ({allowed}). "
            f"term_definitions.py and the pack tree disagree; reconcile "
            f"before publishing a subcategory that misdescribes the term."
        )
    return kind


def _message_pl_versions(added: str, removed: str | None) -> list[str]:
    """The slice of :data:`VERSIONS` a message template is valid on.

    Numeric comparison via the same ``_parse_version`` the runtime catalog
    uses (``messages.load_catalog``), so the published windows and the
    runtime's cannot disagree: a template added at 3.15 is valid on NO
    shipped version, not -- as index-membership semantics would have it --
    on all of them.

    Raises:
        SystemExit: on an unparseable boundary. A window the parser cannot
            read must not silently publish as full validity.
    """
    try:
        added_v = _parse_version(added)
        removed_v = _parse_version(removed) if removed else None
    except Exception:
        raise SystemExit(
            f"messages seed: unparseable version window ({added!r}, "
            f"{removed!r}); refusing to publish a validity set for it."
        ) from None
    return [
        v
        for v in VERSIONS
        if _parse_version(v) >= added_v
        and (removed_v is None or _parse_version(v) < removed_v)
    ]


def build_pl_terminology(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per (target, category, source_term): the target's own facts.

    No natural language appears in this config. Three sources, every one a
    tracked file, so the config stays regenerable from the tag:

    * the pack tree, via the vocabulary ``rows`` -- which terms exist, in
      which sections, on which versions
    * ``vocabulary_definitions.py`` -- the symbol and variable-convention
      inventory (CORE-1396). The pack files do not carry these sections yet,
      so their per-locale renderings are absent from ``vocabulary``; shipping
      the inventory anyway is what makes that gap measurable.
    * the ``cpython_messages.json`` seed -- the error-message templates
      (CORE-1679), English side only. The seed also carries ar/es
      translations; those stay out of ``vocabulary`` until the
      content-addressed-key gate (CORE-1565) clears.
    """
    # Terms: collapse the per-version vocabulary rows to validity sets.
    versions_of: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        # Term sections only: the vocabulary families' inventory comes from
        # vocabulary_definitions/the seed below, so a pack rendering a symbol
        # must not ALSO mint an inventory row for it (the grain guard would
        # refuse the duplicate).
        if row["category"] in SECTIONS:
            versions_of.setdefault((row["category"], row["source_term"]), set()).add(
                row["pl_version"]
            )
    out: list[dict[str, Any]] = []
    for (section, term), versions in versions_of.items():
        ordered = sorted(versions, key=VERSIONS.index)
        out.append(
            {
                "target": TARGET,
                "category": section,
                "subcategory": _subcategory_for(section, term, ordered[0]),
                "source_term": term,
                "source_text": None,
                "glyph": None,
                "pl_versions": ordered,
            }
        )

    # The vocabulary sections come through the inventory's own accessor, so a
    # section added there is exported here without a hand-written twin loop.
    #
    # Symbols also publish their glyph. It is target truth with one row each
    # here, not the 51 copies of a constant that kept it out of the pack files,
    # and without it nothing in this artifact says that `paren_open` means `(`.
    # The card's own `_` example depended on a fact the data did not carry.
    for section in VOCABULARY_SECTIONS:
        glyphs = {
            entry.slug: getattr(entry, "glyph", None)
            for entry in inventory_for_section(section)
        }
        for slug, english in english_values(section).items():
            out.append(
                {
                    "target": TARGET,
                    "category": section,
                    "subcategory": None,
                    "source_term": slug,
                    "source_text": english,
                    "glyph": glyphs.get(slug),
                    "pl_versions": list(VERSIONS),
                }
            )

    seed = json.loads(MESSAGES_SEED.read_text(encoding="utf-8"))
    if seed.get("implementation") != "cpython":
        raise SystemExit(
            f"messages seed: implementation {seed.get('implementation')!r} is "
            f"not this target's -- the v8 seed uses a different version "
            f"scheme, and mislabeling it as python validity would publish "
            f"windows that mean nothing."
        )
    # The seed-level default is REQUIRED, matching seed_message_templates.py:
    # a seed that omits it is malformed there and must be malformed here,
    # not silently defaulted to the range floor.
    default_added = seed["version_added"]
    # A key may appear more than once: CPython reworded
    # UnboundLocalError.before_assignment at 3.11, and the seed carries both
    # wordings as separate version-windowed entries. For this config that is
    # ONE term whose English surface changed -- the same phenomenon as a
    # locale redefining a rendering mid-range -- so the rows merge: the
    # validity set is the union of the windows, and `source_text` is the
    # latest wording, matching the union-at-latest convention the JSON uses.
    by_key: dict[str, list[dict[str, Any]]] = {}
    for template in seed["templates"]:
        by_key.setdefault(template["key"], []).append(template)
    for key, entries in by_key.items():
        windows: list[str] = []
        # Resolved ONCE per entry and reused for both the window and the
        # current-wording ranking: two resolutions with different null
        # handling would let an explicit null count as range-floor for
        # validity but rank lowest for wording, publishing a superseded
        # template as the term's English surface. `or default_added`, not a
        # .get default, because an explicit null bypasses dict.get.
        added_of = {
            id(entry): entry.get("version_added") or default_added for entry in entries
        }
        for entry in entries:
            added = added_of[id(entry)]
            window = _message_pl_versions(added, entry.get("version_removed"))
            if not window and entry.get("version_removed"):
                removed = entry["version_removed"]
                if _parse_version(added) >= _parse_version(removed):
                    raise SystemExit(
                        f"messages seed: {key!r} has an empty window "
                        f"(added {added}, removed {removed}) -- seed "
                        f"corruption, not a template to silently drop."
                    )
            windows.extend(window)
        pl_versions = sorted(set(windows), key=VERSIONS.index)
        if not pl_versions:
            # Every window falls outside the shipped range (e.g. a template
            # added at a future version). Not an error -- just not in this
            # release.
            continue
        current = max(entries, key=lambda e: _parse_version(added_of[id(e)]))
        out.append(
            {
                "target": TARGET,
                "category": "messages",
                # The key convention is "<Surface>.<slug>" -- the leading
                # component IS the message's grouping (ZeroDivisionError,
                # traceback, ...), and unlike the seed's sparse `cluster`
                # field it is total, so no reader meets a null bucket that
                # means "uncurated" beside nulls that mean "not applicable".
                "glyph": None,
                "subcategory": key.split(".", 1)[0],
                "source_term": key,
                "source_text": current["template_en"],
                "pl_versions": pl_versions,
            }
        )

    emitted = {r["category"] for r in out}
    if emitted != set(CATEGORY_FAMILIES):
        raise SystemExit(
            f"pl_terminology categories and CATEGORY_FAMILIES disagree -- "
            f"undescribed: {sorted(emitted - set(CATEGORY_FAMILIES))}, "
            f"declared with no builder: "
            f"{sorted(set(CATEGORY_FAMILIES) - emitted)}. Both directions "
            f"are drift."
        )
    # The declared grain, enforced rather than assumed: one row per
    # (target, category, source_term). The message-rewording merge above is
    # what keeps the seed's duplicate keys from violating it; a duplicate
    # surviving to here means a new source repeated a key and the config
    # would publish an ambiguous join target.
    keys = Counter((r["target"], r["category"], r["source_term"]) for r in out)
    duplicated = sorted(k for k, n in keys.items() if n > 1)
    if duplicated:
        raise SystemExit(
            f"pl_terminology grain violated -- duplicate keys: {duplicated[:5]}"
        )
    out.sort(
        key=lambda r: (
            r["target"],
            CATEGORY_FAMILIES.index(r["category"]),
            r["source_term"],
        )
    )
    return out


def terms_per_version(rows: list[dict[str, Any]]) -> dict[str, int]:
    """One term count per interpreter version.

    Every locale ships the same term set at a given version, so this is one
    number per version, not a distribution. Asserted rather than assumed: an
    uneven locale would make the card's headline count a fiction.

    Raises:
        SystemExit: if locales disagree at any version.
    """
    # Scoped to the term sections: "every locale ships the same term set" is
    # a claim about the translation sections, and the vocabulary families
    # (symbols, messages) are expected to roll out unevenly -- that is the
    # measurable gap, not a uniformity failure.
    per_pack: Counter[tuple[str, str]] = Counter(
        (r["locale"], r["pl_version"]) for r in rows if r["category"] in SECTIONS
    )
    # Completeness before uniformity: a (locale, version) with ZERO rows is
    # invisible to the size-agreement check below -- absent keys contribute
    # nothing to `sizes` -- so a pack whose version file resolves to nothing
    # would slip through and publish coverage the pack does not provide.
    locales_present = {loc for loc, _ in per_pack}
    missing = [
        (loc, v)
        for loc in sorted(locales_present)
        for v in VERSIONS
        if (loc, v) not in per_pack
    ]
    if missing:
        raise SystemExit(
            f"{len(missing)} (locale, version) pairing(s) produced no rows: "
            f"{missing[:5]}. A version a pack does not cover must not be "
            f"published as covered."
        )
    out: dict[str, int] = {}
    for version in VERSIONS:
        sizes = {n for (_, v), n in per_pack.items() if v == version}
        if len(sizes) != 1:
            raise SystemExit(
                f"Locales disagree on term count at Python {version}: "
                f"{sorted(sizes)}. The dataset cannot state one number per "
                f"version until they agree."
            )
        out[version] = sizes.pop()
    return out


def read_package_version(locale: str) -> str:
    """Return the semver of ``locale``'s distributable, from its pyproject.

    This is the number PyPI publishes for that pack, and publishing it here is
    what lets a reader align the two: revision R of this dataset says Arabic is
    at ``0.0.4``, and ``legesher-i18n-python-ar==0.0.4`` is the wheel carrying
    those words. Without it the two artifacts version on unrelated clocks --
    this dataset on :data:`DATASET_VERSION`, each pack on its own semver -- and
    nothing states which pack version a given revision actually describes.

    Read from ``pyproject.toml`` rather than the installed distribution: the
    export must describe the packs in the tree it is exporting, not whatever
    happens to be installed in the environment running it.

    Raises:
        SystemExit: if the pyproject is missing or declares no version. A
            locale whose version cannot be read must not publish a null and
            let a consumer read it as "unversioned".
    """
    pyproject = PACKS_DIR / locale / "pyproject.toml"
    if not pyproject.exists():
        raise SystemExit(
            f"{locale}: no pyproject.toml at {pyproject}. Every shipped pack "
            f"is a distributable and must declare the version it ships as."
        )
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
        import tomli as tomllib  # type: ignore[no-redef]

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = (data.get("project") or {}).get("version")
    if not version:
        raise SystemExit(
            f"{locale}: pyproject.toml declares no [project] version, so the "
            f"dataset cannot state which package version this locale ships."
        )
    return str(version)


def require_card_image() -> None:
    """The card's banner must exist before the export writes anything.

    The card links the image relatively, so a missing file is not cosmetic: it
    is a broken image at the top of a public dataset page. Checked with the
    other refusals, before a byte is written, so a failed run leaves nothing
    that could be mistaken for publishable.

    Raises:
        SystemExit: if the source image is not in the repository.
    """
    if not CARD_IMAGE_SOURCE.is_file():
        raise SystemExit(
            f"EXPORT REFUSED: the dataset card's banner image is missing from "
            f"{CARD_IMAGE_SOURCE}. The card links it relatively, so exporting "
            "without it ships a broken image on the dataset page. Restore the "
            "file, or drop the ![](...) line from the card."
        )


def copy_card_image(out_dir: Path) -> Path:
    """Place the banner where the card's relative link points, and return it.

    Returns the written path so the caller can put it in the manifest's file
    list. The card promises a checksum for every file it ships, and an image
    copied in without one makes that a false claim about a published file.

    ``export_corpus.py`` pairs its copy with a bystander sweep over
    ``<out>/assets``, because a stray PNG there would ship on the dataset page
    under the same allow-list. This export needs no such check: it ``rmtree``s
    ``--out`` and rebuilds it, so nothing it did not write can be in the
    directory to begin with. The guard would be code that never runs, which is
    code nobody has ever exercised.
    """
    target = out_dir / CARD_IMAGE_TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.resolve() != CARD_IMAGE_SOURCE.resolve():
        shutil.copyfile(CARD_IMAGE_SOURCE, target)
    return target


def legesher_i18n_version() -> str:
    """Return the version of the library the packs load through.

    Recorded in the manifest's toolchain block beside pyarrow and Python,
    because that is what it is: something that built this export, not
    something that versions it. This dataset carries its own
    :data:`DATASET_VERSION`, deliberately decoupled -- ``legesher-i18n`` moves
    for library reasons and stands still through pack corrections, so binding
    the two would make each lie about the other. Recording it keeps the
    relationship answerable without making it an identity.

    Read from ``pyproject.toml`` rather than the imported module, for the same
    reason :func:`read_package_version` does: the export must describe the tree
    it is exporting, not whatever is installed in the environment running it.

    Raises:
        SystemExit: if the pyproject is missing or declares no version.
    """
    pyproject = _I18N_ROOT / "pyproject.toml"
    if not pyproject.exists():
        raise SystemExit(
            f"no pyproject.toml at {pyproject}, so the export cannot record "
            f"which legesher-i18n built it."
        )
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
        import tomli as tomllib  # type: ignore[no-redef]

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    version = (data.get("project") or {}).get("version")
    if not version:
        raise SystemExit(
            f"{pyproject} declares no [project] version, so the export cannot "
            f"record which legesher-i18n built it."
        )
    return str(version)


def build_locale_rows(
    locales: list[str],
    registry: dict[str, Any],
    package_versions: dict[str, str],
) -> list[dict[str, Any]]:
    """One row per shipped locale: identity, plus card-only pairing state."""
    out = []
    for locale in locales:
        meta = registry[locale]
        out.append(
            {
                "locale": locale,
                "language_name": meta.get("name"),
                "native_name": meta.get("native"),
                "iso639_2": meta.get("iso639_2"),
                "bcp47": meta.get("bcp47"),
                "rtl": bool(meta.get("rtl", False)),
                "has_case_distinction": bool(meta.get("has_case_distinction", True)),
                # tier and package_version stay on the in-memory row for the
                # card's Languages table and are projected out of the
                # published table by LOCALE_COLUMNS: both live in `packs`,
                # where they vary by pairing.
                "tier": meta.get("status"),
                "package_version": package_versions[locale],
            }
        )
    out.sort(key=lambda r: r["locale"])
    return out


def nfkc_instability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe the NFKC-unstable renderings in the emitted vocabulary.

    Python normalizes identifiers to NFKC at parse time (PEP 3131), so a
    rendering whose NFKC form differs from itself is typed one way and resolved
    another. That is not a defect -- both spellings name the same identifier --
    but it is a property a consumer diffing this dataset against source code, or
    joining it to another corpus, has to know about before they are surprised by
    it.

    MEASURED, never asserted. The count and the characters involved come from
    the rows about to be published, so the card cannot claim a number the data
    stopped supporting. Today it is one locale and one character (Thai
    ``U+0E33 SARA AM``, which decomposes to ``U+0E4D U+0E32``); a regenerated
    pack could move that figure in either direction, and a hand-written "22" is
    exactly how a card outlives the thing it counted.
    """
    by_locale: dict[tuple[str, str], set[str]] = {}
    characters: set[str] = set()
    affected_rows = 0

    for row in rows:
        value = row["translation"]
        if unicodedata.normalize("NFKC", value) == value:
            continue
        affected_rows += 1
        by_locale.setdefault((row["locale"], row["language_name"]), set()).add(value)
        characters.update(ch for ch in value if unicodedata.normalize("NFKC", ch) != ch)

    return {
        "rows": affected_rows,
        "renderings": sum(len(values) for values in by_locale.values()),
        "locales": [
            {"locale": code, "language_name": name} for code, name in sorted(by_locale)
        ],
        "characters": [
            {"codepoint": f"U+{ord(ch):04X}", "name": unicodedata.name(ch, "unnamed")}
            for ch in sorted(characters)
        ],
    }


def assert_python_only(rows: list[dict[str, Any]]) -> None:
    """Re-prove the CORE-1913 property on the emitted rows.

    The pack tree is Python-only by construction, so this should be
    unreachable. That is the point: it converts an argument about
    ``yaml_exporter``'s filter into a check on the bytes about to be published.
    If a member-bearing target ever gains a pack tree, this fails loudly rather
    than shipping JavaScript terminology under a card that says Python.
    """
    targets = {r["target"] for r in rows}
    if targets != {TARGET}:
        raise SystemExit(
            f"Refusing to export: expected only target {TARGET!r}, found "
            f"{sorted(targets)}. This artifact covers Python packs; "
            f"non-Python selections must not be published labeled by target "
            f"(CORE-1913)."
        )


def format_version_range(versions: list[str]) -> str:
    """Render a validity list as the range string the JSON carries.

    One decision, one place: the JSON field is named ``pl_version_range`` and
    is a STRING, while the parquet configs carry ``pl_versions`` lists -- the
    same name carrying two types would hand consumers Python's
    substring-containment trap (``"3.1" in "3.10-3.14"`` is True).

    Asserts contiguity, because a range string cannot represent a gap; the
    parquet lists can, and are the form that survives one appearing.
    """
    if not versions:
        raise SystemExit(
            "a pairing with no covered versions has no range to publish -- "
            "a locale that resolved to zero rows should have been refused "
            "upstream, not rendered here."
        )
    ordered = sorted(versions, key=VERSIONS.index)
    lo, hi = VERSIONS.index(ordered[0]), VERSIONS.index(ordered[-1])
    if ordered != list(VERSIONS[lo : hi + 1]):
        raise SystemExit(
            f"version set {ordered} is not contiguous; a range string would "
            f"misstate it. Publish the list form instead."
        )
    return f"{ordered[0]}-{ordered[-1]}" if lo != hi else ordered[0]


def write_json(
    out: Path,
    rows: list[dict[str, Any]],
    locales: list[str],
    registry: dict[str, Any],
    package_versions: dict[str, str],
) -> list[Path]:
    """Write one loadable JSON per (locale, target): the translations alone.

    ``json/<locale>/<target>.json`` (CORE-2020). The parquet configs are the
    queryable form and carry the structure -- validity sets, delta markers,
    subcategories. This file is the loadable form, shaped like what the
    published package ships: the pack's own semver, the version range it
    covers, and the translations as flat key/value sections.

    Values are the LATEST version's resolved rendering, over the union of
    terms across the range -- ``build_rows`` sorts ascending by version
    within a locale, so a single overwrite pass keeps the last value seen.
    Sections are whatever categories the rows actually carry, in
    :data:`CATEGORY_FAMILIES` order: when symbol or message renderings land
    in the packs, they appear here without this function changing, rather
    than being silently filtered to the four sections of 2026.

    Sorted keys and a trailing newline, so the bytes are stable and the files
    diff cleanly between revisions.
    """
    written: list[Path] = []
    sections_of: dict[str, dict[str, dict[str, str]]] = {}
    versions_of: dict[str, set[str]] = {}
    for row in rows:
        sections_of.setdefault(row["locale"], {}).setdefault(row["category"], {})[
            row["source_term"]
        ] = row["translation"]
        versions_of.setdefault(row["locale"], set()).add(row["pl_version"])

    # One key set for every file in a revision: a family ANY locale renders
    # appears in ALL payloads (empty where absent), so a loader written
    # against one locale's file works against every other's, and a locale's
    # missing section reads as the visible gap it is rather than a KeyError.
    published_families = [
        family
        for family in CATEGORY_FAMILIES
        if any(family in secs for secs in sections_of.values())
    ]
    for locale in locales:
        secs = sections_of.get(locale, {})
        payload = {
            "locale": locale,
            "target": TARGET,
            # The distinction between the two distribution channels, stated
            # in the file: this artifact snapshots what the versioned package
            # ships, and this is the version that ships it.
            "package_version": package_versions[locale],
            "tier": registry[locale].get("status"),
            "pl_version_range": format_version_range(
                sorted(versions_of.get(locale, ()), key=VERSIONS.index)
            ),
            **{
                family: dict(sorted(secs.get(family, {}).items()))
                for family in published_families
            },
        }
        path = out / "json" / locale / f"{TARGET}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def write_parquet(
    out: Path, name: str, rows: list[dict[str, Any]], columns: tuple[str, ...]
) -> Path:
    """Write one Parquet file with deterministic settings.

    ``columns`` is the published schema and is applied here rather than in the
    row builders, which keep the fuller dicts the assertions and the card read
    (CORE-1986). Projecting is explicit and ordered: ``from_pylist`` would
    otherwise take its column order from the first row's insertion order, which
    is a property of how a dict happened to be built.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    missing = [c for c in columns if rows and c not in rows[0]]
    if missing:
        raise SystemExit(
            f"{name}: published schema names {missing}, which the rows do not "
            f"carry. A column silently dropped from the builders would "
            f"otherwise become a column silently missing from the dataset."
        )
    projected = [{c: row[c] for c in columns} for row in rows]

    path = out / "data" / f"{name}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(projected)
    pq.write_table(
        table,
        path,
        compression="zstd",
        compression_level=3,
        write_statistics=True,
        # One row group keeps the layout a function of the rows alone, so two
        # runs over the same input cannot differ by chunking.
        row_group_size=max(len(rows), 1),
    )
    return path


def check_license_consistency(locales: list[str]) -> dict[str, int]:
    """Return the ``metadata.license`` values the packs actually carry.

    The dataset declares :data:`DECLARED_LICENSE` for the compilation, but each
    pack file also carries its own ``metadata.license``. Those are different
    claims and they are allowed to differ in principle -- a compilation license
    is not the license of every part. What is NOT acceptable is publishing a
    card that asserts one license while every row's own metadata asserts
    another, with nobody having decided which is right.

    So this reports rather than assumes: the counts land in the manifest and
    the card, and a disagreement prints a warning at build time. It does not
    hard-fail, because resolving it is a licensing decision for a maintainer,
    not something an exporter should settle by refusing to run.
    """
    seen: Counter[str] = Counter()
    for locale in locales:
        for version in VERSIONS:
            raw = _read_yaml(
                PACKS_DIR
                / locale
                / f"legesher_i18n_python_{locale}"
                / "packs"
                / f"{version}.yml"
            )
            seen[str((raw.get("metadata") or {}).get("license", "(unset)"))] += 1
    return dict(seen)


def licenses_agree(pack_licenses: dict[str, int]) -> bool:
    """Do the packs' own license fields agree with the declared license?

    Case-folded: SPDX writes ``Apache-2.0`` and the Hub frontmatter wants
    ``apache-2.0``. A case-sensitive comparison would keep warning forever the
    moment the packs are reconciled to the canonical SPDX spelling.
    """
    declared = DECLARED_LICENSE.casefold()
    return {name.casefold() for name in pack_licenses} == {declared}


def render_normalization(nfkc: dict[str, Any]) -> str:
    """Render the card's normalization note from the measured instability.

    Two branches, both true statements about the data. The populated one names
    the count, the locales and the characters :func:`nfkc_instability` actually
    found; the empty one says so. Neither hard-codes a figure, because the
    packs are regenerated and the figure moves with them.
    """
    preamble = (
        "Python normalizes identifiers to NFKC when it parses them (PEP 3131), "
        "so a rendering whose own NFKC form differs from it is typed one way "
        "and resolved another."
    )

    renderings = nfkc.get("renderings", 0)
    if not renderings:
        return (
            f"{preamble}\n\n> [!NOTE]\n> No rendering in this release is NFKC-unstable."
        )

    locales = nfkc.get("locales") or []
    characters = nfkc.get("characters") or []
    who = ", ".join(f"{item['language_name']} (`{item['locale']}`)" for item in locales)
    which = ", ".join(f"`{item['codepoint']}` {item['name']}" for item in characters)
    count = f"{renderings} renderings" if renderings != 1 else "One rendering"
    verb = "are" if renderings != 1 else "is"

    return (
        f"{preamble}\n\n"
        f"> [!NOTE]\n"
        f"> {count} in this release {verb} NFKC-unstable, all in {who}, all "
        f"through {which}. If you compare a `translation` value against a name "
        f"taken from a running interpreter, normalize both to NFKC first."
    )


def render_card(
    manifest: dict[str, Any],
    pack_licenses: dict[str, int],
    locale_rows: list[dict[str, Any]],
    terminology_rows: list[dict[str, Any]],
) -> str:
    """Render the Hugging Face dataset card.

    Generated, never hand-edited: the card states counts, and a hand-edited
    card is how a count survives the thing it counted changing.

    ``terminology_rows`` is a parameter for the same reason the manifest's row
    sets are: the category table counts them, and counting a set the card did
    not receive is how the table starts describing a previous export.
    """
    counts = manifest["counts"]
    locales = manifest["locales"]
    src = manifest["source"]

    # Quoted, always. Unquoted, YAML 1.1 reads `no` as boolean false, which is
    # how Norwegian silently disappears from the Hub's language facet.
    lang_yaml = "\n".join(f'  - "{code}"' for code in locales)

    # Every per-pack fact is a table cell, never a sentence. Maturity used to
    # get a prose paragraph asserting the spread; it was both a broad claim and
    # a second place for a number to go stale, and the Status column already
    # states each pack's stamp one row at a time.
    language_rows = "\n".join(
        f"| `{r['locale']}` | {r['language_name']} | {r['native_name']} "
        f"| `{r['tier']}` | `{r['package_version']}` |"
        for r in locale_rows
    )
    category_rows = category_table(terminology_rows)

    # The worked example is READ from the rows, never typed. It said `0.0.4`
    # while `ar` shipped `0.0.5`, because a pack bump moves 51 versions and a
    # sentence does not move with them.
    example = next(
        (r for r in locale_rows if r["locale"] == "ar"),
        locale_rows[0] if locale_rows else {"locale": "ar", "package_version": "0.0.0"},
    )
    eg_locale = example["locale"]
    eg_version = example["package_version"]
    eg_package = f"legesher-i18n-python-{eg_locale}"
    # A range, not a list. Five cells' worth of versions in one column is a
    # column nobody can read; the per-version facts are in `pl_versions`.
    target_versions = f"`{VERSIONS[0]}`-`{VERSIONS[-1]}`"
    normalization_section = render_normalization(manifest.get("nfkc_unstable") or {})
    license_note = ""
    if not licenses_agree(pack_licenses):
        rendered = ", ".join(
            f"`{name}` ({count} files)" for name, count in sorted(pack_licenses.items())
        )
        license_note = (
            f"\n> **Note on the license field inside the packs.** The pack "
            f"files carry their own `metadata.license`, currently {rendered}, "
            f"while this dataset is `{DECLARED_LICENSE}`. The compilation "
            f"license is the one that governs this dataset; the in-pack field "
            f"is being reconciled.\n"
        )

    return f"""\
---
license: {DECLARED_LICENSE}
tags:
  - multilingual
  - code
  - programming
  - localization
task_categories:
  - translation
annotations_creators:
  - machine-generated
  - expert-generated
size_categories:
  - 10K<n<100K
pretty_name: Legesher Language Packs
language:
{lang_yaml}
configs:
  - config_name: vocabulary
    data_files:
      - split: train
        path: data/vocabulary.parquet
  - config_name: locales
    data_files:
      - split: train
        path: data/locales.parquet
  - config_name: pl_terminology
    data_files:
      - split: train
        path: data/pl_terminology.parquet
  - config_name: packs
    data_files:
      - split: train
        path: data/packs.parquet
---

# Legesher Language Packs

![Legesher language packs](assets/language-packs-card.png)

Legesher's language packs 📦 are the localization layer for code; the fixed
vocabulary of a programming language in other natural languages.

Every reserved word within a programming language's grammar (keywords,
builtins, exceptions, error messages) is compiled into a language pack that,
when utilized by Legesher, allows code to be in any language and it compiles
all the same.

| Release | Languages supported | Target | Versions | License | `legesher-i18n` | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| `{DATASET_VERSION}` | {counts["locales"]} | `{TARGET}` | {target_versions} | Apache-2.0 | `{manifest["toolchain"]["legesher_i18n"]}` | `{src["commit"][:12]}` |

## Languages

| Pack | Language | Native name | Status | Package |
| --- | --- | --- | --- | --- |
{language_rows}

## What a pack is made of

### Target

Each language pack is created based on the requirements of a programming
language, its target, which sets the categories it carries, the reserved words
in each, and the forms a rendering is allowed to take. The specific versions of
a programming language a particular reserved word belongs to are noted as well,
so the language pack grows with the progression of a programming language.

### Categories

| Category | Subcategories | Terms | What it holds |
| --- | --- | --- | --- |
{category_rows}

## Maturity

| Stage | What it means |
| --- | --- |
| `experimental` | Machine-drafted, then curated by maintainers and passed through the mechanical gates: identifier validity, cross-section collision checks, Unicode normalization, and a regeneration check proving the packs match their source of truth. No native speaker has signed off. |
| `reviewed` | A native speaker of the language has reviewed the pack and signed off on it. |
| `official` | Certified review plus term screening. |

## The dataset

| Config | One row per | Answers |
| --- | --- | --- |
| `locales` | natural language | who is this language? |
| `pl_terminology` | (target, category, source term) | what vocabulary does the target carry, and on which versions? |
| `vocabulary` | (locale, target, version, category, source term) | what is it called in this language? |
| `packs` | (locale, target) | how far along is this pairing? |

### `pl_terminology`

The programming language's own terminology. No natural language appears in
this config.

* `target`, `category`, `source_term`: the key
* `subcategory`: the finer kind, as in the table above
* `source_text`: the English surface, where `source_term` is not itself that
  surface. `symbols` carry the name, so `paren_open` is *opening parenthesis*.
  `variable_conventions` carry the identifier, so `accumulator` is `total`.
  `messages` carry the template. Null on `keywords`, `builtins`, `exceptions`
  and `implicit_params`, where `source_term` is the English. A message with no
  text carries `""`, which is a different fact from null: `AssertionError` on a
  bare `assert` genuinely has no message
* `glyph`: the character a symbol names, so `paren_open` is `(`. Null on every
  other category, and null on the symbols with no printable form: indentation,
  a line break, a space
* `pl_versions`: the target versions the entry is valid for

Availability lives here, once: `except*` carries `["3.11", ...]`, and a term
in two categories carries two rows with their own sets, so `type` is a builtin
on every version and a keyword only from 3.12.

This config is also the coverage checklist. A `pl_terminology` entry with no
matching `vocabulary` rows for a locale is a gap in that pack, stated by the
data rather than discovered downstream: the `symbols`, `variable_conventions`
and `messages` categories ship their source-side inventory ahead of any
locale's renderings for exactly that reason.

### `vocabulary`

The renderings, one row per (locale, target, version, category, source term).

* `locale`: join into `locales`; `target`, `category`, `source_term`: join
  into `pl_terminology`
* `pl_version`: rows are given resolved, so each states what you would get on
  that version of the target
* `translation`: the rendering Legesher ships
* `defined_at`: the version whose pack file defines this rendering. A row
  inherits when `defined_at` differs from `pl_version`. This is a fact about
  the rendering, not the term: Sinhala redefines terms at 3.13 to conjunct
  forms, so its `defined_at` differs from every other language's on the same
  term

`category` is part of the key on purpose: `type` is rendered once as a
keyword and once as a builtin, and those renderings may differ.

### `locales`

Natural-language identity: names (`language_name`, `native_name`), identity
tags (`iso639_2`, `bcp47`), script properties (`rtl`, `has_case_distinction`).

`locale` is a pack id, not a language tag. Where the two differ, `locale` is
the shorter form: `no` is BCP 47 `nb`, `zh` is `zh-Hans`, `sr` is `sr-Cyrl`.
Join to anything keyed by language tag on `bcp47`, or you drop exactly the rows
that differ.

### `packs`

The shipping unit, one row per (locale, target) pairing.

* `package_version`: the semver of this pairing's own distributable. A row
  reading `{eg_locale}` / `{TARGET}` / `{eg_version}` means these are the words
  in `{eg_package}=={eg_version}`. Each pairing versions on its own clock
* `tier`: the maturity of exactly this pairing
* `pl_versions`: the target versions this pack covers

### JSON

`json/<locale>/<target>.json` is the loadable form: the translations alone,
with the pack's `package_version` and a `pl_version_range` string naming the
versions it covers. Values are the latest version's resolved rendering over
the union of terms across the range; the parquet configs carry the full
per-version structure the JSON leaves out.

## Normalization

{normalization_section}

## Packages

Legesher uses this dataset as the language packs for coding in other natural
languages. Each language ships as its own distribution,
`legesher-i18n-python-<locale>`, so Arabic is `{eg_package}`, and they are
loaded by `legesher-i18n`, which resolves a pack against the interpreter you are
running.
{license_note}
## Citation

```bibtex
@misc{{legesher_language_packs,
  title        = {{Legesher Language Packs: programming vocabulary rendered in natural languages}},
  version      = {{{DATASET_VERSION}}},
  author       = {{Legesher}},
  year         = {{2026}},
  publisher    = {{Hugging Face}},
  howpublished = {{\\url{{https://huggingface.co/datasets/legesher/language-packs}}}}
}}
```
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


class ExportRefused(SystemExit):
    """A gate refused the push. Named so a caller can tell it from a crash."""


def require_push_approval(governance_signoff: str | None) -> None:
    """Refuse to push without the governance sign-off AND the env approval.

    Runs BEFORE the export writes anything and BEFORE any network library is
    imported.

    Raises:
        ExportRefused: unless both keys are turned.
    """
    if governance_signoff != GOVERNANCE_TICKET:
        raise ExportRefused(
            f"PUSH REFUSED: --push requires --governance-signoff "
            f"{GOVERNANCE_TICKET}. Publishing terminology under a community's "
            "name is a governance decision, not a scripting one."
        )
    if os.environ.get(PUSH_ENV_VAR) != "1":
        raise ExportRefused(
            f"PUSH REFUSED: --push requires {PUSH_ENV_VAR}=1 in the "
            "environment. The flag and the variable are deliberately two "
            "separate keys: a command-line typo must not be able to publish."
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


def require_reproducible_source(source: dict[str, str]) -> None:
    """Refuse to push a revision that cannot be rebuilt from the commit it names.

    The runbook's second precondition is "clean AND tagged". Both halves are
    checked here, because the manifest records both and recording only helps a
    reader who checks.

    Clean: a published revision is pinned by consumers against the commit in
    its manifest; if the tree had uncommitted changes, that commit rebuilds
    something else. Export freely from a dirty tree -- publish from one, never.
    "git unavailable" is refused with the same force, because both mean the
    provenance claim is unverified and only one of them looks alarming.

    Tagged: the tag is how a Hub revision, a release ticket and the card's
    provenance line say the same version out loud. An untagged push stamps
    ``(untagged)`` into the card and leaves the three with no shared name.

    Raises:
        ExportRefused: unless the worktree was clean and the commit tagged.
    """
    worktree = source.get("worktree")
    if worktree != "clean":
        raise ExportRefused(
            f"PUSH REFUSED: worktree is {worktree!r}, so the manifest's commit "
            f"({source.get('commit', 'unknown')[:12]}) does not rebuild this "
            "artifact. Commit or stash, then re-run. Exporting from a dirty "
            "tree is fine; pinning a public revision to a commit it did not "
            "come from is not."
        )
    tag = source.get("tag", UNTAGGED)
    # Checked against the EXACT release tag, not merely the prefix. A release
    # commit here routinely carries `v0.24.0` and a per-pack
    # `i18n-python-ar-v0.0.4` as well; accepting any of them would stamp a
    # version string this dataset does not have, which is the failure this
    # gate exists to prevent rather than a near-miss of it.
    #
    # Prefix-matching was the earlier rule and it left the real hole open: it
    # accepted `language-packs-v2026.08.24` against a build declaring 0.1.0,
    # so a revision could publish under a version it did not claim. The
    # declared version is the one in this file; the tag has to agree with it.
    if tag != RELEASE_TAG:
        raise ExportRefused(
            f"PUSH REFUSED: commit {source.get('commit', 'unknown')[:12]} "
            f"carries {tag!r}, not {RELEASE_TAG!r}. This export declares "
            f"version {DATASET_VERSION}, and a published revision has to be "
            f"reachable by the version it announces. Either tag this commit "
            f"(`git tag {RELEASE_TAG}`), or bump DATASET_VERSION if this is a "
            f"new release, then re-run."
        )


def require_license_agreement(pack_licenses: dict[str, int]) -> None:
    """Refuse to push while the declared and per-pack licenses disagree.

    "Reconcile before publishing" is what the export has always printed here.
    On a push that is a gate, not advice: both claims become public in the same
    revision, and a reader has no way to tell which one is load-bearing.

    Reads only the pack YAML, so it belongs with the pre-export gates rather
    than after the artifact is built.

    Raises:
        ExportRefused: if the compilation license and the packs disagree.
    """
    if licenses_agree(pack_licenses):
        return
    rendered = ", ".join(f"{n}={c}" for n, c in sorted(pack_licenses.items()))
    raise ExportRefused(
        f"PUSH REFUSED: the card declares {DECLARED_LICENSE!r} for the "
        f"compilation, but the packs' own metadata.license says: {rendered}. "
        f"Both claims are public once pushed; reconcile them first."
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
    """Upload the exported packs to the Hugging Face Hub.

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
    info = api.upload_folder(
        folder_path=str(out_dir),
        repo_id=target_repo,
        repo_type="dataset",
        allow_patterns=list(PUSH_ALLOW_PATTERNS),
        # upload_folder only ADDS. The export rebuilds --out from scratch, but
        # that says nothing about the remote: a locale withdrawn by a
        # contributor, or a Python version dropped at EOL, leaves its files on
        # the Hub forever -- present in the dataset, absent from manifest.json,
        # accounted for by nothing. Scoped to the same patterns the upload
        # carries so it can only ever remove files this export owns.
        delete_patterns=list(PUSH_ALLOW_PATTERNS),
        # A dataset repo's commit history is as public as its files, so the
        # message obeys the same rule they do: no internal ticket.
        commit_message="packs export",
    )
    print(f"Pushed {out_dir} -> {target_repo}")
    # The runbook says to pin the revision against the release ticket, so
    # print the thing being pinned rather than sending the operator to the Hub
    # to copy it by hand.
    revision = getattr(info, "oid", None)
    if revision:
        print(f"revision:         {revision}")
    url = getattr(info, "commit_url", None)
    if url:
        print(f"commit:           {url}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    parser.add_argument(
        "--verify-deterministic",
        action="store_true",
        help="Export twice into separate trees and compare every checksum",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help=(
            "upload to the Hub. Refuses without the gates below; never changes "
            "visibility, so it cannot publish a private dataset"
        ),
    )
    parser.add_argument(
        "--target-repo",
        default=DEFAULT_TARGET_REPO,
        help=(
            f"push destination (default {DEFAULT_TARGET_REPO}). Anything else "
            f"must be repeated verbatim in {TARGET_OVERRIDE_ENV_VAR}"
        ),
    )
    parser.add_argument(
        "--governance-signoff",
        help=(
            f"must be {GOVERNANCE_TICKET} to push, and {PUSH_ENV_VAR}=1 must be "
            f"set in the environment: two keys, so a typo cannot publish"
        ),
    )
    args = parser.parse_args()

    # Silently accepting push flags without --push lets a forgotten --push exit
    # 0 looking like a successful publish.
    if not args.push and (
        args.governance_signoff or args.target_repo != DEFAULT_TARGET_REPO
    ):
        raise SystemExit(
            "--target-repo/--governance-signoff are push options, but --push "
            "was not given. Nothing would be uploaded. Add --push, or drop them."
        )

    registry = load_registry()
    locales = pack_locales()
    reconcile_locales(registry, locales)

    rows = build_rows(locales, registry)
    assert_python_only(rows)
    rowless = sorted(set(locales) - {r["locale"] for r in rows})
    if rowless:
        raise SystemExit(
            f"locale(s) produced no vocabulary rows: {rowless}. A scaffolded "
            f"pack with empty sections must be finished or removed, not "
            f"published as an empty pairing."
        )
    # One read per locale per pass -- three builders consume it, and reading
    # it three times would open a window where a mid-export pyproject edit
    # publishes one version in packs.parquet and another in the JSON.
    package_versions = {loc: read_package_version(loc) for loc in locales}
    locale_rows = build_locale_rows(locales, registry, package_versions)

    # ONE snapshot, taken before anything is written and reused for both the
    # gate and the manifest. Two calls would let the gate pass on a clean tree
    # and the manifest then record `dirty`, because writing the export into a
    # non-ignored --out dirties the very tree being described -- publishing as
    # false the exact claim the gate exists to protect.
    source = git_describe(_I18N_ROOT)
    pack_licenses = check_license_consistency(locales)

    # Not gated on --push: the card links its banner relatively, so a missing
    # image is a broken picture at the top of the page on EVERY export, not
    # only a published one. Cheaper to fail here than to notice on the Hub.
    require_card_image()

    # Every gate that can run before the export does. An unauthenticated or
    # unapproved run must not leave a fully-built artifact sitting there
    # looking push-ready. All of these read git, the registry or the pack YAML
    # -- none needs a built artifact -- so the export never starts.
    if args.push:
        require_push_approval(args.governance_signoff)
        require_intended_target(args.target_repo)
        require_reproducible_source(source)
        require_license_agreement(pack_licenses)
        preflight_hub_auth()
        # The runbook has always said determinism should be verified for any
        # revision that will be published. A push makes that mechanical rather
        # than remembered.
        args.verify_deterministic = True

    out: Path = args.out
    # Rebuilt from scratch. A folder upload publishes whatever is on disk, so a
    # stale json/<locale>/ left by an earlier run would ship with no manifest
    # entry and no checksum -- a file in the dataset that nothing accounts for.
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    json_files = write_json(out, rows, locales, registry, package_versions)
    terminology_rows = build_pl_terminology(rows)
    packs_rows = build_packs_rows(locales, registry, rows, package_versions)
    vocab_parquet = write_parquet(out, "vocabulary", rows, VOCABULARY_COLUMNS)
    locales_parquet = write_parquet(out, "locales", locale_rows, LOCALE_COLUMNS)
    terminology_parquet = write_parquet(
        out, "pl_terminology", terminology_rows, PL_TERMINOLOGY_COLUMNS
    )
    packs_parquet = write_parquet(out, "packs", packs_rows, PACKS_COLUMNS)

    import pyarrow

    tiers = sorted({r["tier"] for r in locale_rows})

    def build_manifest(
        tree: Path,
        files: list[Path],
        vocab_rows: list[dict[str, Any]],
        loc_rows: list[dict[str, Any]],
        term_rows: list[dict[str, Any]],
        pk_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """The manifest for one exported tree.

        A function rather than a literal so the determinism pass can rebuild it
        for the second tree and compare.

        Both row sets are PARAMETERS, never captured from the enclosing scope.
        Closing over the first pass's rows would make the second manifest a
        partial copy of the first, and the determinism check would then be
        comparing a file against itself -- proving nothing about exactly the
        file it was widened to cover.
        """
        pass_tiers = sorted({r["tier"] for r in loc_rows})
        return {
            # Named from the push target so a rehearsal artifact does not tell its
            # readers to cite the production one.
            "artifact": args.target_repo,
            # This dataset's own version, not any package's. Recorded here as
            # well as stated on the card so a consumer who pulled the files
            # without the card can still tell which release they hold.
            "version": DATASET_VERSION,
            "layer": "packs",
            "description": (
                "The reserved-word vocabulary Legesher's language packs "
                "carry: what a programming language's keywords, builtins and "
                "exceptions are called in each natural language."
            ),
            "source": source,
            "toolchain": {
                "pyarrow": pyarrow.__version__,
                "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                # The library the packs load through. This dataset's version
                # is deliberately not tied to it -- that number moves for
                # library reasons and stands still through pack corrections --
                # so the relationship is recorded rather than encoded, and a
                # reader can still say which library built a given revision.
                "legesher_i18n": legesher_i18n_version(),
            },
            "counts": {
                "locales": len(locales),
                "pl_versions": len(VERSIONS),
                # SOURCE files in the pack tree, not files in this artifact:
                # the artifact's own inventory is the `files` map below. The
                # old name `pack_files` became a dangling number when the JSON
                # mirror went per-pairing (51 files) and stopped equalling it.
                "pack_source_files": len(locales) * len(VERSIONS),
                "vocabulary_rows": len(vocab_rows),
                "pl_terminology_rows": len(term_rows),
                "packs_rows": len(pk_rows),
                # Per target version, because the vocabulary grows with the
                # language: 3.11 adds except* and the two exception-group types,
                # 3.12 adds type. A single "terms per locale" figure would be an
                # average of five different numbers and match none of them.
                "terms_per_locale_by_version": terms_per_version(vocab_rows),
            },
            "tiers_present": pass_tiers,
            "tier_counts": {
                tier: sum(1 for r in loc_rows if r["tier"] == tier)
                for tier in pass_tiers
            },
            # Measured on the emitted rows so the card's normalization note and the
            # manifest cannot disagree, and so neither carries a number that the
            # next pack regeneration silently invalidates.
            "nfkc_unstable": nfkc_instability(vocab_rows),
            "declared_license": DECLARED_LICENSE,
            "pack_metadata_licenses": pack_licenses,
            "categories": list(CATEGORY_FAMILIES),
            "pl_versions": list(VERSIONS),
            "locales": locales,
            "files": {
                str(f.relative_to(tree)): sha256(f)
                for f in sorted(files, key=lambda f: str(f.relative_to(tree)))
            },
        }

    # Copied BEFORE the manifest is built. The manifest is the artifact's own
    # inventory, so a file placed afterwards ships unaccounted for, and the
    # determinism pass reports it as "missing on re-run" rather than as the
    # ordering bug it is.
    banner = copy_card_image(out)

    manifest = build_manifest(
        out,
        [
            vocab_parquet,
            locales_parquet,
            terminology_parquet,
            packs_parquet,
            banner,
            *json_files,
        ],
        rows,
        locale_rows,
        terminology_rows,
        packs_rows,
    )
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        render_card(manifest, pack_licenses, locale_rows, terminology_rows),
        encoding="utf-8",
    )

    print(f"locales:          {len(locales)}")
    print(f"pack source files: {len(locales) * len(VERSIONS)}")
    print(f"vocabulary rows:  {len(rows)}")
    print(f"tiers present:    {', '.join(tiers)}")
    print(f"source commit:    {source['commit'][:12]} ({source['worktree']})")
    print(f"wrote:            {out}")

    if not licenses_agree(pack_licenses):
        rendered = ", ".join(
            f"{name}={count}" for name, count in sorted(pack_licenses.items())
        )
        print(
            f"\nWARNING: the card declares '{DECLARED_LICENSE}' for the "
            f"compilation, but the packs' own metadata.license says: {rendered}.\n"
            f"         Both claims will be public. Decide which is right and "
            f"reconcile before publishing (CORE-1043)."
        )

    if args.verify_deterministic:
        second = out.parent / f"{out.name}-verify"
        if second.exists():
            shutil.rmtree(second)
        second.mkdir(parents=True)
        rows2 = build_rows(locales, registry)
        # Recomputed, not reused: the determinism proof rebuilds every input
        # from scratch, and a cached mapping would let the second pass ride
        # the first pass's reads.
        package_versions2 = {loc: read_package_version(loc) for loc in locales}
        locale_rows2 = build_locale_rows(locales, registry, package_versions2)
        terminology_rows2 = build_pl_terminology(rows2)
        packs_rows2 = build_packs_rows(locales, registry, rows2, package_versions2)
        json2 = write_json(second, rows2, locales, registry, package_versions2)
        v2 = write_parquet(second, "vocabulary", rows2, VOCABULARY_COLUMNS)
        l2 = write_parquet(second, "locales", locale_rows2, LOCALE_COLUMNS)
        t2 = write_parquet(
            second, "pl_terminology", terminology_rows2, PL_TERMINOLOGY_COLUMNS
        )
        pk2 = write_parquet(second, "packs", packs_rows2, PACKS_COLUMNS)
        # The card and the manifest are two of the published file classes this
        # export once got wrong. Leaving anything out of the determinism proof
        # means the operator reads a green line about a surface it never
        # checked, so every file class is in.
        banner2 = copy_card_image(second)
        manifest2 = build_manifest(
            second,
            [v2, l2, t2, pk2, banner2, *json2],
            rows2,
            locale_rows2,
            terminology_rows2,
            packs_rows2,
        )
        m2 = second / "manifest.json"
        m2.write_text(
            json.dumps(manifest2, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        r2 = second / "README.md"
        r2.write_text(
            render_card(manifest2, pack_licenses, locale_rows2, terminology_rows2),
            encoding="utf-8",
        )
        # Keyed on the relative path, never zipped. Zipping two sorted lists
        # silently truncates to the shorter one, so a run that produced FEWER
        # files than the first would still report "deterministic".
        first_map = {
            p.relative_to(out): p
            for p in [
                vocab_parquet,
                locales_parquet,
                terminology_parquet,
                packs_parquet,
                out / "manifest.json",
                out / "README.md",
                banner,
                *json_files,
            ]
        }
        second_map = {
            p.relative_to(second): p for p in [v2, l2, t2, pk2, m2, r2, banner2, *json2]
        }
        only_first = sorted(str(k) for k in first_map.keys() - second_map.keys())
        only_second = sorted(str(k) for k in second_map.keys() - first_map.keys())
        mismatches = sorted(
            str(k)
            for k in first_map.keys() & second_map.keys()
            if sha256(first_map[k]) != sha256(second_map[k])
        )
        if only_first or only_second or mismatches:
            print(
                f"NON-DETERMINISTIC: {len(mismatches)} file(s) differ, "
                f"{len(only_first)} missing on re-run, {len(only_second)} extra"
            )
            for name in (mismatches + only_first + only_second)[:10]:
                print(f"  {name}")
            return 1
        print(f"deterministic:    {len(first_map)} file(s) reproduced identically")

    # Last, and only after determinism proved: a revision that does not
    # reproduce is not one to pin consumers against.
    if args.push:
        push_to_hub(out, args.target_repo)

    return 0


if __name__ == "__main__":
    sys.exit(main())
