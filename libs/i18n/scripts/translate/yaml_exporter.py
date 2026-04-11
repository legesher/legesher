"""YAML export functionality for translation pipeline.

This module exports translations from the database to YAML format
compatible with the Legesher language pack structure.

Exports to hierarchical format:
  language-packs/python/{lang}/legesher_i18n_python_{lang}/packs/3.10.yml
"""

import logging
from datetime import datetime
from pathlib import Path

import yaml

from legesher_i18n.db import TranslationDatabase
from legesher_i18n.language_registry import get_language_name

try:
    from .term_classifier import (
        classify_term,
        get_yaml_section_for_term_type,
        is_valid_term_type,
    )
except ImportError:
    # If relative import fails, try absolute import
    from term_classifier import (  # type: ignore[no-redef]
        classify_term,
        get_yaml_section_for_term_type,
        is_valid_term_type,
    )

logger = logging.getLogger(__name__)

# NOTE: Python version-specific additions are now tracked in:
#   libs/i18n/language-packs/python/version-index.yml
# And the base terms are defined in:
#   legesher_i18n/term_definitions.py
# Use VersionIndex.load() to access version-specific deltas.

# Natural language names for README generation
NATURAL_LANGUAGE_NAMES = {
    "ar": ("Arabic", "العربية"),
    "da": ("Danish", "Dansk"),
    "de": ("German", "Deutsch"),
    "el": ("Greek", "Ελληνικά"),
    "en": ("English", "English"),
    "es": ("Spanish", "Español"),
    "fi": ("Finnish", "Suomi"),
    "fr": ("French", "Français"),
    "he": ("Hebrew", "עברית"),
    "hi": ("Hindi", "हिन्दी"),
    "hu": ("Hungarian", "Magyar"),
    "id": ("Indonesian", "Bahasa Indonesia"),
    "it": ("Italian", "Italiano"),
    "ja": ("Japanese", "日本語"),
    "ko": ("Korean", "한국어"),
    "ms": ("Malay", "Bahasa Melayu"),
    "nl": ("Dutch", "Nederlands"),
    "no": ("Norwegian", "Norsk"),
    "pl": ("Polish", "Polski"),
    "pt": ("Portuguese", "Português"),
    "ru": ("Russian", "Русский"),
    "sv": ("Swedish", "Svenska"),
    "th": ("Thai", "ไทย"),
    "tr": ("Turkish", "Türkçe"),
    "vi": ("Vietnamese", "Tiếng Việt"),
    "zh": ("Chinese", "中文"),
}


