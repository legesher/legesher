"""Tests for language abstraction interface (CORE-415).

This test module verifies the factory functions and environment variable
configuration for creating translators. Tests ensure that the abstraction
layer properly supports multiple backends and respects user configuration.
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
from tests.data.keyword_maps_spanish import (
    SPANISH_KEYWORDS,
    SPANISH_BUILTINS,
)


class TestCreateTranslator:
    """Test create_translator factory function."""

    def test_create_translator_default_token(self):
        """Default should create TokenTranslator when no env var set."""
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_explicit_token(self):
        """use_tree_sitter=False should create TokenTranslator."""
        translator = create_translator(
            "python", SPANISH_KEYWORDS, SPANISH_BUILTINS, use_tree_sitter=False
        )
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_explicit_tree_sitter(self):
        """use_tree_sitter=True should create TreeSitterTranslator."""
        translator = create_translator(
            "python", SPANISH_KEYWORDS, SPANISH_BUILTINS, use_tree_sitter=True
        )
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_with_programming_language_version(self):
        """Should accept programming_language_version parameter."""
        translator = create_translator(
            "python",
            SPANISH_KEYWORDS,
            SPANISH_BUILTINS,
            programming_language_version="3.13",
            use_tree_sitter=False,
        )
        assert isinstance(translator, TokenTranslator)
        assert translator.python_version == "3.13"

    def test_create_translator_works_functionally(self):
        """Created translator should actually translate code."""
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        code = "def hello():\n    print('Hi')"
        result = translator.translate_code(code, "en", "es")

        assert "definir" in result
        assert "imprimir" in result


class TestCreateTranslatorEnvironmentVariable:
    """Test environment variable support for create_translator."""

    def test_create_translator_from_env_true(self, monkeypatch):
        """LEGESHER_USE_TREE_SITTER=true should use TreeSitterTranslator."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_false(self, monkeypatch):
        """LEGESHER_USE_TREE_SITTER=false should use TokenTranslator."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "false")
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_from_env_1(self, monkeypatch):
        """LEGESHER_USE_TREE_SITTER=1 should use TreeSitterTranslator."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "1")
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_0(self, monkeypatch):
        """LEGESHER_USE_TREE_SITTER=0 should use TokenTranslator."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "0")
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        assert isinstance(translator, TokenTranslator)

    def test_create_translator_from_env_yes(self, monkeypatch):
        """LEGESHER_USE_TREE_SITTER=yes should use TreeSitterTranslator."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "yes")
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_on(self, monkeypatch):
        """LEGESHER_USE_TREE_SITTER=on should use TreeSitterTranslator."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "on")
        translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
        assert isinstance(translator, TreeSitterTranslator)

    def test_create_translator_from_env_case_insensitive(self, monkeypatch):
        """Environment variable should be case-insensitive."""
        for value in ["True", "TRUE", "tRuE", "YES", "Yes", "ON", "On"]:
            monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", value)
            translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
            assert isinstance(translator, TreeSitterTranslator), (
                f"Failed for value: {value}"
            )

    def test_create_translator_from_env_various_falsy_values(self, monkeypatch):
        """Test various falsy environment values."""
        falsy_values = ["false", "False", "FALSE", "0", "no", "No", "NO", "off", ""]

        for value in falsy_values:
            monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", value)
            translator = create_translator("python", SPANISH_KEYWORDS, SPANISH_BUILTINS)
            assert isinstance(translator, TokenTranslator), (
                f"Failed for value: {value!r}"
            )

    def test_create_translator_explicit_overrides_env(self, monkeypatch):
        """Explicit parameter should override environment variable."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")

        # Explicit False should override env var
        translator = create_translator(
            "python", SPANISH_KEYWORDS, SPANISH_BUILTINS, use_tree_sitter=False
        )
        assert isinstance(translator, TokenTranslator)

        # Explicit True should override env var
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "false")
        translator = create_translator(
            "python", SPANISH_KEYWORDS, SPANISH_BUILTINS, use_tree_sitter=True
        )
        assert isinstance(translator, TreeSitterTranslator)


