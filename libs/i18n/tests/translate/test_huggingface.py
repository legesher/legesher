"""Tests for the generic HuggingFace translation engine.

Tests cover:
- HFModelProfile dataclass and registry
- Default prompt builder
- HuggingFaceModel dry-run translations
- HuggingFaceAPIModel dry-run translations
- CLI argument validation (--hf-profile requirement)

All tests run without torch, transformers, or huggingface_hub installed.
"""

import pytest
from scripts.translate.models.base import TranslationRequest
from scripts.translate.models.hf_profiles import (
    DEFAULT_LANGUAGE_NAMES,
    HF_PROFILES,
    HFModelProfile,
    default_prompt_builder,
    get_profile,
    list_profiles,
    register_profile,
)
from scripts.translate.models.huggingface_api_model import HuggingFaceAPIModel
from scripts.translate.models.huggingface_model import HuggingFaceModel

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_profile():
    """A minimal profile for testing."""
    return HFModelProfile(
        name="test-model",
        model_id="TestOrg/test-model",
        architecture="causal",
        use_chat_template=True,
        generation_params={
            "temperature": 0.1,
            "max_new_tokens": 256,
            "top_p": 0.9,
            "do_sample": True,
        },
        dtype="float32",
        context_max_chars=500,
        standards_max_chars=300,
    )


@pytest.fixture
def sample_request():
    """A sample translation request."""
    return TranslationRequest(
        term="def",
        target_language="es",
        context="Python function definition keyword",
        linguistic_standards="Use infinitive verb form for function keywords.",
    )


@pytest.fixture
def sample_request_no_context():
    """A translation request without optional fields."""
    return TranslationRequest(
        term="print",
        target_language="ar",
    )


# ---------------------------------------------------------------------------
# HFModelProfile Tests
# ---------------------------------------------------------------------------


class TestHFModelProfile:
    """Test the HFModelProfile dataclass."""

    def test_creation_with_defaults(self):
        """Test profile creation with default values."""
        profile = HFModelProfile(name="test", model_id="org/model")
        assert profile.architecture == "causal"
        assert profile.use_chat_template is True
        assert profile.dtype == "bfloat16"
        assert profile.context_max_chars == 800
        assert profile.standards_max_chars == 500
        assert profile.prompt_builder is None
        assert profile.language_names is None

    def test_get_language_name_from_default(self, sample_profile):
        """Test language name resolution from DEFAULT_LANGUAGE_NAMES."""
        assert sample_profile.get_language_name("es") == "Spanish"
        assert sample_profile.get_language_name("ar") == "Arabic"
        assert sample_profile.get_language_name("ja") == "Japanese"

    def test_get_language_name_unknown_code(self, sample_profile):
        """Unknown codes fall back to uppercased code."""
        assert sample_profile.get_language_name("xx") == "XX"

    def test_get_language_name_custom_override(self):
        """Profile-level language_names override the default dict."""
        profile = HFModelProfile(
            name="custom",
            model_id="org/model",
            language_names={"es": "Castellano"},
        )
        assert profile.get_language_name("es") == "Castellano"
        # Unknown code still falls back
        assert profile.get_language_name("fr") == "FR"

    def test_generation_params_independence(self):
        """Each profile should have its own generation_params dict."""
        p1 = HFModelProfile(
            name="a",
            model_id="org/a",
            generation_params=dict({"temperature": 0.1}),
        )
        p2 = HFModelProfile(
            name="b",
            model_id="org/b",
            generation_params=dict({"temperature": 0.1}),
        )
        p1.generation_params["temperature"] = 0.9
        assert p2.generation_params["temperature"] == 0.1


# ---------------------------------------------------------------------------
# Profile Registry Tests
# ---------------------------------------------------------------------------


