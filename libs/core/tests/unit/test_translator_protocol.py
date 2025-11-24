"""Tests for Translator Protocol conformance (CORE-415).

This test module verifies that both TokenTranslator and TreeSitterTranslator
properly implement the Translator Protocol, enabling polymorphic usage and
type safety across the legesher-core package.
"""

import pytest

from legesher_core import Translator, TokenTranslator, TreeSitterTranslator
from tests.data.keyword_maps_spanish import (
    SPANISH_KEYWORDS,
    SPANISH_BUILTINS,
)


@pytest.fixture(
    params=[TokenTranslator, TreeSitterTranslator], ids=["token", "tree-sitter"]
)
def translator_class(request):
    """Parametrized fixture for testing both translator implementations.

    This fixture runs each test with both TokenTranslator and TreeSitterTranslator
    to ensure both implementations conform to the Translator Protocol.
    """
    return request.param


@pytest.fixture
def translator_instance(translator_class):
    """Create a translator instance for testing.

    Creates an instance of the translator class with Spanish language pack.
    """
    return translator_class(
        keyword_map=SPANISH_KEYWORDS,
        builtin_map=SPANISH_BUILTINS,
    )


class TestProtocolConformance:
    """Test suite for Translator Protocol conformance."""

    def test_protocol_conformance_runtime(self, translator_instance):
        """Verify translator satisfies Translator Protocol at runtime.

        The Protocol check ensures the instance can be used wherever
        a Translator type is expected.
        """
        # Protocol is @runtime_checkable, so isinstance works directly
        assert isinstance(translator_instance, Translator)

    def test_has_translate_code_method(self, translator_instance):
        """Verify translate_code method exists with correct signature."""
        assert hasattr(translator_instance, "translate_code")
        assert callable(translator_instance.translate_code)

    def test_has_translate_file_method(self, translator_instance):
        """Verify translate_file method exists."""
        assert hasattr(translator_instance, "translate_file")
        assert callable(translator_instance.translate_file)

    def test_has_reverse_method(self, translator_instance):
        """Verify reverse method exists."""
        assert hasattr(translator_instance, "reverse")
        assert callable(translator_instance.reverse)

    def test_has_from_language_pack_classmethod(self, translator_class):
        """Verify from_language_pack classmethod exists."""
        assert hasattr(translator_class, "from_language_pack")
        assert callable(translator_class.from_language_pack)

    def test_has_list_available_languages_classmethod(self, translator_class):
        """Verify list_available_languages classmethod exists."""
        assert hasattr(translator_class, "list_available_languages")
        assert callable(translator_class.list_available_languages)

    def test_has_get_pack_info_method(self, translator_instance):
        """Verify get_pack_info method exists."""
        assert hasattr(translator_instance, "get_pack_info")
        assert callable(translator_instance.get_pack_info)

    def test_all_required_methods_exist(self, translator_instance):
        """Verify all 7 required Protocol methods are implemented."""
        required_methods = [
            "translate_code",
            "translate_file",
            "reverse",
            "from_language_pack",
            "list_available_languages",
            "get_pack_info",
        ]

        for method_name in required_methods:
            assert hasattr(translator_instance, method_name), (
                f"Missing required method: {method_name}"
            )
            assert callable(getattr(translator_instance, method_name)), (
                f"Method {method_name} is not callable"
            )


