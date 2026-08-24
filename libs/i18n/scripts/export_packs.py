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
terminology *labelled by target*, asserting a level of review that population
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
path the runtime uses -- rather than by re-implementing the merge here. Rows
record whether a term was defined at that version or inherited, so the delta
structure survives the flattening instead of being erased by it.

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
* a ``language-packs-v*`` tag on that commit -- the one version string the Hub
  revision, the release ticket and the card's provenance line share. Checked
  against the prefix, not merely "is there a tag": this repo tags releases
  ``v0.24.0`` and packs ``i18n-python-ar-v0.0.4``, and neither names a revision
  of this dataset
* agreement between the declared compilation licence and the packs' own
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

from legesher_i18n.pack_loader import LanguagePackLoader  # noqa: E402

PACKS_DIR = _I18N_ROOT / "language-packs" / "python"
REGISTRY = _I18N_ROOT / "legesher_i18n" / "languages.json"

#: Where a push goes unless a second key says otherwise.
DEFAULT_TARGET_REPO = "legesher/language-packs"

#: What the manifest records when ``git describe`` finds no tag on the commit.
UNTAGGED = "(untagged)"

#: Tag shape a published revision is expected to carry, e.g.
#: ``language-packs-v2026.08.24``. The date is the version the Hub revision,
#: the release ticket and the card's provenance line all say.
TAG_PREFIX = "language-packs-v"

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
)

#: Published columns, per config (CORE-1986). The row dicts built in memory
#: carry more than this on purpose -- ``assert_python_only`` needs ``target``,
#: ``nfkc_instability`` and the card need ``language_name`` -- so the published
#: schema is a projection applied at write time rather than a restructuring of
#: the builders. It is also then one list to read when asking "what does this
#: dataset expose", instead of an argument reconstructed from three functions.
#:
#: What was dropped and why: ``language_name``, ``native_name`` and ``rtl`` are
#: functionally dependent on ``locale`` and already in ``locales``; ``target``
#: is ``python`` on every row; ``tier`` belongs in ``locales`` alone, where it
#: is designed to vary -- carrying it here too means a promotion rewrites 912
#: vocabulary rows and one locales row, which is two places to drift.
VOCABULARY_COLUMNS: tuple[str, ...] = (
    "locale",
    "python_version",
    "category",
    "source_term",
    "translation",
    "defined_at",
    "inherited",
)

#: ``terms_latest`` and ``pack_versions`` are gone: the first was a cached
#: aggregate of the ``vocabulary`` config in the same dataset, the second was
#: ``len(VERSIONS)`` on every row -- a property of the dataset, not the locale.
#:
#: ``package_version`` replaces them with the number that actually varies and
#: actually matters: the semver of THIS locale's distributable, so a reader can
#: line a Hub revision up against PyPI without guessing.
LOCALE_COLUMNS: tuple[str, ...] = (
    "locale",
    "language_name",
    "native_name",
    "iso639_2",
    "bcp47",
    "rtl",
    "has_case_distinction",
    "tier",
    "package_version",
)

#: Interpreter versions each locale ships a pack for. Mirrors
#: ``verify_pack_regen.EXPECTED_VERSIONS``; the two must agree or the dataset
#: would claim a matrix the regen gate does not certify.
VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")

#: Pack sections, in the order a reader meets them. ``members`` is deliberately
#: absent: it is the MLCP partition for member-bearing targets such as
#: JavaScript (CORE-1372) and is empty for every Python pack. Exporting an
#: always-empty column would advertise a surface this artifact does not cover.
SECTIONS = ("keywords", "builtins", "exceptions", "reserved_words")

#: One line per category, for the card. Keyed by :data:`SECTIONS` so a partition
#: added for another target cannot reach the card undescribed -- the render
#: raises rather than printing a bare name a reader cannot interpret.
CATEGORY_BLURBS: dict[str, str] = {
    "keywords": (
        "The words the grammar reserves. A parser recognises these, so a "
        "rendering has to be a legal identifier and cannot collide with "
        "anything else in the vocabulary."
    ),
    "builtins": (
        "Functions and types available without importing anything — `print`, "
        "`len`, `dict`. Callable names rather than grammar."
    ),
    "exceptions": (
        "The error hierarchy. These reach a reader at the worst moment, in a "
        "traceback, which is where reading your own language matters most."
    ),
    "reserved_words": (
        "Names the language treats as special without reserving them in the "
        "grammar — soft keywords and contextual forms."
    ),
}