class TestProfileRegistry:
    """Test the HF_PROFILES registry."""

    def test_tiny_aya_profiles_registered(self):
        """All 4 Tiny Aya profiles should be registered at import time."""
        for variant in ("earth", "fire", "water", "global"):
            name = f"tiny-aya-{variant}"
            assert name in HF_PROFILES, f"Profile '{name}' not registered"

    def test_get_profile_existing(self):
        """get_profile returns the correct profile."""
        profile = get_profile("tiny-aya-earth")
        assert profile.name == "tiny-aya-earth"
        assert profile.model_id == "CohereLabs/tiny-aya-earth"
        assert profile.architecture == "causal"
        assert profile.use_chat_template is True

    def test_get_profile_missing_raises(self):
        """get_profile raises KeyError for unknown profiles."""
        with pytest.raises(
            KeyError, match="No HuggingFace model profile 'nonexistent'"
        ):
            get_profile("nonexistent")

    def test_list_profiles_sorted(self):
        """list_profiles returns sorted names."""
        names = list_profiles()
        assert names == sorted(names)
        assert "tiny-aya-earth" in names

    def test_register_profile_custom(self, sample_profile):
        """Custom profiles can be registered and retrieved."""
        register_profile(sample_profile)
        try:
            retrieved = get_profile("test-model")
            assert retrieved.model_id == "TestOrg/test-model"
        finally:
            # Clean up to avoid polluting other tests
            HF_PROFILES.pop("test-model", None)

    def test_tiny_aya_profiles_have_independent_params(self):
        """Each Tiny Aya profile should own its own generation_params dict."""
        earth = get_profile("tiny-aya-earth")
        fire = get_profile("tiny-aya-fire")
        assert earth.generation_params is not fire.generation_params

    def test_tiny_aya_profiles_have_correct_model_ids(self):
        """Verify model IDs match HuggingFace repo names."""
        expected = {
            "tiny-aya-earth": "CohereLabs/tiny-aya-earth",
            "tiny-aya-fire": "CohereLabs/tiny-aya-fire",
            "tiny-aya-water": "CohereLabs/tiny-aya-water",
            "tiny-aya-global": "CohereLabs/tiny-aya-global",
        }
        for name, model_id in expected.items():
            profile = get_profile(name)
            assert profile.model_id == model_id


# ---------------------------------------------------------------------------
# Default Prompt Builder Tests
# ---------------------------------------------------------------------------


class TestDefaultPromptBuilder:
    """Test the default prompt builder."""

    def test_basic_prompt_content(self, sample_request, sample_profile):
        """Prompt includes term, language, and JSON format instructions."""
        prompt = default_prompt_builder(sample_request, sample_profile)

        assert '"def"' in prompt
        assert "Spanish" in prompt
        assert '"translation"' in prompt
        assert "JSON" in prompt
        assert "Python identifier" in prompt

    def test_prompt_includes_context(self, sample_request, sample_profile):
        """Prompt includes context when available."""
        prompt = default_prompt_builder(sample_request, sample_profile)
        assert "Python function definition keyword" in prompt

    def test_prompt_includes_standards(self, sample_request, sample_profile):
        """Prompt includes linguistic standards when available."""
        prompt = default_prompt_builder(sample_request, sample_profile)
        assert "infinitive verb form" in prompt

    def test_prompt_no_context(self, sample_request_no_context, sample_profile):
        """Prompt omits context section when not provided."""
        prompt = default_prompt_builder(sample_request_no_context, sample_profile)
        assert "CONTEXT:" not in prompt
        assert "Arabic" in prompt

    def test_prompt_context_truncation(self, sample_profile):
        """Long context is truncated to profile.context_max_chars."""
        long_context = "A" * 1000
        request = TranslationRequest(
            term="if",
            target_language="fr",
            context=long_context,
        )
        prompt = default_prompt_builder(request, sample_profile)
        # context_max_chars=500, so should be truncated with "..."
        assert "..." in prompt
        # Full 1000-char context should NOT appear
        assert long_context not in prompt

    def test_prompt_context_disabled(self):
        """Profile with context_max_chars=None omits context entirely."""
        profile = HFModelProfile(
            name="no-ctx",
            model_id="org/model",
            context_max_chars=None,
        )
        request = TranslationRequest(
            term="for",
            target_language="de",
            context="Some context that should be ignored",
        )
        prompt = default_prompt_builder(request, profile)
        assert "CONTEXT:" not in prompt

    def test_prompt_uses_profile_language_name(self):
        """Custom language names from profile are used in prompt."""
        profile = HFModelProfile(
            name="custom-lang",
            model_id="org/model",
            language_names={"es": "Castellano"},
        )
        request = TranslationRequest(term="while", target_language="es")
        prompt = default_prompt_builder(request, profile)
        assert "Castellano" in prompt


