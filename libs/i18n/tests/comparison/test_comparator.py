"""Tests for translation comparison engine."""

import pytest
from unittest.mock import AsyncMock

from legesher_i18n.comparison.comparator import TranslationComparator
from legesher_i18n.comparison.models import Translation, DifferenceAnalysis
from tests.comparison.fixtures.mock_translations import (
    get_mock_translations_for_term,
    MOCK_SPANISH_TRANSLATIONS,
)


class TestAgreementCalculation:
    """Test agreement score calculation."""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance."""
        return TranslationComparator()

    def test_perfect_agreement(self, comparator):
        """Test perfect agreement (all sources identical)."""
        translations = get_mock_translations_for_term("print", "es")
        agreement = comparator.calculate_agreement(translations)
        assert agreement == 1.0

    def test_high_agreement(self, comparator):
        """Test high agreement (3/4 sources agree)."""
        translations = get_mock_translations_for_term("def", "es")
        agreement = comparator.calculate_agreement(translations)
        # 3 out of 4 sources agree on "definir"
        assert agreement == 0.75

    def test_no_agreement(self, comparator):
        """Test no agreement (all different)."""
        translations = get_mock_translations_for_term("return", "es")
        agreement = comparator.calculate_agreement(translations)
        # All 4 sources have different translations
        assert agreement == 0.25  # 1/4 (each unique translation counts as 1)

    def test_partial_agreement_with_missing_source(self, comparator):
        """Test agreement with missing source."""
        translations = get_mock_translations_for_term("yield", "es")
        agreement = comparator.calculate_agreement(translations)
        # Only 3 sources, each different
        assert agreement == pytest.approx(0.333, abs=0.01)

    def test_empty_translations(self, comparator):
        """Test agreement with no translations."""
        agreement = comparator.calculate_agreement({})
        assert agreement == 0.0


class TestDifferenceIdentification:
    """Test difference identification."""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance."""
        return TranslationComparator()

    def test_no_differences(self, comparator):
        """Test with identical translations."""
        translations = get_mock_translations_for_term("print", "es")
        diff = comparator.identify_differences(translations)

        assert diff.word_type_differs is False
        assert diff.form_differs is False
        assert diff.length_differs_significantly is False
        assert diff.completely_different_words is False
        assert diff.has_differences() is False

    def test_word_type_differs(self, comparator):
        """Test word type differences."""
        translations = get_mock_translations_for_term("class", "es")
        diff = comparator.identify_differences(translations)

        # gpt4o has "verb" while others have "noun"
        assert diff.word_type_differs is True

    def test_completely_different_words(self, comparator):
        """Test completely different translations."""
        translations = get_mock_translations_for_term("return", "es")
        diff = comparator.identify_differences(translations)

        # All 4 sources have different translations
        assert diff.completely_different_words is True

    def test_length_differs_significantly(self, comparator):
        """Test significant length differences."""
        translations = get_mock_translations_for_term("is", "es")
        diff = comparator.identify_differences(translations)

        # "es" (2 chars) vs "esexactamente" (13 chars)
        assert diff.length_differs_significantly is True

    def test_multiple_differences(self, comparator):
        """Test detection of multiple difference types."""
        translations = get_mock_translations_for_term("def", "es")
        diff = comparator.identify_differences(translations)

        # Has both word type differences and different words
        assert diff.word_type_differs is True
        assert diff.has_differences() is True


