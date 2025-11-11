"""Data models for translation comparison and analysis."""

from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, List
from datetime import datetime, UTC


@dataclass
class Translation:
    """Single translation from one source."""

    term: str  # Original Python term (e.g., "def")
    translation: str  # Translated term (e.g., "definir")
    source: Literal["community", "aya23", "claude", "gpt4o"]
    language: str  # Target language code (e.g., "es")
    word_type: Optional[str] = None  # verb, noun, adjective, etc.
    form: Optional[str] = None  # infinitive, present, singular, etc.
    confidence: float = 1.0  # 0.0-1.0 confidence score
    rationale: Optional[str] = None  # Explanation of translation choice
    alternatives: Optional[List[str]] = None  # Alternative translations

    def __post_init__(self):
        """Validate confidence is 0-1."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

    def __hash__(self):
        """Make Translation hashable for use in sets/dicts."""
        return hash((self.term, self.translation, self.source, self.language))

    def __eq__(self, other):
        """Equality based on term, translation, source, language."""
        if not isinstance(other, Translation):
            return False
        return (
            self.term == other.term
            and self.translation == other.translation
            and self.source == other.source
            and self.language == other.language
        )


@dataclass
class DifferenceAnalysis:
    """Analysis of differences between translations."""

    word_type_differs: bool  # Do translations have different word types?
    form_differs: bool  # Do translations have different grammatical forms?
    length_differs_significantly: bool  # Significant length variation?
    completely_different_words: bool  # All unique translations?
    semantic_equivalence: Optional[float] = None  # 0.0-1.0, from Claude analysis

    def has_differences(self) -> bool:
        """Check if any differences exist."""
        return (
            self.word_type_differs
            or self.form_differs
            or self.length_differs_significantly
            or self.completely_different_words
        )

    def severity_score(self) -> float:
        """
        Calculate severity of differences (0.0-1.0).

        Higher score = more severe differences.
        """
        score = 0.0

        if self.completely_different_words:
            score += 0.4
        if self.word_type_differs:
            score += 0.3
        if self.form_differs:
            score += 0.2
        if self.length_differs_significantly:
            score += 0.1

        return min(1.0, score)


@dataclass
class LinguisticAnalysis:
    """Linguistic properties of translations."""

    word_types: Dict[str, str] = field(default_factory=dict)  # source -> word_type
    forms: Dict[str, str] = field(default_factory=dict)  # source -> form
    lengths: Dict[str, int] = field(default_factory=dict)  # source -> char count
    scripts: Dict[str, str] = field(default_factory=dict)  # source -> script type

    def get_dominant_word_type(self) -> Optional[str]:
        """Get most common word type."""
        if not self.word_types:
            return None

        from collections import Counter

        counts = Counter(self.word_types.values())
        return counts.most_common(1)[0][0] if counts else None

    def get_dominant_form(self) -> Optional[str]:
        """Get most common grammatical form."""
        if not self.forms:
            return None

        from collections import Counter

        counts = Counter(self.forms.values())
        return counts.most_common(1)[0][0] if counts else None

    def get_average_length(self) -> float:
        """Get average character length."""
        if not self.lengths:
            return 0.0

        return sum(self.lengths.values()) / len(self.lengths)

    def get_script_types(self) -> List[str]:
        """Get unique script types used."""
        return list(set(self.scripts.values()))


@dataclass
class ComparisonResult:
    """Result of comparing translations for one term in one language."""

    term: str  # Python term being compared
    language: str  # Target language code
    translations: Dict[str, Translation]  # source -> Translation
    agreement_score: float  # 0.0-1.0 (1.0 = perfect agreement)
    differences: DifferenceAnalysis
    linguistic_analysis: LinguisticAnalysis
    recommendation: str  # Human-readable recommendation
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def get_unique_translations(self) -> List[str]:
        """Get list of unique translation texts."""
        return list(set(t.translation for t in self.translations.values()))

    def has_perfect_agreement(self) -> bool:
        """Check if all sources agree."""
        return self.agreement_score >= 1.0

    def sources_in_agreement(self) -> int:
        """Count how many sources agree with most common translation."""
        from collections import Counter

        translation_texts = [t.translation for t in self.translations.values()]
        counts = Counter(translation_texts)
        return counts.most_common(1)[0][1] if counts else 0

    def get_most_common_translation(self) -> Optional[str]:
        """Get the most commonly agreed upon translation."""
        from collections import Counter

        translation_texts = [t.translation for t in self.translations.values()]
        counts = Counter(translation_texts)
        return counts.most_common(1)[0][0] if counts else None

    def get_community_translation(self) -> Optional[Translation]:
        """Get community translation if available."""
        return self.translations.get("community")

    def needs_review(self) -> bool:
        """Check if comparison needs human review."""
        # Needs review if:
        # - Agreement score is low (< 0.5)
        # - Has significant differences
        # - No clear consensus
        return (
            self.agreement_score < 0.5
            or self.differences.severity_score() > 0.5
            or len(self.get_unique_translations()) == len(self.translations)
        )

    def get_confidence_range(self) -> tuple[float, float]:
        """Get min and max confidence scores."""
        if not self.translations:
            return (0.0, 0.0)

        confidences = [t.confidence for t in self.translations.values()]
        return (min(confidences), max(confidences))

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "term": self.term,
            "language": self.language,
            "translations": {
                source: {
                    "translation": t.translation,
                    "source": t.source,
                    "word_type": t.word_type,
                    "form": t.form,
                    "confidence": t.confidence,
                    "rationale": t.rationale,
                    "alternatives": t.alternatives,
                }
                for source, t in self.translations.items()
            },
            "agreement_score": self.agreement_score,
            "differences": {
                "word_type_differs": self.differences.word_type_differs,
                "form_differs": self.differences.form_differs,
                "length_differs_significantly": self.differences.length_differs_significantly,
                "completely_different_words": self.differences.completely_different_words,
                "semantic_equivalence": self.differences.semantic_equivalence,
                "severity_score": self.differences.severity_score(),
            },
            "linguistic_analysis": {
                "word_types": self.linguistic_analysis.word_types,
                "forms": self.linguistic_analysis.forms,
                "lengths": self.linguistic_analysis.lengths,
                "scripts": self.linguistic_analysis.scripts,
                "dominant_word_type": self.linguistic_analysis.get_dominant_word_type(),
                "dominant_form": self.linguistic_analysis.get_dominant_form(),
                "average_length": self.linguistic_analysis.get_average_length(),
            },
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
            "needs_review": self.needs_review(),
        }
