"""Round-trip translation tests.

Tests that EN → ES → EN and EN → AR → EN translations are lossless,
ensuring the translation engine preserves code semantics perfectly.
"""

import pytest

from legesher_core.transformer import TokenTranslator
from tests.data.keyword_maps_spanish import (
    SPANISH_KEYWORDS,
    SPANISH_BUILTINS,
    ENGLISH_KEYWORDS,
    ENGLISH_BUILTINS,
)
from tests.data.keyword_maps_arabic import (
    ARABIC_KEYWORDS,
    ARABIC_BUILTINS,
    ENGLISH_KEYWORDS as AR_ENGLISH_KEYWORDS,
    ENGLISH_BUILTINS as AR_ENGLISH_BUILTINS,
)


class TestRoundTripTranslation:
    """Test suite for round-trip translation (lossless verification)."""

    @pytest.fixture
    def en_to_es_translator(self):
        """English to Spanish translator."""
        return TokenTranslator(
            keyword_map=SPANISH_KEYWORDS, builtin_map=SPANISH_BUILTINS
        )

    @pytest.fixture
    def es_to_en_translator(self):
        """Spanish to English translator."""
        return TokenTranslator(
            keyword_map=ENGLISH_KEYWORDS, builtin_map=ENGLISH_BUILTINS
        )

    @pytest.fixture
    def en_to_ar_translator(self):
        """English to Arabic translator."""
        return TokenTranslator(keyword_map=ARABIC_KEYWORDS, builtin_map=ARABIC_BUILTINS)

    @pytest.fixture
    def ar_to_en_translator(self):
        """Arabic to English translator."""
        return TokenTranslator(
            keyword_map=AR_ENGLISH_KEYWORDS, builtin_map=AR_ENGLISH_BUILTINS
        )

    def test_simple_function_round_trip_spanish(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test EN → ES → EN for simple function."""
        original = "def greet():\n    print('Hello')"

        # Translate to Spanish
        spanish = en_to_es_translator.translate_code(original, "en", "es")
        assert "definir" in spanish
        assert "imprimir" in spanish

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
        self, en_to_ar_translator, ar_to_en_translator
    ):
        """Test EN → AR → EN for simple function (RTL)."""
        original = "def greet():\n    print('Hello')"

        # Translate to Arabic
        arabic = en_to_ar_translator.translate_code(original, "en", "ar")
        assert "تعريف" in arabic
        assert "طباعة" in arabic

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
            # Count leading spaces
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
        # Verify blank lines count
        assert original.count("\n\n") == back_to_english.count("\n\n")

    def test_round_trip_unicode_identifiers(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test round-trip with Unicode identifiers."""
        original = "def café():\n    return '☕'"

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert original == back_to_english
        assert "café" in spanish  # Unicode identifier preserved
        assert "☕" in spanish  # Unicode in string preserved

    def test_arabic_unicode_not_corrupted(self, en_to_ar_translator):
        """Test that Arabic Unicode survives tokenization."""
        original = "def calculate_tax(income):\n    return income * 0.25"

        # Translate to Arabic
        arabic = en_to_ar_translator.translate_code(original, "en", "ar")

        # Verify Arabic characters are valid UTF-8
        arabic_bytes = arabic.encode("utf-8")
        decoded = arabic_bytes.decode("utf-8")
        assert decoded == arabic

        # Verify specific Arabic keywords present
        assert "تعريف" in arabic  # def
        assert "إرجاع" in arabic  # return

    def test_round_trip_mixed_ltr_rtl(self, en_to_ar_translator, ar_to_en_translator):
        """Test round-trip with mixed LTR/RTL content."""
        # English identifiers with Arabic keywords
        original = "def calculate_tax(income):\n    return income * rate"

        arabic = en_to_ar_translator.translate_code(original, "en", "ar")

        # Arabic keywords + English identifiers
        assert "تعريف" in arabic
        assert "calculate_tax" in arabic
        assert "income" in arabic

        back = ar_to_en_translator.translate_code(arabic, "ar", "en")
        assert original == back
