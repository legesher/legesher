"""Tests for diagnostic provider (CORE-359).

This module tests:
- Syntax error detection and translation
- Indentation error detection
- Variable extraction and preservation
- Error message caching
- Translation to multiple languages (Spanish, Arabic)
- Graceful fallback to English
- Position accuracy
- Performance requirements (<500ms)
- Integration with Language Server
"""

import time

import pytest
from lsprotocol.types import (
    DiagnosticSeverity,
)

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.providers.diagnostic import (
    ERROR_TEMPLATES,
    DiagnosticProvider,
    _error_message_cache,
    provide_diagnostics,
)
from legesher_language_server.server import LegesherLanguageServer
from tests.timing import assert_within


class TestDiagnosticProviderInit:
    """Test DiagnosticProvider initialization."""

    @pytest.fixture
    def provider(self):
        """Create diagnostic provider for testing."""
        return DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

    def test_init_with_defaults(self, provider):
        """Test initialization with default values."""
        assert provider.source_lang == "en"
        assert provider.target_lang == "es"
        assert provider.document_text == ""
        assert provider.document_uri == "file:///test.py"

    def test_init_with_arabic(self):
        """Test initialization with Arabic target language."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="ar",
            document_text="test",
            document_uri="file:///test.py",
        )
        assert provider.target_lang == "ar"

    def test_init_with_document_text(self):
        """Test initialization with actual document text."""
        code = "def hello():\n    pass"
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )
        assert provider.document_text == code


class TestDiagnosticProviderSyntaxErrors:
    """Test syntax error detection and translation."""

    @pytest.fixture
    def provider(self):
        """Create diagnostic provider for testing."""
        return DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

    @pytest.mark.asyncio
    async def test_syntax_error_missing_colon(self, provider):
        """Test detection of missing colon in function definition."""
        provider.document_text = "def foo()\n    pass"
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error
        assert diagnostics[0].source == "legesher-lsp"
        # Should contain Spanish word "sintaxis"
        assert "sintaxis" in diagnostics[0].message.lower()

    @pytest.mark.asyncio
    async def test_syntax_error_invalid_syntax(self, provider):
        """Test generic invalid syntax error."""
        provider.document_text = "if True\n    pass"
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error
        assert "sintaxis" in diagnostics[0].message.lower()

    @pytest.mark.asyncio
    async def test_syntax_error_eol_while_scanning(self, provider):
        """Test EOL while scanning string literal."""
        provider.document_text = 'print("unterminated string)'
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error
        assert "sintaxis" in diagnostics[0].message.lower()

    @pytest.mark.asyncio
    async def test_syntax_error_unmatched_parentheses(self, provider):
        """Test unmatched parentheses error."""
        provider.document_text = "print('hello'"
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error

    @pytest.mark.asyncio
    async def test_syntax_error_invalid_character(self, provider):
        """Test invalid character in code."""
        provider.document_text = "x = 10\n@@@"
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error

    @pytest.mark.asyncio
    async def test_syntax_error_eof(self, provider):
        """Test EOF errors."""
        provider.document_text = "def foo():\n    if True:"
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error

    @pytest.mark.asyncio
    async def test_multiple_syntax_errors_reports_first(self, provider):
        """Test that only first syntax error is reported."""
        # Python parser stops at first syntax error
        provider.document_text = "def foo(\ndef bar("
        diagnostics = await provider.get_diagnostics()

        # Only reports first error
        assert len(diagnostics) == 1


class TestDiagnosticProviderIndentationErrors:
    """Test indentation error detection."""

    @pytest.mark.asyncio
    async def test_unexpected_indent(self):
        """Test unexpected indent error."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="    print('hello')",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error
        # IndentationError is caught as SyntaxError in Python 3.13
        # Should contain Spanish word "sintaxis" or "indentación"
        assert any(word in diagnostics[0].message.lower() for word in ["sintaxis", "indentación"])

    @pytest.mark.asyncio
    async def test_unindent_does_not_match(self):
        """Test unindent error."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo():\n    if True:\n        pass\n   pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Should contain Spanish error word
        assert any(word in diagnostics[0].message.lower() for word in ["sintaxis", "indentación"])

    @pytest.mark.asyncio
    async def test_indentation_error_arabic(self):
        """Test indentation error in Arabic."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="ar",
            document_text="    print('hello')",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Should contain Arabic characters for "indentation"
        assert any("\u0600" <= c <= "\u06ff" for c in diagnostics[0].message)


