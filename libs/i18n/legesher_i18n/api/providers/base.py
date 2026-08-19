"""Base provider interface for translation services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TranslationResult:
    """Result of a translation operation."""

    text: str
    source_lang: str
    target_lang: str
    provider: str
    confidence: float | None = None  # 0.0-1.0 if provider supports it
    billed_characters: int | None = None
    quality_score: float | None = None  # 0-10 expected quality
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)  # Provider-specific data


@dataclass
class UsageStats:
    """Provider usage statistics."""

    total_requests: int
    total_characters: int
    characters_by_provider: dict[str, int]
    period_start: datetime
    period_end: datetime
    # None means "no rate configured", never "free". See api/rates.py.
    cost_estimate_usd: float | None = None


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
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: dict | None = None,
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

    async def translate_batch_with_context(
        self,
        items: list[dict[str, Any]],
        source_lang: str,
        target_lang: str,
    ) -> list["TranslationResult"]:
        """Translate a batch of context-carrying items.

        Each item is ``{"text": str, "context": dict | None}``. The default
        implementation issues one ``translate()`` call per item — correct,
        but O(items). Providers with a batched prompt path (CORE-1805)
        override this to issue O(1) API calls per batch;
        ``PromptBuilder.build_identifier_prompt`` / ``build_text_prompt``
        were designed for lists, and this is the method that uses that
        capacity.

        Args:
            items: Items to translate, in order.
            source_lang: Source language code.
            target_lang: Target language code.

        Returns:
            ``TranslationResult`` list aligned with *items*.

        Raises:
            TranslationError: If translation fails.
        """
        results: list[TranslationResult] = []
        for item in items:
            results.append(
                await self.translate(
                    item["text"],
                    source_lang,
                    target_lang,
                    context=item.get("context"),
                )
            )
        return results

    @abstractmethod
    async def get_usage(self) -> UsageStats | None:
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
