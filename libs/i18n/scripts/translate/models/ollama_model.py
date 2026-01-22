"""Ollama model implementation for local LLM translation.

This module implements the TranslationModel interface using Ollama
for local LLM inference. Supports any model available in Ollama,
including Aya for multilingual translation.

Setup:
    1. Install Ollama: https://ollama.ai
    2. Pull the Aya model: ollama pull aya
    3. Ensure Ollama is running: ollama serve

Usage:
    python run_pipeline.py --models ollama --languages ru --terms except
"""

import logging
import os
from typing import Optional

import httpx

from .base import Translation, TranslationModel, TranslationRequest
from .json_utils import parse_json_response

logger = logging.getLogger(__name__)

# Default Ollama API endpoint
DEFAULT_OLLAMA_HOST = "http://localhost:11434"

# Default model - Aya is good for multilingual tasks
DEFAULT_MODEL = "aya"


class OllamaModel(TranslationModel):
    """Translation model using Ollama for local LLM inference.

    This model uses Ollama to run LLMs locally, supporting models like
    Aya for multilingual translation without cloud dependencies.

    Requirements:
        - Ollama installed and running (ollama serve)
        - Model pulled (e.g., ollama pull aya)

    Attributes:
        model: Ollama model name (default: aya)
        host: Ollama API host (default: http://localhost:11434)
        dry_run: If True, return mock translations
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        host: Optional[str] = None,
        dry_run: bool = False,
        timeout: float = 120.0,
    ):
        """Initialize Ollama model.

        Args:
            model: Ollama model name (default: aya)
            host: Ollama API host. If None, uses OLLAMA_HOST env var or default.
            dry_run: If True, don't make real API calls (for testing)
            timeout: Request timeout in seconds (default: 120)
        """
        self.model = model
        self.host = host or os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
        self.dry_run = dry_run
        self.timeout = timeout

        logger.info(
            f"Initialized Ollama model: {model} (host={self.host}, dry_run={dry_run})"
        )

    def get_model_name(self) -> str:
        """Get model name for tracking."""
        return f"ollama-{self.model}"

    def estimate_cost(self, request: TranslationRequest) -> float:
        """Estimate cost for translation request.

        Ollama runs locally, so cost is always $0.00.

        Args:
            request: Translation request

        Returns:
            0.0 (free local model)
        """
        return 0.0

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term using Ollama.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If API call fails
        """
        if self.dry_run:
            return self._mock_translation(request)

        prompt = self._build_prompt(request)

        try:
            logger.debug(
                f"Calling Ollama ({self.model}) for '{request.term}' -> "
                f"{request.target_language}"
            )

            response_text = await self._call_ollama(prompt)

            # Try to parse as JSON first
            try:
                result_data = parse_json_response(response_text)
            except ValueError:
                # If JSON parsing fails, use the raw response as translation
                logger.debug("JSON parsing failed, using raw response")
                result_data = {
                    "translation": response_text.strip(),
                    "confidence": 0.7,
                }

            translation = result_data.get("translation", response_text.strip())

            logger.info(
                f"Ollama translation: '{request.term}' -> '{translation}' "
                f"({request.target_language})"
            )

            return Translation(
                translation=translation,
                alternatives=result_data.get("alternatives", []),
                rationale=result_data.get("rationale", ""),
                word_type=result_data.get("word_type", ""),
                form=result_data.get("form", ""),
                model_name=self.get_model_name(),
                cost=0.0,
                input_tokens=0,
                output_tokens=0,
                confidence=result_data.get("confidence", 0.8),
            )

        except Exception as e:
            logger.error(f"Ollama error for '{request.term}': {e}")
            raise

    async def _call_ollama(self, prompt: str) -> str:
        """Make API call to Ollama.

        Args:
            prompt: The translation prompt

        Returns:
            Response text from the model
        """
        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower for more consistent translations
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    def _build_prompt(self, request: TranslationRequest) -> str:
        """Build translation prompt for Ollama.

        Args:
            request: Translation request

        Returns:
            Formatted prompt string
        """
        # Map language codes to full names
        language_names = {
            "ar": "Arabic",
            "bn": "Bengali",
            "da": "Danish",
            "de": "German",
            "el": "Greek",
            "en": "English",
            "es": "Spanish",
            "fi": "Finnish",
            "fr": "French",
            "he": "Hebrew",
            "hi": "Hindi",
            "hu": "Hungarian",
            "id": "Indonesian",
            "it": "Italian",
            "ja": "Japanese",
            "ko": "Korean",
            "ms": "Malay",
            "nl": "Dutch",
            "no": "Norwegian",
            "pl": "Polish",
            "pt": "Portuguese",
            "ru": "Russian",
            "sv": "Swedish",
            "th": "Thai",
            "tr": "Turkish",
            "vi": "Vietnamese",
            "zh": "Chinese",
        }

        language_name = language_names.get(
            request.target_language, request.target_language.upper()
        )

        prompt = f"""You are translating Python programming keywords for developers who code in {language_name}.

TERM TO TRANSLATE: "{request.term}"
TARGET LANGUAGE: {language_name}

IMPORTANT CONTEXT:
- This is the Python keyword "{request.term}" used in exception handling (try/except blocks)
- The translation should be a SINGLE WORD that {language_name}-speaking programmers would use
- It must be a valid identifier (no spaces, no special characters except underscore)
- Focus on the programming CONCEPT, not literal word translation

Respond with ONLY a valid JSON object:
{{
  "translation": "the_translated_term",
  "word_type": "keyword",
  "confidence": 0.85,
  "rationale": "Brief explanation of why this translation"
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
            "ru": {
                "except": "исключение",
                "def": "определить",
                "return": "вернуть",
                "print": "печать",
            },
            "es": {
                "except": "excepto",
                "def": "definir",
                "return": "retornar",
                "print": "imprimir",
            },
        }

        term_lower = request.term.lower()
        lang_translations = mock_translations.get(request.target_language, {})
        translation = lang_translations.get(term_lower, f"[MOCK_OLLAMA_{term_lower}]")

        return Translation(
            translation=translation,
            alternatives=[],
            rationale="Mock translation for dry-run mode (Ollama)",
            word_type="keyword",
            form="",
            model_name=self.get_model_name(),
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            confidence=0.85,
        )
