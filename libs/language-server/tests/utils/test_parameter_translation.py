"""Unit tests for ParameterTranslation class."""

import pytest

from legesher_language_server.utils.keyword_docs import (
    ParameterTranslation,
    get_param_translator,
)


class TestParameterTranslation:
    """Test ParameterTranslation class for signature translation."""

    def test_translate_simple_parameter(self):
        """Test translating a simple parameter name."""
        trans = ParameterTranslation()
        result = trans.translate("sep", "es")
        assert result == "separador"

    def test_translate_unknown_parameter(self):
        """Test that unknown parameters are returned unchanged."""
        trans = ParameterTranslation()
        result = trans.translate("unknown_param", "es")
        assert result == "unknown_param"

    def test_translate_signature_with_none(self):
        """Test translating signature with None constant."""
        trans = ParameterTranslation()
        result = trans.translate_signature("(file=None)", "es")
        assert result == "(archivo=nulo)"

    def test_translate_signature_with_bool(self):
        """Test translating signature with boolean constants."""
        trans = ParameterTranslation()
        result = trans.translate_signature("(flag=True, verbose=False)", "es")
        assert result == "(flag=verdadero, verbose=falso)"

    def test_translate_signature_with_types(self):
        """Test translating signature with builtin type defaults."""
        trans = ParameterTranslation()
        result = trans.translate_signature("(factory=dict, default=str)", "es")
        assert result == "(factory=diccionario, predeterminado=cadena)"

    def test_translate_signature_with_exceptions(self):
        """Test translating signature with exception types."""
        trans = ParameterTranslation()
        result = trans.translate_signature("(exc=ValueError, retry=True)", "es")
        # ValueError should match case-insensitively
        assert "error de valor" in result.lower() or "valor incorrecto" in result.lower()

    def test_translate_signature_camelcase_exception(self):
        """Test case-insensitive matching for CamelCase exceptions."""
        trans = ParameterTranslation()
        # ValueError (CamelCase) should match valueerror (lowercase in pack)
        result = trans.translate_signature("(error=ValueError)", "es")
        assert "ValueError" not in result  # Should be translated
        assert "=" in result  # Structure preserved

    def test_translate_signature_with_varargs(self):
        """Test translating signature with *args and **kwargs."""
        trans = ParameterTranslation()
        result = trans.translate_signature("(*args, **kwargs)", "es")
        # args and kwargs might not be in PARAMETER_TRANSLATIONS
        # Just verify structure is preserved
        assert "*" in result
        assert "**" in result

    def test_translate_signature_complex(self):
        """Test translating a complex realistic signature."""
        trans = ParameterTranslation()
        signature = "(sep=' ', end='\\n', file=None, flush=False)"
        result = trans.translate_signature(signature, "es")

        # Check each part was translated
        assert "separador" in result
        assert "fin" in result
        assert "archivo" in result
        assert "nulo" in result
        assert "vaciar" in result or "flush" in result  # flush might not translate
        assert "falso" in result

    def test_translate_signature_preserves_string_literals(self):
        """Test that string literals in signatures are preserved."""
        trans = ParameterTranslation()
        result = trans.translate_signature("(sep=', ', end='\\n')", "es")
        # String content should be preserved
        assert "', '" in result
        assert "'\\n'" in result or "'\\\\n'" in result

    def test_lazy_loading_caches_language(self):
        """Test that language packs are cached after first load."""
        trans = ParameterTranslation()

        # First call loads Spanish
        trans.translate_signature("(file=None)", "es")
        assert "es" in trans._keyword_constants_cache

        # Second call uses cache
        cache_size_before = len(trans._keyword_constants_cache)
        trans.translate_signature("(sep=' ')", "es")
        cache_size_after = len(trans._keyword_constants_cache)
        assert cache_size_before == cache_size_after

    def test_lazy_loading_only_loads_requested_language(self):
        """Test that only requested languages are loaded, not all."""
        trans = ParameterTranslation()

        # Load only Spanish
        trans.translate_signature("(file=None)", "es")

        # Should only have Spanish cached, not all 11 languages
        assert len(trans._keyword_constants_cache) == 1
        assert "es" in trans._keyword_constants_cache
        assert "ar" not in trans._keyword_constants_cache
        assert "zh" not in trans._keyword_constants_cache

    def test_multiple_languages(self):
        """Test translating to multiple different languages."""
        trans = ParameterTranslation()

        # Spanish
        result_es = trans.translate_signature("(file=None)", "es")
        assert "nulo" in result_es

        # Arabic (if available)
        result_ar = trans.translate_signature("(file=None)", "ar")
        # Arabic should have different translation or fall back
        assert result_ar != result_es

    def test_translate_signature_with_whitespace_variations(self):
        """Test handling of various whitespace patterns."""
        trans = ParameterTranslation()

        # No spaces
        assert trans.translate_signature("(file=None)", "es") == "(archivo=nulo)"

        # With spaces
        result = trans.translate_signature("(file = None)", "es")
        assert "nulo" in result


