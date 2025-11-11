#!/usr/bin/env python3
"""One-time migration of community translations to database.

This script migrates community translation data from extracted JSON files
into the SQLite database. It's a one-time migration and can be deleted
after successful completion.
"""

import json
import re
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


def map_emoji_to_vote(comment: str) -> str:
    """Map emoji in comment to vote type.

    Args:
        comment: Review comment potentially containing emojis

    Returns:
        Vote type: "approved", "suggest_revision", or "rejected"
    """
    if "✅" in comment:
        return "approved"
    elif "🤔" in comment or "❓" in comment:
        return "suggest_revision"
    elif "❌" in comment:
        return "rejected"
    return "suggest_revision"  # default


def extract_emoji(comment: str) -> str:
    """Extract the first emoji from comment.

    Args:
        comment: Review comment potentially containing emojis

    Returns:
        First emoji found, or empty string
    """
    emoji_pattern = r'[✅❌🤔❓]'
    match = re.search(emoji_pattern, comment)
    return match.group(0) if match else ""


def extract_reviewer(comment: str) -> str | None:
    """Extract @username from comment.

    Args:
        comment: Review comment potentially containing @mentions

    Returns:
        GitHub username (without @), or None if not found
    """
    match = re.search(r'@(\w+)', comment)
    return match.group(1) if match else None


def migrate_language(db: TranslationDatabase, data: dict, stats: dict) -> None:
    """Migrate one language from JSON to database.

    Args:
        db: Database instance
        data: Parsed JSON data for one language
        stats: Statistics dictionary to update
    """
    lang_code = data["language_code"]
    print(f"  Processing {lang_code}...", end=" ")

    lang_stats = {"translations": 0, "reviews": 0, "errors": []}

    # Migrate keywords
    for term, translation in data["keywords"].items():
        try:
            db.add_translation(
                language_code=lang_code,
                term=term,
                term_type="keyword",
                translation=translation,
                source="community"
            )
            lang_stats["translations"] += 1
            stats["translations"] += 1
        except Exception as e:
            error_msg = f"{lang_code}/{term} (keyword): {e}"
            lang_stats["errors"].append(error_msg)
            stats["errors"].append(error_msg)

    # Migrate builtins
    for term, translation in data["builtins"].items():
        try:
            db.add_translation(
                language_code=lang_code,
                term=term,
                term_type="builtin",
                translation=translation,
                source="community"
            )
            lang_stats["translations"] += 1
            stats["translations"] += 1
        except Exception as e:
            error_msg = f"{lang_code}/{term} (builtin): {e}"
            lang_stats["errors"].append(error_msg)
            stats["errors"].append(error_msg)

    # Migrate reviews
    for review in data.get("reviews", []):
        # Map category to term_type
        term_type = "keyword" if review.get("category") == "keyword" else "builtin"

        # Find the translation ID
        try:
            trans = db.get_translation(lang_code, review["term"], term_type, "community")
            if trans:
                # Extract review metadata
                reviewer = extract_reviewer(review["comment"])
                emoji = extract_emoji(review["comment"])
                vote = map_emoji_to_vote(review["comment"])

                # Store alternatives as JSON
                alternatives = review.get("suggestions", [])
                alternatives_json = json.dumps(alternatives) if alternatives else None

                db.add_review(
                    translation_id=trans["id"],
                    reviewer_github=reviewer,
                    emoji=emoji,
                    vote=vote,
                    comment=review["comment"],
                    alternatives_suggested=alternatives_json,
                    review_source="legacy_repo"
                )
                lang_stats["reviews"] += 1
                stats["reviews"] += 1
            else:
                error_msg = f"Translation not found for review: {lang_code}/{review['term']}"
                lang_stats["errors"].append(error_msg)
                stats["errors"].append(error_msg)
        except Exception as e:
            error_msg = f"Review {lang_code}/{review['term']}: {e}"
            lang_stats["errors"].append(error_msg)
            stats["errors"].append(error_msg)

    print(f"✅ {lang_stats['translations']} translations, {lang_stats['reviews']} reviews")
    if lang_stats["errors"]:
        print(f"    ⚠️  {len(lang_stats['errors'])} errors")


def main():
    """Run the one-time migration."""
    print("=" * 60)
    print("Community Translation Migration")
    print("=" * 60)
    print()

    # Initialize database
    db_path = I18N_LIB / "legesher_i18n" / "db" / "translations.db"
    print(f"Database: {db_path}")
    db = TranslationDatabase(db_path=str(db_path))

    # Initialize statistics
    stats = {
        "translations": 0,
        "reviews": 0,
        "languages": 0,
        "errors": []
    }

    # Load and process JSON files
    json_files = load_json_files()
    print(f"Found {len(json_files)} language files")
    print()

    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text())
            migrate_language(db, data, stats)
            stats["languages"] += 1
        except Exception as e:
            print(f"  ❌ Failed to process {json_file.name}: {e}")
            stats["errors"].append(f"File {json_file.name}: {e}")

    # Print summary
    print()
    print("=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"Languages migrated:    {stats['languages']}")
    print(f"Translations inserted: {stats['translations']}")
    print(f"Reviews inserted:      {stats['reviews']}")
    print(f"Errors encountered:    {len(stats['errors'])}")

    if stats["errors"]:
        print()
        print("Errors (first 10):")
        for error in stats["errors"][:10]:
            print(f"  - {error}")

        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")

    print()
    print(f"Database location: {db_path}")
    print()

    # Return success/failure
    return 0 if len(stats["errors"]) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
