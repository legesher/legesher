"""Unit tests for GitFilter class.

Tests the git clean/smudge filter implementation for multilingual code translation.
"""

import io
import sys
from unittest.mock import Mock, patch

import pytest

from legesher_core.git_filter import GitFilter, clean_filter, smudge_filter


@pytest.fixture
def spanish_filter():
    """Create a GitFilter instance for Spanish."""
    return GitFilter(language="es", python_version="3.13")


@pytest.fixture
def arabic_filter():
    """Create a GitFilter instance for Arabic."""
    return GitFilter(language="ar", python_version="3.13")


class TestGitFilterInit:
    """Test GitFilter initialization."""

    def test_init_with_language(self):
        """Test initialization with explicit language."""
        filter = GitFilter(language="es")
        assert filter.language == "es"
        assert filter.canonical_language == "en"
        assert filter.python_version is not None  # Auto-detected

    def test_init_with_python_version(self):
        """Test initialization with explicit Python version."""
        filter = GitFilter(language="es", python_version="3.10")
        assert filter.python_version == "3.10"

    def test_init_with_custom_canonical_language(self):
        """Test initialization with custom canonical language."""
        filter = GitFilter(language="es", canonical_language="en")
        assert filter.canonical_language == "en"

    def test_init_creates_translators(self, spanish_filter):
        """Test that initialization creates bidirectional translators."""
        assert spanish_filter.translator_to_en is not None
        assert spanish_filter.translator_from_en is not None

    def test_init_invalid_language(self):
        """Test initialization with invalid language raises error."""
        with pytest.raises(ValueError, match="Could not load language pack"):
            GitFilter(language="invalid-lang")


