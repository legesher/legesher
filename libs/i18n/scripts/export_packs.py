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
governs the Hub commit message, which the publish runbook carries rather than
a test, because this artifact is pushed by hand.

Usage:
    uv run python scripts/export_packs.py --out build/hf-packs
    uv run python scripts/export_packs.py --out build/hf-packs --verify-deterministic

This script NEVER pushes. Publishing is a governance act that belongs to the
release ticket (CORE-1905), not to a script flag.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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

#: Interpreter versions each locale ships a pack for. Mirrors
#: ``verify_pack_regen.EXPECTED_VERSIONS``; the two must agree or the dataset
#: would claim a matrix the regen gate does not certify.
VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")

#: Pack sections, in the order a reader meets them. ``members`` is deliberately
#: absent: it is the MLCP partition for member-bearing targets such as
#: JavaScript (CORE-1372) and is empty for every Python pack. Exporting an
#: always-empty column would advertise a surface this artifact does not cover.
SECTIONS = ("keywords", "builtins", "exceptions", "reserved_words")

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
    _, tag = run("describe", "--tags", "--exact-match")
    status_ok, status = run("status", "--porcelain")

    if not (commit_ok and status_ok):
        worktree = "unknown (git unavailable)"
    else:
        worktree = "dirty" if status else "clean"

    return {
        "commit": commit if commit_ok else "unknown",
        "tag": tag or "(untagged)",
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
                "terms_latest": per_locale_terms[locale],
                "pack_versions": len(VERSIONS),
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


def write_parquet(out: Path, name: str, rows: list[dict[str, Any]]) -> Path:
    """Write one Parquet file with deterministic settings."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    path = out / "data" / f"{name}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows)
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


def render_card(manifest: dict[str, Any], pack_licenses: dict[str, int]) -> str:
    """Render the Hugging Face dataset card.

    Generated, never hand-edited: the card states counts, and a hand-edited
    card is how a count survives the thing it counted changing.
    """
    counts = manifest["counts"]
    locales = manifest["locales"]
    by_version = counts["terms_per_locale_by_version"]
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
    version_rows = "\n".join(
        f"| {version} | {by_version[version]} |" for version in VERSIONS
    )
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

The vocabulary Legesher ships: Python's keywords, builtins, exceptions and
reserved words, rendered in {counts["locales"]} human languages across
{counts["python_versions"]} interpreter versions.

## Corpus, canon, or packs — which one do I want?

{THREE_LAYERS}
Take this dataset if you want the words Legesher ships. Take the canon if you
want the decision and its maturity. Take the corpus if you want the evidence
behind both, including the renderings that were proposed and not chosen.

The corpus is also wider in one respect: it holds a small set of Arabic
renderings of JavaScript concepts, which are out of scope here — `target` is
`python` on every row in this dataset.

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
of them. Endorsements do exist, but they live in the corpus and they are at
contributor rung — one person backing one rendering, which is a data point about
that rendering and not a review of the pack it sits in. Nothing on the review
ladder above `experimental` has been earned yet.

## Contents

| Python | Terms per locale |
| --- | --- |
{version_rows}

The vocabulary grows with the language: 3.11 adds `except*` and the two
exception-group types, 3.12 adds `type`.

### `vocabulary`

One row per (locale, interpreter version, category, source term):

* `locale`, `language_name`, `native_name`, `rtl`
* `target` — always `python` in this release
* `python_version`, `category` (`keywords` / `builtins` / `exceptions` /
  `reserved_words`)
* `source_term` — the English term, e.g. `for`, `ValueError`
* `translation` — the rendering Legesher ships
* `defined_at` — the interpreter version whose pack file defines this term
* `inherited` — true when the term is inherited rather than defined at
  `python_version`
* `tier` — the maturity stamp

Packs for 3.11+ carry only a delta and inherit the rest, so rows are given
**resolved**: `python_version` is what you would actually get on that
interpreter. `defined_at` and `inherited` preserve the delta structure.

### `locales`

One row per shipped locale: identity (`iso639_2`, `bcp47`), script properties
(`rtl`, `has_case_distinction`), `tier`, and term counts.

Join this dataset to the corpus on `bcp47`, not on `locale`: a pack id is not a
locale tag (`no` here is `nb` in the corpus, `zh` is `zh-Hans`), so joining on
the pack id drops exactly the rows that differ.

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

The source is the YAML pack tree, not the selection database. This matters:
the database also holds selections for other targets, and sourcing from it
would publish terminology this artifact does not claim to cover.
{license_note}
## Citation

```bibtex
@misc{{legesher_language_packs,
  title        = {{Legesher Language Packs: Python reserved-word vocabulary in {counts["locales"]} languages}},
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    parser.add_argument(
        "--verify-deterministic",
        action="store_true",
        help="Export twice into separate trees and compare every checksum",
    )
    args = parser.parse_args()

    registry = load_registry()
    locales = pack_locales()
    reconcile_locales(registry, locales)

    rows = build_rows(locales, registry)
    assert_python_only(rows)
    locale_rows = build_locale_rows(locales, registry, rows)

    out: Path = args.out
    # Rebuilt from scratch. A folder upload publishes whatever is on disk, so a
    # stale json/<locale>/ left by an earlier run would ship with no manifest
    # entry and no checksum -- a file in the dataset that nothing accounts for.
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    json_files = write_json(out, rows, locales, registry)
    vocab_parquet = write_parquet(out, "vocabulary", rows)
    locales_parquet = write_parquet(out, "locales", locale_rows)

    import pyarrow

    source = git_describe(_I18N_ROOT)
    tiers = sorted({r["tier"] for r in locale_rows})
    pack_licenses = check_license_consistency(locales)

    # Every locale ships the same term set at a given version, so this is one
    # number per version, not a distribution. Assert that rather than assume
    # it: an uneven locale would make the card's headline count a fiction.
    per_pack: Counter[tuple[str, str]] = Counter(
        (r["locale"], r["python_version"]) for r in rows
    )
    terms_by_version: dict[str, int] = {}
    for version in VERSIONS:
        sizes = {n for (_, v), n in per_pack.items() if v == version}
        if len(sizes) != 1:
            raise SystemExit(
                f"Locales disagree on term count at Python {version}: "
                f"{sorted(sizes)}. The dataset cannot state one number per "
                f"version until they agree."
            )
        terms_by_version[version] = sizes.pop()
    manifest = {
        "artifact": "legesher/language-packs",
        "layer": "canon",
        "description": (
            "The decision layer: the vocabulary Legesher ships in its Python "
            "language packs. The evidence layer is legesher/language-corpus."
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
            "vocabulary_rows": len(rows),
            # Per interpreter version, because the vocabulary grows with the
            # language: 3.11 adds except* and the two exception-group types,
            # 3.12 adds type. A single "terms per locale" figure would be an
            # average of five different numbers and match none of them.
            "terms_per_locale_by_version": terms_by_version,
        },
        "tiers_present": tiers,
        "tier_counts": {
            tier: sum(1 for r in locale_rows if r["tier"] == tier) for tier in tiers
        },
        # Measured on the emitted rows so the card's normalization note and the
        # manifest cannot disagree, and so neither carries a number that the
        # next pack regeneration silently invalidates.
        "nfkc_unstable": nfkc_instability(rows),
        "declared_license": DECLARED_LICENSE,
        "pack_metadata_licenses": pack_licenses,
        "categories": list(SECTIONS),
        "python_versions": list(VERSIONS),
        "locales": locales,
        "files": {
            str(p.relative_to(out)): sha256(p)
            for p in sorted(
                [vocab_parquet, locales_parquet, *json_files],
                key=lambda p: str(p.relative_to(out)),
            )
        },
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        render_card(manifest, pack_licenses), encoding="utf-8"
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
        json2 = write_json(second, rows2, locales, registry)
        v2 = write_parquet(second, "vocabulary", rows2)
        l2 = write_parquet(
            second, "locales", build_locale_rows(locales, registry, rows2)
        )
        # Keyed on the relative path, never zipped. Zipping two sorted lists
        # silently truncates to the shorter one, so a run that produced FEWER
        # files than the first would still report "deterministic".
        first_map = {
            p.relative_to(out): p for p in [vocab_parquet, locales_parquet, *json_files]
        }
        second_map = {p.relative_to(second): p for p in [v2, l2, *json2]}
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