# ---------------------------------------------------------------------------
# DEFAULT_LANGUAGE_NAMES Tests
# ---------------------------------------------------------------------------


class TestLanguageNames:
    """Test the DEFAULT_LANGUAGE_NAMES mapping."""

    def test_has_iso_639_1_codes(self):
        """Common ISO 639-1 codes should be present."""
        for code in ("en", "es", "fr", "de", "ar", "zh", "ja", "ko", "ru", "hi"):
            assert code in DEFAULT_LANGUAGE_NAMES

    def test_has_iso_639_3_codes(self):
        """Extended ISO 639-3 codes (used by Aya-101) should be present."""
        for code in ("amh", "ben", "urd", "tam"):
            assert code in DEFAULT_LANGUAGE_NAMES

    def test_has_tiny_aya_languages(self):
        """Languages specifically needed for Tiny Aya should be present."""
        assert DEFAULT_LANGUAGE_NAMES.get("am") == "Amharic"
        assert DEFAULT_LANGUAGE_NAMES.get("ur") == "Urdu"


# ---------------------------------------------------------------------------
# HuggingFaceModel Dry-Run Tests
# ---------------------------------------------------------------------------


class TestHuggingFaceModelDryRun:
    """Test HuggingFaceModel in dry-run mode (no torch/transformers needed)."""

    def test_dry_run_creation(self, sample_profile):
        """Model can be created in dry-run mode without torch."""
        model = HuggingFaceModel(profile=sample_profile, dry_run=True)
        assert model.dry_run is True

    def test_get_model_name(self, sample_profile):
        """get_model_name returns profile name."""
        model = HuggingFaceModel(profile=sample_profile, dry_run=True)
        assert model.get_model_name() == "test-model"

    def test_estimate_cost_zero(self, sample_profile, sample_request):
        """Local model cost is always 0."""
        model = HuggingFaceModel(profile=sample_profile, dry_run=True)
        assert model.estimate_cost(sample_request) == 0.0

    @pytest.mark.asyncio
    async def test_dry_run_known_translation(self):
        """Dry-run returns known mock translations for common terms."""
        profile = get_profile("tiny-aya-earth")
        model = HuggingFaceModel(profile=profile, dry_run=True)

        request = TranslationRequest(term="def", target_language="es")
        result = await model.translate(request)

        assert result.translation == "definir"
        assert result.model_name == "tiny-aya-earth"
        assert result.cost == 0.0

    @pytest.mark.asyncio
    async def test_dry_run_unknown_term_fallback(self):
        """Dry-run returns a mock placeholder for unknown terms."""
        profile = get_profile("tiny-aya-fire")
        model = HuggingFaceModel(profile=profile, dry_run=True)

        request = TranslationRequest(term="breakpoint", target_language="es")
        result = await model.translate(request)

        assert "MOCK_HF" in result.translation
        assert "tiny-aya-fire" in result.translation

    @pytest.mark.asyncio
    async def test_dry_run_amharic(self):
        """Dry-run works for Amharic (primary Tiny Aya use case)."""
        profile = get_profile("tiny-aya-earth")
        model = HuggingFaceModel(profile=profile, dry_run=True)

        request = TranslationRequest(term="def", target_language="am")
        result = await model.translate(request)

        assert result.translation == "ግለጽ"

    @pytest.mark.asyncio
    async def test_dry_run_urdu(self):
        """Dry-run works for Urdu (primary Tiny Aya use case)."""
        profile = get_profile("tiny-aya-fire")
        model = HuggingFaceModel(profile=profile, dry_run=True)

        request = TranslationRequest(term="return", target_language="ur")
        result = await model.translate(request)

        assert result.translation == "واپسی"


# ---------------------------------------------------------------------------
# HuggingFaceAPIModel Dry-Run Tests
# ---------------------------------------------------------------------------


