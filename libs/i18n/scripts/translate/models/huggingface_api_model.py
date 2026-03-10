"""Generic HuggingFace Inference API model for cloud-based translation.

This module implements the TranslationModel interface using any HuggingFace
model via the Inference API. The model to use is determined by an
HFModelProfile — no subclassing needed.

Setup:
    pip install huggingface_hub
    export HF_TOKEN="hf_your_token_here"

Usage:
    python run_pipeline.py --models tiny-aya-api --tiny-aya-variant earth --languages am
    python run_pipeline.py --models hf-api --hf-profile tiny-aya-fire --languages ur

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
from .hf_profiles import HFModelProfile, default_prompt_builder
from .json_utils import parse_json_response

logger = logging.getLogger(__name__)

HF_TOKEN_ENV_VAR = "HF_TOKEN"


class HuggingFaceAPIModel(TranslationModel):
    """Generic HuggingFace translation model via Inference API.

    Works with any HuggingFace-hosted model specified via an HFModelProfile.
    No local model download required — translations happen in the cloud.

    Adding a new model requires only a profile definition in hf_profiles.py.
    """

    @staticmethod
    def check_dependencies() -> None:
        """Verify that huggingface_hub is installed.

        Raises:
            ImportError: If huggingface_hub is not available.
        """
        try:
            import huggingface_hub  # noqa: F401
        except ImportError:
            raise ImportError(
                "HuggingFace API model requires huggingface_hub. "
                "Install with: pip install huggingface_hub"
            )

    def __init__(
        self,
        profile: HFModelProfile,
        hf_token: Optional[str] = None,
        dry_run: bool = False,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """Initialize generic HuggingFace API model.

        Args:
            profile: Model profile with model ID and generation params
            hf_token: HF API token. If None, reads from HF_TOKEN env var.
            dry_run: If True, return mock translations without API calls
            rate_limit_delay: Seconds between requests to respect rate limits
            max_retries: Maximum retry attempts on failure
            retry_delay: Initial delay before first retry (exponential backoff)

        Raises:
            ValueError: If no HF token is provided and HF_TOKEN env var is not set
        """
        self.profile = profile
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if rate_limit_delay < 0:
            raise ValueError("rate_limit_delay must be non-negative")
        self.rate_limit_delay = rate_limit_delay

        # Resolve HF token from environment
        self._hf_token = hf_token or os.environ.get(HF_TOKEN_ENV_VAR)

        if not self.dry_run and not self._hf_token:
            raise ValueError(
                f"HuggingFace token required for API model '{profile.name}'. "
                f"Set {HF_TOKEN_ENV_VAR} environment variable or pass hf_token parameter. "
                "Get your token at: https://huggingface.co/settings/tokens"
            )

        # Lazy-load the InferenceClient
        self._client = None
        self._last_request_time = 0.0

        logger.info(
            f"Initialized HuggingFace API model: {profile.name} "
            f"({profile.model_id}, dry_run={dry_run}, "
            f"rate_limit_delay={rate_limit_delay}s)"
        )

    def _get_client(self):
        """Lazy-load the HuggingFace InferenceClient.

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
                    "huggingface_hub package required for HF Inference API. "
                    "Install with: pip install huggingface_hub"
                ) from e

            self._client = InferenceClient(
                model=self.profile.model_id,
                token=self._hf_token,
            )
            logger.debug(f"Created InferenceClient for model: {self.profile.model_id}")

        return self._client

    def get_model_name(self) -> str:
        """Get model name from profile."""
        return f"hf-api-{self.profile.name}"

    def estimate_cost(self, request: TranslationRequest) -> float:
        """HF Inference API — effectively free for our usage patterns."""
        return 0.0

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term using a HuggingFace model via Inference API.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If API call fails after all retries
        """
        if self.dry_run:
            return self._mock_translation(request)

        await self._wait_for_rate_limit()

        # Build prompt using custom or default builder
        builder = self.profile.prompt_builder or default_prompt_builder
        prompt = builder(request, self.profile)

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling HF API ({self.profile.name}) for '{request.term}' -> "
                    f"{request.target_language} (attempt {attempt + 1}/{self.max_retries})"
                )

                response_text = await asyncio.to_thread(
                    self._call_inference_api, prompt
                )

                result_data = parse_json_response(response_text)

                logger.info(
                    f"{self.profile.name} API translation: '{request.term}' -> "
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

                # Rate limit errors (429) — longer backoff
                if "429" in str(e) or "rate limit" in error_str:
                    delay = self.retry_delay * (2**attempt) * 2
                    logger.warning(
                        f"Rate limit hit for '{request.term}' (attempt {attempt + 1}). "
                        f"Waiting {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue

                # Server errors (5xx) — retryable
                if any(code in str(e) for code in ("500", "502", "503")):
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        logger.warning(
                            f"Server error for '{request.term}' (attempt {attempt + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue

                # JSON parsing errors — retryable
                if isinstance(e, ValueError):
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        logger.warning(
                            f"Response parsing failed for '{request.term}' "
                            f"(attempt {attempt + 1}): {e}. Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue

                # Non-retryable error
                logger.error(
                    f"HF API error for '{request.term}' ({self.profile.name}): {e}"
                )
                raise

        if last_exception:
            raise last_exception
        raise RuntimeError("Translation failed after all retries")

    def _call_inference_api(self, prompt: str) -> str:
        """Make the actual API call to HF Inference API.

        Uses text_generation() which works for both causal and seq2seq models
        on the HF Inference API.

        Args:
            prompt: The translation prompt

        Returns:
            Response text from the model
        """
        client = self._get_client()

        # Extract relevant generation params for the API call
        gen_params = self.profile.generation_params
        response = client.text_generation(
            prompt,
            max_new_tokens=gen_params.get("max_new_tokens", 512),
            temperature=gen_params.get("temperature", 0.3),
            top_p=gen_params.get("top_p", 0.95),
            do_sample=gen_params.get("do_sample", True),
        )

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

    def _mock_translation(self, request: TranslationRequest) -> Translation:
        """Generate mock translation for dry-run mode."""
        mock_translations = {
            "am": {
                "def": "ግለጽ",
                "return": "መልስ",
                "print": "አትም",
                "if": "ከሆነ",
            },
            "ur": {
                "def": "وضاحت",
                "return": "واپسی",
                "print": "چھاپو",
                "if": "اگر",
            },
            "ar": {
                "def": "تعريف",
                "return": "إرجاع",
                "print": "طباعة",
                "if": "إذا",
            },
            "es": {
                "def": "definir",
                "return": "retornar",
                "print": "imprimir",
                "if": "si",
            },
        }

        term_lower = request.term.lower()
        lang_translations = mock_translations.get(request.target_language, {})
        translation = lang_translations.get(
            term_lower, f"[MOCK_HF_API_{self.profile.name}_{term_lower}]"
        )

        return Translation(
            translation=translation,
            alternatives=[],
            rationale=f"Mock translation for dry-run mode ({self.profile.name} API)",
            word_type="verb",
            form="infinitive",
            model_name=self.get_model_name(),
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            confidence=0.85,
        )