class YAMLExporter:
    """Exports translations to YAML language pack format with hierarchical structure."""

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
    ) -> Path | None:
        """Export translations for a language to hierarchical pack structure.

        Creates:
          {lang}/
            legesher_i18n_python_{lang}/
              __init__.py
              packs/
                3.10.yml  (base pack with all terms)
                3.11.yml  (extends 3.10, adds 3.11-specific)
                3.12.yml  (extends 3.11, adds 3.12-specific)
                3.13.yml  (extends 3.12)
                3.14.yml  (extends 3.13)
            pyproject.toml
            README.md
            CHANGELOG.md

        Args:
            language_code: Language code (e.g., 'es', 'ar')
            source: Filter by translation source ('claude', 'aya', 'community')
            overwrite: If True, overwrite existing files

        Returns:
            Path to the language pack directory, or None if no translations
        """
        lang_dir = self.output_dir / language_code
        pack_name = f"legesher_i18n_python_{language_code}"
        packs_dir = lang_dir / pack_name / "packs"

        # Check if already exists
        if lang_dir.exists() and not overwrite:
            logger.info(f"Language pack {language_code} already exists, skipping")
            return lang_dir

        # Get all translations for this language (joined with term info)
        translations = self.db.get_translations_joined(
            language_code=language_code, source=source
        )

        if not translations:
            logger.warning(
                f"No translations found for language '{language_code}'"
                + (f" with source '{source}'" if source else "")
            )
            return None

        # Group by term and select best translation
        term_map = self._build_term_map(translations)

        # Classify all terms
        classified = self._classify_terms(term_map)

        # Create directory structure
        packs_dir.mkdir(parents=True, exist_ok=True)

        # Generate version-aware YAML files
        self._export_version_packs(language_code, classified, packs_dir)

        # Generate package files
        self._generate_init_py(language_code, lang_dir / pack_name)
        self._generate_pyproject_toml(language_code, lang_dir)
        self._generate_readme(language_code, lang_dir, classified)
        self._generate_changelog(language_code, lang_dir)

        logger.info(f"Exported language pack for '{language_code}' to {lang_dir}")
        return lang_dir

    def _build_term_map(self, translations: list[dict]) -> dict[str, dict]:
        """Build a map of terms to their best translations.

        Priority logic:
        1. Prefer actual translations (term != translation) over untranslated (term == translation)
        2. Among translations of same "translated" status, prefer higher confidence
        """
        term_map: dict[str, dict] = {}

        for trans in translations:
            term = trans["term"]
            translation = trans["translation"]

            # Check if this is actually translated (term != translation)
            is_translated = term.lower() != translation.lower()

            if term in term_map:
                existing = term_map[term]
                existing_translated = (
                    existing["term"].lower() != existing["translation"].lower()
                )

                # Prefer translated over untranslated
                if is_translated and not existing_translated:
                    term_map[term] = trans
                elif not is_translated and existing_translated:
                    # Keep existing (it's actually translated)
                    pass
                else:
                    # Both same status, compare confidence
                    existing_conf = self._confidence_to_score(existing["confidence"])
                    new_conf = self._confidence_to_score(trans["confidence"])
                    if new_conf > existing_conf:
                        term_map[term] = trans
            else:
                term_map[term] = trans

        return term_map

    def _classify_terms(self, term_map: dict[str, dict]) -> dict[str, dict[str, str]]:
        """Classify terms into YAML sections using stored term_type from database.

        This method uses the term_type stored in the database as the single source
        of truth, rather than re-classifying terms. This ensures consistency between
        what's stored and what's exported.

        For legacy data with missing/invalid term_type, falls back to classify_term()
        with a warning logged.

        Args:
            term_map: Dictionary mapping term -> translation record (with term_type)

        Returns:
            Dictionary with YAML section names as keys (keywords, builtins, exceptions)
            and dictionaries of term -> translation as values.
        """
        # Initialize output sections dynamically based on TERM_TYPE_YAML_SECTIONS
        sections: dict[str, dict[str, str]] = {}
        python_version = "3.13"  # Use latest for fallback classification

        for term, trans in term_map.items():
            translation = trans["translation"]
            stored_term_type = trans.get("term_type")

            # Validate the stored term_type
            if stored_term_type and is_valid_term_type(stored_term_type):
                term_type = stored_term_type
            else:
                # Fallback: re-classify term and log warning
                term_type = classify_term(term, python_version)
                if stored_term_type is None:
                    logger.warning(
                        f"Missing term_type for '{term}' - using fallback classification: {term_type}"
                    )
                else:
                    logger.warning(
                        f"Invalid term_type '{stored_term_type}' for '{term}' - "
                        f"using fallback classification: {term_type}"
                    )

            # Get the YAML section for this term_type
            yaml_section = get_yaml_section_for_term_type(term_type)

            # Skip terms that don't belong in YAML (helper, unknown)
            if yaml_section is None:
                logger.debug(
                    f"Skipping term '{term}' with type '{term_type}' (no YAML section)"
                )
                continue

            # Add to the appropriate section
            if yaml_section not in sections:
                sections[yaml_section] = {}
            sections[yaml_section][term] = translation

        # Ensure the standard sections exist (even if empty) for backwards compatibility
        result = {
            "keywords": sections.get("keywords", {}),
            "builtins": sections.get("builtins", {}),
            "exceptions": sections.get("exceptions", {}),
        }

        # Add any additional sections (for future term types like dunder_methods)
        for section_name, section_terms in sections.items():
            if section_name not in result:
                result[section_name] = section_terms

        return result

    def _export_version_packs(
        self, language_code: str, classified: dict, packs_dir: Path
    ):
        """Export version-aware YAML pack files."""
        lang_name = get_language_name(language_code)

        # Base builtins (pre-3.10 - everything except version-specific additions)
        base_builtins = {
            k: v
            for k, v in classified["builtins"].items()
            if k not in ["aiter", "anext"]  # These were added in 3.10
        }

        # 3.10 additions: keywords (match/case) and builtins (aiter/anext)
        base_keywords = {
            k: v
            for k, v in classified["keywords"].items()
            if k not in ["except*", "type"]  # Exclude 3.11+ and 3.12+
        }
        base_exceptions = {
            k: v
            for k, v in classified["exceptions"].items()
            if k
            not in [
                "exceptiongroup",
                "baseexceptiongroup",
                "encodingwarning",
            ]  # Exclude 3.11+
        }

        # 3.10-specific builtins (aiter, anext added in 3.10)
        builtins_310 = {}
        for b in ["aiter", "anext"]:
            if b in classified["builtins"]:
                builtins_310[b] = classified["builtins"][b]

        # Combine pre-3.10 base + 3.10-specific additions for the 3.10 pack
        builtins_310_all = {**base_builtins, **builtins_310}

        self._write_yaml_pack(
            packs_dir / "3.10.yml",
            language_code,
            "3.10",
            None,  # No extends for base
            base_keywords,
            builtins_310_all,
            base_exceptions,
            f"# {lang_name} Language Pack for Python 3.10+\n"
            f"# Base pack with all core keywords and Python 3.10 additions (match/case, aiter/anext)\n"
            f"# Generated by Legesher Translation Pipeline\n\n",
        )

        # 3.11 - Extends 3.10, adds except* and exception groups
        keywords_311 = {}
        if "except*" in classified["keywords"]:
            keywords_311["except*"] = classified["keywords"]["except*"]

        exceptions_311 = {}
        for ex in ["exceptiongroup", "baseexceptiongroup", "encodingwarning"]:
            if ex in classified["exceptions"]:
                exceptions_311[ex] = classified["exceptions"][ex]

        self._write_yaml_pack(
            packs_dir / "3.11.yml",
            language_code,
            "3.11",
            "3.10.yml",
            (
                keywords_311
                if keywords_311
                else {"# Python 3.11+ specific (PEP 654)": None}
            ),
            {},  # No new builtins in 3.11
            exceptions_311,
            f"# {lang_name} Language Pack for Python 3.11+\n"
            f"# Extends 3.10 pack and adds except* for exception groups\n\n",
        )

        # 3.12 - Extends 3.11, adds type keyword
        keywords_312 = {}
        if "type" in classified["keywords"]:
            keywords_312["type"] = classified["keywords"]["type"]

        self._write_yaml_pack(
            packs_dir / "3.12.yml",
            language_code,
            "3.12",
            "3.11.yml",
            (
                keywords_312
                if keywords_312
                else {"# Python 3.12+ specific (PEP 695)": None}
            ),
            {},  # No new builtins in 3.12
            {},  # No new exceptions in 3.12
            f"# {lang_name} Language Pack for Python 3.12+\n"
            f"# Extends 3.11 pack and adds 'type' keyword for type parameters\n\n",
        )

        # 3.13 - Extends 3.12 (no new keywords/builtins/exceptions)
        self._write_yaml_pack(
            packs_dir / "3.13.yml",
            language_code,
            "3.13",
            "3.12.yml",
            {},  # No new keywords
            {},  # No new builtins
            {},  # No new exceptions
            f"# {lang_name} Language Pack for Python 3.13+\n"
            f"# Extends 3.12 pack (no new keywords in 3.13)\n\n",
        )

        # 3.14 - Extends 3.13 (no new keywords/builtins/exceptions yet)
        self._write_yaml_pack(
            packs_dir / "3.14.yml",
            language_code,
            "3.14",
            "3.13.yml",
            {},  # No new keywords
            {},  # No new builtins
            {},  # No new exceptions
            f"# {lang_name} Language Pack for Python 3.14+\n"
            f"# Extends 3.13 pack (Python 3.14 in development)\n\n",
        )

    def _write_yaml_pack(
        self,
        filepath: Path,
        language_code: str,
        version: str,
        extends: str | None,
        keywords: dict,
        builtins: dict,
        exceptions: dict,
        header: str,
    ):
        """Write a single YAML pack file, merging with existing content if present."""
        # Load existing file if it exists
        existing_data = {}
        if filepath.exists():
            try:
                with open(filepath, encoding="utf-8") as f:
                    existing_data = yaml.safe_load(f) or {}
                logger.debug(f"Merging with existing {filepath}")
            except Exception as e:
                logger.warning(f"Could not read existing {filepath}: {e}")
                existing_data = {}

        # Merge keywords - new translations override existing
        merged_keywords = existing_data.get("keywords", {})
        merged_keywords.update(keywords)

        # Merge builtins - new translations override existing
        merged_builtins = existing_data.get("builtins", {})
        merged_builtins.update(builtins)

        # Merge exceptions - new translations override existing
        merged_exceptions = existing_data.get("exceptions", {})
        merged_exceptions.update(exceptions)

        # Build yaml data with merged content
        yaml_data = {
            "language": language_code,
            "target": "python",
            "version": version,
        }

        if extends:
            yaml_data["extends"] = extends

        # Use merged data
        yaml_data["keywords"] = merged_keywords if merged_keywords else {}
        if merged_builtins:
            yaml_data["builtins"] = merged_builtins
        yaml_data["exceptions"] = merged_exceptions if merged_exceptions else {}

        # Update metadata with existing values where present
        existing_metadata = existing_data.get("metadata", {})
        yaml_data["metadata"] = {
            "python_version_min": existing_metadata.get("python_version_min", version),
            "python_version_max": existing_metadata.get("python_version_max", "3.14"),
            "compatibility_tested": existing_metadata.get(
                "compatibility_tested", [version]
            ),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "community_reviewed": existing_metadata.get("community_reviewed", False),
            "author": existing_metadata.get("author", "Legesher Team (Aya AI Model)"),
            "license": existing_metadata.get("license", "Apache-2.0"),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header)
            yaml.dump(
                yaml_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        logger.debug(f"Wrote {filepath}")

    def _generate_init_py(self, language_code: str, package_dir: Path):
        """Generate __init__.py for the language pack."""
        lang_name, _ = NATURAL_LANGUAGE_NAMES.get(
            language_code, (language_code.upper(), language_code)
        )

        init_content = f'''"""{lang_name} language pack for Python in Legesher.

This package provides {lang_name} translations for Python keywords and built-ins,
supporting Python versions 3.10 through 3.14.
"""

__version__ = "0.0.1"

from pathlib import Path

# Package metadata
LANGUAGE = "{language_code}"
TARGET = "python"
PACK_DIR = Path(__file__).parent / "packs"

__all__ = ["__version__", "LANGUAGE", "TARGET", "PACK_DIR"]
'''
        init_file = package_dir / "__init__.py"
        init_file.write_text(init_content, encoding="utf-8")
        logger.debug(f"Wrote {init_file}")

    def _generate_pyproject_toml(self, language_code: str, lang_dir: Path):
        """Generate pyproject.toml for the language pack."""
        lang_name, native_name = NATURAL_LANGUAGE_NAMES.get(
            language_code, (language_code.upper(), language_code)
        )

        toml_content = f"""[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"

[project]
authors = [
    {{name = "Madison (Pfaff) Edgar", email = "7844510+madiedgar@users.noreply.github.com"}}
]
license = {{text = "Apache-2.0"}}
requires-python = ">=3.10,<4.0"
dependencies = [
    "legesher-i18n>=0.0.1,<0.1.0",
]
name = "legesher-i18n-python-{language_code}"
version = "0.0.1"
description = "{lang_name} language pack for Python in Legesher"
readme = "README.md"
keywords = ["legesher", "i18n", "{lang_name.lower()}", "python", "translation", "multilingual"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Internationalization",
    "Topic :: Software Development :: Localization",
    "Natural Language :: {lang_name}",
    "Operating System :: OS Independent",
]

[tool.uv.sources]
legesher-i18n = {{ path = "../../../", editable = true }}

[tool.semantic_release]
version_variable = "legesher_i18n_python_{language_code}/__init__.py:__version__"
version_toml = "pyproject.toml:project.version"
commit_parser = "angular"
major_on_zero = true
allow_zero_version = true
branch = "main"
tag_format = "i18n-python-{language_code}-v{{version}}"
upload_to_vcs_release = true
upload_to_pypi = false

[tool.semantic_release.commit_parser_options]
allowed_tags = [
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "build", "ci", "chore", "revert"
]
minor_tags = ["feat"]
patch_tags = ["fix", "perf"]

[tool.semantic_release.changelog]
exclude_commit_patterns = [
    "^chore\\\\(release\\\\):",
    "^Merge",
]
"""
        toml_file = lang_dir / "pyproject.toml"
        toml_file.write_text(toml_content, encoding="utf-8")
        logger.debug(f"Wrote {toml_file}")

    def _generate_readme(self, language_code: str, lang_dir: Path, classified: dict):
        """Generate README.md for the language pack."""
        lang_name, native_name = NATURAL_LANGUAGE_NAMES.get(
            language_code, (language_code.upper(), language_code)
        )

        num_keywords = len(classified["keywords"])
        num_builtins = len(classified["builtins"])
        num_exceptions = len(classified["exceptions"])

        readme_content = f"""# legesher-i18n-python-{language_code}

{lang_name} ({native_name}) language pack for Python in Legesher.

## Overview

This package provides {lang_name} translations for Python keywords and built-in functions, enabling developers to write
Python code in {lang_name}.

## Supported Python Versions

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

## Installation

```bash
# Install with legesher-i18n
uv pip install legesher-i18n legesher-i18n-python-{language_code}

# Or with pip
pip install legesher-i18n legesher-i18n-python-{language_code}
```

## Usage

The language pack is automatically discovered by `legesher-i18n` when installed:

```python
from legesher_i18n import LanguagePackLoader

# Load {lang_name} pack for Python 3.12
loader = LanguagePackLoader()
pack = loader.load("{language_code}", "python", "3.12")

# Use translated keywords
print(pack.keywords["def"])
print(pack.keywords["class"])
print(pack.keywords["return"])
```

## Translation Coverage

This pack provides translations for:

- **Keywords**: {num_keywords} Python keywords
- **Built-ins**: {num_builtins} built-in functions and types
- **Exceptions**: {num_exceptions} exception classes

## Version Inheritance

Language packs use inheritance to minimize duplication:

- `3.10.yml` - Complete Python 3.10 translations
- `3.11.yml` - Extends 3.10, adds new keywords (e.g., `except*`)
- `3.12.yml` - Extends 3.11, adds `type` keyword
- `3.13.yml` - Extends 3.12 (no new keywords)
- `3.14.yml` - Extends 3.13 (Python 3.14 in development)

## Contributing

To contribute translations or improvements:

1. Fork the [Legesher repository](https://github.com/madiedgar/legesher)
2. Edit files in `libs/i18n/language-packs/python/{language_code}/legesher_i18n_python_{language_code}/packs/`
3. Submit a pull request

Translation guidelines:

- Keep translations concise and commonly used
- Maintain consistency with existing translations
- Follow {lang_name} programming terminology conventions
- Test with real code examples

## License

Apache License 2.0 - See [LICENSE](../../../LICENSE) for details.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.
"""
        readme_file = lang_dir / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")
        logger.debug(f"Wrote {readme_file}")

    def _generate_changelog(self, language_code: str, lang_dir: Path):
        """Generate CHANGELOG.md for the language pack."""
        lang_name, _ = NATURAL_LANGUAGE_NAMES.get(
            language_code, (language_code.upper(), language_code)
        )
        today = datetime.now().strftime("%Y-%m-%d")

        changelog_content = f"""# Changelog - legesher-i18n-python-{language_code}

All notable changes to this language pack.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - {today}

### Added

- **Initial {lang_name} Language Pack**
  - Complete keyword translations for Python 3.10-3.14
  - Built-in function and type translations
  - Exception class translations
  - Version-aware inheritance system (3.10 → 3.11 → 3.12 → 3.13 → 3.14)
  - Support for Python 3.10+ features (match/case)
  - Support for Python 3.11+ features (except*)
  - Support for Python 3.12+ features (type parameter syntax)

### Technical Details

- **Python Versions**: 3.10, 3.11, 3.12, 3.13, 3.14
- **Inheritance Depth**: 5 levels (3.10 base → 3.14)
- **Translation Source**: Aya AI Model
- **Format**: YAML with version inheritance

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Legesher Monorepo](../../../)
"""
        changelog_file = lang_dir / "CHANGELOG.md"
        changelog_file.write_text(changelog_content, encoding="utf-8")
        logger.debug(f"Wrote {changelog_file}")

    def export_all_languages(
        self, sources: list[str] = None, overwrite: bool = False
    ) -> dict[str, Path]:
        """Export translations for all languages in database.

        Args:
            sources: List of sources to include ('claude', 'aya', 'community')
                    If None, includes all sources
            overwrite: If True, overwrite existing files

        Returns:
            Dictionary mapping language_code -> output_directory_path
        """
        all_translations = self.db.get_translations_joined()
        language_codes = {trans["language_code"] for trans in all_translations}

        logger.info(f"Exporting {len(language_codes)} languages: {language_codes}")

        results = {}

        for lang_code in sorted(language_codes):
            try:
                output_dir = self.export_language(
                    language_code=lang_code,
                    source=sources[0] if sources and len(sources) == 1 else None,
                    overwrite=overwrite,
                )
                if output_dir:
                    results[lang_code] = output_dir
            except Exception as e:
                logger.error(f"Failed to export language '{lang_code}': {e}")

        logger.info(f"Exported {len(results)} language packs successfully")
        return results

    def _confidence_to_score(self, confidence_str: str) -> float:
        """Convert confidence string to numeric score."""
        if confidence_str is None:
            return 0.5
        confidence_map = {"high": 0.9, "medium": 0.5, "low": 0.2}
        return confidence_map.get(str(confidence_str).lower(), 0.5)


def export_language_pack(
    db_path: str, language_code: str, output_dir: str = None, source: str = None
) -> Path:
    """Convenience function to export a language pack.

    Args:
        db_path: Path to translation database
        language_code: Language code to export
        output_dir: Output directory for language packs
        source: Filter by translation source

    Returns:
        Path to generated language pack directory
    """
    db = TranslationDatabase(db_path=db_path)
    exporter = YAMLExporter(db=db, output_dir=output_dir)

    return exporter.export_language(language_code=language_code, source=source)
