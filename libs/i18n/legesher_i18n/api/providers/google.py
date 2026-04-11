"""Google Cloud Translation provider with rate tracking."""

import asyncio
import logging
import os
from collections import deque
from datetime import datetime, timedelta

try:
    from google.cloud import translate_v2 as translate
    from google.api_core import exceptions as google_exceptions
except ImportError:
    translate = None  # type: ignore
    google_exceptions = None  # type: ignore

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


class GoogleTranslateProvider(TranslationProvider):
    """
    Google Cloud Translation provider.

    Best for broad language coverage (133+ languages) and Asian languages.
    Requires Google Cloud API key or credentials.

    Usage:
        # With API key
        provider = GoogleTranslateProvider(api_key="your-key")

        # With service account (GOOGLE_APPLICATION_CREDENTIALS env var)
        provider = GoogleTranslateProvider()

        result = await provider.translate("Hello", "en", "es")
    """

    name = "google"
    requires_api_key = True
    cost_per_million_chars = 20.0  # $20 per 1M chars (Google Translate API)

    # Google supports 133+ languages
    # Only listing common ones here, but supports many more
    COMMON_LANGUAGES = {
        "af",
        "sq",
        "am",
        "ar",
        "hy",
        "az",
        "eu",
        "be",
        "bn",
        "bs",
        "bg",
        "ca",
        "ceb",
        "ny",
        "zh",
        "zh-CN",
        "zh-TW",
        "co",
        "hr",
        "cs",
        "da",
        "nl",
        "en",
        "eo",
        "et",
        "tl",
        "fi",
        "fr",
        "fy",
        "gl",
        "ka",
        "de",
        "el",
        "gu",
        "ht",
        "ha",
        "haw",
        "iw",
        "he",
        "hi",
        "hmn",
        "hu",
        "is",
        "ig",
        "id",
        "ga",
        "it",
        "ja",
        "jw",
        "kn",
        "kk",
        "km",
        "ko",
        "ku",
        "ky",
        "lo",
        "la",
        "lv",
        "lt",
        "lb",
        "mk",
        "mg",
        "ms",
        "ml",
        "mt",
        "mi",
        "mr",
        "mn",
        "my",
        "ne",
        "no",
        "or",
        "ps",
        "fa",
        "pl",
        "pt",
        "pa",
        "ro",
        "ru",
        "sm",
        "gd",
        "sr",
        "st",
        "sn",
        "sd",
        "si",
        "sk",
        "sl",
        "so",
        "es",
        "su",
        "sw",
        "sv",
        "tg",
        "ta",
        "te",
        "th",
        "tr",
        "uk",
        "ur",
        "ug",
        "uz",
        "vi",
        "cy",
        "xh",
        "yi",
        "yo",
        "zu",
    }

    def __init__(
        self,
        api_key: str | None = None,
        project_id: str | None = None,
        max_requests_per_second: int = 10,
    ):
        """
        Initialize Google Translate provider.

        Args:
            api_key: Google Cloud API key (optional, can use service account)
            project_id: Google Cloud project ID (optional)
            max_requests_per_second: Rate limit for API requests
        """
        if translate is None:
            raise ImportError(
                "google-cloud-translate package not installed. "
                "Install with: pip install 'legesher-i18n[api]'"
            )

        self.api_key = api_key or os.getenv("GOOGLE_TRANSLATE_API_KEY")
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")

        self.max_rps = max_requests_per_second
        self.request_times: deque = deque()
        self.total_characters = 0
        self.total_requests = 0

        # Initialize client
        self.client: translate.Client | None = None
        try:
            if self.api_key:
                # Use API key authentication
                self.client = translate.Client(api_key=self.api_key)
            else:
                # Use service account authentication (GOOGLE_APPLICATION_CREDENTIALS)
                self.client = translate.Client()
        except Exception as e:
            logger.error(f"Failed to initialize Google Translate client: {e}")

    def is_available(self) -> bool:
        """Check if Google Translate is configured and ready."""
        if not self.client:
            return False

        try:
            # Test with a simple supported languages call
            self.client.get_languages()
            return True
        except Exception as e:
            logger.error(f"Google Translate not available: {e}")
            return False

    def supports(self, source_lang: str, target_lang: str) -> bool:
        """
        Check if Google Translate supports this language pair.

        Note: Google supports 133+ languages, so we accept most language codes.
        """
        # Normalize language codes
        source = source_lang.lower().split("-")[0]
        target = target_lang.lower().split("-")[0]

        # Google supports a huge number of languages
        # For common ones, check the list; otherwise assume supported
        return (source in self.COMMON_LANGUAGES or len(source) == 2) and (
            target in self.COMMON_LANGUAGES or len(target) == 2
        )

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: dict | None = None,
    ) -> TranslationResult:
        """
        Translate text using Google Cloud Translation API.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')

        Returns:
            TranslationResult with translated text and metadata

        Raises:
            TranslationError: If translation fails
            QuotaExceededError: If API quota exceeded
            AuthenticationError: If authentication fails
            UnsupportedLanguageError: If language pair not supported
        """
        if not self.client:
            raise AuthenticationError(
                "Google Translate client not initialized. "
                "Set GOOGLE_TRANSLATE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS"
            )

        if not self.supports(source_lang, target_lang):
            raise UnsupportedLanguageError(
                f"Google Translate does not support {source_lang}-{target_lang}"
            )

        # Rate limiting
        await self._enforce_rate_limit()

        # Normalize language codes
        source = source_lang.lower().split("-")[0]
        target = target_lang.lower().split("-")[0]

        # Translate
        try:
            result = await asyncio.to_thread(
                self.client.translate,
                text,
                target_language=target,
                source_language=source if source != "auto" else None,
            )

            # Track usage
            billed_chars = len(text)
            self.total_characters += billed_chars
            self.total_requests += 1

            logger.info(
                f"Google: Translated {billed_chars} chars. "
                f"Total: {self.total_characters} chars, {self.total_requests} requests"
            )

            # Google returns dict with keys: translatedText, detectedSourceLanguage, input
            translated_text = result.get("translatedText", "")
            detected_lang = result.get("detectedSourceLanguage")

            return TranslationResult(
                text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=self.name,
                confidence=None,  # Google doesn't provide confidence scores in v2
                billed_characters=billed_chars,
                quality_score=self.get_quality_score(source_lang, target_lang),
                metadata={
                    "detected_source_language": detected_lang,
                    "input": result.get("input"),
                },
            )

        except Exception as e:
            # Handle Google-specific exceptions
            if google_exceptions:
                if isinstance(e, google_exceptions.TooManyRequests):
                    raise QuotaExceededError(f"Google Translate quota exceeded: {e}")
                elif isinstance(
                    e,
                    (
                        google_exceptions.PermissionDenied,
                        google_exceptions.Unauthenticated,
                    ),
                ):
                    raise AuthenticationError(f"Google Translate auth failed: {e}")
                elif isinstance(e, google_exceptions.InvalidArgument):
                    raise UnsupportedLanguageError(
                        f"Google Translate invalid language: {e}"
                    )

            raise TranslationError(f"Google Translate failed: {e}")

    async def get_usage(self) -> UsageStats | None:
        """
        Get Google Translate usage stats.

        Note: Google Cloud doesn't provide usage stats directly through the SDK.
        You need to use Cloud Monitoring API separately.
        This returns tracked local usage only.

        Returns:
            UsageStats with local tracking data
        """
        return UsageStats(
            total_requests=self.total_requests,
            total_characters=self.total_characters,
            characters_by_provider={self.name: self.total_characters},
            cost_estimate_usd=(self.total_characters / 1_000_000)
            * self.cost_per_million_chars,
            period_start=datetime.now(),  # Local tracking only
            period_end=datetime.now(),
        )

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
