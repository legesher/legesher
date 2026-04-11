#!/usr/bin/env python
"""Fix validation issues in language pack YAML files.

This script fixes:
1. Comment keys that were incorrectly stored (e.g., '# Python 3.11+ specific': null)
2. Translations with spaces (replaces with underscores)
3. Translations with invalid punctuation (hyphens, slashes)
4. English True/False that need quoting

Usage:
    python fix_validation_issues.py
    python fix_validation_issues.py --dry-run
"""

import argparse
from pathlib import Path

import yaml

# Path to language packs
LANGUAGE_PACKS_DIR = Path(__file__).parent.parent.parent / "language-packs" / "python"


def fix_translation(translation: str) -> str:
    """Fix a translation to be a valid Python identifier.

    Args:
        translation: The translation string to fix

    Returns:
        Fixed translation string
    """
    if not isinstance(translation, str):
        return translation

    # Replace spaces with underscores
    fixed = translation.replace(" ", "_")

    # Replace hyphens with underscores
    fixed = fixed.replace("-", "_")

    # Replace slashes with underscores
    fixed = fixed.replace("/", "_")

    # Remove multiple consecutive underscores
    while "__" in fixed:
        fixed = fixed.replace("__", "_")

    # Remove leading/trailing underscores (but keep single leading underscore if it was intentional)
    fixed = fixed.strip("_") or fixed

    return fixed


def fix_yaml_file(yaml_path: Path, dry_run: bool = False) -> list[str]:
    """Fix validation issues in a single YAML file.

    Args:
        yaml_path: Path to the YAML file
        dry_run: If True, don't write changes

    Returns:
        List of fixes made
    """
    fixes = []

    try:
        with open(yaml_path, encoding="utf-8") as f:
            content = f.read()
            data = yaml.safe_load(content)

        if not data:
            return fixes

        modified = False

        # Fix comment keys in keywords/builtins/exceptions sections
        for section in ["keywords", "builtins", "exceptions"]:
            section_data = data.get(section, {})
            if not isinstance(section_data, dict):
                continue

            # Find and remove comment keys
            keys_to_remove = [k for k in section_data.keys() if k.startswith("#")]
            for key in keys_to_remove:
                del section_data[key]
                fixes.append(f"Removed comment key: {key}")
                modified = True

            # Fix translations with spaces/invalid chars
            for term, translation in list(section_data.items()):
                if translation is None:
                    continue
                if not isinstance(translation, str):
                    continue

                fixed = fix_translation(translation)
                if fixed != translation:
                    section_data[term] = fixed
                    fixes.append(f"{section}.{term}: '{translation}' -> '{fixed}'")
                    modified = True

        if modified and not dry_run:
            # Write back with proper formatting
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                    width=1000,  # Prevent line wrapping
                )

    except yaml.YAMLError as e:
        fixes.append(f"YAML error: {e}")
    except Exception as e:
        fixes.append(f"Error: {e}")

    return fixes


def main():
    parser = argparse.ArgumentParser(
        description="Fix validation issues in language pack YAML files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    parser.add_argument(
        "--languages",
        "-l",
        nargs="+",
        help="Specific languages to fix (default: all)",
    )

    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]\n")

    # Get list of languages
    if args.languages:
        languages = args.languages
    else:
        languages = [
            d.name
            for d in sorted(LANGUAGE_PACKS_DIR.iterdir())
            if d.is_dir() and len(d.name) == 2
        ]

    total_fixes = 0

    for lang in languages:
        lang_dir = LANGUAGE_PACKS_DIR / lang
        pack_name = f"legesher_i18n_python_{lang}"
        packs_dir = lang_dir / pack_name / "packs"

        if not packs_dir.exists():
            continue

        lang_fixes = []

        for yaml_file in sorted(packs_dir.glob("3.*.yml")):
            fixes = fix_yaml_file(yaml_file, args.dry_run)
            if fixes:
                lang_fixes.extend([(yaml_file.name, fix) for fix in fixes])

        if lang_fixes:
            print(f"\n{lang}:")
            for filename, fix in lang_fixes:
                print(f"  {filename}: {fix}")
            total_fixes += len(lang_fixes)

    print(f"\n{'Would fix' if args.dry_run else 'Fixed'} {total_fixes} issues")


if __name__ == "__main__":
    main()
