"""Tests for comparison data models."""

import pytest
from legesher_i18n.comparison.models import (
    Translation,
    DifferenceAnalysis,
    LinguisticAnalysis,
    ComparisonResult,
)


class TestTranslation:
    """Test Translation model."""

    def test_translation_creation(self):
        """Test creating a translation."""
        t = Translation(
            term="def",
            translation="definir",
            source="claude",
            language="es",
            word_type="verb",
            form="infinitive",
            confidence=0.95,
        )
        assert t.term == "def"
        assert t.translation == "definir"
        assert t.source == "claude"
        assert t.language == "es"
        assert t.word_type == "verb"
        assert t.form == "infinitive"
        assert t.confidence == 0.95

    def test_translation_defaults(self):
        """Test default values."""
        t = Translation(
            term="print", translation="imprimir", source="community", language="es"
        )
        assert t.word_type is None
        assert t.form is None
        assert t.confidence == 1.0
        assert t.rationale is None
        assert t.alternatives is None

    def test_translation_with_alternatives(self):
        """Test translation with alternatives."""
        t = Translation(
            term="return",
            translation="retornar",
            source="claude",
            language="es",
            alternatives=["devolver", "regresar"],
            rationale="Most natural infinitive form",
        )
        assert t.alternatives == ["devolver", "regresar"]
        assert t.rationale == "Most natural infinitive form"

    def test_translation_confidence_validation(self):
        """Test confidence must be 0-1."""
        with pytest.raises(ValueError, match="Confidence must be 0-1"):
            Translation(
                term="def",
                translation="definir",
                source="claude",
                language="es",
                confidence=1.5,  # Invalid
            )

        with pytest.raises(ValueError, match="Confidence must be 0-1"):
            Translation(
                term="def",
                translation="definir",
                source="claude",
                language="es",
                confidence=-0.1,  # Invalid
            )

    def test_translation_hashable(self):
        """Test translations are hashable."""
        t1 = Translation("def", "definir", "claude", "es")
        t2 = Translation("def", "definir", "claude", "es")
        t3 = Translation("def", "función", "gpt4o", "es")

        # Same translations should have same hash
        assert hash(t1) == hash(t2)

        # Can be used in sets
        translations = {t1, t2, t3}
        assert len(translations) == 2  # t1 and t2 are the same

    def test_translation_equality(self):
        """Test translation equality."""
        t1 = Translation("def", "definir", "claude", "es", confidence=0.95)
        t2 = Translation("def", "definir", "claude", "es", confidence=0.90)
        t3 = Translation("def", "función", "gpt4o", "es")

        # Equality based on term, translation, source, language (not confidence)
        assert t1 == t2
        assert t1 != t3


class TestDifferenceAnalysis:
    """Test DifferenceAnalysis model."""

    def test_difference_analysis_creation(self):
        """Test creating difference analysis."""
        diff = DifferenceAnalysis(
            word_type_differs=True,
            form_differs=False,
            length_differs_significantly=False,
            completely_different_words=False,
            semantic_equivalence=0.85,
        )
        assert diff.word_type_differs is True
        assert diff.form_differs is False
        assert diff.semantic_equivalence == 0.85

    def test_has_differences_true(self):
        """Test has_differences returns True when differences exist."""
        diff = DifferenceAnalysis(
            word_type_differs=True,
            form_differs=False,
            length_differs_significantly=False,
            completely_different_words=False,
        )
        assert diff.has_differences() is True

    def test_has_differences_false(self):
        """Test has_differences returns False when no differences."""
        diff = DifferenceAnalysis(
            word_type_differs=False,
            form_differs=False,
            length_differs_significantly=False,
            completely_different_words=False,
        )
        assert diff.has_differences() is False

    def test_severity_score_no_differences(self):
        """Test severity score with no differences."""
        diff = DifferenceAnalysis(False, False, False, False)
        assert diff.severity_score() == 0.0

    def test_severity_score_all_differences(self):
        """Test severity score with all differences."""
        diff = DifferenceAnalysis(True, True, True, True)
        # 0.4 + 0.3 + 0.2 + 0.1 = 1.0
        assert diff.severity_score() == pytest.approx(1.0)

    def test_severity_score_partial(self):
        """Test severity score with partial differences."""
        diff = DifferenceAnalysis(
            word_type_differs=True,  # 0.3
            form_differs=True,  # 0.2
            length_differs_significantly=False,
            completely_different_words=False,
        )
        assert diff.severity_score() == 0.5