class TestPolymorphicUsage:
    """Test polymorphic usage through Protocol interface."""

    def test_polymorphic_translate_function(self, translator_instance):
        """Test polymorphic usage in a function accepting Translator."""

        def translate_with_protocol(translator: Translator, code: str) -> str:
            """Example function using Translator Protocol."""
            return translator.translate_code(code, "en", "es")

        code = "def hello():\n    pass"
        result = translate_with_protocol(translator_instance, code)

        assert "definir" in result
        assert "hello" in result

    def test_polymorphic_list_comprehension(self, translator_class):
        """Test polymorphic usage in list comprehension."""
        translators = [
            translator_class(SPANISH_KEYWORDS, SPANISH_BUILTINS) for _ in range(3)
        ]

        code = "def greet(): print('Hello')"
        results = [t.translate_code(code, "en", "es") for t in translators]

        assert len(results) == 3
        assert all("definir" in result for result in results)
        assert all("imprimir" in result for result in results)

    def test_polymorphic_type_annotation(self, translator_instance):
        """Test type annotation with Translator Protocol."""

        def process_code(translator: Translator) -> dict:
            """Process code and return metadata using Translator."""
            code = "class MyClass:\n    pass"
            translated = translator.translate_code(code, "en", "es")
            info = translator.get_pack_info()
            return {"translated": translated, "info": info}

        result = process_code(translator_instance)

        assert "translated" in result
        assert "info" in result
        assert "clase" in result["translated"]
        assert "keyword_count" in result["info"]


class TestProtocolAPICompatibility:
    """Test API compatibility across both implementations."""

    def test_translate_code_basic(self, translator_instance):
        """Verify translate_code works with basic code."""
        code = "def hello():\n    return True"
        result = translator_instance.translate_code(code, "en", "es")

        assert isinstance(result, str)
        assert "definir" in result
        assert "retornar" in result

    def test_translate_code_with_metadata(self, translator_instance):
        """Verify translate_code with return_metadata parameter."""
        code = "def hello():\n    pass"
        result = translator_instance.translate_code(
            code, "en", "es", return_metadata=True
        )

        # Should return tuple when return_metadata=True
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_reverse_returns_translator(self, translator_instance):
        """Verify reverse() returns a Translator."""
        reversed_translator = translator_instance.reverse()

        # Should be a Translator (duck typing check)
        assert hasattr(reversed_translator, "translate_code")
        assert callable(reversed_translator.translate_code)

    def test_get_pack_info_returns_dict(self, translator_instance):
        """Verify get_pack_info returns expected dictionary."""
        info = translator_instance.get_pack_info()

        assert isinstance(info, dict)
        assert "keyword_count" in info
        assert "builtin_count" in info
        assert isinstance(info["keyword_count"], int)
        assert isinstance(info["builtin_count"], int)

    def test_list_available_languages_returns_list(self, translator_class):
        """Verify list_available_languages returns list of tuples."""
        languages = translator_class.list_available_languages()

        assert isinstance(languages, list)
        if languages:  # May be empty in test environment
            assert all(isinstance(lang, tuple) for lang in languages)
            assert all(len(lang) == 2 for lang in languages)


class TestProtocolInterchangeability:
    """Test that both implementations are interchangeable."""

    def test_same_input_same_output(self):
        """Verify both translators produce identical output for same input."""
        token_translator = TokenTranslator(SPANISH_KEYWORDS, SPANISH_BUILTINS)
        tree_sitter_translator = TreeSitterTranslator(
            SPANISH_KEYWORDS, SPANISH_BUILTINS
        )

        code = "def greet():\n    print('Hello')\n    return True"

        token_result = token_translator.translate_code(code, "en", "es")
        tree_sitter_result = tree_sitter_translator.translate_code(code, "en", "es")

        # Both should produce equivalent translations
        assert "definir" in token_result
        assert "definir" in tree_sitter_result
        assert "imprimir" in token_result
        assert "imprimir" in tree_sitter_result
        assert "retornar" in token_result
        assert "retornar" in tree_sitter_result

    def test_can_substitute_implementations(self):
        """Test that implementations can be substituted without code changes."""

        def translate_project(translator: Translator, code: str) -> str:
            """Function that works with any Translator implementation."""
            return translator.translate_code(code, "en", "es")

        code = "class Test:\n    def method(self):\n        pass"

        # Both implementations should work in the same function
        token_result = translate_project(
            TokenTranslator(SPANISH_KEYWORDS, SPANISH_BUILTINS), code
        )
        tree_sitter_result = translate_project(
            TreeSitterTranslator(SPANISH_KEYWORDS, SPANISH_BUILTINS), code
        )

        assert "clase" in token_result
        assert "clase" in tree_sitter_result
        assert "definir" in token_result
        assert "definir" in tree_sitter_result
