"""Unit tests for TokenTranslator class.

Tests the core translation functionality for keywords, builtins,
and formatting preservation.
"""

import pytest

from legesher_core.transformer import TokenTranslator
from tests.data.keyword_maps_spanish import SPANISH_KEYWORDS, SPANISH_BUILTINS
from tests.data.keyword_maps_arabic import ARABIC_KEYWORDS, ARABIC_BUILTINS


class TestTokenTranslator:
    """Test suite for TokenTranslator core functionality."""

    @pytest.fixture
    def spanish_translator(self):
        """Create a translator configured for Spanish."""
        return TokenTranslator(
            keyword_map=SPANISH_KEYWORDS, builtin_map=SPANISH_BUILTINS
        )

    @pytest.fixture
    def arabic_translator(self):
        """Create a translator configured for Arabic."""
        return TokenTranslator(keyword_map=ARABIC_KEYWORDS, builtin_map=ARABIC_BUILTINS)

    def test_translate_simple_function(self, spanish_translator):
        """Test translating a simple function definition."""
        code = "def greet():\n    print('Hello')"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert "definir" in translated  # 'def' → 'definir'
        assert "imprimir" in translated  # 'print' → 'imprimir'
        assert "greet" in translated  # function name unchanged
        assert "'Hello'" in translated  # string unchanged

    def test_translate_keywords(self, spanish_translator):
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

        assert "si" in translated  # 'if' → 'si'
        assert "Verdadero" in translated  # 'True' → 'Verdadero'
        assert "para" in translated  # 'for' → 'para'
        assert "en" in translated  # 'in' → 'en'
        assert "romper" in translated  # 'break' → 'romper'
        assert "sino" in translated  # 'else' → 'sino'
        assert "continuar" in translated  # 'continue' → 'continuar'

    def test_translate_return_statement(self, spanish_translator):
        """Test return statement translation."""
        code = "def calculate(x):\n    return x * 2"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert "definir" in translated  # 'def' → 'definir'
        assert "retornar" in translated  # 'return' → 'retornar'
        assert "calculate" in translated  # function name unchanged
        assert "x * 2" in translated  # expression unchanged

    def test_translate_class_definition(self, spanish_translator):
        """Test class definition translation."""
        code = "class MyClass:\n    pass"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert "clase" in translated  # 'class' → 'clase'
        assert "MyClass" in translated  # class name unchanged
        assert "pasar" in translated  # 'pass' → 'pasar'

    def test_preserve_indentation(self, spanish_translator):
        """Test that indentation is preserved exactly."""
        code = "def foo():\n    if True:\n        return 42"
        translated = spanish_translator.translate_code(code, "en", "es")

        # Check that structure is preserved
        lines = translated.split("\n")
        assert lines[0].startswith("definir")
        assert lines[1].startswith("    ")  # 4 spaces
        assert lines[2].startswith("        ")  # 8 spaces

    def test_preserve_comments(self, spanish_translator):
        """Test that comments are preserved unchanged."""
        code = "def foo():\n    # This is a comment\n    return 42"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert "# This is a comment" in translated  # Comment unchanged
        assert "definir" in translated  # 'def' → 'definir'
        assert "retornar" in translated  # 'return' → 'retornar'

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

    def test_arabic_translation(self, arabic_translator):
        """Test Arabic (RTL) translation."""
        code = "def greet():\n    print('Hello')"
        translated = arabic_translator.translate_code(code, "en", "ar")

        assert "تعريف" in translated  # 'def' → 'تعريف'
        assert "طباعة" in translated  # 'print' → 'طباعة'
        assert "greet" in translated  # function name unchanged

    def test_arabic_unicode_preservation(self, arabic_translator):
        """Test that Arabic Unicode characters are not corrupted."""
        code = "def foo():\n    return True"
        translated = arabic_translator.translate_code(code, "en", "ar")

        # Verify Arabic characters are present and valid UTF-8
        assert "تعريف" in translated
        assert "إرجاع" in translated
        assert "صحيح" in translated

        # Ensure we can encode/decode without errors
        translated.encode("utf-8").decode("utf-8")
