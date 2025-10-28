#!/usr/bin/env python3
"""
Extract Python keyword and builtin translations from legesher-translations repo.

This script:
1. Analyzes all dialect branches
2. Extracts Python keywords and built-ins
3. Preserves community review comments (the @mentions and emoji feedback)
4. Outputs structured data for comparison with AI translations

Usage:
    uv run python scripts/migrate_translations/extract_python_translations.py
"""

import re
import subprocess
from pathlib import Path
from typing import Any
import json
import yaml

# Configuration
WORK_DIR = Path(__file__).parent / "migration_data"
CLONE_DIR = WORK_DIR / "legesher-translations-clone"
OUTPUT_DIR = WORK_DIR / "extracted_translations"
COMMUNITY_REVIEWS_DIR = WORK_DIR / "community_reviews"


def setup_directories() -> None:
    """Create output directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    COMMUNITY_REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directories created")


def get_translation_branches() -> list[str]:
    """Get all translation branches."""
    result = subprocess.run(
        ["git", "branch", "-r"],
        cwd=CLONE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )

    branches = []
    for line in result.stdout.split("\n"):
        line = line.strip()
        if "translation" in line.lower() and "origin/" in line and "HEAD" not in line:
            branch = line.replace("origin/", "")
            branches.append(branch)

    return sorted(branches)


def extract_python_section(yaml_content: str) -> dict[str, Any]:
    """Extract Python keywords and builtins from YAML content with community comments."""
    # Find the Python section
    python_match = re.search(
        r'#\s*\|\s*LANGUAGE:\s*PYTHON\s*\|.*?(?=#\s*-{20,}\s*#\s*\|\s*LANGUAGE:|\Z)',
        yaml_content,
        re.DOTALL | re.IGNORECASE
    )

    if not python_match:
        return {"keywords": {}, "builtins": {}, "reviews": []}

    python_section = python_match.group(0)

    # Extract keywords section
    keywords = {}
    builtins = {}
    reviews = []

    # Find keywords section
    keywords_match = re.search(
        r'#\s*<<\s*Keywords\s*>>(.*?)#\s*<<\s*Built-In Functions\s*>>',
        python_section,
        re.DOTALL | re.IGNORECASE
    )

    if keywords_match:
        keywords_text = keywords_match.group(1)
        keywords, keyword_reviews = _parse_translations(keywords_text, "keyword")
        reviews.extend(keyword_reviews)

    # Find builtins section
    builtins_match = re.search(
        r'#\s*<<\s*Built-In Functions\s*>>(.*?)(?:#\s*<<\s*Error Messages\s*>>|\Z)',
        python_section,
        re.DOTALL | re.IGNORECASE
    )

    if builtins_match:
        builtins_text = builtins_match.group(1)
        builtins, builtin_reviews = _parse_translations(builtins_text, "builtin")
        reviews.extend(builtin_reviews)

    return {
        "keywords": keywords,
        "builtins": builtins,
        "reviews": reviews,
        "has_data": bool(keywords or builtins)
    }


def _parse_translations(section_text: str, category: str) -> tuple[dict[str, str], list[dict]]:
    """Parse translation entries with community review comments."""
    translations = {}
    reviews = []

    # Pattern to match translation lines with comments
    # Example:   def: "تعريف" #✅✅
    # Example:   print: "طباعة" #✅✅
    # Example with review:   as: "كـ" #🤔, @OussamaSALAHOUELHADJ ❓ "بدل" or "بإسم".

    lines = section_text.split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') and not ':' in line:
            continue

        # Match pattern: keyword: "translation" # review comments
        match = re.match(r'\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*["\']([^"\']*)["\']?\s*#?(.*)', line)

        if match:
            english_term = match.group(1).strip()
            translation = match.group(2).strip()
            comment = match.group(3).strip() if match.group(3) else ""

            # Skip empty translations
            if not translation or translation == '""':
                continue

            translations[english_term] = translation

            # Extract review information
            if comment:
                review_entry = {
                    "term": english_term,
                    "translation": translation,
                    "comment": comment,
                    "category": category,
                    "has_emoji": bool(re.search(r'[✅❌🤔❓]', comment)),
                    "has_mention": bool(re.search(r'@\w+', comment)),
                    "suggestions": []
                }

                # Extract alternative suggestions from comments
                # Pattern: ❓ "alternative" or ❓ alternative: "suggestion"
                suggestions = re.findall(r'[❓🤔]\s*["\']?([^"\'#,]+)["\']?', comment)
                if suggestions:
                    review_entry["suggestions"] = [s.strip() for s in suggestions]

                reviews.append(review_entry)

    return translations, reviews


def analyze_branch(branch_name: str) -> dict[str, Any] | None:
    """Analyze a single branch for Python translations."""
    print(f"\n📖 Extracting from: {branch_name}")

    # Checkout branch
    try:
        subprocess.run(
            ["git", "checkout", branch_name],
            cwd=CLONE_DIR,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Failed to checkout: {e}")
        return None

    # Find locale file for this language
    locale_dir = CLONE_DIR / "locale"
    if not locale_dir.exists():
        print(f"  ⚠️  No locale directory")
        return None

    # Look for language-specific YAML file
    # Pattern: ar.yml, es.yml, zh.yml, etc.
    yaml_files = list(locale_dir.glob("*.yml"))

    # Filter out template and list files
    yaml_files = [
        f for f in yaml_files
        if f.name not in ["en.yml", "dialect-list.yml", "language-keyword-template.yml"]
    ]

    if not yaml_files:
        print(f"  ⚠️  No translation file found")
        return None

    # Use the first matching file
    translation_file = yaml_files[0]
    lang_code = translation_file.stem  # e.g., "ar" from "ar.yml"

    print(f"  → Found: {translation_file.name} (lang: {lang_code})")

    # Read and parse the file
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ⚠️  Failed to read file: {e}")
        return None

    # Extract Python section
    python_data = extract_python_section(content)

    if not python_data["has_data"]:
        print(f"  ⚠️  No Python translations found")
        return None

    keyword_count = len(python_data["keywords"])
    builtin_count = len(python_data["builtins"])
    review_count = len(python_data["reviews"])

    print(f"  ✓ {keyword_count} keywords, {builtin_count} builtins, {review_count} reviews")

    return {
        "branch": branch_name,
        "language_code": lang_code,
        "keywords": python_data["keywords"],
        "builtins": python_data["builtins"],
        "reviews": python_data["reviews"],
        "stats": {
            "keyword_count": keyword_count,
            "builtin_count": builtin_count,
            "review_count": review_count,
        }
    }


def save_extraction(data: dict[str, Any]) -> None:
    """Save extracted translation data."""
    lang_code = data["language_code"]

    # Save main translation data
    output_file = OUTPUT_DIR / f"{lang_code}_python.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save community reviews separately for easy reading
    if data["reviews"]:
        review_file = COMMUNITY_REVIEWS_DIR / f"{lang_code}_reviews.md"
        with open(review_file, 'w', encoding='utf-8') as f:
            f.write(f"# Community Reviews for {lang_code.upper()} Python Translations\n\n")
            f.write(f"**Branch**: {data['branch']}\n\n")
            f.write(f"**Stats**: {data['stats']['keyword_count']} keywords, ")
            f.write(f"{data['stats']['builtin_count']} builtins, ")
            f.write(f"{data['stats']['review_count']} reviews\n\n")
            f.write("---\n\n")

            for review in data["reviews"]:
                f.write(f"## `{review['term']}` ({review['category']})\n\n")
                f.write(f"**Translation**: `{review['translation']}`\n\n")
                f.write(f"**Review Comment**: {review['comment']}\n\n")

                if review['suggestions']:
                    f.write(f"**Alternatives Suggested**:\n")
                    for suggestion in review['suggestions']:
                        f.write(f"- {suggestion}\n")
                    f.write("\n")

                f.write("---\n\n")


def generate_summary(all_extractions: list[dict[str, Any]]) -> None:
    """Generate summary report."""
    summary_file = OUTPUT_DIR / "extraction_summary.md"

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Python Translation Extraction Summary\n\n")
        f.write(f"**Total Languages Extracted**: {len(all_extractions)}\n\n")

        # Summary table
        f.write("## Language Coverage\n\n")
        f.write("| Language | Code | Keywords | Builtins | Reviews | Branch |\n")
        f.write("|----------|------|----------|----------|---------|--------|\n")

        for data in sorted(all_extractions, key=lambda x: x['language_code']):
            f.write(
                f"| {data['language_code'].upper()} | "
                f"`{data['language_code']}` | "
                f"{data['stats']['keyword_count']} | "
                f"{data['stats']['builtin_count']} | "
                f"{data['stats']['review_count']} | "
                f"{data['branch']} |\n"
            )

        f.write("\n## Next Steps\n\n")
        f.write("1. Review extracted translations in `extracted_translations/`\n")
        f.write("2. Review community feedback in `community_reviews/`\n")
        f.write("3. Run AI translation generation for comparison\n")
        f.write("4. Create final language pack YAML files\n\n")

    print(f"\n✓ Summary report: {summary_file}")


def main() -> None:
    """Main extraction workflow."""
    print("=" * 70)
    print("PYTHON TRANSLATION EXTRACTION")
    print("=" * 70)

    setup_directories()

    # Get all translation branches
    branches = get_translation_branches()
    print(f"\n📊 Found {len(branches)} translation branches")

    # Extract from each branch
    all_extractions = []

    for branch in branches:
        try:
            data = analyze_branch(branch)
            if data:
                save_extraction(data)
                all_extractions.append(data)
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            continue

    # Generate summary
    if all_extractions:
        generate_summary(all_extractions)

        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)
        print(f"\n✓ Extracted {len(all_extractions)} languages")
        print(f"✓ Translations saved to: {OUTPUT_DIR}")
        print(f"✓ Community reviews saved to: {COMMUNITY_REVIEWS_DIR}")
    else:
        print("\n⚠️  No translations extracted")


if __name__ == "__main__":
    main()
