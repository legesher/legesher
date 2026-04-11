"""Usage tracking and cost calculation for translation APIs."""

import csv
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Single usage record for a translation request."""

    timestamp: datetime
    provider: str
    source_lang: str
    target_lang: str
    characters: int
    cost_usd: float
    request_id: str
    cached: bool


class UsageTracker:
    """
    Track translation API usage and calculate costs.

    Stores usage data in SQLite database for:
    - Cost tracking per provider
    - Usage analytics (language pairs, trends)
    - Cache effectiveness metrics
    - Export to CSV for analysis
    """

    def __init__(self, db_path: str = ".legesher/usage.db"):
        """
        Initialize usage tracker.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Initialize usage tracking database."""
        conn = sqlite3.connect(self.db_path)

        # Create usage table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
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

        # Create indices for common queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON usage(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_provider ON usage(provider)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_language_pair
            ON usage(source_lang, target_lang)
        """)

        conn.commit()
        conn.close()

        logger.debug(f"Usage tracker initialized at {self.db_path}")

    def record(self, record: UsageRecord):
        """
        Record a translation usage event.

        Args:
            record: Usage record to store
        """
        conn = sqlite3.connect(self.db_path)

        conn.execute(
            """
            INSERT INTO usage (timestamp, provider, source_lang, target_lang,
                             characters, cost_usd, request_id, cached)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.timestamp.isoformat(),
                record.provider,
                record.source_lang,
                record.target_lang,
                record.characters,
                record.cost_usd,
                record.request_id,
                record.cached,
            ),
        )

        conn.commit()
        conn.close()

        logger.debug(
            f"Recorded usage: {record.provider} "
            f"{record.source_lang}->{record.target_lang} "
            f"{record.characters} chars (${record.cost_usd:.4f})"
        )

    def record_batch(self, records: list[UsageRecord]):
        """
        Record multiple usage events in a single transaction for better performance.

        Args:
            records: List of usage records to store
        """
        if not records:
            return

        conn = sqlite3.connect(self.db_path)

        # Batch insert using executemany for better performance
        values = [
            (
                record.timestamp.isoformat(),
                record.provider,
                record.source_lang,
                record.target_lang,
                record.characters,
                record.cost_usd,
                record.request_id,
                record.cached,
            )
            for record in records
        ]

        conn.executemany(
            """
            INSERT INTO usage (timestamp, provider, source_lang, target_lang,
                             characters, cost_usd, request_id, cached)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            values,
        )

        conn.commit()
        conn.close()

        total_chars = sum(r.characters for r in records)
        total_cost = sum(r.cost_usd for r in records)
        logger.info(
            f"Recorded {len(records)} usage events in batch: "
            f"{total_chars} chars total (${total_cost:.4f})"
        )

    def get_usage_stats(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """
        Get usage statistics for a time period.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)

        Returns:
            Dict with usage statistics including:
            - total requests/characters/cost
            - breakdown by provider
            - top language pairs
            - cache hit rate
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total usage
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_requests,
                SUM(characters) as total_characters,
                SUM(cost_usd) as total_cost,
                SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cached_requests
            FROM usage
            WHERE timestamp BETWEEN ? AND ?
        """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        total_stats = cursor.fetchone()

        # Per-provider usage
        cursor.execute(
            """
            SELECT
                provider,
                COUNT(*) as requests,
                SUM(characters) as characters,
                SUM(cost_usd) as cost
            FROM usage
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY provider
            ORDER BY requests DESC
        """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        provider_stats = cursor.fetchall()

        # Per-language-pair usage
        cursor.execute(
            """
            SELECT
                source_lang || '-' || target_lang as language_pair,
                COUNT(*) as requests,
                SUM(characters) as characters
            FROM usage
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY source_lang, target_lang
            ORDER BY requests DESC
            LIMIT 10
        """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        language_pair_stats = cursor.fetchall()

        # Daily usage trend (last 7 days)
        cursor.execute(
            """
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as requests,
                SUM(characters) as characters,
                SUM(cost_usd) as cost
            FROM usage
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        """,
            ((datetime.now() - timedelta(days=7)).isoformat(),),
        )

        daily_stats = cursor.fetchall()

        conn.close()

        # Calculate cache hit rate
        total_requests = total_stats[0] or 0
        cached_requests = total_stats[3] or 0
        cache_hit_rate = (
            (cached_requests / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total": {
                "requests": total_requests,
                "characters": total_stats[1] or 0,
                "cost_usd": total_stats[2] or 0.0,
                "cached_requests": cached_requests,
                "cache_hit_rate": cache_hit_rate,
            },
            "by_provider": [
                {
                    "provider": row[0],
                    "requests": row[1],
                    "characters": row[2],
                    "cost_usd": row[3],
                }
                for row in provider_stats
            ],
            "top_language_pairs": [
                {"pair": row[0], "requests": row[1], "characters": row[2]}
                for row in language_pair_stats
            ],
            "daily_trend": [
                {
                    "date": row[0],
                    "requests": row[1],
                    "characters": row[2],
                    "cost_usd": row[3],
                }
                for row in daily_stats
            ],
        }

    def export_csv(
        self,
        filepath: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Export usage data to CSV.

        Args:
            filepath: Output CSV file path
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, provider, source_lang, target_lang,
                   characters, cost_usd, request_id, cached
            FROM usage
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """,
            (start_date.isoformat(), end_date.isoformat()),
        )

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Timestamp",
                    "Provider",
                    "Source Lang",
                    "Target Lang",
                    "Characters",
                    "Cost (USD)",
                    "Request ID",
                    "Cached",
                ]
            )
            writer.writerows(cursor.fetchall())

        conn.close()

        logger.info(f"Exported usage data to {filepath}")

    def get_recent_usage(self, limit: int = 100) -> list[UsageRecord]:
        """
        Get recent usage records.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of recent UsageRecord objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT timestamp, provider, source_lang, target_lang,
                   characters, cost_usd, request_id, cached
            FROM usage
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        records = []
        for row in cursor.fetchall():
            records.append(
                UsageRecord(
                    timestamp=datetime.fromisoformat(row[0]),
                    provider=row[1],
                    source_lang=row[2],
                    target_lang=row[3],
                    characters=row[4],
                    cost_usd=row[5],
                    request_id=row[6],
                    cached=bool(row[7]),
                )
            )

        conn.close()

        return records

    def clear_old_records(self, days: int = 90):
        """
        Delete usage records older than specified days.

        Args:
            days: Delete records older than this many days
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            DELETE FROM usage
            WHERE timestamp < ?
        """,
            (cutoff_date.isoformat(),),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Deleted {deleted} usage records older than {days} days")

        return deleted
