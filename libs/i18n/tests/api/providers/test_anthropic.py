"""Tests for Anthropic translation provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from legesher_i18n.api.providers.anthropic import AnthropicProvider
from legesher_i18n.api.providers.base import (
    TranslationResult,
    TranslationError,
    AuthenticationError,
    UnsupportedLanguageError,
)


@pytest.fixture
def mock_anthropic_client():
    """Mock AsyncAnthropic client."""
    with patch("legesher_i18n.api.providers.anthropic.AsyncAnthropic") as mock:
        yield mock


@pytest.fixture
def provider(mock_anthropic_client):
    """Create provider instance with mocked client."""
    return AnthropicProvider(api_key="sk-ant-test-key-123")


@pytest.fixture
def mock_response():
    """Create a mock Anthropic API response."""
    response = MagicMock()
    response.content = [
        MagicMock(
            text="""```json
{
  "translation": "definir",
  "word_type": "verb",
  "form": "infinitive",
  "confidence": 0.95,
  "alternatives": ["función", "def"],
  "rationale": "Infinitive verb form is standard for Python keywords"
}
```"""
        )
    ]
    response.usage = MagicMock(input_tokens=150, output_tokens=50)
    return response


class TestAnthropicProviderInit:
    """Test provider initialization."""

    def test_init_with_api_key(self, mock_anthropic_client):
        """Test initialization with API key."""
        provider = AnthropicProvider(api_key="sk-ant-test-key")
        assert provider.api_key == "sk-ant-test-key"
        assert provider.model == "claude-3-5-sonnet-20241022"
        assert provider.max_tokens == 1024
        assert provider.name == "anthropic"

    def test_init_with_env_var(self, mock_anthropic_client, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")
        provider = AnthropicProvider()
        assert provider.api_key == "sk-ant-env-key"

    def test_init_custom_model(self, mock_anthropic_client):
        """Test initialization with custom model."""
        provider = AnthropicProvider(
            api_key="sk-ant-test", model="claude-3-opus-20240229", max_tokens=2048
        )
        assert provider.model == "claude-3-opus-20240229"
        assert provider.max_tokens == 2048

    def test_init_without_anthropic_package(self):
        """Test initialization fails without anthropic package."""
        with patch("legesher_i18n.api.providers.anthropic.AsyncAnthropic", None):
            with pytest.raises(ImportError, match="anthropic package not installed"):
                AnthropicProvider(api_key="test")


class TestAvailability:
    """Test provider availability checks."""

    def test_is_available_with_valid_key(self, provider):
        """Test is_available with valid API key."""
        assert provider.is_available() is True

    def test_is_available_without_client(self, mock_anthropic_client):
        """Test is_available without initialized client."""
        provider = AnthropicProvider(api_key="sk-ant-test")
        provider.client = None
        assert provider.is_available() is False

    def test_is_available_invalid_key_format(self, mock_anthropic_client):
        """Test is_available with invalid key format."""
        provider = AnthropicProvider(api_key="invalid-key")
        assert provider.is_available() is False

    def test_supports_valid_language_pair(self, provider):
        """Test supports with valid language pair."""
        assert provider.supports("en", "es") is True
        assert provider.supports("en", "ar") is True
        assert provider.supports("en", "zh") is True

    def test_supports_invalid_language(self, provider):
        """Test supports with invalid language."""
        assert provider.supports("en", "xx") is False
        assert provider.supports("zz", "en") is False


class TestTranslation:
    """Test translation functionality."""

    @pytest.mark.asyncio
    async def test_translate_basic(self, provider, mock_response):
        """Test basic translation."""
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        result = await provider.translate("def", "en", "es")

        # Verify result
        assert isinstance(result, TranslationResult)
        assert result.text == "definir"
        assert result.source_lang == "en"
        assert result.target_lang == "es"
        assert result.provider == "anthropic"
        assert result.confidence == 0.95
        assert result.metadata["word_type"] == "verb"
        assert result.metadata["form"] == "infinitive"
        assert "alternatives" in result.metadata
        assert result.metadata["alternatives"] == ["función", "def"]

        # Verify API was called
        provider.client.messages.create.assert_called_once()
        call_args = provider.client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert len(call_args.kwargs["messages"]) == 1

    @pytest.mark.asyncio
    async def test_translate_with_context(self, provider, mock_response):
        """Test translation with additional context."""
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        context = {
            "explanation": "Keyword for defining functions",
            "etymology": "Short for 'define'",
        }

        result = await provider.translate("def", "en", "es", context=context)

        assert result.text == "definir"

        # Verify prompt was constructed — branch on which path was taken
        call_args = provider.client.messages.create.call_args
        kwargs = call_args.kwargs
        prompt = kwargs["messages"][0]["content"]

        if "system" in kwargs:
            # PromptBuilder path: system prompt has style guide markers
            assert "Critical Rules" in kwargs["system"]
            assert "`def`" in prompt  # term appears in identifier table
        else:
            # Legacy path: context embedded in prompt body
            assert "ADDITIONAL CONTEXT" in prompt
            assert "Keyword for defining functions" in prompt

    @pytest.mark.asyncio
    async def test_translate_tracks_usage(self, provider, mock_response):
        """Test that translation tracks token usage."""
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        await provider.translate("def", "en", "es")

        assert provider.total_input_tokens == 150
        assert provider.total_output_tokens == 50
        assert provider.total_requests == 1

    @pytest.mark.asyncio
    async def test_translate_reports_cost_from_configured_rate(
        self, provider, mock_response, monkeypatch
    ):
        """With a rate configured, the reported cost uses the operator's price."""
        from legesher_i18n.api import rates

        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", "3.0")
        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", "15.0")
        rates.reset_cache()
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        result = await provider.translate("def", "en", "es")

        assert result.metadata["cost_usd"] == pytest.approx(
            (150 * 3.0 + 50 * 15.0) / 1_000_000
        )

    @pytest.mark.asyncio
    async def test_translate_reports_unknown_cost_without_a_rate(
        self, provider, mock_response, monkeypatch
    ):
        """Tokens are still counted — only the price is withheld."""
        from legesher_i18n.api import rates

        monkeypatch.delenv("LEGESHER_RATES_FILE", raising=False)
        for var in (
            "LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK",
            "LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK",
        ):
            monkeypatch.delenv(var, raising=False)
        rates.reset_cache()
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        result = await provider.translate("def", "en", "es")

        assert result.metadata["cost_usd"] is None
        assert provider.total_input_tokens == 150

    @pytest.mark.asyncio
    async def test_translate_without_client(self, provider):
        """Test translation fails without client."""
        provider.client = None

        with pytest.raises(AuthenticationError, match="not initialized"):
            await provider.translate("def", "en", "es")

    @pytest.mark.asyncio
    async def test_translate_unsupported_language(self, provider):
        """Test translation with unsupported language."""
        with pytest.raises(UnsupportedLanguageError, match="does not support en-xx"):
            await provider.translate("def", "en", "xx")

    @pytest.mark.asyncio
    async def test_translate_api_error(self, provider):
        """Test translation handles API errors."""
        provider.client.messages.create = AsyncMock(
            side_effect=Exception("API connection failed")
        )

        with pytest.raises(TranslationError, match="translation failed"):
            await provider.translate("def", "en", "es")


