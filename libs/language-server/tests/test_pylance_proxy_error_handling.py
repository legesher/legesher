"""Unit tests for pylance_proxy.py error handling.

Tests comprehensive error handling for language pack loading in PylanceProxy including:
- Missing directories
- Missing files with version fallback
- Invalid YAML syntax
- Missing keywords section
- Invalid keyword mappings with validation
- Successful loads with count logging

Related to CORE-447
"""

import logging
from unittest.mock import patch

import pytest
import yaml

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.pylance_proxy import PylanceProxy


class TestPylanceProxyErrorHandling:
    """Test error handling in PylanceProxy._get_keyword_map()."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return LanguageServerConfig(
            source_language="en",
            target_language="es",
            pylance_enabled=False,  # Don't start Pyright process in tests
        )

    @pytest.fixture
    def mock_pack_dir(self, tmp_path):
        """Create temporary pack directory structure."""
        pack_dir = tmp_path / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)
        return pack_dir

    def test_directory_not_found(self, config, caplog):
        """Test handling when language pack directory doesn't exist."""
        proxy = PylanceProxy(config)

        with caplog.at_level(logging.WARNING):
            result = proxy._get_keyword_map("nonexistent")

        assert result == {}
        assert "Language pack directory for 'nonexistent' not found" in caplog.text
        assert "translation disabled" in caplog.text

    def test_pack_file_missing_all_versions(self, config, tmp_path, caplog):
        """Test handling when no pack files exist for any Python version."""
        pack_dir = tmp_path / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=pack_dir):
            with caplog.at_level(logging.WARNING):
                result = proxy._get_keyword_map("es")

        assert result == {}
        assert "Language pack file not found for 'es'" in caplog.text
        assert "3.10, 3.11, 3.12, 3.13" in caplog.text

    def test_version_fallback_finds_312(self, config, mock_pack_dir, caplog):
        """Test version fallback finds 3.12 when earlier versions missing."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.12.yml"
        valid_pack = {"keywords": {"def": "definir", "class": "clase", "if": "si"}}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(valid_pack, f)

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.INFO):
                result = proxy._get_keyword_map("es")

        assert result == {"definir": "def", "clase": "class", "si": "if"}
        assert "Loaded 3 keyword translations for es" in caplog.text
        assert "3.12.yml" in caplog.text

    def test_invalid_yaml_syntax(self, config, mock_pack_dir, caplog):
        """Test handling of malformed YAML."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"

        with open(pack_file, "w", encoding="utf-8") as f:
            f.write("keywords:\n  def: definir\n  - invalid list item")

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.ERROR):
                result = proxy._get_keyword_map("es")

        assert result == {}
        assert "Invalid YAML in es language pack" in caplog.text

    def test_missing_keywords_section(self, config, mock_pack_dir, caplog):
        """Test handling when keywords section is missing."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        invalid_pack = {"language": "es", "target": "python"}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(invalid_pack, f)

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.WARNING):
                result = proxy._get_keyword_map("es")

        assert result == {}
        assert "has no keywords section" in caplog.text
        assert "translation disabled" in caplog.text

    def test_invalid_pack_data_type(self, config, mock_pack_dir, caplog):
        """Test handling when pack_data is not a dict."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"

        with open(pack_file, "w", encoding="utf-8") as f:
            f.write("42")  # YAML loads as int

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.ERROR):
                result = proxy._get_keyword_map("es")

        assert result == {}
        assert "Invalid language pack format" in caplog.text
        assert "expected dict, got int" in caplog.text

    def test_invalid_keywords_section_type(self, config, mock_pack_dir, caplog):
        """Test handling when keywords section is not a dict."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        invalid_pack = {"keywords": "should be dict"}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(invalid_pack, f)

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.ERROR):
                result = proxy._get_keyword_map("es")

        assert result == {}
        assert "Invalid keywords section" in caplog.text
        assert "expected dict, got str" in caplog.text

    def test_invalid_translation_value_skipped(self, config, mock_pack_dir, caplog):
        """Test that invalid translation values are skipped with warning."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        mixed_pack = {
            "keywords": {
                "def": "definir",  # Valid
                "class": 123,  # Invalid - int
                "if": "si",  # Valid
                "for": None,  # Invalid - None
            }
        }

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(mixed_pack, f)

        # Apply mock before creating proxy to avoid loading real language packs during __init__
        with patch.object(PylanceProxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.INFO):
                proxy = PylanceProxy(config)

        # Proxy is already initialized with the test pack, get the result from translator
        result = proxy.translator.keyword_map

        # Only valid entries should be in result
        assert result == {"definir": "def", "si": "if"}
        assert "Loaded 2 keyword translations for es" in caplog.text
        assert "Skipped 2 invalid translation entries" in caplog.text
        assert "Invalid translation for 'class'" in caplog.text

    def test_successful_load_with_count(self, config, mock_pack_dir, caplog):
        """Test successful load logs info message with count."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        valid_pack = {
            "keywords": {
                "def": "definir",
                "class": "clase",
                "if": "si",
                "elif": "sinoentonces",
                "else": "sino",
            }
        }

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(valid_pack, f)

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.INFO):
                result = proxy._get_keyword_map("es")

        assert len(result) == 5
        assert result["definir"] == "def"
        assert result["clase"] == "class"
        assert "Loaded 5 keyword translations for es" in caplog.text

    def test_empty_keywords_dict(self, config, mock_pack_dir, caplog):
        """Test handling of empty keywords dict."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        pack = {"keywords": {}}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(pack, f)

        proxy = PylanceProxy(config)

        with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.WARNING):
                result = proxy._get_keyword_map("es")

        assert result == {}
        assert "has no keywords section" in caplog.text

    def test_file_permission_error(self, config, mock_pack_dir, caplog):
        """Test handling of file permission errors."""
        from pathlib import Path

        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump({"keywords": {"def": "definir"}}, f)

        proxy = PylanceProxy(config)

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with patch.object(proxy, "_find_language_pack", return_value=mock_pack_dir):
                with patch.object(Path, "exists", return_value=True):
                    with caplog.at_level(logging.ERROR):
                        result = proxy._get_keyword_map("es")

        assert result == {}
        assert "Failed to read language pack file" in caplog.text

    def test_unexpected_exception_with_traceback(self, config, caplog):
        """Test that unexpected exceptions are logged with traceback."""
        proxy = PylanceProxy(config)

        with patch.object(
            proxy,
            "_find_language_pack",
            side_effect=RuntimeError("Unexpected error"),
        ):
            with caplog.at_level(logging.ERROR):
                result = proxy._get_keyword_map("es")

        assert result == {}
        assert "Unexpected error loading language pack for 'es'" in caplog.text
        assert "Unexpected error" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
