"""Tests for translation API coordinator."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytest

from legesher_i18n.api.cache import SQLiteCache
from legesher_i18n.api.coordinator import TranslationCoordinator
from legesher_i18n.api.providers.base import (
    TranslationError,
    TranslationProvider,
    TranslationResult,
    UsageStats,
)
from legesher_i18n.api.quality_validator import QualityValidator
from legesher_i18n.api.usage_tracker import UsageTracker


class MockProvider(TranslationProvider):
    """Mock translation provider for testing."""

    def __init__(
        self,
        name: str,
        quality_score: float = 8.0,
        should_fail: bool = False,
        translation: str = "Translated",
    ):
        self.name = name
        self.requires_api_key = False
        self.cost_per_million_chars = 0.0
        self._quality_score = quality_score
        self._should_fail = should_fail
        self._translation = translation
        self.translate_calls = []

    def is_available(self) -> bool:
        return True

    def supports(self, source_lang: str, target_lang: str) -> bool:
        return True

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[dict] = None,
    ) -> TranslationResult:
        self.translate_calls.append((text, source_lang, target_lang, context))

        if self._should_fail:
            raise TranslationError(f"{self.name} failed")

        return TranslationResult(
            text=self._translation,
            source_lang=source_lang,
            target_lang=target_lang,
            provider=self.name,
            confidence=0.9,
            billed_characters=len(text),
            quality_score=self._quality_score,
            timestamp=datetime.now(),
        )

    async def get_usage(self) -> Optional[UsageStats]:
        return None

    def get_quality_score(self, source_lang: str, target_lang: str) -> float:
        return self._quality_score


class TestTranslationCoordinator:
    """Test translation coordinator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def coordinator(self, temp_dir):
        """Create coordinator with mock providers."""
        cache = SQLiteCache(db_path=str(temp_dir / "cache.db"))
        tracker = UsageTracker(db_path=str(temp_dir / "usage.db"))

        providers = [
            MockProvider("high_quality", quality_score=9.0),
            MockProvider("medium_quality", quality_score=7.5),
            MockProvider("low_quality", quality_score=6.0),
        ]

        coord = TranslationCoordinator(
            providers=providers,
            cache=cache,
            usage_tracker=tracker,
            max_fallback_attempts=3,
        )
        yield coord
        # Explicitly close cache connections before temp directory cleanup (important on Windows)
        cache.close()

    @pytest.mark.asyncio
    async def test_translate_success(self, coordinator):
        """Test successful translation with highest quality provider."""
        result = await coordinator.translate("Hello", "en", "es")

        assert result.text == "Translated"
        assert result.provider == "high_quality"
        assert result.quality_score == 9.0

    @pytest.mark.asyncio
    async def test_translate_with_cache(self, coordinator):
        """Test translation uses cache."""
        # First request - no cache
        result1 = await coordinator.translate("Hello", "en", "es")
        assert result1.provider == "high_quality"
        assert result1.cached is False

        # Second request - should use cache
        result2 = await coordinator.translate("Hello", "en", "es")
        assert result2.provider == "cache"
        assert result2.cached is True
        assert result2.text == "Translated"

    @pytest.mark.asyncio
    async def test_translate_skip_cache(self, coordinator):
        """Test skipping cache."""
        # First request
        await coordinator.translate("Hello", "en", "es")

        # Second request with skip_cache
        result = await coordinator.translate("Hello", "en", "es", skip_cache=True)
        assert result.provider == "high_quality"
        assert result.cached is False

    @pytest.mark.asyncio
    async def test_automatic_fallback_on_failure(self, temp_dir):
        """Test automatic fallback when provider fails."""
        cache = SQLiteCache(db_path=str(temp_dir / "cache.db"))
        tracker = UsageTracker(db_path=str(temp_dir / "usage.db"))

        providers = [
            MockProvider("failing", should_fail=True),
            MockProvider("working", quality_score=8.0),
        ]

        coordinator = TranslationCoordinator(
            providers=providers, cache=cache, usage_tracker=tracker
        )

        result = await coordinator.translate("Hello", "en", "es")

        # Should fall back to working provider
        assert result.provider == "working"
        assert result.text == "Translated"

        # Close cache before cleanup
        cache.close()

    @pytest.mark.asyncio
    async def test_automatic_fallback_on_low_quality(self, temp_dir):
        """Test automatic fallback on low quality result."""
        cache = SQLiteCache(db_path=str(temp_dir / "cache.db"))
        tracker = UsageTracker(db_path=str(temp_dir / "usage.db"))

        providers = [
            MockProvider("low_quality", quality_score=5.0),  # Below threshold
            MockProvider("high_quality", quality_score=9.0),
        ]

        # Use strict quality validator
        validator = QualityValidator(min_quality_score=7.0)

        coordinator = TranslationCoordinator(
            providers=providers,
            cache=cache,
            usage_tracker=tracker,
            quality_validator=validator,
        )

        result = await coordinator.translate("Hello", "en", "es")

        # Should fall back to high quality provider
        assert result.provider == "high_quality"

        # Close cache before cleanup
        cache.close()

    @pytest.mark.asyncio
    async def test_all_providers_fail(self, temp_dir):
        """Test error when all providers fail."""
        cache = SQLiteCache(db_path=str(temp_dir / "cache.db"))
        tracker = UsageTracker(db_path=str(temp_dir / "usage.db"))

        providers = [
            MockProvider("fail1", should_fail=True),
            MockProvider("fail2", should_fail=True),
        ]

        coordinator = TranslationCoordinator(
            providers=providers, cache=cache, usage_tracker=tracker
        )

        with pytest.raises(TranslationError) as exc_info:
            await coordinator.translate("Hello", "en", "es")

        assert "failed after 2 attempts" in str(exc_info.value)

        # Close cache before cleanup
        cache.close()

    @pytest.mark.asyncio
    async def test_preferred_provider(self, coordinator):
        """Test using preferred provider."""
        result = await coordinator.translate(
            "Hello", "en", "es", preferred_provider="medium_quality"
        )

        # Should use preferred provider first
        assert result.provider == "medium_quality"

    @pytest.mark.asyncio
    async def test_batch_translation(self, coordinator):
        """Test batch translation."""
        texts = ["Hello", "Goodbye", "Thank you"]

        results = await coordinator.translate_batch(texts, "en", "es")

        assert len(results) == 3
        for result in results:
            assert result.text == "Translated"
            assert result.provider == "high_quality"

    @pytest.mark.asyncio
    async def test_usage_tracking(self, coordinator):
        """Test usage is tracked."""
        await coordinator.translate("Hello", "en", "es")

        stats = coordinator.get_usage_stats()

        assert stats["total"]["requests"] == 1
        assert stats["total"]["characters"] == 5  # "Hello" = 5 chars
        assert len(stats["by_provider"]) == 1

    @pytest.mark.asyncio
    async def test_cache_stats(self, coordinator):
        """Test cache statistics."""
        # Add some cached translations
        await coordinator.translate("Hello", "en", "es")
        await coordinator.translate("Goodbye", "en", "es")

        stats = coordinator.get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["backend"] == "sqlite"

    @pytest.mark.asyncio
    async def test_clear_cache(self, coordinator):
        """Test clearing cache."""
        # Add cached translation
        await coordinator.translate("Hello", "en", "es")

        # Clear cache
        deleted = coordinator.clear_cache()
        assert deleted == 1

        # Verify cache is empty
        stats = coordinator.get_cache_stats()
        assert stats["total_entries"] == 0

    @pytest.mark.asyncio
    async def test_add_provider(self, coordinator):
        """Test adding provider dynamically."""
        new_provider = MockProvider("new_provider", quality_score=10.0)

        coordinator.add_provider(new_provider, priority=0)

        # New provider should be first and used
        result = await coordinator.translate("Hello", "en", "es")
        assert result.provider == "new_provider"

    @pytest.mark.asyncio
    async def test_max_fallback_attempts(self, temp_dir):
        """Test max fallback attempts limit."""
        cache = SQLiteCache(db_path=str(temp_dir / "cache.db"))
        tracker = UsageTracker(db_path=str(temp_dir / "usage.db"))

        # Create 5 failing providers
        providers = [MockProvider(f"fail{i}", should_fail=True) for i in range(5)]

        coordinator = TranslationCoordinator(
            providers=providers,
            cache=cache,
            usage_tracker=tracker,
            max_fallback_attempts=2,  # Only try 2
        )

        with pytest.raises(TranslationError) as exc_info:
            await coordinator.translate("Hello", "en", "es")

        # Should only try 2 providers despite having 5
        assert "failed after 2 attempts" in str(exc_info.value)

        # Close cache before cleanup
        cache.close()

    @pytest.mark.asyncio
    async def test_provider_order_by_quality(self, temp_dir):
        """Test providers are ordered by quality score for language pair."""
        cache = SQLiteCache(db_path=str(temp_dir / "cache.db"))
        tracker = UsageTracker(db_path=str(temp_dir / "usage.db"))

        # Add providers in wrong order (low to high quality)
        providers = [
            MockProvider("low", quality_score=6.0, translation="Low"),
            MockProvider("medium", quality_score=7.5, translation="Medium"),
            MockProvider("high", quality_score=9.0, translation="High"),
        ]

        coordinator = TranslationCoordinator(
            providers=providers, cache=cache, usage_tracker=tracker
        )

        result = await coordinator.translate("Hello", "en", "es")

        # Should automatically use highest quality provider first
        assert result.provider == "high"
        assert result.text == "High"

        # Close cache before cleanup
        cache.close()

    @pytest.mark.asyncio
    async def test_no_providers_available(self, temp_dir):
        """Test error when no providers are available."""
        cache = SQLiteCache(db_path=str(temp_dir / "cache.db"))
        tracker = UsageTracker(db_path=str(temp_dir / "usage.db"))

        coordinator = TranslationCoordinator(
            providers=[],  # No providers
            cache=cache,
            usage_tracker=tracker,
        )

        with pytest.raises(TranslationError) as exc_info:
            await coordinator.translate("Hello", "en", "es")

        assert "No translation providers available" in str(exc_info.value)

        # Close cache before cleanup
        cache.close()
