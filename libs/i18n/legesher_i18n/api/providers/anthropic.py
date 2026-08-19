"""Anthropic (Claude) translation provider with semantic analysis."""

import asyncio
import hashlib
import logging
import os
from typing import Any

try:
    from anthropic import AsyncAnthropic

    try:
        from anthropic import APIError as AnthropicAPIError
        from anthropic import RateLimitError as AnthropicRateLimitError
    except ImportError:  # pragma: no cover - very old SDK
        AnthropicAPIError = None  # type: ignore
        AnthropicRateLimitError = None  # type: ignore
except ImportError:
    AsyncAnthropic = None  # type: ignore
    AnthropicAPIError = None  # type: ignore
    AnthropicRateLimitError = None  # type: ignore

from legesher_i18n.language_names import language_name, supported_language_codes
from legesher_i18n.llm_json import parse_json_object
from legesher_i18n.model_config import anthropic_model

from ..rates import cost_for_tokens, format_cost
from .base import (
    TranslationProvider,
    TranslationResult,
    UsageStats,
    TranslationError,
    QuotaExceededError,
    AuthenticationError,
    UnsupportedLanguageError,
)
from .response_parser import parse_llm_response

logger = logging.getLogger(__name__)


class AnthropicProvider(TranslationProvider):
    """
    Anthropic (Claude) translation provider.

    Supports high-quality translations with semantic analysis and confidence scoring.
    Best for understanding context and nuanced translations.

    Usage:
        provider = AnthropicProvider(api_key="your-anthropic-key")
        result = await provider.translate("def", "en", "es", context={"explanation": "..."})

        # For semantic analysis
        analysis = await provider.analyze_semantic_similarity("def", ["definir", "función"], "es")
    """

    name = "anthropic"
    requires_api_key = True
    # Pricing is operator-configured via api/rates.py — never hardcoded here.

    # Supported languages: derived from languages.json (single source,
    # CORE-1804). Claude supports 100+ languages; this set is the shipped
    # Legesher language inventory plus English as the source language.
    # bg and uk are grandfathered: the pre-consolidation hardcoded set listed
    # them and Claude supports them, but they have no shipped pack yet, so
    # deriving from languages.json alone would silently drop working pairs.
    SUPPORTED_LANGUAGES = frozenset(supported_language_codes()) | {"en", "bg", "uk"}

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (if not provided, reads from ANTHROPIC_API_KEY env var)
            model: Claude model to use. Defaults to the configured model
                (``LEGESHER_ANTHROPIC_MODEL`` env var, else the packaged
                default in ``legesher_i18n.model_config``).
            max_tokens: Maximum tokens in response
        """
        if AsyncAnthropic is None:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable. "
                "Never commit API keys to version control. Use environment variables or secure secrets management."
            )

        self.model = model or anthropic_model()
        self.max_tokens = max_tokens
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

        # Initialize client if key available
        self.client: AsyncAnthropic | None = None
        if self.api_key:
            try:
                self.client = AsyncAnthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")

        # Cache for semantic analysis results (to avoid duplicate API calls)
        self._semantic_cache: dict[str, dict] = {}

        # Initialize PromptBuilder — the sole prompt source (CORE-1804).
        # Failure is loud: style guides are load-bearing (CORE-1354), so a
        # broken PromptBuilder must never quietly downgrade the prompts.
        self._prompt_builder = None
        try:
            from legesher_i18n.style_guides import StyleGuideLoader
            from legesher_i18n.prompt_builder import PromptBuilder

            loader = StyleGuideLoader()
            self._prompt_builder = PromptBuilder(loader)
        except Exception as exc:
            logger.warning(
                "PromptBuilder failed to initialize — falling back to the "
                "minimal plain-text prompt; style guides will NOT be applied "
                "and results are flagged prompt_source='legacy_fallback': %s",
                exc,
            )

    def is_available(self) -> bool:
        """Check if Anthropic is configured and ready."""
        if not self.client:
            return False

        if not self.api_key:
            logger.error("Anthropic API key not configured")
            return False

        # Basic validation - API key should start with "sk-ant-"
        if not self.api_key.startswith("sk-ant-"):
            logger.error("Anthropic API key format is invalid")
            return False

        return True

    def supports(self, source_lang: str, target_lang: str) -> bool:
        """Check if Anthropic supports this language pair."""
        # Normalize language codes
        source = source_lang.lower().split("-")[0]
        target = target_lang.lower().split("-")[0]

        # Claude supports all language pairs in our supported set
        return source in self.SUPPORTED_LANGUAGES and target in self.SUPPORTED_LANGUAGES

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: dict | None = None,
    ) -> TranslationResult:
        """
        Translate text using Claude API.

        Args:
            text: Text to translate (e.g., Python keyword "def")
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es')
            context: Optional deep context with etymology, explanation

        Returns:
            TranslationResult with translated text and metadata

        Raises:
            TranslationError: If translation fails
            QuotaExceededError: If API quota exceeded
            AuthenticationError: If API key is invalid
            UnsupportedLanguageError: If language pair not supported
        """
        if not self.client:
            raise AuthenticationError("Anthropic client not initialized (no API key)")

        if not self.supports(source_lang, target_lang):
            raise UnsupportedLanguageError(
                f"Anthropic does not support {source_lang}-{target_lang}"
            )

        # Build translation prompt — PromptBuilder is the sole prompt
        # source (CORE-1804). The minimal plain-text prompt remains only as
        # the loudly-flagged last resort when PromptBuilder failed to
        # initialize.
        prompt_builder = self._prompt_builder
        prompt_source = "prompt_builder"
        if prompt_builder is not None:
            if context and context.get("kind"):
                # text element (comment/docstring/string)
                system_prompt, user_prompt = prompt_builder.build_text_prompt(
                    texts=[{"text": text, "kind": context["kind"], "context": context}],
                    target_lang=target_lang,
                    identifier_glossary=context.get("glossary", {}),
                )
            elif context:
                # identifier
                system_prompt, user_prompt = prompt_builder.build_identifier_prompt(
                    identifiers=[
                        {
                            "text": text,
                            "role": context.get("role", "unknown"),
                            "context": context,
                        }
                    ],
                    target_lang=target_lang,
                    existing_glossary=context.get("glossary", {}),
                    forbidden_values=context.get("forbidden_values"),
                )
            else:
                # Context-free term translation with linguistic metadata —
                # the same prompt the generation pipeline uses.
                system_prompt, user_prompt = prompt_builder.build_term_prompt(
                    text, target_lang, role="term"
                )
        else:
            prompt_source = "legacy_fallback"
            logger.warning(
                "PromptBuilder unavailable — translating '%s' (%s->%s) with "
                "the minimal fallback prompt; style guides NOT applied",
                text,
                source_lang,
                target_lang,
            )
            from legesher_i18n.prompt_builder import PLAIN_TEXT_SYSTEM_PROMPT

            system_prompt = PLAIN_TEXT_SYSTEM_PROMPT.format(
                source_lang=source_lang, target_lang=target_lang
            )
            user_prompt = text

        try:
            raw_text, input_tokens, output_tokens = await self.complete(
                system_prompt, user_prompt
            )

            # Parse the response with the shared parser (CORE-1804).
            result_data: dict[str, Any] = {}
            if prompt_source == "prompt_builder":
                try:
                    parsed = parse_json_object(raw_text)
                    if isinstance(parsed, dict):
                        result_data = parsed
                except ValueError:
                    result_data = {}
                if "translation" in result_data:
                    translated_text = str(result_data["translation"])
                else:
                    translated_text = parse_llm_response(raw_text, text, context or {})
            else:
                translated_text = raw_text.strip()

            # Calculate billed characters (approximate from tokens)
            billed_chars = len(text)

            return TranslationResult(
                text=translated_text,
                source_lang=source_lang,
                target_lang=target_lang,
                provider=self.name,
                confidence=result_data.get("confidence", 0.9),
                billed_characters=billed_chars,
                quality_score=self.get_quality_score(source_lang, target_lang),
                metadata={
                    "word_type": result_data.get("word_type"),
                    "form": result_data.get("form"),
                    "alternatives": result_data.get("alternatives", []),
                    "rationale": result_data.get("rationale"),
                    "model": self.model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    # None unless the operator configured a rate — see api/rates.py
                    "cost_usd": cost_for_tokens(self.name, input_tokens, output_tokens),
                    # Provenance: which prompt surface produced this result
                    # (CORE-1804). "legacy_fallback" marks a style-guide
                    # regression.
                    "prompt_source": prompt_source,
                },
            )

        except Exception as e:
            error_str = str(e).lower()

            # Map Anthropic errors to our exception types with context
            if "authentication" in error_str or "api key" in error_str:
                raise AuthenticationError(
                    f"Anthropic auth failed for term '{text}' ({source_lang}->{target_lang}): {e}"
                )
            elif "quota" in error_str or "rate limit" in error_str:
                raise QuotaExceededError(
                    f"Anthropic quota/rate limit exceeded for term '{text}' ({source_lang}->{target_lang}): {e}"
                )
            else:
                raise TranslationError(
                    f"Anthropic translation failed for term '{text}' ({source_lang}->{target_lang}): {e}"
                )

    async def analyze_semantic_similarity(
        self,
        term: str,
        translations: list[str],
        language: str,
    ) -> dict:
        """
        Analyze if different translations are semantically equivalent.

        This is a custom method not in the base provider interface,
        used for comparing translations from different sources.

        Results are cached to avoid duplicate API calls for the same analysis.

        Args:
            term: Original Python term (e.g., "def")
            translations: List of different translations to compare
                         (e.g., ["definir", "función", "def"])
            language: Target language code (e.g., "es")

        Returns:
            {
                "similarity_scores": {"definir": 0.95, "función": 0.7, ...},
                "most_natural": "definir",
                "recommendation": "Use 'definir' - infinitive verb form...",
                "analysis": "Detailed linguistic analysis..."
            }

        Raises:
            TranslationError: If analysis fails
            AuthenticationError: If API key is invalid
        """
        if not self.client:
            raise AuthenticationError("Anthropic client not initialized (no API key)")

        # Check cache first
        cache_key = self._generate_cache_key(term, translations, language)
        if cache_key in self._semantic_cache:
            logger.debug(
                f"Using cached semantic analysis for term '{term}' in '{language}'"
            )
            return self._semantic_cache[cache_key]

        prompt = self._build_similarity_prompt(term, translations, language)

        try:
            raw_text, input_tokens, output_tokens = await self.complete(None, prompt)

            logger.info(
                f"Anthropic Semantic Analysis: {input_tokens} in / {output_tokens} out"
            )

            result = self._parse_json_response(raw_text)
            # None unless the operator configured a rate — see api/rates.py
            result["cost_usd"] = cost_for_tokens(self.name, input_tokens, output_tokens)
            result["model"] = self.model

            # Cache the result
            self._semantic_cache[cache_key] = result

            return result

        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str:
                raise AuthenticationError(
                    f"Anthropic auth failed for semantic analysis of term '{term}' in '{language}': {e}"
                )
            elif "quota" in error_str or "rate limit" in error_str:
                raise QuotaExceededError(
                    f"Anthropic quota/rate limit exceeded for semantic analysis of term '{term}' in '{language}': {e}"
                )
            else:
                raise TranslationError(
                    f"Semantic analysis failed for term '{term}' in '{language}' (comparing {len(translations)} translations): {e}"
                )

    async def get_usage(self) -> UsageStats | None:
        """
        Get Anthropic API usage stats.

        Note: Anthropic doesn't provide a usage API endpoint,
        so we track usage locally during the session.

        Returns:
            UsageStats with session usage information
        """
        if not self.client:
            return None

        total_chars = (
            self.total_input_tokens + self.total_output_tokens
        ) * 4  # ~4 chars/token
        from datetime import datetime

        return UsageStats(
            total_requests=self.total_requests,
            total_characters=total_chars,
            characters_by_provider={self.name: total_chars},
            cost_estimate_usd=cost_for_tokens(
                self.name, self.total_input_tokens, self.total_output_tokens
            ),
            period_start=datetime.now(),  # Session-based tracking
            period_end=datetime.now(),
        )

    def _generate_cache_key(
        self, term: str, translations: list[str], language: str
    ) -> str:
        """
        Generate cache key for semantic analysis.

        Args:
            term: Original term
            translations: List of translations to compare
            language: Target language code

        Returns:
            MD5 hash as cache key
        """
        # Sort translations to ensure consistent cache key regardless of order
        sorted_translations = sorted(translations)
        key_str = f"{term}:{language}:{':'.join(sorted_translations)}"
        # MD5 is used here for cache keying only, not for any security purpose.
        # usedforsecurity=False signals intent and silences bandit B324.
        return hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

    def clear_semantic_cache(self):
        """Clear the semantic analysis cache."""
        self._semantic_cache.clear()
        logger.info("Semantic analysis cache cleared")

    async def complete(
        self,
        system_prompt: str | None,
        user_prompt: str,
        *,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> tuple[str, int, int]:
        """Send one prompt pair through the single Anthropic call path.

        This is THE Anthropic client call site (CORE-1804): one client, one
        retry loop, one usage tracker. The generation-side ``ClaudeModel``
        delegates here instead of carrying its own client and retry loop.

        Args:
            system_prompt: Optional system prompt.
            user_prompt: User prompt content.
            max_retries: Maximum retry attempts (exponential backoff).
            initial_delay: Initial backoff delay in seconds.

        Returns:
            Tuple of ``(response_text, input_tokens, output_tokens)``.

        Raises:
            AuthenticationError: If the client is not initialized.
            Exception: Whatever the API raised after retries are exhausted.
        """
        if not self.client:
            raise AuthenticationError("Anthropic client not initialized (no API key)")
        client = self.client

        async def api_call():
            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": user_prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            return await client.messages.create(**kwargs)

        response = await self._call_api_with_retry(
            api_call, max_retries=max_retries, initial_delay=initial_delay
        )

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1

        logger.info(
            f"Anthropic: Tokens: {input_tokens} in / {output_tokens} out | "
            f"Cost: {format_cost(cost_for_tokens(self.name, input_tokens, output_tokens))} | "
            f"Total requests: {self.total_requests}"
        )

        return response.content[0].text, input_tokens, output_tokens

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Classify an exception as retryable (rate limit / transient)."""
        if AnthropicRateLimitError is not None and isinstance(
            exc, AnthropicRateLimitError
        ):
            return True
        error_str = str(exc).lower()
        return any(
            marker in error_str
            for marker in ("rate limit", "rate_limit", "overloaded", "529")
        )

    async def _call_api_with_retry(
        self,
        func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ):
        """
        Call API with exponential backoff retry logic.

        Args:
            func: Async function to call
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            backoff_factor: Multiplier for delay between retries

        Returns:
            Result from the API call

        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Don't retry authentication errors
                if "authentication" in error_str or "api key" in error_str:
                    raise

                # Retry on rate limits and transient errors
                if attempt < max_retries - 1:
                    if self._is_retryable(e):
                        logger.warning(
                            f"API call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        # For other errors, raise immediately
                        raise
                else:
                    # Last attempt failed
                    logger.error(f"API call failed after {max_retries} attempts: {e}")
                    raise

        # Should never reach here, but just in case
        raise (
            last_exception
            if last_exception
            else Exception("Unknown error in retry logic")
        )

    def _build_similarity_prompt(
        self, term: str, translations: list[str], language: str
    ) -> str:
        """Build prompt for semantic similarity analysis."""
        lang_name = language_name(language)

        translations_list = "\n".join(
            f"{i + 1}. {t}" for i, t in enumerate(translations)
        )

        prompt = f"""You are a linguistic expert analyzing translations of Python terms to {lang_name}.

ORIGINAL PYTHON TERM: "{term}"

PROPOSED {lang_name.upper()} TRANSLATIONS:
{translations_list}

TASK:
Analyze these translations and determine:
1. Are they semantically equivalent (same concept, different words)?
2. Which is most natural for native {lang_name} speakers?
3. Which best preserves the programming concept?
4. Rate each translation's quality (0.0-1.0)

OUTPUT FORMAT (JSON):
{{
  "similarity_scores": {{
    "translation1": 0.95,
    "translation2": 0.85,
    ...
  }},
  "most_natural": "the most natural translation",
  "recommendation": "Brief recommendation on which to use and why",
  "analysis": "Detailed linguistic analysis of differences"
}}

Respond ONLY with the JSON object, no additional text."""

        return prompt

    def _parse_json_response(self, content: str) -> dict:
        """Extract and parse a JSON object from Claude's response.

        Delegates to the shared parser (CORE-1804): fence-stripping,
        repair, and last-resort field extraction live in one place
        (``legesher_i18n.llm_json``).
        """
        data = parse_json_object(content)
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a JSON object in response, got {type(data).__name__}"
            )
        return data
