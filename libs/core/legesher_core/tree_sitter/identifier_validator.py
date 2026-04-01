"""Identifier validation for translated Python identifiers.

Ensures that LLM-translated identifiers are valid Python identifiers
that won't cause syntax errors or keyword collisions. Includes special
handling for RTL scripts and mixed-script detection.
"""

import keyword
import logging
import unicodedata

logger = logging.getLogger(__name__)


# Scripts that are RTL
RTL_SCRIPTS = frozenset(
    {
        "Arabic",
        "Hebrew",
        "Syriac",
        "Thaana",
        "Mandaic",
        "Samaritan",
        "Nko",
        "Hanifi_Rohingya",
        "Yezidi",
        "Old_South_Arabian",
        "Old_North_Arabian",
        "Manichaean",
        "Imperial_Aramaic",
        "Palmyrene",
        "Nabataean",
        "Hatran",
        "Phoenician",
        "Lydian",
        "Meroitic_Cursive",
        "Meroitic_Hieroglyphs",
        "Kharoshthi",
        "Old_Turkic",
        "Old_Hungarian",
        "Hanifi_Rohingya",
        "Old_Sogdian",
        "Sogdian",
        "Elymaic",
        "Chorasmian",
        "Yezidi",
    }
)


def _get_script(char: str) -> str:
    """Get the Unicode script of a character."""
    try:
        name = unicodedata.name(char, "")
        # Simple heuristic based on character name
        if "CJK" in name or "CHINESE" in name:
            return "Han"
        if "ARABIC" in name or "URDU" in name:
            return "Arabic"
        if "HEBREW" in name:
            return "Hebrew"
        if "DEVANAGARI" in name:
            return "Devanagari"
        if "LATIN" in name:
            return "Latin"
        if "CYRILLIC" in name:
            return "Cyrillic"
        if "GREEK" in name:
            return "Greek"
        if "HANGUL" in name:
            return "Hangul"
        if "KATAKANA" in name or "HIRAGANA" in name:
            return "Japanese"
        if "THAI" in name:
            return "Thai"
        if "GUJARATI" in name:
            return "Gujarati"
        if "GURMUKHI" in name:
            return "Gurmukhi"
        if "TELUGU" in name:
            return "Telugu"
        if "KANNADA" in name:
            return "Kannada"
        if "MALAYALAM" in name:
            return "Malayalam"
        if "SINHALA" in name:
            return "Sinhala"
        if "BENGALI" in name:
            return "Bengali"
        if "MYANMAR" in name:
            return "Myanmar"
        if "MONGOLIAN" in name:
            return "Mongolian"
    except ValueError:
        pass
    return "Unknown"


class IdentifierValidator:
    """Validates that translated identifiers are valid Python identifiers.

    Checks:
    1. str.isidentifier() — Python's built-in check (handles Unicode)
    2. keyword.iskeyword() — must not collide with Python keywords
    3. Mixed-script detection — warns about mixing scripts (e.g., Latin + Arabic)
    4. Sanitization — attempts to fix common issues

    Example:
        >>> validator = IdentifierValidator()
        >>> validator.is_valid("calcular_impuesto")
        True
        >>> validator.is_valid("123invalid")
        False
        >>> validator.is_valid("def")
        False
    """

    def is_valid(self, identifier: str) -> bool:
        """Check if an identifier is a valid Python identifier.

        Args:
            identifier: The translated identifier to validate

        Returns:
            True if valid, False otherwise
        """
        if not identifier:
            return False
        if not identifier.isidentifier():
            return False
        if keyword.iskeyword(identifier):
            return False
        return True

    def is_mixed_script(self, identifier: str) -> bool:
        """Check if an identifier mixes multiple scripts.

        Mixing scripts (e.g., Latin + Arabic) can cause confusion and
        readability issues. Underscores and digits are ignored.

        Args:
            identifier: The identifier to check

        Returns:
            True if multiple scripts are detected
        """
        scripts: set[str] = set()
        for char in identifier:
            if char == "_" or char.isdigit():
                continue
            script = _get_script(char)
            if script != "Unknown":
                scripts.add(script)
        return len(scripts) > 1

    def validate(self, identifier: str) -> tuple[bool, list[str]]:
        """Validate an identifier and return detailed issues.

        Args:
            identifier: The identifier to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues: list[str] = []

        if not identifier:
            issues.append("Empty identifier")
            return False, issues

        if not identifier.isidentifier():
            issues.append(f"Not a valid Python identifier: {identifier!r}")

        if keyword.iskeyword(identifier):
            issues.append(f"Collides with Python keyword: {identifier!r}")

        if self.is_mixed_script(identifier):
            issues.append(
                f"Mixed scripts detected in: {identifier!r} — "
                "consider using a single script for readability"
            )

        # Check for spaces (common LLM mistake)
        if " " in identifier:
            issues.append(f"Contains spaces: {identifier!r}")

        # Check for hyphens (common LLM mistake — valid in many languages but not Python)
        if "-" in identifier:
            issues.append(f"Contains hyphens: {identifier!r}")

        is_valid = len(issues) == 0 or (
            len(issues) == 1 and "Mixed scripts" in issues[0]
        )
        return is_valid, issues

    def sanitize(self, identifier: str) -> str:
        """Attempt to fix common issues with a translated identifier.

        Fixes:
        - Replace spaces with underscores
        - Replace hyphens with underscores
        - Remove invalid characters
        - Prepend underscore if starts with digit
        - Replace keyword collisions with underscore suffix

        Args:
            identifier: The potentially invalid identifier

        Returns:
            A sanitized identifier, or the original if already valid
        """
        if not identifier:
            return "_empty"

        # Replace spaces and hyphens with underscores
        result = identifier.replace(" ", "_").replace("-", "_")

        # Remove characters that aren't valid in identifiers
        # Keep: letters, digits, underscores (Python 3 Unicode identifiers)
        cleaned = []
        for char in result:
            if char == "_" or char.isalnum():
                # Check if the character is valid in an identifier context
                test = "a" + char if not cleaned else "".join(cleaned) + char
                if test.isidentifier():
                    cleaned.append(char)
            elif char.isidentifier():
                cleaned.append(char)

        result = "".join(cleaned) if cleaned else "_sanitized"

        # Ensure it doesn't start with a digit
        if result[0].isdigit():
            result = "_" + result

        # Handle keyword collisions
        if keyword.iskeyword(result):
            result = result + "_"

        # Final validation
        if not result.isidentifier():
            logger.warning(
                "Sanitization failed for %r, falling back to placeholder", identifier
            )
            return "_untranslated"

        return result