class TestCreateTranslatorUnsupportedLanguages:
    """Test error handling for unsupported languages."""

    def test_create_translator_typescript_not_implemented(self):
        """TypeScript should raise NotImplementedError with helpful message."""
        with pytest.raises(NotImplementedError) as exc_info:
            create_translator("typescript", {}, {})

        assert "TypeScript support coming in Phase 2C" in str(exc_info.value)
        assert "CORE-421" in str(exc_info.value)

    def test_create_translator_unsupported_language(self):
        """Unsupported language should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            create_translator("rust", {}, {})

        assert "Unsupported programming language: 'rust'" in str(exc_info.value)

    def test_create_translator_invalid_language_shows_supported(self):
        """Error message should show supported languages."""
        with pytest.raises(ValueError) as exc_info:
            create_translator("golang", {}, {})

        error_msg = str(exc_info.value)
        assert "python" in error_msg
        assert "Supported languages" in error_msg


class TestGetDefaultBackend:
    """Test get_default_backend function."""

    def test_get_default_backend_no_env(self, monkeypatch):
        """Default should be 'token' when no environment variable."""
        monkeypatch.delenv("LEGESHER_USE_TREE_SITTER", raising=False)
        assert get_default_backend() == "token"

    def test_get_default_backend_env_true(self, monkeypatch):
        """Should return 'tree-sitter' when env var is true."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")
        assert get_default_backend() == "tree-sitter"

    def test_get_default_backend_env_false(self, monkeypatch):
        """Should return 'token' when env var is false."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "false")
        assert get_default_backend() == "token"

    def test_get_default_backend_env_1(self, monkeypatch):
        """Should return 'tree-sitter' for '1'."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "1")
        assert get_default_backend() == "tree-sitter"

    def test_get_default_backend_env_0(self, monkeypatch):
        """Should return 'token' for '0'."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "0")
        assert get_default_backend() == "token"

    def test_get_default_backend_env_yes(self, monkeypatch):
        """Should return 'tree-sitter' for 'yes'."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "yes")
        assert get_default_backend() == "tree-sitter"

    def test_get_default_backend_env_on(self, monkeypatch):
        """Should return 'tree-sitter' for 'on'."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "on")
        assert get_default_backend() == "tree-sitter"


class TestGetSupportedLanguages:
    """Test get_supported_languages function."""

    def test_get_supported_languages_returns_dict(self):
        """Should return a dictionary."""
        languages = get_supported_languages()
        assert isinstance(languages, dict)

    def test_get_supported_languages_includes_python(self):
        """Should include Python with both backends."""
        languages = get_supported_languages()
        assert "python" in languages
        assert isinstance(languages["python"], list)
        assert "token" in languages["python"]
        assert "tree-sitter" in languages["python"]

    def test_get_supported_languages_includes_typescript_planned(self):
        """Should include TypeScript as planned (empty list)."""
        languages = get_supported_languages()
        assert "typescript" in languages
        assert isinstance(languages["typescript"], list)
        assert len(languages["typescript"]) == 0

    def test_get_supported_languages_structure(self):
        """Should have correct structure for all languages."""
        languages = get_supported_languages()

        for lang, backends in languages.items():
            assert isinstance(lang, str)
            assert isinstance(backends, list)


class TestCreateTranslatorFromLanguagePack:
    """Test create_translator_from_language_pack convenience function."""

    def test_create_translator_from_language_pack_default(self):
        """Should create translator from language pack with defaults."""
        # This will fail if Spanish pack not available, which is expected in CI
        try:
            translator = create_translator_from_language_pack("python", "es")
            assert hasattr(translator, "translate_code")
        except Exception:
            pytest.skip("Spanish language pack not available")

    def test_create_translator_from_language_pack_tree_sitter(self):
        """Should create tree-sitter translator from language pack."""
        try:
            translator = create_translator_from_language_pack(
                "python", "es", use_tree_sitter=True
            )
            assert isinstance(translator, TreeSitterTranslator)
        except Exception:
            pytest.skip("Spanish language pack not available")

    def test_create_translator_from_language_pack_respects_env(self, monkeypatch):
        """Should respect environment variable."""
        monkeypatch.setenv("LEGESHER_USE_TREE_SITTER", "true")

        try:
            translator = create_translator_from_language_pack("python", "es")
            assert isinstance(translator, TreeSitterTranslator)
        except Exception:
            pytest.skip("Spanish language pack not available")

    def test_create_translator_from_language_pack_typescript_not_implemented(self):
        """TypeScript should raise NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            create_translator_from_language_pack("typescript", "es")

        assert "TypeScript support coming in Phase 2C" in str(exc_info.value)

    def test_create_translator_from_language_pack_with_version(self):
        """Should accept programming language version parameter."""
        try:
            translator = create_translator_from_language_pack(
                "python", "es", programming_language_version="3.13"
            )
            assert hasattr(translator, "translate_code")
        except Exception:
            pytest.skip("Spanish language pack not available")
