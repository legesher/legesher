#!/usr/bin/env python
"""Import existing YAML language packs into the translation database.

This script ensures the database is the source of truth by importing
all existing translations from YAML files. Should be run before
translating new terms to ensure the export doesn't lose existing work.

Usage:
    # Import all languages
    python import_yaml_to_db.py

    # Import specific languages
    python import_yaml_to_db.py --languages hu de es

    # Dry run to see what would be imported
    python import_yaml_to_db.py --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from legesher_i18n.db import TranslationDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Path to language packs
LANGUAGE_PACKS_DIR = Path(__file__).parent.parent.parent / "language-packs" / "python"

# Skip English (it's the reference, not a translation)
SKIP_LANGUAGES = {"en"}


def import_yaml_file(
    yaml_path: Path,
    language_code: str,
    db: TranslationDatabase,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Import translations from a single YAML file into the database.

    Args:
        yaml_path: Path to the YAML file
        language_code: Language code (e.g., 'hu', 'de')
        db: Translation database instance
        dry_run: If True, don't actually write to database

    Returns:
        Tuple of (imported_count, skipped_count)
    """
    imported = 0
    skipped = 0

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return imported, skipped

        sections = ["keywords", "builtins", "exceptions"]

        for section in sections:
            section_data = data.get(section, {})
            if not isinstance(section_data, dict):
                continue

            # Map YAML section to term category
            section_to_category = {
                "keywords": "keyword",
                "builtins": "builtin_func",
                "exceptions": "exception",
            }
            category = section_to_category.get(section, "unknown")

            for term, translation in section_data.items():
                # Skip comments
                if term.startswith("#"):
                    continue

                # Skip None values
                if translation is None:
                    skipped += 1
                    continue

                if dry_run:
                    logger.debug(f"  Would import: {term} -> {translation}")
                    imported += 1
                    continue

                try:
                    # Get or create the term in the terms table
                    term_id = db.get_or_create_term(
                        name=term,
                        programming_language="python",
                        category=category,
                    )

                    db.add_translation(
                        term_id=term_id,
                        language_code=language_code,
                        translation=str(translation),
                        source="yaml-import",
                        confidence="high",
                        created_by="yaml-import",
                    )
                    imported += 1
                except Exception as e:
                    logger.warning(f"Failed to import {term}: {e}")
                    skipped += 1

    except yaml.YAMLError as e:
        logger.warning(f"YAML error in {yaml_path}: {e}")
    except Exception as e:
        logger.warning(f"Error reading {yaml_path}: {e}")

    return imported, skipped


def import_language(
    language_code: str,
    db: TranslationDatabase,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Import all YAML files for a language into the database.

    Args:
        language_code: Language code
        db: Translation database instance
        dry_run: If True, don't actually write to database

    Returns:
        Tuple of (total_imported, total_skipped)
    """
    lang_dir = LANGUAGE_PACKS_DIR / language_code
    pack_name = f"legesher_i18n_python_{language_code}"
    packs_dir = lang_dir / pack_name / "packs"

    if not packs_dir.exists():
        logger.warning(f"Packs directory not found: {packs_dir}")
        return 0, 0

    total_imported = 0
    total_skipped = 0

    # Import base file (3.10.yml) - contains most translations
    base_file = packs_dir / "3.10.yml"
    if base_file.exists():
        imported, skipped = import_yaml_file(base_file, language_code, db, dry_run)
        total_imported += imported
        total_skipped += skipped
        logger.debug(f"  {base_file.name}: {imported} imported, {skipped} skipped")

    # Also import higher version files for version-specific terms
    for version_file in sorted(packs_dir.glob("3.*.yml")):
        if version_file.name == "3.10.yml":
            continue  # Already processed

        imported, skipped = import_yaml_file(version_file, language_code, db, dry_run)
        total_imported += imported
        total_skipped += skipped

        if imported > 0:
            logger.debug(
                f"  {version_file.name}: {imported} imported, {skipped} skipped"
            )

    return total_imported, total_skipped


def main():
    parser = argparse.ArgumentParser(
        description="Import existing YAML language packs into the translation database"
    )
    parser.add_argument(
        "--languages",
        "-l",
        nargs="+",
        help="Specific languages to import (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - show what would be imported without writing to database",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to translation database (default: package db)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize database
    db = TranslationDatabase(db_path=str(args.db_path) if args.db_path else None)
    logger.info(f"Using database: {db.db_path}")

    # Get list of languages to import
    if args.languages:
        languages = args.languages
    else:
        # All languages except skipped ones
        languages = [
            d.name
            for d in sorted(LANGUAGE_PACKS_DIR.iterdir())
            if d.is_dir() and len(d.name) == 2 and d.name not in SKIP_LANGUAGES
        ]

    logger.info(f"Importing {len(languages)} languages: {languages}")

    if args.dry_run:
        logger.info("[DRY RUN MODE - No database writes]")

    # Import each language
    grand_total_imported = 0
    grand_total_skipped = 0

    for language in languages:
        logger.info(f"Importing {language}...")
        imported, skipped = import_language(language, db, args.dry_run)
        grand_total_imported += imported
        grand_total_skipped += skipped
        logger.info(f"  {language}: {imported} imported, {skipped} skipped")

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("IMPORT SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total imported: {grand_total_imported}")
    logger.info(f"Total skipped: {grand_total_skipped}")
    logger.info("=" * 60)

    if not args.dry_run:
        logger.info("")
        logger.info("Database is now the source of truth.")
        logger.info(
            "You can run translate_untranslated.py to fill in missing translations."
        )


if __name__ == "__main__":
    main()