class TestSemanticAnalysis:
    """Test semantic similarity analysis."""

    @pytest.fixture
    def mock_similarity_response(self):
        """Mock response for semantic analysis."""
        response = MagicMock()
        response.content = [
            MagicMock(
                text="""```json
{
  "similarity_scores": {
    "definir": 0.95,
    "función": 0.70,
    "def": 0.30
  },
  "most_natural": "definir",
  "recommendation": "Use 'definir' - most natural infinitive verb",
  "analysis": "All are valid but 'definir' is most idiomatic"
}
```"""
            )
        ]
        response.usage = MagicMock(input_tokens=200, output_tokens=80)
        return response

    @pytest.mark.asyncio
    async def test_semantic_similarity_basic(self, provider, mock_similarity_response):
        """Test basic semantic similarity analysis."""
        provider.client.messages.create = AsyncMock(
            return_value=mock_similarity_response
        )

        result = await provider.analyze_semantic_similarity(
            "def", ["definir", "función", "def"], "es"
        )

        # Verify result structure
        assert "similarity_scores" in result
        assert result["similarity_scores"]["definir"] == 0.95
        assert result["similarity_scores"]["función"] == 0.70
        assert result["most_natural"] == "definir"
        assert "recommendation" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_semantic_similarity_tracks_cost(
        self, provider, mock_similarity_response
    ):
        """Test semantic analysis tracks costs."""
        provider.client.messages.create = AsyncMock(
            return_value=mock_similarity_response
        )

        result = await provider.analyze_semantic_similarity(
            "def", ["definir", "función"], "es"
        )

        assert "cost_usd" in result
        # Reported, but unknown until the operator configures a rate.
        assert result["cost_usd"] is None
        assert provider.total_input_tokens == 200
        assert provider.total_output_tokens == 80

    @pytest.mark.asyncio
    async def test_semantic_similarity_without_client(self, provider):
        """Test semantic analysis fails without client."""
        provider.client = None

        with pytest.raises(AuthenticationError):
            await provider.analyze_semantic_similarity("def", ["definir"], "es")


