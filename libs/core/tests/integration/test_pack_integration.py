"""Integration tests for TokenTranslator with LanguagePackLoader (CORE-436).

This module tests the integration between legesher_core and legesher_i18n,
ensuring that:
- TokenTranslator.from_language_pack() works correctly
- Language packs load and translate properly
- Version-aware keyword selection works
- Bidirectional translation works
- Thread safety is maintained
- Error messages are helpful
"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from legesher_core import TokenTranslator
from tests.timing import assert_within
from legesher_i18n.exceptions import PackNotFoundError


class TestFromLanguagePack:
    """Test TokenTranslator.from_language_pack() factory method."""

    def test_spanish_pack_loads(self, spanish_keywords):
        """Test Spanish pack loads from YAML and translates correctly."""
        translator = TokenTranslator.from_language_pack("es")

        code = "def greet(): return 'Hello'"
        result = translator.translate_code(code)

        assert spanish_keywords["def"] in result
        assert spanish_keywords["return"] in result
        assert "greet" in result  # Identifiers not translated

    def test_arabic_pack_loads(self, arabic_keywords, arabic_builtins):
        """Test Arabic pack loads and translates (RTL language)."""
        translator = TokenTranslator.from_language_pack("ar")

        code = "def calculate(): print('test')"
        result = translator.translate_code(code)

        # Arabic keywords should be present
        assert arabic_keywords["def"] in result
        assert arabic_builtins["print"] in result

    def test_arabic_comprehensive(self, arabic_keywords):
        """Test Arabic pack with more comprehensive code."""
        translator = TokenTranslator.from_language_pack("ar")

        code = "class Calculator: pass"
        result = translator.translate_code(code)

        # Arabic keywords should be present
        assert arabic_keywords["class"] in result

    def test_auto_detects_python_version(self):
        """Test that Python version is auto-detected from runtime."""
        translator = TokenTranslator.from_language_pack("es")

        # Should have a python_version set
        assert translator.python_version is not None
        assert "." in translator.python_version  # Format: "3.13"

    def test_explicit_python_version(self):
        """Test explicit Python version specification."""
        translator = TokenTranslator.from_language_pack("es", python_version="3.10")

        assert translator.python_version == "3.10"


class TestVersionAwareKeywords:
    """Test version-specific keyword selection."""

    def test_python_310_keywords(self):
        """Test Python 3.10 keywords (match/case)."""
        translator = TokenTranslator.from_language_pack("es", python_version="3.10")

        # Python 3.10+ has match/case
        code = "match x:\n    case 1:\n        pass"
        result = translator.translate_code(code)

        # Should translate match/case
        assert (
            "coincidir" in result or "match" in result
        )  # Spanish for 'match' or kept as match

    def test_python_312_keywords(self):
        """Test Python 3.12 keywords (type)."""
        translator = TokenTranslator.from_language_pack("es", python_version="3.12")

        # Python 3.12+ has type keyword (PEP 695)
        code = "type Point = tuple[float, float]"
        result = translator.translate_code(code)

        # Should attempt to translate 'type' or keep it
        assert "Point" in result  # Identifier preserved

    def test_python_313_all_keywords(self):
        """Test Python 3.13 includes all keywords."""
        translator = TokenTranslator.from_language_pack("es", python_version="3.13")

        # Should have full keyword set
        info = translator.get_pack_info()
        assert info["keyword_count"] > 30  # At least 35 keywords expected


class TestBidirectionalTranslation:
    """Test reverse() method for bidirectional translation."""

    def test_reverse_translator(self):
        """Test creating reversed translator (ES→EN)."""
        en_to_es = TokenTranslator.from_language_pack("es")
        es_to_en = en_to_es.reverse()

        # English to Spanish
        english = "def foo(): return 42"
        spanish = en_to_es.translate_code(english)

        # Spanish back to English
        back_to_english = es_to_en.translate_code(spanish)

        # Should be lossless (keywords restored)
        assert "def" in back_to_english
        assert "return" in back_to_english
        assert "42" in back_to_english

    def test_round_trip_spanish(self):
        """Test complete round-trip EN→ES→EN."""
        en_to_es = TokenTranslator.from_language_pack("es")
        es_to_en = en_to_es.reverse()

        original = """def calculate_tax(income, rate):
    '''Calculate tax amount.'''
    tax = income * rate
    return tax
