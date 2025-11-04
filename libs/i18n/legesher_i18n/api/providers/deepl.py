"""DeepL translation provider with rate tracking."""

import asyncio
import logging
import os
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

try:
    import deepl
except ImportError:
    deepl = None  # type: ignore

from .base import (
    TranslationProvider,
    TranslationResult,
    UsageStats,
    TranslationError,
    QuotaExceededError,
    AuthenticationError,
    UnsupportedLanguageError,
)

logger = logging.getLogger(__name__)


class DeepLProvider(TranslationProvider):
    """
    DeepL translation provider.

    Best for European languages (Spanish, French, German, etc.).
    Requires DeepL API key.

    Usage:
        provider = DeepLProvider(api_key="your-deepl-key")
        result = await provider.translate("Hello", "en", "es")
    """

    name = "deepl"
    requires_api_key = True
    cost_per_million_chars = 20.0  # $20 per 1M chars (DeepL API Pro)

    # Supported languages (as of DeepL API 2024)
    SUPPORTED_LANGUAGES = {
        "ar",  # Arabic
        "bg",  # Bulgarian
        "cs",  # Czech
        "da",  # Danish
        "de",  # German
        "el",  # Greek
        "en",  # English
        "es",  # Spanish
        "et",  # Estonian
        "fi",  # Finnish
        "fr",  # French
        "hu",  # Hungarian
        "id",  # Indonesian
        "it",  # Italian
        "ja",  # Japanese
        "ko",  # Korean
        "lt",  # Lithuanian
        "lv",  # Latvian
        "nb",  # Norwegian Bokmål
        "nl",  # Dutch
        "pl",  # Polish
        "pt",  # Portuguese
        "ro",  # Romanian
        "ru",  # Russian
        "sk",  # Slovak
        "sl",  # Slovenian
        "sv",  # Swedish
        "tr",  # Turkish
        "uk",  # Ukrainian
        "zh",  # Chinese
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_requests_per_second: int = 10,
    ):
        """
        Initialize DeepL provider.

        Args:
            api_key: DeepL API key (if not provided, reads from DEEPL_API_KEY env var)
            max_requests_per_second: Rate limit for API requests
        """
        if deepl is None:
            raise ImportError(
                "deepl package not installed. "
                "Install with: pip install 'legesher-i18n[api]'"
            )

        self.api_key = api_key or os.getenv("DEEPL_API_KEY")
        if not self.api_key:
            logger.warning(
                "DeepL API key not configured. Set DEEPL_API_KEY environment variable."
            )

        self.max_rps = max_requests_per_second
        self.request_times: deque = deque()
        self.total_characters = 0
        self.total_requests = 0

        # Initialize translator if key available
        self.translator: Optional[deepl.Translator] = None
        if self.api_key:
            try:
                self.translator = deepl.Translator(self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize DeepL translator: {e}")

    def is_available(self) -> bool:
        """Check if DeepL is configured and ready."""
        if not self.translator:
            return False

        # Validate API key format before making external call
        # DeepL keys are UUIDs with optional :fx suffix
        if not self._validate_api_key_format():
            logger.error("DeepL API key format is invalid")
            return False

        try:
            # Test with usage call
            self.translator.get_usage()
            return True
        except deepl.exceptions.AuthorizationException:
            logger.error("DeepL API key is invalid")
            return False
        except Exception as e:
            logger.error(f"DeepL not available: {e}")
            return False

    def _validate_api_key_format(self) -> bool:
        """
        Validate DeepL API key format before making external calls.

        DeepL API keys are UUIDs (with optional :fx suffix for free tier).
        Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx[:fx]
        """
        if not hasattr(self.translator, "auth_key"):
            return False

        key = self.translator.auth_key
        if not key or not isinstance(key, str):
            return False

        # Remove optional :fx suffix for free tier
        key = key.split(":")[0]

        # Check UUID format (8-4-4-4-12 hex digits)
        import re

        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        return bool(re.match(uuid_pattern, key.lower()))

    def supports(self, source_lang: str, target_lang: str) -> bool:
        """Check if DeepL supports this language pair."""
        # Normalize language codes
        source = source_lang.lower().split("-")[0]  # Handle en-US -> en
        target = target_lang.lower().split("-")[0]

        return source in self.SUPPORTED_LANGUAGES and target in self.SUPPORTED_LANGUAGES

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """
        Translate text using DeepL API.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')

        Returns:
            TranslationResult with translated text and metadata

        Raises:
            TranslationError: If translation fails
            QuotaExceededError: If API quota exceeded
            AuthenticationError: If API key is invalid
            UnsupportedLanguageError: If language pair not supported
        """
        if not self.translator:
            raise AuthenticationError("DeepL translator not initialized (no API key)")

        if not self.supports(source_lang, target_lang):
            raise UnsupportedLanguageError(
                f"DeepL does not support {source_lang}-{target_lang}"
            )

        # Rate limiting
        await self._enforce_rate_limit()

        # Normalize language codes for DeepL API
        source = source_lang.upper().split("-")[0]
        target = target_lang.upper().split("-")[0]

        # Translate
        try:
            result = await asyncio.to_thread(
                self.translator.translate_text,
                text,
                source_lang=source if source != "AUTO" else None,
                target_lang=target,
            )

            # Track usage
            billed_chars = len(text)
            self.total_characters += billed_chars
            self.total_requests += 1

            logger.info(
                f"DeepL: Translated {billed_chars} chars. "
                f"Total: {self.total_characters} chars, {self.total_requests} requests"
            )

            return TranslationResult(
                text=result.text,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=self.name,
                confidence=None,  # DeepL doesn't provide confidence scores
                billed_characters=billed_chars,
                quality_score=self.get_quality_score(source_lang, target_lang),
                metadata={
                    "detected_source_language": result.detected_source_lang,
                },
            )

        except deepl.exceptions.QuotaExceededException as e:
            raise QuotaExceededError(f"DeepL quota exceeded: {e}")
        except deepl.exceptions.AuthorizationException as e:
            raise AuthenticationError(f"DeepL auth failed: {e}")
        except deepl.exceptions.DeepLException as e:
            raise TranslationError(f"DeepL translation failed: {e}")
        except Exception as e:
            raise TranslationError(f"DeepL unexpected error: {e}")

    async def get_usage(self) -> Optional[UsageStats]:
        """
        Get DeepL API usage stats.

        Returns:
            UsageStats with quota information, or None if unavailable
        """
        if not self.translator:
            return None

        try:
            usage = await asyncio.to_thread(self.translator.get_usage)

            if usage.character is None:
                return None

            return UsageStats(
                total_requests=self.total_requests,
                total_characters=usage.character.count,
                characters_by_provider={self.name: usage.character.count},
                cost_estimate_usd=(usage.character.count / 1_000_000)
                * self.cost_per_million_chars,
                period_start=datetime.now(),  # DeepL doesn't provide period info
                period_end=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to get DeepL usage: {e}")
            return None

    async def _enforce_rate_limit(self):
        """Enforce max requests per second."""
        now = datetime.now()

        # Remove requests older than 1 second
        while self.request_times and self.request_times[0] < now - timedelta(seconds=1):
            self.request_times.popleft()

        # If at limit, wait
        if len(self.request_times) >= self.max_rps:
            sleep_time = (
                self.request_times[0] + timedelta(seconds=1) - now
            ).total_seconds()
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.3f}s")
                await asyncio.sleep(sleep_time)

        self.request_times.append(now)