#: The only target this artifact covers. Asserted against every emitted row.
TARGET = "python"

#: SPDX identifier declared for the published compilation. Matches the monorepo
#: LICENSE, ``libs/i18n/pyproject.toml``, all 51 per-pack ``pyproject.toml``
#: files, and — since CORE-1043 — every pack's own ``metadata.license``.
#:
#: The in-pack field said ``MIT`` on all 255 files until then, contradicting the
#: distribution that shipped them. :func:`check_license_consistency` keeps the
#: two claims from drifting apart again: both are public, and a card asserting
#: one licence over rows asserting another is not a discrepancy anyone should
#: find after the fact.
DECLARED_LICENSE = "apache-2.0"

#: The three layers, in one wording. The dataset cards, the site (CORE-1930),
#: the language-support page (CORE-1929) and the announcement (HOME-44) all
#: have to state this, and near-miss paraphrases of the same idea read worse
#: than one sentence repeated. This is the sentence.
#:
#: It became three-way on 2026-08-19, when the canon shipped as its own dataset
#: and stopped being a second name for this one. The middle layer had always
#: existed conceptually; until then it had no artifact, so the split was
#: written as two.
THREE_LAYERS = """\
**The corpus is the evidence; the canon is the decision; the packs are what
ships.**
[`legesher/language-corpus`](https://huggingface.co/datasets/legesher/language-corpus)
records every rendering anyone proposed for a programming concept, append-only,
with the endorsements attached.
[`legesher/language-canon`](https://huggingface.co/datasets/legesher/language-canon)
records which rendering was selected for each concept in each language, and how
much review stands behind that choice. **This** dataset is the vocabulary those
decisions produce: what you get when you write `import legesher`.
"""


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
    directory listing counts it as a 52nd locale. It is not one.
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
    whose pack file supplies the value SEEN ON THIS ROW, and ``inherited`` is
    the derived flag, so the delta structure the pack tree encodes is still
    legible after flattening.

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
            for section in SECTIONS:
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
            for section in SECTIONS:
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
                            "python_version": version,
                            "category": section,
                            "source_term": term,
                            "translation": str(translation),
                            "defined_at": origin,
                            "inherited": origin != version,
                            "tier": meta.get("status"),
                            "rtl": bool(meta.get("rtl", False)),
                        }
                    )

    rows.sort(
        key=lambda r: (
            r["locale"],
            r["python_version"],
            SECTIONS.index(r["category"]),
            r["source_term"],
        )
    )
    return rows


def _read_yaml(path: Path) -> dict[str, Any]:
    import yaml

    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def terms_per_version(rows: list[dict[str, Any]]) -> dict[str, int]:
    """One term count per interpreter version.

    Every locale ships the same term set at a given version, so this is one
    number per version, not a distribution. Asserted rather than assumed: an
    uneven locale would make the card's headline count a fiction.

    Raises:
        SystemExit: if locales disagree at any version.
    """
    per_pack: Counter[tuple[str, str]] = Counter(
        (r["locale"], r["python_version"]) for r in rows
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
    this dataset on a release date, each pack on its own semver -- and nothing
    states which pack version a given revision actually describes.

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


def build_locale_rows(
    locales: list[str], registry: dict[str, Any], rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """One row per shipped locale: identity, tier, and derived term counts.

    Counts are DERIVED from the exported vocabulary rows, never stored
    separately, so the headline number on the card is reproducible from the
    rows a consumer downloads instead of being asserted at them.
    """
    per_locale_terms: Counter[str] = Counter()
    for row in rows:
        if row["python_version"] == VERSIONS[-1]:
            per_locale_terms[row["locale"]] += 1

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
                "tier": meta.get("status"),
                "package_version": read_package_version(locale),
                # Kept on the in-memory row for the card's headline count, and
                # projected out of the published table by LOCALE_COLUMNS: it is
                # derivable from the vocabulary config sitting beside it.
                "terms_latest": per_locale_terms[locale],
            }
        )
    out.sort(key=lambda r: r["locale"])
    return out


