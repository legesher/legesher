#!/usr/bin/env python3
"""Emit the client-shape LanguagePack artifact for a JavaScript-target locale.

CORE-1371 step 3 (client half). Reads the canonical selections from
``translations.db`` (``selected_translations``, the CORE-1400 publish layer)
for ``programming_language='javascript'`` and renders the ``@legesher/core``
``LanguagePack`` shape as a generated TypeScript module, ready to vendor into
the JavaScript engine repository's ``packages/packs/src/packs/<locale>.ts``.

Contract:

- The DB is the single source of truth; the emitted file carries a
  DO-NOT-EDIT header and the source commit. Corrections go upstream to the
  generation layer and re-emit — never edits to the artifact.
- Fail-loud completeness (CORE-1400 rule 4): every seeded term must have a
  selection; a partial pack is never emitted.
- Metadata is registry-driven: locale (bcp47), direction, numeral system
  (DB vocabulary mapped to the CLDR numbering-system id the client/Intl
  APIs speak), and stability from ``languages.status``.
- Deterministic output: alphabetical term order, no timestamps — the same
  DB state emits byte-identical artifacts.

Usage:
    uv run python scripts/emit_js_client_pack.py --out /path/to/ar.ts \\
        [--language ar] [--db-path PATH] [--pack-version 0.1.0] \\
        [--source-commit SHA]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from legesher_i18n.db.database import TranslationDatabase  # noqa: E402

TARGET = "javascript"
EXPECTED_SPLIT = {"keyword": 17, "builtin": 16, "member": 29}
CATEGORY_TO_PARTITION = {
    "keyword": "keywords",
    "builtin": "builtins",
    "member": "members",
}
#: DB ``languages.numeral_system`` vocabulary -> CLDR numbering-system id
#: (what ``Intl.NumberFormat`` and the editor layer speak). Extend as
#: locales are added; unknown values fail loud rather than guess.
NUMERAL_SYSTEM_CLDR = {
    "arabic_indic": "arab",
    "western": "latn",
    "latin": "latn",
}

HEADER = """\
// GENERATED FILE — DO NOT EDIT. Pack data is generated in the Legesher
// monorepo (the source of truth) and only consumed here; corrections go
// upstream to the generation layer and are re-emitted (CORE-1371).
// Generator: legesher libs/i18n/scripts/emit_js_client_pack.py
// Source: translations.db selected_translations ({language}/{target})
//         @ legesher {source_commit}
"""


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def repo_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def check_value(term: str, value: str) -> str | None:
    """Defense-in-depth re-check of the publish-gate invariants."""
    if "ـ" in value or "‌" in value or "‍" in value:
        return f"{term}: forbidden codepoint in {value!r}"
    if unicodedata.normalize("NFKC", value) != value:
        return f"{term}: {value!r} is not an NFKC fixed point"
    if not value.isidentifier():
        return f"{term}: {value!r} is not a valid identifier"
    return None


def render(
    language: str,
    metadata: dict[str, str],
    partitions: dict[str, dict[str, str]],
    source_commit: str,
) -> str:
    const_name = f"{language.upper().replace('-', '_')}_PACK"
    lines = [
        HEADER.format(language=language, target=TARGET, source_commit=source_commit),
        "import type { LanguagePack } from '@legesher/core';",
        "",
        "/**",
        f" * Generated {metadata['_name']} pack for the JavaScript (JEJ) target —",
        " * 17 keywords / 16 builtins / 29 members, bare (unvocalized) forms.",
        " * Experimental: the trial is the review mechanism; revisions flow",
        " * through the monorepo generation layer, never edits here.",
        " */",
        f"const {const_name}: LanguagePack = Object.freeze({{",
        "  metadata: Object.freeze({",
        f"    locale: '{metadata['locale']}',",
        f"    target: '{TARGET}',",
        f"    direction: '{metadata['direction']}',",
        f"    packVersion: '{metadata['pack_version']}',",
        f"    numeralSystem: '{metadata['numeral_system']}',",
        f"    stability: '{metadata['stability']}',",
        "  }),",
    ]
    for partition in ("keywords", "builtins", "members"):
        lines.append(f"  {partition}: Object.freeze({{")
        for term in sorted(partitions[partition]):
            lines.append(f"    {term}: '{partitions[partition][term]}',")
        lines.append("  }),")
    lines.extend(
        [
            "});",
            "",
            f"export default {const_name};",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", default="ar")
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pack-version", default="0.1.0")
    parser.add_argument(
        "--source-commit",
        default=None,
        help="legesher commit recorded in the header (default: HEAD)",
    )
    args = parser.parse_args()

    db = (
        TranslationDatabase(db_path=str(args.db_path))
        if args.db_path
        else TranslationDatabase()
    )
    try:
        language_row = db.get_language(args.language)
        if language_row is None:
            return fail(f"language {args.language!r} not in the languages registry")
        numeral_db = language_row.get("numeral_system")
        if numeral_db not in NUMERAL_SYSTEM_CLDR:
            return fail(
                f"no CLDR mapping for numeral_system {numeral_db!r} — "
                f"extend NUMERAL_SYSTEM_CLDR deliberately"
            )
        terms = db.get_terms(programming_language=TARGET)
        if not terms:
            return fail(f"no {TARGET} terms seeded (run seed_js_terms.py)")
        selected = {
            s["term_id"]: s["translation"]
            for s in db.get_all_selected(language_code=args.language)
        }
        partitions: dict[str, dict[str, str]] = {
            p: {} for p in CATEGORY_TO_PARTITION.values()
        }
        unselected: list[str] = []
        problems: list[str] = []
        for term in terms:
            value = selected.get(term["id"])
            if value is None:
                unselected.append(term["name"])
                continue
            problem = check_value(term["name"], value)
            if problem:
                problems.append(problem)
            partition = CATEGORY_TO_PARTITION.get(term["category"])
            if partition is None:
                problems.append(
                    f"{term['name']}: unmapped category {term['category']!r}"
                )
                continue
            partitions[partition][term["name"]] = value
        if unselected:
            return fail(
                f"{len(unselected)} term(s) unselected for "
                f"{args.language!r} — a partial pack is never emitted "
                f"(CORE-1400 rule 4): {sorted(unselected)[:5]}…"
            )
        if problems:
            for problem in problems:
                print(f"GATE FAIL: {problem}", file=sys.stderr)
            return 1
        split = {
            category: len(partitions[partition])
            for category, partition in CATEGORY_TO_PARTITION.items()
        }
        if split != EXPECTED_SPLIT:
            return fail(f"partition split {split} != expected {EXPECTED_SPLIT}")

        stability = language_row.get("status") or "experimental"
        if stability not in ("experimental", "stable"):
            return fail(
                f"languages.status {stability!r} is outside the client "
                f"PackMetadata stability union ('experimental' | 'stable') — "
                f"map it deliberately before emitting"
            )
        metadata = {
            "_name": language_row["name"],
            "locale": language_row.get("bcp47") or args.language,
            "direction": language_row["direction"],
            "numeral_system": NUMERAL_SYSTEM_CLDR[numeral_db],
            "stability": stability,
            "pack_version": args.pack_version,
        }
        source_commit = args.source_commit or repo_head()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            render(args.language, metadata, partitions, source_commit),
            encoding="utf-8",
        )
        print(
            f"Emitted {sum(len(p) for p in partitions.values())} terms "
            f"({args.language}/{TARGET}) -> {args.out}"
        )
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
