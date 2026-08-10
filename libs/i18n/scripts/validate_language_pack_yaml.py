#!/usr/bin/env python3
"""Custom YAML validator for language pack files.

This validator ensures language pack YAML files maintain proper formatting
and preserve necessary quotes (e.g., for values like 'no' that would
otherwise be parsed as booleans).

Rules:
1. All translations must be strings (not booleans, numbers, or null)
2. Values that look like YAML booleans must be quoted ('yes', 'no', 'true', 'false')
3. No spaces in translation values (a space makes the value multiple Python tokens)
4. No punctuation in translation values (no /, -, :, ., parentheses)
5. Proper YAML structure with required sections
6. No duplicate translations (same translation for different terms)
7. Script-aware validation (RTL, CJK, Latin scripts have different conventions)

How multi-word terms join:
The joining strategy is NOT a property of the script. It is declared per language
in ``style-guides/<lang>.yml`` under ``naming.detail`` today; CORE-1602 replaces it
with an enumerated ``naming.word_joiner``. That declaration is the only authority.
This file enforces rule 3 -- that the shipped value contains no space -- and says
nothing about how the space should have been resolved.

Rule 3 states a constraint; it does not imply a remedy. Deleting the space is a
destructive edit, not a fix (see CORE-1713 / the 5494504 retro on CORE-1515).

Historical note: this docstring previously asserted "RTL scripts (ar, he):
Concatenate without separators (Arabic/Hebrew naturally connect)." That is
linguistically false and was load-bearing for real damage. Arabic and Hebrew
letters join *within* a word as a rendering property of the script; this has
nothing to do with whether a boundary *between* two words may be deleted. The
claim was used to justify destroying word separation in the two languages that
ended up worst affected -- 55 of 70 Arabic exception terms, and an 18/52 Hebrew
convention split. It is removed rather than corrected in place because no
script-derived joining rule belongs here at all.

Usage:
    python validate_language_pack_yaml.py <file1.yml> <file2.yml> ...
"""

import sys
from pathlib import Path
import re
import yaml

# Cross-partition collision detection is Python-specific: CPython's ``tokenize``
# dispatches tokens flat, so a value shared across partitions round-trips to the
# wrong token (CORE-710). Acorn-style targets (JavaScript) are category-aware, so
# cross-partition homonyms are legal and this pass is skipped for them
# (CORE-1372); intra-section duplicates (reversibility) still apply to every
# target. Keyed on the pack's own ``target`` field. Interim seed for CORE-1503's
# per-target profiles (which also own the version-token grammar this script's
# schema check still enforces Python-style).
_CROSS_SECTION_TARGETS = frozenset({"python"})


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
                        f"{section}.{term}: Translation '{value_part}' contains spaces, "
                        f"so it is not a single Python identifier. Do NOT simply "
                        f"delete the spaces — follow the multi-word convention stated "
                        f"for this language in style-guides/<lang>.yml (naming.detail)."
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

        # Collision detection (CORE-605, CORE-710, CORE-950).
        #
        # Single source of truth: ``SchemaValidator.check_duplicates()``.
        # It surfaces both intra-section duplicates (e.g., two keywords
        # mapping to the same value) AND cross-section collisions (e.g.,
        # ``reserved_words.self`` matching ``keywords.in`` -- the
        # AYA-213 Cycle-4 Urdu failure mode CORE-710 fixed). It covers
        # all 6 sections: keywords / builtins / exceptions /
        # reserved_words / operators / standard_library.
        #
        # The previous in-script duplicate pass only covered the first
        # 3 sections AND emitted a duplicate error for any cross-section
        # collision involving them (Copilot review on PR #237 flagged
        # the noise). Replacing it with a single schema-validator call
        # produces one clean error per distinct collision.
        try:
            from legesher_i18n.schema_validator import (
                LanguagePackSchema,
                SchemaValidator,
            )

            schema = LanguagePackSchema(**data)
            dup = SchemaValidator.check_duplicates(schema)
        except ImportError as exc:
            self.errors.append(
                f"Collision validation could not run: legesher-i18n not "
                f"importable in this environment ({exc}). Install with "
                f"'uv sync' in the venv used by pre-commit."
            )
        except Exception as exc:
            # Surface the underlying error verbatim so the operator
            # sees the actual root cause (malformed YAML, schema
            # violation, etc.) rather than a misleading hint.
            self.errors.append(
                f"Collision validation failed: {type(exc).__name__}: {exc}"
            )
        else:
            # Intra-section duplicates: each section reports its own
            # ``{section}_duplicates`` list of {translation, source_terms}.
            for section_name, key in [
                ("keywords", "keyword_duplicates"),
                ("builtins", "builtin_duplicates"),
                ("exceptions", "exception_duplicates"),
                ("reserved_words", "reserved_word_duplicates"),
                ("operators", "operator_duplicates"),
                ("standard_library", "stdlib_duplicates"),
            ]:
                for entry in dup.get(key, []):
                    terms = ", ".join(
                        f"{section_name}.{t}" for t in entry["source_terms"]
                    )
                    self.errors.append(
                        f"Collision: translation '{entry['translation']}' used "
                        f"for multiple terms: {terms}. Each term must have a "
                        f"unique translation."
                    )

            # Cross-section collisions: same value in 2+ distinct sections.
            # Python-only (see ``_CROSS_SECTION_TARGETS``): acorn's AST is
            # category-aware, so this pass is skipped for non-Python targets.
            # Message is prefixed with "Collision" (capital C) so the
            # existing test_validate_yaml.py assertions
            # ``"Collision" in error_message`` work uniformly across
            # intra-section and cross-section findings.
            cross_section = (
                dup.get("cross_section_collisions", [])
                if schema.target in _CROSS_SECTION_TARGETS
                else []
            )
            for collision in cross_section:
                locations = ", ".join(
                    f"{loc['section']}.{loc['source_key']}"
                    for loc in collision.get("locations", [])
                )
                self.errors.append(
                    f"Collision across sections: translation "
                    f"'{collision['translation']}' appears in multiple sections "
                    f"({locations}). Each translation must be unique across "
                    f"all pack sections."
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
