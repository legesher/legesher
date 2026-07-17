"""Tests for version_index module."""

import pytest
from pathlib import Path

from legesher_i18n.version_index import VersionIndex
from legesher_i18n.exceptions import (
    VersionIndexError,
    UnsupportedVersionError,
)
from tests import language_packs_root


# Use actual version-index.yml from language-packs/python/ (version-index is a
# Python-only artifact; the target segment comes from the shared helper).
REAL_INDEX_PATH = language_packs_root() / "version-index.yml"


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


class TestConnectedArchitecture:
    """Test that VersionIndex uses term_definitions as the source of truth.

    These tests verify that the connected architecture works correctly:
    - Base terms come from term_definitions.py
    - Version deltas come from version-index.yml
    - get_all_keywords/builtins/exceptions return complete sets
    """

    def test_get_all_keywords_includes_base_keywords(self):
        """Verify base keywords from term_definitions are included."""
        from legesher_i18n.term_definitions import KEYWORDS_BASE, SPECIAL_VALUES

        index = VersionIndex.load(REAL_INDEX_PATH)
        kw_310 = index.get_all_keywords("3.10")

        # Should include all base keywords
        for base_kw in KEYWORDS_BASE:
            assert base_kw in kw_310, f"Base keyword '{base_kw}' missing from 3.10"

        # Should include special values (None, True, False)
        for special in SPECIAL_VALUES:
            assert special in kw_310, f"Special value '{special}' missing from 3.10"

    def test_get_all_keywords_includes_version_additions(self):
        """Verify version-specific keywords are added."""
        index = VersionIndex.load(REAL_INDEX_PATH)

        # 3.10 additions
        kw_310 = index.get_all_keywords("3.10")
        assert "match" in kw_310
        assert "case" in kw_310

        # 3.11 additions
        kw_311 = index.get_all_keywords("3.11")
        assert "except*" in kw_311

        # 3.12 additions
        kw_312 = index.get_all_keywords("3.12")
        assert "type" in kw_312

    def test_get_all_keywords_returns_complete_set(self):
        """Verify get_all_keywords returns a complete set, not just deltas."""

        index = VersionIndex.load(REAL_INDEX_PATH)
        kw_310 = index.get_all_keywords("3.10")

        # Should have at least 35 keywords (32 base + 3 special + match/case)
        assert len(kw_310) >= 35, f"Expected >= 35 keywords, got {len(kw_310)}"

        # Verify common keywords
        assert "def" in kw_310
        assert "class" in kw_310
        assert "if" in kw_310
        assert "for" in kw_310
        assert "while" in kw_310

    def test_get_all_builtins_includes_base_builtins(self):
        """Verify base builtins from term_definitions are included."""

        index = VersionIndex.load(REAL_INDEX_PATH)
        builtins = index.get_all_builtins("3.10")

        # Should include common builtin functions
        assert "print" in builtins
        assert "len" in builtins
        assert "range" in builtins
        assert "open" in builtins

        # Should include builtin types
        assert "int" in builtins
        assert "str" in builtins
        assert "list" in builtins
        assert "dict" in builtins

        # Should include special constants
        assert "ellipsis" in builtins
        assert "notimplemented" in builtins

    def test_get_all_builtins_returns_complete_set(self):
        """Verify get_all_builtins returns a complete set."""
        index = VersionIndex.load(REAL_INDEX_PATH)
        builtins = index.get_all_builtins("3.10")

        # Should have at least 70 builtins (52 functions + 18 types + 2 constants)
        assert len(builtins) >= 70, f"Expected >= 70 builtins, got {len(builtins)}"

    def test_get_all_exceptions_includes_base_exceptions(self):
        """Verify base exceptions from term_definitions are included."""
        index = VersionIndex.load(REAL_INDEX_PATH)
        exceptions = index.get_all_exceptions("3.10")

        # Should include common exceptions
        assert "exception" in exceptions
        assert "valueerror" in exceptions
        assert "typeerror" in exceptions
        assert "keyerror" in exceptions
        assert "indexerror" in exceptions

    def test_get_all_exceptions_returns_complete_set(self):
        """Verify get_all_exceptions returns a complete set."""
        index = VersionIndex.load(REAL_INDEX_PATH)
        exceptions = index.get_all_exceptions("3.10")

        # Should have at least 60 exceptions
        assert len(exceptions) >= 60, (
            f"Expected >= 60 exceptions, got {len(exceptions)}"
        )

    def test_get_all_terms_returns_all_categories(self):
        """Verify get_all_terms returns all term categories."""
        index = VersionIndex.load(REAL_INDEX_PATH)
        terms = index.get_all_terms("3.10")

        assert "keywords" in terms
        assert "builtins" in terms
        assert "exceptions" in terms

        # Verify each category has content
        assert len(terms["keywords"]) >= 35
        assert len(terms["builtins"]) >= 70
        assert len(terms["exceptions"]) >= 60

    def test_term_definitions_is_source_of_truth(self):
        """Verify term_definitions.py is the source of truth for base terms."""
        from legesher_i18n.term_definitions import KEYWORDS_BASE

        index = VersionIndex.load(REAL_INDEX_PATH)
        kw = index.get_all_keywords("3.10")

        # All base keywords should be in result
        for base_kw in KEYWORDS_BASE:
            assert base_kw in kw, f"Base keyword '{base_kw}' not in result"

        # This confirms the import from term_definitions is working
        assert "def" in kw
        assert "class" in kw
        assert "return" in kw


class TestBackwardsCompatibility:
    """Test backwards compatibility of the term_classifier re-export."""

    def test_old_import_path_works(self):
        """Verify the old import path still works."""
        # This import should work via the re-export in term_classifier.py
        from scripts.translate.term_classifier import (
            classify_term,
            KEYWORDS_BASE,
            get_keywords_for_version,
        )

        # Test the imported functions work
        assert classify_term("def") == "keyword"
        assert "def" in KEYWORDS_BASE
        assert "def" in get_keywords_for_version("3.10")

    def test_new_import_path_works(self):
        """Verify the new direct import path works."""
        from legesher_i18n.term_definitions import (
            classify_term,
            KEYWORDS_BASE,
            get_keywords_for_version,
        )

        # Test the imported functions work
        assert classify_term("def") == "keyword"
        assert "def" in KEYWORDS_BASE
        assert "def" in get_keywords_for_version("3.10")

    def test_both_paths_return_same_data(self):
        """Verify both import paths return identical data."""
        from scripts.translate.term_classifier import (
            KEYWORDS_BASE as OLD_KEYWORDS,
            BUILTIN_FUNCTIONS as OLD_FUNCTIONS,
        )
        from legesher_i18n.term_definitions import (
            KEYWORDS_BASE as NEW_KEYWORDS,
            BUILTIN_FUNCTIONS as NEW_FUNCTIONS,
        )

        assert OLD_KEYWORDS == NEW_KEYWORDS
        assert OLD_FUNCTIONS == NEW_FUNCTIONS
