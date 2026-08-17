"""Round-trip translation tests.

Tests that EN → ES → EN and EN → AR → EN translations are lossless,
ensuring the translation engine preserves code semantics perfectly.
Uses real language pack translations.
"""

import pytest

from legesher_core.round_trip import first_divergence
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
        assert first_divergence(original, back_to_english) is None

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

        assert first_divergence(original, back_to_english) is None

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

        assert first_divergence(original, back_to_english) is None
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
        assert first_divergence(original, back_to_english) is None

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

        assert first_divergence(original, back_to_english) is None

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

        assert first_divergence(original, back_to_english) is None

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

        assert first_divergence(original, back_to_english) is None

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

        assert first_divergence(original, back_to_english) is None
        assert original.count("\n\n") == back_to_english.count("\n\n")

    def test_round_trip_unicode_identifiers(
        self, en_to_es_translator, es_to_en_translator
    ):
        """Test round-trip with Unicode identifiers."""
        original = "def café():\n    return '☕'"

        spanish = en_to_es_translator.translate_code(original, "en", "es")
        back_to_english = es_to_en_translator.translate_code(spanish, "es", "en")

        assert first_divergence(original, back_to_english) is None
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
        assert first_divergence(original, back) is None


class TestRoundTripWhitespace:
    """Tests documenting CRLF normalization behavior (CORE-1160).

    The translator's normalize_newlines() converts \\r\\n → \\n during
    translation. This is expected behavior — canonical storage uses LF.
    Round-trip is lossless for LF-only input; CRLF input normalizes to LF.
    """

    @pytest.fixture
    def en_to_es(self, translator_class, spanish_keywords, spanish_builtins):
        return translator_class(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    @pytest.fixture
    def es_to_en(
        self,
        translator_class,
        english_keywords_from_spanish,
        english_builtins_from_spanish,
    ):
        return translator_class(
            keyword_map=english_keywords_from_spanish,
            builtin_map=english_builtins_from_spanish,
        )

    def test_crlf_normalized_to_lf(self, en_to_es, es_to_en):
        """CRLF input produces LF output — expected normalization (CORE-1160)."""
        crlf_code = "def foo():\r\n    return True\r\n"
        lf_code = "def foo():\n    return True\n"

        spanish = en_to_es.translate_code(crlf_code, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        # Round-trip normalizes CRLF to LF — this is intentional
        assert "\r\n" not in back
        assert back == lf_code

    def test_lf_only_round_trips_perfectly(self, en_to_es, es_to_en):
        """LF-only code round-trips without any modification."""
        original = "def foo():\n    return True\n"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None

    def test_trailing_newline_preserved(self, en_to_es, es_to_en):
        """Trailing newline is preserved through round-trip."""
        original = "def foo():\n    pass\n"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None
        assert back.endswith("\n")

    def test_blank_lines_preserved(self, en_to_es, es_to_en):
        """Blank lines between code blocks are preserved."""
        original = "def foo():\n    pass\n\n\ndef bar():\n    pass\n"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None

    def test_multiple_trailing_newlines_preserved(self, en_to_es, es_to_en):
        """Multiple trailing newlines are preserved."""
        original = "def foo():\n    pass\n\n\n"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None

    def test_mixed_crlf_lf_normalized(self, en_to_es, es_to_en):
        """Mixed CRLF and LF lines are all normalized to LF."""
        mixed = "def foo():\r\n    x = 1\n    return x\r\n"
        expected = "def foo():\n    x = 1\n    return x\n"

        spanish = en_to_es.translate_code(mixed, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert "\r\n" not in back
        assert back == expected


class TestLatinScriptCollision:
    """Tests documenting Latin-script reverse collision (CORE-704).

    When Spanish translations of builtins are common English words (e.g.,
    ``todo`` = ``all``, ``tipo`` = ``type``, ``objeto`` = ``object``,
    ``entrada`` = ``input``), the reverse translator incorrectly maps
    English variable names that happen to match Spanish builtins back to
    their English builtin equivalents.

    Non-Latin scripts (e.g., Chinese) are immune because CJK characters
    never appear as identifiers in English source code.
    """

    @pytest.fixture
    def en_to_es(self, translator_class, spanish_keywords, spanish_builtins):
        return translator_class(
            keyword_map=spanish_keywords, builtin_map=spanish_builtins
        )

    @pytest.fixture
    def es_to_en(
        self,
        translator_class,
        english_keywords_from_spanish,
        english_builtins_from_spanish,
    ):
        return translator_class(
            keyword_map=english_keywords_from_spanish,
            builtin_map=english_builtins_from_spanish,
        )

    @pytest.fixture
    def en_to_zh(self, translator_class, chinese_keywords, chinese_builtins):
        return translator_class(
            keyword_map=chinese_keywords, builtin_map=chinese_builtins
        )

    @pytest.fixture
    def zh_to_en(
        self,
        translator_class,
        english_keywords_from_chinese,
        english_builtins_from_chinese,
    ):
        return translator_class(
            keyword_map=english_keywords_from_chinese,
            builtin_map=english_builtins_from_chinese,
        )

    @pytest.mark.xfail(
        reason="CORE-704: Latin-script reverse collision — "
        "'todo' variable incorrectly mapped to 'all' builtin",
        strict=True,
    )
    def test_todo_variable_collides_with_spanish_all(self, en_to_es, es_to_en):
        """Variable named 'todo' (Spanish for 'all') breaks round-trip."""
        original = 'todo = []\ntodo.append("buy milk")\nprint(todo)'

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None

    @pytest.mark.xfail(
        reason="CORE-704: Latin-script reverse collision — "
        "'tipo' variable incorrectly mapped to 'type' builtin",
        strict=True,
    )
    def test_tipo_variable_collides_with_spanish_type(self, en_to_es, es_to_en):
        """Variable named 'tipo' (Spanish for 'type') breaks round-trip."""
        original = "tipo = 'A'\nprint(tipo)"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None

    @pytest.mark.xfail(
        reason="CORE-704: Latin-script reverse collision — "
        "'objeto' variable incorrectly mapped to 'object' builtin",
        strict=True,
    )
    def test_objeto_variable_collides_with_spanish_object(self, en_to_es, es_to_en):
        """Variable named 'objeto' (Spanish for 'object') breaks round-trip."""
        original = "objeto = {}\nobjeto['key'] = 1"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None

    @pytest.mark.xfail(
        reason="CORE-704: Latin-script reverse collision — "
        "'entrada' variable incorrectly mapped to 'input' builtin",
        strict=True,
    )
    def test_entrada_variable_collides_with_spanish_input(self, en_to_es, es_to_en):
        """Variable named 'entrada' (Spanish for 'input') breaks round-trip."""
        original = "entrada = 42\nprint(entrada)"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None

    def test_chinese_immune_to_collision(self, en_to_zh, zh_to_en):
        """Same variables round-trip perfectly with Chinese (non-Latin immune)."""
        original = 'todo = []\ntodo.append("buy milk")\nprint(todo)'

        chinese = en_to_zh.translate_code(original, "en", "zh")
        back = zh_to_en.translate_code(chinese, "zh", "en")

        assert first_divergence(original, back) is None

    def test_spanish_without_collision_variables(self, en_to_es, es_to_en):
        """Code without collision-prone variable names round-trips perfectly."""
        original = "result = []\nresult.append(42)\nprint(result)"

        spanish = en_to_es.translate_code(original, "en", "es")
        back = es_to_en.translate_code(spanish, "es", "en")

        assert first_divergence(original, back) is None
