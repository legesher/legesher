"""Unit tests for import hook functionality."""

import sys

import pytest

from legesher.runtime.import_hook import (
    LegesherMetaPathFinder,
    install_import_hook,
    uninstall_import_hook,
)


class TestImportHookInstallation:
    """Test import hook installation and uninstallation."""

    @pytest.mark.skip(reason="Requires language pack loading - integration test")
    def test_install_import_hook(self):
        """Test that import hook is installed correctly."""
        # Uninstall any existing hooks first
        uninstall_import_hook()

        # Install hook
        finder = install_import_hook("es")

        # Verify finder is installed
        assert finder in sys.meta_path
        assert sys.meta_path[0] == finder
        assert isinstance(finder, LegesherMetaPathFinder)

        # Cleanup
        uninstall_import_hook()

    @pytest.mark.skip(reason="Requires language pack loading - integration test")
    def test_uninstall_import_hook(self):
        """Test that import hook is uninstalled correctly."""
        # Install hook first
        install_import_hook("es")

        # Uninstall
        uninstall_import_hook()

        # Verify no Legesher finders remain
        assert not any(isinstance(f, LegesherMetaPathFinder) for f in sys.meta_path)

    @pytest.mark.skip(reason="Requires language pack loading - integration test")
    def test_multiple_install_uninstall(self):
        """Test installing and uninstalling multiple times."""
        for _ in range(3):
            install_import_hook("es")
            assert any(isinstance(f, LegesherMetaPathFinder) for f in sys.meta_path)

            uninstall_import_hook()
            assert not any(isinstance(f, LegesherMetaPathFinder) for f in sys.meta_path)


class TestModuleFinding:
    """Test module finding functionality."""

    @pytest.mark.skip(reason="Requires language pack loading - integration test")
    def test_invalid_module_name_rejected(self):
        """Test that invalid module names are rejected (path traversal protection)."""
        finder = LegesherMetaPathFinder("es")

        # Test invalid characters
        assert finder.find_spec("../malicious", None) is None
        assert finder.find_spec("evil..module", None) is None
        assert finder.find_spec("hack/../../etc/passwd", None) is None

    @pytest.mark.skip(reason="Requires language pack loading - integration test")
    def test_valid_module_name_accepted(self):
        """Test that valid module names are processed."""
        finder = LegesherMetaPathFinder("es")

        # Valid names should not be rejected by validation
        # (may still return None if file doesn't exist)
        finder.find_spec("valid_module", None)
        # Result may be None (file doesn't exist), but shouldn't raise

        finder.find_spec("package.submodule", None)
        # Result may be None, but validation should pass


class TestKeywordDetection:
    """Test native language keyword detection."""

    def test_needs_translation_detection(self):
        """Test that native language code is detected."""
        # This test requires a mock translator - skip for MVP
        pytest.skip("Requires mock translator setup")

    def test_english_code_passthrough(self):
        """Test that English code is not translated."""
        # This test requires a mock translator - skip for MVP
        pytest.skip("Requires mock translator setup")
