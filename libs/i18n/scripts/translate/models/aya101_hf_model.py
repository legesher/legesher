"""Aya-101 model implementation via Hugging Face Transformers.

This module implements the TranslationModel interface using the Aya-101
massively multilingual model (101 languages) from Cohere via Hugging Face.
"""

import asyncio
import logging

from .base import Translation, TranslationModel, TranslationRequest
from .json_utils import parse_json_response

logger = logging.getLogger(__name__)


class Aya101HuggingFaceModel(TranslationModel):
    """Aya-101 translation model via Hugging Face Transformers.

    This model uses the Aya-101 massively multilingual model (101 languages)
    from Cohere, loaded via the Hugging Face transformers library.

    Model: CohereForAI/aya-101
    Languages: 101 languages supported

    Setup:
        pip install transformers torch accelerate sentencepiece
        # Or with UV:
        uv pip install "legesher-i18n[ml]"

    Pricing:
        - Free (runs locally)
        - Requires: ~16GB RAM recommended, ~20GB disk space for model weights
        - GPU optional but recommended (reduces inference from seconds to milliseconds)
    """

    def __init__(
        self,
        model_name: str = "CohereLabs/aya-101",  # Correct repository name
        device: str | None = None,
        dry_run: bool = False,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        cache_dir: str | None = None,
    ):
        """Initialize Aya-101 model.

        Args:
            model_name: Hugging Face model identifier (CohereLabs/aya-101)
            device: Device to run on ('cpu', 'cuda', 'mps', or None for auto-detect)
            dry_run: If True, don't load model (for testing)
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Initial delay in seconds before first retry (exponential backoff)
            cache_dir: Directory to cache model weights (default: ~/.cache/huggingface)
        """
        self.model_name = model_name
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_dir = cache_dir

        # Model and tokenizer (lazy loaded)
        self._model = None
        self._tokenizer = None
        self._device = device

        if not self.dry_run:
            # Import here to avoid requiring transformers for all users
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                self._torch = torch
                self._AutoModelForSeq2SeqLM = AutoModelForSeq2SeqLM
                self._AutoTokenizer = AutoTokenizer

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
                    f"Initialized Aya-101 Hugging Face model: {model_name} "
                    f"(device={self._device}, dry_run={dry_run})"
                )

            except ImportError as e:
                logger.error(
                    f"Failed to import transformers/torch: {e}. "
                    "Install with: uv pip install 'legesher-i18n[ml]'"
                )
                raise

    def _load_model(self):
        """Lazy load model and tokenizer (expensive operation)."""
        if self._model is None and not self.dry_run:
            logger.info(f"Loading Aya-101 model from {self.model_name}...")

            # Try to load from cache first
            try_local_first = True

            # Load tokenizer
            for attempt in range(2):  # Try cache first, then download
                try:
                    self._tokenizer = self._AutoTokenizer.from_pretrained(
                        self.model_name,
                        cache_dir=self.cache_dir,
                        local_files_only=try_local_first and attempt == 0,
                    )
                    logger.info("✓ Tokenizer loaded successfully")
                    break
                except Exception:
                    if attempt == 0 and try_local_first:
                        logger.info("Tokenizer not in cache, downloading...")
                        continue
                    else:
                        raise

            # Load model with appropriate dtype and optimizations
            logger.info("Loading model weights (this may take a few minutes)...")

            for attempt in range(2):  # Try cache first, then download
                try:
                    if self._device == "cuda":
                        # Use float16 on GPU to save memory
                        self._model = self._AutoModelForSeq2SeqLM.from_pretrained(
                            self.model_name,
                            cache_dir=self.cache_dir,
                            torch_dtype=self._torch.float16,
                            low_cpu_mem_usage=True,  # Reduce memory spikes
                            local_files_only=try_local_first and attempt == 0,
                        ).to(self._device)
                    else:
                        # Use float32 on CPU/MPS with memory optimizations
                        self._model = self._AutoModelForSeq2SeqLM.from_pretrained(
                            self.model_name,
                            cache_dir=self.cache_dir,
                            low_cpu_mem_usage=True,  # Reduce memory spikes
                            local_files_only=try_local_first and attempt == 0,
                        ).to(self._device)
                    logger.info(f"✓ Model loaded successfully on {self._device}")
                    break
                except Exception:
                    if attempt == 0 and try_local_first:
                        logger.info(
                            "Model not fully cached, downloading missing files..."
                        )
                        logger.info("This may take 10-30 minutes for ~20GB download...")
                        continue
                    else:
                        raise

    def get_model_name(self) -> str:
        """Get model name."""
        return "aya-101-hf"

    def estimate_cost(self, request: TranslationRequest) -> float:
        """Estimate cost for translation request.

        Aya-101 runs locally, so cost is always $0.00.

        Args:
            request: Translation request

        Returns:
            0.0 (free local model)
        """
        return 0.0

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term using Aya-101 with retry logic.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If translation fails after all retries
        """
        if self.dry_run:
            return self._mock_translation(request)

        # Ensure model is loaded
        self._load_model()

        prompt = self._build_prompt(request)

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling Aya-101 HF for term '{request.term}' -> {request.target_language} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

                # Run inference in thread to avoid blocking event loop
                response_text = await asyncio.to_thread(self._generate, prompt)

                # Parse JSON from response
                result_data = parse_json_response(response_text)

                logger.info(
                    f"Aya-101 HF translation: '{request.term}' -> '{result_data.get('translation')}' "
                    f"({request.target_language})"
                )

                # Build Translation object
                return Translation(
                    translation=result_data.get("translation", ""),
                    alternatives=result_data.get("alternatives", []),
                    rationale=result_data.get("rationale", ""),
                    word_type=result_data.get("word_type", ""),
                    form=result_data.get("form", ""),
                    model_name=self.get_model_name(),
                    cost=0.0,  # Local model, no cost
                    input_tokens=0,  # Could calculate if needed
                    output_tokens=0,
                    confidence=result_data.get("confidence", 0.85),
                )

            except (RuntimeError, OSError) as e:
                # Retryable errors (OOM, device errors, etc.)
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Aya-101 HF error for '{request.term}' (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Aya-101 HF error for '{request.term}' after {self.max_retries} attempts: {e}"
                    )
                    raise

            except ValueError as e:
                # JSON parsing errors - retry in case of malformed response
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Aya-101 HF response parsing failed for '{request.term}' (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Aya-101 HF response parsing failed for '{request.term}' after {self.max_retries} attempts: {e}"
                    )
                    raise

            except Exception as e:
                # Non-retryable errors
                logger.error(f"Aya-101 HF error for '{request.term}': {e}")
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise Exception("Translation failed after all retries")

    def _generate(self, prompt: str) -> str:
        """Generate response from model (blocking, call in thread).

        Args:
            prompt: Input prompt

        Returns:
            Generated text
        """
        # Tokenize
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)

        # Generate
        with self._torch.no_grad():  # Disable gradients for inference
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.3,  # Lower temperature for more consistent translations
                do_sample=True,
                top_p=0.95,
                num_return_sequences=1,
            )

        # Decode
        response_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        return response_text

    def _build_prompt(self, request: TranslationRequest) -> str:
        """Build translation prompt for Aya-101.

        Args:
            request: Translation request

        Returns:
            Formatted prompt string
        """
        # Map language codes to full names (Aya-101 supports 101 languages)
        LANGUAGE_NAMES = {
            # From Aya-101 documentation
            "afr": "Afrikaans",
            "amh": "Amharic",
            "ar": "Arabic",
            "aze": "Azerbaijani",
            "bel": "Belarusian",
            "ben": "Bengali",
            "bul": "Bulgarian",
            "cat": "Catalan",
            "ceb": "Cebuano",
            "ces": "Czech",
            "cym": "Welsh",
            "da": "Danish",
            "de": "German",
            "el": "Greek",
            "en": "English",
            "epo": "Esperanto",
            "es": "Spanish",
            "est": "Estonian",
            "eus": "Basque",
            "fi": "Finnish",
            "fil": "Filipino",
            "fr": "French",
            "fry": "Frisian",
            "gla": "Scottish Gaelic",
            "gle": "Irish",
            "glg": "Galician",
            "guj": "Gujarati",
            "hat": "Haitian Creole",
            "hau": "Hausa",
            "he": "Hebrew",
            "hi": "Hindi",
            "hu": "Hungarian",
            "hye": "Armenian",
            "ibo": "Igbo",
            "id": "Indonesian",
            "isl": "Icelandic",
            "it": "Italian",
            "jav": "Javanese",
            "ja": "Japanese",
            "kan": "Kannada",
            "kat": "Georgian",
            "kaz": "Kazakh",
            "khm": "Khmer",
            "kir": "Kyrgyz",
            "ko": "Korean",
            "kur": "Kurdish",
            "lao": "Lao",
            "lav": "Latvian",
            "lat": "Latin",
            "lit": "Lithuanian",
            "ltz": "Luxembourgish",
            "mal": "Malayalam",
            "mar": "Marathi",
            "mkd": "Macedonian",
            "mlg": "Malagasy",
            "mlt": "Maltese",
            "mon": "Mongolian",
            "mri": "Maori",
            "ms": "Malay",
            "mya": "Burmese",
            "nep": "Nepali",
            "nl": "Dutch",
            "no": "Norwegian",
            "nso": "Northern Sotho",
            "nya": "Nyanja",
            "ory": "Oriya",
            "pan": "Punjabi",
            "pes": "Persian",
            "pl": "Polish",
            "pt": "Portuguese",
            "pus": "Pashto",
            "ro": "Romanian",
            "ru": "Russian",
            "sin": "Sinhala",
            "slk": "Slovak",
            "slv": "Slovenian",
            "smo": "Samoan",
            "sna": "Shona",
            "snd": "Sindhi",
            "som": "Somali",
            "sot": "Southern Sotho",
            "sqi": "Albanian",
            "srp": "Serbian",
            "sun": "Sundanese",
            "swa": "Swahili",
            "sv": "Swedish",
            "tam": "Tamil",
            "tel": "Telugu",
            "tgk": "Tajik",
            "th": "Thai",
            "tr": "Turkish",
            "twi": "Twi",
            "ukr": "Ukrainian",
            "urd": "Urdu",
            "uzb": "Uzbek",
            "vi": "Vietnamese",
            "xho": "Xhosa",
            "yid": "Yiddish",
            "yor": "Yoruba",
            "zh": "Chinese",
            "zul": "Zulu",
        }

        language_name = LANGUAGE_NAMES.get(
            request.target_language, request.target_language.upper()
        )

        prompt = f"""You are a multilingual expert translating Python programming terms.

