"""Tests for language abstraction interface (CORE-415).

Uses real language pack translations via conftest fixtures.
"""

import pytest

from legesher_core import (
    TokenTranslator,
    TreeSitterTranslator,
    create_translator,
    create_translator_from_language_pack,
    get_default_backend,
    get_supported_languages,
)


class TestCreateTranslator:
    """Test create_translator factory function."""

    def test_create_translator_default_token(self, spanish_keywords, spanish_builtins):
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_explicit_token(self, spanish_keywords, spanish_builtins):
        translator = create_translator(
            "python", spanish_keywords, spanish_builtins, use_tree_sitter=False
        )
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_explicit_tree_sitter(
        self, spanish_keywords, spanish_builtins
    ):
        translator = create_translator(
            "python", spanish_keywords, spanish_builtins, use_tree_sitter=True
        )
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_with_programming_language_version(
        self, spanish_keywords, spanish_builtins
    ):
        translator = create_translator(
            "python",
            spanish_keywords,
            spanish_builtins,
            programming_language_version="3.13",
            use_tree_sitter=False,
        )
        assert isinstance(translator, TokenTranslator)
        assert translator.python_version == "3.13"

    def test_create_translator_works_functionally(
        self, spanish_keywords, spanish_builtins
    ):
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        code = "def hello():\n    print('Hi')"
        result = translator.translate_code(code, "en", "es")
        assert spanish_keywords["def"] in result
        assert spanish_builtins["print"] in result


class TestCreateTranslatorEnvironmentVariable:
    """Test environment variable support for create_translator."""

    def test_create_translator_from_env_true(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_false(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "false")
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_from_env_1(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "1")
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_0(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "0")
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_from_env_yes(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "yes")
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_on(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "on")
        translator = create_translator("python", spanish_keywords, spanish_builtins)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_case_insensitive(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        for value in ["True", "TRUE", "tRuE", "YES", "Yes", "ON", "On"]:
            monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", value)
            translator = create_translator("python", spanish_keywords, spanish_builtins)
            assert isinstance(translator, TreeSitterTranslator), (
                f"Failed for value: {value}"
            )

    def test_create_translator_from_env_various_falsy_values(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        falsy_values = ["false", "False", "FALSE", "0", "no", "No", "NO", "off", ""]
        for value in falsy_values:
            monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", value)
            translator = create_translator("python", spanish_keywords, spanish_builtins)
            assert isinstance(translator, TokenTranslator), (
                f"Failed for value: {value!r}"
            )

    def test_create_translator_explicit_overrides_env(
        self, monkeypatch, spanish_keywords, spanish_builtins
    ):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")
        translator = create_translator(
            "python", spanish_keywords, spanish_builtins, use_tree_sitter=False
        )
        assert isinstance(translator, TokenTranslator)

        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "false")
        translator = create_translator(
            "python", spanish_keywords, spanish_builtins, use_tree_sitter=True
        )
        assert isinstance(translator, TreeSitterTranslator)


class TestCreateTranslatorUnsupportedLanguages:
    """Test error handling for unsupported languages."""

    def test_create_translator_typescript_not_implemented(self):
        with pytest.raises(NotImplementedError) as exc_info:
            create_translator("typescript", {}, {})
        assert "TypeScript support coming in Phase 2C" in str(exc_info.value)
        assert "CORE-421" in str(exc_info.value)

    def test_create_translator_unsupported_language(self):
        with pytest.raises(ValueError) as exc_info:
            create_translator("rust", {}, {})
        assert "Unsupported programming language: 'rust'" in str(exc_info.value)

    def test_create_translator_invalid_language_shows_supported(self):
        with pytest.raises(ValueError) as exc_info:
            create_translator("golang", {}, {})
        error_msg = str(exc_info.value)
        assert "python" in error_msg
        assert "Supported languages" in error_msg


class TestGetDefaultBackend:
    """Test get_default_backend function."""

    def test_get_default_backend_no_env(self, monkeypatch):
        monkeypatch.delenv("LEGESHER_USE_TREE_SITTER", raising=False)
        assert get_default_backend() == "token"

    def test_get_default_backend_env_true(self, monkeypatch):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")
        assert get_default_backend() == "tree-sitter"

    def test_get_default_backend_env_false(self, monkeypatch):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "false")
        assert get_default_backend() == "token"

    def test_get_default_backend_env_1(self, monkeypatch):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "1")
        assert get_default_backend() == "tree-sitter"

    def test_get_default_backend_env_0(self, monkeypatch):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "0")
        assert get_default_backend() == "token"

    def test_get_default_backend_env_yes(self, monkeypatch):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "yes")
        assert get_default_backend() == "tree-sitter"

    def test_get_default_backend_env_on(self, monkeypatch):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "on")
        assert get_default_backend() == "tree-sitter"


class TestGetSupportedLanguages:
    """Test get_supported_languages function."""

    def test_get_supported_languages_returns_dict(self):
        languages = get_supported_languages()
        assert isinstance(languages, dict)

    def test_get_supported_languages_includes_python(self):
        languages = get_supported_languages()
        assert "python" in languages
        assert isinstance(languages["python"], list)
        assert "token" in languages["python"]
        assert "tree-sitter" in languages["python"]

    def test_get_supported_languages_includes_typescript_planned(self):
        languages = get_supported_languages()
        assert "typescript" in languages
        assert isinstance(languages["typescript"], list)
        assert len(languages["typescript"]) == 0

    def test_get_supported_languages_structure(self):
        languages = get_supported_languages()
        for lang, backends in languages.items():
            assert isinstance(lang, str)
            assert isinstance(backends, list)


class TestCreateTranslatorFromLanguagePack:
    """Test create_translator_from_language_pack convenience function."""

    def test_create_translator_from_language_pack_default(self):
        translator = create_translator_from_language_pack("python", "es")
        assert hasattr(translator, "translate_code")

    def test_create_translator_from_language_pack_tree_sitter(self):
        translator = create_translator_from_language_pack(
            "python", "es", use_tree_sitter=True
        )
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_language_pack_respects_env(self, monkeypatch):
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")
        translator = create_translator_from_language_pack("python", "es")
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_language_pack_typescript_not_implemented(self):
        with pytest.raises(NotImplementedError) as exc_info:
            create_translator_from_language_pack("typescript", "es")
        assert "TypeScript support coming in Phase 2C" in str(exc_info.value)

    def test_create_translator_from_language_pack_with_version(self):
        translator = create_translator_from_language_pack(
            "python", "es", programming_language_version="3.13"
        )
        assert hasattr(translator, "translate_code")
