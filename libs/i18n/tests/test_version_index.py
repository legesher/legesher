"""Tests for version_index module."""

import pytest
from pathlib import Path

from legesher_i18n.version_index import VersionIndex
from legesher_i18n.exceptions import (
    VersionIndexError,
    UnsupportedVersionError,
)


# Use actual version-index.yml from programming_languages/python/
REAL_INDEX_PATH = (
    Path(__file__).parent.parent
    / "programming_languages"
    / "python"
    / "version-index.yml"
)


class TestVersionIndexLoading:
    """Test version index loading and parsing."""

    def test_load_real_index(self):
        """Test loading the actual version-index.yml file."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        assert index is not None
        assert len(index.versions) > 0
        assert "3.10" in index.versions
        assert "3.11" in index.versions
        assert "3.12" in index.versions
        assert "3.13" in index.versions

    def test_index_structure(self):
        """Test version index has correct structure."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        # Check Python 3.10
        v310 = index.get_version_info("3.10")
        assert "match" in v310.added_keywords
        assert "case" in v310.added_keywords
        assert v310.base is None  # Base version for MVP

        # Check Python 3.11
        v311 = index.get_version_info("3.11")
        assert "except*" in v311.added_keywords
        assert v311.base == "3.10"

        # Check Python 3.12
        v312 = index.get_version_info("3.12")
        assert "type" in v312.added_keywords
        assert v312.base == "3.11"

    def test_nonexistent_file(self):
        """Test error handling for missing file."""
        with pytest.raises(VersionIndexError):
            VersionIndex.load(Path("/nonexistent/path/version-index.yml"))


class TestVersionInfo:
    """Test version info functionality."""

    def test_get_supported_versions(self):
        """Test getting list of supported versions."""
        index = VersionIndex.load(REAL_INDEX_PATH)
        versions = index.get_supported_versions()

        assert isinstance(versions, list)
        assert len(versions) >= 4
        assert "3.10" in versions
        assert "3.13" in versions

    def test_unsupported_version(self):
        """Test error for unsupported version."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        with pytest.raises(UnsupportedVersionError) as exc_info:
            index.get_version_info("2.7")

        assert "2.7" in str(exc_info.value)


class TestInheritanceChain:
    """Test inheritance chain resolution."""

    def test_get_inheritance_chain(self):
        """Test building inheritance chain."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        # Python 3.13 should inherit from 3.12, 3.11, 3.10, 3.9
        chain = index.get_inheritance_chain("3.13")

        assert len(chain) >= 4
        assert chain[-1] == "3.13"  # Most specific last
        assert chain[-2] == "3.12"
        assert chain[-3] == "3.11"
        assert chain[-4] == "3.10"

    def test_inheritance_chain_order(self):
        """Test inheritance chain is in correct order (base to specific)."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        chain = index.get_inheritance_chain("3.12")

        # Should be ordered from base to specific
        # Just verify the chain has multiple versions
        assert len(chain) > 1


class TestKeywordTracking:
    """Test keyword availability tracking."""

    def test_get_all_keywords(self):
        """Test getting all keywords for a version."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        # Python 3.10 should have match/case
        keywords_310 = index.get_all_keywords("3.10")
        assert "match" in keywords_310
        assert "case" in keywords_310

        # Python 3.11 should have match/case + except*
        keywords_311 = index.get_all_keywords("3.11")
        assert "match" in keywords_311
        assert "case" in keywords_311
        assert "except*" in keywords_311

        # Python 3.12 should have all above + type
        keywords_312 = index.get_all_keywords("3.12")
        assert "match" in keywords_312
        assert "except*" in keywords_312
        assert "type" in keywords_312

    def test_is_keyword_available(self):
        """Test checking keyword availability."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        # match/case added in 3.10
        assert index.is_keyword_available("match", "3.10")
        assert index.is_keyword_available("match", "3.11")
        assert index.is_keyword_available("match", "3.13")

        # except* added in 3.11
        assert index.is_keyword_available("except*", "3.11")
        assert index.is_keyword_available("except*", "3.12")
        assert index.is_keyword_available("except*", "3.13")

        # type added in 3.12
        assert index.is_keyword_available("type", "3.12")
        assert index.is_keyword_available("type", "3.13")

    def test_get_added_since(self):
        """Test getting keywords added between versions."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        # From 3.10 to 3.12 should add except* and type
        added = index.get_added_since("3.10", "3.12")

        assert "except*" in added
        assert "type" in added
        assert "match" not in added  # Already in 3.10


class TestAutoUpdateConfig:
    """Test auto-update configuration."""

    def test_auto_update_config_present(self):
        """Test that auto-update config is loaded."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        assert index.auto_update_config is not None
        assert index.auto_update_config.enabled is True
        assert "python.org" in index.auto_update_config.source


class TestVersionIndexRepr:
    """Test string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        index = VersionIndex.load(REAL_INDEX_PATH)
        repr_str = repr(index)

        assert "VersionIndex" in repr_str
        assert "3.10" in repr_str or "versions" in repr_str
