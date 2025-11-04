"""Cache backends for translation results."""

import hashlib
import json
import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Retrieve cached translation."""
        pass

    @abstractmethod
    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str,
        provider: str,
    ):
        """Cache translation."""
        pass

    @abstractmethod
    def clear(self):
        """Clear all cached translations."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Get cache statistics."""
        pass

    @staticmethod
    def _make_key(text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key from text and languages."""
        content = f"translation:{text}|{source_lang}|{target_lang}"
        return hashlib.sha256(content.encode()).hexdigest()


class SQLiteCache(CacheBackend):
    """
    SQLite-based cache backend with connection pooling.

    Default cache backend, requires no external services.
    Stores translations in a local SQLite database with TTL support.
    Uses a persistent connection for better performance in high-frequency operations.
    """

    def __init__(self, db_path: str = ".legesher/cache.db", ttl_seconds: int = 604800):
        """
        Initialize SQLite cache.

        Args:
            db_path: Path to SQLite database file
            ttl_seconds: Time-to-live for cached entries (default: 7 days)
        """
        self.db_path = db_path
        self.ttl = timedelta(seconds=ttl_seconds)

        # Ensure directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Connection pooling: maintain persistent connection per thread
        self._local = threading.local()

        self._init_db()

    def __del__(self):
        """Clean up connections on deletion."""
        self.close()

    def close(self):
        """
        Close all thread-local database connections.

        Important on Windows to prevent file locking issues.
        """
        if hasattr(self, "_local") and hasattr(self._local, "conn"):
            if self._local.conn is not None:
                try:
                    self._local.conn.close()
                    self._local.conn = None
                    logger.debug(
                        f"Closed SQLite connection for thread {threading.current_thread().name}"
                    )
                except Exception as e:
                    logger.warning(f"Error closing SQLite connection: {e}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection for the current thread.

        Uses thread-local storage to maintain one connection per thread,
        providing connection pooling for high-frequency operations.
        """
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=10.0
            )
            # Enable WAL mode for better concurrent access
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            logger.debug(
                f"Created new SQLite connection for thread {threading.current_thread().name}"
            )
        return self._local.conn

    def _init_db(self):
        """Initialize cache database."""
        conn = sqlite3.connect(self.db_path)

        # Create translations cache table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                translation TEXT NOT NULL,
                provider TEXT NOT NULL,
                cached_at TEXT NOT NULL
            )
        """)

        # Create index on cached_at for TTL cleanup
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cached_at ON cache(cached_at)
        """)

        conn.commit()
        conn.close()

        logger.debug(f"SQLite cache initialized at {self.db_path}")

    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Retrieve cached translation if not expired."""
        key = self._make_key(text, source_lang, target_lang)

        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT translation, cached_at FROM cache WHERE key = ?", (key,)
        )
        row = cursor.fetchone()

        if row:
            translation, cached_at_str = row
            cached_at = datetime.fromisoformat(cached_at_str)
            age = datetime.now() - cached_at

            if age < self.ttl:
                logger.debug(
                    f"Cache hit: {source_lang}->{target_lang} "
                    f"(age: {age.total_seconds():.0f}s)"
                )
                return translation
            else:
                # Expired, delete it
                logger.debug(f"Cache expired: {source_lang}->{target_lang}")
                self._delete(key)

        return None

    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str,
        provider: str,
    ):
        """Cache translation with current timestamp."""
        key = self._make_key(text, source_lang, target_lang)

        conn = self._get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO cache
            (key, text, source_lang, target_lang, translation, provider, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                key,
                text,
                source_lang,
                target_lang,
                translation,
                provider,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

        logger.debug(
            f"Cached translation: {source_lang}->{target_lang} (provider: {provider})"
        )

    def clear(self):
        """Clear all cached translations."""
        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM cache")
        deleted = cursor.rowcount
        conn.commit()

        logger.info(f"Cleared {deleted} cached translations")
        return deleted

    def get_stats(self) -> dict:
        """Get cache statistics."""
        conn = self._get_connection()

        # Total entries
        cursor = conn.execute("SELECT COUNT(*) FROM cache")
        total_entries = cursor.fetchone()[0]

        # Entries by provider
        cursor = conn.execute("""
            SELECT provider, COUNT(*) as count
            FROM cache
            GROUP BY provider
        """)
        by_provider = {row[0]: row[1] for row in cursor.fetchall()}

        # Database size
        cursor = conn.execute(
            "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
        )
        db_size_bytes = cursor.fetchone()[0]

        return {
            "backend": "sqlite",
            "total_entries": total_entries,
            "by_provider": by_provider,
            "db_size_bytes": db_size_bytes,
            "db_size_mb": round(db_size_bytes / 1024 / 1024, 2),
            "ttl_seconds": int(self.ttl.total_seconds()),
        }

    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        cutoff_time = datetime.now() - self.ttl

        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM cache WHERE cached_at < ?", (cutoff_time.isoformat(),)
        )
        deleted = cursor.rowcount
        conn.commit()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired cache entries")

        return deleted

    def _delete(self, key: str):
        """Delete a specific cache entry."""
        conn = self._get_connection()
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()


class RedisCache(CacheBackend):
    """
    Redis-based cache backend.

    Production-ready cache for multi-process and distributed scenarios.
    Requires Redis server running.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl_seconds: int = 604800,
    ):
        """
        Initialize Redis cache.

        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            ttl_seconds: Time-to-live for cached entries (default: 7 days)
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "redis package not installed. "
                "Install with: pip install 'legesher-i18n[api]'"
            )

        self.ttl_seconds = ttl_seconds

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
            )
            # Test connection
            self.client.ping()
            logger.info(f"Redis cache connected to {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {host}:{port}: {e}")
            raise

    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Retrieve cached translation from Redis."""
        key = self._make_key(text, source_lang, target_lang)

        try:
            value = self.client.get(key)
            if value:
                # Redis stores as JSON with metadata
                data = json.loads(value)
                logger.debug(
                    f"Cache hit (Redis): {source_lang}->{target_lang} "
                    f"(provider: {data.get('provider')})"
                )
                return data["translation"]
        except Exception as e:
            logger.error(f"Redis get error: {e}")

        return None

    def set(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str,
        provider: str,
    ):
        """Cache translation in Redis with TTL."""
        key = self._make_key(text, source_lang, target_lang)

        # Store with metadata as JSON
        value = json.dumps(
            {
                "translation": translation,
                "provider": provider,
                "cached_at": datetime.now().isoformat(),
            }
        )

        try:
            self.client.setex(key, self.ttl_seconds, value)
            logger.debug(
                f"Cached translation (Redis): {source_lang}->{target_lang} "
                f"(provider: {provider}, ttl: {self.ttl_seconds}s)"
            )
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def clear(self):
        """Clear all cached translations in Redis."""
        try:
            # Delete all keys matching our pattern
            pattern = "translation:*"
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Cleared {deleted} cached translations from Redis")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    def get_stats(self) -> dict:
        """Get Redis cache statistics."""
        try:
            info = self.client.info("stats")
            memory_info = self.client.info("memory")

            # Count our cache keys
            pattern = "translation:*"
            cache_keys = len(self.client.keys(pattern))

            return {
                "backend": "redis",
                "total_entries": cache_keys,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0)
                    / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                    * 100
                ),
                "memory_used_bytes": memory_info.get("used_memory", 0),
                "memory_used_mb": round(
                    memory_info.get("used_memory", 0) / 1024 / 1024, 2
                ),
                "ttl_seconds": self.ttl_seconds,
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"backend": "redis", "error": str(e)}
