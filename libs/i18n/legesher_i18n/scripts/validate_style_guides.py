#!/usr/bin/env python3
"""Validate the per-language style guides against ``_schema.json`` + languages.json.

Checks each ``{code}.yml`` guide (not the ``python.yml`` base or the ``_*.yml``
overlays) for:

1. **Structure** — the required keys, the exact ``supports`` flag set, and the
   enum-valued fields, read from ``_schema.json`` so the two stay in sync.
2. **Consistency with languages.json** (the single source of truth):
   ``supports.case_distinction`` matches ``has_case_distinction``; the
   case-dependent flags (``upper_snake_case`` / ``pascal_case`` / ``camel_case``)
   are ``false`` for a caseless script; ``script.direction`` matches ``rtl``.
3. **Resolvable chain** — every file named in ``extends`` exists.

Exits non-zero when any guide has a problem. Zero == all guides valid.

Usage::

    python -m legesher_i18n.scripts.validate_style_guides
    python -m legesher_i18n.scripts.validate_style_guides --lang te
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from legesher_i18n.style_guides import StyleGuideLoader

_LANG_CODE_RE = re.compile(r"^[a-z]{2,3}$")
_STYLE_GUIDES_DIR = Path(__file__).resolve().parents[2] / "style-guides"
_LANGUAGES_JSON = Path(__file__).resolve().parents[1] / "languages.json"
_SCHEMA = _STYLE_GUIDES_DIR / "_schema.json"

_CASE_DEPENDENT = ("upper_snake_case", "pascal_case", "camel_case")


def _enums(schema: dict) -> dict[str, list[str]]:
    """Pull the enum-constrained leaf fields we enforce, from the schema."""
    props = schema["properties"]
    return {
        "status": props["status"]["enum"],
        "naming.case_substitute": props["naming"]["properties"]["case_substitute"][
            "enum"
        ],
        "script.direction": props["script"]["properties"]["direction"]["enum"],
        "formatting.programming_punctuation": props["formatting"]["properties"][
            "programming_punctuation"
        ]["enum"],
    }


def _validate_guide(
    code: str, guide: dict, schema: dict, meta: dict, loader: StyleGuideLoader
) -> list[str]:
    problems: list[str] = []

    # 1. Required top-level keys.
    for key in schema["required"]:
        if key not in guide:
            problems.append(f"missing required key '{key}'")
    if problems:
        return problems  # structure too broken to check the rest

    # 1a0. language must equal the filename code. Catches the YAML 1.1 boolean
    #      trap (`language: no` → PyYAML reads False) and any code/filename drift.
    if guide.get("language") != code:
        problems.append(
            f"language is {guide.get('language')!r}, expected {code!r} "
            "(quote codes like 'no' so PyYAML keeps them strings)"
        )

    # 1a. supports: exactly the schema's flag set, all booleans.
    want = set(schema["properties"]["supports"]["required"])
    got = set(guide["supports"])
    if got != want:
        if want - got:
            problems.append(f"supports missing flags: {sorted(want - got)}")
        if got - want:
            problems.append(f"supports has unknown flags: {sorted(got - want)}")
    for flag, val in guide["supports"].items():
        if flag in want and not isinstance(val, bool):
            problems.append(f"supports.{flag} must be a boolean, got {val!r}")

    # 1b. Enum fields.
    def _leaf(dotted: str):
        node = guide
        for part in dotted.split("."):
            node = node.get(part, {}) if isinstance(node, dict) else {}
        return node

    for dotted, allowed in _enums(schema).items():
        val = _leaf(dotted)
        if val not in allowed:
            problems.append(f"{dotted} = {val!r} not in {allowed}")

    # 2. Consistency with languages.json.
    s = guide["supports"]
    if s.get("case_distinction") != meta["has_case_distinction"]:
        problems.append(
            f"supports.case_distinction ({s.get('case_distinction')}) != "
            f"languages.json has_case_distinction ({meta['has_case_distinction']})"
        )
    if not meta["has_case_distinction"]:
        for flag in _CASE_DEPENDENT:
            if s.get(flag):
                problems.append(f"caseless script: supports.{flag} must be false")
    want_dir = "rtl" if meta["rtl"] else "ltr"
    if guide["script"]["direction"] != want_dir:
        problems.append(
            f"script.direction ({guide['script']['direction']}) != "
            f"languages.json rtl-implied direction ({want_dir})"
        )

    # 3. Every file named in ``extends`` (the declared base → … → family chain)
    #    exists. Checked directly against the guide's declared list rather than
    #    through the loader, so it catches a missing overlay regardless of loader
    #    internals (the transitive-resolution loader lands separately, CORE-1394).
    sg_dir = loader.style_guides_dir
    for parent in guide.get("extends") or []:
        if not (sg_dir / parent).exists():
            problems.append(f"extends references missing file '{parent}'")

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", help="validate a single language code")
    args = parser.parse_args(argv)

    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    languages = json.loads(_LANGUAGES_JSON.read_text(encoding="utf-8"))["languages"]
    loader = StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR)

    guides = sorted(
        p
        for p in _STYLE_GUIDES_DIR.glob("*.yml")
        if _LANG_CODE_RE.match(p.stem) and p.stem != "python"
    )
    if args.lang:
        guides = [p for p in guides if p.stem == args.lang]
        if not guides:
            print(f"No guide found for '{args.lang}'.")
            return 2

    total = 0
    for path in guides:
        code = path.stem
        if code not in languages:
            print(f"[{code}] not in languages.json")
            total += 1
            continue
        try:
            guide = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            print(f"[{code}] YAML parse error: {exc}")
            total += 1
            continue
        problems = _validate_guide(code, guide, schema, languages[code], loader)
        for p in problems:
            print(f"[{code}] {p}")
        total += len(problems)

    print(
        f"\n{'OK' if total == 0 else total} "
        f"{'— all guides valid' if total == 0 else 'problem(s)'} "
        f"across {len(guides)} guide(s)."
    )
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
