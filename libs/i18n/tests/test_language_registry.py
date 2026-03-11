"""Tests for the language registry module.

The language registry is the single source of truth for language metadata
loaded from languages.json. These tests verify the registry functions work
correctly and stay in sync with the JSON source.
"""

import json
from pathlib import Path


from legesher_i18n import (
    CANONICAL_LANGUAGE,
    LANGUAGE_METADATA,
    get_active_language_codes,
    get_available_language_codes,
    get_language_name,
    get_native_name,
    get_rtl_language_codes,
    is_rtl_language,
    is_supported_language,
)

# Path to the source JSON file
LANGUAGES_JSON = Path(__file__).parent.parent / "legesher_i18n" / "languages.json"


class TestLanguageRegistry:
    """Test the language registry loads correctly from JSON."""

    def test_languages_json_exists(self):
        """Verify the source JSON file exists."""
        assert LANGUAGES_JSON.exists(), f"languages.json not found at {LANGUAGES_JSON}"

    def test_language_metadata_matches_json(self):
        """Verify LANGUAGE_METADATA matches languages.json."""
        with open(LANGUAGES_JSON, encoding="utf-8") as f:
            data = json.load(f)

        json_languages = data["languages"]

        # Same number of languages
        assert len(LANGUAGE_METADATA) == len(json_languages)

        # Same language codes
        assert set(LANGUAGE_METADATA.keys()) == set(json_languages.keys())

    def test_canonical_language_matches_json(self):
        """Verify CANONICAL_LANGUAGE matches languages.json."""
        with open(LANGUAGES_JSON, encoding="utf-8") as f:
            data = json.load(f)

        assert CANONICAL_LANGUAGE == data["canonical_language"]

    def test_language_metadata_has_required_fields(self):
        """Verify each language has all required metadata fields."""
        required_fields = {"name", "native", "iso639_2", "bcp47", "rtl", "status"}

        for code, meta in LANGUAGE_METADATA.items():
            for field in required_fields:
                assert field in meta, f"Language '{code}' missing field '{field}'"


class TestGetActiveLanguageCodes:
    """Test get_active_language_codes function."""

    def test_returns_list(self):
        """Verify function returns a list."""
        result = get_active_language_codes()
        assert isinstance(result, list)

    def test_returns_non_empty_list(self):
        """Verify function returns at least one language."""
        result = get_active_language_codes()
        assert len(result) > 0

    def test_excludes_deprecated_languages(self):
        """Verify deprecated languages are excluded."""
        active_codes = get_active_language_codes()

        for code in active_codes:
            status = LANGUAGE_METADATA[code]["status"]
            assert status != "deprecated", (
                f"Deprecated language '{code}' found in active list"
            )

    def test_includes_experimental_languages(self):
        """Verify experimental languages are included."""
        active_codes = get_active_language_codes()

        # Find experimental languages in metadata
        experimental_codes = [
            code
            for code, meta in LANGUAGE_METADATA.items()
            if meta["status"] == "experimental"
        ]

        # All experimental languages should be in active list
        for code in experimental_codes:
            assert code in active_codes, (
                f"Experimental language '{code}' not in active list"
            )

    def test_includes_available_languages(self):
        """Verify available languages are included."""
        active_codes = get_active_language_codes()

        # Find available languages in metadata
        available_codes = [
            code
            for code, meta in LANGUAGE_METADATA.items()
            if meta["status"] == "available"
        ]

        # All available languages should be in active list
        for code in available_codes:
            assert code in active_codes, (
                f"Available language '{code}' not in active list"
            )

    def test_all_current_languages_are_active(self):
        """Verify all 29 languages are currently active (all experimental)."""
        active_codes = get_active_language_codes()
        assert len(active_codes) == 29


class TestGetAvailableLanguageCodes:
    """Test get_available_language_codes function."""

    def test_returns_list(self):
        """Verify function returns a list."""
        result = get_available_language_codes()
        assert isinstance(result, list)

    def test_only_includes_available_status(self):
        """Verify only 'available' status languages are returned."""
        available_codes = get_available_language_codes()

        for code in available_codes:
            status = LANGUAGE_METADATA[code]["status"]
            assert status == "available", f"Non-available language '{code}' found"

    def test_currently_returns_empty(self):
        """Verify function currently returns empty (all are experimental)."""
        # This test documents current behavior - all languages are experimental
        result = get_available_language_codes()
        assert len(result) == 0, "Expected empty list (all languages are experimental)"


