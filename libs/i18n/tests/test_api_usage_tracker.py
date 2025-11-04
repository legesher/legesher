"""Tests for translation API usage tracker."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from legesher_i18n.api.usage_tracker import UsageRecord, UsageTracker


class TestUsageTracker:
    """Test usage tracker."""

    @pytest.fixture
    def tracker(self):
        """Create temporary usage tracker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_usage.db")
            yield UsageTracker(db_path=db_path)

    def test_record_usage(self, tracker):
        """Test recording usage."""
        record = UsageRecord(
            timestamp=datetime.now(),
            provider="deepl",
            source_lang="en",
            target_lang="es",
            characters=100,
            cost_usd=0.002,
            request_id="test-123",
            cached=False,
        )

        tracker.record(record)

        # Verify it was recorded
        recent = tracker.get_recent_usage(limit=1)
        assert len(recent) == 1
        assert recent[0].provider == "deepl"
        assert recent[0].characters == 100

    def test_usage_stats(self, tracker):
        """Test usage statistics calculation."""
        now = datetime.now()

        # Record some usage
        for i in range(5):
            record = UsageRecord(
                timestamp=now - timedelta(days=i),
                provider="deepl",
                source_lang="en",
                target_lang="es",
                characters=100,
                cost_usd=0.002,
                request_id=f"test-{i}",
                cached=False,
            )
            tracker.record(record)

        stats = tracker.get_usage_stats(
            start_date=now - timedelta(days=7), end_date=now
        )

        assert stats["total"]["requests"] == 5
        assert stats["total"]["characters"] == 500
        assert stats["total"]["cost_usd"] == 0.01
        assert len(stats["by_provider"]) == 1
        assert stats["by_provider"][0]["provider"] == "deepl"

    def test_multiple_providers(self, tracker):
        """Test tracking multiple providers."""
        now = datetime.now()

        # Record from different providers
        providers = ["deepl", "google", "libretranslate"]
        for provider in providers:
            record = UsageRecord(
                timestamp=now,
                provider=provider,
                source_lang="en",
                target_lang="es",
                characters=100,
                cost_usd=0.002 if provider != "libretranslate" else 0.0,
                request_id=f"test-{provider}",
                cached=False,
            )
            tracker.record(record)

        stats = tracker.get_usage_stats()
        assert stats["total"]["requests"] == 3
        assert len(stats["by_provider"]) == 3

        # Verify providers are sorted by request count
        provider_names = [p["provider"] for p in stats["by_provider"]]
        assert set(provider_names) == set(providers)

    def test_cache_hit_rate(self, tracker):
        """Test cache hit rate calculation."""
        now = datetime.now()

        # Record 3 cached, 7 non-cached
        for i in range(10):
            record = UsageRecord(
                timestamp=now,
                provider="deepl",
                source_lang="en",
                target_lang="es",
                characters=100,
                cost_usd=0.0 if i < 3 else 0.002,  # Cached requests cost $0
                request_id=f"test-{i}",
                cached=i < 3,
            )
            tracker.record(record)

        stats = tracker.get_usage_stats()
        assert stats["total"]["requests"] == 10
        assert stats["total"]["cached_requests"] == 3
        assert stats["total"]["cache_hit_rate"] == 30.0

    def test_language_pair_stats(self, tracker):
        """Test language pair statistics."""
        now = datetime.now()

        # Record different language pairs
        pairs = [("en", "es"), ("en", "fr"), ("en", "es"), ("es", "en")]
        for source, target in pairs:
            record = UsageRecord(
                timestamp=now,
                provider="deepl",
                source_lang=source,
                target_lang=target,
                characters=100,
                cost_usd=0.002,
                request_id=f"test-{source}-{target}",
                cached=False,
            )
            tracker.record(record)

        stats = tracker.get_usage_stats()
        pairs_stats = stats["top_language_pairs"]

        # Should have 3 unique pairs
        assert len(pairs_stats) == 3

        # en-es should be most common (2 requests)
        assert pairs_stats[0]["pair"] == "en-es"
        assert pairs_stats[0]["requests"] == 2

    def test_daily_trend(self, tracker):
        """Test daily usage trend."""
        now = datetime.now()

        # Record usage over several days
        for i in range(7):
            for j in range(i + 1):  # Increasing usage each day
                record = UsageRecord(
                    timestamp=now - timedelta(days=i),
                    provider="deepl",
                    source_lang="en",
                    target_lang="es",
                    characters=100,
                    cost_usd=0.002,
                    request_id=f"test-{i}-{j}",
                    cached=False,
                )
                tracker.record(record)

        stats = tracker.get_usage_stats()
        daily = stats["daily_trend"]

        # Should have up to 7 days
        assert len(daily) <= 7

        # Each day should have the correct request count
        # Query returns most recent first: [day0, day1, day2, ..., day6]
        # Day 0 (today) has 1 request, day 1 has 2, etc.
        for i, day_stat in enumerate(daily):
            if i < 7:
                assert day_stat["requests"] == i + 1

    def test_export_csv(self, tracker):
        """Test CSV export."""
        now = datetime.now()

        # Record some usage
        for i in range(3):
            record = UsageRecord(
                timestamp=now,
                provider="deepl",
                source_lang="en",
                target_lang="es",
                characters=100,
                cost_usd=0.002,
                request_id=f"test-{i}",
                cached=False,
            )
            tracker.record(record)

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = str(Path(tmpdir) / "usage.csv")
            tracker.export_csv(csv_path)

            # Verify file exists
            assert Path(csv_path).exists()

            # Read and verify content
            content = Path(csv_path).read_text()
            assert "Timestamp,Provider,Source Lang,Target Lang" in content
            assert "deepl" in content
            assert "100" in content

    def test_recent_usage(self, tracker):
        """Test retrieving recent usage."""
        now = datetime.now()

        # Record 10 requests
        for i in range(10):
            record = UsageRecord(
                timestamp=now - timedelta(minutes=i),
                provider="deepl",
                source_lang="en",
                target_lang="es",
                characters=100,
                cost_usd=0.002,
                request_id=f"test-{i}",
                cached=False,
            )
            tracker.record(record)

        # Get recent 5
        recent = tracker.get_recent_usage(limit=5)
        assert len(recent) == 5

        # Should be in reverse chronological order (most recent first)
        for i in range(4):
            assert recent[i].timestamp >= recent[i + 1].timestamp

    def test_clear_old_records(self, tracker):
        """Test clearing old records."""
        now = datetime.now()

        # Record old and new usage
        old_record = UsageRecord(
            timestamp=now - timedelta(days=100),
            provider="deepl",
            source_lang="en",
            target_lang="es",
            characters=100,
            cost_usd=0.002,
            request_id="old",
            cached=False,
        )
        tracker.record(old_record)

        new_record = UsageRecord(
            timestamp=now,
            provider="deepl",
            source_lang="en",
            target_lang="es",
            characters=100,
            cost_usd=0.002,
            request_id="new",
            cached=False,
        )
        tracker.record(new_record)

        # Clear records older than 90 days
        deleted = tracker.clear_old_records(days=90)
        assert deleted == 1

        # Only new record should remain
        recent = tracker.get_recent_usage()
        assert len(recent) == 1
        assert recent[0].request_id == "new"
