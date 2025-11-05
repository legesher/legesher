"""Tests for error message templates (CORE-359).

This module tests:
- Template loading and structure
- Translation lookup (English, Spanish, Arabic)
- Variable substitution in templates
- Error message pattern matching
- Fallback behavior for missing translations
"""

import pytest

from legesher_language_server.utils.error_templates import ErrorMessageTemplates


class TestErrorMessageTemplatesInit:
    """Test initialization and template loading."""

    def test_init(self):
        """Test basic initialization."""
        templates = ErrorMessageTemplates()
        assert templates is not None
        assert templates._templates is not None

    def test_templates_loaded(self):
        """Test that templates are loaded on init."""
        templates = ErrorMessageTemplates()
        assert len(templates._templates) > 0

    def test_has_common_error_types(self):
        """Test that common error types are loaded."""
        templates = ErrorMessageTemplates()
        error_types = templates.get_error_types()

        assert "SyntaxError" in error_types
        assert "NameError" in error_types
        assert "TypeError" in error_types
        assert "IndentationError" in error_types
        assert "AttributeError" in error_types
        assert "ImportError" in error_types
        assert "ValueError" in error_types
        assert "KeyError" in error_types
        assert "IndexError" in error_types
        assert "ZeroDivisionError" in error_types

    def test_supported_languages(self):
        """Test supported languages are correct."""
        templates = ErrorMessageTemplates()
        languages = templates.get_supported_languages()

        assert "en" in languages
        assert "es" in languages
        assert "ar" in languages
        assert len(languages) == 3


class TestGetTranslation:
    """Test getting translated error messages."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_get_translation_english(self, templates):
        """Test getting English translation."""
        result = templates.get_translation(
            "SyntaxError",
            "invalid_syntax",
            "en",
        )
        assert result == "invalid syntax"

    def test_get_translation_spanish(self, templates):
        """Test getting Spanish translation."""
        result = templates.get_translation(
            "SyntaxError",
            "invalid_syntax",
            "es",
        )
        assert result == "sintaxis inválida"

    def test_get_translation_arabic(self, templates):
        """Test getting Arabic translation."""
        result = templates.get_translation(
            "SyntaxError",
            "invalid_syntax",
            "ar",
        )
        assert result == "بناء جملة غير صالح"

    def test_get_translation_with_variable(self, templates):
        """Test translation with variable substitution."""
        result = templates.get_translation(
            "NameError",
            "not_defined",
            "en",
            var="foo",
        )
        assert result == "name 'foo' is not defined"

    def test_get_translation_spanish_with_variable(self, templates):
        """Test Spanish translation with variable."""
        result = templates.get_translation(
            "NameError",
            "not_defined",
            "es",
            var="foo",
        )
        assert result == "el nombre 'foo' no está definido"

    def test_get_translation_arabic_with_variable(self, templates):
        """Test Arabic translation with variable."""
        result = templates.get_translation(
            "NameError",
            "not_defined",
            "ar",
            var="foo",
        )
        assert result == "الاسم 'foo' غير معرف"

    def test_get_translation_multiple_variables(self, templates):
        """Test translation with multiple variables."""
        result = templates.get_translation(
            "TypeError",
            "wrong_arg_count",
            "en",
            expected="2",
            actual="3",
        )
        assert result == "takes 2 positional argument but 3 were given"

    def test_get_translation_missing_error_type(self, templates):
        """Test translation with non-existent error type."""
        result = templates.get_translation(
            "NonExistentError",
            "some_key",
            "en",
        )
        assert result is None

    def test_get_translation_missing_template_key(self, templates):
        """Test translation with non-existent template key."""
        result = templates.get_translation(
            "SyntaxError",
            "nonexistent_key",
            "en",
        )
        assert result is None

    def test_get_translation_fallback_to_english(self, templates):
        """Test fallback to English when target language not found."""
        # Add templates but with missing Spanish translation
        # Since all our templates have all languages, we'll test with unsupported language
        result = templates.get_translation(
            "SyntaxError",
            "invalid_syntax",
            "fr",  # Unsupported language
        )
        # Should fallback to English
        assert result == "invalid syntax"

    def test_get_translation_missing_variables(self, templates):
        """Test translation with missing required variables."""
        # Template expects 'var' but we don't provide it
        result = templates.get_translation(
            "NameError",
            "not_defined",
            "en",
            # Missing var parameter
        )
        # Should return template without substitution
        assert result == "name '{var}' is not defined"


class TestAttributeErrorTranslations:
    """Test AttributeError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_attribute_error_english(self, templates):
        """Test AttributeError in English."""
        result = templates.get_translation(
            "AttributeError",
            "no_attribute",
            "en",
            obj="int",
            attr="append",
        )
        assert result == "'int' object has no attribute 'append'"

    def test_attribute_error_spanish(self, templates):
        """Test AttributeError in Spanish."""
        result = templates.get_translation(
            "AttributeError",
            "no_attribute",
            "es",
            obj="int",
            attr="append",
        )
        assert result == "el objeto 'int' no tiene el atributo 'append'"

    def test_attribute_error_arabic(self, templates):
        """Test AttributeError in Arabic."""
        result = templates.get_translation(
            "AttributeError",
            "no_attribute",
            "ar",
            obj="int",
            attr="append",
        )
        assert result == "الكائن 'int' ليس له سمة 'append'"


