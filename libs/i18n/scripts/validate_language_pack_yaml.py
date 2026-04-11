#!/usr/bin/env python3
"""Custom YAML validator for language pack files.

This validator ensures language pack YAML files maintain proper formatting
and preserve necessary quotes (e.g., for values like 'no' that would
otherwise be parsed as booleans).

Rules:
1. All translations must be strings (not booleans, numbers, or null)
2. Values that look like YAML booleans must be quoted ('yes', 'no', 'true', 'false')
3. No spaces in translation values (must be concatenated)
4. No punctuation in translation values (no /, -, :, ., parentheses)
5. Proper YAML structure with required sections
6. No duplicate translations (same translation for different terms)
7. Script-aware validation (RTL, CJK, Latin scripts have different conventions)

Script-Specific Concatenation Guidelines:
- Latin scripts (en, es, fr, de, etc.): Use snake_case for multi-word terms
- RTL scripts (ar, he): Concatenate without separators (Arabic/Hebrew naturally connect)
- CJK scripts (zh, ja, ko): No separators needed (characters are self-contained)
- Cyrillic (ru): Use snake_case similar to Latin
- Greek (el): Use snake_case similar to Latin

Usage:
    python validate_language_pack_yaml.py <file1.yml> <file2.yml> ...
"""

import sys
from pathlib import Path
import re
import yaml