class TestJSONParsing:
    """Test JSON parsing from various formats."""

    def test_parse_json_with_code_block(self, provider):
        """Test parsing JSON from markdown code block."""
        content = """Here is the translation:
```json
{
  "translation": "imprimir",
  "confidence": 0.99
}
```
Hope that helps!"""

        result = provider._parse_json_response(content)
        assert result["translation"] == "imprimir"
        assert result["confidence"] == 0.99

    def test_parse_json_without_language_tag(self, provider):
        """Test parsing JSON from code block without language tag."""
        content = """```
{
  "translation": "devolver"
}
```"""

        result = provider._parse_json_response(content)
        assert result["translation"] == "devolver"

    def test_parse_raw_json(self, provider):
        """Test parsing raw JSON without code block."""
        content = '{"translation": "clase", "confidence": 0.95}'

        result = provider._parse_json_response(content)
        assert result["translation"] == "clase"
        assert result["confidence"] == 0.95

    def test_parse_json_with_newlines(self, provider):
        """Test parsing JSON with newlines."""
        content = """```json
{
  "translation": "retornar",
  "word_type": "verb",
  "alternatives": [
    "devolver",
    "regresar"
  ]
}
```"""

        result = provider._parse_json_response(content)
        assert result["translation"] == "retornar"
        assert len(result["alternatives"]) == 2

    def test_parse_json_invalid(self, provider):
        """Test parsing invalid JSON raises error."""
        content = "This is not JSON at all"

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            provider._parse_json_response(content)

    def test_parse_json_malformed(self, provider):
        """Unrepairable JSON with no extractable fields raises."""
        content = "```json\n{this is: not, even close}\n```"

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            provider._parse_json_response(content)


class TestUsageStats:
    """Test usage statistics tracking."""

    @pytest.mark.asyncio
    async def test_get_usage_no_requests(self, provider):
        """Test get_usage with no requests made."""
        stats = await provider.get_usage()

        assert stats is not None
        assert stats.total_requests == 0
        assert stats.total_characters == 0
        # No rate configured — cost is unknown, never a fabricated zero.
        assert stats.cost_estimate_usd is None

    @pytest.mark.asyncio
    async def test_get_usage_after_requests(self, provider, mock_response):
        """Test get_usage after making requests."""
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        # Make a translation
        await provider.translate("def", "en", "es")

        stats = await provider.get_usage()

        assert stats.total_requests == 1
        assert stats.total_characters > 0
        # Still unknown: usage is measured, price is not ours to assume.
        assert stats.cost_estimate_usd is None
        assert provider.name in stats.characters_by_provider

    @pytest.mark.asyncio
    async def test_get_usage_without_client(self, provider):
        """Test get_usage without client returns None."""
        provider.client = None

        stats = await provider.get_usage()
        assert stats is None


