"""Tests for Translator Protocol conformance (CORE-415).

This test module verifies that both TokenTranslator and TreeSitterTranslator
properly implement the Translator Protocol. Uses real language pack translations.
"""

import pytest

from legesher_core import Translator, TokenTranslator, TreeSitterTranslator


@pytest.fixture
def translator_instance(translator_class, spanish_keywords, spanish_builtins):
    """Create a translator instance for testing."""
    return translator_class(
        keyword_map=spanish_keywords,
        builtin_map=spanish_builtins,
    )


class TestProtocolConformance:
    """Test suite for Translator Protocol conformance."""

    def test_protocol_conformance_runtime(self, translator_instance):
        assert isinstance(translator_instance, Translator)

    def test_has_translate_code_method(self, translator_instance):
        assert hasattr(translator_instance, "translate_code")
        assert callable(translator_instance.translate_code)

    def test_has_translate_file_method(self, translator_instance):
        assert hasattr(translator_instance, "translate_file")
        assert callable(translator_instance.translate_file)

    def test_has_reverse_method(self, translator_instance):
        assert hasattr(translator_instance, "reverse")
        assert callable(translator_instance.reverse)

    def test_has_from_language_pack_classmethod(self, translator_class):
        assert hasattr(translator_class, "from_language_pack")
        assert callable(translator_class.from_language_pack)

    def test_has_list_available_languages_classmethod(self, translator_class):
        assert hasattr(translator_class, "list_available_languages")
        assert callable(translator_class.list_available_languages)

    def test_has_get_pack_info_method(self, translator_instance):
        assert hasattr(translator_instance, "get_pack_info")
        assert callable(translator_instance.get_pack_info)

    def test_all_required_methods_exist(self, translator_instance):
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

    def test_polymorphic_translate_function(
        self, translator_instance, spanish_keywords
    ):
        def translate_with_protocol(translator: Translator, code: str) -> str:
            return translator.translate_code(code, "en", "es")

        code = "def hello():\n    pass"
        result = translate_with_protocol(translator_instance, code)
        assert spanish_keywords["def"] in result
        assert "hello" in result

    def test_polymorphic_list_comprehension(
        self, translator_class, spanish_keywords, spanish_builtins
    ):
        translators = [
            translator_class(spanish_keywords, spanish_builtins) for _ in range(3)
        ]
        code = "def greet(): print('Hello')"
        results = [t.translate_code(code, "en", "es") for t in translators]
        assert len(results) == 3
        assert all(spanish_keywords["def"] in r for r in results)
        assert all(spanish_builtins["print"] in r for r in results)

    def test_polymorphic_type_annotation(self, translator_instance, spanish_keywords):
        def process_code(translator: Translator) -> dict:
            code = "class MyClass:\n    pass"
            translated = translator.translate_code(code, "en", "es")
            info = translator.get_pack_info()
            return {"translated": translated, "info": info}

        result = process_code(translator_instance)
        assert "translated" in result
        assert "info" in result
        assert spanish_keywords["class"] in result["translated"]
        assert "keyword_count" in result["info"]


class TestProtocolAPICompatibility:
    """Test API compatibility across both implementations."""

    def test_translate_code_basic(self, translator_instance, spanish_keywords):
        code = "def hello():\n    return True"
        result = translator_instance.translate_code(code, "en", "es")
        assert isinstance(result, str)
        assert spanish_keywords["def"] in result
        assert spanish_keywords["return"] in result

    def test_translate_code_with_metadata(self, translator_instance):
        code = "def hello():\n    pass"
        result = translator_instance.translate_code(
            code, "en", "es", return_metadata=True
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_reverse_returns_translator(self, translator_instance):
        reversed_translator = translator_instance.reverse()
        assert hasattr(reversed_translator, "translate_code")
        assert callable(reversed_translator.translate_code)

    def test_get_pack_info_returns_dict(self, translator_instance):
        info = translator_instance.get_pack_info()
        assert isinstance(info, dict)
        assert "keyword_count" in info
        assert "builtin_count" in info
        assert isinstance(info["keyword_count"], int)
        assert isinstance(info["builtin_count"], int)

    def test_list_available_languages_returns_list(self, translator_class):
        languages = translator_class.list_available_languages()
        assert isinstance(languages, list)
        if languages:
            assert all(isinstance(lang, tuple) for lang in languages)
            assert all(len(lang) == 2 for lang in languages)


class TestProtocolInterchangeability:
    """Test that both implementations are interchangeable."""

    def test_same_input_same_output(self, spanish_keywords, spanish_builtins):
        token_translator = TokenTranslator(spanish_keywords, spanish_builtins)
        tree_sitter_translator = TreeSitterTranslator(
            spanish_keywords, spanish_builtins
        )

        code = "def greet():\n    print('Hello')\n    return True"

        token_result = token_translator.translate_code(code, "en", "es")
        tree_sitter_result = tree_sitter_translator.translate_code(code, "en", "es")

        assert spanish_keywords["def"] in token_result
        assert spanish_keywords["def"] in tree_sitter_result
        assert spanish_builtins["print"] in token_result
        assert spanish_builtins["print"] in tree_sitter_result
        assert spanish_keywords["return"] in token_result
        assert spanish_keywords["return"] in tree_sitter_result

    def test_can_substitute_implementations(self, spanish_keywords, spanish_builtins):
        def translate_project(translator: Translator, code: str) -> str:
            return translator.translate_code(code, "en", "es")

        code = "class Test:\n    def method(self):\n        pass"

        token_result = translate_project(
            TokenTranslator(spanish_keywords, spanish_builtins), code
        )
        tree_sitter_result = translate_project(
            TreeSitterTranslator(spanish_keywords, spanish_builtins), code
        )

        assert spanish_keywords["class"] in token_result
        assert spanish_keywords["class"] in tree_sitter_result
        assert spanish_keywords["def"] in token_result
        assert spanish_keywords["def"] in tree_sitter_result
