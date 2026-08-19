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
        host: str | None = None,
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

    def get_model_version(self) -> str | None:
        """Exact Ollama model tag for provenance."""
        return self.model

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
        # Language names come from languages.json — the single source
        # (CORE-1804).
        from legesher_i18n.language_names import language_name as _resolve_name

        language_name = _resolve_name(request.target_language)

        # Term concept explanations - what the term DOES, not what it's CALLED
        term_concepts = {
            # High-impact builtins (15 terms covering ~150 untranslated entries)
            "bytearray": "a mutable sequence of bytes (like a changeable list of byte values)",
            "aiter": "asynchronous iterator - gets items one at a time without blocking",
            "ord": "gets the numeric Unicode code point for a single character",
            "isinstance": "checks if an object is of a specific type (type verification)",
            "super": "refers to the parent/base class in inheritance",
            "float": "a decimal/fractional number (numbers with decimal points)",
            "divmod": "division with remainder - returns both quotient and modulo",
            "lambda": "an anonymous/unnamed small inline function",
            "ascii": "converts to text representation using ASCII encoding",
            "dir": "lists all attributes and methods of an object (directory listing)",
            "vars": "returns the __dict__ attribute (variables dictionary) of an object",
            "hash": "computes a hash value (integer) for an object",
            "bin": "converts integer to binary string representation",
            "anext": "gets the next item from an async iterator",
            "global": "declares a variable as global scope (not local)",
            # Additional common terms
            "enumerate": "pairs each item in a sequence with its index number",
            "filter": "selects items from a sequence that pass a test",
            "map": "applies a function to each item in a sequence",
            "zip": "combines multiple sequences element by element",
            "iter": "creates an iterator from a sequence",
            "next": "gets the next item from an iterator",
            "range": "generates a sequence of numbers",
            "slice": "extracts a portion of a sequence",
            "sorted": "returns a new sorted list from items",
            "reversed": "returns items in reverse order",
            "sum": "adds all numbers in a sequence",
            "len": "returns the length/count of items",
            "max": "returns the largest item",
            "min": "returns the smallest item",
            "abs": "returns absolute value (removes negative sign)",
            "pow": "raises a number to a power (exponentiation)",
            "round": "rounds a number to specified precision",
            "hex": "converts integer to hexadecimal string",
            "oct": "converts integer to octal string",
            "chr": "converts Unicode code point to character",
            "repr": "returns printable representation of object",
            "format": "formats a value according to a format spec",
            "eval": "evaluates a string as Python expression",
            "exec": "executes Python code from a string",
            "compile": "compiles source code into a code object",
            "input": "reads a line of text from user input",
            "print": "outputs text to the console",
            "open": "opens a file for reading or writing",
            "help": "displays documentation for an object",
            "id": "returns unique identifier of an object",
            "type": "returns the type/class of an object",
            "callable": "checks if an object can be called like a function",
            "getattr": "gets an attribute value from an object",
            "setattr": "sets an attribute value on an object",
            "delattr": "deletes an attribute from an object",
            "hasattr": "checks if an object has an attribute",
            "globals": "returns dictionary of global variables",
            "locals": "returns dictionary of local variables",
            "breakpoint": "pauses execution for debugging",
            "memoryview": "creates a view into memory of an object",
            "object": "base class for all Python classes",
            "property": "creates a managed attribute with getter/setter",
            "classmethod": "defines a method that receives the class",
            "staticmethod": "defines a method without self parameter",
            "bool": "boolean type - True or False",
            "int": "integer type - whole numbers",
            "str": "string type - text",
            "list": "ordered mutable sequence",
            "dict": "key-value mapping (dictionary)",
            "set": "unordered collection of unique items",
            "tuple": "ordered immutable sequence",
            "frozenset": "immutable set",
            "bytes": "immutable sequence of bytes",
            "complex": "complex number with real and imaginary parts",
            "issubclass": "checks if a class inherits from another",
            "all": "returns True if all items are truthy",
            "any": "returns True if any item is truthy",
            "ellipsis": "placeholder indicating continuation (...)",
            "notimplemented": "marker for unimplemented operations",
        }

        # Script type detection for concatenation rules
        logographic_scripts = {"zh", "ja"}  # Characters naturally concatenate

        if request.target_language in logographic_scripts:
            concat_rule = (
                "Characters naturally concatenate in your script. "
                "Underscores are OPTIONAL but acceptable for clarity in long terms."
            )
        else:
            concat_rule = (
                "Use UNDERSCORES to join compound words. "
                "NO spaces allowed (invalid Python identifier)."
            )

        # Get concept explanation for this term
        term_lower = request.term.lower()
        concept = term_concepts.get(
            term_lower,
            "a Python programming concept (translate based on what it does)",
        )

        # Language-specific examples to discourage transliteration
        transliteration_examples = {
            "ar": (
                '❌ BAD: "bytearray" → "بايتاراي" (just sounds like English)\n'
                '✅ GOOD: "bytearray" → "مصفوفة_بايت" (means "byte array")'
            ),
            "hi": (
                '❌ BAD: "isinstance" → "इन्स्टेन्स" (just sounds like English)\n'
                '✅ GOOD: "isinstance" → "प्रकार_जाँच" (means "type check")'
            ),
            "ru": (
                '❌ BAD: "float" → "флоат" (just sounds like English)\n'
                '✅ GOOD: "float" → "дробное" (means "fractional/decimal")'
            ),
            "zh": (
                '❌ BAD: "isinstance" → "实例" (incomplete meaning)\n'
                '✅ GOOD: "isinstance" → "是实例" (means "is instance of")'
            ),
            "ja": (
                '❌ BAD: "isinstance" → "インスタンス" (just katakana of English)\n'
                '✅ GOOD: "isinstance" → "型確認" (means "type verification")'
            ),
            "ko": (
                '❌ BAD: "isinstance" → "인스턴스" (just sounds like English)\n'
                '✅ GOOD: "isinstance" → "유형확인" (means "type check")'
            ),
            "th": (
                '❌ BAD: "bytearray" → "ไบต์อาร์เรย์" (just sounds like English)\n'
                '✅ GOOD: "bytearray" → "อาร์เรย์_ไบต์" (means "byte array")'
            ),
            "he": (
                '❌ BAD: "lambda" → "למבדה" (just sounds like English)\n'
                '✅ GOOD: "lambda" → "פונקציה_אלמונית" (means "anonymous function")'
            ),
            "de": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "ist_instanz_von" (means "is instance of")'
            ),
            "es": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "es_instancia_de" (means "is instance of")'
            ),
            "fr": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "est_instance_de" (means "is instance of")'
            ),
            "pt": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "é_instância_de" (means "is instance of")'
            ),
            "it": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "è_istanza_di" (means "is instance of")'
            ),
            "nl": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "is_instantie_van" (means "is instance of")'
            ),
            "pl": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "jest_instancją" (means "is instance of")'
            ),
            "hu": (
                '❌ BAD: "isinstance" → "isinstance" (unchanged English)\n'
                '✅ GOOD: "isinstance" → "példány_e" (means "is instance of")'
            ),
        }

        # Get language-specific example or use a generic one
        example = transliteration_examples.get(
            request.target_language,
            (
                "❌ BAD: Keeping the English word unchanged or just making it sound local\n"
                "✅ GOOD: Using native words that describe what the concept DOES"
            ),
        )

        prompt = f"""You are translating Python programming terms into {language_name}.

TERM: "{request.term}"
CONCEPT: {concept}
TARGET LANGUAGE: {language_name}

## CRITICAL: Conceptual Translation, NOT Transliteration

You must translate the MEANING/CONCEPT into native {language_name} words.
DO NOT just make the English word sound like {language_name}.

{example}

## Word Concatenation Rule for {language_name}

{concat_rule}

## Requirements

1. Translate the CONCEPT using native {language_name} words
2. Think: "What would a {language_name} speaker call this functionality?"
3. Result MUST be a valid Python identifier:
   - NO spaces (use underscores instead)
   - NO hyphens (minus sign in Python)
   - Start with letter or underscore
4. DO NOT return the English term unchanged

Respond with ONLY valid JSON (no markdown code blocks):
{{
  "translation": "your_translation_here",
  "rationale": "Brief explanation of your word choice",
  "confidence": 0.85
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