class TestPromptBuilding:
    """Test prompt construction (PromptBuilder is the sole source, CORE-1804)."""

    @pytest.mark.asyncio
    async def test_context_free_translate_uses_prompt_builder(
        self, provider, mock_response
    ):
        """No-context calls go through the PromptBuilder term prompt."""
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        result = await provider.translate("def", "en", "es")

        kwargs = provider.client.messages.create.call_args.kwargs
        assert "system" in kwargs  # PromptBuilder always produces a system prompt
        assert "## Critical Rules" in kwargs["system"]
        assert "`def`" in kwargs["messages"][0]["content"]
        assert result.metadata["prompt_source"] == "prompt_builder"

    @pytest.mark.asyncio
    async def test_prompt_builder_failure_is_loud_and_flagged(
        self, provider, mock_response, caplog
    ):
        """PromptBuilder failure warns and flags the result (CORE-1804)."""
        import logging

        provider._prompt_builder = None
        response = MagicMock()
        response.content = [MagicMock(text="definir")]
        response.usage = MagicMock(input_tokens=10, output_tokens=5)
        provider.client.messages.create = AsyncMock(return_value=response)

        with caplog.at_level(logging.WARNING):
            result = await provider.translate("def", "en", "es")

        assert result.metadata["prompt_source"] == "legacy_fallback"
        assert result.text == "definir"
        assert any(
            "PromptBuilder unavailable" in record.message for record in caplog.records
        )

    def test_no_legacy_prompt_surface_remains(self, provider):
        """The inline legacy prompt builder is deleted (CORE-1804)."""
        assert not hasattr(provider, "_build_translation_prompt")

    def test_build_similarity_prompt(self, provider):
        """Test semantic similarity prompt."""
        prompt = provider._build_similarity_prompt("def", ["definir", "función"], "es")

        assert "Spanish" in prompt
        assert '"def"' in prompt
        assert "definir" in prompt
        assert "función" in prompt
        assert "similarity_scores" in prompt


@pytest.fixture(autouse=True)
def _isolate_rate_config(monkeypatch):
    """Rates are process-global and cached; isolate them per test.

    Without this, a test that configures a rate leaves it configured for every
    test after it, and the failure surfaces somewhere unrelated.
    """
    from legesher_i18n.api import rates

    monkeypatch.delenv("LEGESHER_RATES_FILE", raising=False)
    for key in [
        k for k in list(__import__("os").environ) if k.startswith("LEGESHER_RATE_")
    ]:
        monkeypatch.delenv(key, raising=False)
    rates.reset_cache()
    yield
    rates.reset_cache()


class TestCostCalculation:
    """Cost is operator-configured, never inferred.

    Legesher ships no rates. Prices change without notice and differ by
    contract, so a hardcoded figure is wrong the moment a provider updates a
    price list — quietly, and by a ratio nobody notices. An operator who wants
    cost reporting supplies the prices they are actually billed.
    """

    def test_no_rate_configured_means_unknown_not_free(self, provider, monkeypatch):
        from legesher_i18n.api import rates

        monkeypatch.delenv("LEGESHER_RATES_FILE", raising=False)
        rates.reset_cache()

        assert rates.cost_for_tokens(provider.name, 1000, 500) is None
        assert rates.format_cost(None) == "unknown"

    def test_configured_rate_is_applied(self, provider, monkeypatch):
        from legesher_i18n.api import rates

        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", "3.0")
        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", "15.0")
        rates.reset_cache()

        cost = rates.cost_for_tokens("anthropic", 1000, 500)
        assert cost == pytest.approx((1000 * 3.0 + 500 * 15.0) / 1_000_000)

    def test_half_configured_rate_reports_unknown(self, monkeypatch):
        """Under-reporting is the failure a budget guard can least afford."""
        from legesher_i18n.api import rates

        monkeypatch.delenv("LEGESHER_RATES_FILE", raising=False)
        monkeypatch.setenv("LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK", "3.0")
        monkeypatch.delenv("LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK", raising=False)
        rates.reset_cache()

        assert rates.cost_for_tokens("anthropic", 1000, 500) is None

    def test_provider_carries_no_rate_constants(self, provider):
        assert not hasattr(provider, "cost_per_million_chars")
        assert not hasattr(provider, "input_cost_per_token")