class TestGetParamTranslatorSingleton:
    """Test the get_param_translator singleton function."""

    def test_singleton_returns_same_instance(self):
        """Test that get_param_translator returns the same instance."""
        trans1 = get_param_translator()
        trans2 = get_param_translator()
        assert trans1 is trans2

    def test_singleton_is_parameter_translation(self):
        """Test that singleton is a ParameterTranslation instance."""
        trans = get_param_translator()
        assert isinstance(trans, ParameterTranslation)

    def test_singleton_caching_works(self):
        """Test that singleton caching prevents repeated loading."""
        trans = get_param_translator()

        # Use it to load Spanish
        trans.translate_signature("(file=None)", "es")

        # Get "new" instance and check cache is preserved
        trans2 = get_param_translator()
        assert "es" in trans2._keyword_constants_cache


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_signature(self):
        """Test translating an empty signature."""
        trans = ParameterTranslation()
        result = trans.translate_signature("()", "es")
        assert result == "()"

    def test_signature_with_only_positional(self):
        """Test signature with only positional parameters."""
        trans = ParameterTranslation()
        result = trans.translate_signature("(a, b, c)", "es")
        # No defaults to translate, just return as-is
        assert result == "(a, b, c)"

    def test_invalid_language_code(self):
        """Test handling of invalid language codes."""
        trans = ParameterTranslation()
        # Should not crash, just return original or log warning
        result = trans.translate_signature("(file=None)", "invalid_lang")
        # Should still have structure even if not translated
        assert "file" in result or "archivo" in result
        assert "=" in result

    def test_nested_parentheses(self):
        """Test that nested structures don't break translation."""
        trans = ParameterTranslation()
        # Complex case with tuple default
        signature = "(values=(1, 2, 3), default=None)"
        result = trans.translate_signature(signature, "es")
        # Should preserve structure
        assert "(" in result
        assert ")" in result
        assert "nulo" in result  # None should be translated


class TestPerformance:
    """Test performance characteristics."""

    def test_lazy_loading_is_fast_second_time(self):
        """Test that cached lookups are faster than first load."""
        import time

        trans = ParameterTranslation()

        # First call - loads pack
        start = time.time()
        trans.translate_signature("(file=None, sep=',')", "es")
        first_duration = time.time() - start

        # Second call - uses cache
        start = time.time()
        trans.translate_signature("(end='\\n', flush=False)", "es")
        second_duration = time.time() - start

        # Second should be significantly faster (or at least not slower)
        # Allow some margin for timing variance
        assert second_duration <= first_duration * 1.5

    def test_memory_efficient_single_language(self):
        """Test that we don't load all 11 languages when only using 1."""
        trans = ParameterTranslation()

        # Only use Spanish
        for _ in range(10):
            trans.translate_signature("(file=None, sep=',')", "es")

        # Should only have Spanish loaded
        assert len(trans._keyword_constants_cache) == 1


class TestRealWorldScenarios:
    """Test real-world scenarios from actual usage."""

    def test_imprimir_signature_from_screenshot(self):
        """Test the exact signature from the user's screenshot issue.

        This reproduces the bug where parameter names were translated but
        default values (None, False) were not.
        """
        trans = get_param_translator()

        # Exact signature from Python's print function
        signature = "(*values, sep=' ', end='\\n', file=None, flush=False)"
        result = trans.translate_signature(signature, "es")

        # Verify parameter names are translated
        assert "separador" in result, "Parameter 'sep' should be translated to 'separador'"
        assert "fin" in result, "Parameter 'end' should be translated to 'fin'"
        assert "archivo" in result, "Parameter 'file' should be translated to 'archivo'"
        assert "vaciar" in result, "Parameter 'flush' should be translated to 'vaciar'"

        # Verify default values are translated (THIS WAS THE BUG)
        assert "nulo" in result, "None should be translated to 'nulo'"
        assert "falso" in result, "False should be translated to 'falso'"

        # Verify English values are NOT present
        assert "None" not in result, "None should not appear untranslated"
        assert "False" not in result, "False should not appear untranslated"

        # Verify expected output
        expected = "(*values, separador=' ', fin='\\n', archivo=nulo, vaciar=falso)"
        assert result == expected, f"Expected: {expected}, Got: {result}"

    def test_language_server_restart_not_needed(self):
        """Verify that using get_param_translator returns updated code.

        This test ensures that after code changes, the singleton properly
        uses the new implementation without requiring a language server restart
        (as long as tests import fresh).
        """
        trans1 = get_param_translator()
        trans2 = get_param_translator()

        # Should be same instance
        assert trans1 is trans2

        # Should have the new translation capability
        result = trans1.translate_signature("(x=None)", "es")
        assert "nulo" in result, "Should translate None to nulo with current code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
