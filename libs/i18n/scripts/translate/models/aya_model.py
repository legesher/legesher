"""Aya 23 model implementation via Ollama for local translations.

This module implements the TranslationModel interface using the Aya 23
multilingual model running locally through Ollama.
"""

import asyncio
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
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """Initialize Aya model.

        Args:
            model: Aya model version in Ollama
            dry_run: If True, don't make real calls (for testing)
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Initial delay in seconds before first retry (exponential backoff)
        """
        self.model = model
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_delay = retry_delay

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

    def get_model_version(self) -> str | None:
        """Exact Ollama model tag for provenance."""
        return self.model

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
        """Translate a Python term using Aya 23 with retry logic.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If Ollama call fails after all retries
        """
        if self.dry_run:
            return self._mock_translation(request)

        prompt = self._build_prompt(request)

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling Aya via Ollama for term '{request.term}' -> {request.target_language} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

                # Call Ollama API in a thread to avoid blocking the event loop
                response = await asyncio.to_thread(
                    ollama.generate,
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

            except (ConnectionError, TimeoutError, OSError) as e:
                # Retryable errors (connection issues, timeouts)
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Aya/Ollama error for '{request.term}' (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Aya/Ollama error for '{request.term}' after {self.max_retries} attempts: {e}"
                    )
                    raise

            except ValueError as e:
                # JSON parsing errors - retry in case of malformed response
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Aya response parsing failed for '{request.term}' (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Aya response parsing failed for '{request.term}' after {self.max_retries} attempts: {e}"
                    )
                    raise

            except Exception as e:
                # Non-retryable errors
                logger.error(f"Aya/Ollama error for '{request.term}': {e}")
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise Exception("Translation failed after all retries")

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
            "hu": "Hungarian",
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
1. Focus on the programming CONCEPT, not the English word
2. Use natural {language_name} that programmers would understand
3. Prefer appropriate grammatical forms (infinitive for verbs, singular for nouns)

CRITICAL RULES:
- You MUST translate to {language_name}. DO NOT return the English term.
- Even technical terms like "ValueError", "isinstance", "bytearray" MUST be translated.
- Example: "ValueError" in Spanish should be "ErrorDeValor", not "ValueError"
- Example: "isinstance" in German should be "istinstanzvon", not "isinstance"
- The only exception: if the {language_name} word happens to be identical to English (like "no" in Spanish)
- Combine words without spaces to create valid Python identifiers (e.g., "istinstanzvon" not "ist instanz von")

OUTPUT:
Respond with ONLY a valid JSON object (no markdown, no extra text):
{{
  "translation": "the translated term in {language_name}",
  "word_type": "verb|noun|etc",
  "form": "infinitive|singular|etc",
  "confidence": 0.85,
  "alternatives": ["alt1", "alt2"],
  "rationale": "Why you chose this {language_name} translation"
}}
"""

        return prompt

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from Aya response with multiple fallback strategies.

        Aya may wrap JSON in markdown code blocks, add extra text, or produce
        malformed JSON. This method tries multiple parsing strategies.

        Args:
            response_text: Raw response from Aya

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If JSON cannot be extracted or parsed with any strategy
        """
        # Strategy 1: Try to extract from markdown code blocks
        code_block_pattern = r"```(?:json)?\s*(\{[^`]*?\})\s*```"
        match = re.search(code_block_pattern, response_text, re.DOTALL)

        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.debug("Failed to parse JSON from code block, trying repair")
                # Try to repair and parse
                repaired = self._repair_json(json_str)
                if repaired:
                    return repaired

        # Strategy 2: Find raw JSON object (greedy match)
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.finditer(json_pattern, response_text, re.DOTALL)

        for match in matches:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to repair this candidate
                repaired = self._repair_json(json_str)
                if repaired:
                    return repaired

        # Strategy 3: Extract field by field with regex
        logger.warning("Standard JSON parsing failed, attempting field extraction")
        extracted = self._extract_fields_from_text(response_text)
        if extracted and "translation" in extracted:
            return extracted

        # All strategies failed
        logger.error(
            f"Could not parse JSON from Aya response: {response_text[:500]}..."
        )
        raise ValueError("Failed to parse JSON after trying all strategies")

    def _repair_json(self, json_str: str) -> dict | None:
        """Attempt to repair malformed JSON.

        Common issues with LLM-generated JSON:
        - Trailing commas
        - Unescaped quotes in strings
        - Incomplete JSON
        - Extra text after closing brace

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Parsed dict if repair successful, None otherwise
        """
        # Remove trailing commas before closing braces/brackets
        repaired = re.sub(r",(\s*[}\]])", r"\1", json_str)

        # Remove any text after the final closing brace
        brace_match = re.search(r"\}[^}]*$", repaired)
        if brace_match:
            repaired = repaired[: brace_match.start() + 1]

        # Try to fix common quote escaping issues
        # This is tricky, so we'll just try parsing
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            # Try adding missing closing braces
            open_braces = repaired.count("{")
            close_braces = repaired.count("}")
            if open_braces > close_braces:
                repaired += "}" * (open_braces - close_braces)
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    pass

        return None

    def _extract_fields_from_text(self, text: str) -> dict:
        """Extract translation fields from text using regex patterns.

        Fallback method when JSON parsing completely fails. Looks for
        field patterns like "translation": "value" in the text.

        Args:
            text: Response text

        Returns:
            Dictionary with extracted fields
        """
        result = {}

        # Extract translation (most important field)
        translation_patterns = [
            r'"translation"\s*:\s*"([^"]*)"',
            r"'translation'\s*:\s*'([^']*)'",
            r'translation:\s*"([^"]*)"',
            r"translation:\s*([^\s,}\n]+)",
        ]

        for pattern in translation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["translation"] = match.group(1)
                break

        # Extract word_type
        word_type_match = re.search(r'"word_type"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
        if word_type_match:
            result["word_type"] = word_type_match.group(1)

        # Extract form
        form_match = re.search(r'"form"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
        if form_match:
            result["form"] = form_match.group(1)

        # Extract confidence (as float)
        confidence_match = re.search(
            r'"confidence"\s*:\s*([0-9.]+)', text, re.IGNORECASE
        )
        if confidence_match:
            try:
                result["confidence"] = float(confidence_match.group(1))
            except ValueError:
                result["confidence"] = 0.7

        # Extract alternatives array
        alternatives_match = re.search(
            r'"alternatives"\s*:\s*\[(.*?)\]', text, re.IGNORECASE | re.DOTALL
        )
        if alternatives_match:
            # Extract quoted strings from array
            alt_strings = re.findall(r'"([^"]*)"', alternatives_match.group(1))
            result["alternatives"] = alt_strings

        # Extract rationale
        rationale_match = re.search(r'"rationale"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
        if rationale_match:
            result["rationale"] = rationale_match.group(1)

        logger.info(f"Extracted fields from malformed response: {result}")
        return result

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
