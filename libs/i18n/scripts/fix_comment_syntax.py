#!/usr/bin/env python3
"""
Fix YAML comment syntax in language pack translations.

This script fixes two issues in language pack YAML files:

1. Comments inside quoted strings (1,247+ entries, 25 languages)
   Before: assert: 'परिभाषितकरना  #परिभाषित करना'
   After:  assert: परिभाषितकरना  # परिभाषित करना

2. Apostrophes in translations (French - 15 entries)
   Before: break: s'échapper
   After:  break: séchapper  # s'échapper

The script preserves original translations as proper YAML comments.
"""

import re
from pathlib import Path
from typing import NamedTuple


class FixResult(NamedTuple):
    """Result of fixing a single file."""

    file_path: Path
    fixes_applied: int
    apostrophe_fixes: int


def fix_quoted_comment_line(line: str) -> tuple[str, bool]:
    """
    Fix a line with a comment inside quoted string.

    Transforms: key: 'value  #comment'
    To:         key: value  # comment

    Returns: (fixed_line, was_fixed)
    """
    # Pattern: key: 'value  #comment' or key: 'value  # comment'
    # YAML escapes single quotes as '' inside single-quoted strings
    pattern = r"^(\s+)([a-zA-Z_][a-zA-Z0-9_]*): '(.+?)  #(.+)'$"
    match = re.match(pattern, line)

    if match:
        indent, key, value, comment = match.groups()
        # Unescape YAML single quotes ('' -> ')
        value = value.replace("''", "'")
        comment = comment.replace("''", "'")
        # Remove apostrophes from value (for valid Python identifiers)
        clean_value = value.replace("'", "")
        # Build the fixed line
        fixed_line = f"{indent}{key}: {clean_value}  # {comment}\n"
        return fixed_line, True

    return line, False


def fix_apostrophe_line(line: str) -> tuple[str, bool]:
    """
    Fix a line with apostrophe in unquoted value.

    Transforms: key: s'échapper
    To:         key: séchapper  # s'échapper

    Returns: (fixed_line, was_fixed)
    """
    # Pattern: key: value_with_apostrophe (unquoted, no existing comment)
    # Match lines that have an apostrophe in the value but aren't quoted
    pattern = r"^(\s+)([a-zA-Z_][a-zA-Z0-9_]*): ([^'#\n]+)'([^'#\n]+)$"
    match = re.match(pattern, line.rstrip("\n"))

    if match:
        indent, key, before_apos, after_apos = match.groups()
        original = f"{before_apos}'{after_apos}"
        clean_value = f"{before_apos}{after_apos}"
        fixed_line = f"{indent}{key}: {clean_value}  # {original}\n"
        return fixed_line, True

    return line, False


def fix_multiline_quoted_comments(content: str) -> tuple[str, int]:
    """
    Fix multi-line quoted comments in YAML content.

    Handles cases like:
      key: 'value  #comment that
          spans multiple lines'

    Returns: (fixed_content, fix_count)
    """
    # Pattern for multi-line quoted strings with embedded comments
    # Matches: key: 'value  #comment...' where the closing quote may be on another line
    pattern = r"^(\s+)([a-zA-Z_*][a-zA-Z0-9_*]*): '([^']*?)  #([^']*)'$"

    fix_count = 0

    def replace_match(match):
        nonlocal fix_count
        indent, key, value, comment = match.groups()
        # Unescape YAML single quotes ('' -> ')
        value = value.replace("''", "'")
        # Normalize comment (remove newlines and extra spaces)
        comment = " ".join(comment.replace("''", "'").split())
        # Remove apostrophes from value (for valid Python identifiers)
        clean_value = value.replace("'", "")
        fix_count += 1
        return f"{indent}{key}: {clean_value}  # {comment}"

    fixed_content = re.sub(
        pattern, replace_match, content, flags=re.MULTILINE | re.DOTALL
    )
    return fixed_content, fix_count


def fix_file(file_path: Path) -> FixResult:
    """
    Fix all translation issues in a single YAML file.

    Returns: FixResult with counts of fixes applied.
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    original_content = content
    comment_fixes = 0
    apostrophe_fixes = 0

    # First pass: fix multi-line quoted comments
    content, multiline_fixes = fix_multiline_quoted_comments(content)
    comment_fixes += multiline_fixes

    # Second pass: fix single-line issues (line by line)
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        line_with_newline = line + "\n" if line else line

        # Try to fix single-line quoted comment syntax
        fixed_line, was_fixed = fix_quoted_comment_line(line_with_newline)
        if was_fixed:
            comment_fixes += 1
            fixed_lines.append(fixed_line.rstrip("\n"))
            continue

        # Try to fix apostrophe in value
        fixed_line, was_fixed = fix_apostrophe_line(line_with_newline)
        if was_fixed:
            apostrophe_fixes += 1
            fixed_lines.append(fixed_line.rstrip("\n"))
            continue

        # No fix needed
        fixed_lines.append(line)

    final_content = "\n".join(fixed_lines)

    # Write back if any fixes were made
    if final_content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    return FixResult(
        file_path=file_path,
        fixes_applied=comment_fixes,
        apostrophe_fixes=apostrophe_fixes,
    )


def find_language_pack_files(base_path: Path) -> list[Path]:
    """Find all language pack YAML files."""
    pattern = "language-packs/python/*/legesher_i18n_python_*/packs/*.yml"
    return sorted(base_path.glob(pattern))


def main():
    """Main entry point."""
    # Find the i18n directory
    script_dir = Path(__file__).parent
    i18n_dir = script_dir.parent

    print(f"Scanning for language pack files in: {i18n_dir}")

    files = find_language_pack_files(i18n_dir)
    print(f"Found {len(files)} YAML files to process")

    total_comment_fixes = 0
    total_apostrophe_fixes = 0
    files_modified = 0

    for file_path in files:
        result = fix_file(file_path)

        if result.fixes_applied > 0 or result.apostrophe_fixes > 0:
            files_modified += 1
            total_comment_fixes += result.fixes_applied
            total_apostrophe_fixes += result.apostrophe_fixes

            rel_path = file_path.relative_to(i18n_dir)
            print(
                f"  {rel_path}: {result.fixes_applied} comment fixes, {result.apostrophe_fixes} apostrophe fixes"
            )

    print("\nSummary:")
    print(f"  Files modified: {files_modified}")
    print(f"  Comment syntax fixes: {total_comment_fixes}")
    print(f"  Apostrophe fixes: {total_apostrophe_fixes}")
    print(f"  Total fixes: {total_comment_fixes + total_apostrophe_fixes}")


if __name__ == "__main__":
    main()