def nfkc_instability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe the NFKC-unstable renderings in the emitted vocabulary.

    Python normalises identifiers to NFKC at parse time (PEP 3131), so a
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
            f"non-Python selections must not be published labelled by target "
            f"(CORE-1913)."
        )


def write_json(
    out: Path,
    rows: list[dict[str, Any]],
    locales: list[str],
    registry: dict[str, Any],
) -> list[Path]:
    """Write the resolved pack per (locale, version) as JSON.

    Sorted keys and a trailing newline, so the bytes are stable and the files
    diff cleanly between revisions -- the point of a pinned artifact is that
    two revisions can be compared.
    """
    written: list[Path] = []
    by_key: dict[tuple[str, str], dict[str, dict[str, str]]] = {}
    for row in rows:
        bucket = by_key.setdefault((row["locale"], row["python_version"]), {})
        bucket.setdefault(row["category"], {})[row["source_term"]] = row["translation"]

    for locale in locales:
        for version in VERSIONS:
            payload = {
                "locale": locale,
                "target": TARGET,
                "python_version": version,
                # From the registry, not a scan of the row list: a locale that
                # contributed no rows would make a generator scan raise a bare
                # StopIteration halfway through writing the tree.
                "tier": registry[locale].get("status"),
                **{
                    section: dict(
                        sorted(
                            by_key.get((locale, version), {}).get(section, {}).items()
                        )
                    )
                    for section in SECTIONS
                },
            }
            path = out / "json" / locale / f"{version}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
                + "\n",
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
    claims and they are allowed to differ in principle -- a compilation licence
    is not the licence of every part. What is NOT acceptable is publishing a
    card that asserts one licence while every row's own metadata asserts
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
    """Do the packs' own licence fields agree with the declared licence?

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
        "Python normalises identifiers to NFKC when it parses them (PEP 3131). "
        "A rendering whose own NFKC form differs from it is therefore typed one "
        "way and resolved another: the bytes in your source file and the bytes "
        "of the name the interpreter binds are not the same, though they are the "
        "same identifier."
    )

    renderings = nfkc.get("renderings", 0)
    if not renderings:
        return (
            f"{preamble}\n\nNo rendering in this release is NFKC-unstable, so "
            f"every `translation` value here is byte-identical to the name it "
            f"binds."
        )

    locales = nfkc.get("locales") or []
    characters = nfkc.get("characters") or []
    who = ", ".join(f"{item['language_name']} (`{item['locale']}`)" for item in locales)
    which = ", ".join(f"`{item['codepoint']}` {item['name']}" for item in characters)
    count = f"{renderings} renderings" if renderings != 1 else "One rendering"
    verb = "are" if renderings != 1 else "is"
    only = "the same character" if len(characters) == 1 else "the same few characters"

    return (
        f"{preamble}\n\n"
        f"{count} in this release {verb} NFKC-unstable, all in {who}, and all "
        f"through {only}: {which}. Nothing else in the vocabulary is affected. "
        f"The figure is measured over the rows this release actually contains, "
        f"not asserted, so it moves when the packs do. If you compare a "
        f"`translation` value against a name taken from a running interpreter, "
        f"normalise both to NFKC first."
    )


def render_card(
    manifest: dict[str, Any],
    pack_licenses: dict[str, int],
    locale_rows: list[dict[str, Any]],
) -> str:
    """Render the Hugging Face dataset card.

    Generated, never hand-edited: the card states counts, and a hand-edited
    card is how a count survives the thing it counted changing.
    """
    counts = manifest["counts"]
    locales = manifest["locales"]
    src = manifest["source"]

    # Quoted, always. Unquoted, YAML 1.1 reads `no` as boolean false, which is
    # how Norwegian silently disappears from the Hub's language facet.
    lang_yaml = "\n".join(f'  - "{code}"' for code in locales)

    # Derived from what the artifact actually stamps. Hard-coding "every pack
    # is experimental" would survive the first promotion and publish a card
    # that contradicts its own `tier` column — the failure this function is
    # generated to prevent.
    tiers_present: list[str] = manifest["tiers_present"]
    tier_counts: dict[str, int] = manifest.get("tier_counts") or {}
    if tiers_present == ["experimental"]:
        tier_paragraph = (
            f"All {counts['locales']} locales are stamped **`experimental`**, and "
            f"that is not a formality — it is the honest state of the work. "
        )
        promotion_note = (
            "Nothing has been promoted yet, so no pack in this release carries "
            "`reviewed` or `official`. "
        )
    else:
        spread = ", ".join(
            f"**{tier_counts.get(tier, 0)}** `{tier}`" for tier in tiers_present
        )
        tier_paragraph = (
            f"Across {counts['locales']} locales: {spread}. Each stamp is the "
            f"honest state of that pack. "
        )
        promotion_note = ""
    # Listed out the way the canon and corpus cards list theirs: the frontmatter
    # rollup is what the Hub indexes, this is what a reader actually reads.
    language_rows = "\n".join(
        f"| `{r['locale']}` | {r['language_name']} | {r['native_name']} "
        f"| `{r['tier']}` | `{r['package_version']}` |"
        for r in locale_rows
    )
    tier_spread = ", ".join(
        f"**{tier_counts.get(tier, 0)}** at `{tier}`" for tier in tiers_present
    )
    category_rows = "\n".join(
        f"| `{name}` | {CATEGORY_BLURBS[name]} |" for name in SECTIONS
    )
    target_versions = ", ".join(f"`{v}`" for v in VERSIONS)
    normalization_section = render_normalization(manifest.get("nfkc_unstable") or {})
    license_note = ""
    if not licenses_agree(pack_licenses):
        rendered = ", ".join(
            f"`{name}` ({count} files)" for name, count in sorted(pack_licenses.items())
        )
        license_note = (
            f"\n> **Note on the licence field inside the packs.** The pack files "
            f"carry their own `metadata.license`, currently {rendered}, while "
            f"this dataset and the `legesher-i18n` package are "
            f"`{DECLARED_LICENSE}`. The compilation licence above is the one "
            f"that governs this dataset; the in-pack field is being "
            f"reconciled.\n"
        )

    return f"""\