class TestDiagnosticProviderVariableExtraction:
    """Test variable extraction from error messages."""

    @pytest.fixture
    def provider(self):
        """Create diagnostic provider for testing."""
        return DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

    def test_extract_single_quoted_variable(self, provider):
        """Test extraction of single-quoted variable name."""
        variables = provider._extract_variables("name 'foo' is not defined")
        assert "var" in variables
        assert variables["var"] == "foo"

    def test_extract_double_quoted_variable(self, provider):
        """Test extraction of double-quoted variable name."""
        variables = provider._extract_variables('name "bar" is not defined')
        assert "var" in variables
        assert variables["var"] == "bar"

    def test_extract_module_name(self, provider):
        """Test extraction of module name."""
        variables = provider._extract_variables("No module named 'math'")
        assert "module" in variables
        assert variables["module"] == "math"

    def test_extract_multiple_variables(self, provider):
        """Test extraction of multiple variable names."""
        variables = provider._extract_variables("cannot import name 'foo' from 'bar'")
        assert "var" in variables
        assert variables["var"] == "foo"
        assert "module" in variables
        assert variables["module"] == "bar"

    def test_extract_attribute_error(self, provider):
        """Test extraction from attribute error."""
        variables = provider._extract_variables("'str' object has no attribute 'append'")
        assert "var" in variables
        assert variables["var"] == "str"
        assert "attr" in variables
        assert variables["attr"] == "append"

    def test_extract_numbers(self, provider):
        """Test extraction of numbers from error messages."""
        variables = provider._extract_variables("expected 3 arguments, got 2")
        assert "expected" in variables
        assert variables["expected"] == "3"
        assert "actual" in variables
        assert variables["actual"] == "2"

    def test_extract_message_always_present(self, provider):
        """Test that message is always extracted."""
        variables = provider._extract_variables("some error text")
        assert "message" in variables
        assert "some error text" in variables["message"]

    def test_extract_long_message_truncated(self, provider):
        """Test that long messages are truncated."""
        long_message = "x" * 200
        variables = provider._extract_variables(long_message)
        assert len(variables["message"]) <= 100
        assert variables["message"].endswith("...")


class TestDiagnosticProviderVariablePreservation:
    """Test that variable names are never translated."""

    @pytest.mark.asyncio
    async def test_variable_name_preserved_in_spanish(self):
        """Test that variable name 'foo' appears in Spanish error message."""
        # This would generate a NameError if we had runtime checking
        # For now, test with a syntax error that contains identifiers
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def my_function()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # The function name should be preserved if mentioned in error
        # Error message should be in Spanish
        assert "sintaxis" in diagnostics[0].message.lower()

    @pytest.mark.asyncio
    async def test_variable_name_preserved_in_arabic(self):
        """Test that variable names preserved in Arabic."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="ar",
            document_text="def my_function()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Should have Arabic characters for error type
        assert any("\u0600" <= c <= "\u06ff" for c in diagnostics[0].message)

    def test_extracted_variables_not_translated(self):
        """Test that extracted variable names are not modified."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

        # Test variable extraction preserves names exactly
        variables = provider._extract_variables("name 'my_var_123' is not defined")
        assert variables["var"] == "my_var_123"


class TestDiagnosticProviderTranslation:
    """Test translation to different languages."""

    @pytest.mark.asyncio
    async def test_translate_to_spanish(self):
        """Test translation to Spanish."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Spanish translation should be used
        assert any(
            spanish_word in diagnostics[0].message.lower() for spanish_word in ["sintaxis", "error"]
        )

    @pytest.mark.asyncio
    async def test_translate_to_arabic(self):
        """Test translation to Arabic."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="ar",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Arabic characters should be present
        assert any("\u0600" <= c <= "\u06ff" for c in diagnostics[0].message)

    @pytest.mark.asyncio
    async def test_fallback_to_english(self):
        """Test fallback to English for unsupported language."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="fr",  # Not supported in templates
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Should fall back to English template
        assert "invalid syntax" in diagnostics[0].message or "expected" in diagnostics[0].message

    @pytest.mark.asyncio
    async def test_translation_uses_templates(self):
        """Test that translation uses ERROR_TEMPLATES."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )

        # Manually translate to verify template usage
        translated = await provider._translate_error_message("SyntaxError", "invalid syntax")

        # Should match template pattern
        assert "Error de sintaxis" in translated or "sintaxis" in translated.lower()

    def test_all_error_templates_have_english(self):
        """Test that all error templates have English fallback."""
        for error_type, templates in ERROR_TEMPLATES.items():
            assert "en" in templates, f"{error_type} missing English template"

    def test_error_templates_have_spanish_and_arabic(self):
        """Test that error templates have Spanish and Arabic."""
        for error_type, templates in ERROR_TEMPLATES.items():
            assert "es" in templates, f"{error_type} missing Spanish template"
            assert "ar" in templates, f"{error_type} missing Arabic template"


