"""Cohere Aya API translation provider.

Uses the Cohere API to access Aya multilingual models for translation.
Supports Aya Expanse and other Cohere chat models.

Install: pip install cohere
"""

import logging
import os
from datetime import datetime

from .base import (
    AuthenticationError,
    TranslationError,
    TranslationProvider,
    TranslationResult,
    UsageStats,
)

logger = logging.getLogger(__name__)

# Translation system prompt — fallback path used only when PromptBuilder
# fails to initialize. Empirical CORE-950 finding: lower-resource targets
# (zh, ur) trigger trace-format pollution on weak prompts; the rule list
# below mirrors PromptBuilder's `_CRITICAL_RULES` no-explanation entry so
# both paths share the same failure-mode anchoring.
_SYSTEM_PROMPT = (
    "You are a precise translation engine for code-related content. "
    "Translate the given text from {source_lang} to {target_lang}. "
    "Return ONLY the translated text -- no prefix, no suffix, no "
    "explanation, no markup, no trace-format wrappers, and no "
    "surrounding commentary. Do NOT emit patterns like "
    "`__original_X_translation_Y_Explanation_...`, "
    "`____translated_identifier_X____`, or JSON-style metadata "
    "wrappers around the translation. Output the translation value alone."
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
        api_key: str | None = None,
        model: str = "c4ai-aya-expanse-32b",
    ) -> None:
        self._api_key = api_key or os.getenv("COHERE_API_KEY")
        self._model = model
        self._client = None
        self._total_tokens_in = 0
        self._total_tokens_out = 0
        self._total_requests = 0

        # Try to initialize PromptBuilder for style-guide-aware prompts
        self._prompt_builder = None
        try:
            from legesher_i18n.style_guides import StyleGuideLoader
            from legesher_i18n.prompt_builder import PromptBuilder

            loader = StyleGuideLoader()
            self._prompt_builder = PromptBuilder(loader)
        except Exception as exc:
            logger.debug("PromptBuilder not available, using legacy prompts: %s", exc)

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
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: dict | None = None,
    ) -> TranslationResult:
        client = self._get_client()

        # Use PromptBuilder when available and context is provided
        if self._prompt_builder and context:
            glossary = context.get("glossary", {})
            kind = context.get("kind")

            if kind:  # text element
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
                        forbidden_values=context.get("forbidden_values"),
                    )
                )
        else:
            system_prompt = _SYSTEM_PROMPT.format(
                source_lang=source_lang, target_lang=target_lang
            )
            user_prompt = text

        try:
            response = await client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            raw_text = response.message.content[0].text.strip()

            # Parse JSON response when PromptBuilder was used
            translated_text = self._parse_response(raw_text, text, context)

            # Track usage. Cohere V2 SDK 6.x exposes tokens at one of
            # several attribute paths depending on the build (CORE-950);
            # try them in priority order and fall back to legacy direct
            # attributes for older SDKs.
            tokens_in, tokens_out = self._read_token_counts(response.usage)
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

    @staticmethod
    def _parse_response(
        raw_text: str,
        original_text: str,
        context: dict | None,
    ) -> str:
        """Extract the translation from an LLM response."""
        from .response_parser import parse_llm_response

        return parse_llm_response(raw_text, original_text, context)

    @staticmethod
    def _read_token_counts(usage: object) -> tuple[int, int]:
        """Extract (tokens_in, tokens_out) from a Cohere V2 usage object.

        The Cohere V2 SDK 6.x exposes token counts at one of several
        attribute paths depending on the SDK build:

        * ``usage.tokens.input_tokens`` / ``.output_tokens`` (V2 6.1.x)
        * ``usage.billed_units.input_tokens`` / ``.output_tokens``
          (alternate V2 build, also seen in some versions)
        * ``usage.input_tokens`` / ``.output_tokens`` (legacy / V1)

        Tries each path in priority order; falls back to ``(0, 0)`` if
        none yield non-None values. Defensive against arbitrary mock
        objects in tests via ``isinstance(_, int)`` guards on the
        terminal attributes.
        """

        def _get_int(value: object) -> int | None:
            return value if isinstance(value, int) else None

        for nested_attr in ("tokens", "billed_units"):
            nested = getattr(usage, nested_attr, None)
            if nested is None:
                continue
            t_in = _get_int(getattr(nested, "input_tokens", None))
            t_out = _get_int(getattr(nested, "output_tokens", None))
            if t_in is not None or t_out is not None:
                return (t_in or 0, t_out or 0)

        # Legacy / V1 direct attributes.
        t_in = _get_int(getattr(usage, "input_tokens", None))
        t_out = _get_int(getattr(usage, "output_tokens", None))
        return (t_in or 0, t_out or 0)

    async def get_usage(self) -> UsageStats | None:
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
