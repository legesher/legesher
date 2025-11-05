#!/usr/bin/env python3
"""Generate keyword compatibility matrix for language packs across Python versions.

This script loads all language pack versions for a given language and generates
a Markdown table showing which keywords are available in which Python versions.

Usage:
    python scripts/generate_compatibility_matrix.py es
    python scripts/generate_compatibility_matrix.py ar --output docs/compatibility/ar.md
"""

import argparse
import sys
from pathlib import Path

import yaml


def load_language_packs(language: str, target: str = "python") -> dict[str, dict]:
    """Load all language pack versions for a given language.

    Args:
        language: Language code (e.g., 'es', 'ar')
        target: Target programming language (default: 'python')

    Returns:
        Dictionary mapping version -> pack data
    """
    # Find languages directory
    package_dir = Path(__file__).parent.parent
    languages_dir = package_dir / "languages"

    if not languages_dir.exists():
        print(f"Error: Languages directory not found: {languages_dir}", file=sys.stderr)
        sys.exit(1)

    target_dir = languages_dir / target
    if not target_dir.exists():
        print(f"Error: Target '{target}' not found", file=sys.stderr)
        sys.exit(1)

    # Find all version directories
    version_dirs = [
        d for d in target_dir.iterdir() if d.is_dir() and d.name[0].isdigit()
    ]

    if not version_dirs:
        print(f"Error: No version directories found for {target}", file=sys.stderr)
        sys.exit(1)

    # Sort versions
    version_dirs.sort(key=lambda d: [int(x) for x in d.name.split(".")])

    # Load packs
    packs = {}
    for version_dir in version_dirs:
        version = version_dir.name
        pack_file = version_dir / f"{language}.yml"

        if pack_file.exists():
            with open(pack_file) as f:
                pack_data = yaml.safe_load(f)
                packs[version] = pack_data

    if not packs:
        print(
            f"Error: No language packs found for '{language}' in {target}",
            file=sys.stderr,
        )
        sys.exit(1)

    return packs


def merge_inherited_keywords(
    pack_data: dict, all_packs: dict[str, dict], languages_dir: Path
) -> dict[str, str]:
    """Recursively merge keywords from parent packs.

    Args:
        pack_data: Current pack data
        all_packs: All loaded packs
        languages_dir: Path to languages directory

    Returns:
        Merged keywords dictionary
    """
    keywords = pack_data.get("keywords", {}).copy()

    # Check if pack extends another
    extends = pack_data.get("extends")
    if extends:
        # Try to resolve extends path
        # Format: ../3.10/es.yml
        import re

        match = re.search(r"(\d+\.\d+)", extends)
        if match:
            parent_version = match.group(1)
            if parent_version in all_packs:
                parent_keywords = merge_inherited_keywords(
                    all_packs[parent_version], all_packs, languages_dir
                )
                # Parent keywords are base, current pack overrides
                keywords = {**parent_keywords, **keywords}

    return keywords


def generate_compatibility_matrix(
    language: str, target: str = "python"
) -> tuple[str, dict[str, dict[str, str]]]:
    """Generate compatibility matrix for a language.

    Args:
        language: Language code
        target: Target programming language

    Returns:
        Tuple of (markdown_content, keyword_data)
    """
    packs = load_language_packs(language, target)

    # Find languages directory for inheritance resolution
    package_dir = Path(__file__).parent.parent
    languages_dir = package_dir / "languages"

    # Collect all keywords across all versions (with inheritance)
    all_keywords = set()
    version_keywords = {}

    for version in sorted(packs.keys(), key=lambda v: [int(x) for x in v.split(".")]):
        keywords = merge_inherited_keywords(packs[version], packs, languages_dir)
        version_keywords[version] = keywords
        all_keywords.update(keywords.keys())

    # Sort keywords alphabetically
    sorted_keywords = sorted(all_keywords)
    sorted_versions = sorted(packs.keys(), key=lambda v: [int(x) for x in v.split(".")])

    # Generate Markdown table
    lines = []
    lines.append(f"# {language.upper()} Keyword Compatibility Matrix")
    lines.append("")
    lines.append(
        f"Compatibility matrix for **{language}** language pack across Python versions."
    )
    lines.append("")
    lines.append(
        "This table shows which English keywords have translations in each Python version."
    )
    lines.append(
        "Keywords with `—` are not available in that version (either not yet introduced or removed)."
    )
    lines.append("")

    # Table header
    header = (
        "| Keyword (EN) | " + " | ".join([f"Py {v}" for v in sorted_versions]) + " |"
    )
    lines.append(header)

    # Separator
    separator = "|" + "|".join(["---"] + ["---" for _ in sorted_versions]) + "|"
    lines.append(separator)

    # Rows
    for keyword in sorted_keywords:
        row = f"| `{keyword}` |"
        for version in sorted_versions:
            translation = version_keywords[version].get(keyword, "—")
            if translation == "—":
                row += " — |"
            else:
                row += f" `{translation}` |"
        lines.append(row)

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**Total keywords:** {len(sorted_keywords)}")
    lines.append(f"**Python versions:** {', '.join(sorted_versions)}")
    lines.append("")
    lines.append("*Generated automatically by Legesher i18n*")
    lines.append("")

    return "\n".join(lines), version_keywords


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate compatibility matrix for language packs"
    )
    parser.add_argument("language", help="Language code (e.g., es, ar)")
    parser.add_argument(
        "--target", default="python", help="Target language (default: python)"
    )
    parser.add_argument(
        "--output", "-o", help="Output file path (default: stdout)", type=Path
    )

    args = parser.parse_args()

    print(f"Generating compatibility matrix for {args.language}...", file=sys.stderr)

    try:
        markdown, _ = generate_compatibility_matrix(args.language, args.target)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(markdown)
            print(f"✅ Matrix saved to: {args.output}", file=sys.stderr)
        else:
            print(markdown)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
