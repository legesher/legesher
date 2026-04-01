"""Translation API for Legesher i18n package."""

from .cache import CacheBackend, SQLiteCache, RedisCache
from .coordinator import TranslationCoordinator
from .dashboard import DashboardGenerator
from .providers import (
    TranslationProvider,
    TranslationResult,
    UsageStats,
    TranslationError,
    QuotaExceededError,
    AuthenticationError,
    UnsupportedLanguageError,
)
from .quality_validator import QualityValidator
from .usage_tracker import UsageRecord, UsageTracker

__all__ = [
    # Core coordinator
    "TranslationCoordinator",
    # Providers
    "TranslationProvider",
    "TranslationResult",
    "UsageStats",
    # Errors
    "TranslationError",
    "QuotaExceededError",
    "AuthenticationError",
    "UnsupportedLanguageError",
    # Cache
    "CacheBackend",
    "SQLiteCache",
    "RedisCache",
    # Quality validation
    "QualityValidator",
    # Usage tracking
    "UsageTracker",
    "UsageRecord",
    # Dashboard
    "DashboardGenerator",
    # Backend adapter
    "ProviderBackendAdapter",
]

from .backends import ProviderBackendAdapter
