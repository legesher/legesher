"""Unit tests for TreeSitterTranslator class.

Tests the tree-sitter-based translation functionality for keywords, builtins,
and formatting preservation. This test suite mirrors test_token_translator.py
to ensure API compatibility.
"""

import sys

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


class TestTreeSitterUTF8Encoding:
    """Test suite for UTF-8 encoding edge cases (CORE-799).

    Validates that TreeSitterTranslator handles source files containing
    non-standard byte sequences in string literals, especially when
    translating to multi-byte languages (Chinese, Arabic, etc.).
    """

    @pytest.fixture
    def chinese_translator(self, chinese_keywords, chinese_builtins):
        """Create a translator configured for Chinese."""
        return TreeSitterTranslator(
            keyword_map=chinese_keywords, builtin_map=chinese_builtins
        )

    @pytest.fixture
    def arabic_translator(self, arabic_keywords, arabic_builtins):
        """Create a translator configured for Arabic."""
        return TreeSitterTranslator(
            keyword_map=arabic_keywords, builtin_map=arabic_builtins
        )

    @pytest.fixture
    def spanish_translator(self, spanish_keywords, spanish_builtins):
        """Create a translator configured for Spanish."""
        return TreeSitterTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    def test_control_char_u009f_with_chinese(
        self, chinese_translator, chinese_keywords
    ):
        """U+009F control character in string literal + CJK translation.

        This is the exact character from The Stack bug reports. The string
        contains U+009F which is valid Python but encodes to multi-byte UTF-8.
        With CJK translations (multi-byte replacements), the old byte-level
        approach would corrupt the output.
        """
        code = 'x = "\u009f"\ndef foo():\n    return True'
        result = chinese_translator.translate_code(code, "en", "zh")

        # Keywords must be translated (not returned as original)
        assert "def" not in result
        assert "return" not in result
        assert "True" not in result
        assert chinese_keywords["def"] in result
        assert chinese_keywords["return"] in result
        assert chinese_keywords["True"] in result

        # String content must be preserved
        assert "\u009f" in result

        # Result must be valid UTF-8
        result.encode("utf-8").decode("utf-8")

    def test_mixed_multibyte_content_preserved(
        self, chinese_translator, chinese_keywords
    ):
        """Code with emoji, CJK in strings, and translatable keywords."""
        code = 'def greet():\n    msg = "Hello 世界 🎉"\n    return True'
        result = chinese_translator.translate_code(code, "en", "zh")

        assert chinese_keywords["def"] in result
        assert chinese_keywords["return"] in result
        assert chinese_keywords["True"] in result
        assert "世界" in result
        assert "🎉" in result
        assert "greet" in result  # function name unchanged

    def test_rtl_with_control_characters(self, arabic_translator, arabic_keywords):
        """Arabic translations with U+009F and other control characters."""
        code = 'x = "\u009f\u0080"\ndef process():\n    if True:\n        return False'
        result = arabic_translator.translate_code(code, "en", "ar")

        assert arabic_keywords["def"] in result
        assert arabic_keywords["if"] in result
        assert arabic_keywords["True"] in result
        assert arabic_keywords["return"] in result
        assert arabic_keywords["False"] in result
        assert "\u009f" in result
        assert "\u0080" in result

        result.encode("utf-8").decode("utf-8")

    def test_multiple_non_ascii_chars_near_keywords(
        self, chinese_translator, chinese_keywords
    ):
        """Control characters \\x80, \\x8f, \\x9f in string literals near keywords."""
        code = (
            'a = "\u0080"\n'
            "if True:\n"
            '    b = "\u008f"\n'
            '    c = "\u009f"\n'
            "    return False\n"
        )
        result = chinese_translator.translate_code(code, "en", "zh")

        assert chinese_keywords["if"] in result
        assert chinese_keywords["True"] in result
        assert chinese_keywords["return"] in result
        assert chinese_keywords["False"] in result
        assert "\u0080" in result
        assert "\u008f" in result
        assert "\u009f" in result

    def test_large_file_with_scattered_control_chars(
        self, chinese_translator, chinese_keywords
    ):
        """50+ line file with control characters among many keywords."""
        lines = []
        for i in range(20):
            lines.append(f"def func_{i}(x):")
            lines.append(f"    if x > {i}:")
            lines.append("        return True")
            if i % 7 == 0:
                lines.append(f'    note = "data\u009f{i}"')
            lines.append("")

        code = "\n".join(lines)
        result = chinese_translator.translate_code(code, "en", "zh")

        assert "def" not in result
        assert chinese_keywords["def"] in result
        assert chinese_keywords["if"] in result
        assert chinese_keywords["return"] in result
        assert "\u009f" in result

        result.encode("utf-8").decode("utf-8")

    def test_byte_to_char_map_ascii(self):
        """Byte-to-char mapping for pure ASCII is identity."""
        source = "def foo(): return 42"
        mapping = TreeSitterTranslator._build_byte_to_char_map(source)

        for i in range(len(source)):
            assert mapping[i] == i
        assert mapping[len(source)] == len(source)

    def test_byte_to_char_map_multibyte(self):
        """Byte-to-char mapping handles multi-byte characters correctly."""
        # "a" (1 byte) + "é" (2 bytes) + "中" (3 bytes) + "🎉" (4 bytes)
        source = "aé中🎉"
        mapping = TreeSitterTranslator._build_byte_to_char_map(source)

        # 'a' at byte 0 → char 0
        assert mapping[0] == 0
        # 'é' at byte 1 → char 1
        assert mapping[1] == 1
        # '中' at byte 3 → char 2
        assert mapping[3] == 2
        # '🎉' at byte 6 → char 3
        assert mapping[6] == 3
        # End sentinel at byte 10 → char 4
        assert mapping[10] == 4

    def test_byte_to_char_map_control_chars(self):
        """Byte-to-char mapping handles U+009F (2-byte UTF-8) correctly."""
        # U+009F encodes as C2 9F in UTF-8 (2 bytes)
        source = "a\u009fb"
        mapping = TreeSitterTranslator._build_byte_to_char_map(source)

        assert mapping[0] == 0  # 'a' at byte 0
        assert mapping[1] == 1  # U+009F at byte 1
        assert mapping[3] == 2  # 'b' at byte 3
        assert mapping[4] == 3  # end sentinel

    def test_round_trip_with_control_chars_chinese(
        self, chinese_translator, chinese_keywords
    ):
        """EN→ZH→EN round-trip preserves code with control characters."""
        original = 'def foo():\n    x = "\u009f"\n    return True'

        translated = chinese_translator.translate_code(original, "en", "zh")
        assert chinese_keywords["def"] in translated

        reversed_t = chinese_translator.reverse()
        back = reversed_t.translate_code(translated, "zh", "en")

        assert "def" in back
        assert "return" in back
        assert "True" in back
        assert "\u009f" in back

    def test_spanish_ascii_translations_unaffected(
        self, spanish_translator, spanish_keywords
    ):
        """Spanish (ASCII-only translations) still works with control chars."""
        code = 'x = "\u009f"\ndef foo():\n    return True'
        result = spanish_translator.translate_code(code, "en", "es")

        assert spanish_keywords["def"] in result
        assert spanish_keywords["return"] in result
        assert "\u009f" in result


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