class TestDiagnosticProviderPositionAccuracy:
    """Test that diagnostic positions are accurate."""

    @pytest.mark.asyncio
    async def test_error_position_line_number(self):
        """Test error is reported on correct line."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="print('line 1')\ndef foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Error on line 2 (0-indexed = line 1)
        assert diagnostics[0].range.start.line == 1

    @pytest.mark.asyncio
    async def test_error_position_column(self):
        """Test error column position is reported."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Column should be non-negative
        assert diagnostics[0].range.start.character >= 0

    @pytest.mark.asyncio
    async def test_error_range_valid(self):
        """Test that error range is valid (end >= start)."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        diag = diagnostics[0]
        assert diag.range.end.line >= diag.range.start.line
        if diag.range.end.line == diag.range.start.line:
            assert diag.range.end.character > diag.range.start.character

    @pytest.mark.asyncio
    async def test_error_position_first_line(self):
        """Test error on first line."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="if True",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        assert diagnostics[0].range.start.line == 0

    @pytest.mark.asyncio
    async def test_position_clamping_prevents_negative(self):
        """Test that positions are clamped to valid ranges."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="@@@",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        diag = diagnostics[0]
        # All positions should be non-negative
        assert diag.range.start.line >= 0
        assert diag.range.start.character >= 0
        assert diag.range.end.line >= 0
        assert diag.range.end.character >= 0


class TestDiagnosticProviderCaching:
    """Test caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit_same_error(self):
        """Test that same error hits cache."""
        # Clear cache first
        _error_message_cache.clear()

        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )

        # First call (cache miss)
        diagnostics1 = await provider.get_diagnostics()

        # Second call (cache hit)
        provider2 = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics2 = await provider2.get_diagnostics()

        assert diagnostics1[0].message == diagnostics2[0].message

    @pytest.mark.asyncio
    async def test_cache_stores_translations(self):
        """Test that cache stores translations."""
        _error_message_cache.clear()

        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )

        # Generate diagnostic to populate cache
        await provider.get_diagnostics()

        # Cache should have entries
        assert len(_error_message_cache) > 0

    @pytest.mark.asyncio
    async def test_cache_different_languages(self):
        """Test that cache differentiates languages."""
        _error_message_cache.clear()

        # Spanish
        provider_es = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics_es = await provider_es.get_diagnostics()

        # Arabic
        provider_ar = DiagnosticProvider(
            source_lang="en",
            target_lang="ar",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics_ar = await provider_ar.get_diagnostics()

        # Messages should be different (different languages)
        assert diagnostics_es[0].message != diagnostics_ar[0].message


@pytest.mark.timing
class TestDiagnosticProviderPerformance:
    """Test performance requirements.

    The bounds are enforced only under ``make bench`` (CORE-2321); the
    functional assertions run in every run.
    """

    @pytest.mark.asyncio
    async def test_diagnostic_response_time_small_file(self):
        """Test response time for small file (<100 lines)."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )

        start = time.perf_counter()
        diagnostics = await provider.get_diagnostics()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(diagnostics) == 1
        assert_within(elapsed_ms, 500, "Diagnostics for a small file")

    @pytest.mark.asyncio
    async def test_diagnostic_response_time_large_file(self):
        """Test response time for larger file (~500 lines)."""
        # Create a large document with error at the end
        large_doc = "print('hello')\n" * 500 + "def foo()\n    pass"

        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text=large_doc,
            document_uri="file:///test.py",
        )

        start = time.perf_counter()
        diagnostics = await provider.get_diagnostics()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(diagnostics) == 1
        assert_within(elapsed_ms, 500, "Diagnostics for a 500-line file")

    @pytest.mark.asyncio
    async def test_diagnostic_valid_code_fast(self):
        """Test that valid code is processed quickly."""
        valid_code = """
def calculate_tax(income, rate):
    '''Calculate tax.'''
    return income * rate

class Calculator:
    def __init__(self):
        self.value = 0

    def add(self, x):
        self.value += x
        return self.value

val1 = 10
val2 = 20
result = calculate_tax(val1, val2)
"""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text=valid_code,
            document_uri="file:///test.py",
        )

        start = time.perf_counter()
        diagnostics = await provider.get_diagnostics()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(diagnostics) == 0  # No errors in valid code
        assert_within(elapsed_ms, 500, "Diagnostics for valid code")

    @pytest.mark.asyncio
    async def test_caching_improves_performance(self, monkeypatch):
        """Test that caching improves performance.

        The proof is that the second call never builds a translation
        (CORE-2321): ``_get_translation_template`` runs only on a cache miss.
        The timing comparison is checked only under ``make bench``.
        """
        _error_message_cache.clear()

        built = []
        real_template = DiagnosticProvider._get_translation_template

        def counting_template(self, error_type, variables):
            built.append(error_type)
            return real_template(self, error_type, variables)

        monkeypatch.setattr(DiagnosticProvider, "_get_translation_template", counting_template)

        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )

        # First call (cache miss)
        start1 = time.perf_counter()
        await provider.get_diagnostics()
        duration1 = (time.perf_counter() - start1) * 1000
        built_by_first_call = list(built)

        # Second call (cache hit)
        provider2 = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo()\n    pass",
            document_uri="file:///test.py",
        )
        start2 = time.perf_counter()
        await provider2.get_diagnostics()
        duration2 = (time.perf_counter() - start2) * 1000

        # Both calls are sub-millisecond, so only the build count runs in
        # every run.
        assert len(built_by_first_call) == 1, "the first call did not build its translation"
        assert built == built_by_first_call, "the second call rebuilt a cached translation"
        assert_within(duration2, max(duration1 * 5.0, 1.0), "Diagnostics with a cached translation")


class TestDiagnosticProviderEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_document(self):
        """Test empty document returns no diagnostics."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 0

    @pytest.mark.asyncio
    async def test_whitespace_only_document(self):
        """Test whitespace-only document returns no diagnostics."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="   \n\n   \t\n",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 0

    @pytest.mark.asyncio
    async def test_valid_document(self):
        """Test valid Python document returns no diagnostics."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="def foo():\n    pass\n\nfoo()",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 0

    @pytest.mark.asyncio
    async def test_unicode_content(self):
        """Test handling of Unicode content."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="# Comment with émojis 😀\ndef foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Should handle unicode without crashing

    @pytest.mark.asyncio
    async def test_comment_only_document(self):
        """Test document with only comments."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="# This is a comment\n# Another comment",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 0

    @pytest.mark.asyncio
    async def test_docstring_only_document(self):
        """Test document with only docstring."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text='"""This is a module docstring."""',
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 0

    @pytest.mark.asyncio
    async def test_very_long_line(self):
        """Test handling of very long lines."""
        long_line = "x = " + "1" * 10000
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text=long_line + "\ndef foo()\n    pass",
            document_uri="file:///test.py",
        )
        diagnostics = await provider.get_diagnostics()

        assert len(diagnostics) == 1
        # Should handle long lines without issues


class TestDiagnosticProviderTabError:
    """Test TabError detection (mixing tabs and spaces)."""

    @pytest.mark.asyncio
    async def test_tab_error_detection(self):
        """Test detection of mixed tabs and spaces."""
        # Mix tabs and spaces in indentation
        code = "def foo():\n\tif True:\n        pass"
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )
        # Note: Python 3 is more lenient with tabs, might not always error
        _ = await provider.get_diagnostics()

        # May or may not error depending on Python version
        # Just verify it doesn't crash


class TestDiagnosticProviderContextExtraction:
    """Test error position context extraction."""

    def test_get_error_position_context(self):
        """Test extraction of code context around error."""
        code = """line 1
line 2
line 3
line 4
line 5"""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        # Get context for line 2 (0-indexed)
        context = provider._get_error_position_context(line=2, column=5)

        assert "line 3" in context  # Error line
        assert "line 2" in context  # Previous line
        assert "line 4" in context  # Next line

    def test_get_error_context_with_marker(self):
        """Test that error marker is placed at correct column."""
        code = "def foo():\n    pass"
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
        )

        context = provider._get_error_position_context(line=0, column=8)

        # Should contain marker line
        assert "^" in context

    def test_get_error_context_invalid_line(self):
        """Test context extraction with invalid line number."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="line 1",
            document_uri="file:///test.py",
        )

        context = provider._get_error_position_context(line=100, column=0)

        assert context == ""


