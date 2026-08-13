"""Every consumer of a cost must survive that cost being unknown.

Rates are operator-supplied (see ``api/rates.py``), so an unconfigured
provider reports ``None`` rather than a fabricated ``0.0``. That value then
flows into the usage database, the summary aggregates, the CLI and the
dashboard — and a review of CORE-1863 found each of those crashing or
resurrecting the zero, while the suite stayed green because nothing ever
passed them a None.

These tests pass them a None.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pytest

from legesher_i18n.api.cli import format_currency
from legesher_i18n.api.dashboard import fmt_cost
from legesher_i18n.api.usage_tracker import UsageRecord, UsageTracker


def _record(cost, provider="anthropic", chars=100):
    return UsageRecord(
        timestamp=datetime.now(),
        provider=provider,
        source_lang="en",
        target_lang="fr",
        characters=chars,
        cost_usd=cost,
        request_id="req-1",
        cached=False,
    )


class TestLegacyDatabaseMigration:
    def test_notnull_cost_column_is_migrated(self, tmp_path):
        """A database created before rates were configurable must accept None.

        `CREATE TABLE IF NOT EXISTS` does not alter an existing table, so
        without a migration the first unknown-cost insert raises IntegrityError
        — and that escapes `coordinator.translate()`, losing a translation that
        already succeeded.
        """
        db = tmp_path / "usage.db"
        conn = sqlite3.connect(db)
        conn.execute("""
            CREATE TABLE usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provider TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                characters INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                request_id TEXT,
                cached BOOLEAN DEFAULT 0
            )
        """)
        conn.execute(
            "INSERT INTO usage (timestamp, provider, source_lang, target_lang,"
            " characters, cost_usd) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(), "google", "en", "fr", 50, 0.001),
        )
        conn.commit()
        conn.close()

        tracker = UsageTracker(db_path=str(db))
        tracker.record(_record(None))

        rows = (
            sqlite3.connect(db)
            .execute("SELECT cost_usd FROM usage ORDER BY id")
            .fetchall()
        )
        assert [r[0] for r in rows] == [0.001, None], "pre-existing rows must survive"


class TestUnknownCostDoesNotCrashConsumers:
    @pytest.fixture
    def tracker(self, tmp_path):
        return UsageTracker(db_path=str(tmp_path / "usage.db"))

    def test_recording_an_unknown_cost_succeeds(self, tracker):
        tracker.record(_record(None))

    def test_batch_with_unknown_costs_does_not_raise(self, tracker):
        tracker.record_batch([_record(None), _record(0.5)])

    def test_summary_reports_unknown_rather_than_zero(self, tracker):
        """The fabricated zero this change removes must not reappear here."""
        tracker.record(_record(None))
        stats = tracker.get_usage_stats(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1),
        )
        assert stats["total"]["cost_usd"] != 0.0

    def test_recent_usage_renders_unknown_costs(self, tracker):
        tracker.record(_record(None))
        recent = tracker.get_recent_usage(limit=10)
        assert recent[0].cost_usd is None

    def test_formatters_say_unknown(self):
        assert format_currency(None) == "unknown"
        assert fmt_cost(None) == "unknown"
        assert format_currency(1.5) == "$1.50"
        assert fmt_cost(1.5) == "$1.50"


class TestKnowableZeroIsNotUnknown:
    """Self-hosted providers really are free. Zero is a fact there."""

    def test_self_hosted_providers_report_zero_not_none(self):
        from legesher_i18n.api.providers import libretranslate, openai_compat

        for module in (libretranslate, openai_compat):
            source = (module.__file__ or "").replace(".pyc", ".py")
            with open(source, encoding="utf-8") as fh:
                assert "cost_estimate_usd=0.0" in fh.read(), (
                    f"{module.__name__} should report a true zero, not unknown"
                )
