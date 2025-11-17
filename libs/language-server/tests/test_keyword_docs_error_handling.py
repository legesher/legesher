"""Unit tests for keyword_docs.py error handling.

Tests comprehensive error handling for language pack loading including:
- Missing directories
- Missing files with version fallback
- Invalid YAML syntax
- Missing keywords section
- Invalid keyword mappings
- Successful loads with logging

Related to CORE-447
"""

import logging
from unittest.mock import patch

import pytest
import yaml

from legesher_language_server.utils.keyword_docs import KeywordDocumentation


class TestKeywordDocsErrorHandling:
    """Test error handling in KeywordDocumentation class."""

    @pytest.fixture
    def keyword_docs(self):
        """Create KeywordDocumentation instance."""
        return KeywordDocumentation()

    @pytest.fixture
    def mock_pack_dir(self, tmp_path):
        """Create temporary pack directory structure."""
        pack_dir = tmp_path / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)
        return pack_dir

    def test_directory_not_found(self, keyword_docs, caplog):
        """Test handling when language pack directory doesn't exist."""
        with caplog.at_level(logging.WARNING):
            result = keyword_docs.get_keyword_translation("def", "nonexistent")

        assert result is None
        assert "Language pack directory for 'nonexistent' not found" in caplog.text

    def test_pack_file_missing_all_versions(self, keyword_docs, tmp_path, caplog):
        """Test handling when no pack files exist for any Python version."""
        pack_dir = tmp_path / "i18n-python-es"
        pack_subdir = pack_dir / "legesher_i18n_python_es" / "packs"
        pack_subdir.mkdir(parents=True)

        with patch.object(keyword_docs, "_find_language_pack", return_value=pack_dir):
            with caplog.at_level(logging.WARNING):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result is None
        assert "Language pack file not found for 'es'" in caplog.text
        assert "3.10, 3.11, 3.12, 3.13" in caplog.text

    def test_version_fallback_finds_311(self, keyword_docs, mock_pack_dir, caplog):
        """Test version fallback finds 3.11 when 3.10 is missing."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.11.yml"
        valid_pack = {"keywords": {"def": "definir", "class": "clase"}}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(valid_pack, f)

        with patch.object(keyword_docs, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.DEBUG):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result == "definir"

    def test_invalid_yaml_syntax(self, keyword_docs, mock_pack_dir, caplog):
        """Test handling of malformed YAML with syntax errors."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"

        with open(pack_file, "w", encoding="utf-8") as f:
            f.write("keywords:\n  def: definir\n  class: [unclosed")

        with patch.object(keyword_docs, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.ERROR):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result is None
        assert "Invalid YAML in es language pack" in caplog.text

    def test_missing_keywords_section(self, keyword_docs, mock_pack_dir, caplog):
        """Test handling when keywords section is missing from pack."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        invalid_pack = {"language": "es", "target": "python"}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(invalid_pack, f)

        with patch.object(keyword_docs, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.WARNING):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result is None
        assert "has no keywords section" in caplog.text

    def test_invalid_pack_data_type(self, keyword_docs, mock_pack_dir, caplog):
        """Test handling when pack_data is not a dict."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"

        with open(pack_file, "w", encoding="utf-8") as f:
            f.write("just a string")

        with patch.object(keyword_docs, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.ERROR):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result is None
        assert "Invalid language pack format" in caplog.text
        assert "expected dict, got str" in caplog.text

    def test_invalid_keywords_section_type(self, keyword_docs, mock_pack_dir, caplog):
        """Test handling when keywords section is not a dict."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        invalid_pack = {"keywords": ["def", "class"]}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(invalid_pack, f)

        with patch.object(keyword_docs, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.ERROR):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result is None
        assert "Invalid keywords section" in caplog.text
        assert "expected dict, got list" in caplog.text

    def test_invalid_translation_value_type(self, keyword_docs, mock_pack_dir, caplog):
        """Test handling when translation value is not a string."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        invalid_pack = {"keywords": {"def": 12345}}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(invalid_pack, f)

        with patch.object(keyword_docs, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.WARNING):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result is None
        assert "Invalid translation for keyword 'def'" in caplog.text
        assert "expected string, got int" in caplog.text

    def test_successful_load_with_info_logging(self, keyword_docs, mock_pack_dir, caplog):
        """Test successful load logs info message with translation count."""
        pack_file = mock_pack_dir / "legesher_i18n_python_es" / "packs" / "3.10.yml"
        valid_pack = {"keywords": {"def": "definir"}}

        with open(pack_file, "w", encoding="utf-8") as f:
            yaml.dump(valid_pack, f)

        with patch.object(keyword_docs, "_find_language_pack", return_value=mock_pack_dir):
            with caplog.at_level(logging.INFO):
                result = keyword_docs.get_keyword_translation("def", "es")

        assert result == "definir"
        assert "Found translation for 'def' in es" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
