"""Unit tests for TokenTranslator class.

Tests the core translation functionality for keywords, builtins,
and formatting preservation. Uses real language pack translations.
"""

import pytest

from legesher_core.transformer import TokenTranslator


class TestTokenTranslator:
    """Test suite for TokenTranslator core functionality."""

    @pytest.fixture
    def spanish_translator(self, spanish_keywords, spanish_builtins):
        """Create a translator configured for Spanish."""
        return TokenTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    @pytest.fixture
    def arabic_translator(self, arabic_keywords, arabic_builtins):
        """Create a translator configured for Arabic."""
        return TokenTranslator(keyword_map=arabic_keywords, builtin_map=arabic_builtins)

    def test_translate_simple_function(
        self, spanish_translator, spanish_keywords, spanish_builtins
    ):
        """Test translating a simple function definition."""
        code = "def greet():\n    print('Hello')"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["def"] in translated
        assert spanish_builtins["print"] in translated
        assert "greet" in translated  # function name unchanged
        assert "'Hello'" in translated  # string unchanged

    def test_translate_keywords(self, spanish_translator, spanish_keywords):
        """Test that all keywords are translated correctly."""
        code = """
if True:
    for i in range(10):
        if i > 5:
            break
        else:
            continue
"""
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["if"] in translated
        assert spanish_keywords["True"] in translated
        assert spanish_keywords["for"] in translated
        assert spanish_keywords["in"] in translated
        assert spanish_keywords["break"] in translated
        assert spanish_keywords["else"] in translated
        assert spanish_keywords["continue"] in translated

    def test_translate_return_statement(self, spanish_translator, spanish_keywords):
        """Test return statement translation."""
        code = "def calculate(x):\n    return x * 2"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["def"] in translated
        assert spanish_keywords["return"] in translated
        assert "calculate" in translated  # function name unchanged
        assert "x * 2" in translated  # expression unchanged

    def test_translate_class_definition(self, spanish_translator, spanish_keywords):
        """Test class definition translation."""
        code = "class MyClass:\n    pass"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["class"] in translated
        assert "MyClass" in translated  # class name unchanged
        assert spanish_keywords["pass"] in translated

    def test_preserve_indentation(self, spanish_translator, spanish_keywords):
        """Test that indentation is preserved exactly."""
        code = "def foo():\n    if True:\n        return 42"
        translated = spanish_translator.translate_code(code, "en", "es")

        # Check that structure is preserved
        lines = translated.split("\n")
        assert lines[0].startswith(spanish_keywords["def"])
        assert lines[1].startswith("    ")  # 4 spaces
        assert lines[2].startswith("        ")  # 8 spaces

    def test_preserve_comments(self, spanish_translator, spanish_keywords):
        """Test that comments are preserved unchanged."""
        code = "def foo():\n    # This is a comment\n    return 42"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert "# This is a comment" in translated  # Comment unchanged
        assert spanish_keywords["def"] in translated
        assert spanish_keywords["return"] in translated

    def test_empty_code(self, spanish_translator):
        """Test handling of empty code."""
        assert spanish_translator.translate_code("", "en", "es") == ""
        assert spanish_translator.translate_code("   ", "en", "es") == "   "

    def test_incomplete_code(self, spanish_translator):
        """Test graceful handling of incomplete code."""
        incomplete = "def foo(\n    # incomplete"
        result = spanish_translator.translate_code(incomplete, "en", "es")

        # Should return original code when tokenization fails
        assert result == incomplete

    def test_arabic_translation(
        self, arabic_translator, arabic_keywords, arabic_builtins
    ):
        """Test Arabic (RTL) translation."""
        code = "def greet():\n    print('Hello')"
        translated = arabic_translator.translate_code(code, "en", "ar")

        assert arabic_keywords["def"] in translated
        assert arabic_builtins["print"] in translated
        assert "greet" in translated  # function name unchanged

    def test_arabic_unicode_preservation(self, arabic_translator, arabic_keywords):
        """Test that Arabic Unicode characters are not corrupted."""
        code = "def foo():\n    return True"
        translated = arabic_translator.translate_code(code, "en", "ar")

        # Verify Arabic characters are present and valid UTF-8
        assert arabic_keywords["def"] in translated
        assert arabic_keywords["return"] in translated
        assert arabic_keywords["True"] in translated

        # Ensure we can encode/decode without errors
        translated.encode("utf-8").decode("utf-8")
