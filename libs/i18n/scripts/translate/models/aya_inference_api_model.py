"""Aya-101 model implementation via Hugging Face Inference API.

This module implements the TranslationModel interface using the Aya-101
multilingual model through Hugging Face's cloud-based Inference API.

Unlike the local Transformers implementation (aya101_hf_model.py), this
version requires no local GPU or significant RAM - just network connectivity
and a Hugging Face API token.

Setup:
    export HF_TOKEN="hf_your_token_here"

Usage:
    python run_pipeline.py --models aya-api --languages es ar fr

Cost:
    - HF Free tier: ~1000 requests/day ($0)
    - HF Pro ($9/mo): Higher rate limits
"""

import asyncio
import logging
import os
import time
from typing import Optional

from .base import Translation, TranslationModel, TranslationRequest
from .json_utils import parse_json_response

logger = logging.getLogger(__name__)

# Environment variable name for HF token (follows HF conventions)
HF_TOKEN_ENV_VAR = "HF_TOKEN"

# Default model - Aya-101 supports 101 languages
# Note: The correct repository is CohereLabs/aya-101 (not CohereForAI)
DEFAULT_MODEL = "CohereLabs/aya-101"


class AyaInferenceAPIModel(TranslationModel):
    """Aya-101 translation model via Hugging Face Inference API.

    This model uses the Aya-101 multilingual model through HF's serverless
    inference API. No local model download required - translations happen
    in the cloud.

    Requirements:
        - HF_TOKEN environment variable set with valid Hugging Face token
        - Network connectivity
        - huggingface_hub package installed

    Rate Limits:
        - Free tier: Limited requests/day
        - Pro tier: Higher limits
        - See https://huggingface.co/pricing for current rates

    Attributes:
        model: Hugging Face model identifier
        dry_run: If True, return mock translations without API calls
        rate_limit_delay: Seconds to wait between requests (respect rate limits)
        max_retries: Maximum retry attempts on transient failures
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        hf_token: Optional[str] = None,
        dry_run: bool = False,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """Initialize Aya Inference API model.

        Args:
            model: Hugging Face model identifier (default: CohereLabs/aya-101)
            hf_token: HF API token. If None, reads from HF_TOKEN env var.
            dry_run: If True, don't make real API calls (for testing)
            rate_limit_delay: Seconds between requests to respect rate limits
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Initial delay before first retry (exponential backoff)

        Raises:
            ValueError: If no HF token is provided and HF_TOKEN env var is not set
        """
        self.model = model
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Validate rate_limit_delay
        if rate_limit_delay < 0:
            raise ValueError("rate_limit_delay must be non-negative")
        self.rate_limit_delay = rate_limit_delay

        # Resolve HF token securely from environment
        self._hf_token = hf_token or os.environ.get(HF_TOKEN_ENV_VAR)

        if not self.dry_run and not self._hf_token:
            raise ValueError(
                f"Hugging Face token required. Set {HF_TOKEN_ENV_VAR} environment "
                "variable or pass hf_token parameter. "
                "Get your token at: https://huggingface.co/settings/tokens"
            )

        # Lazy-load the InferenceClient to avoid import errors if not installed
        self._client = None
        self._last_request_time = 0.0

        logger.info(
            f"Initialized Aya Inference API model: {model} "
            f"(dry_run={dry_run}, rate_limit_delay={rate_limit_delay}s)"
        )

    def _get_client(self):
        """Lazy-load the Hugging Face InferenceClient.

        Returns:
            InferenceClient instance

        Raises:
            ImportError: If huggingface_hub is not installed
        """
        if self._client is None:
            try:
                from huggingface_hub import InferenceClient
            except ImportError as e:
                raise ImportError(
                    "huggingface_hub package required for Inference API. "
                    "Install with: pip install huggingface_hub"
                ) from e

            self._client = InferenceClient(
                model=self.model,
                token=self._hf_token,
            )
            logger.debug(f"Created InferenceClient for model: {self.model}")

        return self._client

    def get_model_name(self) -> str:
        """Get model name for tracking."""
        return f"aya-api-{self.model.split('/')[-1]}"

    def estimate_cost(self, request: TranslationRequest) -> float:
        """Estimate cost for translation request.

        HF Inference API is free for basic usage (rate limited).
        Pro tier is $9/month flat rate.

        Args:
            request: Translation request

        Returns:
            0.0 (effectively free for our usage patterns)
        """
        return 0.0

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term using Aya-101 via HF Inference API.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If API call fails after all retries
        """
        if self.dry_run:
            return self._mock_translation(request)

        # Rate limiting - respect API limits
        await self._wait_for_rate_limit()

        prompt = self._build_prompt(request)

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling HF Inference API for '{request.term}' -> "
                    f"{request.target_language} (attempt {attempt + 1}/{self.max_retries})"
                )

                # Make API call in thread to not block event loop
                response_text = await asyncio.to_thread(
                    self._call_inference_api, prompt
                )

                # Parse JSON from response
                result_data = parse_json_response(response_text)

                logger.info(
                    f"Aya API translation: '{request.term}' -> "
                    f"'{result_data.get('translation')}' ({request.target_language})"
                )

                return Translation(
                    translation=result_data.get("translation", ""),
                    alternatives=result_data.get("alternatives", []),
                    rationale=result_data.get("rationale", ""),
                    word_type=result_data.get("word_type", ""),
                    form=result_data.get("form", ""),
                    model_name=self.get_model_name(),
                    cost=0.0,
                    input_tokens=0,
                    output_tokens=0,
                    confidence=result_data.get("confidence", 0.85),
                )

            except Exception as e:
                last_exception = e
                error_str = str(e).lower()

                # Check for rate limit errors (429)
                if "429" in str(e) or "rate limit" in error_str:
                    delay = (
                        self.retry_delay * (2**attempt) * 2
                    )  # Longer delay for rate limits
                    logger.warning(
                        f"Rate limit hit for '{request.term}' (attempt {attempt + 1}). "
                        f"Waiting {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue

                # Check for server errors (5xx) - retryable
                if "500" in str(e) or "502" in str(e) or "503" in str(e):
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        logger.warning(
                            f"Server error for '{request.term}' (attempt {attempt + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue

                # Check for JSON parsing errors - retryable
                if isinstance(e, ValueError) and "json" in error_str:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        logger.warning(
                            f"JSON parse error for '{request.term}' (attempt {attempt + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue

                # Non-retryable error
                logger.error(f"HF Inference API error for '{request.term}': {e}")
                raise

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError("Translation failed after all retries")

    def _call_inference_api(self, prompt: str) -> str:
        """Make the actual API call to HF Inference API.

        Args:
            prompt: The translation prompt

        Returns:
            Response text from the model
        """
        client = self._get_client()

        # Aya-101 is a seq2seq model, use text2text_generation
        # Note: The Inference API handles the model type automatically
        response = client.text_generation(
            prompt,
            max_new_tokens=512,
            temperature=0.3,  # Lower for more consistent translations
            do_sample=True,
        )

        # Record request time for rate limiting
        self._last_request_time = time.time()

        return response

    async def _wait_for_rate_limit(self):
        """Wait if needed to respect rate limits."""
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                wait_time = self.rate_limit_delay - elapsed
                logger.debug(f"Rate limit delay: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

    def _build_prompt(self, request: TranslationRequest) -> str:
        """Build translation prompt for Aya-101.

        Uses a structured prompt format optimized for programming term
        translation with strict output constraints.

        Args:
            request: Translation request

        Returns:
            Formatted prompt string
        """
        # Language code to full name mapping
        # Supports both ISO 639-1 (2-letter) and ISO 639-2 (3-letter) codes
        language_names = {
            "am": "Amharic",
            "amh": "Amharic",
            "ar": "Arabic",
            "bn": "Bengali",
            "ben": "Bengali",
            "bs": "Bosnian",
            "bos": "Bosnian",
            "ca": "Catalan",
            "cat": "Catalan",
            "cs": "Czech",
            "ces": "Czech",
            "cy": "Welsh",
            "cym": "Welsh",
            "da": "Danish",
            "de": "German",
            "el": "Greek",
            "en": "English",
            "es": "Spanish",
            "fa": "Persian",
            "fas": "Persian",
            "fi": "Finnish",
            "fr": "French",
            "ga": "Irish",
            "gle": "Irish",
            "gd": "Scottish Gaelic",
            "gla": "Scottish Gaelic",
            "gl": "Galician",
            "glg": "Galician",
            "gu": "Gujarati",
            "guj": "Gujarati",
            "he": "Hebrew",
            "hi": "Hindi",
            "hr": "Croatian",
            "hrv": "Croatian",
            "hu": "Hungarian",
            "id": "Indonesian",
            "it": "Italian",
            "ja": "Japanese",
            "kn": "Kannada",
            "kan": "Kannada",
            "ko": "Korean",
            "lv": "Latvian",
            "lav": "Latvian",
            "mk": "Macedonian",
            "mkd": "Macedonian",
            "ml": "Malayalam",
            "mal": "Malayalam",
            "mn": "Mongolian",
            "mon": "Mongolian",
            "ms": "Malay",
            "my": "Burmese",
            "mya": "Burmese",
            "nl": "Dutch",
            "no": "Norwegian",
            "pl": "Polish",
            "pt": "Portuguese",
            "ro": "Romanian",
            "ron": "Romanian",
            "ru": "Russian",
            "si": "Sinhala",
            "sin": "Sinhala",
            "sr": "Serbian",
            "srp": "Serbian",
            "su": "Sundanese",
            "sun": "Sundanese",
            "sv": "Swedish",
            "sw": "Swahili",
            "swa": "Swahili",
            "ta": "Tamil",
            "tam": "Tamil",
            "te": "Telugu",
            "tel": "Telugu",
            "th": "Thai",
            "tr": "Turkish",
            "ur": "Urdu",
            "urd": "Urdu",
            "uz": "Uzbek",
            "uzb": "Uzbek",
            "vi": "Vietnamese",
            "zh": "Chinese (Simplified)",
        }

        language_name = language_names.get(
            request.target_language, request.target_language.upper()
        )

        # Build structured prompt with critical constraints
        prompt = f"""You are translating Python programming keywords for multilingual coding.

TERM: "{request.term}"
TARGET LANGUAGE: {language_name}

CRITICAL CONSTRAINTS:
1. NO SPACES in the translation (must be valid Python identifier)
2. NO PUNCTUATION (no apostrophes, hyphens, periods)
3. NO NUMBERS at the start
4. PRESERVE accents and diacritics (é, ñ, ü are OK)
5. Use the grammatical form that fits best for code

TASK: Translate "{request.term}" to {language_name} for use as a Python keyword.

OUTPUT FORMAT (respond with ONLY valid JSON, no markdown):
{{
  "translation": "translated_term",
  "word_type": "verb|noun|adjective|other",
  "form": "infinitive|imperative|singular|plural",
  "confidence": 0.85,
  "alternatives": ["alt1", "alt2"],
  "rationale": "Brief explanation"
}}"""

        return prompt

    def _mock_translation(self, request: TranslationRequest) -> Translation:
        """Generate mock translation for dry-run mode.

        Args:
            request: Translation request

        Returns:
            Mock Translation object
        """
        mock_translations = {
            "es": {"def": "definir", "return": "retornar", "print": "imprimir"},
            "ar": {"def": "تعريف", "return": "إرجاع", "print": "طباعة"},
            "fr": {"def": "definir", "return": "retourner", "print": "afficher"},
            "de": {"def": "definieren", "return": "zurückgeben", "print": "drucken"},
            "zh": {"def": "定义", "return": "返回", "print": "打印"},
            "bn": {"def": "সংজ্ঞায়িত", "return": "ফেরত", "print": "মুদ্রণ"},
            "ben": {"def": "সংজ্ঞায়িত", "return": "ফেরত", "print": "মুদ্রণ"},
        }

        term_lower = request.term.lower()
        lang_translations = mock_translations.get(request.target_language, {})
        translation = lang_translations.get(term_lower, f"[MOCK_AYA_API_{term_lower}]")

        return Translation(
            translation=translation,
            alternatives=[],
            rationale="Mock translation for dry-run mode (Aya Inference API)",
            word_type="verb",
            form="infinitive",
            model_name=self.get_model_name(),
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            confidence=0.85,
        )
