"""Claude 3.5 Sonnet model implementation for translations.

This module implements the TranslationModel interface using Anthropic's
Claude 3.5 Sonnet model for high-quality AI translations.
"""

import asyncio
import json
import logging
import os
import re

from anthropic import AsyncAnthropic, APIError, RateLimitError

from .base import Translation, TranslationModel, TranslationRequest

logger = logging.getLogger(__name__)


class ClaudeModel(TranslationModel):
    """Claude 3.5 Sonnet translation model.

    This model uses Anthropic's Claude API to generate high-quality
    translations with detailed rationale and linguistic metadata.

    Pricing (as of 2025):
        - Input: $3.00 per 1M tokens
        - Output: $15.00 per 1M tokens
    """

    # Cost per token in USD
    INPUT_COST_PER_TOKEN = 3.0 / 1_000_000
    OUTPUT_COST_PER_TOKEN = 15.0 / 1_000_000

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        dry_run: bool = False,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        target: str = "python",
    ):
        """Initialize Claude model.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model version to use
            max_tokens: Maximum tokens in response
            dry_run: If True, don't make real API calls (for testing)
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Initial delay in seconds before first retry (exponential backoff)
            target: Programming-language target whose spec profile seasons
                the prompts (CORE-1608/CORE-1371); ``"python"`` keeps the
                historical wording byte-for-byte.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.target = target

        if not self.dry_run and not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set or api_key provided"
            )

        self.client = AsyncAnthropic(api_key=self.api_key) if not self.dry_run else None

        # Try to load PromptBuilder for style-guide-aware prompts
        self._prompt_builder = None
        try:
            from legesher_i18n.style_guides import StyleGuideLoader
            from legesher_i18n.prompt_builder import PromptBuilder

            loader = StyleGuideLoader()
            self._prompt_builder = PromptBuilder(loader, target=self.target)
            logger.info("PromptBuilder loaded — style-guide-aware prompts enabled")
        except Exception as exc:
            logger.debug("PromptBuilder not available, using legacy prompts: %s", exc)

        logger.info(
            f"Initialized Claude model: {model} (dry_run={dry_run}, max_retries={max_retries})"
        )

    def get_model_name(self) -> str:
        """Get model name."""
        return f"claude-{self.model}"

    def estimate_cost(self, request: TranslationRequest) -> float:
        """Estimate cost for translation request.

        Args:
            request: Translation request

        Returns:
            Estimated cost in USD
        """
        # Estimate token counts
        system_prompt, user_prompt = self._build_prompt_pair(request)
        total_chars = len(system_prompt or "") + len(user_prompt)
        estimated_input_tokens = total_chars // 4  # Rough estimate: 1 token ≈ 4 chars
        estimated_output_tokens = 200  # Conservative estimate for JSON response

        input_cost = estimated_input_tokens * self.INPUT_COST_PER_TOKEN
        output_cost = estimated_output_tokens * self.OUTPUT_COST_PER_TOKEN

        return input_cost + output_cost

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a Python term using Claude with retry logic.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If API call fails after all retries
        """
        if self.dry_run:
            return self._mock_translation(request)

        # Build prompt — use PromptBuilder when available for style-guide-aware prompts
        system_prompt, user_prompt = self._build_prompt_pair(request)

        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling Claude API for term '{request.term}' -> {request.target_language} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

                api_kwargs = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "messages": [{"role": "user", "content": user_prompt}],
                }
                if system_prompt:
                    api_kwargs["system"] = system_prompt

                response = await self.client.messages.create(**api_kwargs)

                # Extract response text
                response_text = response.content[0].text

                # Parse JSON from response
                result_data = self._parse_json_response(response_text)

                # Calculate actual cost
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._calculate_cost(input_tokens, output_tokens)

                logger.info(
                    f"Claude translation: '{request.term}' -> '{result_data.get('translation')}' "
                    f"({request.target_language}) | Tokens: {input_tokens}→{output_tokens} | Cost: ${cost:.4f}"
                )

                # Build Translation object
                return Translation(
                    translation=result_data.get("translation", ""),
                    alternatives=result_data.get("alternatives", []),
                    rationale=result_data.get("rationale", ""),
                    word_type=result_data.get("word_type", ""),
                    form=result_data.get("form", ""),
                    model_name=self.get_model_name(),
                    cost=cost,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    confidence=result_data.get("confidence", 0.9),
                )

            except (RateLimitError, APIError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"Claude API error for '{request.term}' (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Claude API error for '{request.term}' after {self.max_retries} attempts: {e}"
                    )
                    raise  # Raise on last attempt

            except Exception as e:
                # Non-retryable errors
                logger.error(f"Claude API error for '{request.term}': {e}")
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        raise Exception("Translation failed after all retries")

    def _build_prompt_pair(self, request: TranslationRequest) -> tuple[str | None, str]:
        """Build a (system_prompt, user_prompt) pair for the API call.

        When PromptBuilder is available, delegates to it for style-guide-aware
        prompts using the ``system`` parameter.  Otherwise falls back to the
        legacy single-prompt approach (system=None, user=full prompt).

        Args:
            request: Translation request

        Returns:
            Tuple of (system_prompt_or_None, user_prompt)
        """
        if self._prompt_builder is not None:
            try:
                # Wrap the single term as an identifier for PromptBuilder
                identifier = {
                    "text": request.term,
                    "role": "keyword",
                    "context": {},
                }
                # Feed any existing context/standards through the context dict
                if request.context:
                    identifier["context"]["deep_context"] = request.context
                if request.linguistic_standards:
                    identifier["context"]["linguistic_standards"] = (
                        request.linguistic_standards
                    )

                system, user = self._prompt_builder.build_identifier_prompt(
                    identifiers=[identifier],
                    target_lang=request.target_language,
                    existing_glossary={},
                )

                # Append the JSON output format expected by _parse_json_response
                user += (
                    "\n\nIMPORTANT: For EACH identifier, also provide linguistic "
                    "metadata. Respond with ONLY valid JSON in this format:\n"
                    "{\n"
                    '  "translation": "the translated term",\n'
                    '  "word_type": "verb|noun|adjective|preposition|conjunction|etc",\n'
                    '  "form": "infinitive|present|singular|etc",\n'
                    '  "confidence": 0.95,\n'
                    '  "alternatives": ["alternative1", "alternative2"],\n'
                    '  "rationale": "Brief explanation (2-3 sentences)"\n'
                    "}\n"
                    "Do not wrap JSON in markdown code blocks."
                )

                logger.debug(
                    "Using PromptBuilder for '%s' -> %s",
                    request.term,
                    request.target_language,
                )
                return system, user

            except Exception as exc:
                logger.warning(
                    "PromptBuilder failed for '%s', falling back to legacy prompt: %s",
                    request.term,
                    exc,
                )

        # Legacy fallback: entire prompt in the user message
        return None, self._build_prompt(request)

    def _build_prompt(self, request: TranslationRequest) -> str:
        """Build translation prompt for Claude (legacy fallback).

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

        prompt = f"""You are translating Python programming terms to {language_name}.

