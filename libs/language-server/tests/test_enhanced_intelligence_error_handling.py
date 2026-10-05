"""Unit tests for enhanced_intelligence.py error handling.

Tests comprehensive error handling for language pack loading in EnhancedIntelligenceProxy including:
- Missing language packs
- Invalid language lookups
- Successful loads with logging
- Cache behavior validation (CORE-446)

After CORE-446 refactoring, error handling is delegated to LanguagePackLoader
which has its own comprehensive tests in legesher_i18n package.

These tests verify that EnhancedIntelligenceProxy._get_keyword_map() gracefully handles errors
by returning empty dict and logging warnings.

Related to CORE-447, CORE-446
"""

import logging

import pytest

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy
from tests.timing import assert_within


class TestEnhancedIntelligenceProxyErrorHandling:
    """Test error handling in EnhancedIntelligenceProxy._get_keyword_map()."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return LanguageServerConfig(
            source_language="en",
            target_language="es",
            enhanced_intelligence_enabled=False,  # Don't start Pyright process in tests
        )

    @pytest.fixture
    def proxy(self, config):
        """Create EnhancedIntelligenceProxy instance."""
        return EnhancedIntelligenceProxy(config)

    def test_directory_not_found(self, proxy, caplog):
        """Test handling when language pack doesn't exist."""
        with caplog.at_level(logging.WARNING):
            result = proxy._get_keyword_map("nonexistent")

        assert result == {}
        assert "Failed to load language pack" in caplog.text
        assert "nonexistent" in caplog.text

    def test_successful_spanish_load(self, proxy):
        """Test successful keyword map loading for Spanish."""
        result = proxy._get_keyword_map("es")

        # Verify reversed mapping (localized → English)
        assert result.get("definir") == "def"
        assert result.get("clase") == "class"
        assert result.get("si") == "if"
        assert len(result) > 30  # Should have all Python keywords

    def test_successful_arabic_load(self, proxy):
        """Test successful keyword map loading for Arabic."""
        result = proxy._get_keyword_map("ar")

        # Verify reversed mapping (localized → English)
        assert result.get("تعريف") == "def"
        assert result.get("الصف") == "class"
        assert len(result) > 30  # Should have all Python keywords

    @pytest.mark.timing
    def test_caching_behavior(self, proxy):
        """Test that repeated calls use cached language pack.

        This indirectly tests CORE-446 cache implementation. The proof is the
        lru_cache hit count (CORE-2321): a repeated call must not reload the
        YAML. Its time is checked only under ``make bench``.
        """
        import time

        from legesher_i18n import LanguagePackLoader

        # First call - loads from cache or disk
        result1 = proxy._get_keyword_map("es")

        # Second call - should use cache
        hits_before = LanguagePackLoader.load.cache_info().hits
        start = time.perf_counter()
        result2 = proxy._get_keyword_map("es")
        second_time = (time.perf_counter() - start) * 1000
        hits = LanguagePackLoader.load.cache_info().hits - hits_before

        # Verify results are consistent
        assert result1 == result2
        assert len(result1) > 30

        # The CORE-446 cache path, proved by its hit count
        assert hits == 1, f"the repeated call produced {hits} lru_cache hit(s), expected 1"
        assert_within(second_time, 5, "Cached call")

    def test_proxy_initialization_loads_target_language(self, config, caplog):
        """Test that EnhancedIntelligenceProxy initialization loads the target language pack."""
        with caplog.at_level(logging.DEBUG):
            proxy = EnhancedIntelligenceProxy(config)

        # Verify translator has keyword map for target language
        assert len(proxy.translator.keyword_map) > 30
        assert proxy.translator.keyword_map.get("definir") == "def"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