---
license: {DECLARED_LICENSE}
tags:
  - multilingual
  - code
  - programming
  - localization
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
---

# Legesher Language Packs

A **language pack** is what a programming language's reserved words are called
in one natural language.

Every word a programming language reserves — its keywords, its builtins, its
exception hierarchy — rendered in a natural language, in a form that language's
own script and grammar accept as an identifier. A developer who does not read
English memorises `def` and `ValueError` as shapes; a pack lets them read the
words instead.

A pack is what the tooling loads: the terminology settled, resolved into the
structure its target programming language needs, and stamped with how much
review stands behind it.

This release carries {counts["locales"]} natural languages.

## Languages

Every language in this export, with where it sits on the maturity ladder and
the version of its own package. The primary-subtag rollup in the frontmatter is
what the Hub indexes for search; this is the full list.

| Pack | Language | Native name | Status | Package |
| --- | --- | --- | --- | --- |
{language_rows}

Today: {tier_spread}.

The `locales` config carries this same list, so you can sort and filter it
rather than read it.

## What a pack is made of

### Target

Every pack targets **one programming language**, and the target is what decides
the pack's shape: which categories exist, what counts as a reserved word, and
which forms a rendering is allowed to take. One settled term is rendered
differently for different targets, because each programming language's grammar
admits different identifiers.

**This release ships the `python` target**, across
{counts["python_versions"]} interpreter versions ({target_versions}).
Selections exist internally for other targets and are deliberately excluded:
exporting them would publish terminology labelled by a target it has not been
reviewed for.

### Categories

Terminology is partitioned, and the partitions are the target's, not ours:

| Category | What it holds |
| --- | --- |
{category_rows}

### Versions

A target moves, and its vocabulary moves with it. Packs for later versions
carry only what changed and inherit the rest, so a pack is a delta over its
base rather than a full copy.

The rows in this dataset are given **resolved**: each one states what you would
actually get on that version, with the delta structure preserved alongside it
rather than erased by the flattening.

