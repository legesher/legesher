"""OpenAI-compatible translation provider for local and cloud models.

Targets the standard /v1/chat/completions API format, working with:
- vLLM (vllm serve model-name)
- Ollama (ollama run model-name)
- llama.cpp server
- LocalAI
- Any OpenAI-compatible API (OpenAI, Azure OpenAI, etc.)

Users serve any model and point this provider at the endpoint.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Optional

import httpx

from .base import (
    TranslationError,
    TranslationProvider,
    TranslationResult,
    UsageStats,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a precise translation engine for code-related content. "
    "Translate the given text from {source_lang} to {target_lang}. "
    "Return ONLY the translated text, nothing else. "
    "Do not add explanations, quotes, or formatting."
)


class OpenAICompatProvider(TranslationProvider):
    """OpenAI-compatible translation provider.

    Connects to any endpoint serving the OpenAI chat completions API.
    Designed for plug-and-play use with local models (Tiny Aya via vLLM,
    Ollama, etc.) or any OpenAI-compatible cloud API.

    Example:
        >>> # Local model via vLLM
        >>> provider = OpenAICompatProvider(
        ...     base_url="http://localhost:8000",
        ...     model="CohereForAI/aya-expanse-8b",
        ... )
        >>> result = await provider.translate("Hello", "en", "es")

        >>> # Ollama
        >>> provider = OpenAICompatProvider(
        ...     base_url="http://localhost:11434/v1",
        ...     model="aya",
        ... )
    """

    name = "openai_compat"
    requires_api_key = False
    cost_per_million_chars = 0.0  # Typically free for local models

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "default",
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = (
            base_url or os.getenv("OPENAI_BASE_URL", "http://localhost:8000")
        ).rstrip("/")
        self._model = model
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._timeout = timeout
        self._total_requests = 0
        self._total_tokens_in = 0
        self._total_tokens_out = 0

        # Try to initialize PromptBuilder for style-guide-aware prompts
        self._prompt_builder = None
        try:
            from legesher_i18n.style_guides import StyleGuideLoader
            from legesher_i18n.prompt_builder import PromptBuilder

            loader = StyleGuideLoader()
            self._prompt_builder = PromptBuilder(loader)
        except Exception as exc:
            logger.debug("PromptBuilder not available, using legacy prompts: %s", exc)

    def is_available(self) -> bool:
        # Can't easily check without making a request — assume available
        return True

    def supports(self, source_lang: str, target_lang: str) -> bool:
        # Depends on the model — assume yes
        return True

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[Dict] = None,
    ) -> TranslationResult:
        # Use PromptBuilder when available and context is provided
        if self._prompt_builder and context:
            glossary = context.get("glossary", {})
            kind = context.get("kind")

            if kind:  # text element (comment/docstring/string)
                system_prompt, user_prompt = self._prompt_builder.build_text_prompt(
                    texts=[{"text": text, "kind": kind, "context": context}],
                    target_lang=target_lang,
                    identifier_glossary=glossary,
                )
            else:  # identifier
                system_prompt, user_prompt = (
                    self._prompt_builder.build_identifier_prompt(
                        identifiers=[
                            {
                                "text": text,
                                "role": context.get("role", "unknown"),
                                "context": context,
                            }
                        ],
                        target_lang=target_lang,
                        existing_glossary=glossary,
                    )
                )
        else:
            # Legacy fallback
            system_prompt = _SYSTEM_PROMPT.format(
                source_lang=source_lang, target_lang=target_lang
            )
            user_prompt = text

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
        }

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # Handle base_url with or without /v1 suffix (e.g., Ollama uses /v1)
        base = self._base_url.rstrip("/")
        if base.endswith("/v1"):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
            except httpx.ConnectError as e:
                raise TranslationError(
                    f"Could not connect to {self._base_url}. "
                    "Is the model server running?"
                ) from e
            except httpx.HTTPStatusError as e:
                error_text = (e.response.text or "")[:200]
                logger.error(
                    "OpenAI-compat API error: %s %s",
                    e.response.status_code,
                    error_text,
                )
                raise TranslationError(
                    f"API error {e.response.status_code}: {error_text}"
                ) from e

        # Extract translated text with safe error handling
        try:
            raw_text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as e:
            raise TranslationError(
                f"Unexpected response shape from {self._base_url}: {e}"
            ) from e

        # When PromptBuilder was used, the LLM response is JSON — extract
        # the translation value(s) from it
        translated_text = self._parse_response(raw_text, text, context)

        # Track usage
        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        self._total_tokens_in += tokens_in
        self._total_tokens_out += tokens_out
        self._total_requests += 1

        billed_chars = (tokens_in + tokens_out) * 4

        return TranslationResult(
            text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            provider=self.name,
            confidence=0.8,
            billed_characters=billed_chars,
            quality_score=7.5,
            timestamp=datetime.now(),
            metadata={
                "model": self._model,
                "base_url": self._base_url,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            },
        )

    @staticmethod
    def _parse_response(
        raw_text: str,
        original_text: str,
        context: Optional[Dict],
    ) -> str:
        """Extract the translation from an LLM response.

        Delegates to the shared :func:`response_parser.parse_llm_response`.
        """
        from .response_parser import parse_llm_response

        return parse_llm_response(raw_text, original_text, context)

    async def get_usage(self) -> Optional[UsageStats]:
        if self._total_requests == 0:
            return None
        total_chars = (self._total_tokens_in + self._total_tokens_out) * 4
        return UsageStats(
            total_requests=self._total_requests,
            total_characters=total_chars,
            characters_by_provider={self.name: total_chars},
            cost_estimate_usd=0.0,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
