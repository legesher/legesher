"""LibreTranslate provider for self-hosted translation."""

import logging
import os
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from .base import (
    TranslationProvider,
    TranslationResult,
    UsageStats,
    TranslationError,
    AuthenticationError,
    UnsupportedLanguageError,
)

logger = logging.getLogger(__name__)


class LibreTranslateProvider(TranslationProvider):
    """
    LibreTranslate provider for self-hosted, open-source translation.

    Best for privacy (self-hosted), no API costs, offline capability.
    Quality is lower than DeepL/Google but adequate for programming keywords.

    Usage:
        # Self-hosted instance
        provider = LibreTranslateProvider(host="http://localhost:5000")

        # Public instance (not recommended for production)
        provider = LibreTranslateProvider(host="https://libretranslate.com")

        result = await provider.translate("Hello", "en", "es")
    """

    name = "libretranslate"
    requires_api_key = False  # No API key for self-hosted

    # LibreTranslate supports 20+ languages
    SUPPORTED_LANGUAGES = {
        "en",
        "ar",
        "az",
        "zh",
        "cs",
        "da",
        "nl",
        "eo",
        "fi",
        "fr",
        "de",
        "el",
        "he",
        "hi",
        "hu",
        "id",
        "ga",
        "it",
        "ja",
        "ko",
        "fa",
        "pl",
        "pt",
        "ru",
        "sk",
        "es",
        "sv",
        "tr",
        "uk",
        "vi",
    }

    def __init__(
        self,
        host: str | None = None,
        api_key: str | None = None,
        timeout: float = 10.0,
    ):
        """
        Initialize LibreTranslate provider.

        Args:
            host: LibreTranslate server URL (default: http://localhost:5000)
            api_key: Optional API key if server requires authentication
            timeout: Request timeout in seconds
        """
        if httpx is None:
            raise ImportError(
                "httpx package not installed. "
                "Install with: pip install 'legesher-i18n[api]'"
            )

        self.host = host or os.getenv("LIBRETRANSLATE_HOST") or "http://localhost:5000"
        self.api_key = api_key or os.getenv("LIBRETRANSLATE_API_KEY")
        self.timeout = timeout

        self.total_characters = 0
        self.total_requests = 0

        # Remove trailing slash from host
        self.host = self.host.rstrip("/")

    def is_available(self) -> bool:
        """Check if LibreTranslate server is reachable."""
        try:
            # Test with a simple request to /languages endpoint
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.host}/languages")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LibreTranslate not available at {self.host}: {e}")
            return False

    def supports(self, source_lang: str, target_lang: str) -> bool:
        """Check if LibreTranslate supports this language pair."""
        # Normalize language codes
        source = source_lang.lower().split("-")[0]
        target = target_lang.lower().split("-")[0]

        return source in self.SUPPORTED_LANGUAGES and target in self.SUPPORTED_LANGUAGES

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: dict | None = None,
    ) -> TranslationResult:
        """
        Translate text using LibreTranslate API.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')

        Returns:
            TranslationResult with translated text and metadata

        Raises:
            TranslationError: If translation fails
            AuthenticationError: If API key is invalid
            UnsupportedLanguageError: If language pair not supported
        """
        if not self.supports(source_lang, target_lang):
            raise UnsupportedLanguageError(
                f"LibreTranslate does not support {source_lang}-{target_lang}"
            )

        # Normalize language codes
        source = source_lang.lower().split("-")[0]
        target = target_lang.lower().split("-")[0]

        # Prepare request
        payload = {
            "q": text,
            "source": source,
            "target": target,
            "format": "text",
        }

        if self.api_key:
            payload["api_key"] = self.api_key

        # Translate
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.host}/translate",
                    json=payload,
                )

                if response.status_code == 403:
                    raise AuthenticationError(
                        "LibreTranslate API key invalid or required"
                    )
                elif response.status_code == 400:
                    error_msg = response.json().get("error", "Bad request")
                    raise TranslationError(f"LibreTranslate error: {error_msg}")
                elif response.status_code != 200:
                    raise TranslationError(
                        f"LibreTranslate HTTP {response.status_code}: {response.text}"
                    )

                result = response.json()
                translated_text = result.get("translatedText", "")

                # Track usage
                billed_chars = len(text)
                self.total_characters += billed_chars
                self.total_requests += 1

                logger.info(
                    f"LibreTranslate: Translated {billed_chars} chars. "
                    f"Total: {self.total_characters} chars, {self.total_requests} requests"
                )

                return TranslationResult(
                    text=translated_text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    provider=self.name,
                    confidence=None,  # LibreTranslate doesn't provide confidence
                    billed_characters=billed_chars,
                    quality_score=self.get_quality_score(source_lang, target_lang),
                    metadata={
                        "host": self.host,
                    },
                )

        except httpx.TimeoutException:
            raise TranslationError(
                f"LibreTranslate timeout after {self.timeout}s at {self.host}"
            )
        except httpx.ConnectError:
            raise TranslationError(
                f"Cannot connect to LibreTranslate at {self.host}. "
                "Is the server running?"
            )
        except Exception as e:
            if isinstance(e, (TranslationError, AuthenticationError)):
                raise
            raise TranslationError(f"LibreTranslate failed: {e}")

    async def get_usage(self) -> UsageStats | None:
        """
        Get LibreTranslate usage stats.

        Note: LibreTranslate doesn't provide server-side usage tracking.
        This returns local tracking only.

        Returns:
            UsageStats with local tracking data
        """
        return UsageStats(
            total_requests=self.total_requests,
            total_characters=self.total_characters,
            cost_estimate_usd=0.0,  # Self-hosted: zero is a fact, not a guess
            characters_by_provider={self.name: self.total_characters},
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