class TestTypeErrorTranslations:
    """Test TypeError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_not_callable_english(self, templates):
        """Test not callable error in English."""
        result = templates.get_translation(
            "TypeError",
            "not_callable",
            "en",
            var="int",
        )
        assert result == "'int' object is not callable"

    def test_not_callable_spanish(self, templates):
        """Test not callable error in Spanish."""
        result = templates.get_translation(
            "TypeError",
            "not_callable",
            "es",
            var="int",
        )
        assert result == "el objeto 'int' no es invocable"

    def test_unsupported_operand(self, templates):
        """Test unsupported operand error."""
        result = templates.get_translation(
            "TypeError",
            "unsupported_operand",
            "en",
            op="+",
            type1="int",
            type2="str",
        )
        assert result == "unsupported operand type(s) for +: 'int' and 'str'"

    def test_unsupported_operand_spanish(self, templates):
        """Test unsupported operand error in Spanish."""
        result = templates.get_translation(
            "TypeError",
            "unsupported_operand",
            "es",
            op="+",
            type1="int",
            type2="str",
        )
        assert result == "tipo(s) de operando no soportado(s) para +: 'int' y 'str'"


class TestIndentationErrorTranslations:
    """Test IndentationError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_unexpected_indent_english(self, templates):
        """Test unexpected indent in English."""
        result = templates.get_translation(
            "IndentationError",
            "unexpected_indent",
            "en",
        )
        assert result == "unexpected indent"

    def test_unexpected_indent_spanish(self, templates):
        """Test unexpected indent in Spanish."""
        result = templates.get_translation(
            "IndentationError",
            "unexpected_indent",
            "es",
        )
        assert result == "indentación inesperada"

    def test_expected_indent_arabic(self, templates):
        """Test expected indent in Arabic."""
        result = templates.get_translation(
            "IndentationError",
            "expected_indent",
            "ar",
        )
        assert result == "متوقع كتلة ذات مسافة بادئة"


