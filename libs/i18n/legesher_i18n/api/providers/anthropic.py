"""Anthropic (Claude) translation provider with semantic analysis."""

import asyncio
import hashlib
import json
import logging
import os
import re

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None  # type: ignore

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
    # Claude 3.5 Sonnet pricing: $3/1M input tokens, $15/1M output tokens
    # Average ~4 chars per token, so roughly $4.5/1M chars ((3+15)/2/4)
    cost_per_million_chars = 4.5

    # Supported languages (Claude supports 100+ languages)
    SUPPORTED_LANGUAGES = {
        "ar",  # Arabic
        "bg",  # Bulgarian
        "bn",  # Bengali
        "cs",  # Czech
        "da",  # Danish
        "de",  # German
        "el",  # Greek
        "en",  # English
        "es",  # Spanish
        "fa",  # Persian
        "fi",  # Finnish
        "fr",  # French
        "he",  # Hebrew
        "hi",  # Hindi
        "hu",  # Hungarian
        "id",  # Indonesian
        "it",  # Italian
        "ja",  # Japanese
        "ko",  # Korean
        "nl",  # Dutch
        "pl",  # Polish
        "pt",  # Portuguese
        "ro",  # Romanian
        "ru",  # Russian
        "sv",  # Swedish
        "th",  # Thai
        "tr",  # Turkish
        "uk",  # Ukrainian
        "vi",  # Vietnamese
        "zh",  # Chinese
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (if not provided, reads from ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: claude-3-5-sonnet-20241022)
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

        self.model = model
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

        # Cost tracking (per 1M tokens)
        self.input_cost_per_token = 3.0 / 1_000_000  # $3/1M input tokens
        self.output_cost_per_token = 15.0 / 1_000_000  # $15/1M output tokens

        # Cache for semantic analysis results (to avoid duplicate API calls)
        self._semantic_cache: dict[str, dict] = {}

        # Try to initialize PromptBuilder for enhanced prompts
        self._prompt_builder = None
        try:
            from legesher_i18n.style_guides import StyleGuideLoader
            from legesher_i18n.prompt_builder import PromptBuilder

            loader = StyleGuideLoader()
            self._prompt_builder = PromptBuilder(loader)
        except Exception as exc:
            logger.debug("PromptBuilder not available, using legacy prompts: %s", exc)

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

        # Build translation prompt, using PromptBuilder if available
        use_prompt_builder = self._prompt_builder and context
        if use_prompt_builder:
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
                        forbidden_values=context.get("forbidden_values"),
                    )
                )
        else:
            system_prompt = None
            user_prompt = self._build_translation_prompt(text, target_lang, context)

        # Call Claude API with retry logic
        async def api_call():
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": user_prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            return await self.client.messages.create(**kwargs)

        try:
            response = await self._call_api_with_retry(api_call)

            # Track usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_requests += 1

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            logger.info(
                f"Anthropic: Tokens: {input_tokens} in / {output_tokens} out | "
                f"Cost: ${cost:.4f} | Total requests: {self.total_requests}"
            )

            # Parse JSON response
            result_data = self._parse_json_response(response.content[0].text)

            # Calculate billed characters (approximate from tokens)
            billed_chars = len(text)

            return TranslationResult(
                text=result_data["translation"],
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
                    "cost_usd": cost,
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

        # Call API with retry logic
        async def api_call():
            return await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

        try:
            response = await self._call_api_with_retry(api_call)

            # Track usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_requests += 1

            cost = self._calculate_cost(input_tokens, output_tokens)

            logger.info(
                f"Anthropic Semantic Analysis: {input_tokens} in / {output_tokens} out | "
                f"Cost: ${cost:.4f}"
            )

            result = self._parse_json_response(response.content[0].text)
            result["cost_usd"] = cost
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
        cost = self._calculate_cost(self.total_input_tokens, self.total_output_tokens)

        from datetime import datetime

        return UsageStats(
            total_requests=self.total_requests,
            total_characters=total_chars,
            characters_by_provider={self.name: total_chars},
            cost_estimate_usd=cost,
            period_start=datetime.now(),  # Session-based tracking
            period_end=datetime.now(),
        )

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API usage."""
        input_cost = input_tokens * self.input_cost_per_token
        output_cost = output_tokens * self.output_cost_per_token
        return input_cost + output_cost

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
                    if "rate limit" in error_str or "overloaded" in error_str:
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

    def _build_translation_prompt(
        self, term: str, language: str, context: dict | None
    ) -> str:
        """Build prompt for translation task."""
        # Map language codes to full names
        lang_names = {
            "es": "Spanish",
            "ar": "Arabic",
            "fr": "French",
            "zh": "Chinese",
            "hi": "Hindi",
            "ru": "Russian",
            "pt": "Portuguese",
            "de": "German",
            "ja": "Japanese",
            "ko": "Korean",
            "it": "Italian",
            "nl": "Dutch",
            "pl": "Polish",
            "tr": "Turkish",
            "th": "Thai",
            "vi": "Vietnamese",
            "id": "Indonesian",
            "bn": "Bengali",
            "fa": "Persian",
            "he": "Hebrew",
        }
        lang_name = lang_names.get(language, language.upper())

        context_section = ""
        if context:
            context_parts = []
            if "explanation" in context:
                context_parts.append(f"Explanation: {context['explanation']}")
            if "etymology" in context:
                context_parts.append(f"Etymology: {context['etymology']}")
            if "usage" in context:
                context_parts.append(f"Usage: {context['usage']}")

            if context_parts:
                context_section = "\n\nADDITIONAL CONTEXT:\n" + "\n".join(context_parts)

        prompt = f"""You are translating Python programming terms to {lang_name}.

TERM TO TRANSLATE: "{term}"

TASK:
Translate "{term}" to {lang_name} following these guidelines:
1. Focus on the CONCEPT, not word-for-word translation
2. Consider what native {lang_name} speakers would naturally use
3. Preserve technical accuracy for programming context
4. Prefer appropriate word forms:
   - Action verbs (def, return, yield): Use infinitive form
   - State verbs (is, in): Use present tense
   - Nouns/objects: Use singular form
5. Keep it concise - typically a single word or short phrase{context_section}

OUTPUT FORMAT (JSON):
{{
  "translation": "the translated term",
  "word_type": "verb|noun|adjective|etc",
  "form": "infinitive|present|singular|etc",
  "confidence": 0.0-1.0,
  "alternatives": ["alternative1", "alternative2"],
  "rationale": "Brief explanation of why this translation was chosen"
}}

Respond ONLY with the JSON object, no additional text."""

        return prompt

    def _build_similarity_prompt(
        self, term: str, translations: list[str], language: str
    ) -> str:
        """Build prompt for semantic similarity analysis."""
        lang_names = {
            "es": "Spanish",
            "ar": "Arabic",
            "fr": "French",
            "zh": "Chinese",
            "hi": "Hindi",
            "ru": "Russian",
            "pt": "Portuguese",
            "de": "German",
            "ja": "Japanese",
        }
        lang_name = lang_names.get(language, language.upper())

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
        """
        Extract and parse JSON from Claude's response.

        Claude often wraps JSON in markdown code blocks, so we need to extract it.
        """
        # Try to find JSON in markdown code block first
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError(f"No JSON found in response: {content}")

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {json_str}") from e
