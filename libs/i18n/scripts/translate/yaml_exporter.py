"""YAML export functionality for translation pipeline.

This module exports translations from the database to YAML format
compatible with the Legesher language pack structure.

Exports to hierarchical format:
  language-packs/python/{lang}/legesher_i18n_python_{lang}/packs/3.10.yml
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from legesher_i18n.db import TranslationDatabase
from legesher_i18n.language_registry import get_language_name

try:
    from .term_classifier import classify_term, is_python_term
except ImportError:
    # If relative import fails, try absolute import
    from term_classifier import classify_term, is_python_term

logger = logging.getLogger(__name__)

# Python version-specific additions
PYTHON_VERSION_ADDITIONS = {
    "3.10": {
        "keywords": ["match", "case"],  # PEP 634: Structural Pattern Matching
        "exceptions": [],
    },
    "3.11": {
        "keywords": ["except*"],  # PEP 654: Exception Groups
        "exceptions": ["exceptiongroup", "baseexceptiongroup", "encodingwarning"],
    },
    "3.12": {
        "keywords": ["type"],  # PEP 695: Type Parameter Syntax
        "exceptions": [],
    },
    "3.13": {
        "keywords": [],
        "exceptions": [],
    },
    "3.14": {
        "keywords": [],
        "exceptions": [],
    },
}

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
    ) -> Optional[Path]:
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

    def _build_term_map(self, translations: List[Dict]) -> Dict[str, Dict]:
        """Build a map of terms to their best translations."""
        term_map: Dict[str, Dict] = {}

        for trans in translations:
            term = trans["term"]

            if term in term_map:
                existing_conf = self._confidence_to_score(term_map[term]["confidence"])
                new_conf = self._confidence_to_score(trans["confidence"])
                if new_conf > existing_conf:
                    term_map[term] = trans
            else:
                term_map[term] = trans

        return term_map

    def _classify_terms(self, term_map: Dict[str, Dict]) -> Dict[str, Dict[str, str]]:
        """Classify terms into keywords, builtins, and exceptions."""
        keywords = {}
        builtins = {}
        exceptions = {}
        python_version = "3.13"  # Use latest for classification

        for term, trans in term_map.items():
            if not is_python_term(term, python_version):
                logger.debug(f"Skipping helper term: {term}")
                continue

            category = classify_term(term, python_version)
            translation = trans["translation"]

            if category == "keyword":
                keywords[term] = translation
            elif category == "exception":
                exceptions[term] = translation
            elif category in ("builtin_func", "builtin_type", "special_constant"):
                builtins[term] = translation
            else:
                logger.warning(
                    f"Unknown term category for '{term}': {category} - adding to builtins"
                )
                builtins[term] = translation

        return {"keywords": keywords, "builtins": builtins, "exceptions": exceptions}

    def _export_version_packs(
        self, language_code: str, classified: Dict, packs_dir: Path
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
            keywords_311
            if keywords_311
            else {"# Python 3.11+ specific (PEP 654)": None},
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
            keywords_312
            if keywords_312
            else {"# Python 3.12+ specific (PEP 695)": None},
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
        extends: Optional[str],
        keywords: Dict,
        builtins: Dict,
        exceptions: Dict,
        header: str,
    ):
        """Write a single YAML pack file."""
        yaml_data = {
            "language": language_code,
            "target": "python",
            "version": version,
        }

        if extends:
            yaml_data["extends"] = extends

        # Only add non-empty sections
        if keywords:
            yaml_data["keywords"] = keywords
        else:
            yaml_data["keywords"] = {}

        if builtins:
            yaml_data["builtins"] = builtins

        if exceptions:
            yaml_data["exceptions"] = exceptions
        else:
            yaml_data["exceptions"] = {}

        yaml_data["metadata"] = {
            "python_version_min": version,
            "python_version_max": "3.14",
            "compatibility_tested": [version],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "community_reviewed": False,
            "author": "Legesher Team (Aya AI Model)",
            "license": "MIT",
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

        toml_content = f'''[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"

[project]
authors = [
    {{name = "Madison (Pfaff) Edgar", email = "7844510+madiedgar@users.noreply.github.com"}}
]
license = {{text = "MIT"}}
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
    "License :: OSI Approved :: MIT License",
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
'''
        toml_file = lang_dir / "pyproject.toml"
        toml_file.write_text(toml_content, encoding="utf-8")
        logger.debug(f"Wrote {toml_file}")

    def _generate_readme(self, language_code: str, lang_dir: Path, classified: Dict):
        """Generate README.md for the language pack."""
        lang_name, native_name = NATURAL_LANGUAGE_NAMES.get(
            language_code, (language_code.upper(), language_code)
        )

        num_keywords = len(classified["keywords"])
        num_builtins = len(classified["builtins"])
        num_exceptions = len(classified["exceptions"])

        readme_content = f'''# legesher-i18n-python-{language_code}

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

MIT License - See [LICENSE](../../../LICENSE) for details.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.
'''
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
        self, sources: List[str] = None, overwrite: bool = False
    ) -> Dict[str, Path]:
        """Export translations for all languages in database.

        Args:
            sources: List of sources to include ('claude', 'aya', 'community')
                    If None, includes all sources
            overwrite: If True, overwrite existing files

        Returns:
            Dictionary mapping language_code -> output_directory_path
        """
        all_translations = self.db.get_all_translations()
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
