"""Tests for metrics calculator."""

import pytest
import pytest_asyncio
from legesher_i18n.comparison.metrics import (
    MetricsCalculator,
    LanguageMetrics,
    SourceMetrics,
    CrossLanguageMetrics,
)
from legesher_i18n.comparison.comparator import TranslationComparator
from tests.comparison.fixtures.mock_translations import (
    get_mock_translations_for_term,
    get_mock_terms_for_language,
)


class TestLanguageMetrics:
    """Test language metrics calculation."""

    @pytest.fixture
    def calculator(self):
        """Create metrics calculator."""
        return MetricsCalculator()

    @pytest_asyncio.fixture
    async def spanish_results(self):
        """Create comparison results for Spanish."""
        comparator = TranslationComparator()
        terms = get_mock_terms_for_language("es")
        results = []
        for term in terms:
            translations = get_mock_translations_for_term(term, "es")
            if translations:
                result = await comparator.compare_term(term, "es", translations)
                results.append(result)
        return results

    @pytest.mark.asyncio
    async def test_calculate_language_metrics(self, calculator, spanish_results):
        """Test calculating metrics for a language."""
        metrics = calculator.calculate_language_metrics(spanish_results)

        assert isinstance(metrics, LanguageMetrics)
        assert metrics.language == "es"
        assert metrics.total_terms > 0
        assert metrics.perfect_agreement >= 0
        assert metrics.high_agreement >= 0
        assert metrics.medium_agreement >= 0
        assert metrics.low_agreement >= 0
        assert 0.0 <= metrics.average_agreement <= 1.0

    @pytest.mark.asyncio
    async def test_language_metrics_sources_coverage(self, calculator, spanish_results):
        """Test source coverage tracking."""
        metrics = calculator.calculate_language_metrics(spanish_results)

        # Should have coverage for multiple sources
        assert len(metrics.sources_coverage) > 0
        assert (
            "claude" in metrics.sources_coverage or "gpt4o" in metrics.sources_coverage
        )

    @pytest.mark.asyncio
    async def test_language_metrics_conflicts(self, calculator, spanish_results):
        """Test conflict tracking."""
        metrics = calculator.calculate_language_metrics(spanish_results)

        # Should detect some conflicts
        assert metrics.word_type_conflicts >= 0
        assert metrics.form_conflicts >= 0
        assert metrics.length_conflicts >= 0
        assert metrics.semantic_conflicts >= 0

    @pytest.mark.asyncio
    async def test_get_agreement_distribution(self, calculator, spanish_results):
        """Test agreement distribution calculation."""
        metrics = calculator.calculate_language_metrics(spanish_results)
        distribution = metrics.get_agreement_distribution()

        assert "perfect" in distribution
        assert "high" in distribution
        assert "medium" in distribution
        assert "low" in distribution

        # Percentages should sum to ~100
        total = sum(distribution.values())
        assert 99.0 <= total <= 101.0

    @pytest.mark.asyncio
    async def test_get_review_percentage(self, calculator, spanish_results):
        """Test review percentage calculation."""
        metrics = calculator.calculate_language_metrics(spanish_results)
        review_pct = metrics.get_review_percentage()

        assert 0.0 <= review_pct <= 100.0

    def test_empty_results(self, calculator):
        """Test metrics with no results."""
        metrics = calculator.calculate_language_metrics([])

        assert metrics.total_terms == 0
        assert metrics.average_agreement == 0.0
        assert metrics.get_review_percentage() == 0.0


