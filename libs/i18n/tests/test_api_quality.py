"""Tests for translation API quality validation."""

import pytest

from legesher_i18n.api.providers.base import TranslationResult
from legesher_i18n.api.quality_validator import QualityValidator


class TestQualityValidator:
    """Test quality validator."""

    @pytest.fixture
    def validator(self):
        """Create quality validator with default thresholds."""
        return QualityValidator(min_confidence=0.7, min_quality_score=7.0)

    def test_validate_good_result(self, validator):
        """Test validation of good quality result."""
        result = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            confidence=0.95,
            quality_score=9.5,
        )

        assert validator.validate(result, "Hello") is True

    def test_validate_low_confidence(self, validator):
        """Test validation fails for low confidence."""
        result = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            confidence=0.5,  # Below threshold
            quality_score=9.5,
        )

        assert validator.validate(result, "Hello") is False

    def test_validate_low_quality_score(self, validator):
        """Test validation fails for low quality score."""
        result = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="libretranslate",
            confidence=0.9,
            quality_score=6.0,  # Below threshold
        )

        assert validator.validate(result, "Hello") is False

    def test_validate_empty_translation(self, validator):
        """Test validation fails for empty translation."""
        result = TranslationResult(
            text="",
            source_lang="en",
            target_lang="es",
            provider="deepl",
        )

        assert validator.validate(result, "Hello") is False

    def test_validate_whitespace_only(self, validator):
        """Test validation fails for whitespace-only translation."""
        result = TranslationResult(
            text="   ",
            source_lang="en",
            target_lang="es",
            provider="deepl",
        )

        assert validator.validate(result, "Hello") is False

    def test_validate_identical_to_source(self):
        """Test validation of translation identical to source."""
        # Create validator that doesn't allow identical
        validator = QualityValidator(allow_identical=False)

        result = TranslationResult(
            text="This is a long text that is identical to source",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            quality_score=8.0,
        )

        # Should fail for long texts (>20 chars)
        assert (
            validator.validate(
                result, "This is a long text that is identical to source"
            )
            is False
        )

    def test_validate_identical_short_text(self):
        """Test validation allows identical for short text (e.g., keywords)."""
        # Create validator that doesn't allow identical
        validator = QualityValidator(allow_identical=False)

        result = TranslationResult(
            text="API",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            quality_score=8.0,
        )

        # Should pass for short texts (<=20 chars) - keywords often don't translate
        assert validator.validate(result, "API") is True

    def test_validate_no_confidence_score(self, validator):
        """Test validation when provider doesn't provide confidence."""
        result = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="libretranslate",
            confidence=None,  # Provider doesn't provide confidence
            quality_score=8.0,
        )

        # Should still pass based on quality score
        assert validator.validate(result, "Hello") is True

    def test_get_best_translation(self, validator):
        """Test selecting best translation from multiple results."""
        results = [
            TranslationResult(
                text="Hola",
                source_lang="en",
                target_lang="es",
                provider="libretranslate",
                confidence=0.8,
                quality_score=7.5,
            ),
            TranslationResult(
                text="Hola",
                source_lang="en",
                target_lang="es",
                provider="deepl",
                confidence=0.95,
                quality_score=9.5,
            ),
            TranslationResult(
                text="Hola",
                source_lang="en",
                target_lang="es",
                provider="google",
                confidence=0.9,
                quality_score=8.5,
            ),
        ]

        best = validator.get_best_translation(results, "Hello")

        # Should select DeepL (highest quality score)
        assert best is not None
        assert best.provider == "deepl"
        assert best.quality_score == 9.5

    def test_get_best_translation_all_invalid(self, validator):
        """Test get_best_translation when all results are invalid."""
        results = [
            TranslationResult(
                text="",  # Empty
                source_lang="en",
                target_lang="es",
                provider="deepl",
            ),
            TranslationResult(
                text="Hola",
                source_lang="en",
                target_lang="es",
                provider="google",
                quality_score=5.0,  # Too low
            ),
        ]

        best = validator.get_best_translation(results, "Hello")
        assert best is None

    def test_should_fallback(self, validator):
        """Test should_fallback decision."""
        # Good result - no fallback needed
        good_result = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            confidence=0.95,
            quality_score=9.5,
        )
        assert validator.should_fallback(good_result, "Hello") is False

        # Low quality - should fallback
        low_quality = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="libretranslate",
            quality_score=6.0,
        )
        assert validator.should_fallback(low_quality, "Hello") is True

        # Borderline quality - should consider fallback
        borderline = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="libretranslate",
            quality_score=7.5,  # Just above threshold, but borderline
        )
        assert validator.should_fallback(borderline, "Hello") is True

    def test_compare_results(self, validator):
        """Test comparing two results."""
        result1 = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            confidence=0.95,
            quality_score=9.5,
        )

        result2 = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="google",
            confidence=0.9,
            quality_score=8.5,
        )

        # DeepL should win (higher quality)
        better = validator.compare_results(result1, result2)
        assert better.provider == "deepl"

    def test_compare_results_same_quality(self, validator):
        """Test comparing results with same quality, different confidence."""
        result1 = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            confidence=0.95,
            quality_score=8.5,
        )

        result2 = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="google",
            confidence=0.85,
            quality_score=8.5,
        )

        # DeepL should win (higher confidence)
        better = validator.compare_results(result1, result2)
        assert better.provider == "deepl"

    def test_compare_results_one_invalid(self, validator):
        """Test comparing when one result is invalid."""
        valid = TranslationResult(
            text="Hola",
            source_lang="en",
            target_lang="es",
            provider="deepl",
            quality_score=8.0,
        )

        invalid = TranslationResult(
            text="",  # Empty
            source_lang="en",
            target_lang="es",
            provider="google",
        )

        # Should return the valid one
        better = validator.compare_results(valid, invalid)
        assert better.provider == "deepl"

        # Test reverse order too
        better = validator.compare_results(invalid, valid)
        assert better.provider == "deepl"
