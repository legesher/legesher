"""Unit tests for TreeSitterTranslator class.

Tests the tree-sitter-based translation functionality for keywords, builtins,
and formatting preservation. This test suite mirrors test_token_translator.py
to ensure API compatibility.
"""

import pytest

from legesher_core.tree_sitter.translator import TreeSitterTranslator


class TestTreeSitterTranslator:
    """Test suite for TreeSitterTranslator core functionality."""

    @pytest.fixture
    def spanish_translator(self, spanish_keywords, spanish_builtins):
        """Create a translator configured for Spanish."""
        return TreeSitterTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    @pytest.fixture
    def arabic_translator(self, arabic_keywords, arabic_builtins):
        """Create a translator configured for Arabic."""
        return TreeSitterTranslator(
            keyword_map=arabic_keywords, builtin_map=arabic_builtins
        )

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

        # Tree-sitter handles incomplete code - should still attempt translation
        # At minimum, should not crash and should return a string
        assert isinstance(result, str)

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

    def test_round_trip_translation(self, spanish_translator, spanish_keywords):
        """Test that EN → ES → EN produces equivalent code."""
        original = "def greet():\n    return True"

        # Translate to Spanish
        spanish = spanish_translator.translate_code(original, "en", "es")
        assert spanish_keywords["def"] in spanish
        assert spanish_keywords["return"] in spanish

        # Translate back to English
        es_to_en = spanish_translator.reverse()
        back_to_english = es_to_en.translate_code(spanish, "es", "en")

        # Keywords should be back to English
        assert "def" in back_to_english
        assert "return" in back_to_english

    def test_translate_builtins(self, spanish_translator, spanish_builtins):
        """Test translation of builtin function calls."""
        code = """
def example():
    x = len([1, 2, 3])
    print(x)
    return str(x)
"""
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_builtins["len"] in translated
        assert spanish_builtins["print"] in translated
        assert spanish_builtins["str"] in translated

    def test_translate_lambda(self, spanish_translator, spanish_keywords):
        """Test translation of lambda expressions."""
        code = "f = lambda x: x * 2"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["lambda"] in translated

    def test_translate_with_statement(self, spanish_translator, spanish_keywords):
        """Test translation of with statements."""
        code = "with open('file.txt') as f:\n    pass"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["with"] in translated
        assert spanish_keywords["as"] in translated
        assert spanish_keywords["pass"] in translated

    def test_translate_try_except(self, spanish_translator, spanish_keywords):
        """Test translation of try/except blocks."""
        code = """
try:
    x = 1 / 0
except ZeroDivisionError:
    pass
finally:
    print('done')
"""
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["try"] in translated
        assert spanish_keywords["except"] in translated
        assert spanish_keywords["finally"] in translated
        assert spanish_keywords["pass"] in translated

    def test_preserve_blank_lines(self, spanish_translator, spanish_keywords):
        """Test that blank lines are preserved."""
        code = "def foo():\n    pass\n\n\ndef bar():\n    pass"
        translated = spanish_translator.translate_code(code, "en", "es")

        # Count newlines
        assert code.count("\n") == translated.count("\n")

    def test_preserve_inline_comments(self, spanish_translator):
        """Test that inline comments are preserved."""
        code = "x = 42  # This is inline"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert "# This is inline" in translated

    def test_multiline_string_preservation(self, spanish_translator, spanish_keywords):
        """Test that multiline strings are preserved."""
        code = '''def foo():
    """This is
    a multiline
    docstring"""
    return True'''
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["def"] in translated
        assert spanish_keywords["return"] in translated
        assert "This is" in translated  # Docstring unchanged
        assert "multiline" in translated

    def test_reverse_translator(self, spanish_translator, spanish_keywords):
        """Test that reverse() creates a bidirectional translator."""
        reversed_translator = spanish_translator.reverse()

        # Translate Spanish back to English
        spanish_code = f"{spanish_keywords['def']} saludar():\n    {spanish_keywords['return']} {spanish_keywords['True']}"
        english = reversed_translator.translate_code(spanish_code, "es", "en")

        assert "def" in english
        assert "return" in english
        assert "True" in english

    def test_get_pack_info(self, spanish_translator):
        """Test get_pack_info returns correct metadata."""
        info = spanish_translator.get_pack_info()

        assert "python_version" in info
        assert "keyword_count" in info
        assert "builtin_count" in info
        assert info["keyword_count"] > 0
        assert info["builtin_count"] > 0

    def test_return_metadata_flag(self, spanish_translator, spanish_keywords):
        """Test that return_metadata flag works."""
        code = "def foo():\n    return 42"

        # Without metadata
        result = spanish_translator.translate_code(
            code, "en", "es", return_metadata=False
        )
        assert isinstance(result, str)

        # With metadata
        result, metadata = spanish_translator.translate_code(
            code, "en", "es", return_metadata=True
        )
        assert isinstance(result, str)
        assert metadata is not None

    def test_translate_boolean_operators(self, spanish_translator, spanish_keywords):
        """Test translation of boolean operators."""
        code = "if True and False or not None:\n    pass"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["and"] in translated
        assert spanish_keywords["or"] in translated
        assert spanish_keywords["not"] in translated

    def test_translate_import_statements(self, spanish_translator, spanish_keywords):
        """Test translation of import statements."""
        code = "import sys\nfrom os import path"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["import"] in translated
        assert spanish_keywords["from"] in translated

    def test_async_function_translation(self, spanish_translator, spanish_keywords):
        """Test translation of async/await keywords."""
        code = "async def fetch():\n    await something()"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["def"] in translated
        assert spanish_keywords["async"] in translated