class TestSourceMetrics:
    """Test source metrics calculation."""

    @pytest.fixture
    def calculator(self):
        """Create metrics calculator."""
        return MetricsCalculator()

    @pytest_asyncio.fixture
    async def spanish_results(self):
        """Create comparison results for Spanish."""
        comparator = TranslationComparator()
        terms = get_mock_terms_for_language("es")
        results = []
        for term in terms:
            translations = get_mock_translations_for_term(term, "es")
            if translations:
                result = await comparator.compare_term(term, "es", translations)
                results.append(result)
        return results

    @pytest.mark.asyncio
    async def test_calculate_source_metrics_claude(self, calculator, spanish_results):
        """Test calculating metrics for Claude."""
        metrics = calculator.calculate_source_metrics("claude", spanish_results)

        assert isinstance(metrics, SourceMetrics)
        assert metrics.source == "claude"
        assert metrics.total_translations > 0
        assert 0.0 <= metrics.average_confidence <= 1.0
        assert "es" in metrics.languages_covered

    @pytest.mark.asyncio
    async def test_source_metrics_agreement_tracking(self, calculator, spanish_results):
        """Test agreement tracking."""
        metrics = calculator.calculate_source_metrics("claude", spanish_results)

        # Should track agreements
        assert metrics.agreement_with_community >= 0
        assert metrics.agreement_with_others >= 0

    @pytest.mark.asyncio
    async def test_source_metrics_unique_translations(
        self, calculator, spanish_results
    ):
        """Test unique translation tracking."""
        metrics = calculator.calculate_source_metrics("claude", spanish_results)

        # Some unique translations expected
        assert metrics.unique_translations >= 0

    @pytest.mark.asyncio
    async def test_source_metrics_word_types(self, calculator, spanish_results):
        """Test word type distribution."""
        metrics = calculator.calculate_source_metrics("claude", spanish_results)

        # Should have word type distribution
        if metrics.word_type_distribution:
            assert (
                "verb" in metrics.word_type_distribution
                or "noun" in metrics.word_type_distribution
            )

    @pytest.mark.asyncio
    async def test_compare_sources(self, calculator, spanish_results):
        """Test comparing different sources."""
        claude_metrics = calculator.calculate_source_metrics("claude", spanish_results)
        gpt4o_metrics = calculator.calculate_source_metrics("gpt4o", spanish_results)

        # Both should have data
        assert claude_metrics.total_translations > 0
        assert gpt4o_metrics.total_translations > 0

        # They might have different confidence
        # (not asserting inequality as they could be equal)
        assert claude_metrics.average_confidence >= 0
        assert gpt4o_metrics.average_confidence >= 0

    def test_nonexistent_source(self, calculator):
        """Test metrics for non-existent source."""
        metrics = calculator.calculate_source_metrics("nonexistent", [])

        assert metrics.total_translations == 0
        assert metrics.average_confidence == 0.0


class TestCrossLanguageMetrics:
    """Test cross-language metrics calculation."""

    @pytest.fixture
    def calculator(self):
        """Create metrics calculator."""
        return MetricsCalculator()

    @pytest_asyncio.fixture
    async def multilanguage_results(self):
        """Create results for multiple languages."""
        comparator = TranslationComparator()
        results_by_language = {}

        for lang in ["es", "ar"]:
            terms = get_mock_terms_for_language(lang)
            results = []
            for term in terms:
                translations = get_mock_translations_for_term(term, lang)
                if translations:
                    result = await comparator.compare_term(term, lang, translations)
                    results.append(result)
            if results:
                results_by_language[lang] = results

        return results_by_language

    @pytest.mark.asyncio
    async def test_calculate_cross_language_metrics(
        self, calculator, multilanguage_results
    ):
        """Test cross-language metrics calculation."""
        metrics = calculator.calculate_cross_language_metrics(multilanguage_results)

        assert isinstance(metrics, CrossLanguageMetrics)
        assert metrics.total_languages > 0
        assert metrics.total_terms > 0
        assert 0.0 <= metrics.overall_average_agreement <= 1.0

    @pytest.mark.asyncio
    async def test_best_worst_languages(self, calculator, multilanguage_results):
        """Test best/worst language identification."""
        metrics = calculator.calculate_cross_language_metrics(multilanguage_results)

        # Should identify best and worst
        assert metrics.best_language is not None
        assert metrics.worst_language is not None
        assert metrics.best_language in multilanguage_results
        assert metrics.worst_language in multilanguage_results

    @pytest.mark.asyncio
    async def test_most_least_consistent_sources(
        self, calculator, multilanguage_results
    ):
        """Test source consistency identification."""
        metrics = calculator.calculate_cross_language_metrics(multilanguage_results)

        # Should identify consistent/inconsistent sources
        if metrics.most_consistent_source:
            assert metrics.most_consistent_source in [
                "claude",
                "gpt4o",
                "aya23",
                "community",
            ]
        if metrics.least_consistent_source:
            assert metrics.least_consistent_source in [
                "claude",
                "gpt4o",
                "aya23",
                "community",
            ]

    @pytest.mark.asyncio
    async def test_languages_by_agreement(self, calculator, multilanguage_results):
        """Test per-language agreement tracking."""
        metrics = calculator.calculate_cross_language_metrics(multilanguage_results)

        assert len(metrics.languages_by_agreement) > 0
        for lang, score in metrics.languages_by_agreement.items():
            assert 0.0 <= score <= 1.0

    def test_empty_cross_language_metrics(self, calculator):
        """Test cross-language metrics with no data."""
        metrics = calculator.calculate_cross_language_metrics({})

        assert metrics.total_languages == 0
        assert metrics.total_terms == 0
        assert metrics.overall_average_agreement == 0.0