class TestLinguisticAnalysis:
    """Test LinguisticAnalysis model."""

    def test_linguistic_analysis_creation(self):
        """Test creating linguistic analysis."""
        analysis = LinguisticAnalysis(
            word_types={"claude": "verb", "gpt4o": "verb"},
            forms={"claude": "infinitive", "gpt4o": "infinitive"},
            lengths={"claude": 7, "gpt4o": 7},
            scripts={"claude": "latin", "gpt4o": "latin"},
        )
        assert len(analysis.word_types) == 2
        assert analysis.word_types["claude"] == "verb"

    def test_linguistic_analysis_defaults(self):
        """Test default empty dicts."""
        analysis = LinguisticAnalysis()
        assert analysis.word_types == {}
        assert analysis.forms == {}
        assert analysis.lengths == {}
        assert analysis.scripts == {}

    def test_get_dominant_word_type(self):
        """Test getting dominant word type."""
        analysis = LinguisticAnalysis(
            word_types={
                "claude": "verb",
                "gpt4o": "verb",
                "aya23": "noun",
                "community": "verb",
            }
        )
        assert analysis.get_dominant_word_type() == "verb"

    def test_get_dominant_word_type_empty(self):
        """Test get_dominant_word_type with no data."""
        analysis = LinguisticAnalysis()
        assert analysis.get_dominant_word_type() is None

    def test_get_dominant_form(self):
        """Test getting dominant grammatical form."""
        analysis = LinguisticAnalysis(
            forms={
                "claude": "infinitive",
                "gpt4o": "infinitive",
                "aya23": "present",
            }
        )
        assert analysis.get_dominant_form() == "infinitive"

    def test_get_average_length(self):
        """Test calculating average length."""
        analysis = LinguisticAnalysis(lengths={"claude": 7, "gpt4o": 8, "aya23": 6})
        assert analysis.get_average_length() == 7.0

    def test_get_average_length_empty(self):
        """Test average length with no data."""
        analysis = LinguisticAnalysis()
        assert analysis.get_average_length() == 0.0

    def test_get_script_types(self):
        """Test getting unique script types."""
        analysis = LinguisticAnalysis(
            scripts={
                "claude": "latin",
                "gpt4o": "latin",
                "aya23": "arabic",
                "community": "latin",
            }
        )
        scripts = analysis.get_script_types()
        assert len(scripts) == 2
        assert "latin" in scripts
        assert "arabic" in scripts


