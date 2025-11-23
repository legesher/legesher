"""YAML export functionality for translation pipeline.

This module exports translations from the database to YAML format
compatible with the Legesher language pack structure.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml

from legesher_i18n.db import TranslationDatabase
from legesher_i18n.language_registry import get_language_name

try:
    from .term_classifier import classify_term, is_python_term
except ImportError:
    # If relative import fails, try absolute import
    from term_classifier import classify_term, is_python_term

logger = logging.getLogger(__name__)


class YAMLExporter:
    """Exports translations to YAML language pack format."""

    def __init__(self, db: TranslationDatabase, output_dir: Path = None):
        """Initialize YAML exporter.

        Args:
            db: Translation database instance
            output_dir: Output directory for YAML files
                       (defaults to libs/i18n/language-packs/python/)
        """
        self.db = db
        if output_dir is None:
            self.output_dir = (
                Path(__file__).parent.parent.parent / "language-packs" / "python"
            )
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"YAML exporter initialized: {self.output_dir}")

    def export_language(
        self, language_code: str, source: str = None, overwrite: bool = False
    ) -> Path:
        """Export translations for a language to YAML file.

        Args:
            language_code: Language code (e.g., 'es', 'ar')
            source: Filter by translation source ('claude', 'aya', 'community')
                   If None, uses highest-confidence translation from any source
            overwrite: If True, overwrite existing file

        Returns:
            Path to the generated YAML file

        Raises:
            FileExistsError: If file exists and overwrite=False
        """
        output_file = self.output_dir / f"{language_code}.yml"

        if output_file.exists() and not overwrite:
            raise FileExistsError(
                f"File {output_file} already exists. Use overwrite=True to replace."
            )

        # Get all translations for this language
        translations = self.db.get_all_translations(
            language_code=language_code, source=source
        )

        if not translations:
            logger.warning(
                f"No translations found for language '{language_code}'"
                + (f" with source '{source}'" if source else "")
            )
            return None

        # Group by term and select best translation
        term_map: Dict[str, Dict] = {}

        for trans in translations:
            term = trans["term"]

            # If we already have this term, compare confidence
            if term in term_map:
                existing_conf = self._confidence_to_score(term_map[term]["confidence"])
                new_conf = self._confidence_to_score(trans["confidence"])

                # Keep the higher confidence translation
                if new_conf > existing_conf:
                    term_map[term] = trans
            else:
                term_map[term] = trans

        # Classify and organize terms
        keywords = {}
        builtins = {}
        exceptions = {}
        python_version = "3.10"  # Default version for base packs

        for term, trans in term_map.items():
            # Skip helper terms (README, underscore, etc.) - they're not in language packs
            if not is_python_term(term, python_version):
                logger.debug(f"Skipping helper term: {term}")
                continue

            category = classify_term(term, python_version)
            translation = trans["translation"]

            # Keywords and special values
            if category == "keyword":
                keywords[term] = translation
            # Exceptions get their own section
            elif category == "exception":
                exceptions[term] = translation
            # Built-in functions, types, and constants
            elif category in (
                "builtin_func",
                "builtin_type",
                "special_constant",
            ):
                builtins[term] = translation
            else:
                # Unknown terms - add to builtins as fallback
                logger.warning(
                    f"Unknown term category for '{term}': {category} - adding to builtins"
                )
                builtins[term] = translation

        # Build YAML structure
        yaml_data = {
            "language": language_code,
            "target": "python",
            "version": python_version,
            "keywords": keywords,
            "builtins": builtins,
            "exceptions": exceptions,
            "metadata": {
                "python_version_min": python_version,
                "python_version_max": "3.13",
                "compatibility_tested": [python_version],
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "community_reviewed": False,
                "author": "Legesher Team (Aya AI Model)",
                "license": "MIT",
            },
        }

        # Generate header comment
        lang_name = get_language_name(language_code)
        header = (
            f"# {lang_name} Language Pack for Python {python_version}+\n"
            f"# Base pack with all core keywords and Python {python_version} additions (match/case)\n"
            f"# Generated by Legesher Translation Pipeline\n\n"
        )

        # Write to file with header
        with open(output_file, "w", encoding="utf-8") as f:
            # Write header comment
            f.write(header)

            # Write YAML data
            yaml.dump(
                yaml_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        logger.info(
            f"Exported {len(keywords)} keywords + {len(builtins)} builtins + "
            f"{len(exceptions)} exceptions to {output_file}"
            + (f" (source: {source})" if source else "")
        )

        return output_file

    def export_all_languages(
        self, sources: List[str] = None, overwrite: bool = False
    ) -> Dict[str, Path]:
        """Export translations for all languages in database.

        Args:
            sources: List of sources to include ('claude', 'aya', 'community')
                    If None, includes all sources
            overwrite: If True, overwrite existing files

        Returns:
            Dictionary mapping language_code -> output_file_path
        """
        # Get all unique language codes from database
        all_translations = self.db.get_all_translations()
        language_codes = {trans["language_code"] for trans in all_translations}

        logger.info(f"Exporting {len(language_codes)} languages: {language_codes}")

        results = {}

        for lang_code in sorted(language_codes):
            try:
                output_file = self.export_language(
                    language_code=lang_code,
                    source=sources[0] if sources and len(sources) == 1 else None,
                    overwrite=overwrite,
                )
                if output_file:
                    results[lang_code] = output_file
            except Exception as e:
                logger.error(f"Failed to export language '{lang_code}': {e}")

        logger.info(f"Exported {len(results)} language files successfully")
        return results

    def _confidence_to_score(self, confidence_str: str) -> float:
        """Convert confidence string to numeric score.

        Args:
            confidence_str: Confidence level ('high', 'medium', 'low')

        Returns:
            Numeric score (0.0-1.0)
        """
        if confidence_str is None:
            return 0.5  # Default to medium

        confidence_map = {"high": 0.9, "medium": 0.5, "low": 0.2}

        return confidence_map.get(confidence_str.lower(), 0.5)


def export_language_pack(
    db_path: str, language_code: str, output_dir: str = None, source: str = None
) -> Path:
    """Convenience function to export a language pack.

    Args:
        db_path: Path to translation database
        language_code: Language code to export
        output_dir: Output directory for YAML files
        source: Filter by translation source

    Returns:
        Path to generated YAML file
    """
    db = TranslationDatabase(db_path=db_path)
    exporter = YAMLExporter(db=db, output_dir=output_dir)

    return exporter.export_language(language_code=language_code, source=source)
