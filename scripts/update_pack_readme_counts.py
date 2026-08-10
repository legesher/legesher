#!/usr/bin/env python3
"""Rewrite the Translation Coverage count lines in pack README.md files.

Each pack README at ``libs/i18n/language-packs/python/{lang}/README.md``
states how many keywords, built-ins, and exceptions the pack translates.
Those numbers used to be frozen at generation time (the exporter never
overwrites an existing README), so they drifted from the packs (CORE-1014).

This script derives the counts from the pack YAML files using the SAME
resolution logic ``generate_reference_docs.py`` uses for REFERENCE.md
(every version file merged, distinct English terms counted), so README.md
and REFERENCE.md can never disagree. It rewrites ONLY the three count
lines; every other byte of each README is preserved. Lines that don't
match the numeric template (e.g. the English pack's prose lines) are
left untouched.

It also maintains one status blockquote per README (the line starting
``> **Status:``), derived from ``metadata.review_status`` in the pack's
base version file — the review-ladder tier vocabulary
(experimental/reviewed/official, ``schema_validator.LanguagePackMetadata``,
default ``experimental``) — so the maturity tier a pack claims is
surfaced where an installer actually reads. Because the tier lives in
pack YAML, the existing pre-commit trigger on pack-file changes re-runs
this script exactly when the tier can change. The canonical language
(``canonical_language`` in ``legesher_i18n/languages.json``) is the
English source surface, not a translation, and never gets a status
line. An existing status line is rewritten in place; a README without
one gets it inserted before its first ``##`` heading.

Usage (from the repo root):

    uv run python scripts/update_pack_readme_counts.py
"""

import re
import sys
from pathlib import Path

# Share the REFERENCE.md generator's pack-resolution and registry
# loading verbatim.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_reference_docs import (  # noqa: E402
    LANGUAGES_JSON,
    PACKS_DIR,
    get_packs_dir,
    load_merged_pack,
)


def _canonical_language() -> str:
    """The registry's canonical (source-surface) language code."""
    import json

    data = json.loads(LANGUAGES_JSON.read_text(encoding="utf-8"))
    return data.get("canonical_language", "en")

# One honest sentence per maturity tier (the CORE-1513 ladder). The
# pack's own metadata.review_status is the source of truth for which
# tier it is on (schema enum: experimental/reviewed/official). Each
# entry is a two-line blockquote paragraph so no line exceeds the
# markdownlint 120-character limit.
_STATUS_TEMPLATES = {
    "experimental": (
        "> **Status: experimental** — machine-generated translations; "
        "community validation in progress.\n"
        "> Terms may change as native speakers review them."
    ),
    "reviewed": (
        "> **Status: reviewed** — native speakers have endorsed this "
        "pack's vocabulary.\n"
        "> Community ratification pending."
    ),
    "official": (
        "> **Status: official** — ratified by the language community."
    ),
}

_STATUS_LINE = re.compile(r"^> \*\*Status: .*$")
# Continuation lines of OUR blockquote only: plain "> " prose (or a bare
# ">") that is neither another status line nor an admonition a
# maintainer added below ours.
_STATUS_CONTINUATION = re.compile(r"^>($| (?!\*\*Status:|\[!).*$)")

# Only lines matching these exact templates are rewritten.
_COUNT_LINES = {
    "keywords": (
        re.compile(r"^- \*\*Keywords\*\*: \d+ Python keywords$"),
        "- **Keywords**: {n} Python keywords",
    ),
    "builtins": (
        re.compile(r"^- \*\*Built-ins\*\*: \d+ built-in functions and types$"),
        "- **Built-ins**: {n} built-in functions and types",
    ),
    "exceptions": (
        re.compile(r"^- \*\*Exceptions\*\*: \d+ exception classes$"),
        "- **Exceptions**: {n} exception classes",
    ),
}


def _pack_review_status(lang_code: str) -> str:
    """The pack's review-ladder tier, from its base version file.

    ``metadata.review_status`` carries the tier when a promotion has been
    stamped (CORE-1796); the schema default is ``experimental``.
    """
    import yaml

    version_files = sorted(get_packs_dir(lang_code).glob("3.*.yml"))
    if not version_files:
        return "experimental"
    with open(version_files[0], encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    metadata = data.get("metadata") or {}
    return str(metadata.get("review_status", "experimental"))


def _apply_status_line(
    lines: list[str], status: str, warnings: list[str]
) -> bool:
    """Insert or rewrite the status blockquote. Returns True if changed."""
    template = _STATUS_TEMPLATES.get(status)
    if template is None:
        warnings.append(f"unrecognized review_status {status!r}; status line not updated")
        return False
    block = template.split("\n")

    for i, line in enumerate(lines):
        if _STATUS_LINE.match(line):
            # Replace the whole existing blockquote (first line plus any
            # continuation lines) with the current template.
            end = i + 1
            while end < len(lines) and _STATUS_CONTINUATION.match(lines[end]):
                end += 1
            if lines[i:end] != block:
                lines[i:end] = block
                return True
            return False

    # No status line yet: insert before the first section heading,
    # separated by a blank line on each side.
    for i, line in enumerate(lines):
        if line.startswith("## "):
            prefix = [] if i == 0 or lines[i - 1] == "" else [""]
            lines[i:i] = [*prefix, *block, ""]
            return True
    warnings.append("no '## ' heading found; status line not inserted")
    return False


def _remove_status_line(lines: list[str]) -> bool:
    """Drop a status blockquote (canonical language). True if changed."""
    for i, line in enumerate(lines):
        if _STATUS_LINE.match(line):
            end = i + 1
            while end < len(lines) and _STATUS_CONTINUATION.match(lines[end]):
                end += 1
            if end < len(lines) and lines[end] == "":
                end += 1
            del lines[i:end]
            return True
    return False


def update_readme(
    lang_code: str, canonical: str, warnings: list[str]
) -> bool:
    """Rewrite the count + status lines of one pack README."""
    readme = PACKS_DIR / lang_code / "README.md"
    merged = load_merged_pack(lang_code)

    text = readme.read_text(encoding="utf-8")
    lines = text.split("\n")
    changed = False
    for i, line in enumerate(lines):
        for section, (pattern, template) in _COUNT_LINES.items():
            if pattern.match(line):
                new_line = template.format(n=len(merged.get(section, {})))
                if new_line != line:
                    lines[i] = new_line
                    changed = True

    if lang_code == canonical:
        # The canonical language is the source surface, not a
        # translation — a maturity-tier claim would be false on it.
        if _remove_status_line(lines):
            changed = True
    elif _apply_status_line(lines, _pack_review_status(lang_code), warnings):
        changed = True

    if changed:
        readme.write_text("\n".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    updated = []
    unchanged = []
    errors = []

    canonical = _canonical_language()
    for lang_dir in sorted(PACKS_DIR.iterdir()):
        if not lang_dir.is_dir() or not (lang_dir / "README.md").exists():
            continue
        lang_code = lang_dir.name
        pack_warnings: list[str] = []
        try:
            if update_readme(lang_code, canonical, pack_warnings):
                updated.append(lang_code)
            else:
                unchanged.append(lang_code)
        except Exception as e:  # keep going: report every pack's outcome
            errors.append(f"  {lang_code}: {e}")
        for w in pack_warnings:
            errors.append(f"  {lang_code}: {w}")

    print(f"Updated {len(updated)} README.md files: {' '.join(updated)}")
    print(f"Unchanged: {len(unchanged)} ({' '.join(unchanged)})")
    if errors:
        print(f"Errors ({len(errors)}):")
        for line in errors:
            print(line)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
