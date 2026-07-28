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

Usage (from the repo root):

    uv run python scripts/update_pack_readme_counts.py
"""

import re
import sys
from pathlib import Path

# Share the REFERENCE.md generator's pack-resolution logic verbatim.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_reference_docs import PACKS_DIR, load_merged_pack  # noqa: E402

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


def update_readme(lang_code: str) -> bool:
    """Rewrite the count lines of one pack README. Returns True if changed."""
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

    if changed:
        readme.write_text("\n".join(lines), encoding="utf-8")
    return changed


def main() -> int:
    updated = []
    unchanged = []
    errors = []

    for lang_dir in sorted(PACKS_DIR.iterdir()):
        if not lang_dir.is_dir() or not (lang_dir / "README.md").exists():
            continue
        lang_code = lang_dir.name
        try:
            if update_readme(lang_code):
                updated.append(lang_code)
            else:
                unchanged.append(lang_code)
        except Exception as e:  # keep going: report every pack's outcome
            errors.append(f"  {lang_code}: {e}")

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
