#!/usr/bin/env python3
"""Validate community translation migration to database.

This script validates that all community translations and reviews
from the extracted JSON files were successfully migrated to the database.
"""

import json
import sys
from pathlib import Path

# Add libs/i18n to path to import the database module
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
I18N_LIB = REPO_ROOT / "libs" / "i18n"
sys.path.insert(0, str(I18N_LIB))

from legesher_i18n.db.database import TranslationDatabase


def load_json_files() -> list[Path]:
    """Load all extracted translation JSON files."""
    json_dir = SCRIPT_DIR / "migration_data" / "extracted_translations"
    if not json_dir.exists():
        raise FileNotFoundError(f"Directory not found: {json_dir}")

    files = sorted(json_dir.glob("*_python.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {json_dir}")

    return files


def validate_language(db: TranslationDatabase, json_file: Path, report: list[str]) -> dict:
    """Validate one language migration.

    Args:
        db: Database instance
        json_file: Path to JSON file
        report: List to append report lines to

    Returns:
        Dictionary with validation results
    """
    data = json.loads(json_file.read_text())
    lang_code = data["language_code"]

    # Count translations in JSON
    json_keywords = len(data["keywords"])
    json_builtins = len(data["builtins"])
    json_total = json_keywords + json_builtins

    # Count reviews in JSON
    json_reviews = len(data.get("reviews", []))

    # Count translations in database
    db_translations = db.get_all_translations(language_code=lang_code, source="community")
    db_total = len(db_translations)

    # Count reviews in database
    db_reviews = 0
    for trans in db_translations:
        db_reviews += len(db.get_reviews(trans["id"]))

    # Determine status
    trans_match = db_total == json_total
    reviews_match = db_reviews == json_reviews
    status = "✅" if (trans_match and reviews_match) else "❌"

    # Add to report
    report.append(f"## {lang_code.upper()}: {status}")
    report.append(f"- **Branch**: {data.get('branch', 'unknown')}")
    report.append(f"- **Translations**: {db_total}/{json_total} {('✅' if trans_match else '❌')}")
    report.append(f"  - Keywords: {json_keywords}")
    report.append(f"  - Builtins: {json_builtins}")
    report.append(f"- **Reviews**: {db_reviews}/{json_reviews} {('✅' if reviews_match else '❌')}")

    if not trans_match:
        report.append(f"  ⚠️  **MISMATCH**: Expected {json_total} translations, found {db_total}")
    if not reviews_match:
        report.append(f"  ⚠️  **MISMATCH**: Expected {json_reviews} reviews, found {db_reviews}")

    report.append("")

    return {
        "lang_code": lang_code,
        "status": status,
        "trans_match": trans_match,
        "reviews_match": reviews_match,
        "json_total": json_total,
        "db_total": db_total,
        "json_reviews": json_reviews,
        "db_reviews": db_reviews
    }


def main():
    """Run validation and generate report."""
    print("=" * 60)
    print("Community Translation Migration Validation")
    print("=" * 60)
    print()

    # Initialize database
    db_path = I18N_LIB / "legesher_i18n" / "db" / "translations.db"
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Run populate_from_json.py first to migrate the data.")
        return 1

    print(f"Database: {db_path}")
    db = TranslationDatabase(db_path=str(db_path))

    # Load JSON files
    json_files = load_json_files()
    print(f"Found {len(json_files)} language files to validate")
    print()

    # Validation report
    report = ["# Community Translation Migration Validation Report\n"]
    report.append(f"**Generated**: {Path(__file__).name}\n")
    report.append(f"**Database**: {db_path}\n")
    report.append("---\n")

    # Validate each language
    results = []
    for json_file in json_files:
        try:
            result = validate_language(db, json_file, report)
            results.append(result)
            print(f"  {result['lang_code']}: {result['status']}")
        except Exception as e:
            print(f"  ❌ Error validating {json_file.name}: {e}")
            report.append(f"## {json_file.stem}: ❌ ERROR")
            report.append(f"- **Error**: {e}\n")

    # Summary statistics
    report.append("---\n")
    report.append("## Summary Statistics\n")

    total_langs = len(results)
    passed_langs = sum(1 for r in results if r["trans_match"] and r["reviews_match"])
    total_trans_json = sum(r["json_total"] for r in results)
    total_trans_db = sum(r["db_total"] for r in results)
    total_reviews_json = sum(r["json_reviews"] for r in results)
    total_reviews_db = sum(r["db_reviews"] for r in results)

    report.append(f"- **Languages Validated**: {passed_langs}/{total_langs}")
    report.append(f"- **Total Translations**: {total_trans_db}/{total_trans_json}")
    report.append(f"- **Total Reviews**: {total_reviews_db}/{total_reviews_json}")
    report.append("")

    if passed_langs == total_langs:
        report.append("✅ **All languages validated successfully!**")
        report.append("")
        report.append("The migration is complete and data integrity is confirmed.")
    else:
        report.append("❌ **Some languages have validation issues.**")
        report.append("")
        report.append("Please review the errors above and re-run the migration if needed.")

    # Write report to file
    output_path = SCRIPT_DIR / "migration_data" / "migration_report.md"
    output_path.write_text("\n".join(report))

    # Print summary
    print()
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"Languages validated:   {passed_langs}/{total_langs}")
    print(f"Total translations:    {total_trans_db}/{total_trans_json}")
    print(f"Total reviews:         {total_reviews_db}/{total_reviews_json}")
    print()

    if passed_langs == total_langs:
        print("✅ All validations passed!")
    else:
        print("❌ Some validations failed. See report for details.")

    print()
    print(f"Full report: {output_path}")
    print()

    return 0 if passed_langs == total_langs else 1


if __name__ == "__main__":
    sys.exit(main())
