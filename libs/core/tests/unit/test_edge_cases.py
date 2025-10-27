"""Edge case tests for TokenTranslator.

Tests handling of incomplete code, syntax errors, encoding issues,
and other edge cases that might occur during real-world usage.
"""

import pytest

from legesher_core.transformer import TokenTranslator
from tests.data.keyword_maps_spanish import SPANISH_KEYWORDS, SPANISH_BUILTINS


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.fixture
    def translator(self):
        """Create a Spanish translator for testing."""
        return TokenTranslator(
            keyword_map=SPANISH_KEYWORDS, builtin_map=SPANISH_BUILTINS
        )

    def test_empty_file(self, translator):
        """Test handling of completely empty file."""
        result = translator.translate_code("", "en", "es")
        assert result == ""

    def test_whitespace_only(self, translator):
        """Test file with only whitespace."""
        result = translator.translate_code("   \n\t\n  ", "en", "es")
        assert result == "   \n\t\n  "

    def test_comments_only_file(self, translator):
        """Test file containing only comments."""
        code = "# Comment 1\n# Comment 2\n# Comment 3"
        result = translator.translate_code(code, "en", "es")
        assert result == code  # Comments should be unchanged

    def test_incomplete_function_definition(self, translator):
        """Test incomplete function (missing closing paren)."""
        incomplete = "def foo(\n    x: int"
        result = translator.translate_code(incomplete, "en", "es")
        # Should return original when tokenization fails
        assert result == incomplete

    def test_incomplete_string(self, translator):
        """Test incomplete string literal.

        Note: Python 3.10-3.12 successfully tokenizes this and translates,
        while Python 3.13+ fails tokenization. We accept both behaviors.
        """
        incomplete = "def foo():\n    x = 'unclosed string"
        result = translator.translate_code(incomplete, "en", "es")
        # Either returns original OR translates successfully (version dependent)
        assert result == incomplete or "definir" in result

    def test_syntax_error_reversed_parens(self, translator):
        """Test syntax error with reversed parentheses.

        Note: Python 3.10-3.12 successfully tokenizes this and translates,
        while Python 3.13+ may fail tokenization. We accept both behaviors.
        """
        invalid = "def foo)(:\n    pass"
        result = translator.translate_code(invalid, "en", "es")
        # Either returns original OR translates successfully (version dependent)
        assert result == invalid or "definir" in result

    def test_mixed_indentation(self, translator):
        """Test code with mixed tabs and spaces (valid Python 3)."""
        code = "def foo():\n\tif True:\n\t    return 42"
        result = translator.translate_code(code, "en", "es")
        # Should translate keywords and preserve indentation
        assert "definir" in result
        assert "si" in result
        assert "retornar" in result
        assert "\t" in result  # Tabs preserved

    def test_very_long_line(self, translator):
        """Test handling of very long lines."""
        # Create a line with 1000 characters
        long_code = "x = " + " + ".join(["1"] * 500)
        result = translator.translate_code(long_code, "en", "es")
        assert result == long_code  # No keywords/builtins, unchanged

    def test_deeply_nested_code(self, translator):
        """Test deeply nested control structures."""
        code = """
def foo():
    if True:
        for i in range(10):
            while i > 0:
                if i % 2:
                    return i
"""
        result = translator.translate_code(code, "en", "es")
        assert "definir" in result
        assert "si" in result
        assert "para" in result
        assert "mientras" in result
        assert "retornar" in result

    def test_multiline_string_preservation(self, translator):
        """Test that multiline strings are preserved."""
        code = '''def foo():
    """This is a
    multiline
    docstring"""
    return 42'''
        result = translator.translate_code(code, "en", "es")
        assert "definir" in result
        assert "retornar" in result
        assert "This is a" in result
        assert "multiline" in result
        assert "docstring" in result

    def test_raw_string_preservation(self, translator):
        """Test that raw strings are preserved."""
        code = 'def foo():\n    path = r"C:/Users/test"'
        result = translator.translate_code(code, "en", "es")
        assert "definir" in result
        assert "C:/Users/test" in result

    def test_f_string_preservation(self, translator):
        """Test that f-strings are preserved."""
        code = 'def foo(name):\n    return f"Hello {name}"'
        result = translator.translate_code(code, "en", "es")
        assert "definir" in result
        assert "retornar" in result
        assert 'f"Hello {name}"' in result

    def test_lambda_translation(self, translator):
        """Test lambda function translation."""
        code = "f = lambda x: x * 2"
        result = translator.translate_code(code, "en", "es")
        # 'lambda' stays same in Spanish per our maps
        assert "lambda" in result

    def test_list_comprehension(self, translator):
        """Test list comprehension translation."""
        code = "result = [x for x in range(10) if x > 5]"
        result = translator.translate_code(code, "en", "es")
        assert "para" in result  # 'for' → 'para'
        assert "en" in result  # 'in' → 'en'
        assert "si" in result  # 'if' → 'si'
        assert "rango" in result  # 'range' → 'rango'

    def test_multiple_statements_one_line(self, translator):
        """Test multiple statements on one line (semicolons)."""
        code = "x = 1; y = 2; print(x + y)"
        result = translator.translate_code(code, "en", "es")
        assert "imprimir" in result  # 'print' → 'imprimir'

    def test_decorator_preservation(self, translator):
        """Test that decorators are preserved."""
        code = "@decorator\ndef foo():\n    pass"
        result = translator.translate_code(code, "en", "es")
        assert "@decorator" in result
        assert "definir" in result
        assert "pasar" in result

    def test_async_def_translation(self, translator):
        """Test async function definition."""
        code = "async def fetch():\n    await request()"
        result = translator.translate_code(code, "en", "es")
        assert "asincrono" in result  # 'async' → 'asincrono'
        assert "definir" in result  # 'def' → 'definir'
        assert "esperar" in result  # 'await' → 'esperar'

    def test_exception_handling(self, translator):
        """Test try/except/finally translation."""
        code = """
try:
    risky_operation()
except ValueError:
    print("Error")
finally:
    cleanup()
"""
        result = translator.translate_code(code, "en", "es")
        assert "intentar" in result  # 'try' → 'intentar'
        assert "excepto" in result  # 'except' → 'excepto'
        assert "imprimir" in result  # 'print' → 'imprimir'
        assert "finalmente" in result  # 'finally' → 'finalmente'

    def test_context_manager(self, translator):
        """Test with statement translation."""
        code = 'with open("file.txt") as f:\n    content = f.read()'
        result = translator.translate_code(code, "en", "es")
        assert "con" in result  # 'with' → 'con'
        assert "abrir" in result  # 'open' → 'abrir'
        assert "como" in result  # 'as' → 'como'

    def test_global_and_nonlocal(self, translator):
        """Test global and nonlocal keyword translation."""
        code = """
def outer():
    x = 1
    def inner():
        nonlocal x
        global y
        x = 2
"""
        result = translator.translate_code(code, "en", "es")
        assert "nolocal" in result  # 'nonlocal' → 'nolocal'
        assert "global" in result  # 'global' → 'global'

    def test_type_hints_preservation(self, translator):
        """Test that type hints are preserved."""
        code = "def add(a: int, b: int) -> int:\n    return a + b"
        result = translator.translate_code(code, "en", "es")
        assert "definir" in result
        assert "entero" in result  # 'int' → 'entero' (builtin)
        assert "retornar" in result

    def test_walrus_operator(self, translator):
        """Test walrus operator (:=) preservation."""
        code = "if (n := len(items)) > 10:\n    print(n)"
        result = translator.translate_code(code, "en", "es")
        assert "si" in result  # 'if' → 'si'
        assert "longitud" in result  # 'len' → 'longitud'
        assert "imprimir" in result  # 'print' → 'imprimir'
        assert ":=" in result  # Walrus operator preserved

    def test_match_case_statement(self, translator):
        """Test match/case statement (Python 3.10+)."""
        # Note: match/case are not in our keyword maps yet
        code = """
match value:
    case 1:
        print("one")
    case _:
        pass
"""
        result = translator.translate_code(code, "en", "es")
        # match/case won't be translated (not in maps)
        # but other keywords should be
        assert "imprimir" in result
        assert "pasar" in result

    def test_encoding_detection_utf8(self, translator, tmp_path):
        """Test UTF-8 file encoding detection."""
        test_file = tmp_path / "test_utf8.py"
        test_file.write_text("def foo():\n    return 42", encoding="utf-8")

        result = translator.translate_file(test_file, "es")
        assert "definir" in result
        assert "retornar" in result

    def test_user_defined_function_not_translated(self, translator):
        """Test that user-defined functions are NOT translated."""
        code = "def print_message():\n    print('test')"
        result = translator.translate_code(code, "en", "es")
        # 'def' is translated, but 'print_message' is not
        assert "definir" in result
        assert "print_message" in result  # User function name unchanged
        assert "imprimir" in result  # builtin 'print' is translated