class TestGetRtlLanguageCodes:
    """Test get_rtl_language_codes function."""

    def test_returns_list(self):
        """Verify function returns a list."""
        result = get_rtl_language_codes()
        assert isinstance(result, list)

    def test_includes_known_rtl_languages(self):
        """Verify known RTL languages are included."""
        rtl_codes = get_rtl_language_codes()

        # Arabic and Hebrew are RTL
        assert "ar" in rtl_codes, "Arabic should be RTL"
        assert "he" in rtl_codes, "Hebrew should be RTL"

    def test_excludes_ltr_languages(self):
        """Verify LTR languages are excluded."""
        rtl_codes = get_rtl_language_codes()

        # English, Spanish, etc. are NOT RTL
        assert "en" not in rtl_codes, "English should not be RTL"
        assert "es" not in rtl_codes, "Spanish should not be RTL"
        assert "zh" not in rtl_codes, "Chinese should not be RTL"

    def test_count_matches_metadata(self):
        """Verify count matches RTL languages in metadata."""
        rtl_codes = get_rtl_language_codes()
        expected_count = sum(1 for meta in LANGUAGE_METADATA.values() if meta["rtl"])
        assert len(rtl_codes) == expected_count


class TestGetLanguageName:
    """Test get_language_name function."""

    def test_returns_english_name(self):
        """Verify function returns English name."""
        assert get_language_name("en") == "English"
        assert get_language_name("es") == "Spanish"
        assert get_language_name("ar") == "Arabic"
        assert get_language_name("zh") == "Chinese"

    def test_unknown_language_returns_uppercase_code(self):
        """Verify unknown language returns uppercase code."""
        assert get_language_name("xx") == "XX"
        assert get_language_name("unknown") == "UNKNOWN"


class TestGetNativeName:
    """Test get_native_name function."""

    def test_returns_native_name(self):
        """Verify function returns native name."""
        assert get_native_name("en") == "English"
        assert get_native_name("es") == "Español"
        assert get_native_name("ar") == "العربية"
        assert get_native_name("zh") == "中文"
        assert get_native_name("ja") == "日本語"

    def test_unknown_language_returns_uppercase_code(self):
        """Verify unknown language returns uppercase code."""
        assert get_native_name("xx") == "XX"


class TestIsRtlLanguage:
    """Test is_rtl_language function."""

    def test_rtl_languages_return_true(self):
        """Verify RTL languages return True."""
        assert is_rtl_language("ar") is True
        assert is_rtl_language("he") is True

    def test_ltr_languages_return_false(self):
        """Verify LTR languages return False."""
        assert is_rtl_language("en") is False
        assert is_rtl_language("es") is False
        assert is_rtl_language("zh") is False

    def test_unknown_language_returns_false(self):
        """Verify unknown language returns False."""
        assert is_rtl_language("xx") is False


class TestIsSupportedLanguage:
    """Test is_supported_language function."""

    def test_supported_languages_return_true(self):
        """Verify supported languages return True."""
        assert is_supported_language("en") is True
        assert is_supported_language("es") is True
        assert is_supported_language("ar") is True
        assert is_supported_language("zh") is True

    def test_unsupported_languages_return_false(self):
        """Verify unsupported languages return False."""
        assert is_supported_language("xx") is False
        assert is_supported_language("unknown") is False
        assert is_supported_language("") is False


class TestLanguageMetadataFields:
    """Test individual metadata fields are correct."""

    def test_iso639_2_codes_are_three_letters(self):
        """Verify ISO 639-2 codes are 3 lowercase letters."""
        for code, meta in LANGUAGE_METADATA.items():
            iso639_2 = meta["iso639_2"]
            assert len(iso639_2) == 3, (
                f"Language '{code}' has invalid ISO 639-2: {iso639_2}"
            )
            assert iso639_2.islower(), (
                f"Language '{code}' ISO 639-2 should be lowercase"
            )
            assert iso639_2.isalpha(), (
                f"Language '{code}' ISO 639-2 should be alphabetic"
            )

    def test_bcp47_tags_are_valid_format(self):
        """Verify BCP 47 tags have valid format."""
        import re

        # BCP 47 pattern: 2-3 letter code, optional script, optional region
        bcp47_pattern = re.compile(r"^[a-z]{2,3}(-[A-Za-z]{4})?(-[A-Z]{2})?$")

        for code, meta in LANGUAGE_METADATA.items():
            bcp47 = meta["bcp47"]
            assert bcp47_pattern.match(bcp47), (
                f"Language '{code}' has invalid BCP 47: {bcp47}"
            )

    def test_status_values_are_valid(self):
        """Verify status values are one of the allowed values."""
        valid_statuses = {"available", "experimental", "deprecated"}

        for code, meta in LANGUAGE_METADATA.items():
            status = meta["status"]
            assert status in valid_statuses, (
                f"Language '{code}' has invalid status: {status}"
            )

    def test_rtl_values_are_boolean(self):
        """Verify RTL values are booleans."""
        for code, meta in LANGUAGE_METADATA.items():
            rtl = meta["rtl"]
            assert isinstance(rtl, bool), (
                f"Language '{code}' RTL should be boolean: {rtl}"
            )