class TestLinguisticAnalysis:
    """Test linguistic analysis."""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance."""
        return TranslationComparator()

    def test_analyze_linguistics_basic(self, comparator):
        """Test basic linguistic analysis."""
        translations = get_mock_translations_for_term("print", "es")
        analysis = comparator.analyze_linguistics(translations)

        # All should have same properties
        assert len(analysis.word_types) == 4
        assert all(wt == "verb" for wt in analysis.word_types.values())
        assert analysis.get_dominant_word_type() == "verb"

    def test_analyze_linguistics_with_differences(self, comparator):
        """Test linguistic analysis with differences."""
        translations = get_mock_translations_for_term("def", "es")
        analysis = comparator.analyze_linguistics(translations)

        # Should detect different word types
        assert len(analysis.word_types) == 4
        assert analysis.get_dominant_word_type() == "verb"  # 3 verbs, 1 noun

    def test_script_detection_latin(self, comparator):
        """Test Latin script detection."""
        assert comparator._detect_script("definir") == "latin"
        assert comparator._detect_script("función") == "latin"

    def test_script_detection_arabic(self, comparator):
        """Test Arabic script detection."""
        assert comparator._detect_script("تعريف") == "arabic"
        assert comparator._detect_script("طباعة") == "arabic"

    def test_script_detection_chinese(self, comparator):
        """Test Chinese script detection."""
        assert comparator._detect_script("定义") == "chinese"
        assert comparator._detect_script("打印") == "chinese"

    def test_script_detection_empty(self, comparator):
        """Test script detection with empty string."""
        assert comparator._detect_script("") == "unknown"


class TestRecommendationGeneration:
    """Test recommendation generation."""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance."""
        return TranslationComparator()

    def test_recommendation_perfect_agreement(self, comparator):
        """Test recommendation with perfect agreement."""
        translations = get_mock_translations_for_term("print", "es")
        agreement = comparator.calculate_agreement(translations)
        diff = comparator.identify_differences(translations)
        ling = comparator.analyze_linguistics(translations)

        rec = comparator._generate_recommendation(translations, agreement, diff, ling)

        assert "Perfect agreement" in rec
        assert "imprimir" in rec

    def test_recommendation_high_agreement(self, comparator):
        """Test recommendation with high agreement."""
        translations = get_mock_translations_for_term("def", "es")
        agreement = comparator.calculate_agreement(translations)
        diff = comparator.identify_differences(translations)
        ling = comparator.analyze_linguistics(translations)

        rec = comparator._generate_recommendation(translations, agreement, diff, ling)

        assert "High agreement" in rec
        assert "definir" in rec

    def test_recommendation_community_support(self, comparator):
        """Test recommendation favoring community translation."""
        # Create translations where community has some support
        translations = get_mock_translations_for_term("class", "es")
        agreement = comparator.calculate_agreement(translations)
        diff = comparator.identify_differences(translations)
        ling = comparator.analyze_linguistics(translations)

        rec = comparator._generate_recommendation(translations, agreement, diff, ling)

        # Should recommend community translation "clase"
        assert "community" in rec or "clase" in rec

    def test_recommendation_no_agreement(self, comparator):
        """Test recommendation with no agreement."""
        translations = get_mock_translations_for_term("return", "es")
        agreement = comparator.calculate_agreement(translations)
        diff = comparator.identify_differences(translations)
        ling = comparator.analyze_linguistics(translations)

        rec = comparator._generate_recommendation(translations, agreement, diff, ling)

        assert "review" in rec.lower()