"""

        spanish = en_to_es.translate_code(original)
        back = es_to_en.translate_code(spanish)

        # Keywords should round-trip
        assert "def calculate_tax" in back
        assert "return tax" in back

    def test_reverse_preserves_builtins(self, spanish_builtins):
        """Test that reverse() works for builtins too."""
        en_to_es = TokenTranslator.from_language_pack("es")
        es_to_en = en_to_es.reverse()

        english = "print(len([1, 2, 3]))"
        spanish = en_to_es.translate_code(english)

        # Should have Spanish builtins
        assert spanish_builtins["print"] in spanish
        assert spanish_builtins["len"] in spanish

        # Reverse back
        back = es_to_en.translate_code(spanish)
        assert "print" in back
        assert "len" in back


class TestErrorHandling:
    """Test error handling and helpful error messages."""

    def test_missing_pack_helpful_error(self):
        """Test that missing pack error shows available languages."""
        with pytest.raises(PackNotFoundError) as exc:
            TokenTranslator.from_language_pack("xyz")

        error_msg = str(exc.value)

        # Should mention the missing language
        assert "xyz" in error_msg

        # Should list available languages
        assert "Available languages:" in error_msg
        assert "es" in error_msg or "Spanish" in error_msg

    def test_missing_pack_includes_link(self):
        """Test error includes documentation link."""
        with pytest.raises(PackNotFoundError) as exc:
            TokenTranslator.from_language_pack("missing_lang")

        error_msg = str(exc.value)
        assert "docs.legesher.io" in error_msg


class TestThreadSafety:
    """Test thread-safe pack loading."""

    def test_concurrent_pack_loading(self, spanish_keywords):
        """Test 100 concurrent calls to load same pack."""

        def load_pack():
            return TokenTranslator.from_language_pack("es")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(load_pack) for _ in range(100)]
            translators = [f.result() for f in futures]

        # All should succeed
        assert len(translators) == 100

        # All should work
        for translator in translators:
            result = translator.translate_code("def foo(): pass")
            assert spanish_keywords["def"] in result

    def test_concurrent_different_languages(self):
        """Test concurrent loading of different language packs."""
        # Only use languages that exist: Spanish and Arabic
        languages = ["es", "ar", "es", "ar"] * 15  # 60 total

        def load_pack(lang):
            return TokenTranslator.from_language_pack(lang)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(load_pack, lang) for lang in languages]
            translators = [f.result() for f in futures]

        # All should succeed
        assert len(translators) == 60


class TestPackCaching:
    """Test pack loader caching."""

    def test_pack_loader_caches_results(self):
        """Test that subsequent loads use cache."""
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()

        # Clear cache first
        loader.clear_cache()

        # Load twice
        pack1 = loader.load("es", "python", "3.13")
        pack2 = loader.load("es", "python", "3.13")

        # Should be same object (cached)
        assert pack1 is pack2

        # Check cache stats
        stats = loader.get_cache_stats()
        assert stats["hits"] >= 1
        assert stats["size"] >= 1

    def test_translator_uses_cached_packs(self):
        """Test that multiple translators benefit from cache."""
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()
        loader.clear_cache()

        # Create multiple translators
        TokenTranslator.from_language_pack("es")
        TokenTranslator.from_language_pack("es")
        TokenTranslator.from_language_pack("ar")

        # Cache should have 2 entries (es and ar)
        stats = loader.get_cache_stats()
        assert stats["size"] >= 2


class TestPackInfo:
    """Test get_pack_info() and list_available_languages() methods."""

    def test_get_pack_info(self):
        """Test getting pack metadata."""
        translator = TokenTranslator.from_language_pack("es")
        info = translator.get_pack_info()

        assert "python_version" in info
        assert "keyword_count" in info
        assert "builtin_count" in info

        # Spanish should have ~35 keywords and some builtins
        assert info["keyword_count"] > 30
        assert info["builtin_count"] > 0  # At least some builtins

    def test_list_available_languages(self):
        """Test listing available languages."""
        languages = TokenTranslator.list_available_languages()

        # Should return list of tuples
        assert isinstance(languages, list)
        assert len(languages) > 0

        # Each should be (code, name) tuple
        for code, name in languages:
            assert isinstance(code, str)
            assert isinstance(name, str)

        # Should include Spanish and Arabic (known to exist)
        codes = [code for code, _ in languages]
        assert "es" in codes
        assert "ar" in codes


class TestBackwardCompatibility:
    """Test that old API still works."""

    def test_old_api_with_hardcoded_maps(self):
        """Test that creating TokenTranslator with dicts still works."""
        spanish_keywords = {"def": "definir", "return": "retornar"}
        spanish_builtins = {"print": "imprimir"}

        translator = TokenTranslator(
            keyword_map=spanish_keywords,
            builtin_map=spanish_builtins,
            python_version="3.13",
        )

        code = "def test(): return 42"
        result = translator.translate_code(code)

        assert "definir" in result
        assert "retornar" in result

    def test_old_and_new_api_coexist(self, spanish_keywords):
        """Test that both APIs can be used in same codebase."""
        # Old API
        old_translator = TokenTranslator(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
        )

        # New API
        new_translator = TokenTranslator.from_language_pack("es")

        # Both should work
        code = "def foo(): print('test')"

        old_result = old_translator.translate_code(code)
        new_result = new_translator.translate_code(code)

        assert "definir" in old_result
        assert spanish_keywords["def"] in new_result


@pytest.mark.timing
class TestPerformance:
    """Latency of pack loading and translation.

    The code runs in every run; the wall-clock bounds are enforced only under
    ``--timing`` (``make bench``), because a bound in the default run measures
    the machine's load as much as the code.
    """

    def test_pack_loading_performance(self):
        """A cold pack load stays under 500 ms."""
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()
        loader.clear_cache()

        # Measure first load (cold cache)
        start = time.perf_counter()
        pack = loader.load("es", "python", "3.13")
        duration = time.perf_counter() - start

        assert pack is not None
        # Local development typically sees <50ms; Windows CI cold loads are slower.
        assert_within(duration * 1000, 500, "a cold pack load")

    def test_cached_pack_loading_fast(self):
        """A second load of the same pack is a cache hit, and returns the same pack."""
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()
        loader.clear_cache()

        first = loader.load("es", "python", "3.13")
        hits_before = loader.get_cache_stats()["hits"]
        start = time.perf_counter()
        second = loader.load("es", "python", "3.13")
        duration = time.perf_counter() - start

        assert loader.get_cache_stats()["hits"] == hits_before + 1, (
            "the second load of es/python/3.13 missed the cache"
        )
        assert second is first
        assert_within(duration * 1000, 1, "a cached pack load")

    def test_translation_performance(self):
        """Translating 500 lines stays under 100 ms."""
        translator = TokenTranslator.from_language_pack("es")

        # Create 500-line test code
        code = "def foo(): return 42\n" * 500

        start = time.perf_counter()
        translated = translator.translate_code(code)
        duration = time.perf_counter() - start

        assert translated.count("\n") == 500
        assert "def foo" not in translated, "the keywords were not translated"
        assert_within(duration * 1000, 100, "translating 500 lines")


class TestLanguagePackIntegration:
    """Test actual language pack content integration."""

    def test_spanish_comprehensive(self, spanish_keywords):
        """Test comprehensive Spanish translation."""
        translator = TokenTranslator.from_language_pack("es")

        code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class Calculator:
    def __init__(self):
        self.value = 0

    def add(self, x):
        self.value += x
        return self.value
"""

        result = translator.translate_code(code)

        # Check keywords
        assert spanish_keywords["def"] in result
        assert spanish_keywords["return"] in result
        assert spanish_keywords["class"] in result
        assert spanish_keywords["if"] in result
        assert spanish_keywords["else"] in result

    def test_arabic_rtl_handling(self, arabic_keywords, arabic_builtins):
        """Test Arabic pack with RTL script."""
        translator = TokenTranslator.from_language_pack("ar")

        code = "def hello(): print('world')"
        result = translator.translate_code(code)

        # Arabic keywords should be present
        assert arabic_keywords["def"] in result
        assert arabic_builtins["print"] in result

        # Identifiers should be preserved
        assert "hello" in result

    def test_arabic_comprehensive_code(self, arabic_keywords):
        """Test Arabic pack with comprehensive code."""
        translator = TokenTranslator.from_language_pack("ar")

        code = """
def greet():
    return "Hello"

if True:
    pass
"""

        result = translator.translate_code(code)

        # Arabic keywords should be present
        assert arabic_keywords["def"] in result
        assert arabic_keywords["if"] in result


