"""Round-trip translation tests.

Tests that EN → ES → EN and EN → AR → EN translations are lossless,
ensuring the translation engine preserves code semantics perfectly.
Uses real language pack translations.
"""

import pytest

from legesher_core.transformer import TokenTranslator


class TestRoundTripTranslation:
    """Test suite for round-trip translation (lossless verification)."""

    @pytest.fixture
    def en_to_es_translator(self, spanish_keywords, spanish_builtins):
        """English to Spanish translator."""
        return TokenTranslator(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    @pytest.fixture
    def es_to_en_translator(
        self, english_keywords_from_spanish, english_builtins_from_spanish
    ):
        """Spanish to English translator."""
        return TokenTranslator(
            keyword_map=english_keywords_from_spanish,
            builtin_map=english_builtins_from_spanish,
        )

    @pytest.fixture
    def en_to_ar_translator(self, arabic_keywords, arabic_builtins):
        """English to Arabic translator."""
        return TokenTranslator(keyword_map=arabic_keywords, builtin_map=arabic_builtins)

    @pytest.fixture
    def ar_to_en_translator(
        self, english_keywords_from_arabic, english_builtins_from_arabic
    ):
        """Arabic to English translator."""
        return TokenTranslator(
            keyword_map=english_keywords_from_arabic,
            builtin_map=english_builtins_from_arabic,
        )

    def test_simple_function_round_trip_spanish(
        self,
        en_to_es_translator,
        es_to_en_translator,
        spanish_keywords,
        spanish_builtins,
    ):
        """Test EN → ES → EN for simple function."""
        original = "def greet():\n    print('Hello')"

        # Translate to Spanish
        spanish = en_to_es_translator.translate_code(original, "en", "es")
        assert spanish_keywords["def"] in spanish
        assert spanish_builtins["print"] in spanish

        # Translate back to English
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        # Should be byte-for-byte identical
        assert original == back_to_english

    def test_complex_code_round_trip_spanish(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test EN → ES → EN for complex code."""
        original = """def calculate_tax(income, rate):
    if income > 100000:
        return income * rate
    else:
        return 0
"""

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert original == back_to_english

    def test_round_trip_with_comments_spanish(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test round-trip with comments preserved."""
        original = """def foo():
    # This is a comment
    return 42
"""

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert original == back_to_english
        assert "# This is a comment" in spanish  # Comment unchanged

    def test_simple_function_round_trip_arabic(
        self, en_to_ar_translator, ar_to_en_translator, arabic_keywords, arabic_builtins
    ):
        """Test EN → AR → EN for simple function (RTL)."""
        original = "def greet():\n    print('Hello')"

        # Translate to Arabic
        arabic = en_to_ar_translator.translate_code(original, "en", "ar")
        assert arabic_keywords["def"] in arabic
        assert arabic_builtins["print"] in arabic

        # Translate back to English
        back_to_english = ar_to_en_translator.translate_code(arabic, "ar", "en")

        # Should be byte-for-byte identical
        assert original == back_to_english

    def test_complex_code_round_trip_arabic(
        self, en_to_ar_translator, ar_to_en_translator
    ):
        """Test EN → AR → EN for complex code (RTL)."""
        original = """def calculate_tax(income, rate):
    if income > 100000:
        return income * rate
    else:
        return 0
"""

        arabic = en_to_ar_translator.translate_code(original, "en", "ar")
        back_to_english = ar_to_en_translator.translate_code(arabic, "ar", "en")

        assert original == back_to_english

    def test_round_trip_preserves_indentation(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test round-trip preserves exact indentation."""
        original = """def outer():
    def inner():
        if True:
            return 42
"""

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert original == back_to_english

        # Verify indentation levels
        lines = original.split("\n")
        back_lines = back_to_english.split("\n")
        for orig_line, back_line in zip(lines, back_lines):
            orig_indent = len(orig_line) - len(orig_line.lstrip())
            back_indent = len(back_line) - len(back_line.lstrip())
            assert orig_indent == back_indent

    def test_round_trip_all_keywords(self, en_to_es_translator, es_to_en_translator):
        """Test round-trip with many keywords."""
        original = """
async def process():
    try:
        for i in range(10):
            if i > 5:
                break
            elif i < 2:
                continue
            else:
                pass

        while True:
            await fetch()

        with open("file.txt") as f:
            data = f.read()

    except Exception:
        raise
    finally:
        cleanup()

    return True
"""

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert original == back_to_english

    def test_round_trip_preserves_blank_lines(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test round-trip preserves blank lines."""
        original = """def foo():
    x = 1

    z = 2


    return x + z
"""

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert original == back_to_english
        assert original.count("\n\n") == back_to_english.count("\n\n")

    def test_round_trip_unicode_identifiers(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test round-trip with Unicode identifiers."""
        original = "def café():\n    return '☕'"

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert original == back_to_english
        assert "café" in spanish
        assert "☕" in spanish

    def test_arabic_unicode_not_corrupted(self, en_to_ar_translator, arabic_keywords):
        """Test that Arabic Unicode survives tokenization."""
        original = "def calculate_tax(income):\n    return income * 0.25"

        arabic = en_to_ar_translator.translate_code(original, "en", "ar")

        arabic_bytes = arabic.encode("utf-8")
        decoded = arabic_bytes.decode("utf-8")
        assert decoded == arabic

        assert arabic_keywords["def"] in arabic
        assert arabic_keywords["return"] in arabic

    def test_round_trip_mixed_ltr_rtl(
        self, en_to_ar_translator, ar_to_en_translator, arabic_keywords
    ):
        """Test round-trip with mixed LTR/RTL content."""
        original = "def calculate_tax(income):\n    return income * rate"

        arabic = en_to_ar_translator.translate_code(original, "en", "ar")

        assert arabic_keywords["def"] in arabic
        assert "calculate_tax" in arabic
        assert "income" in arabic

        back = ar_to_en_translator.translate_code(arabic, "ar", "en")
        assert original == back