class TestImportErrorTranslations:
    """Test ImportError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_no_module_english(self, templates):
        """Test no module error in English."""
        result = templates.get_translation(
            "ImportError",
            "no_module",
            "en",
            module="nonexistent",
        )
        assert result == "No module named 'nonexistent'"

    def test_no_module_spanish(self, templates):
        """Test no module error in Spanish."""
        result = templates.get_translation(
            "ImportError",
            "no_module",
            "es",
            module="nonexistent",
        )
        assert result == "No hay módulo llamado 'nonexistent'"

    def test_cannot_import_name(self, templates):
        """Test cannot import name error."""
        result = templates.get_translation(
            "ImportError",
            "cannot_import_name",
            "en",
            name="foo",
            module="bar",
        )
        assert result == "cannot import name 'foo' from 'bar'"


class TestValueErrorTranslations:
    """Test ValueError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_invalid_literal(self, templates):
        """Test invalid literal error."""
        result = templates.get_translation(
            "ValueError",
            "invalid_literal",
            "en",
            type="int",
            base="10",
            value="abc",
        )
        assert result == "invalid literal for int() with base 10: 'abc'"

    def test_not_enough_values(self, templates):
        """Test not enough values to unpack."""
        result = templates.get_translation(
            "ValueError",
            "not_enough_values",
            "en",
            expected="3",
            actual="2",
        )
        assert result == "not enough values to unpack (expected 3, got 2)"

    def test_not_enough_values_spanish(self, templates):
        """Test not enough values to unpack in Spanish."""
        result = templates.get_translation(
            "ValueError",
            "not_enough_values",
            "es",
            expected="3",
            actual="2",
        )
        assert (
            result
            == "no hay suficientes valores para desempaquetar (se esperaban 3, se obtuvieron 2)"
        )


class TestIndexErrorTranslations:
    """Test IndexError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_list_index_english(self, templates):
        """Test list index out of range in English."""
        result = templates.get_translation(
            "IndexError",
            "list_index",
            "en",
        )
        assert result == "list index out of range"

    def test_list_index_spanish(self, templates):
        """Test list index out of range in Spanish."""
        result = templates.get_translation(
            "IndexError",
            "list_index",
            "es",
        )
        assert result == "índice de lista fuera de rango"

    def test_tuple_index_arabic(self, templates):
        """Test tuple index out of range in Arabic."""
        result = templates.get_translation(
            "IndexError",
            "tuple_index",
            "ar",
        )
        assert result == "فهرس المجموعة خارج النطاق"


class TestMatchErrorMessage:
    """Test error message pattern matching."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_match_name_error(self, templates):
        """Test matching NameError message."""
        template_key, variables = templates.match_error_message(
            "NameError",
            "name 'foo' is not defined",
        )
        assert template_key == "not_defined"
        assert variables == {"var": "foo"}

    def test_match_attribute_error(self, templates):
        """Test matching AttributeError message."""
        template_key, variables = templates.match_error_message(
            "AttributeError",
            "'int' object has no attribute 'append'",
        )
        assert template_key == "no_attribute"
        assert variables == {"obj": "int", "attr": "append"}

    def test_match_import_error(self, templates):
        """Test matching ImportError message."""
        template_key, variables = templates.match_error_message(
            "ImportError",
            "No module named 'nonexistent'",
        )
        assert template_key == "no_module"
        assert variables == {"module": "nonexistent"}

    def test_match_simple_error(self, templates):
        """Test matching simple error without variables."""
        template_key, variables = templates.match_error_message(
            "SyntaxError",
            "invalid syntax",
        )
        assert template_key == "invalid_syntax"
        assert variables == {}

    def test_match_no_match(self, templates):
        """Test no match for unknown message."""
        template_key, variables = templates.match_error_message(
            "NameError",
            "some completely different error",
        )
        assert template_key is None
        assert variables == {}

    def test_match_invalid_error_type(self, templates):
        """Test matching with invalid error type."""
        template_key, variables = templates.match_error_message(
            "NonExistentError",
            "some error message",
        )
        assert template_key is None
        assert variables == {}


