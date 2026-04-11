"""Quality validation for translation results with automatic fallback logic."""

import logging

from .providers.base import TranslationResult

logger = logging.getLogger(__name__)


class QualityValidator:
    """
    Validates translation quality and selects best result from multiple providers.

    Checks:
    - Confidence scores (if provided by provider)
    - Expected quality scores for language pair
    - Empty/invalid translations
    - Identical source/target (potential failure)
    """

    def __init__(
        self,
        min_confidence: float = 0.7,
        min_quality_score: float = 7.0,
        allow_identical: bool = True,
    ):
        """
        Initialize quality validator.

        Args:
            min_confidence: Minimum confidence score (0-1) if provider supports it
            min_quality_score: Minimum expected quality score (0-10)
            allow_identical: Allow translation identical to source (for keywords)
        """
        self.min_confidence = min_confidence
        self.min_quality_score = min_quality_score
        self.allow_identical = allow_identical

    def validate(self, result: TranslationResult, source_text: str = "") -> bool:
        """
        Validate a single translation result.

        Args:
            result: Translation result to validate
            source_text: Original source text (for comparison)

        Returns:
            bool: True if translation passes quality checks
        """
        # Check if result exists and has content
        if not result or not result.text:
            logger.warning("Translation resulted in empty string")
            return False

        # Strip whitespace for validation
        translated = result.text.strip()
        if not translated:
            logger.warning("Translation resulted in whitespace-only string")
            return False

        # Check confidence score (if provided)
        if result.confidence is not None:
            if result.confidence < self.min_confidence:
                logger.warning(
                    f"Translation confidence too low: {result.confidence:.2f} < {self.min_confidence} "
                    f"(provider: {result.provider})"
                )
                return False

        # Check expected quality score for language pair
        if result.quality_score is not None:
            if result.quality_score < self.min_quality_score:
                logger.warning(
                    f"Translation quality score too low: {result.quality_score:.1f} < {self.min_quality_score} "
                    f"(provider: {result.provider}, pair: {result.source_lang}-{result.target_lang})"
                )
                return False

        # Check if translation is identical to source
        if source_text and not self.allow_identical:
            # For longer texts (>20 chars), identical might indicate failure
            if len(source_text) > 20 and translated == source_text:
                logger.warning(
                    f"Translation identical to source (potential failure): '{source_text[:50]}...'"
                )
                return False

        logger.debug(
            f"Translation passed validation: provider={result.provider}, "
            f"confidence={result.confidence}, quality={result.quality_score}"
        )
        return True

    def get_best_translation(
        self, results: list[TranslationResult], source_text: str = ""
    ) -> TranslationResult | None:
        """
        Select best translation from multiple provider results.

        Args:
            results: List of translation results from different providers
            source_text: Original source text

        Returns:
            Best TranslationResult, or None if all failed validation
        """
        if not results:
            return None

        # Filter to valid results
        valid_results = [r for r in results if self.validate(r, source_text)]

        if not valid_results:
            logger.error("All translation results failed validation")
            return None

        # Sort by quality score (primary) and confidence (secondary)
        valid_results.sort(
            key=lambda r: (
                r.quality_score if r.quality_score is not None else 0,
                r.confidence if r.confidence is not None else 0,
            ),
            reverse=True,
        )

        best = valid_results[0]
        logger.info(
            f"Selected best translation: provider={best.provider}, "
            f"quality={best.quality_score:.1f}, "
            f"confidence={best.confidence if best.confidence else 'N/A'}"
        )

        return best

    def should_fallback(self, result: TranslationResult, source_text: str = "") -> bool:
        """
        Determine if we should try fallback provider.

        Args:
            result: Translation result to check
            source_text: Original source text

        Returns:
            bool: True if should try fallback provider
        """
        # If validation fails, definitely try fallback
        if not self.validate(result, source_text):
            return True

        # If quality score is borderline, might want fallback for comparison
        if result.quality_score is not None:
            # If within 1 point of threshold, consider fallback
            if result.quality_score < self.min_quality_score + 1.0:
                logger.info(
                    f"Quality score borderline ({result.quality_score:.1f}), "
                    "considering fallback"
                )
                return True

        return False

    def compare_results(
        self, result1: TranslationResult, result2: TranslationResult
    ) -> TranslationResult:
        """
        Compare two translation results and return the better one.

        Args:
            result1: First translation result
            result2: Second translation result

        Returns:
            Better TranslationResult
        """
        # If one is invalid, return the other
        if not self.validate(result1, ""):
            return result2
        if not self.validate(result2, ""):
            return result1

        # Compare quality scores
        score1 = result1.quality_score if result1.quality_score is not None else 0
        score2 = result2.quality_score if result2.quality_score is not None else 0

        if score1 > score2:
            return result1
        elif score2 > score1:
            return result2

        # Quality scores equal, compare confidence
        conf1 = result1.confidence if result1.confidence is not None else 0
        conf2 = result2.confidence if result2.confidence is not None else 0

        if conf1 > conf2:
            return result1
        elif conf2 > conf1:
            return result2

        # Everything equal, prefer first provider (likely higher priority)
        return result1
