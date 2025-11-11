"""Translation comparison engine.

This module provides the core logic for comparing translations from
multiple sources (Claude, GPT-4o, Aya 23, community) and generating
detailed comparison results with recommendations.
"""

import logging
from collections import Counter
from typing import Any, Dict, Optional

from .models import (
    ComparisonResult,
    DifferenceAnalysis,
    LinguisticAnalysis,
    Translation,
)
from ..api.providers.anthropic import AnthropicProvider

logger = logging.getLogger(__name__)


class TranslationComparator:
    """Compare translations from multiple sources."""

    def __init__(self, anthropic_provider: Optional[AnthropicProvider] = None):
        """
        Initialize comparator.

        Args:
            anthropic_provider: Optional Anthropic provider for semantic analysis
                              If provided, will use Claude to analyze semantic similarity
                              when translations differ significantly.
        """
        self.anthropic = anthropic_provider

    async def compare_term(
        self,
        term: str,
        language: str,
        translations: Dict[str, Translation],
    ) -> ComparisonResult:
        """
        Compare translations for a single term.

        Args:
            term: Python term (e.g., "def")
            language: Target language (e.g., "es")
            translations: Dict of source -> Translation

        Returns:
            ComparisonResult with full analysis

        Example:
            >>> comparator = TranslationComparator()
            >>> translations = {
            ...     "claude": Translation("def", "definir", "claude", "es"),
            ...     "gpt4o": Translation("def", "función", "gpt4o", "es"),
            ... }
            >>> result = await comparator.compare_term("def", "es", translations)
            >>> print(result.agreement_score)
            0.5
        """
        # Calculate agreement score
        agreement = self.calculate_agreement(translations)

        # Identify differences
        differences = self.identify_differences(translations)

        # Analyze linguistic properties
        linguistic = self.analyze_linguistics(translations)

        # Use Claude for semantic analysis if available and needed
        if self.anthropic and differences.completely_different_words:
            translation_texts = [t.translation for t in translations.values()]
            try:
                semantic_result = await self.anthropic.analyze_semantic_similarity(
                    term, translation_texts, language
                )

                # Calculate average similarity from scores
                similarity_scores = semantic_result.get("similarity_scores", {})
                if similarity_scores:
                    avg_similarity = sum(similarity_scores.values()) / len(
                        similarity_scores
                    )
                    differences.semantic_equivalence = avg_similarity
            except Exception as e:
                # If semantic analysis fails, continue without it
                logger.warning(
                    f"Semantic analysis failed for term '{term}' in language '{language}': {e}"
                )
                differences.semantic_equivalence = None

        # Generate recommendation
        recommendation = self._generate_recommendation(
            translations, agreement, differences, linguistic
        )

        return ComparisonResult(
            term=term,
            language=language,
            translations=translations,
            agreement_score=agreement,
            differences=differences,
            linguistic_analysis=linguistic,
            recommendation=recommendation,
        )

    def calculate_agreement(self, translations: Dict[str, Translation]) -> float:
        """
        Calculate agreement score 0.0-1.0.

        Perfect agreement (all identical): 1.0
        Partial agreement: Proportion of sources agreeing with most common
        No agreement (all different): Based on number of sources

        Args:
            translations: Dict of source -> Translation

        Returns:
            float: Agreement score from 0.0 (no agreement) to 1.0 (perfect)

        Example:
            >>> t1 = Translation("def", "definir", "claude", "es")
            >>> t2 = Translation("def", "definir", "gpt4o", "es")
            >>> t3 = Translation("def", "función", "aya23", "es")
            >>> comparator.calculate_agreement({"claude": t1, "gpt4o": t2, "aya23": t3})
            0.6666666666666666
        """
        if not translations:
            return 0.0

        # Count unique translations
        translation_texts = [t.translation for t in translations.values()]
        unique = set(translation_texts)

        if len(unique) == 1:
            return 1.0  # Perfect agreement

        # Calculate based on most common translation
        counts = Counter(translation_texts)
        most_common_count = counts.most_common(1)[0][1]

        return most_common_count / len(translations)

    def identify_differences(
        self, translations: Dict[str, Translation]
    ) -> DifferenceAnalysis:
        """
        Identify and categorize differences.

        Args:
            translations: Dict of source -> Translation

        Returns:
            DifferenceAnalysis with categorized differences
        """
        # Check word types
        word_types = [t.word_type for t in translations.values() if t.word_type]
        word_type_differs = len(set(word_types)) > 1 if word_types else False

        # Check forms
        forms = [t.form for t in translations.values() if t.form]
        form_differs = len(set(forms)) > 1 if forms else False

        # Check lengths
        lengths = [len(t.translation) for t in translations.values()]
        avg_length = sum(lengths) / len(lengths) if lengths else 0

        # Consider length differs significantly if any translation is >50% different from avg
        length_differs_significantly = (
            any(abs(length - avg_length) > avg_length * 0.5 for length in lengths)
            if avg_length > 0
            else False
        )

        # Check if completely different words
        translation_texts = [t.translation for t in translations.values()]
        completely_different = len(set(translation_texts)) == len(translation_texts)

        return DifferenceAnalysis(
            word_type_differs=word_type_differs,
            form_differs=form_differs,
            length_differs_significantly=length_differs_significantly,
            completely_different_words=completely_different,
        )

    def analyze_linguistics(
        self, translations: Dict[str, Translation]
    ) -> LinguisticAnalysis:
        """
        Analyze linguistic properties.

        Args:
            translations: Dict of source -> Translation

        Returns:
            LinguisticAnalysis with linguistic metadata
        """
        word_types = {}
        forms = {}
        lengths = {}
        scripts = {}

        for source, t in translations.items():
            if t.word_type:
                word_types[source] = t.word_type
            if t.form:
                forms[source] = t.form
            lengths[source] = len(t.translation)
            scripts[source] = self._detect_script(t.translation)

        return LinguisticAnalysis(
            word_types=word_types,
            forms=forms,
            lengths=lengths,
            scripts=scripts,
        )

    def _detect_script(self, text: str) -> str:
        """
        Detect script type (latin, arabic, cyrillic, etc.).

        Args:
            text: Text to analyze

        Returns:
            str: Script type name
        """
        if not text:
            return "unknown"

        # Simple detection based on Unicode ranges
        first_char = ord(text[0])

        if 0x0600 <= first_char <= 0x06FF:
            return "arabic"
        elif 0x4E00 <= first_char <= 0x9FFF:
            return "chinese"
        elif 0x0400 <= first_char <= 0x04FF:
            return "cyrillic"
        elif 0x0041 <= first_char <= 0x007A or 0x00C0 <= first_char <= 0x024F:
            return "latin"
        elif 0x3040 <= first_char <= 0x309F:
            return "hiragana"
        elif 0x30A0 <= first_char <= 0x30FF:
            return "katakana"
        elif 0x0E00 <= first_char <= 0x0E7F:
            return "thai"
        elif 0x0900 <= first_char <= 0x097F:
            return "devanagari"
        else:
            return "other"

    def _generate_recommendation(
        self,
        translations: Dict[str, Translation],
        agreement: float,
        differences: DifferenceAnalysis,
        linguistic: LinguisticAnalysis,
    ) -> str:
        """
        Generate recommendation based on analysis.

        Args:
            translations: Dict of source -> Translation
            agreement: Agreement score
            differences: Difference analysis
            linguistic: Linguistic analysis

        Returns:
            str: Human-readable recommendation
        """
        # Perfect agreement
        if agreement >= 1.0:
            translation = list(translations.values())[0].translation
            return f"Perfect agreement across all sources - use '{translation}' with confidence"

        # High agreement (75%+)
        if agreement >= 0.75:
            # Find most common translation
            translation_texts = [t.translation for t in translations.values()]
            counts = Counter(translation_texts)
            most_common = counts.most_common(1)[0][0]
            agreeing_sources = [
                s for s, t in translations.items() if t.translation == most_common
            ]
            sources_str = ", ".join(agreeing_sources)
            return f"High agreement - use '{most_common}' (agreed by {sources_str})"

        # Community translation exists and has some support
        if "community" in translations:
            community_trans = translations["community"].translation
            support_count = sum(
                1 for t in translations.values() if t.translation == community_trans
            )
            if support_count >= 2:
                return f"Use community translation '{community_trans}' - has support from {support_count} sources"

        # Check if word type issue
        if differences.word_type_differs:
            dominant_type = linguistic.get_dominant_word_type()
            if dominant_type:
                matching = [
                    (s, t)
                    for s, t in translations.items()
                    if t.word_type == dominant_type
                ]
                if matching:
                    source, trans = matching[0]
                    return f"Word type differs - recommend '{trans.translation}' ({dominant_type} form from {source})"

        # Low agreement - need review
        unique_count = len(set(t.translation for t in translations.values()))
        if unique_count == len(translations):
            return (
                f"No agreement - all {unique_count} sources differ. "
                "Requires human review and semantic analysis."
            )

        return f"Low agreement ({agreement:.1%}) - requires human review to determine best translation"

    async def compare_multiple_terms(
        self,
        terms: list[str],
        language: str,
        translations_by_term: Dict[str, Dict[str, Translation]],
    ) -> list[ComparisonResult]:
        """
        Compare translations for multiple terms.

        Args:
            terms: List of Python terms to compare
            language: Target language
            translations_by_term: Dict of term -> (source -> Translation)

        Returns:
            List of ComparisonResult objects
        """
        results = []
        for term in terms:
            if term in translations_by_term:
                result = await self.compare_term(
                    term, language, translations_by_term[term]
                )
                results.append(result)
        return results

    def get_summary_statistics(self, results: list[ComparisonResult]) -> Dict[str, Any]:
        """
        Get summary statistics for a list of comparison results.

        Args:
            results: List of ComparisonResult objects

        Returns:
            Dict with summary statistics
        """
        if not results:
            return {
                "total_terms": 0,
                "perfect_agreement": 0,
                "high_agreement": 0,
                "low_agreement": 0,
                "needs_review": 0,
                "average_agreement": 0.0,
            }

        perfect = sum(1 for r in results if r.has_perfect_agreement())
        high = sum(1 for r in results if 0.75 <= r.agreement_score < 1.0)
        low = sum(1 for r in results if r.agreement_score < 0.75)
        needs_review = sum(1 for r in results if r.needs_review())
        avg_agreement = sum(r.agreement_score for r in results) / len(results)

        return {
            "total_terms": len(results),
            "perfect_agreement": perfect,
            "high_agreement": high,
            "low_agreement": low,
            "needs_review": needs_review,
            "average_agreement": avg_agreement,
            "perfect_agreement_pct": (perfect / len(results)) * 100,
            "high_agreement_pct": (high / len(results)) * 100,
            "low_agreement_pct": (low / len(results)) * 100,
            "needs_review_pct": (needs_review / len(results)) * 100,
        }
