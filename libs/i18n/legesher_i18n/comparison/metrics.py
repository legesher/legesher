"""Metrics calculator for translation comparison analysis.

This module provides comprehensive metrics and statistics for analyzing
translation comparison results across multiple languages and terms.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .models import ComparisonResult


@dataclass
class LanguageMetrics:
    """Metrics for a single language."""

    language: str
    total_terms: int
    perfect_agreement: int
    high_agreement: int  # 75%+
    medium_agreement: int  # 50-75%
    low_agreement: int  # <50%
    needs_review: int
    average_agreement: float
    sources_coverage: dict[str, int] = field(
        default_factory=dict
    )  # source -> term count
    word_type_conflicts: int = 0
    form_conflicts: int = 0
    length_conflicts: int = 0
    semantic_conflicts: int = 0

    def get_agreement_distribution(self) -> dict[str, float]:
        """Get percentage distribution of agreement levels."""
        if self.total_terms == 0:
            return {
                "perfect": 0.0,
                "high": 0.0,
                "medium": 0.0,
                "low": 0.0,
            }

        return {
            "perfect": (self.perfect_agreement / self.total_terms) * 100,
            "high": (self.high_agreement / self.total_terms) * 100,
            "medium": (self.medium_agreement / self.total_terms) * 100,
            "low": (self.low_agreement / self.total_terms) * 100,
        }

    def get_review_percentage(self) -> float:
        """Get percentage of terms needing review."""
        if self.total_terms == 0:
            return 0.0
        return (self.needs_review / self.total_terms) * 100


@dataclass
class SourceMetrics:
    """Metrics for a single translation source (claude, gpt4o, etc.)."""

    source: str
    total_translations: int
    average_confidence: float
    languages_covered: list[str] = field(default_factory=list)
    agreement_with_community: int = 0  # How often it agrees with community
    agreement_with_others: int = 0  # How often it agrees with other AI sources
    unique_translations: int = 0  # Translations only this source has
    word_type_distribution: dict[str, int] = field(default_factory=dict)


@dataclass
class CrossLanguageMetrics:
    """Metrics comparing across all languages."""

    total_languages: int
    total_terms: int
    total_comparisons: int
    overall_average_agreement: float
    best_language: str | None = None  # Language with highest agreement
    worst_language: str | None = None  # Language with lowest agreement
    most_consistent_source: str | None = None
    least_consistent_source: str | None = None
    languages_by_agreement: dict[str, float] = field(default_factory=dict)


class MetricsCalculator:
    """Calculate comprehensive metrics from comparison results."""

    def calculate_language_metrics(
        self, results: list[ComparisonResult]
    ) -> LanguageMetrics:
        """
        Calculate metrics for a single language.

        Args:
            results: List of ComparisonResult for one language

        Returns:
            LanguageMetrics with comprehensive statistics
        """
        if not results:
            return LanguageMetrics(
                language="unknown",
                total_terms=0,
                perfect_agreement=0,
                high_agreement=0,
                medium_agreement=0,
                low_agreement=0,
                needs_review=0,
                average_agreement=0.0,
            )

        language = results[0].language
        total_terms = len(results)

        # Agreement levels
        perfect = sum(1 for r in results if r.agreement_score >= 1.0)
        high = sum(1 for r in results if 0.75 <= r.agreement_score < 1.0)
        medium = sum(1 for r in results if 0.5 <= r.agreement_score < 0.75)
        low = sum(1 for r in results if r.agreement_score < 0.5)

        # Review needed
        needs_review = sum(1 for r in results if r.needs_review())

        # Average agreement
        avg_agreement = sum(r.agreement_score for r in results) / total_terms

        # Source coverage
        sources_coverage = defaultdict(int)
        for result in results:
            for source in result.translations.keys():
                sources_coverage[source] += 1

        # Conflict types
        word_type_conflicts = sum(1 for r in results if r.differences.word_type_differs)
        form_conflicts = sum(1 for r in results if r.differences.form_differs)
        length_conflicts = sum(
            1 for r in results if r.differences.length_differs_significantly
        )
        semantic_conflicts = sum(
            1 for r in results if r.differences.completely_different_words
        )

        return LanguageMetrics(
            language=language,
            total_terms=total_terms,
            perfect_agreement=perfect,
            high_agreement=high,
            medium_agreement=medium,
            low_agreement=low,
            needs_review=needs_review,
            average_agreement=avg_agreement,
            sources_coverage=dict(sources_coverage),
            word_type_conflicts=word_type_conflicts,
            form_conflicts=form_conflicts,
            length_conflicts=length_conflicts,
            semantic_conflicts=semantic_conflicts,
        )

    def calculate_source_metrics(
        self, source: str, results: list[ComparisonResult]
    ) -> SourceMetrics:
        """
        Calculate metrics for a single translation source.

        Args:
            source: Source name (e.g., "claude", "gpt4o")
            results: List of all ComparisonResult objects

        Returns:
            SourceMetrics with source-specific statistics
        """
        # Filter results that include this source
        source_translations = []
        languages = set()

        for result in results:
            if source in result.translations:
                source_translations.append(result.translations[source])
                languages.add(result.language)

        if not source_translations:
            return SourceMetrics(
                source=source,
                total_translations=0,
                average_confidence=0.0,
            )

        # Calculate metrics
        total = len(source_translations)
        avg_confidence = sum(t.confidence for t in source_translations) / total

        # Agreement with community
        agreement_with_community = 0
        for result in results:
            if source in result.translations and "community" in result.translations:
                if (
                    result.translations[source].translation
                    == result.translations["community"].translation
                ):
                    agreement_with_community += 1

        # Agreement with other AI sources
        agreement_with_others = 0
        for result in results:
            if source in result.translations:
                source_trans = result.translations[source].translation
                other_sources = [
                    s
                    for s in result.translations.keys()
                    if s != source and s != "community"
                ]
                for other in other_sources:
                    if result.translations[other].translation == source_trans:
                        agreement_with_others += 1
                        break  # Count once per term

        # Unique translations (only this source has this translation)
        unique = 0
        for result in results:
            if source in result.translations:
                source_trans = result.translations[source].translation
                other_trans = [
                    t.translation for s, t in result.translations.items() if s != source
                ]
                if source_trans not in other_trans:
                    unique += 1

        # Word type distribution
        word_types = Counter(t.word_type for t in source_translations if t.word_type)

        return SourceMetrics(
            source=source,
            total_translations=total,
            average_confidence=avg_confidence,
            languages_covered=sorted(list(languages)),
            agreement_with_community=agreement_with_community,
            agreement_with_others=agreement_with_others,
            unique_translations=unique,
            word_type_distribution=dict(word_types),
        )

    def calculate_cross_language_metrics(
        self, results_by_language: dict[str, list[ComparisonResult]]
    ) -> CrossLanguageMetrics:
        """
        Calculate metrics comparing across all languages.

        Args:
            results_by_language: Dict of language -> List[ComparisonResult]

        Returns:
            CrossLanguageMetrics with cross-language comparisons
        """
        if not results_by_language:
            return CrossLanguageMetrics(
                total_languages=0,
                total_terms=0,
                total_comparisons=0,
                overall_average_agreement=0.0,
            )

        # Calculate per-language averages
        languages_by_agreement = {}
        for lang, results in results_by_language.items():
            if results:
                avg = sum(r.agreement_score for r in results) / len(results)
                languages_by_agreement[lang] = avg

        # Overall statistics
        total_languages = len(results_by_language)
        total_terms = sum(len(results) for results in results_by_language.values())
        total_comparisons = total_terms

        # Overall average
        if total_terms > 0:
            all_scores = [
                r.agreement_score
                for results in results_by_language.values()
                for r in results
            ]
            overall_avg = sum(all_scores) / len(all_scores)
        else:
            overall_avg = 0.0

        # Best and worst languages
        best_lang = None
        worst_lang = None
        if languages_by_agreement:
            best_lang = max(languages_by_agreement, key=languages_by_agreement.get)
            worst_lang = min(languages_by_agreement, key=languages_by_agreement.get)

        # Most/least consistent sources
        all_results = [r for results in results_by_language.values() for r in results]
        sources = set()
        for result in all_results:
            sources.update(result.translations.keys())

        source_consistency = {}
        for source in sources:
            source_metrics = self.calculate_source_metrics(source, all_results)
            # Consistency = agreement with others / total translations
            if source_metrics.total_translations > 0:
                consistency = (
                    source_metrics.agreement_with_others
                    / source_metrics.total_translations
                )
                source_consistency[source] = consistency

        most_consistent = None
        least_consistent = None
        if source_consistency:
            most_consistent = max(source_consistency, key=source_consistency.get)
            least_consistent = min(source_consistency, key=source_consistency.get)

        return CrossLanguageMetrics(
            total_languages=total_languages,
            total_terms=total_terms,
            total_comparisons=total_comparisons,
            overall_average_agreement=overall_avg,
            best_language=best_lang,
            worst_language=worst_lang,
            most_consistent_source=most_consistent,
            least_consistent_source=least_consistent,
            languages_by_agreement=languages_by_agreement,
        )

    def get_top_disagreements(
        self, results: list[ComparisonResult], limit: int = 10
    ) -> list[ComparisonResult]:
        """
        Get top terms with most disagreement.

        Args:
            results: List of ComparisonResult objects
            limit: Maximum number to return

        Returns:
            List of ComparisonResult sorted by disagreement (lowest agreement first)
        """
        sorted_results = sorted(results, key=lambda r: r.agreement_score)
        return sorted_results[:limit]

    def get_terms_needing_review(
        self, results: list[ComparisonResult]
    ) -> list[ComparisonResult]:
        """
        Get all terms that need human review.

        Args:
            results: List of ComparisonResult objects

        Returns:
            List of ComparisonResult that need review
        """
        return [r for r in results if r.needs_review()]

    def get_conflict_summary(self, results: list[ComparisonResult]) -> dict[str, int]:
        """
        Get summary of conflict types.

        Args:
            results: List of ComparisonResult objects

        Returns:
            Dict with counts of each conflict type
        """
        return {
            "word_type_conflicts": sum(
                1 for r in results if r.differences.word_type_differs
            ),
            "form_conflicts": sum(1 for r in results if r.differences.form_differs),
            "length_conflicts": sum(
                1 for r in results if r.differences.length_differs_significantly
            ),
            "semantic_conflicts": sum(
                1 for r in results if r.differences.completely_different_words
            ),
            "total_with_conflicts": sum(
                1 for r in results if r.differences.has_differences()
            ),
        }

    def generate_summary(
        self, results_by_language: dict[str, list[ComparisonResult]]
    ) -> dict:
        """
        Generate comprehensive summary of all metrics.

        Args:
            results_by_language: Dict of language -> List[ComparisonResult]

        Returns:
            Dict with complete metrics summary
        """
        # Per-language metrics
        language_metrics = {}
        for lang, results in results_by_language.items():
            language_metrics[lang] = self.calculate_language_metrics(results)

        # Cross-language metrics
        cross_metrics = self.calculate_cross_language_metrics(results_by_language)

        # Source metrics (all sources)
        all_results = [r for results in results_by_language.values() for r in results]
        sources = set()
        for result in all_results:
            sources.update(result.translations.keys())

        source_metrics = {}
        for source in sources:
            source_metrics[source] = self.calculate_source_metrics(source, all_results)

        return {
            "cross_language": cross_metrics,
            "by_language": language_metrics,
            "by_source": source_metrics,
            "top_disagreements": self.get_top_disagreements(all_results),
            "needs_review": len(self.get_terms_needing_review(all_results)),
            "conflict_summary": self.get_conflict_summary(all_results),
        }