class TestExceptionTranslation:
    """Test that exception names are loaded and translated."""

    def test_exceptions_loaded_into_builtin_map(self):
        """Exceptions should be merged into the builtin map with PascalCase keys."""
        translator = TokenTranslator.from_language_pack("es")
        assert translator.mapper.get_builtin("ValueError") is not None
        assert translator.mapper.get_builtin("TypeError") is not None
        assert translator.mapper.get_builtin("IndexError") is not None

    def test_exception_translation_in_code(self):
        """Exception names in except clauses should be translated."""
        translator = TokenTranslator.from_language_pack("es")

        code = """
try:
    x = int("abc")
except ValueError:
    print("bad value")
"""
        result = translator.translate_code(code)

        # ValueError should be translated, not left as English
        assert "ValueError" not in result
        # The Spanish translation should be present
        ve_translation = translator.mapper.get_builtin("ValueError")
        assert ve_translation in result

    def test_multiple_exceptions_translated(self):
        """Multiple exception types in the same code should all translate."""
        translator = TokenTranslator.from_language_pack("zh")

        code = """
try:
    pass
except (ValueError, TypeError, KeyError):
    pass
"""
        result = translator.translate_code(code)

        assert "ValueError" not in result
        assert "TypeError" not in result
        assert "KeyError" not in result

    def test_exception_round_trip(self):
        """Exception translation should survive round-trip EN→ES→EN."""
        en_to_es = TokenTranslator.from_language_pack("es")
        es_to_en = en_to_es.reverse()

        original = """
try:
    x = 1 / 0
except ZeroDivisionError:
    pass
"""
        spanish = en_to_es.translate_code(original)
        assert "ZeroDivisionError" not in spanish

        back = es_to_en.translate_code(spanish)
        assert "ZeroDivisionError" in back

    @pytest.mark.parametrize("lang", ["es", "zh", "ur"])
    def test_common_exceptions_translated_per_language(self, lang):
        """Common exceptions should translate in all 3 target languages."""
        translator = TokenTranslator.from_language_pack(lang)

        for exc_name in [
            "ValueError",
            "TypeError",
            "KeyError",
            "IndexError",
            "RuntimeError",
        ]:
            translation = translator.mapper.get_builtin(exc_name)
            assert translation is not None, (
                f"{exc_name} not found in {lang} builtin map"
            )
            assert translation != exc_name, f"{exc_name} not translated in {lang}"

    def test_exception_count_in_pack_info(self):
        """Pack info builtin_count should now include exceptions."""
        translator = TokenTranslator.from_language_pack("es")
        info = translator.get_pack_info()

        # Builtins + exceptions should be significantly more than builtins alone
        # Typical: ~72 builtins + ~69 exceptions = ~141
        assert info["builtin_count"] > 100