class TestCompareTerm:
    """Test full term comparison."""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance."""
        return TranslationComparator()

    @pytest.mark.asyncio
    async def test_compare_term_perfect_agreement(self, comparator):
        """Test comparing term with perfect agreement."""
        translations = get_mock_translations_for_term("print", "es")
        result = await comparator.compare_term("print", "es", translations)

        assert result.term == "print"
        assert result.language == "es"
        assert result.agreement_score == 1.0
        assert result.has_perfect_agreement()
        assert not result.needs_review()
        assert "Perfect agreement" in result.recommendation

    @pytest.mark.asyncio
    async def test_compare_term_high_agreement(self, comparator):
        """Test comparing term with high agreement."""
        translations = get_mock_translations_for_term("def", "es")
        result = await comparator.compare_term("def", "es", translations)

        assert result.term == "def"
        assert result.agreement_score == 0.75
        assert not result.has_perfect_agreement()
        assert result.sources_in_agreement() == 3
        assert result.get_most_common_translation() == "definir"

    @pytest.mark.asyncio
    async def test_compare_term_no_agreement(self, comparator):
        """Test comparing term with no agreement."""
        translations = get_mock_translations_for_term("return", "es")
        result = await comparator.compare_term("return", "es", translations)

        assert result.term == "return"
        assert result.agreement_score == 0.25
        assert len(result.get_unique_translations()) == 4
        assert result.needs_review()

    @pytest.mark.asyncio
    async def test_compare_term_with_anthropic(self):
        """Test comparison with Anthropic semantic analysis."""
        # Mock Anthropic provider
        mock_anthropic = AsyncMock()
        mock_anthropic.analyze_semantic_similarity = AsyncMock(
            return_value={
                "similarity_scores": {
                    "retornar": 0.95,
                    "devolver": 0.92,
                    "regresar": 0.88,
                    "volver": 0.85,
                },
                "most_natural": "devolver",
                "recommendation": "Use 'devolver'",
                "analysis": "All semantically similar",
            }
        )

        comparator = TranslationComparator(anthropic_provider=mock_anthropic)
        translations = get_mock_translations_for_term("return", "es")
        result = await comparator.compare_term("return", "es", translations)

        # Verify semantic analysis was called
        mock_anthropic.analyze_semantic_similarity.assert_called_once()

        # Check that semantic equivalence was set
        assert result.differences.semantic_equivalence is not None
        assert result.differences.semantic_equivalence > 0.8

    @pytest.mark.asyncio
    async def test_compare_term_handles_anthropic_error(self):
        """Test that comparison continues if Anthropic fails."""
        # Mock Anthropic provider that raises error
        mock_anthropic = AsyncMock()
        mock_anthropic.analyze_semantic_similarity = AsyncMock(
            side_effect=Exception("API error")
        )

        comparator = TranslationComparator(anthropic_provider=mock_anthropic)
        translations = get_mock_translations_for_term("return", "es")

        # Should not raise error
        result = await comparator.compare_term("return", "es", translations)

        assert result.term == "return"
        assert result.differences.semantic_equivalence is None  # Not set due to error


class TestCompareMultipleTerms:
    """Test comparing multiple terms."""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance."""
        return TranslationComparator()

    @pytest.mark.asyncio
    async def test_compare_multiple_terms(self, comparator):
        """Test comparing multiple terms."""
        terms = ["print", "def", "return"]
        translations_by_term = {
            term: get_mock_translations_for_term(term, "es") for term in terms
        }

        results = await comparator.compare_multiple_terms(
            terms, "es", translations_by_term
        )

        assert len(results) == 3
        assert results[0].term == "print"
        assert results[1].term == "def"
        assert results[2].term == "return"

    @pytest.mark.asyncio
    async def test_compare_multiple_terms_with_missing(self, comparator):
        """Test comparing with missing term data."""
        terms = ["print", "nonexistent", "def"]
        translations_by_term = {
            "print": get_mock_translations_for_term("print", "es"),
            "def": get_mock_translations_for_term("def", "es"),
        }

        results = await comparator.compare_multiple_terms(
            terms, "es", translations_by_term
        )

        # Should only return results for existing terms
        assert len(results) == 2
        assert all(r.term in ["print", "def"] for r in results)


class TestSummaryStatistics:
    """Test summary statistics generation."""

    @pytest.fixture
    def comparator(self):
        """Create comparator instance."""
        return TranslationComparator()

    @pytest.mark.asyncio
    async def test_summary_statistics(self, comparator):
        """Test generating summary statistics."""
        terms = ["print", "def", "return", "if"]
        translations_by_term = {
            term: get_mock_translations_for_term(term, "es") for term in terms
        }

        results = await comparator.compare_multiple_terms(
            terms, "es", translations_by_term
        )

        stats = comparator.get_summary_statistics(results)

        assert stats["total_terms"] == 4
        assert "perfect_agreement" in stats
        assert "high_agreement" in stats
        assert "low_agreement" in stats
        assert "needs_review" in stats
        assert "average_agreement" in stats
        assert 0.0 <= stats["average_agreement"] <= 1.0

    def test_summary_statistics_empty(self, comparator):
        """Test summary statistics with empty results."""
        stats = comparator.get_summary_statistics([])

        assert stats["total_terms"] == 0
        assert stats["perfect_agreement"] == 0
        assert stats["average_agreement"] == 0.0
