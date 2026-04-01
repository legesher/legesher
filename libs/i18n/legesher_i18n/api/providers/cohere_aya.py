"""Cohere Aya API translation provider.

Uses the Cohere API to access Aya multilingual models for translation.
Supports Aya Expanse and other Cohere chat models.

Install: pip install cohere
"""

import logging
import os
from datetime import datetime
from typing import Optional

from .base import (
    AuthenticationError,
    TranslationError,
    TranslationProvider,
    TranslationResult,
    UsageStats,
)

logger = logging.getLogger(__name__)

# Translation system prompt
_SYSTEM_PROMPT = (
    "You are a precise translation engine for code-related content. "
    "Translate the given text from {source_lang} to {target_lang}. "
    "Return ONLY the translated text, nothing else. "
    "Do not add explanations, quotes, or formatting."
)


class CohereAyaProvider(TranslationProvider):
    """Cohere Aya API translation provider.

    Uses Cohere's hosted Aya models for high-quality multilingual translation.
    Requires a Cohere API key (set via COHERE_API_KEY environment variable
    or passed directly).

    Example:
        >>> provider = CohereAyaProvider(api_key="your-key")
        >>> result = await provider.translate("Hello", "en", "es")
        >>> print(result.text)
        Hola
    """

    name = "cohere_aya"
    requires_api_key = True
    cost_per_million_chars = 0.50  # Aya models are relatively cheap

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "c4ai-aya-expanse-32b",
    ) -> None:
        self._api_key = api_key or os.getenv("COHERE_API_KEY")
        self._model = model
        self._client = None
        self._total_tokens_in = 0
        self._total_tokens_out = 0
        self._total_requests = 0

    def _get_client(self):
        if self._client is None:
            try:
                import cohere
            except ImportError:
                raise ImportError(
                    "cohere package required. Install with: pip install cohere"
                )
            if not self._api_key:
                raise AuthenticationError("Cohere API key required")
            self._client = cohere.AsyncClientV2(api_key=self._api_key)
        return self._client

    def is_available(self) -> bool:
        try:
            import cohere  # noqa: F401

            return bool(self._api_key)
        except ImportError:
            return False

    def supports(self, source_lang: str, target_lang: str) -> bool:
        # Aya supports 100+ languages
        return True

    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        client = self._get_client()

        system_prompt = _SYSTEM_PROMPT.format(
            source_lang=source_lang, target_lang=target_lang
        )

        try:
            response = await client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
            )

            translated_text = response.message.content[0].text.strip()

            # Track usage
            tokens_in = getattr(response.usage, "input_tokens", 0) or 0
            tokens_out = getattr(response.usage, "output_tokens", 0) or 0
            self._total_tokens_in += tokens_in
            self._total_tokens_out += tokens_out
            self._total_requests += 1

            # Estimate billed characters (rough: 4 chars per token)
            billed_chars = (tokens_in + tokens_out) * 4

            return TranslationResult(
                text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=self.name,
                confidence=0.85,
                billed_characters=billed_chars,
                quality_score=8.5,
                timestamp=datetime.now(),
                metadata={
                    "model": self._model,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                },
            )
        except (AuthenticationError, TranslationError):
            raise
        except Exception as e:
            logger.error("Cohere Aya translation failed: %s", e)
            raise TranslationError(f"Cohere Aya translation failed: {e}") from e

    async def get_usage(self) -> Optional[UsageStats]:
        if self._total_requests == 0:
            return None
        total_chars = (self._total_tokens_in + self._total_tokens_out) * 4
        return UsageStats(
            total_requests=self._total_requests,
            total_characters=total_chars,
            characters_by_provider={self.name: total_chars},
            cost_estimate_usd=total_chars / 1_000_000 * self.cost_per_million_chars,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
