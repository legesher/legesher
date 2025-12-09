#!/usr/bin/env python3
"""Custom YAML validator for language pack files.

This validator ensures language pack YAML files maintain proper formatting
and preserve necessary quotes (e.g., for values like 'no' that would
otherwise be parsed as booleans).

Rules:
1. All translations must be strings (not booleans, numbers, or null)
2. Values that look like YAML booleans must be quoted ('yes', 'no', 'true', 'false')
3. No spaces in translation values (must be concatenated)
4. No punctuation in translation values (no /, -, :, .)
5. Proper YAML structure with required sections

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

    def validate_file(self, file_path: Path) -> bool:
        """Validate a single language pack file.

        Returns:
            True if valid, False if errors found
        """
        self.errors = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                data = yaml.safe_load(content)
        except Exception as e:
            self.errors.append(f"Failed to parse YAML: {e}")
            return False

        # Validate structure
        if not isinstance(data, dict):
            self.errors.append("Root element must be a dictionary")
            return False

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

                # Check for punctuation
                invalid_chars = set(value_part) & {"/", "-", ":", ".", ",", ";"}
                if invalid_chars:
                    self.errors.append(
                        f"{section}.{term}: Translation '{value_part}' contains invalid "
                        f"punctuation: {', '.join(sorted(invalid_chars))}"
                    )

                # Check for mixed scripts (e.g., Latin + Arabic)
                # Note: Allow Latin + CJK mixing for technical terms in CJK languages
                if self._has_mixed_scripts(value_part):
                    scripts = self._detect_scripts(value_part)
                    # Allow Latin + CJK (common for technical terms like "IO", "with", etc.)
                    is_latin_cjk_only = set(scripts) == {"Latin", "CJK"}
                    if not is_latin_cjk_only:
                        self.errors.append(
                            f"{section}.{term}: Translation '{value_part}' mixes multiple scripts: "
                            f"{', '.join(scripts)}. Use a single script for consistency."
                        )

        return len(self.errors) == 0

    def _is_value_quoted_in_source(self, content: str, section: str, term: str) -> bool:
        """Check if a value is quoted in the source YAML."""
        # Look for the term in the content
        for line in content.split("\n"):
            if f"{term}:" in line:
                # Check if value after colon is quoted
                after_colon = line.split(f"{term}:", 1)[1].strip()
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
        """Print validation errors for a file."""
        if self.errors:
            print(f"\n{file_path}:")
            for error in self.errors:
                print(f"  - {error}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: validate_language_pack_yaml.py <file1.yml> <file2.yml> ...")
        sys.exit(1)

    validator = LanguagePackValidator()
    has_errors = False

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
            validator.print_errors(file_path)

    if has_errors:
        print("\n❌ Language pack validation failed")
        sys.exit(1)
    else:
        print("✅ All language packs valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