class TestDiagnosticProviderGetTranslationTemplate:
    """Test translation template lookup."""

    def test_get_translation_template_spanish(self):
        """Test getting Spanish translation template."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

        template = provider._get_translation_template("SyntaxError", {"message": "test"})

        assert template is not None
        assert "sintaxis" in template.lower()

    def test_get_translation_template_arabic(self):
        """Test getting Arabic translation template."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="ar",
            document_text="",
            document_uri="file:///test.py",
        )

        template = provider._get_translation_template("SyntaxError", {"message": "test"})

        assert template is not None
        # Should contain Arabic characters
        assert any("\u0600" <= c <= "\u06ff" for c in template)

    def test_get_translation_template_unknown_type(self):
        """Test getting template for unknown error type."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

        template = provider._get_translation_template("UnknownError", {"message": "test"})

        assert template is None

    def test_get_translation_template_fallback_to_english(self):
        """Test fallback to English when target language unavailable."""
        provider = DiagnosticProvider(
            source_lang="en",
            target_lang="fr",  # Not in ERROR_TEMPLATES
            document_text="",
            document_uri="file:///test.py",
        )

        template = provider._get_translation_template("SyntaxError", {"message": "test"})

        # Should fallback to English
        assert template is not None


@pytest.mark.asyncio
class TestProvideDiagnosticsFunction:
    """Test the provide_diagnostics async function.

    Note: Skipped due to pygls Python 3.13 compatibility issue.
    These tests will be enabled once pygls supports Python 3.13.
    """

    @pytest.fixture
    def server(self):
        """Create language server for testing."""
        config = LanguageServerConfig(
            source_language="en",
            target_language="es",
            python_version="3.11",
            cache_size=1000,
            cache_ttl=3600,
            log_level="INFO",
        )
        server = LegesherLanguageServer(config)
        return server

    async def test_provide_diagnostics_with_document(self, server):
        """Test provide_diagnostics with real document."""
        uri = "file:///test.py"
        code = "def foo()\n    pass"

        # Open document
        server.document_manager.open_document(uri, code, 1, "python")

        # Get diagnostics
        diagnostics = await provide_diagnostics(server, uri)

        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error
        assert "sintaxis" in diagnostics[0].message.lower()

    async def test_provide_diagnostics_no_document(self, server):
        """Test provide_diagnostics with non-existent document."""
        diagnostics = await provide_diagnostics(server, "file:///nonexistent.py")

        assert diagnostics == []

    async def test_provide_diagnostics_valid_document(self, server):
        """Test provide_diagnostics with valid Python code."""
        uri = "file:///valid.py"
        code = """
