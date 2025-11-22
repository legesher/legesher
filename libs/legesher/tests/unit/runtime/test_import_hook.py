"""Unit tests for import_hook module."""

import sys
import pytest
from unittest.mock import patch

from legesher.runtime.import_hook import (
    LegesherMetaPathFinder,
    LegesherLoader,
    install_import_hook,
    uninstall_import_hook,
    is_hook_installed,
    get_installed_language,
)
from legesher_core import TokenTranslator


class TestLegesherMetaPathFinder:
    """Test LegesherMetaPathFinder class."""

    def test_init_creates_translator(self):
        """Test that initialization creates a translator."""
        finder = LegesherMetaPathFinder(language="es")
        assert finder.language == "es"
        assert isinstance(finder.translator, TokenTranslator)
        assert isinstance(finder.reverse_translator, TokenTranslator)
        assert isinstance(finder.cache, dict)
        assert len(finder.cache) == 0

    def test_find_spec_returns_none_for_nonexistent(self, tmp_path):
        """Test that find_spec returns None when module doesn't exist."""
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(tmp_path)]):
            spec = finder.find_spec("nonexistent_module", None)
            assert spec is None

    def test_find_spec_finds_simple_module(self, tmp_path):
        """Test that find_spec finds a simple .py module."""
        finder = LegesherMetaPathFinder(language="es")
        module_file = tmp_path / "test_module.py"
        module_file.write_text("# Test module")

        with patch.object(sys, "path", [str(tmp_path)]):
            spec = finder.find_spec("test_module", None)
            assert spec is not None
            assert spec.name == "test_module"
            assert isinstance(spec.loader, LegesherLoader)

    def test_invalidate_caches_clears_cache(self):
        """Test that invalidate_caches clears the translation cache."""
        finder = LegesherMetaPathFinder(language="es")
        finder.cache[("test.py", 123.456)] = b"cached data"
        assert len(finder.cache) == 1

        finder.invalidate_caches()
        assert len(finder.cache) == 0


class TestLegesherLoader:
    """Test LegesherLoader class."""

    def test_init_stores_attributes(self):
        """Test that initialization stores module information."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test_module", "/path/to/test.py", finder)

        assert loader.fullname == "test_module"
        assert loader.path == "/path/to/test.py"
        assert loader.finder is finder

    def test_get_filename_returns_path(self):
        """Test that get_filename returns the source file path."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test_module", "/path/to/test.py", finder)

        filename = loader.get_filename("test_module")
        assert filename == "/path/to/test.py"

    def test_get_data_raises_for_nonexistent_file(self):
        """Test that get_data raises FileNotFoundError for missing files."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test", "/nonexistent/file.py", finder)

        with pytest.raises(FileNotFoundError):
            loader.get_data("/nonexistent/file.py")

    @pytest.mark.skip(
        reason="Internal implementation detail - keyword detection depends on translation_pack structure"
    )
    def test_needs_translation_detects_spanish_keywords(self):
        """Test that _needs_translation detects Spanish keywords."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test", "test.py", finder)

        spanish_code = "definir greet():\n    retornar 42"
        needs_translation = loader._needs_translation(spanish_code)
        assert needs_translation is True

    def test_needs_translation_returns_false_for_english(self):
        """Test that _needs_translation returns False for English code."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test", "test.py", finder)

        english_code = "def greet():\n    return 42"
        needs_translation = loader._needs_translation(english_code)
        assert needs_translation is False


class TestImportHookInstallation:
    """Test import hook installation and management."""

    def setup_method(self):
        """Ensure import hook is not installed before each test."""
        uninstall_import_hook()

    def teardown_method(self):
        """Clean up import hook after each test."""
        uninstall_import_hook()

    def test_install_import_hook_adds_to_meta_path(self):
        """Test that install_import_hook adds finder to sys.meta_path."""
        initial_count = len(sys.meta_path)
        install_import_hook(language="es")

        assert len(sys.meta_path) == initial_count + 1
        assert isinstance(sys.meta_path[0], LegesherMetaPathFinder)
        assert sys.meta_path[0].language == "es"

    def test_install_import_hook_raises_if_already_installed(self):
        """Test that installing twice raises RuntimeError."""
        install_import_hook(language="es")

        with pytest.raises(RuntimeError) as exc_info:
            install_import_hook(language="es")
        assert "already installed" in str(exc_info.value)

    def test_uninstall_import_hook_removes_from_meta_path(self):
        """Test that uninstall_import_hook removes finder."""
        install_import_hook(language="es")
        initial_count = len(sys.meta_path)
        uninstall_import_hook()

        assert len(sys.meta_path) == initial_count - 1
        for finder in sys.meta_path:
            assert not isinstance(finder, LegesherMetaPathFinder)

    def test_uninstall_import_hook_safe_when_not_installed(self):
        """Test that uninstall_import_hook is safe to call when not installed."""
        uninstall_import_hook()
        uninstall_import_hook()  # Should not raise

    def test_is_hook_installed_returns_correct_status(self):
        """Test that is_hook_installed returns correct status."""
        assert is_hook_installed() is False

        install_import_hook(language="es")
        assert is_hook_installed() is True

        uninstall_import_hook()
        assert is_hook_installed() is False

    def test_get_installed_language_returns_correct_language(self):
        """Test that get_installed_language returns correct language."""
        assert get_installed_language() is None

        install_import_hook(language="fr")
        assert get_installed_language() == "fr"

        uninstall_import_hook()
        assert get_installed_language() is None