class TestTreeSitterTranslatorClassMethods:
    """Test suite for TreeSitterTranslator class methods."""

    def test_from_language_pack_spanish(self, spanish_keywords):
        """Test creating translator from Spanish language pack."""
        translator = TreeSitterTranslator.from_language_pack("es")

        code = "def foo():\n    return True"
        translated = translator.translate_code(code, "en", "es")

        assert spanish_keywords["def"] in translated
        assert spanish_keywords["return"] in translated

    def test_from_language_pack_with_version(self):
        """Test creating translator with specific Python version."""
        translator = TreeSitterTranslator.from_language_pack(
            "es", python_version="3.13"
        )

        assert translator.python_version == "3.13"

    def test_list_available_languages(self):
        """Test listing available language packs."""
        languages = TreeSitterTranslator.list_available_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0

        # Each entry should be a (code, name) tuple
        for code, name in languages:
            assert isinstance(code, str)
            assert isinstance(name, str)


class TestTreeSitterTranslatorFileOperations:
    """Test suite for file-based operations."""

    @pytest.fixture
    def spanish_translator(self, spanish_keywords, spanish_builtins):
        """Create a translator configured for Spanish."""
        return TreeSitterTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    def test_translate_file(
        self, spanish_translator, spanish_keywords, spanish_builtins, tmp_path
    ):
        """Test translating a file."""
        # Create temporary Python file
        test_file = tmp_path / "test.py"
        test_file.write_text("def greet():\n    print('Hello')")

        # Translate file
        result = spanish_translator.translate_file(test_file, "es")

        assert spanish_keywords["def"] in result
        assert spanish_builtins["print"] in result


class TestTreeSitterTranslatorErrorHandling:
    """Test suite for error handling."""

    @pytest.fixture
    def spanish_translator(self, spanish_keywords, spanish_builtins):
        """Create a translator configured for Spanish."""
        return TreeSitterTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    def test_invalid_code_handling(self, spanish_translator):
        """Test handling of severely malformed code."""
        # Tree-sitter is more forgiving than tokenize, so this might translate
        malformed = "def def def class class"
        result = spanish_translator.translate_code(malformed, "en", "es")

        # Should not crash, should return a string
        assert isinstance(result, str)

    def test_unicode_handling(self, spanish_translator, spanish_keywords):
        """Test handling of various Unicode characters."""
        code = "def foo():\n    # Comment with emoji 🎉\n    return True"
        translated = spanish_translator.translate_code(code, "en", "es")

        assert "🎉" in translated  # Emoji preserved
        assert spanish_keywords["def"] in translated
        assert spanish_keywords["return"] in translated


class TestTreeSitterVsTokenComparison:
    """Tests comparing TreeSitter vs Token-based approaches."""

    def test_api_compatibility(self):
        """Test that TreeSitterTranslator has same API as TokenTranslator."""
        from legesher_core.transformer import TokenTranslator

        # Both should have the same public methods
        tree_sitter_methods = set(dir(TreeSitterTranslator))
        token_methods = set(dir(TokenTranslator))

        expected_methods = {
            "translate_code",
            "translate_file",
            "reverse",
            "from_language_pack",
            "list_available_languages",
            "get_pack_info",
        }

        assert expected_methods.issubset(tree_sitter_methods)
        assert expected_methods.issubset(token_methods)

    def test_same_output_simple_case(self, spanish_keywords, spanish_builtins):
        """Test that both translators produce similar output for simple cases."""
        from legesher_core.transformer import TokenTranslator

        code = "def greet():\n    return True"

        # Create both translators
        ts_translator = TreeSitterTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )
        token_translator = TokenTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

        # Translate with both
        ts_result = ts_translator.translate_code(code, "en", "es")
        token_result = token_translator.translate_code(code, "en", "es")

        # Both should have translated the keywords
        assert spanish_keywords["def"] in ts_result
        assert spanish_keywords["def"] in token_result
        assert spanish_keywords["return"] in ts_result
        assert spanish_keywords["return"] in token_result