TERM TO TRANSLATE: "{request.term}"
"""

        # Add deep context if available
        if request.context:
            prompt += f"""
DEEP CONTEXT:
{request.context}
"""

        # Add linguistic standards if available
        if request.linguistic_standards:
            prompt += f"""
LINGUISTIC STANDARDS FOR {language_name.upper()}:
{request.linguistic_standards}
"""

        prompt += f"""
TASK:
Translate "{request.term}" to {language_name} following these guidelines:
1. Focus on the CONCEPT, not word-for-word translation
2. Consider what native {language_name} speakers would naturally use in programming context
3. Preserve technical accuracy for Python programming
4. Use appropriate grammatical forms:
   - Action verbs (def, return, yield): Use infinitive form
   - State verbs (is, in, or): Use present tense
   - Nouns/types (int, str, list): Use singular form
5. Consider existing conventions in {language_name} programming communities

OUTPUT FORMAT (respond with ONLY valid JSON):
{{
  "translation": "the translated term",
  "word_type": "verb|noun|adjective|preposition|conjunction|etc",
  "form": "infinitive|present|singular|etc",
  "confidence": 0.95,
  "alternatives": ["alternative1", "alternative2"],
  "rationale": "Brief explanation of why this translation was chosen (2-3 sentences)"
}}

Important:
- Respond ONLY with the JSON object, no additional text before or after
- Do not wrap JSON in markdown code blocks
- Ensure all JSON is valid (proper quotes, no trailing commas)
"""

        return prompt

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON from Claude response.

        Claude sometimes wraps JSON in markdown code blocks, so we need
        to extract it carefully.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If JSON cannot be extracted or parsed
        """
        # Try to extract JSON from markdown code blocks first
        # Pattern: ```json\n{...}\n``` or ```\n{...}\n```
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
                raise ValueError(f"No JSON found in response: {response_text}")

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in response: {json_str}")
            raise ValueError(f"Failed to parse JSON: {e}") from e

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate actual cost based on token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        input_cost = input_tokens * self.INPUT_COST_PER_TOKEN
        output_cost = output_tokens * self.OUTPUT_COST_PER_TOKEN
        return input_cost + output_cost

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
        translation = lang_translations.get(term_lower, f"[MOCK_{term_lower}]")

        return Translation(
            translation=translation,
            alternatives=[],
            rationale="Mock translation for dry-run mode",
            word_type="verb",
            form="infinitive",
            model_name=self.get_model_name(),
            cost=0.0,
            input_tokens=100,
            output_tokens=50,
            confidence=1.0,
        )
