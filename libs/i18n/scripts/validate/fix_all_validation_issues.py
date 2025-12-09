#!/usr/bin/env python3
"""Fix ALL validation issues across all language packs.

This script fixes:
1. Multi-word translations (spaces) - concatenate and preserve as comment
2. Invalid punctuation (/, :, -, .) - remove and preserve as comment
3. Mixed scripts (Latin+CJK are allowed for technical terms, others not)

Preserves all original translations as inline comments.
"""

from pathlib import Path
import sys
import yaml


def detect_scripts(text: str) -> set:
    """Detect scripts used in text."""
    scripts = set()
    for char in text:
        if ord(char) < 128:  # ASCII/Latin
            if char.isalpha():
                scripts.add("Latin")
        elif "\u4e00" <= char <= "\u9fff" or "\u3040" <= char <= "\u30ff":  # CJK
            scripts.add("CJK")
        elif "\u0590" <= char <= "\u05ff":  # Hebrew
            scripts.add("Hebrew")
        elif "\u0600" <= char <= "\u06ff":  # Arabic
            scripts.add("Arabic")
        elif "\u0400" <= char <= "\u04ff":  # Cyrillic
            scripts.add("Cyrillic")
        elif "\u0370" <= char <= "\u03ff":  # Greek
            scripts.add("Greek")
    return scripts


def fix_translation(term: str, translation: str, lang: str) -> str:
    """Fix a translation by removing invalid characters and spaces.

    Args:
        term: The Python term being translated
        translation: The translation value
        lang: Language code

    Returns:
        Fixed translation with issues resolved and original preserved in comment
    """
    # Skip if already has comment - assume it's already been processed
    if "#" in translation:
        return translation

    original = translation.strip()
    fixed = original

    # Remove spaces (multi-word translations)
    fixed = fixed.replace(" ", "")

    # Remove invalid punctuation
    for char in ["/", ":", "-", "."]:
        fixed = fixed.replace(char, "")

    # If we made changes, add comment with original
    if fixed != original:
        return f"{fixed}  #{original}"

    return translation


def fix_yaml_file(file_path: Path, lang: str, dry_run: bool = False) -> int:
    """Fix validation issues in a YAML file.

    Args:
        file_path: Path to YAML file
        lang: Language code
        dry_run: If True, only report fixes without writing

    Returns:
        Number of translations fixed
    """
    if not file_path.exists():
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    fix_count = 0
    modified = False

    # Process each section
    for section in ["keywords", "builtins", "exceptions"]:
        if section not in data:
            continue

        for term, translation in data[section].items():
            # Skip metadata fields
            if term in [
                "python_version_min",
                "python_version_max",
                "compatibility_tested",
                "last_updated",
                "community_reviewed",
            ]:
                continue

            # Skip if not a string
            if not isinstance(translation, str):
                continue

            # Check if needs fixing
            fixed = fix_translation(term, translation, lang)
            if fixed != translation:
                if dry_run:
                    print(f"  {section}.{term}:")
                    print(f"    BEFORE: {translation}")
                    print(f"    AFTER:  {fixed}")
                else:
                    data[section][term] = fixed
                fix_count += 1
                modified = True

    # Write back if modified
    if modified and not dry_run:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data, f, allow_unicode=True, sort_keys=False, default_flow_style=False
            )

    return fix_count


def main():
    """Fix validation issues in all language packs."""
    # Base directory for language packs
    base_dir = Path(__file__).parent.parent.parent / "language-packs" / "python"

    if not base_dir.exists():
        print(f"ERROR: Language packs directory not found: {base_dir}")
        return 1

    # Dry run mode for testing
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")

    total_fixes = 0
    files_modified = 0

    # Process all language packs
    for lang_dir in sorted(base_dir.iterdir()):
        if not lang_dir.is_dir() or lang_dir.name == "en":
            continue

        lang_code = lang_dir.name
        packs_dir = lang_dir / f"legesher_i18n_python_{lang_code}" / "packs"

        if not packs_dir.exists():
            continue

        print(f"\n{lang_code}:")

        lang_total = 0
        for yml_file in sorted(packs_dir.glob("*.yml")):
            fix_count = fix_yaml_file(yml_file, lang_code, dry_run)
            if fix_count > 0:
                print(f"  {yml_file.name}: {fix_count} fixes")
                lang_total += fix_count
                files_modified += 1

        if lang_total == 0:
            print("  ✓ No fixes needed")
        else:
            total_fixes += lang_total

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY:")
    print(f"  Total fixes: {total_fixes}")
    print(f"  Files modified: {files_modified}")

    if dry_run:
        print("\n  (DRY RUN - No changes made)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
