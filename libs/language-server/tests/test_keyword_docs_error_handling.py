"""Unit tests for keyword_docs.py error handling.

Tests comprehensive error handling for language pack loading including:
- Missing language packs
- Invalid keyword lookups
- Successful loads with logging
- Cache behavior validation (CORE-446)

After CORE-446 refactoring, error handling is delegated to LanguagePackLoader
which has its own comprehensive tests in legesher_i18n package.

These tests verify that KeywordDocumentation gracefully handles errors
by returning None and logging warnings.

Related to CORE-447, CORE-446
"""

import logging

import pytest

from legesher_language_server.utils.keyword_docs import KeywordDocumentation


class TestKeywordDocsErrorHandling:
    """Test error handling in KeywordDocumentation class."""

    @pytest.fixture
    def keyword_docs(self):
        """Create KeywordDocumentation instance."""
        return KeywordDocumentation()

    def test_directory_not_found(self, keyword_docs, caplog):
        """Test handling when language pack doesn't exist."""
        with caplog.at_level(logging.WARNING):
            result = keyword_docs.get_keyword_translation("def", "nonexistent")

        assert result is None
        assert "Failed to load keyword translation" in caplog.text
        assert "nonexistent" in caplog.text

    def test_successful_translation_spanish(self, keyword_docs):
        """Test successful keyword translation for Spanish."""
        result = keyword_docs.get_keyword_translation("def", "es")
        assert result == "definir"

        result = keyword_docs.get_keyword_translation("class", "es")
        assert result == "clase"

    def test_successful_translation_arabic(self, keyword_docs):
        """Test successful keyword translation for Arabic."""
        result = keyword_docs.get_keyword_translation("def", "ar")
        assert result == "تعريف"

    def test_keyword_not_in_pack(self, keyword_docs):
        """Test handling when keyword doesn't exist in language pack."""
        # Use a valid language but nonexistent keyword
        result = keyword_docs.get_keyword_translation("nonexistent_keyword_xyz", "es")
        assert result is None

    def test_caching_behavior(self, keyword_docs):
        """Test that repeated calls use cached language pack.

        This indirectly tests CORE-446 cache implementation.
        Repeated calls should be fast (using cache) not slow (reloading YAML).
        """
        import time

        # First call - loads from cache or disk
        result1 = keyword_docs.get_keyword_translation("def", "es")

        # Second call - should use cache
        start = time.perf_counter()
        result2 = keyword_docs.get_keyword_translation("class", "es")
        second_time = (time.perf_counter() - start) * 1000

        assert result1 == "definir"
        assert result2 == "clase"

        # Second call should be fast (using cache) - validates CORE-446 cache is working
        assert second_time < 5, f"Cached call took {second_time:.2f}ms, expected <5ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