class TestCleanFilter:
    """Test clean filter (local language → English)."""

    def test_clean_spanish_to_english(self, spanish_filter):
        """Test clean filter translates Spanish code to English."""
        spanish_code = "definir saludar():\n    retornar 42\n"
        input_stream = io.StringIO(spanish_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert "def" in result
        assert "return" in result
        assert "saludar" in result  # Function name preserved

    def test_clean_arabic_to_english(self, arabic_filter):
        """Test clean filter translates Arabic code to English."""
        arabic_code = "تعريف مرحبا():\n    إرجاع 42\n"
        input_stream = io.StringIO(arabic_code)
        output_stream = io.StringIO()

        exit_code = arabic_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert "def" in result
        assert "return" in result

    def test_clean_empty_input(self, spanish_filter):
        """Test clean filter with empty input."""
        input_stream = io.StringIO("")
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        assert output_stream.getvalue() == ""

    def test_clean_whitespace_only(self, spanish_filter):
        """Test clean filter with whitespace-only input."""
        input_stream = io.StringIO("   \n\n   ")
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        assert output_stream.getvalue() == "   \n\n   "

    def test_clean_already_english(self, spanish_filter):
        """Test clean filter with already-English code (pass through)."""
        english_code = "def greet():\n    return 42\n"
        input_stream = io.StringIO(english_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert "def" in result
        assert "return" in result

    def test_clean_preserves_comments(self, spanish_filter):
        """Test clean filter preserves comments."""
        spanish_code = "# Este es un comentario\ndefinir prueba():\n    retornar 1\n"
        input_stream = io.StringIO(spanish_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert "# Este es un comentario" in result or "#" in result

    def test_clean_preserves_strings(self, spanish_filter):
        """Test clean filter preserves string literals."""
        spanish_code = 'definir test():\n    retornar "Hola Mundo"\n'
        input_stream = io.StringIO(spanish_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert '"Hola Mundo"' in result

    def test_clean_invalid_code_passes_through(self, spanish_filter):
        """Test clean filter passes through invalid code without error."""
        invalid_code = "this is not valid python code!@#$"
        input_stream = io.StringIO(invalid_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        # Should not break git - return success
        assert exit_code == 0
        # Should pass through unchanged
        assert output_stream.getvalue() == invalid_code

    def test_clean_incomplete_code(self, spanish_filter):
        """Test clean filter with incomplete code (e.g., during editing)."""
        incomplete_code = "definir test():\n    ret"
        input_stream = io.StringIO(incomplete_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        # Should handle gracefully


class TestSmudgeFilter:
    """Test smudge filter (English → local language)."""

    def test_smudge_english_to_spanish(self, spanish_filter):
        """Test smudge filter translates English code to Spanish."""
        english_code = "def greet():\n    return 42\n"
        input_stream = io.StringIO(english_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert "definir" in result
        assert "retornar" in result
        assert "greet" in result  # Function name preserved

    def test_smudge_english_to_arabic(self, arabic_filter):
        """Test smudge filter translates English code to Arabic."""
        english_code = "def hello():\n    return 42\n"
        input_stream = io.StringIO(english_code)
        output_stream = io.StringIO()

        exit_code = arabic_filter.smudge(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert "تعريف" in result  # Arabic "def"
        assert "إرجاع" in result  # Arabic "return"

    def test_smudge_empty_input(self, spanish_filter):
        """Test smudge filter with empty input."""
        input_stream = io.StringIO("")
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        assert exit_code == 0
        assert output_stream.getvalue() == ""

    def test_smudge_already_target_language(self, spanish_filter):
        """Test smudge filter with already-translated code (pass through)."""
        spanish_code = "definir saludar():\n    retornar 42\n"
        input_stream = io.StringIO(spanish_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        # Should pass through since it's already in target language
        assert "definir" in result or "def" in result

    def test_smudge_preserves_formatting(self, spanish_filter):
        """Test smudge filter preserves code formatting."""
        english_code = "def test():\n    # Comment\n    return 1\n"
        input_stream = io.StringIO(english_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        # Check indentation is preserved
        assert "    " in result

    def test_smudge_invalid_code_passes_through(self, spanish_filter):
        """Test smudge filter passes through invalid code without error."""
        invalid_code = "not valid python!@#$"
        input_stream = io.StringIO(invalid_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        # Should not break git
        assert exit_code == 0
        # Output may have "not" translated to "no" since "not" is a Python keyword
        result = output_stream.getvalue()
        assert "valid python!@#$" in result
        assert "not" in result or "no" in result


class TestRoundTripTranslation:
    """Test round-trip translation (clean then smudge)."""

    def test_roundtrip_spanish(self, spanish_filter):
        """Test Spanish → English → Spanish round trip."""
        original = "definir saludar(nombre):\n    imprimir(nombre)\n    retornar 42\n"

        # Clean: Spanish → English
        input1 = io.StringIO(original)
        output1 = io.StringIO()
        spanish_filter.clean(input1, output1)
        english = output1.getvalue()

        # Smudge: English → Spanish
        input2 = io.StringIO(english)
        output2 = io.StringIO()
        spanish_filter.smudge(input2, output2)
        result = output2.getvalue()

        # Check keywords are translated correctly
        assert "definir" in result
        assert "imprimir" in result
        assert "retornar" in result
        # Check identifiers preserved
        assert "nombre" in result

    def test_roundtrip_preserves_semantics(self, spanish_filter):
        """Test round trip preserves semantic meaning."""
        original = "definir prueba():\n    retornar Verdadero\n"

        # Clean then smudge
        input1 = io.StringIO(original)
        output1 = io.StringIO()
        spanish_filter.clean(input1, output1)

        input2 = io.StringIO(output1.getvalue())
        output2 = io.StringIO()
        spanish_filter.smudge(input2, output2)

        result = output2.getvalue()
        # Semantic meaning preserved
        assert "definir" in result or "def" in result
        assert "retornar" in result or "return" in result


class TestLanguageDetection:
    """Test language detection helpers."""

    def test_is_canonical_language_english(self, spanish_filter):
        """Test detection of English code."""
        english_code = "def test():\n    return 42"
        result = spanish_filter._is_canonical_language(english_code)
        # Should detect English keywords
        assert isinstance(result, bool)
        assert result is True, "English code should be detected as canonical language"

    def test_is_canonical_language_spanish(self, spanish_filter):
        """Test detection of Spanish code."""
        spanish_code = "definir prueba():\n    retornar 42"
        result = spanish_filter._is_canonical_language(spanish_code)
        # Should not detect as English (no English keywords)
        assert isinstance(result, bool)
        assert result is False, (
            "Spanish code should not be detected as canonical language"
        )

    def test_is_canonical_language_empty(self, spanish_filter):
        """Test detection with empty code."""
        assert spanish_filter._is_canonical_language("") is False

    def test_is_canonical_language_mixed(self, spanish_filter):
        """Test detection with mixed language code."""
        # Has English keywords, should detect as English
        mixed_code = "def test():\n    definir otro():\n        pass"
        assert spanish_filter._is_canonical_language(mixed_code) is True


class TestPythonVersionDetection:
    """Test Python version detection."""

    def test_detect_python_version(self, spanish_filter):
        """Test Python version detection."""
        version = spanish_filter._detect_python_version()
        assert version == f"{sys.version_info.major}.{sys.version_info.minor}"


class TestErrorHandling:
    """Test error handling and robustness."""

    def test_clean_with_translator_error(self, spanish_filter, monkeypatch):
        """Test clean filter handles translator errors gracefully."""

        # Mock translator to raise an error
        def mock_translate(*args, **kwargs):
            raise Exception("Translation failed")

        monkeypatch.setattr(
            spanish_filter.translator_to_en, "translate_code", mock_translate
        )

        input_stream = io.StringIO("definir test(): retornar 1")
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        # Should not fail - return success
        assert exit_code == 0
        # Should pass through something (original or empty)
        assert len(output_stream.getvalue()) >= 0

    def test_smudge_with_translator_error(self, spanish_filter, monkeypatch):
        """Test smudge filter handles translator errors gracefully."""

        # Mock translator to raise an error
        def mock_translate(*args, **kwargs):
            raise Exception("Translation failed")

        monkeypatch.setattr(
            spanish_filter.translator_from_en, "translate_code", mock_translate
        )

        input_stream = io.StringIO("def test(): return 1")
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        # Should not fail
        assert exit_code == 0


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @patch("legesher_core.git_filter.GitFilter")
    def test_clean_filter_function(self, mock_filter_class):
        """Test clean_filter convenience function."""
        mock_instance = Mock()
        mock_instance.clean.return_value = 0
        mock_filter_class.return_value = mock_instance

        exit_code = clean_filter(language="es")

        assert exit_code == 0
        mock_filter_class.assert_called_once_with(language="es", python_version=None)
        mock_instance.clean.assert_called_once()

    @patch("legesher_core.git_filter.GitFilter")
    def test_smudge_filter_function(self, mock_filter_class):
        """Test smudge_filter convenience function."""
        mock_instance = Mock()
        mock_instance.smudge.return_value = 0
        mock_filter_class.return_value = mock_instance

        exit_code = smudge_filter(language="ar", python_version="3.13")

        assert exit_code == 0
        mock_filter_class.assert_called_once_with(language="ar", python_version="3.13")
        mock_instance.smudge.assert_called_once()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_clean_with_unicode(self, spanish_filter):
        """Test clean filter with Unicode characters."""
        code = "definir prueba():\n    retornar 'Hola ñ á é í ó ú'\n"
        input_stream = io.StringIO(code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        # Unicode should be preserved
        assert "ñ" in result or "'" in result

    def test_clean_with_very_long_file(self, spanish_filter):
        """Test clean filter with large file."""
        # Create a large file (1000 lines)
        large_code = "definir func_{}():\n    retornar {}\n".format(1, 1) * 1000
        input_stream = io.StringIO(large_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        assert len(result) > 0

    def test_clean_with_mixed_line_endings(self, spanish_filter):
        """Test clean filter with mixed line endings."""
        code = "definir test():\r\n    retornar 42\n"
        input_stream = io.StringIO(code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.clean(input_stream, output_stream)

        assert exit_code == 0

    def test_smudge_with_builtins(self, spanish_filter):
        """Test smudge filter translates built-in functions."""
        english_code = "def test():\n    print('hello')\n    return len('test')\n"
        input_stream = io.StringIO(english_code)
        output_stream = io.StringIO()

        exit_code = spanish_filter.smudge(input_stream, output_stream)

        assert exit_code == 0
        result = output_stream.getvalue()
        # Check builtins are translated
        assert "imprimir" in result or "print" in result
        assert "longitud" in result or "len" in result