TERM TO TRANSLATE: "{request.term}"
TARGET LANGUAGE: {language_name}
"""

        # Add context if available
        if request.context:
            # Truncate context for efficiency
            context_short = request.context[:800]
            if len(request.context) > 800:
                context_short += "..."
            prompt += f"""
CONTEXT:
{context_short}
"""

        # Add linguistic standards if available
        if request.linguistic_standards:
            standards_short = request.linguistic_standards[:500]
            if len(request.linguistic_standards) > 500:
                standards_short += "..."
            prompt += f"""
STANDARDS:
{standards_short}
"""

        prompt += f"""
TASK:
Translate "{request.term}" to {language_name} for Python programming:
1. Focus on the programming CONCEPT
2. Use natural {language_name} that programmers would understand
3. Prefer appropriate grammatical forms (infinitive for verbs, singular for nouns)

OUTPUT:
Respond with ONLY a valid JSON object (no markdown, no extra text):
{{
  "translation": "the translated term",
  "word_type": "verb|noun|etc",
  "form": "infinitive|singular|etc",
  "confidence": 0.85,
  "alternatives": ["alt1", "alt2"],
  "rationale": "Why you chose this translation"
}}
"""

        return prompt

    def _mock_translation(self, request: TranslationRequest) -> Translation:
        """Generate mock translation for dry-run mode.

        Args:
            request: Translation request

        Returns:
            Mock Translation object
        """
        # Simple mock translations for common terms
        MOCK_TRANSLATIONS = {
            "es": {
                "def": "definir",
                "return": "retornar",
                "print": "imprimir",
                "if": "si",
                "for": "para",
                "while": "mientras",
                "class": "clase",
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
            "bn": {
                "def": "সংজ্ঞায়িত",
                "return": "ফেরত",
                "print": "মুদ্রণ",
                "if": "যদি",
                "for": "জন্য",
                "while": "যখন",
                "class": "শ্রেণী",
            },
            "ben": {
                "def": "সংজ্ঞায়িত",
                "return": "ফেরত",
                "print": "মুদ্রণ",
                "if": "যদি",
                "for": "জন্য",
                "while": "যখন",
                "class": "শ্রেণী",
            },
        }

        term_lower = request.term.lower()
        lang_translations = MOCK_TRANSLATIONS.get(request.target_language, {})
        translation = lang_translations.get(term_lower, f"[MOCK_AYA101_{term_lower}]")

        return Translation(
            translation=translation,
            alternatives=[],
            rationale="Mock translation for dry-run mode (Aya-101 HF)",
            word_type="verb",
            form="infinitive",
            model_name=self.get_model_name(),
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            confidence=0.85,
        )
