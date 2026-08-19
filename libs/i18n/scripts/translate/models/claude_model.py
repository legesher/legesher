"""Claude translation model — adapter over the API-side Anthropic provider.

CORE-1804: the generation pipeline used to carry its own Anthropic client,
retry loop, JSON parser, inline legacy prompt, and language-name map here,
duplicating the API-side ``AnthropicProvider``. This class is now a thin
``TranslationModel`` adapter: prompts come from ``PromptBuilder`` (the sole
prompt source), the API call goes through ``AnthropicProvider.complete()``
(the sole Anthropic client and retry loop), and responses are parsed by
``legesher_i18n.llm_json`` (the sole JSON parser).

The model ID defaults from ``legesher_i18n.model_config`` (override with
``LEGESHER_ANTHROPIC_MODEL``). Pricing is operator-configured via
``legesher_i18n/api/rates.py`` — without a configured rate, costs report as
0.0 and the pipeline's ``--max-budget`` guard cannot enforce.
"""

import logging
import os

from legesher_i18n.api.rates import cost_for_tokens
from legesher_i18n.llm_json import parse_json_object
from legesher_i18n.model_config import anthropic_model

from .base import Translation, TranslationModel, TranslationRequest

logger = logging.getLogger(__name__)


class ClaudeModel(TranslationModel):
    """Claude translation model for the generation pipeline.

    Delegates all model-call mechanics to the API-side
    ``AnthropicProvider`` so the Anthropic surface exists exactly once.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        dry_run: bool = False,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        target: str = "python",
        provider=None,
    ):
        """Initialize Claude model.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model ID. Defaults to the configured model
                (``LEGESHER_ANTHROPIC_MODEL`` env var, else the packaged
                default in ``legesher_i18n.model_config``).
            max_tokens: Maximum tokens in response
            dry_run: If True, don't make real API calls (for testing)
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Initial delay in seconds before first retry
                (exponential backoff)
            target: Programming-language target whose spec profile seasons
                the prompts (CORE-1608/CORE-1371); ``"python"`` keeps the
                historical wording byte-for-byte.
            provider: Optional pre-configured ``AnthropicProvider`` (tests
                inject a mock here).
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or anthropic_model()
        self.max_tokens = max_tokens
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.target = target

        if not self.dry_run and not self.api_key and provider is None:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set or api_key provided"
            )

        # PromptBuilder is REQUIRED — there is no legacy prompt to fall
        # back to (CORE-1804). A broken style-guide stack must stop the
        # generation run, never silently produce non-style-guide-aware
        # translations (CORE-1354).
        try:
            from legesher_i18n.style_guides import StyleGuideLoader
            from legesher_i18n.prompt_builder import PromptBuilder

            loader = StyleGuideLoader()
            self._prompt_builder = PromptBuilder(loader, target=self.target)
        except Exception as exc:
            raise RuntimeError(
                "PromptBuilder failed to initialize — the generation "
                "pipeline requires style-guide-aware prompts (CORE-1354) "
                f"and has no legacy fallback (CORE-1804): {exc}"
            ) from exc

        # The single Anthropic call path lives on the API-side provider.
        self._provider = provider
        if not self.dry_run and self._provider is None:
            from legesher_i18n.api.providers.anthropic import AnthropicProvider

            self._provider = AnthropicProvider(
                api_key=self.api_key,
                model=self.model,
                max_tokens=self.max_tokens,
            )

        if not self.dry_run and cost_for_tokens("anthropic", 1, 1) is None:
            logger.warning(
                "No anthropic rate configured (LEGESHER_RATES_FILE / "
                "LEGESHER_RATE_ANTHROPIC_*_PER_MTOK): costs will report as "
                "0.0 and --max-budget cannot enforce. See "
                "legesher_i18n/api/rates.py."
            )

        logger.info(
            f"Initialized Claude model: {self.model} "
            f"(dry_run={dry_run}, max_retries={max_retries})"
        )

    def get_model_name(self) -> str:
        """Get model name."""
        return f"claude-{self.model}"

    def get_model_version(self) -> str | None:
        """Exact API model id for provenance."""
        return self.model

    def estimate_cost(self, request: TranslationRequest) -> float:
        """Estimate the cost in USD for this translation request.

        Uses the operator-configured rate (``legesher_i18n/api/rates.py``).
        Returns 0.0 when no rate is configured — unknown, documented as
        such at init time.
        """
        system_prompt, user_prompt = self._build_prompt_pair(request)
        estimated_input_tokens = self._prompt_builder.estimate_tokens(
            system_prompt, user_prompt
        )
        estimated_output_tokens = 200  # Conservative estimate for JSON response

        cost = cost_for_tokens(
            "anthropic", estimated_input_tokens, estimated_output_tokens
        )
        return cost if cost is not None else 0.0

    async def translate(self, request: TranslationRequest) -> Translation:
        """Translate a term using Claude via the shared provider call path.

        Args:
            request: Translation request with term, language, and context

        Returns:
            Translation with result and metadata

        Raises:
            Exception: If the API call fails after all retries
        """
        if self.dry_run:
            return self._mock_translation(request)

        system_prompt, user_prompt = self._build_prompt_pair(request)

        raw_text, input_tokens, output_tokens = await self._provider.complete(
            system_prompt,
            user_prompt,
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
        )

        result_data = parse_json_object(raw_text)

        cost = cost_for_tokens("anthropic", input_tokens, output_tokens)
        cost = cost if cost is not None else 0.0

        logger.info(
            f"Claude translation: '{request.term}' -> "
            f"'{result_data.get('translation')}' ({request.target_language}) | "
            f"Tokens: {input_tokens}→{output_tokens} | Cost: ${cost:.4f}"
        )

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

    def _build_prompt_pair(self, request: TranslationRequest) -> tuple[str, str]:
        """Build the (system_prompt, user_prompt) pair via PromptBuilder."""
        return self._prompt_builder.build_term_prompt(
            request.term,
            request.target_language,
            role="keyword",
            deep_context=request.context,
            linguistic_standards=request.linguistic_standards,
        )

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
