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

        # Verify context was included in prompt
        call_args = provider.client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
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
    async def test_translate_calculates_cost(self, provider, mock_response):
        """Test that translation calculates costs."""
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        result = await provider.translate("def", "en", "es")

        # Cost calculation: (150 * 3 + 50 * 15) / 1M = $0.0012
        expected_cost = (150 * 3.0 + 50 * 15.0) / 1_000_000
        assert result.metadata["cost_usd"] == pytest.approx(expected_cost)

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
        assert result["cost_usd"] > 0
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

        with pytest.raises(ValueError, match="No JSON found"):
            provider._parse_json_response(content)

    def test_parse_json_malformed(self, provider):
        """Test parsing malformed JSON raises error."""
        content = '```json\n{"translation": broken}\n```'

        with pytest.raises(ValueError, match="Invalid JSON"):
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
        assert stats.cost_estimate_usd == 0.0

    @pytest.mark.asyncio
    async def test_get_usage_after_requests(self, provider, mock_response):
        """Test get_usage after making requests."""
        provider.client.messages.create = AsyncMock(return_value=mock_response)

        # Make a translation
        await provider.translate("def", "en", "es")

        stats = await provider.get_usage()

        assert stats.total_requests == 1
        assert stats.total_characters > 0
        assert stats.cost_estimate_usd > 0
        assert provider.name in stats.characters_by_provider

    @pytest.mark.asyncio
    async def test_get_usage_without_client(self, provider):
        """Test get_usage without client returns None."""
        provider.client = None

        stats = await provider.get_usage()
        assert stats is None


class TestPromptBuilding:
    """Test prompt construction."""

    def test_build_translation_prompt_basic(self, provider):
        """Test basic translation prompt."""
        prompt = provider._build_translation_prompt("def", "es", None)

        assert "Spanish" in prompt
        assert '"def"' in prompt
        assert "JSON" in prompt
        assert "translation" in prompt
        assert "ADDITIONAL CONTEXT" not in prompt

    def test_build_translation_prompt_with_context(self, provider):
        """Test translation prompt with context."""
        context = {
            "explanation": "Defines a function",
            "etymology": "From 'define'",
        }

        prompt = provider._build_translation_prompt("def", "es", context)

        assert "ADDITIONAL CONTEXT" in prompt
        assert "Defines a function" in prompt
        assert "From 'define'" in prompt

    def test_build_similarity_prompt(self, provider):
        """Test semantic similarity prompt."""
        prompt = provider._build_similarity_prompt("def", ["definir", "función"], "es")

        assert "Spanish" in prompt
        assert '"def"' in prompt
        assert "definir" in prompt
        assert "función" in prompt
        assert "similarity_scores" in prompt


class TestCostCalculation:
    """Test cost calculation."""

    def test_calculate_cost_basic(self, provider):
        """Test basic cost calculation."""
        # 1000 input tokens, 500 output tokens
        cost = provider._calculate_cost(1000, 500)

        # Expected: (1000 * 3 + 500 * 15) / 1M = $0.0105
        expected = (1000 * 3.0 + 500 * 15.0) / 1_000_000
        assert cost == pytest.approx(expected)

    def test_calculate_cost_zero(self, provider):
        """Test cost calculation with zero tokens."""
        cost = provider._calculate_cost(0, 0)
        assert cost == 0.0

    def test_cost_per_million_chars(self, provider):
        """Test cost_per_million_chars attribute."""
        # Should be approximately $4.5/1M chars
        assert provider.cost_per_million_chars == 4.5