def calculate_tax(income, rate):
    '''Calculate tax.'''
    return income * rate

x = 10
result = calculate_tax(x, 0.2)
"""
        server.document_manager.open_document(uri, code, 1, "python")

        diagnostics = await provide_diagnostics(server, uri)

        assert len(diagnostics) == 0

    async def test_provide_diagnostics_integration_flow(self, server):
        """Test complete integration flow."""
        uri = "file:///integration_test.py"
        code = """
import os

def hello():
    print('Hello')

# Syntax error below
def broken(
    pass
"""
        # Open document
        server.document_manager.open_document(uri, code, 1, "python")

        # Get diagnostics
        diagnostics = await provide_diagnostics(server, uri)

        # Should detect syntax error
        assert len(diagnostics) == 1
        assert diagnostics[0].severity == DiagnosticSeverity.Error

        # Message should be in Spanish (server config target_language)
        assert "sintaxis" in diagnostics[0].message.lower()

        # Update document to fix error
        fixed_code = """
import os

def hello():
    print('Hello')

def fixed():
    pass
"""
        server.document_manager.update_document(uri, fixed_code, 2)

        # Get diagnostics again
        diagnostics = await provide_diagnostics(server, uri)

        # Should have no errors now
        assert len(diagnostics) == 0

    async def test_provide_diagnostics_arabic_translation(self):
        """Test diagnostics with Arabic translation."""
        config = LanguageServerConfig(
            source_language="en",
            target_language="ar",
            python_version="3.11",
            cache_size=1000,
            cache_ttl=3600,
            log_level="INFO",
        )
        server = LegesherLanguageServer(config)

        uri = "file:///test_ar.py"
        code = "def foo()\n    pass"

        server.document_manager.open_document(uri, code, 1, "python")
        diagnostics = await provide_diagnostics(server, uri)

        assert len(diagnostics) == 1
        # Should contain Arabic characters
        assert any("\u0600" <= c <= "\u06ff" for c in diagnostics[0].message)
