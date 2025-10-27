"""Unit tests for utility functions."""

import pytest

from legesher_core.utils import (
    validate_utf8_encoding,
    detect_encoding,  # Backwards compatibility alias
    validate_python_code,
    normalize_newlines,
    is_rtl_language,
)
from legesher_core.exceptions import EncodingError


class TestValidateUtf8Encoding:
    """Tests for validate_utf8_encoding function."""

    def test_validate_utf8_file(self, tmp_path):
        """Test validating UTF-8 encoded file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass", encoding="utf-8")

        encoding = validate_utf8_encoding(test_file)
        assert encoding == "utf-8"

    def test_validate_utf8_with_unicode(self, tmp_path):
        """Test validating UTF-8 file with Unicode characters."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def café(): return '☕'", encoding="utf-8")

        encoding = validate_utf8_encoding(test_file)
        assert encoding == "utf-8"

    def test_non_utf8_file_raises_error(self, tmp_path):
        """Test that non-UTF-8 file raises EncodingError."""
        test_file = tmp_path / "latin1.py"
        # Write using Latin-1 encoding
        with open(test_file, "w", encoding="latin-1") as f:
            f.write("def foo(): # Café\n")

        # Should raise EncodingError when trying to read as UTF-8
        with pytest.raises(EncodingError, match="must be UTF-8 encoded"):
            validate_utf8_encoding(test_file)

    def test_backwards_compatibility_alias(self, tmp_path):
        """Test that detect_encoding alias still works."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass", encoding="utf-8")

        # Old function name should still work
        encoding = detect_encoding(test_file)
        assert encoding == "utf-8"


class TestValidatePythonCode:
    """Tests for validate_python_code function."""

    def test_valid_simple_code(self):
        """Test validation of simple valid code."""
        code = "def foo(): return 42"
        assert validate_python_code(code) is True

    def test_valid_complex_code(self):
        """Test validation of complex valid code."""
        code = """
def foo():
    if True:
        return 42
    else:
        return 0
"""
        assert validate_python_code(code) is True

    def test_invalid_syntax(self):
        """Test validation of invalid syntax."""
        code = "def foo)(:"
        assert validate_python_code(code) is False

    def test_incomplete_code(self):
        """Test validation of incomplete code."""
        code = "def foo("
        assert validate_python_code(code) is False

    def test_empty_code(self):
        """Test validation of empty code."""
        code = ""
        assert validate_python_code(code) is True  # Empty is valid


class TestNormalizeNewlines:
    """Tests for normalize_newlines function."""

    def test_normalize_windows_newlines(self):
        """Test normalizing Windows CRLF to LF."""
        code = "line1\r\nline2\r\nline3"
        result = normalize_newlines(code)
        assert result == "line1\nline2\nline3"

    def test_normalize_old_mac_newlines(self):
        """Test normalizing old Mac CR to LF."""
        code = "line1\rline2\rline3"
        result = normalize_newlines(code)
        assert result == "line1\nline2\nline3"

    def test_normalize_mixed_newlines(self):
        """Test normalizing mixed line endings."""
        code = "line1\r\nline2\rline3\nline4"
        result = normalize_newlines(code)
        assert result == "line1\nline2\nline3\nline4"

    def test_already_normalized(self):
        """Test that already normalized code is unchanged."""
        code = "line1\nline2\nline3"
        result = normalize_newlines(code)
        assert result == code


class TestIsRtlLanguage:
    """Tests for is_rtl_language function."""

    def test_arabic_is_rtl(self):
        """Test that Arabic is detected as RTL."""
        assert is_rtl_language("ar") is True

    def test_hebrew_is_rtl(self):
        """Test that Hebrew is detected as RTL."""
        assert is_rtl_language("he") is True

    def test_urdu_is_rtl(self):
        """Test that Urdu is detected as RTL."""
        assert is_rtl_language("ur") is True

    def test_farsi_is_rtl(self):
        """Test that Farsi/Persian is detected as RTL."""
        assert is_rtl_language("fa") is True

    def test_yiddish_is_rtl(self):
        """Test that Yiddish is detected as RTL."""
        assert is_rtl_language("yi") is True
        assert is_rtl_language("ji") is True  # alternate code

    def test_english_not_rtl(self):
        """Test that English is not RTL."""
        assert is_rtl_language("en") is False

    def test_spanish_not_rtl(self):
        """Test that Spanish is not RTL."""
        assert is_rtl_language("es") is False

    def test_case_insensitive(self):
        """Test that language code matching is case-insensitive."""
        assert is_rtl_language("AR") is True
        assert is_rtl_language("HE") is True
        assert is_rtl_language("EN") is False