### What is not here

The **style guide** — the rules that govern how a rendering is formed for a
language, such as how multi-word terms are joined — is a separate system and is
not exported in this dataset. A pack is the result those rules produced, not
the rules themselves.

## Maturity

{tier_paragraph}The ladder:

| Stage | What it means |
| --- | --- |
| `experimental` | Machine-drafted, then curated by maintainers and passed through the mechanical gates: identifier validity, cross-section collision checks, Unicode normalization, and a regeneration check proving the packs match their source of truth. **No native speaker has signed off.** |
| `reviewed` | A native speaker of the language has reviewed the pack and signed off on it. |
| `official` | Certified review plus term screening. |

{promotion_note}**What exactly moves a language from `experimental` to
`reviewed` — how many endorsements, from how varied a set of voices — is still
being defined.** Treat an `experimental` pack as a serious starting point that
wants native review, not as settled terminology.

### Who chose these words

Every rendering here was drafted by a language model and then curated by
Legesher's maintainers, who kept it, replaced it, or rewrote it. That is the
whole provenance: no pack in this release has been signed off by a native
speaker of its language, and none of the maintainers is a native speaker of most
of them. Nothing on the review ladder above `experimental` has been earned yet.

## The dataset

### `vocabulary`

One row per (locale, interpreter version, category, source term):

* `locale` — join key into `locales`, which carries the language's names,
  script direction and maturity
* `python_version`, `category` (`keywords` / `builtins` / `exceptions` /
  `reserved_words`)
* `source_term` — the English term, e.g. `for`, `ValueError`
* `translation` — the rendering Legesher ships
* `defined_at` — the interpreter version whose pack file defines this term
* `inherited` — true when the term is inherited rather than defined at
  `python_version`

`defined_at` and `inherited` are what preserve the delta structure through the
resolution described above.

Everything true of a language rather than of a row lives in `locales` and is
joined, not repeated. `target` is not a column: every row in this release is
Python.

### `locales`

One row per shipped locale: identity (`iso639_2`, `bcp47`), script properties
(`rtl`, `has_case_distinction`), `tier`, and `package_version`.

`package_version` is the semver of that language's own distributable, and it is
how you line this dataset up against the packages: a row reading
`ar` / `0.0.4` means these are the words in `legesher-i18n-python-ar==0.0.4`.
Each language versions on its own clock, because each is corrected and promoted
on its own — so there is no single "pack version" for the set, and this column
is the per-language answer instead.

**`locale` is a pack id, not a language tag.** Where the two differ, `locale` is
the shorter form: `no` is BCP 47 `nb`, `zh` is `zh-Hans`, `sr` is `sr-Cyrl`.
Join to anything keyed by language tag on `bcp47`, or you drop exactly the rows
that differ.

### JSON

`json/<locale>/<version>.json` mirrors the resolved pack for consumers that
would rather not read Parquet.

## Normalization

{normalization_section}

## Provenance

Generated from the pack tree at monorepo commit `{src["commit"][:12]}`
(`{src["tag"]}`) by `libs/i18n/scripts/export_packs.py`. Not hand-edited, and
regenerable: `manifest.json` carries a SHA-256 for every file and names the
toolchain that produced them.

The source is the YAML pack tree, not the selection database. This matters: the
database also holds selections for targets this release does not cover, and
sourcing from it would publish terminology labelled by a target it has not been
reviewed for.
{license_note}
## Citation

```bibtex
@misc{{legesher_language_packs,
  title        = {{Legesher Language Packs: programming vocabulary rendered in {counts["locales"]} natural languages}},
  author       = {{Legesher}},
  year         = {{2026}},
  publisher    = {{Hugging Face}},
  howpublished = {{\\url{{https://huggingface.co/datasets/legesher/language-packs}}}}
}}
```

## Licence

