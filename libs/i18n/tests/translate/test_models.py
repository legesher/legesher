"""Tests for translation models."""

import pytest
from scripts.translate.models.base import Translation, TranslationRequest
from scripts.translate.models.claude_model import ClaudeModel
from scripts.translate.models.aya_model import AyaModel


class TestTranslation:
    """Test Translation dataclass."""

    def test_translation_creation(self):
        """Test creating a translation."""
        t = Translation(
            translation="definir",
            alternatives=["función", "def"],
            rationale="Infinitive form is standard",
            word_type="verb",
            form="infinitive",
            model_name="claude-3.5-sonnet",
            cost=0.01,
            input_tokens=150,
            output_tokens=50,
            confidence=0.95,
        )

        assert t.translation == "definir"
        assert len(t.alternatives) == 2
        assert t.cost == 0.01
        assert t.confidence == 0.95

    def test_translation_to_dict(self):
        """Test converting translation to dict."""
        t = Translation(translation="imprimir", model_name="aya23")

        d = t.to_dict()
        assert isinstance(d, dict)
        assert d["translation"] == "imprimir"
        assert d["model_name"] == "aya23"
        assert "timestamp" in d


class TestTranslationRequest:
    """Test TranslationRequest dataclass."""

    def test_request_creation(self):
        """Test creating a translation request."""
        req = TranslationRequest(
            term="def",
            target_language="es",
            context="Deep context about 'def'...",
            linguistic_standards="Spanish uses infinitive verbs...",
        )

        assert req.term == "def"
        assert req.target_language == "es"
        assert req.context is not None
        assert req.linguistic_standards is not None


@pytest.mark.asyncio
class TestClaudeModel:
    """Test Claude model."""

    def test_initialization(self):
        """Test model initialization."""
        model = ClaudeModel(dry_run=True)

        assert model.get_model_name().startswith("claude")
        assert model.dry_run is True

    def test_estimate_cost(self):
        """Test cost estimation."""
        model = ClaudeModel(dry_run=True)

        request = TranslationRequest(
            term="def",
            target_language="es",
        )

        cost = model.estimate_cost(request)
        assert isinstance(cost, float)
        assert cost >= 0.0

    async def test_dry_run_translation(self):
        """Test dry-run translation (no real API call)."""
        model = ClaudeModel(dry_run=True)

        request = TranslationRequest(
            term="def",
            target_language="es",
        )

        translation = await model.translate(request)

        assert isinstance(translation, Translation)
        assert translation.translation == "definir"  # Mock translation
        assert translation.cost == 0.0  # No cost in dry-run
        assert translation.model_name.startswith("claude")

    def test_json_parsing(self):
        """The shared parser handles the response formats Claude produces.

        CORE-1804: ClaudeModel no longer carries its own JSON parser — the
        single implementation lives in ``legesher_i18n.llm_json``.
        """
        from legesher_i18n.llm_json import parse_json_object

        # Test with markdown code block
        response_with_block = """Here is the translation:
```json
{
  "translation": "imprimir",
  "word_type": "verb",
  "form": "infinitive",
  "confidence": 0.98,
  "alternatives": ["escribir", "mostrar"],
  "rationale": "Most natural Spanish verb"
}
```
That's my answer!"""

        result = parse_json_object(response_with_block)
        assert result["translation"] == "imprimir"
        assert result["word_type"] == "verb"
        assert result["confidence"] == 0.98

        # Test with raw JSON
        response_raw = """{
  "translation": "retornar",
  "confidence": 0.95
}"""

        result2 = parse_json_object(response_raw)
        assert result2["translation"] == "retornar"

    async def test_translate_delegates_to_provider(self):
        """CORE-1804: one Anthropic client — ClaudeModel calls the API-side
        provider's ``complete()`` instead of owning a client/retry loop."""
        from unittest.mock import AsyncMock, MagicMock

        provider = MagicMock()
        provider.complete = AsyncMock(
            return_value=(
                '{"translation": "definir", "word_type": "verb", '
                '"form": "infinitive", "confidence": 0.95, '
                '"alternatives": ["crear"], "rationale": "Standard form"}',
                150,
                50,
            )
        )

        model = ClaudeModel(api_key="sk-ant-test", provider=provider)
        request = TranslationRequest(term="def", target_language="es")

        translation = await model.translate(request)

        assert provider.complete.await_count == 1
        system_prompt, user_prompt = provider.complete.await_args.args
        assert "## Critical Rules" in system_prompt
        assert "`def`" in user_prompt
        assert translation.translation == "definir"
        assert translation.input_tokens == 150
        assert translation.output_tokens == 50
        # No rate configured in tests — cost is 0.0, never fabricated
        assert translation.cost == 0.0

    def test_prompt_pair_includes_context_and_standards(self):
        """Deep context and linguistic standards reach the user prompt."""
        model = ClaudeModel(dry_run=True)
        request = TranslationRequest(
            term="def",
            target_language="es",
            context="Deep context about 'def'...",
            linguistic_standards="Spanish uses infinitive verbs...",
        )

        system, user = model._build_prompt_pair(request)

        assert "DEEP CONTEXT:" in user
        assert "Deep context about 'def'..." in user
        assert "LINGUISTIC STANDARDS FOR SPANISH:" in user
        assert '"translation"' in user  # metadata JSON format
        assert "## Style Guide" in system


@pytest.mark.asyncio
class TestAyaModel:
    """Test Aya model."""

    def test_initialization(self):
        """Test model initialization."""
        model = AyaModel(dry_run=True)

        assert model.get_model_name().startswith("aya23")
        assert model.dry_run is True

    def test_estimate_cost(self):
        """Test cost estimation (should be 0 for local model)."""
        model = AyaModel(dry_run=True)

        request = TranslationRequest(
            term="return",
            target_language="ar",
        )

        cost = model.estimate_cost(request)
        assert cost == 0.0  # Aya is free (local)

    async def test_dry_run_translation(self):
        """Test dry-run translation."""
        model = AyaModel(dry_run=True)

        request = TranslationRequest(
            term="print",
            target_language="ar",
        )

        translation = await model.translate(request)

        assert isinstance(translation, Translation)
        assert translation.translation == "طباعة"  # Mock Arabic translation
        assert translation.cost == 0.0
        assert translation.model_name.startswith("aya23")