class LanguagePackValidator:
    """Validator for language pack YAML files."""

    # Values that must be quoted to avoid YAML boolean parsing
    YAML_BOOLEANS = {"yes", "no", "true", "false", "on", "off"}

    # Script detection patterns
    LATIN_SCRIPT = re.compile(r"[a-zA-Z]")
    ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")
    HEBREW_SCRIPT = re.compile(r"[\u0590-\u05FF]")
    CYRILLIC_SCRIPT = re.compile(r"[\u0400-\u04FF]")
    GREEK_SCRIPT = re.compile(r"[\u0370-\u03FF]")
    CJK_SCRIPT = re.compile(r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]")

    def __init__(self):
        self.errors = []
        self.warnings = []  # Non-blocking issues (e.g., mixed scripts)

    def validate_file(self, file_path: Path) -> bool:
        """Validate a single language pack file.

        Returns:
            True if valid, False if errors found
        """
        self.errors = []
        self.warnings = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                data = yaml.safe_load(content)
        except Exception as e:
            self.errors.append(f"Failed to parse YAML: {e}")
            return False

        # Validate structure
        if not isinstance(data, dict):
            self.errors.append("Root element must be a dictionary")
            return False

        # Track all translations to detect duplicates
        translation_to_terms: dict[str, list[str]] = {}

        # Validate each section
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

                # Check if translation is a string
                if not isinstance(translation, str):
                    self.errors.append(
                        f"{section}.{term}: Translation must be a string, "
                        f"got {type(translation).__name__} ({translation})"
                    )
                    continue

                # Extract value part (before comment)
                value_part = (
                    translation.split("#")[0].strip()
                    if "#" in translation
                    else translation.strip()
                )

                # Check if value needs quotes but doesn't have them in source
                if value_part.lower() in self.YAML_BOOLEANS:
                    # Read the raw YAML to check if it's quoted in the source
                    if not self._is_value_quoted_in_source(content, section, term):
                        self.errors.append(
                            f"{section}.{term}: Value '{value_part}' must be quoted to prevent "
                            f"YAML boolean parsing. Use '{value_part}' (with quotes)."
                        )

                # Check for spaces (except in comments)
                if " " in value_part:
                    self.errors.append(
                        f"{section}.{term}: Translation '{value_part}' contains spaces. "
                        f"Multi-word translations must be concatenated."
                    )

                # Check for punctuation (including parentheses)
                invalid_chars = set(value_part) & {
                    "/",
                    "-",
                    ":",
                    ".",
                    ",",
                    ";",
                    "(",
                    ")",
                    "[",
                    "]",
                    "{",
                    "}",
                }
                if invalid_chars:
                    self.errors.append(
                        f"{section}.{term}: Translation '{value_part}' contains invalid "
                        f"characters: {', '.join(sorted(invalid_chars))}"
                    )

                # Check for mixed scripts (e.g., Latin + Arabic)
                # Note: Allow Latin + CJK mixing for technical terms in CJK languages
                # Mixed scripts are a warning (quality issue) not an error (tracked in CORE-530)
                if self._has_mixed_scripts(value_part):
                    scripts = self._detect_scripts(value_part)
                    # Allow Latin + CJK (common for technical terms like "IO", "with", etc.)
                    is_latin_cjk_only = set(scripts) == {"Latin", "CJK"}
                    if not is_latin_cjk_only:
                        self.warnings.append(
                            f"{section}.{term}: Translation '{value_part}' mixes multiple scripts: "
                            f"{', '.join(scripts)}. Consider using a single script for consistency."
                        )

                # Track translation for duplicate detection
                if value_part:
                    key = f"{section}.{term}"
                    if value_part not in translation_to_terms:
                        translation_to_terms[value_part] = []
                    translation_to_terms[value_part].append(key)

        # Check for duplicate translations (same translation used for different terms)
        # Collisions break round-trip translation — upgraded from warning to error
        # in CORE-605 after resolving all existing collisions
        for translation, terms in translation_to_terms.items():
            if len(terms) > 1:
                self.errors.append(
                    f"Collision: translation '{translation}' used for multiple terms: "
                    f"{', '.join(terms)}. Each term must have a unique translation."
                )

        return len(self.errors) == 0

    def _is_value_quoted_in_source(self, content: str, section: str, term: str) -> bool:
        """Check if a value is quoted in the source YAML."""
        # Look for the term in the content - handle both quoted and unquoted keys
        # Patterns to match: `term:`, `'term':`, `"term":`
        key_patterns = [
            f"{term}:",  # unquoted key
            f"'{term}':",  # single-quoted key
            f'"{term}":',  # double-quoted key
        ]

        for line in content.split("\n"):
            for pattern in key_patterns:
                if pattern in line:
                    # Check if value after colon is quoted
                    after_colon = line.split(pattern, 1)[1].strip()
                    return after_colon.startswith("'") or after_colon.startswith('"')
        return False

    def _detect_scripts(self, text: str) -> list:
        """Detect which scripts are present in the text."""
        scripts = []
        if self.LATIN_SCRIPT.search(text):
            scripts.append("Latin")
        if self.ARABIC_SCRIPT.search(text):
            scripts.append("Arabic")
        if self.HEBREW_SCRIPT.search(text):
            scripts.append("Hebrew")
        if self.CYRILLIC_SCRIPT.search(text):
            scripts.append("Cyrillic")
        if self.GREEK_SCRIPT.search(text):
            scripts.append("Greek")
        if self.CJK_SCRIPT.search(text):
            scripts.append("CJK")
        return scripts

    def _has_mixed_scripts(self, text: str) -> bool:
        """Check if text contains multiple writing scripts."""
        scripts = self._detect_scripts(text)
        # More than one script is considered mixed
        return len(scripts) > 1

    def print_errors(self, file_path: Path):
        """Print validation errors and warnings for a file."""
        if self.errors or self.warnings:
            print(f"\n{file_path}:")
            for error in self.errors:
                print(f"  ❌ {error}")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_language_pack_yaml.py <file1.yml> <file2.yml> ...")
        sys.exit(1)

    validator = LanguagePackValidator()
    has_errors = False
    has_warnings = False

    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)

        # Only validate language pack YAML files
        if file_path.suffix not in [".yml", ".yaml"]:
            continue
        if "language-packs" not in str(file_path):
            continue
        if "packs" not in str(file_path):
            continue

        is_valid = validator.validate_file(file_path)

        if not is_valid:
            has_errors = True
        if validator.warnings:
            has_warnings = True

        # Print errors and warnings
        if validator.errors or validator.warnings:
            validator.print_errors(file_path)

    if has_errors:
        print("\n❌ Language pack validation failed")
        sys.exit(1)
    elif has_warnings:
        print("\n⚠️  Language pack validation passed with warnings (see CORE-530)")
        sys.exit(0)  # Warnings don't block
    else:
        print("✅ All language packs valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