class TestHelperMethods:
    """Test helper methods."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_has_error_type(self, templates):
        """Test checking if error type exists."""
        assert templates.has_error_type("SyntaxError") is True
        assert templates.has_error_type("NameError") is True
        assert templates.has_error_type("NonExistentError") is False

    def test_get_error_types(self, templates):
        """Test getting all error types."""
        error_types = templates.get_error_types()
        assert isinstance(error_types, list)
        assert len(error_types) > 10
        assert "SyntaxError" in error_types
        assert "NameError" in error_types

    def test_get_supported_languages(self, templates):
        """Test getting supported languages."""
        languages = templates.get_supported_languages()
        assert languages == ["en", "es", "ar"]


class TestComprehensiveCoverage:
    """Test comprehensive coverage of all error types."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    @pytest.mark.parametrize(
        "error_type,template_key,lang",
        [
            ("SyntaxError", "invalid_syntax", "en"),
            ("SyntaxError", "expected_colon", "es"),
            ("SyntaxError", "eol_while_scanning", "ar"),
            ("IndentationError", "unexpected_indent", "en"),
            ("IndentationError", "expected_indent", "es"),
            ("NameError", "not_defined", "ar"),
            ("TypeError", "not_callable", "en"),
            ("TypeError", "unsupported_operand", "es"),
            ("AttributeError", "no_attribute", "ar"),
            ("ImportError", "no_module", "en"),
            ("ValueError", "invalid_literal", "es"),
            ("KeyError", "missing_key", "ar"),
            ("IndexError", "list_index", "en"),
            ("ZeroDivisionError", "division_by_zero", "es"),
            ("FileNotFoundError", "no_file", "ar"),
            ("RecursionError", "max_depth", "en"),
            ("RuntimeError", "generator_already_executing", "es"),
        ],
    )
    def test_all_error_templates_exist(self, templates, error_type, template_key, lang):
        """Test that all error templates can be retrieved."""
        result = templates.get_translation(error_type, template_key, lang)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_error_types_have_english(self, templates):
        """Test that all templates have English translation."""
        for error_type in templates.get_error_types():
            error_templates = templates._templates[error_type]
            for template_key in error_templates:
                en_translation = error_templates[template_key].get("en")
                assert en_translation is not None, f"{error_type}.{template_key} missing English"

    def test_all_error_types_have_spanish(self, templates):
        """Test that all templates have Spanish translation."""
        for error_type in templates.get_error_types():
            error_templates = templates._templates[error_type]
            for template_key in error_templates:
                es_translation = error_templates[template_key].get("es")
                assert es_translation is not None, f"{error_type}.{template_key} missing Spanish"

    def test_all_error_types_have_arabic(self, templates):
        """Test that all templates have Arabic translation."""
        for error_type in templates.get_error_types():
            error_templates = templates._templates[error_type]
            for template_key in error_templates:
                ar_translation = error_templates[template_key].get("ar")
                assert ar_translation is not None, f"{error_type}.{template_key} missing Arabic"


class TestZeroDivisionError:
    """Test ZeroDivisionError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_division_by_zero_english(self, templates):
        """Test division by zero in English."""
        result = templates.get_translation(
            "ZeroDivisionError",
            "division_by_zero",
            "en",
        )
        assert result == "division by zero"

    def test_division_by_zero_spanish(self, templates):
        """Test division by zero in Spanish."""
        result = templates.get_translation(
            "ZeroDivisionError",
            "division_by_zero",
            "es",
        )
        assert result == "división por cero"

    def test_division_by_zero_arabic(self, templates):
        """Test division by zero in Arabic."""
        result = templates.get_translation(
            "ZeroDivisionError",
            "division_by_zero",
            "ar",
        )
        assert result == "القسمة على صفر"


class TestKeyError:
    """Test KeyError translations."""

    @pytest.fixture
    def templates(self):
        """Create templates instance for testing."""
        return ErrorMessageTemplates()

    def test_missing_key(self, templates):
        """Test missing key error."""
        result = templates.get_translation(
            "KeyError",
            "missing_key",
            "en",
            key="foo",
        )
        assert result == "'foo'"

    def test_missing_key_preserves_value(self, templates):
        """Test that key value is preserved across languages."""
        # KeyError just shows the key name, same in all languages
        en = templates.get_translation("KeyError", "missing_key", "en", key="test")
        es = templates.get_translation("KeyError", "missing_key", "es", key="test")
        ar = templates.get_translation("KeyError", "missing_key", "ar", key="test")

        assert en == "'test'"
        assert es == "'test'"
        assert ar == "'test'"
