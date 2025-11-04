"""Base provider interface for translation services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class TranslationResult:
    """Result of a translation operation."""

    text: str
    source_lang: str
    target_lang: str
    provider: str
    confidence: Optional[float] = None  # 0.0-1.0 if provider supports it
    billed_characters: Optional[int] = None
    quality_score: Optional[float] = None  # 0-10 expected quality
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Provider-specific data


@dataclass
class UsageStats:
    """Provider usage statistics."""

    total_requests: int
    total_characters: int
    characters_by_provider: Dict[str, int]
    cost_estimate_usd: float
    period_start: datetime
    period_end: datetime


class TranslationError(Exception):
    """Base exception for translation errors."""

    pass


class QuotaExceededError(TranslationError):
    """Raised when API quota is exceeded."""

    pass


class AuthenticationError(TranslationError):
    """Raised when API authentication fails."""

    pass


class UnsupportedLanguageError(TranslationError):
    """Raised when language pair is not supported."""

    pass


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""

    name: str
    requires_api_key: bool = False
    cost_per_million_chars: float = 0.0

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is configured and ready.

        Returns:
            bool: True if provider can be used, False otherwise
        """
        pass

    @abstractmethod
    def supports(self, source_lang: str, target_lang: str) -> bool:
        """
        Check if provider supports this language pair.

        Args:
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')

        Returns:
            bool: True if language pair is supported
        """
        pass

    @abstractmethod
    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        """
        Perform translation with quality metrics.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            TranslationResult with translated text and metadata

        Raises:
            TranslationError: If translation fails
            QuotaExceededError: If API quota exceeded
            AuthenticationError: If API authentication fails
            UnsupportedLanguageError: If language pair not supported
        """
        pass

    @abstractmethod
    async def get_usage(self) -> Optional[UsageStats]:
        """
        Get provider usage stats (if supported).

        Returns:
            UsageStats if provider supports usage tracking, None otherwise
        """
        pass

    def get_quality_score(self, source_lang: str, target_lang: str) -> float:
        """
        Return expected quality score (0-10) for this language pair.

        Args:
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            float: Quality score 0-10 (10 = highest quality)
        """
        from ..quality_scores import PROVIDER_QUALITY

        pair = f"{source_lang}-{target_lang}"
        return PROVIDER_QUALITY.get(self.name, {}).get(pair, 5.0)

    def calculate_cost(self, text: str) -> float:
        """
        Calculate cost for translating text.

        Args:
            text: Text to translate

        Returns:
            float: Estimated cost in USD
        """
        chars = len(text)
        return (chars / 1_000_000) * self.cost_per_million_chars
