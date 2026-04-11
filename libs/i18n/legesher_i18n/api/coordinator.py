"""Translation coordinator with quality-based automatic fallback."""

import logging
import uuid
from datetime import datetime

from .cache import CacheBackend, SQLiteCache
from .providers.base import (
    TranslationError,
    TranslationProvider,
    TranslationResult,
)
from .quality_validator import QualityValidator
from .usage_tracker import UsageRecord, UsageTracker

logger = logging.getLogger(__name__)


class TranslationCoordinator:
    """
    Coordinates translation requests across multiple providers with automatic fallback.

    Features:
    - Multi-provider support with priority ordering
    - Automatic quality-based fallback
    - Local caching (SQLite/Redis)
    - Usage tracking and cost calculation
    - Batch translation support

    Usage:
        from legesher_i18n.api import TranslationCoordinator
        from legesher_i18n.api.providers import DeepLProvider, LibreTranslateProvider
        from legesher_i18n.api.cache import SQLiteCache
        from legesher_i18n.api.usage_tracker import UsageTracker

        coordinator = TranslationCoordinator(
            providers=[DeepLProvider(), LibreTranslateProvider()],
            cache=SQLiteCache(),
            usage_tracker=UsageTracker(),
        )

        result = await coordinator.translate("Hello", "en", "es")
        print(result.text)  # "Hola"
    """

    def __init__(
        self,
        providers: list[TranslationProvider] | None = None,
        cache: CacheBackend | None = None,
        usage_tracker: UsageTracker | None = None,
        quality_validator: QualityValidator | None = None,
        max_fallback_attempts: int = 3,
    ):
        """
        Initialize translation coordinator.

        Args:
            providers: List of translation providers in priority order
            cache: Cache backend (default: SQLiteCache)
            usage_tracker: Usage tracker (default: UsageTracker)
            quality_validator: Quality validator (default: QualityValidator)
            max_fallback_attempts: Maximum number of fallback attempts
        """
        self.providers = providers or []
        self.cache = cache or SQLiteCache()
        self.usage_tracker = usage_tracker or UsageTracker()
        self.quality_validator = quality_validator or QualityValidator()
        self.max_fallback_attempts = max_fallback_attempts

        # Validate providers are available
        self.available_providers = [p for p in self.providers if p.is_available()]
        if not self.available_providers:
            logger.warning(
                "No translation providers available. "
                "Configure API keys or start LibreTranslate server."
            )

        logger.info(
            f"Translation coordinator initialized with {len(self.available_providers)} providers: "
            f"{[p.name for p in self.available_providers]}"
        )

    def add_provider(self, provider: TranslationProvider, priority: int | None = None):
        """
        Add a translation provider.

        Args:
            provider: Translation provider to add
            priority: Insert position (None = append to end)
        """
        if not provider.is_available():
            logger.warning(
                f"Provider {provider.name} is not available. "
                "It will be skipped for translation requests."
            )
            return

        if priority is None:
            self.available_providers.append(provider)
        else:
            self.available_providers.insert(priority, provider)

        logger.info(
            f"Added provider {provider.name} at priority {priority or len(self.available_providers)}"
        )

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        skip_cache: bool = False,
        preferred_provider: str | None = None,
        max_length: int = 10000,
        context: dict | None = None,
    ) -> TranslationResult:
        """
        Translate text with automatic quality-based fallback.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')
            skip_cache: Skip cache lookup (default: False)
            preferred_provider: Try this provider first
            max_length: Maximum text length (default: 10000 characters)
            context: Optional context dict (glossary, kind, style guide)
                forwarded to providers that support it

        Returns:
            TranslationResult with translated text and metadata

        Raises:
            TranslationError: If all providers fail or input invalid
        """
        # Input validation
        if not text or not text.strip():
            raise TranslationError("Text cannot be empty or whitespace-only")

        if len(text) > max_length:
            raise TranslationError(
                f"Text length ({len(text)}) exceeds maximum ({max_length} characters)"
            )

        if not source_lang or not target_lang:
            raise TranslationError("Source and target language codes are required")

        if len(source_lang) > 10 or len(target_lang) > 10:
            raise TranslationError("Language codes must be 10 characters or less")

        if not self.available_providers:
            raise TranslationError(
                "No translation providers available. "
                "Configure API keys or start LibreTranslate server."
            )

        # Check cache first — skip cache when context is provided since the
        # PromptBuilder produces different prompts depending on context
        if not skip_cache and context is None:
            cached = self.cache.get(text, source_lang, target_lang)
            if cached:
                logger.info(f"Cache hit: {source_lang}->{target_lang}")
                # Return cached result with metadata
                return TranslationResult(
                    text=cached,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    provider="cache",
                    cached=True,
                    timestamp=datetime.now(),
                )

        # Generate request ID for tracking
        request_id = str(uuid.uuid4())

        # Order providers by preference
        ordered_providers = self._order_providers_by_preference(
            source_lang, target_lang, preferred_provider
        )

        # Try providers with automatic fallback
        errors = []
        for i, provider in enumerate(ordered_providers):
            if i >= self.max_fallback_attempts:
                logger.warning(
                    f"Reached max fallback attempts ({self.max_fallback_attempts})"
                )
                break

            if not provider.supports(source_lang, target_lang):
                logger.debug(
                    f"Provider {provider.name} does not support {source_lang}->{target_lang}"
                )
                continue

            try:
                logger.info(
                    f"Attempting translation with {provider.name} "
                    f"(attempt {i + 1}/{self.max_fallback_attempts})"
                )

                result = await provider.translate(
                    text, source_lang, target_lang, context=context
                )

                # Validate quality
                if self.quality_validator.validate(result, text):
                    logger.info(
                        f"Translation successful with {provider.name} "
                        f"(quality: {result.quality_score:.1f})"
                    )

                    # Cache result
                    self.cache.set(
                        text, source_lang, target_lang, result.text, provider.name
                    )

                    # Track usage
                    if self.usage_tracker and result.billed_characters:
                        cost = (
                            result.billed_characters / 1_000_000
                        ) * provider.cost_per_million_chars
                        self.usage_tracker.record(
                            UsageRecord(
                                timestamp=result.timestamp,
                                provider=provider.name,
                                source_lang=source_lang,
                                target_lang=target_lang,
                                characters=result.billed_characters,
                                cost_usd=cost,
                                request_id=request_id,
                                cached=False,
                            )
                        )

                    return result
                else:
                    logger.warning(
                        f"Translation quality insufficient from {provider.name}, "
                        "attempting fallback"
                    )
                    errors.append(
                        f"{provider.name}: Quality validation failed "
                        f"(quality: {result.quality_score})"
                    )

            except TranslationError as e:
                logger.error(f"Translation failed with {provider.name}: {e}")
                errors.append(f"{provider.name}: {e}")
                continue

        # All providers failed
        error_summary = "; ".join(errors)
        raise TranslationError(
            f"Translation failed after {len(errors)} attempts: {error_summary}"
        )

    async def translate_batch(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str,
        skip_cache: bool = False,
    ) -> list[TranslationResult]:
        """
        Translate multiple texts in batch.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            skip_cache: Skip cache lookup

        Returns:
            List of TranslationResults in same order as input
        """
        import asyncio

        # Translate all texts concurrently
        tasks = [
            self.translate(text, source_lang, target_lang, skip_cache) for text in texts
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch translation failed for text {i}: {result}")
                # Return error result
                final_results.append(
                    TranslationResult(
                        text="",
                        source_lang=source_lang,
                        target_lang=target_lang,
                        provider="error",
                        metadata={"error": str(result)},
                    )
                )
            else:
                final_results.append(result)

        return final_results

    def _order_providers_by_preference(
        self,
        source_lang: str,
        target_lang: str,
        preferred_provider: str | None = None,
    ) -> list[TranslationProvider]:
        """
        Order providers by preference based on quality scores.

        Args:
            source_lang: Source language code
            target_lang: Target language code
            preferred_provider: Try this provider first

        Returns:
            Ordered list of providers (best first)
        """
        # If preferred provider specified, try it first
        if preferred_provider:
            preferred = next(
                (p for p in self.available_providers if p.name == preferred_provider),
                None,
            )
            if preferred:
                other_providers = [
                    p for p in self.available_providers if p.name != preferred_provider
                ]
                return [preferred] + other_providers

        # Order by quality score for this language pair
        providers_with_scores = [
            (p, p.get_quality_score(source_lang, target_lang))
            for p in self.available_providers
        ]

        # Sort by quality score (descending)
        providers_with_scores.sort(key=lambda x: x[1], reverse=True)

        ordered = [p for p, score in providers_with_scores]
        logger.debug(
            f"Provider order for {source_lang}->{target_lang}: "
            f"{[(p.name, p.get_quality_score(source_lang, target_lang)) for p in ordered]}"
        )

        return ordered

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_stats()

    def get_usage_stats(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict:
        """
        Get usage statistics.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)

        Returns:
            Dict with usage statistics
        """
        if self.usage_tracker:
            return self.usage_tracker.get_usage_stats(start_date, end_date)
        return {}

    def clear_cache(self):
        """Clear all cached translations."""
        deleted = self.cache.clear()
        logger.info(f"Cleared {deleted} cached translations")
        return deleted

    async def get_provider_usage(self) -> dict[str, dict]:
        """
        Get usage statistics from all providers.

        Returns:
            Dict mapping provider name to usage stats
        """
        import asyncio

        usage_stats = {}
        tasks = []

        for provider in self.available_providers:
            tasks.append(provider.get_usage())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for provider, result in zip(self.available_providers, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to get usage for {provider.name}: {result}")
                usage_stats[provider.name] = {"error": str(result)}
            elif result:
                usage_stats[provider.name] = {
                    "total_requests": result.total_requests,
                    "total_characters": result.total_characters,
                    "cost_estimate_usd": result.cost_estimate_usd,
                }
            else:
                usage_stats[provider.name] = {"error": "No usage data available"}

        return usage_stats
