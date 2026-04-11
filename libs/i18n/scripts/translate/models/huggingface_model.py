"""Generic HuggingFace model for local inference.

This module implements the TranslationModel interface using any HuggingFace
model loaded via the transformers library. The model to use is determined by
an HFModelProfile — no subclassing needed.

Setup:
    pip install transformers torch accelerate sentencepiece
    # Or with UV:
    uv pip install "legesher-i18n[ml]"

Usage:
    python run_pipeline.py --models tiny-aya --tiny-aya-variant earth --languages am
    python run_pipeline.py --models hf --hf-profile tiny-aya-fire --languages ur
"""

import asyncio
import logging

from .base import Translation, TranslationModel, TranslationRequest
from .hf_profiles import HFModelProfile, default_prompt_builder
from .json_utils import parse_json_response

logger = logging.getLogger(__name__)


class HuggingFaceModel(TranslationModel):
    """Generic HuggingFace translation model for local inference.

    Works with any HuggingFace model specified via an HFModelProfile.
    Supports causal LM and seq2seq architectures, with automatic device
    detection, lazy model loading, and retry logic.

    Adding a new model requires only a profile definition in hf_profiles.py.
    """

    @staticmethod
    def check_dependencies() -> None:
        """Verify that transformers and torch are installed.

        Raises:
            ImportError: If transformers or torch are not available.
        """
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError:
            raise ImportError(
                "HuggingFace model requires transformers and torch. "
                "Install with: uv pip install 'legesher-i18n[ml]'"
            )

    def __init__(
        self,
        profile: HFModelProfile,
        device: str | None = None,
        dry_run: bool = False,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        cache_dir: str | None = None,
    ):
        """Initialize generic HuggingFace model.

        Args:
            profile: Model profile with model ID, architecture, generation params
            device: Device to run on ('cpu', 'cuda', 'mps', or None for auto-detect)
            dry_run: If True, return mock translations without loading model
            max_retries: Maximum retry attempts on failure
            retry_delay: Initial delay in seconds before first retry (exponential backoff)
            cache_dir: Directory to cache model weights (default: ~/.cache/huggingface)
        """
        self.profile = profile
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_dir = cache_dir

        # Model and tokenizer (lazy loaded)
        self._model = None
        self._tokenizer = None
        self._device = device
        self._torch = None

        if not self.dry_run:
            try:
                import torch
                import transformers  # noqa: F401 — verify installed early

                self._torch = torch

                # Auto-detect device if not specified
                if self._device is None:
                    if torch.cuda.is_available():
                        self._device = "cuda"
                        logger.info("CUDA detected, using GPU for inference")
                    elif (
                        hasattr(torch.backends, "mps")
                        and torch.backends.mps.is_available()
                    ):
                        self._device = "mps"
                        logger.info("Apple Silicon detected, using MPS for inference")
                    else:
                        self._device = "cpu"
                        logger.info("No GPU detected, using CPU for inference")

                logger.info(
                    f"Initialized HuggingFace model: {profile.name} "
                    f"({profile.model_id}, device={self._device}, dry_run={dry_run})"
                )

            except ImportError as e:
                raise ImportError(
                    f"HuggingFace model '{profile.name}' requires transformers "
                    "and torch. Install with: uv pip install 'legesher-i18n[ml]'"
                ) from e

    def _load_model(self):
        """Lazy load model and tokenizer based on profile architecture."""
        if self._model is not None or self.dry_run:
            return

        from transformers import AutoTokenizer

        logger.info(f"Loading model from {self.profile.model_id}...")

        # Select model class based on architecture
        if self.profile.architecture == "seq2seq":
            from transformers import AutoModelForSeq2SeqLM

            model_class = AutoModelForSeq2SeqLM
        else:
            from transformers import AutoModelForCausalLM

            model_class = AutoModelForCausalLM

        # Load tokenizer (try cache first, then download)
        for attempt in range(2):
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.profile.model_id,
                    cache_dir=self.cache_dir,
                    local_files_only=(attempt == 0),
                    trust_remote_code=False,
                )
                break
            except Exception:
                if attempt == 0:
                    logger.info("Tokenizer not in cache, downloading...")
                    continue
                raise

        # Determine dtype
        dtype_map = {
            "bfloat16": self._torch.bfloat16,
            "float16": self._torch.float16,
            "float32": self._torch.float32,
        }

        if self.profile.dtype == "auto" or self._device == "cpu":
            torch_dtype = self._torch.float32
        else:
            torch_dtype = dtype_map.get(self.profile.dtype, self._torch.float32)

        # Load model
        logger.info("Loading model weights (this may take a few minutes)...")
        for attempt in range(2):
            try:
                self._model = model_class.from_pretrained(
                    self.profile.model_id,
                    cache_dir=self.cache_dir,
                    torch_dtype=torch_dtype,
                    low_cpu_mem_usage=True,
                    local_files_only=(attempt == 0),
                    trust_remote_code=False,
                ).to(self._device)
                logger.info(f"Model loaded successfully on {self._device}")
                break
            except Exception:
                if attempt == 0:
                    logger.info("Model not fully cached, downloading...")
                    continue
                raise

    def get_model_name(self) -> str:
        """Get model name from profile."""
        return self.profile.name

    def estimate_cost(self, request: TranslationRequest) -> float:
        """Local model — always free."""
        return 0.0

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term using the configured HuggingFace model.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If translation fails after all retries
        """
        if self.dry_run:
            return self._mock_translation(request)

        self._load_model()

        # Build prompt using custom or default builder
        builder = self.profile.prompt_builder or default_prompt_builder
        prompt = builder(request, self.profile)

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling {self.profile.name} for term '{request.term}' -> "
                    f"{request.target_language} (attempt {attempt + 1}/{self.max_retries})"
                )

                response_text = await asyncio.to_thread(self._generate, prompt)
                result_data = parse_json_response(response_text)

                logger.info(
                    f"{self.profile.name} translation: '{request.term}' -> "
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

            except (RuntimeError, OSError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"{self.profile.name} error for '{request.term}' "
                        f"(attempt {attempt + 1}): {e}. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{self.profile.name} error for '{request.term}' "
                        f"after {self.max_retries} attempts: {e}"
                    )
                    raise

            except ValueError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"{self.profile.name} response parsing failed for "
                        f"'{request.term}' (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{self.profile.name} response parsing failed for "
                        f"'{request.term}' after {self.max_retries} attempts: {e}"
                    )
                    raise

            except Exception as e:
                logger.error(f"{self.profile.name} error for '{request.term}': {e}")
                raise

        if last_exception:
            raise last_exception
        raise Exception("Translation failed after all retries")

    def _generate(self, prompt: str) -> str:
        """Generate response from model (blocking, call in thread).

        Handles both chat template and raw text tokenization based on
        the profile configuration.

        Args:
            prompt: Input prompt

        Returns:
            Generated text (decoded)
        """
        if self.profile.use_chat_template:
            messages = [{"role": "user", "content": prompt}]
            input_ids = self._tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
            ).to(self._device)

            with self._torch.no_grad():
                outputs = self._model.generate(
                    input_ids,
                    **self.profile.generation_params,
                )

            # Decode only the new tokens (skip input)
            new_tokens = outputs[0][input_ids.shape[-1] :]
            response_text = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        else:
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)

            with self._torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    **self.profile.generation_params,
                )

            # For causal LMs, generate() returns input + generated tokens; strip input.
            # For encoder-decoder (seq2seq), outputs[0] already contains only generated tokens.
            is_encoder_decoder = getattr(
                self._model.config, "is_encoder_decoder", False
            )
            if is_encoder_decoder:
                response_ids = outputs[0]
            else:
                input_length = inputs["input_ids"].shape[-1]
                response_ids = outputs[0][input_length:]

            response_text = self._tokenizer.decode(
                response_ids, skip_special_tokens=True
            )

        return response_text

    def _mock_translation(self, request: TranslationRequest) -> Translation:
        """Generate mock translation for dry-run mode."""
        mock_translations = {
            "am": {
                "def": "ግለጽ",
                "return": "መልስ",
                "print": "አትም",
                "if": "ከሆነ",
                "for": "ለእያንዳንዱ",
                "while": "እስከ",
                "class": "ክፍል",
            },
            "ur": {
                "def": "وضاحت",
                "return": "واپسی",
                "print": "چھاپو",
                "if": "اگر",
                "for": "ہرایک",
                "while": "جبتک",
                "class": "جماعت",
            },
            "ar": {
                "def": "تعريف",
                "return": "إرجاع",
                "print": "طباعة",
                "if": "إذا",
                "for": "لكل",
                "while": "بينما",
                "class": "فئة",
            },
            "es": {
                "def": "definir",
                "return": "retornar",
                "print": "imprimir",
                "if": "si",
                "for": "para",
                "while": "mientras",
                "class": "clase",
            },
        }

        term_lower = request.term.lower()
        lang_translations = mock_translations.get(request.target_language, {})
        translation = lang_translations.get(
            term_lower, f"[MOCK_HF_{self.profile.name}_{term_lower}]"
        )

        return Translation(
            translation=translation,
            alternatives=[],
            rationale=f"Mock translation for dry-run mode ({self.profile.name})",
            word_type="verb",
            form="infinitive",
            model_name=self.get_model_name(),
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            confidence=0.85,
        )