class TestUtilityMethods:
    """Test utility methods."""

    @pytest.fixture
    def calculator(self):
        """Create metrics calculator."""
        return MetricsCalculator()

    @pytest_asyncio.fixture
    async def spanish_results(self):
        """Create comparison results for Spanish."""
        comparator = TranslationComparator()
        terms = get_mock_terms_for_language("es")
        results = []
        for term in terms:
            translations = get_mock_translations_for_term(term, "es")
            if translations:
                result = await comparator.compare_term(term, "es", translations)
                results.append(result)
        return results

    @pytest.mark.asyncio
    async def test_get_top_disagreements(self, calculator, spanish_results):
        """Test getting top disagreements."""
        top = calculator.get_top_disagreements(spanish_results, limit=5)

        # Should return sorted list
        assert len(top) <= 5
        # Should be sorted by agreement (lowest first)
        if len(top) > 1:
            assert top[0].agreement_score <= top[-1].agreement_score

    @pytest.mark.asyncio
    async def test_get_terms_needing_review(self, calculator, spanish_results):
        """Test getting terms needing review."""
        review_needed = calculator.get_terms_needing_review(spanish_results)

        # All should need review
        assert all(r.needs_review() for r in review_needed)

    @pytest.mark.asyncio
    async def test_get_conflict_summary(self, calculator, spanish_results):
        """Test conflict summary generation."""
        summary = calculator.get_conflict_summary(spanish_results)

        assert "word_type_conflicts" in summary
        assert "form_conflicts" in summary
        assert "length_conflicts" in summary
        assert "semantic_conflicts" in summary
        assert "total_with_conflicts" in summary

        # All should be non-negative
        assert all(v >= 0 for v in summary.values())


class TestComprehensiveSummary:
    """Test comprehensive summary generation."""

    @pytest.fixture
    def calculator(self):
        """Create metrics calculator."""
        return MetricsCalculator()

    @pytest_asyncio.fixture
    async def multilanguage_results(self):
        """Create results for multiple languages."""
        comparator = TranslationComparator()
        results_by_language = {}

        for lang in ["es", "ar"]:
            terms = get_mock_terms_for_language(lang)
            results = []
            for term in terms:
                translations = get_mock_translations_for_term(term, lang)
                if translations:
                    result = await comparator.compare_term(term, lang, translations)
                    results.append(result)
            if results:
                results_by_language[lang] = results

        return results_by_language

    @pytest.mark.asyncio
    async def test_generate_summary(self, calculator, multilanguage_results):
        """Test generating comprehensive summary."""
        summary = calculator.generate_summary(multilanguage_results)

        # Should have all sections
        assert "cross_language" in summary
        assert "by_language" in summary
        assert "by_source" in summary
        assert "top_disagreements" in summary
        assert "needs_review" in summary
        assert "conflict_summary" in summary

        # Cross-language section
        assert isinstance(summary["cross_language"], CrossLanguageMetrics)

        # By-language section
        for lang, metrics in summary["by_language"].items():
            assert isinstance(metrics, LanguageMetrics)

        # By-source section
        for source, metrics in summary["by_source"].items():
            assert isinstance(metrics, SourceMetrics)

        # Top disagreements
        assert isinstance(summary["top_disagreements"], list)

        # Needs review count
        assert isinstance(summary["needs_review"], int)
        assert summary["needs_review"] >= 0

        # Conflict summary
        assert isinstance(summary["conflict_summary"], dict)