class TestComparisonResult:
    """Test ComparisonResult model."""

    @pytest.fixture
    def sample_translations(self):
        """Create sample translations for testing."""
        return {
            "claude": Translation("def", "definir", "claude", "es"),
            "gpt4o": Translation("def", "definir", "gpt4o", "es"),
            "community": Translation("def", "definir", "community", "es"),
        }

    @pytest.fixture
    def sample_comparison(self, sample_translations):
        """Create sample comparison result."""
        return ComparisonResult(
            term="def",
            language="es",
            translations=sample_translations,
            agreement_score=1.0,
            differences=DifferenceAnalysis(False, False, False, False),
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="Perfect agreement - use 'definir'",
        )

    def test_comparison_result_creation(self, sample_comparison):
        """Test creating comparison result."""
        assert sample_comparison.term == "def"
        assert sample_comparison.language == "es"
        assert len(sample_comparison.translations) == 3
        assert sample_comparison.agreement_score == 1.0

    def test_get_unique_translations(self, sample_comparison):
        """Test getting unique translations."""
        unique = sample_comparison.get_unique_translations()
        assert len(unique) == 1
        assert "definir" in unique

    def test_get_unique_translations_multiple(self):
        """Test unique translations with different values."""
        translations = {
            "claude": Translation("return", "retornar", "claude", "es"),
            "gpt4o": Translation("return", "devolver", "gpt4o", "es"),
            "aya23": Translation("return", "regresar", "aya23", "es"),
        }
        result = ComparisonResult(
            term="return",
            language="es",
            translations=translations,
            agreement_score=0.33,
            differences=DifferenceAnalysis(False, False, False, True),
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="Low agreement",
        )
        unique = result.get_unique_translations()
        assert len(unique) == 3
        assert "retornar" in unique
        assert "devolver" in unique
        assert "regresar" in unique

    def test_has_perfect_agreement(self, sample_comparison):
        """Test perfect agreement detection."""
        assert sample_comparison.has_perfect_agreement() is True

    def test_has_perfect_agreement_false(self):
        """Test perfect agreement returns False."""
        translations = {
            "claude": Translation("def", "definir", "claude", "es"),
            "gpt4o": Translation("def", "función", "gpt4o", "es"),
        }
        result = ComparisonResult(
            term="def",
            language="es",
            translations=translations,
            agreement_score=0.5,
            differences=DifferenceAnalysis(True, False, False, False),
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="Partial agreement",
        )
        assert result.has_perfect_agreement() is False

    def test_sources_in_agreement(self, sample_comparison):
        """Test counting sources in agreement."""
        assert sample_comparison.sources_in_agreement() == 3

    def test_sources_in_agreement_partial(self):
        """Test sources in agreement with partial agreement."""
        translations = {
            "claude": Translation("def", "definir", "claude", "es"),
            "gpt4o": Translation("def", "definir", "gpt4o", "es"),
            "aya23": Translation("def", "función", "aya23", "es"),
            "community": Translation("def", "definir", "community", "es"),
        }
        result = ComparisonResult(
            term="def",
            language="es",
            translations=translations,
            agreement_score=0.75,
            differences=DifferenceAnalysis(False, False, False, False),
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="High agreement",
        )
        assert result.sources_in_agreement() == 3  # 3 sources agree on "definir"

    def test_get_most_common_translation(self, sample_comparison):
        """Test getting most common translation."""
        assert sample_comparison.get_most_common_translation() == "definir"

    def test_get_community_translation(self, sample_comparison):
        """Test getting community translation."""
        community = sample_comparison.get_community_translation()
        assert community is not None
        assert community.source == "community"
        assert community.translation == "definir"

    def test_get_community_translation_missing(self):
        """Test getting community translation when missing."""
        translations = {
            "claude": Translation("def", "definir", "claude", "es"),
            "gpt4o": Translation("def", "definir", "gpt4o", "es"),
        }
        result = ComparisonResult(
            term="def",
            language="es",
            translations=translations,
            agreement_score=1.0,
            differences=DifferenceAnalysis(False, False, False, False),
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="Agreement",
        )
        assert result.get_community_translation() is None

    def test_needs_review_false(self, sample_comparison):
        """Test needs_review with perfect agreement."""
        assert sample_comparison.needs_review() is False

    def test_needs_review_low_agreement(self):
        """Test needs_review with low agreement score."""
        translations = {
            "claude": Translation("def", "definir", "claude", "es"),
            "gpt4o": Translation("def", "función", "gpt4o", "es"),
        }
        result = ComparisonResult(
            term="def",
            language="es",
            translations=translations,
            agreement_score=0.4,  # Low
            differences=DifferenceAnalysis(False, False, False, False),
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="Low agreement",
        )
        assert result.needs_review() is True

    def test_needs_review_high_severity(self):
        """Test needs_review with high difference severity."""
        translations = {
            "claude": Translation("def", "definir", "claude", "es"),
            "gpt4o": Translation("def", "función", "gpt4o", "es"),
        }
        result = ComparisonResult(
            term="def",
            language="es",
            translations=translations,
            agreement_score=0.5,
            differences=DifferenceAnalysis(True, True, True, False),  # High severity
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="Significant differences",
        )
        assert result.needs_review() is True

    def test_get_confidence_range(self):
        """Test getting confidence range."""
        translations = {
            "claude": Translation("def", "definir", "claude", "es", confidence=0.95),
            "gpt4o": Translation("def", "definir", "gpt4o", "es", confidence=0.85),
            "aya23": Translation("def", "definir", "aya23", "es", confidence=0.90),
        }
        result = ComparisonResult(
            term="def",
            language="es",
            translations=translations,
            agreement_score=1.0,
            differences=DifferenceAnalysis(False, False, False, False),
            linguistic_analysis=LinguisticAnalysis(),
            recommendation="Agreement",
        )
        min_conf, max_conf = result.get_confidence_range()
        assert min_conf == 0.85
        assert max_conf == 0.95

    def test_to_dict(self, sample_comparison):
        """Test converting to dictionary."""
        result_dict = sample_comparison.to_dict()

        assert result_dict["term"] == "def"
        assert result_dict["language"] == "es"
        assert result_dict["agreement_score"] == 1.0
        assert "translations" in result_dict
        assert "differences" in result_dict
        assert "linguistic_analysis" in result_dict
        assert "recommendation" in result_dict
        assert "timestamp" in result_dict
        assert "needs_review" in result_dict

        # Check translations structure
        assert "claude" in result_dict["translations"]
        assert result_dict["translations"]["claude"]["translation"] == "definir"

        # Check differences structure
        assert "severity_score" in result_dict["differences"]

        # Check linguistic analysis structure
        assert "dominant_word_type" in result_dict["linguistic_analysis"]
        assert "average_length" in result_dict["linguistic_analysis"]