`{DECLARED_LICENSE}`, matching the `legesher-i18n` package the packs ship in.
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
    # Checked against the prefix, not merely against "is there a tag". A
    # release commit here routinely carries `v0.24.0` and a per-pack
    # `i18n-python-ar-v0.0.4` as well; accepting any of them would stamp a
    # version string this dataset does not have, which is the failure this
    # gate exists to prevent rather than a near-miss of it.
    if not tag.startswith(TAG_PREFIX):
        raise ExportRefused(
            f"PUSH REFUSED: commit {source.get('commit', 'unknown')[:12]} "
            f"carries no {TAG_PREFIX}* tag (found {tag!r}), so the card's "
            f"provenance would name no version this dataset shares with its "
            f"release. Tag first, e.g. `git tag {TAG_PREFIX}<YYYY.MM.DD>`, "
            f"then re-run."
        )


def require_license_agreement(pack_licenses: dict[str, int]) -> None:
    """Refuse to push while the declared and per-pack licences disagree.

    "Reconcile before publishing" is what the export has always printed here.
    On a push that is a gate, not advice: both claims become public in the same
    revision, and a reader has no way to tell which one is load-bearing.

    Reads only the pack YAML, so it belongs with the pre-export gates rather
    than after the artifact is built.

    Raises:
        ExportRefused: if the compilation licence and the packs disagree.
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
    locale_rows = build_locale_rows(locales, registry, rows)

    # ONE snapshot, taken before anything is written and reused for both the
    # gate and the manifest. Two calls would let the gate pass on a clean tree
    # and the manifest then record `dirty`, because writing the export into a
    # non-ignored --out dirties the very tree being described -- publishing as
    # false the exact claim the gate exists to protect.
    source = git_describe(_I18N_ROOT)
    pack_licenses = check_license_consistency(locales)

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

    json_files = write_json(out, rows, locales, registry)
    vocab_parquet = write_parquet(out, "vocabulary", rows, VOCABULARY_COLUMNS)
    locales_parquet = write_parquet(out, "locales", locale_rows, LOCALE_COLUMNS)

    import pyarrow

    tiers = sorted({r["tier"] for r in locale_rows})

    def build_manifest(
        tree: Path,
        files: list[Path],
        vocab_rows: list[dict[str, Any]],
        loc_rows: list[dict[str, Any]],
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
            },
            "counts": {
                "locales": len(locales),
                "python_versions": len(VERSIONS),
                "pack_files": len(locales) * len(VERSIONS),
                "vocabulary_rows": len(vocab_rows),
                # Per interpreter version, because the vocabulary grows with the
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
            "categories": list(SECTIONS),
            "python_versions": list(VERSIONS),
            "locales": locales,
            "files": {
                str(f.relative_to(tree)): sha256(f)
                for f in sorted(files, key=lambda f: str(f.relative_to(tree)))
            },
        }

    manifest = build_manifest(
        out, [vocab_parquet, locales_parquet, *json_files], rows, locale_rows
    )
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        render_card(manifest, pack_licenses, locale_rows), encoding="utf-8"
    )

    print(f"locales:          {len(locales)}")
    print(f"pack files:       {len(locales) * len(VERSIONS)}")
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
        locale_rows2 = build_locale_rows(locales, registry, rows2)
        json2 = write_json(second, rows2, locales, registry)
        v2 = write_parquet(second, "vocabulary", rows2, VOCABULARY_COLUMNS)
        l2 = write_parquet(second, "locales", locale_rows2, LOCALE_COLUMNS)
        # The card and the manifest are two of the four published file classes,
        # and the two this export most recently got wrong. Leaving them out of
        # the determinism proof means the operator reads a green line about a
        # surface it never checked.
        manifest2 = build_manifest(second, [v2, l2, *json2], rows2, locale_rows2)
        m2 = second / "manifest.json"
        m2.write_text(
            json.dumps(manifest2, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        r2 = second / "README.md"
        r2.write_text(
            render_card(manifest2, pack_licenses, locale_rows2), encoding="utf-8"
        )
        # Keyed on the relative path, never zipped. Zipping two sorted lists
        # silently truncates to the shorter one, so a run that produced FEWER
        # files than the first would still report "deterministic".
        first_map = {
            p.relative_to(out): p
            for p in [
                vocab_parquet,
                locales_parquet,
                out / "manifest.json",
                out / "README.md",
                *json_files,
            ]
        }
        second_map = {p.relative_to(second): p for p in [v2, l2, m2, r2, *json2]}
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
