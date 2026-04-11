"""Translation validation module.

Validates translations against Python naming constraints and quality standards.
Used by the translation pipeline to ensure generated translations are valid.
"""

import re
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of translation validation.

    Attributes:
        is_valid: Whether translation passes all checks
        errors: List of error messages (critical issues)
        warnings: List of warning messages (quality suggestions)
        translation: The translation being validated
        term: Original Python term
    """

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    translation: str
    term: str

    def __str__(self) -> str:
        """Format validation result for display."""
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        msg = f"{status}: '{self.term}' → '{self.translation}'"

        if self.errors:
            msg += "\n  Errors:"
            for err in self.errors:
                msg += f"\n    - {err}"

        if self.warnings:
            msg += "\n  Warnings:"
            for warn in self.warnings:
                msg += f"\n    - {warn}"

        return msg


class TranslationValidator:
    """Validates translations against Python naming constraints.

    This validator ensures translations can be used as Python identifiers
    and meet quality standards for multilingual code.

    Constants:
        FORBIDDEN_PUNCTUATION: Characters that have special meaning in Python syntax
        NON_CASE_LANGUAGES: Languages without upper/lower case distinctions
        MAX_TRANSLATION_LENGTH: Maximum reasonable length for a translation (50 chars)
            Rationale: Translations longer than 50 chars are difficult to read and type.
            This is a soft limit that triggers a warning, not an error.
        COMMON_PLACEHOLDERS: Patterns indicating untranslated placeholder text
        COMMON_ENGLISH_WORDS: English words that shouldn't appear in non-English translations
    """

    # Punctuation that breaks Python syntax
    FORBIDDEN_PUNCTUATION = ["/", "-", ":", ".", ",", ";", "(", ")", "[", "]", "{", "}"]

    # Languages without case systems
    NON_CASE_LANGUAGES = {
        "ar": "Arabic",
        "he": "Hebrew",
        "hi": "Hindi",
        "ja": "Japanese",
        "ko": "Korean",
        "th": "Thai",
        "zh": "Chinese",
    }

    # Maximum reasonable length for a translation (chars)
    # Longer translations trigger a quality warning
    MAX_TRANSLATION_LENGTH = 50

    # Common placeholder patterns that indicate incomplete translation
    COMMON_PLACEHOLDERS = [
        "the translated term",
        "el término traducido",
        "the global variables",
        "término",
        "traducido",
    ]

    # Common English words that shouldn't appear in non-English translations
    COMMON_ENGLISH_WORDS = ["the", "a", "an", "of", "to", "in", "for", "is", "are"]

    # Pattern that indicates embedded YAML comment (should be outside quotes)
    EMBEDDED_COMMENT_PATTERN = re.compile(r"\s{2,}#")

    def validate(
        self,
        term: str,
        translation: str,
        language_code: str,
        term_type: str,
    ) -> ValidationResult:
        """Validate a translation.

        Args:
            term: Original Python term
            translation: Translated term
            language_code: Target language code (e.g., 'es', 'ar')
            term_type: Type of term ('keyword', 'builtin', 'exception')

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # Rule 1: No spaces (critical for keywords/builtins)
        if term_type in ["keyword", "builtin"] and " " in translation:
            errors.append(
                f"Contains space - Python will treat as multiple tokens. "
                f"Concatenate words: '{translation}' → '{translation.replace(' ', '')}'"
            )

        # Rule 2: No forbidden punctuation
        found_punct = [p for p in self.FORBIDDEN_PUNCTUATION if p in translation]
        if found_punct:
            punct_str = ", ".join(f"'{p}'" for p in found_punct)
            errors.append(
                f"Contains forbidden punctuation: {punct_str}. "
                f"These characters have special meaning in Python syntax."
            )

        # Rule 3: Cannot be empty
        if not translation or translation.strip() == "":
            errors.append("Translation cannot be empty")

        # Rule 4: Cannot be same as original (for non-English languages)
        if language_code != "en" and translation.lower() == term.lower():
            warnings.append(
                "Translation is identical to English term. "
                "Consider a language-specific translation."
            )

        # Rule 5: Check for common placeholder patterns
        translation_lower = translation.lower()
        if any(ph in translation_lower for ph in self.COMMON_PLACEHOLDERS):
            errors.append(
                f"Appears to be a placeholder, not an actual translation: '{translation}'"
            )

        # Rule 6: Should not contain English articles (for non-English)
        if language_code != "en" and term_type in ["keyword", "builtin"]:
            words = translation.lower().split()
            found_english = [w for w in words if w in self.COMMON_ENGLISH_WORDS]
            if found_english:
                warnings.append(
                    f"Contains common English words: {', '.join(found_english)}. "
                    f"Verify this is intentional."
                )

        # Rule 7: Capitalization for True/False/None (Latin scripts only)
        if term in ["True", "False", "None"]:
            if self._is_latin_script(translation):
                # Latin script - should be capitalized
                if (
                    translation
                    and translation[0].isalpha()
                    and translation[0].islower()
                ):
                    warnings.append(
                        f"Should start with capital letter for boolean/None: "
                        f"'{translation}' → '{translation[0].upper() + translation[1:]}'"
                    )
            elif language_code in self.NON_CASE_LANGUAGES:
                # Non-case script - this is fine, no action needed
                pass

        # Rule 8: Check length (suspiciously long translations)
        if len(translation) > self.MAX_TRANSLATION_LENGTH:
            warnings.append(
                f"Translation is very long ({len(translation)} chars). "
                f"Consider a more concise term. "
                f"(Maximum recommended: {self.MAX_TRANSLATION_LENGTH} chars)"
            )

        # Rule 9: Check for multiple consecutive special chars
        if re.search(r"[^\w\s]{2,}", translation):
            warnings.append("Contains multiple consecutive special characters")

        # Rule 10: Check for embedded YAML comments (CORE-529 fix regression check)
        # If a translation contains "  #", it likely means a YAML comment was
        # incorrectly parsed as part of the value (inside quoted string)
        if self.EMBEDDED_COMMENT_PATTERN.search(translation):
            errors.append(
                "Contains embedded YAML comment syntax (  #). "
                "This indicates the YAML file has a comment inside quotes. "
                "Fix: Move the comment outside the quoted string."
            )

        # Rule 11: Check for apostrophes (invalid Python identifiers)
        if "'" in translation:
            errors.append(
                f"Contains apostrophe (') which is invalid in Python identifiers. "
                f"Remove apostrophes: '{translation}' → '{translation.replace(chr(39), '')}'"
            )

        # Determine if valid
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            translation=translation,
            term=term,
        )

    def validate_pack(
        self,
        language_code: str,
        translations: dict,
    ) -> tuple[list[ValidationResult], dict]:
        """Validate an entire language pack.

        Args:
            language_code: Target language code
            translations: Dict of {section: {term: translation}}
                         e.g., {'keywords': {'def': 'definir'}, ...}

        Returns:
            Tuple of (validation_results, duplicate_map)
            - validation_results: List of ValidationResult for each term
            - duplicate_map: Dict mapping translation -> list of terms with that translation
        """
        results = []
        translation_map = {}  # Track duplicates

        for section, terms_dict in translations.items():
            for term, translation in terms_dict.items():
                # Validate individual translation
                result = self.validate(
                    term=term,
                    translation=str(translation),
                    language_code=language_code,
                    term_type=section.rstrip("s"),  # 'keywords' -> 'keyword'
                )
                results.append(result)

                # Track for duplicate detection
                trans_str = str(translation).lower()
                if trans_str not in translation_map:
                    translation_map[trans_str] = []
                translation_map[trans_str].append((section, term))

        # Find duplicates
        duplicates = {
            trans: terms for trans, terms in translation_map.items() if len(terms) > 1
        }

        # Add duplicate errors to results
        for trans, terms in duplicates.items():
            terms_list = [f"{s}.{t}" for s, t in terms]
            for result in results:
                if result.translation.lower() == trans:
                    result.is_valid = False
                    result.errors.append(
                        f"DUPLICATE: Same translation used for multiple terms: "
                        f"{', '.join(terms_list)}"
                    )

        return results, duplicates

    def _is_latin_script(self, text: str) -> bool:
        """Check if text uses primarily Latin script.

        Args:
            text: Text to check

        Returns:
            True if Latin script, False otherwise
        """
        if not text:
            return False

        # Sample first few characters
        for char in text[:3]:
            if char.isalpha():
                import unicodedata

                script = unicodedata.name(char, "").split()[0]
                return script == "LATIN"

        return False

    def print_summary(self, results: list[ValidationResult]) -> None:
        """Print validation summary.

        Args:
            results: List of validation results
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        print(f"\n{'=' * 60}")
        print("Validation Summary")
        print(f"{'=' * 60}")
        print(f"Total translations: {total}")
        print(f"  ✓ Valid: {valid}")
        print(f"  ✗ Invalid: {invalid}")
        print(f"\nTotal errors: {total_errors}")
        print(f"Total warnings: {total_warnings}")

        if invalid > 0:
            print(f"\n{'=' * 60}")
            print("Invalid Translations:")
            print(f"{'=' * 60}")
            for result in results:
                if not result.is_valid:
                    print(f"\n{result}")

        if total_warnings > 0:
            print(f"\n{'=' * 60}")
            print("Warnings:")
            print(f"{'=' * 60}")
            for result in results:
                if result.warnings:
                    print(f"\n{result}")
