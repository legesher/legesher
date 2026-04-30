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


class TestCompoundKeywordLookahead:
    """Test compound keyword handling (e.g., except*)."""

    @pytest.fixture
    def compound_translator(self):
        """Translator with except* compound keyword mapping."""
        keywords = {
            "except": "ماعدا",
            "except*": "استثناء*",
            "try": "التجربة",
        }
        builtins = {"print": "طَبْع"}
        return TokenTranslator(keyword_map=keywords, builtin_map=builtins)

    def test_except_star_uses_compound_mapping(self, compound_translator):
        """except* should use the compound keyword mapping, not the base except."""
        code = "try:\n    pass\nexcept* ValueError:\n    pass"
        translated = compound_translator.translate_code(code)
        assert "استثناء" in translated
        assert "ماعدا" not in translated  # should NOT use base except mapping

    def test_regular_except_still_works(self, compound_translator):
        """Regular except (without *) should use base mapping."""
        code = "try:\n    pass\nexcept ValueError:\n    pass"
        translated = compound_translator.translate_code(code)
        assert "ماعدا" in translated
        assert "استثناء" not in translated

    def test_except_star_round_trip(self, compound_translator):
        """Compound keyword translates and the * is preserved."""
        code = "try:\n    pass\nexcept* ValueError:\n    pass"
        translated = compound_translator.translate_code(code)
        # The * operator should still be present
        assert "*" in translated


class TestReservedWordTranslation:
    """Test self/cls translation via reserved_word_map (CORE-710)."""

    def test_constructor_backward_compat_no_reserved_word_map(self):
        """Existing constructor (no reserved_word_map kwarg) still works."""
        translator = TokenTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
        )
        assert translator.mapper.reserved_word_map == {}

    def test_self_translation_via_reserved_word_map(self):
        """self in method signatures + body translates to pack value."""
        translator = TokenTranslator(
            keyword_map={"def": "definir", "return": "retornar"},
            builtin_map={"print": "imprimir"},
            reserved_word_map={"self": "propio"},
        )
        code = "def foo(self): return self.x"
        translated = translator.translate_code(code, "en", "es")
        assert "propio" in translated
        # Both signature AND attribute access translate to the same value
        assert translated.count("propio") == 2

    def test_cls_translation_in_classmethod(self):
        """cls in classmethod first-param + body translates to pack value."""
        translator = TokenTranslator(
            keyword_map={"def": "definir", "return": "retornar"},
            builtin_map={"print": "imprimir"},
            reserved_word_map={"cls": "clase_ref"},
        )
        code = "def make(cls): return cls()"
        translated = translator.translate_code(code, "en", "es")
        assert "clase_ref" in translated
        assert translated.count("clase_ref") == 2

    def test_dispatch_order_keyword_wins_on_conflict(self):
        """Synthetic conflict: same key in keyword_map AND reserved_word_map.

        Keyword section wins per the documented dispatch order.
        """
        translator = TokenTranslator(
            keyword_map={"self": "KEYWORD_WIN"},
            builtin_map={"print": "imprimir"},
            reserved_word_map={"self": "RESERVED_LOSE"},
        )
        translated = translator.translate_code("def foo(self): pass", "en", "es")
        assert "KEYWORD_WIN" in translated
        assert "RESERVED_LOSE" not in translated

    def test_unmapped_self_remains_untranslated(self):
        """Without reserved_word_map, self stays as-is (backward compat).

        Token translates def → definir but leaves self alone since the pack
        omitted reserved_words. This matches pre-CORE-710 behavior.
        """
        translator = TokenTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
        )
        translated = translator.translate_code("def foo(self): pass", "en", "es")
        assert "definir" in translated
        assert "self" in translated  # untouched

    def test_round_trip_preserves_self(self):
        """en → es → en restores self via reverse() of mapper."""
        en_to_es = TokenTranslator(
            keyword_map={"def": "definir", "return": "retornar"},
            builtin_map={"print": "imprimir"},
            reserved_word_map={"self": "propio"},
        )
        es_to_en = en_to_es.reverse()
        spanish = en_to_es.translate_code("def foo(self): return self.x", "en", "es")
        english = es_to_en.translate_code(spanish, "es", "en")
        assert "self" in english
        assert "propio" not in english

    def test_repr_includes_reserved_words_count(self):
        """__repr__ surfaces reserved_words count for debug visibility."""
        translator = TokenTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            reserved_word_map={"self": "propio", "cls": "clase"},
        )
        assert "reserved_words=2" in repr(translator)

    def test_from_language_pack_picks_up_reserved_words(self):
        """from_language_pack reads pack.reserved_words and threads to mapper.

        Post-CORE-710: all 51 packs ship reserved_words with self/cls.
        This test confirms the wire-up: from_language_pack reads pack.reserved_words
        and forwards it to the TokenMapper so translation lookups succeed.
        """
        translator = TokenTranslator.from_language_pack("es", "3.13")
        # Spanish pack ships self/cls translations
        assert translator.mapper.reserved_word_map.get("self") is not None
        assert translator.mapper.reserved_word_map.get("cls") is not None
        # Sanity: get_reserved_word returns the same value as the underlying map
        assert (
            translator.mapper.get_reserved_word("self")
            == (translator.mapper.reserved_word_map["self"])
        )
