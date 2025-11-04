"""Tests for translation API cache backends."""

import tempfile
from pathlib import Path

import pytest

from legesher_i18n.api.cache import SQLiteCache


class TestSQLiteCache:
    """Test SQLite cache backend."""

    @pytest.fixture
    def cache(self):
        """Create temporary SQLite cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_cache.db")
            cache_instance = SQLiteCache(db_path=db_path, ttl_seconds=3600)
            yield cache_instance
            # Explicitly close connections before temp directory cleanup (important on Windows)
            cache_instance.close()

    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("Hello", "en", "es")
        assert result is None

    def test_cache_hit(self, cache):
        """Test cache hit returns cached translation."""
        cache.set("Hello", "en", "es", "Hola", "deepl")
        result = cache.get("Hello", "en", "es")
        assert result == "Hola"

    def test_cache_different_language_pairs(self, cache):
        """Test cache differentiates language pairs."""
        cache.set("Hello", "en", "es", "Hola", "deepl")
        cache.set("Hello", "en", "fr", "Bonjour", "deepl")

        assert cache.get("Hello", "en", "es") == "Hola"
        assert cache.get("Hello", "en", "fr") == "Bonjour"

    def test_cache_different_texts(self, cache):
        """Test cache differentiates texts."""
        cache.set("Hello", "en", "es", "Hola", "deepl")
        cache.set("Goodbye", "en", "es", "Adiós", "deepl")

        assert cache.get("Hello", "en", "es") == "Hola"
        assert cache.get("Goodbye", "en", "es") == "Adiós"

    def test_cache_update(self, cache):
        """Test cache update replaces old value."""
        cache.set("Hello", "en", "es", "Hola", "deepl")
        cache.set("Hello", "en", "es", "¡Hola!", "google")

        result = cache.get("Hello", "en", "es")
        assert result == "¡Hola!"

    def test_cache_clear(self, cache):
        """Test cache clear removes all entries."""
        cache.set("Hello", "en", "es", "Hola", "deepl")
        cache.set("Goodbye", "en", "es", "Adiós", "deepl")

        deleted = cache.clear()
        assert deleted == 2
        assert cache.get("Hello", "en", "es") is None
        assert cache.get("Goodbye", "en", "es") is None

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        cache.set("Hello", "en", "es", "Hola", "deepl")
        cache.set("Goodbye", "en", "es", "Adiós", "google")

        stats = cache.get_stats()
        assert stats["backend"] == "sqlite"
        assert stats["total_entries"] == 2
        assert stats["by_provider"]["deepl"] == 1
        assert stats["by_provider"]["google"] == 1
        assert stats["ttl_seconds"] == 3600

    def test_cache_expiration(self):
        """Test cache entries expire after TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_cache.db")
            # Create cache with 0-second TTL (immediately expired)
            cache = SQLiteCache(db_path=db_path, ttl_seconds=0)

            cache.set("Hello", "en", "es", "Hola", "deepl")

            # Should be expired immediately
            result = cache.get("Hello", "en", "es")
            assert result is None

            # Close connections before cleanup
            cache.close()

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_cache.db")
            # Create cache with 0-second TTL
            cache = SQLiteCache(db_path=db_path, ttl_seconds=0)

            cache.set("Hello", "en", "es", "Hola", "deepl")
            cache.set("Goodbye", "en", "es", "Adiós", "deepl")

            # Manually trigger cleanup
            deleted = cache.cleanup_expired()
            assert deleted == 2

            stats = cache.get_stats()
            assert stats["total_entries"] == 0

            # Close connections before cleanup
            cache.close()