class TestTreeSitterReservedWordDispatch:
    """Test implicit_param_map dispatch in TreeSitterTranslator (CORE-710).

    Mirrors TestReservedWordTranslation in test_token_translator.py to
    confirm parity between the two backends. The Token + TreeSitter
    backends should yield identical output for any code that uses only
    keywords + builtins + implicit_params.
    """

    def test_constructor_backward_compat_no_implicit_param_map(self):
        """Existing constructor (no implicit_param_map kwarg) still works."""
        translator = TreeSitterTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
        )
        assert translator.mapper.implicit_param_map == {}

    def test_self_translation_via_implicit_param_map(self):
        """self in method signature + body translates to pack value."""
        translator = TreeSitterTranslator(
            keyword_map={"def": "definir", "return": "retornar", "class": "clase"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio"},
        )
        code = "class Foo:\n    def bar(self):\n        return self.x\n"
        translated = translator.translate_code(code, "en", "es")
        assert "propio" in translated
        # Both signature AND attribute access render to same value
        assert translated.count("propio") == 2

    def test_cls_translation_in_classmethod(self):
        """cls in classmethod signature + body translates to pack value."""
        translator = TreeSitterTranslator(
            keyword_map={"def": "definir", "return": "retornar", "class": "clase"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"cls": "clase_ref"},
        )
        code = "class Foo:\n    def make(cls):\n        return cls()\n"
        translated = translator.translate_code(code, "en", "es")
        assert "clase_ref" in translated
        assert translated.count("clase_ref") == 2

    def test_dispatch_order_keyword_wins_on_conflict(self):
        """Synthetic conflict: keyword section wins over implicit_param section."""
        translator = TreeSitterTranslator(
            keyword_map={"self": "KEYWORD_WIN"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "RESERVED_LOSE"},
        )
        translated = translator.translate_code("def foo(self): pass", "en", "es")
        assert "KEYWORD_WIN" in translated
        assert "RESERVED_LOSE" not in translated

    def test_unmapped_self_remains_untranslated(self):
        """Without implicit_param_map, self stays as-is (backward compat).

        Pre-CORE-710 behavior: tree-sitter translates def → definir but
        leaves self untouched since the pack doesn't ship implicit_params.
        """
        translator = TreeSitterTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
        )
        translated = translator.translate_code("def foo(self): pass", "en", "es")
        assert "definir" in translated
        assert "self" in translated  # untouched

    def test_round_trip_preserves_self(self):
        """en → es → en restores self via reverse() of mapper."""
        en_to_es = TreeSitterTranslator(
            keyword_map={"def": "definir", "return": "retornar"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio"},
        )
        es_to_en = en_to_es.reverse()
        spanish = en_to_es.translate_code("def foo(self): return self.x", "en", "es")
        english = es_to_en.translate_code(spanish, "es", "en")
        assert "self" in english
        assert "propio" not in english

    def test_repr_includes_implicit_params_count(self):
        """__repr__ surfaces implicit_params count for debug visibility."""
        translator = TreeSitterTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio", "cls": "clase"},
        )
        assert "implicit_params=2" in repr(translator)

    def test_token_and_tree_sitter_parity_for_implicit_params(self):
        """The two backends produce identical output for self/cls translation.

        Locks in feature parity at the substitution layer. If a future
        change lands implicit_param_map handling on one backend but not
        the other, this test will catch it.
        """
        from legesher_core.transformer import TokenTranslator

        kwargs = dict(
            keyword_map={"def": "definir", "return": "retornar", "class": "clase"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio", "cls": "clase_ref"},
        )
        token = TokenTranslator(**kwargs)
        tree_sitter = TreeSitterTranslator(**kwargs)

        code = (
            "class Foo:\n"
            "    def __init__(self):\n"
            "        self.x = 1\n"
            "    @classmethod\n"
            "    def make(cls):\n"
            "        return cls()\n"
        )
        token_out = token.translate_code(code, "en", "es")
        ts_out = tree_sitter.translate_code(code, "en", "es")

        # Both should translate self → propio and cls → clase_ref
        assert "propio" in token_out
        assert "propio" in ts_out
        assert "clase_ref" in token_out
        assert "clase_ref" in ts_out
        # Both should have the same count of reserved-word substitutions
        assert token_out.count("propio") == ts_out.count("propio")
        assert token_out.count("clase_ref") == ts_out.count("clase_ref")


class TestVersionedKeywordParity:
    """`except*` (PEP 654, 3.11+) and `type` (PEP 695, 3.12+) — CORE-1345.

    Both constructs used to translate on the token backend but not on the
    tree-sitter one, so the two backends silently disagreed on the same
    source. Because Legesher's clean/smudge filters must be exact inverses,
    a mixed-backend team could produce round-trip asymmetries.

    Every test here asserts the two backends agree, not just that the
    tree-sitter output looks right in isolation — that parity is the
    property that keeps the two implementations pinned together.

    Translation itself is host-version independent (``tokenize`` is a lexer
    and the tree-sitter grammar carries its own Python rules), so the parity
    assertions run on every supported interpreter. Only the assertions that
    ``compile()`` the fixture are gated on the interpreter floor.
    """

    #: `except`/`except*` deliberately render differently, the shape that
    #: exposes the bug. Packs where they coincide (e.g. es) mask it.
    DIVERGENT_KEYWORDS = {
        "try": "التجربة",
        "except": "ماعدا",
        "except*": "استثناء*",
        "type": "النوع",
        "pass": "مرور",
    }
    DIVERGENT_BUILTINS = {"print": "طَبْع", "type": "نوع", "list": "قائمة"}

    EXCEPT_STAR = "try:\n    pass\nexcept* ValueError:\n    pass\n"
    TYPE_ALIAS = "type Vec = list[float]\n"

    @pytest.fixture
    def backends(self):
        """A (token, tree-sitter) pair sharing one divergent-rendering pack."""
        from legesher_core.transformer import TokenTranslator

        kwargs = dict(
            keyword_map=dict(self.DIVERGENT_KEYWORDS),
            builtin_map=dict(self.DIVERGENT_BUILTINS),
        )
        return TokenTranslator(**kwargs), TreeSitterTranslator(**kwargs)

    # ---- except* (PEP 654) -------------------------------------------------

    def test_except_star_uses_compound_mapping(self, backends):
        """Tree-sitter must use the `except*` entry, not the bare `except`."""
        _, tree_sitter = backends
        translated = tree_sitter.translate_code(self.EXCEPT_STAR, "en", "ar")
        assert "استثناء" in translated
        assert "ماعدا" not in translated  # the bare `except` rendering
        assert "*" in translated  # the `*` token is left in place

    def test_plain_except_still_uses_base_mapping(self, backends):
        """A `*`-less `except` must keep using the bare entry."""
        _, tree_sitter = backends
        code = "try:\n    pass\nexcept ValueError:\n    pass\n"
        translated = tree_sitter.translate_code(code, "en", "ar")
        assert "ماعدا" in translated
        assert "استثناء" not in translated

    def test_except_star_backend_parity(self, backends):
        """Both backends emit byte-identical output for `except*`."""
        token, tree_sitter = backends
        assert token.translate_code(
            self.EXCEPT_STAR, "en", "ar"
        ) == tree_sitter.translate_code(self.EXCEPT_STAR, "en", "ar")

    # ---- type (PEP 695) ----------------------------------------------------

    def test_type_statement_translates(self, backends):
        """Statement-position `type` must translate, not stay English."""
        _, tree_sitter = backends
        translated = tree_sitter.translate_code(self.TYPE_ALIAS, "en", "ar")
        assert translated.startswith("النوع ")
        assert "type" not in translated

    def test_type_statement_backend_parity(self, backends):
        """Both backends emit byte-identical output for a `type` statement."""
        token, tree_sitter = backends
        assert token.translate_code(
            self.TYPE_ALIAS, "en", "ar"
        ) == tree_sitter.translate_code(self.TYPE_ALIAS, "en", "ar")

    def test_generic_type_alias_backend_parity(self, backends):
        """A PEP 695 alias with type parameters also stays at parity."""
        token, tree_sitter = backends
        code = "type Alias[T] = list[T]\n"
        assert token.translate_code(code, "en", "ar") == tree_sitter.translate_code(
            code, "en", "ar"
        )

    @pytest.mark.parametrize(
        "code",
        [
            "x: int = 3\n",
            "def f(x: type) -> type:\n    return x\n",
            "y = type(3)\n",
        ],
        ids=["annotated-assign", "type-annotation", "builtin-call"],
    )
    def test_named_type_nodes_are_not_rewritten(self, backends, code):
        """Only the anonymous `type` token is the PEP 695 keyword.

        The grammar also emits *named* `type` nodes wrapping arbitrary type
        expressions. Translating those would both mangle annotations and
        queue a replacement overlapping the one for the identifier inside
        them, corrupting the output. Parity with the token backend — which
        has no such node — is the check.
        """
        token, tree_sitter = backends
        assert token.translate_code(code, "en", "ar") == tree_sitter.translate_code(
            code, "en", "ar"
        )

    # ---- round-trip --------------------------------------------------------

    @pytest.mark.parametrize(
        "code",
        [EXCEPT_STAR, TYPE_ALIAS],
        ids=["except-star", "type-alias"],
    )
    def test_round_trip_through_tree_sitter(self, backends, code):
        """en → native → en is the identity on the tree-sitter path.

        The reverse leg matters as much as the forward one: a native
        `except*` rendering reaches the grammar as an identifier followed by
        `*`, so the compound entry has to win there too.
        """
        _, tree_sitter = backends
        native = tree_sitter.translate_code(code, "en", "ar")
        assert tree_sitter.reverse().translate_code(native, "ar", "en") == code

    @pytest.mark.parametrize(
        "code",
        [EXCEPT_STAR, TYPE_ALIAS],
        ids=["except-star", "type-alias"],
    )
    def test_cross_backend_round_trip(self, backends, code):
        """Clean on one backend, smudge on the other, still the identity.

        This is the asymmetry the bug could produce in a mixed-backend team:
        a file cleaned by the token filter and smudged by the tree-sitter
        one (or the reverse) has to come back unchanged.
        """
        token, tree_sitter = backends
        assert (
            tree_sitter.reverse().translate_code(
                token.translate_code(code, "en", "ar"), "ar", "en"
            )
            == code
        )
        assert (
            token.reverse().translate_code(
                tree_sitter.translate_code(code, "en", "ar"), "ar", "en"
            )
            == code
        )

    # ---- real shipped packs ------------------------------------------------

    @pytest.mark.parametrize("language", ["es", "ar"])
    @pytest.mark.parametrize("python_version", ["3.12", "3.13", "3.14"])
    def test_shipped_pack_parity(self, language, python_version):
        """Parity on the real packs, across the versions that define both.

        `except*` needs a 3.11+ pack and `type` a 3.12+ one; 3.12 is the
        first version whose inherited pack carries both.
        """
        from legesher_core.transformer import TokenTranslator

        token = TokenTranslator.from_language_pack(language, python_version)
        tree_sitter = TreeSitterTranslator.from_language_pack(language, python_version)
        code = self.EXCEPT_STAR + self.TYPE_ALIAS
        native = token.translate_code(code, "en", language)
        assert tree_sitter.translate_code(code, "en", language) == native
        assert tree_sitter.reverse().translate_code(native, language, "en") == code

    # ---- interpreter floor -------------------------------------------------

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="`except*` is 3.11+ syntax")
    def test_except_star_fixture_is_valid_python(self):
        """Guard the fixture itself on interpreters that can parse it."""
        compile(self.EXCEPT_STAR, "<fixture>", "exec")

    @pytest.mark.skipif(
        sys.version_info < (3, 12), reason="`type` statements are 3.12+ syntax"
    )
    def test_type_alias_fixture_is_valid_python(self):
        """Guard the fixture itself on interpreters that can parse it."""
        compile(self.TYPE_ALIAS, "<fixture>", "exec")