class TestHuggingFaceAPIModelDryRun:
    """Test HuggingFaceAPIModel in dry-run mode (no huggingface_hub needed)."""

    def test_dry_run_creation(self, sample_profile):
        """API model can be created in dry-run mode without HF token."""
        model = HuggingFaceAPIModel(profile=sample_profile, dry_run=True)
        assert model.dry_run is True

    def test_get_model_name(self, sample_profile):
        """get_model_name returns prefixed profile name."""
        model = HuggingFaceAPIModel(profile=sample_profile, dry_run=True)
        assert model.get_model_name() == "hf-api-test-model"

    def test_estimate_cost_zero(self, sample_profile, sample_request):
        """API model cost is always 0 (free tier)."""
        model = HuggingFaceAPIModel(profile=sample_profile, dry_run=True)
        assert model.estimate_cost(sample_request) == 0.0

    @pytest.mark.asyncio
    async def test_dry_run_known_translation(self):
        """Dry-run returns known mock translations."""
        profile = get_profile("tiny-aya-earth")
        model = HuggingFaceAPIModel(profile=profile, dry_run=True)

        request = TranslationRequest(term="if", target_language="ar")
        result = await model.translate(request)

        assert result.translation == "إذا"
        assert result.model_name == "hf-api-tiny-aya-earth"

    @pytest.mark.asyncio
    async def test_dry_run_unknown_term_fallback(self):
        """Dry-run returns placeholder for unknown terms."""
        profile = get_profile("tiny-aya-water")
        model = HuggingFaceAPIModel(profile=profile, dry_run=True)

        request = TranslationRequest(term="yield", target_language="es")
        result = await model.translate(request)

        assert "MOCK_HF_API" in result.translation
        assert "tiny-aya-water" in result.translation

    def test_requires_token_without_dry_run(self, sample_profile, monkeypatch):
        """Non-dry-run requires HF token."""
        monkeypatch.delenv("HF_TOKEN", raising=False)
        with pytest.raises(ValueError, match="HuggingFace token required"):
            HuggingFaceAPIModel(profile=sample_profile, dry_run=False)

    def test_negative_rate_limit_raises(self, sample_profile):
        """Negative rate_limit_delay raises ValueError."""
        with pytest.raises(ValueError, match="rate_limit_delay must be non-negative"):
            HuggingFaceAPIModel(
                profile=sample_profile, dry_run=True, rate_limit_delay=-1.0
            )


# ---------------------------------------------------------------------------
# Pipeline Validation Tests
# ---------------------------------------------------------------------------


class TestPipelineValidation:
    """Test pipeline-level validation for HF model selection."""

    def test_hf_requires_profile(self, tmp_path):
        """--models hf without --hf-profile should raise ValueError."""
        from scripts.translate.pipeline import PipelineConfig, TranslationPipeline

        config = PipelineConfig(
            models=["hf"],
            dry_run=True,
            hf_profile=None,
            # The pipeline opens (and would CREATE) the real packaged
            # translations.db before this validation raises — keep every
            # construction pointed at tmp_path (CORE-1794).
            output_db=tmp_path / "pipeline.db",
        )
        with pytest.raises(ValueError, match="--models hf requires --hf-profile"):
            TranslationPipeline(config)

    def test_hf_api_requires_profile(self, tmp_path):
        """--models hf-api without --hf-profile should raise ValueError."""
        from scripts.translate.pipeline import PipelineConfig, TranslationPipeline

        config = PipelineConfig(
            models=["hf-api"],
            dry_run=True,
            hf_profile=None,
            output_db=tmp_path / "pipeline.db",
        )
        with pytest.raises(ValueError, match="--models hf-api requires --hf-profile"):
            TranslationPipeline(config)

    def test_tiny_aya_uses_default_variant(self, tmp_path):
        """--models tiny-aya without --hf-profile uses tiny-aya-earth."""
        from scripts.translate.pipeline import PipelineConfig, TranslationPipeline

        config = PipelineConfig(
            models=["tiny-aya"],
            dry_run=True,
            tiny_aya_variant="earth",
            # A default (None) output_db would open — and CREATE — the real
            # packaged translations.db, which is an untracked working copy
            # since CORE-1794 and must never be materialized by a test.
            output_db=tmp_path / "pipeline.db",
        )
        pipeline = TranslationPipeline(config)
        assert "tiny-aya" in pipeline.models

    def test_hf_with_profile_works(self, tmp_path):
        """--models hf with --hf-profile creates the model."""
        from scripts.translate.pipeline import PipelineConfig, TranslationPipeline

        config = PipelineConfig(
            models=["hf"],
            dry_run=True,
            hf_profile="tiny-aya-earth",
            output_db=tmp_path / "pipeline.db",
        )
        pipeline = TranslationPipeline(config)
        assert "hf" in pipeline.models
