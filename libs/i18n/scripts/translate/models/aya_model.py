"""Aya 23 model implementation via Ollama for local translations.

This module implements the TranslationModel interface using the Aya 23
multilingual model running locally through Ollama.
"""

import json
import logging
import re

import ollama

from .base import Translation, TranslationModel, TranslationRequest

logger = logging.getLogger(__name__)


class AyaModel(TranslationModel):
    """Aya 23 translation model via Ollama.

    This model uses the Aya 23 multilingual model running locally through
    Ollama. No API costs since it runs locally, but requires Ollama to be
    installed and the Aya 23 model to be pulled.

    Setup:
        ollama pull aya:latest

    Pricing:
        - Free (runs locally)
        - Requires: ~8GB RAM, ~10GB disk space
    """

    def __init__(
        self,
        model: str = "aya:latest",
        dry_run: bool = False,
    ):
        """Initialize Aya model.

        Args:
            model: Aya model version in Ollama
            dry_run: If True, don't make real calls (for testing)
        """
        self.model = model
        self.dry_run = dry_run

        if not self.dry_run:
            # Test Ollama connection
            try:
                ollama.list()
                logger.info("Connected to Ollama successfully")
            except Exception as e:
                logger.warning(
                    f"Could not connect to Ollama: {e}. "
                    "Make sure Ollama is running: https://ollama.ai"
                )

        logger.info(f"Initialized Aya model: {model} (dry_run={dry_run})")

    def get_model_name(self) -> str:
        """Get model name."""
        return f"aya23-{self.model}"

    def estimate_cost(self, request: TranslationRequest) -> float:
        """Estimate cost for translation request.

        Aya runs locally, so cost is always $0.00.

        Args:
            request: Translation request

        Returns:
            0.0 (free local model)
        """
        return 0.0

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term using Aya 23.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If Ollama call fails or response parsing fails
        """
        if self.dry_run:
            return self._mock_translation(request)

        prompt = self._build_prompt(request)

        try:
            logger.debug(
                f"Calling Aya via Ollama for term '{request.term}' -> {request.target_language}"
            )

            # Call Ollama API (synchronous, but we wrap in async context)
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.3,  # Lower temperature for more consistent translations
                    "num_predict": 512,  # Max output tokens
                },
            )

            response_text = response["response"]

            # Parse JSON from response
            result_data = self._parse_json_response(response_text)

            logger.info(
                f"Aya translation: '{request.term}' -> '{result_data.get('translation')}' "
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
                input_tokens=0,  # Ollama doesn't report token counts
                output_tokens=0,
                confidence=result_data.get("confidence", 0.85),
            )

        except Exception as e:
            logger.error(f"Aya/Ollama error for '{request.term}': {e}")
            raise

    def _build_prompt(self, request: TranslationRequest) -> str:
        """Build translation prompt for Aya.

        Args:
            request: Translation request

        Returns:
            Formatted prompt string
        """
        # Map language codes to full names
        LANGUAGE_NAMES = {
            "es": "Spanish",
            "ar": "Arabic",
            "fr": "French",
            "zh": "Chinese (Simplified)",
            "hi": "Hindi",
            "ru": "Russian",
            "pt": "Portuguese",
            "de": "German",
            "ja": "Japanese",
            "ko": "Korean",
            "it": "Italian",
            "pl": "Polish",
            "tr": "Turkish",
            "vi": "Vietnamese",
            "th": "Thai",
            "nl": "Dutch",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish",
            "el": "Greek",
            "he": "Hebrew",
            "id": "Indonesian",
            "ms": "Malay",
        }

        language_name = LANGUAGE_NAMES.get(
            request.target_language, request.target_language.upper()
        )

        prompt = f"""You are a multilingual expert translating Python programming terms.

TERM TO TRANSLATE: "{request.term}"
TARGET LANGUAGE: {language_name}
"""

        # Add context if available (but keep it shorter for local model)
        if request.context:
            # Truncate context to first 500 chars for local model efficiency
            context_short = request.context[:500]
            if len(request.context) > 500:
                context_short += "..."
            prompt += f"""
CONTEXT:
{context_short}
"""

        # Add linguistic standards if available
        if request.linguistic_standards:
            standards_short = request.linguistic_standards[:300]
            if len(request.linguistic_standards) > 300:
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

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from Aya response.

        Aya may wrap JSON in markdown code blocks or add extra text.

        Args:
            response_text: Raw response from Aya

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If JSON cannot be extracted or parsed
        """
        # Try to extract JSON from markdown code blocks first
        code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(code_block_pattern, response_text, re.DOTALL)

        if match:
            json_str = match.group(1)
        else:
            # Try to find raw JSON object
            json_pattern = r"\{.*\}"
            match = re.search(json_pattern, response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError(f"No JSON found in Aya response: {response_text}")

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from Aya: {json_str}")
            raise ValueError(f"Failed to parse JSON: {e}") from e

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
        }

        term_lower = request.term.lower()
        lang_translations = MOCK_TRANSLATIONS.get(request.target_language, {})
        translation = lang_translations.get(term_lower, f"[MOCK_AYA_{term_lower}]")

        return Translation(
            translation=translation,
            alternatives=[],
            rationale="Mock translation for dry-run mode (Aya)",
            word_type="verb",
            form="infinitive",
            model_name=self.get_model_name(),
            cost=0.0,
            input_tokens=0,
            output_tokens=0,
            confidence=0.85,
        )
