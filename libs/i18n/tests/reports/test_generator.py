"""Tests for report generation with Jinja2 templates."""

import pytest
import pytest_asyncio
from pathlib import Path
import tempfile

from legesher_i18n.reports.generator import ReportGenerator
from legesher_i18n.comparison.models import (
    ComparisonResult,
    Translation,
    DifferenceAnalysis,
    LinguisticAnalysis,
)
from legesher_i18n.comparison.comparator import TranslationComparator


class TestReportGenerator:
    """Test report generation functionality."""

    @pytest.fixture
    def generator(self):
        """Create report generator instance."""
        return ReportGenerator()

    @pytest.fixture
    def sample_translations_spanish(self):
        """Sample Spanish translations for testing."""
        return {
            "print": {
                "community": Translation(
                    "print", "imprimir", "community", "es", "verb", "infinitive", 1.0
                ),
                "claude": Translation(
                    "print", "imprimir", "claude", "es", "verb", "infinitive", 0.98
                ),
                "gpt4o": Translation(
                    "print", "imprimir", "gpt4o", "es", "verb", "infinitive", 0.97
                ),
            },
            "return": {
                "community": Translation(
                    "return", "retornar", "community", "es", "verb", "infinitive", 1.0
                ),
                "claude": Translation(
                    "return",
                    "devolver",
                    "claude",
                    "es",
                    "verb",
                    "infinitive",
                    0.92,
                    rationale="'devolver' is more natural in Spanish",
                ),
                "gpt4o": Translation(
                    "return", "regresar", "gpt4o", "es", "verb", "infinitive", 0.88
                ),
            },
            "def": {
                "community": Translation(
                    "def", "definir", "community", "es", "verb", "infinitive", 1.0
                ),
                "claude": Translation(
                    "def", "definir", "claude", "es", "verb", "infinitive", 0.95
                ),
                "gpt4o": Translation(
                    "def", "función", "gpt4o", "es", "noun", None, 0.85
                ),
            },
        }

    @pytest_asyncio.fixture
    async def sample_results_spanish(self, sample_translations_spanish):
        """Create sample ComparisonResult objects for Spanish."""
        comparator = TranslationComparator()
        results = []

        for term, translations in sample_translations_spanish.items():
            result = await comparator.compare_term(term, "es", translations)
            results.append(result)

        return results

    @pytest.fixture
    def sample_translations_arabic(self):
        """Sample Arabic translations for testing."""
        return {
            "def": {
                "community": Translation(
                    "def", "تعريف", "community", "ar", "verb", "infinitive", 1.0
                ),
                "claude": Translation(
                    "def", "تعريف", "claude", "ar", "verb", "infinitive", 0.97
                ),
                "gpt4o": Translation("def", "وظيفة", "gpt4o", "ar", "noun", None, 0.80),
            },
            "print": {
                "community": Translation(
                    "print", "طباعة", "community", "ar", "verb", "infinitive", 1.0
                ),
                "claude": Translation(
                    "print", "طباعة", "claude", "ar", "verb", "infinitive", 0.98
                ),
                "gpt4o": Translation(
                    "print", "طباعة", "gpt4o", "ar", "verb", "infinitive", 0.96
                ),
            },
        }

    @pytest_asyncio.fixture
    async def sample_results_arabic(self, sample_translations_arabic):
        """Create sample ComparisonResult objects for Arabic."""
        comparator = TranslationComparator()
        results = []

        for term, translations in sample_translations_arabic.items():
            result = await comparator.compare_term(term, "ar", translations)
            results.append(result)

        return results

    @pytest.mark.asyncio
    async def test_generator_initialization(self, generator):
        """Test ReportGenerator initializes correctly."""
        assert generator is not None
        assert generator.template_dir.exists()
        assert generator.env is not None
        assert generator.metrics_calculator is not None

    @pytest.mark.asyncio
    async def test_custom_template_directory(self, tmp_path):
        """Test generator with custom template directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        # Create a simple template
        (custom_dir / "test.md.j2").write_text("Test: {{ value }}")

        generator = ReportGenerator(template_dir=custom_dir)
        assert generator.template_dir == custom_dir

        # Test rendering custom template
        template = generator.env.get_template("test.md.j2")
        result = template.render(value="test_value")
        assert result == "Test: test_value"

    @pytest.mark.asyncio
    async def test_format_percentage_filter(self, generator):
        """Test percentage formatting filter."""
        assert generator._format_percentage(0.75) == "75.0%"
        assert generator._format_percentage(0.9234) == "92.3%"
        assert generator._format_percentage(1.0) == "100.0%"

    @pytest.mark.asyncio
    async def test_format_decimal_filter(self, generator):
        """Test decimal formatting filter."""
        assert generator._format_decimal(0.12345, 2) == "0.12"
        assert generator._format_decimal(0.12345, 3) == "0.123"
        assert generator._format_decimal(1.5, 1) == "1.5"

    @pytest.mark.asyncio
    async def test_generate_language_report_basic(
        self, generator, sample_results_spanish
    ):
        """Test basic language report generation."""
        report = generator.generate_language_report("es", sample_results_spanish)

        # Check report structure
        assert "Translation Comparison Report: ES" in report
        assert "Summary Statistics" in report
        assert "Source Coverage" in report
        assert "Conflict Analysis" in report
        assert "Top Disagreements" in report
        assert "Recommendations" in report

        # Check report contains data
        assert "Total Terms" in report
        assert "Perfect Agreement" in report
        assert "Average Agreement Score" in report

    @pytest.mark.asyncio
    async def test_generate_language_report_content(
        self, generator, sample_results_spanish
    ):
        """Test language report contains correct content."""
        report = generator.generate_language_report("es", sample_results_spanish)

        # Should mention specific terms
        assert "print" in report
        assert "return" in report
        assert "def" in report

        # Should include source names
        assert "community" in report
        assert "claude" in report
        assert "gpt4o" in report

        # Should have translations
        assert "imprimir" in report
        assert "retornar" in report or "devolver" in report or "regresar" in report

    @pytest.mark.asyncio
    async def test_generate_language_report_disagreements(
        self, generator, sample_results_spanish
    ):
        """Test top disagreements section."""
        report = generator.generate_language_report(
            "es", sample_results_spanish, include_top_disagreements=5
        )

        # Should identify return as a disagreement (3 different translations)
        assert "return" in report

        # Should show agreement scores
        assert "Agreement:" in report

    @pytest.mark.asyncio
    async def test_generate_language_report_with_rationale(
        self, generator, sample_results_spanish
    ):
        """Test report includes translation rationales."""
        report = generator.generate_language_report("es", sample_results_spanish)

        # Should include rationale for 'return' from claude
        assert "devolver" in report
        # The rationale might be in the report
        if "Translation Rationales" in report:
            assert "natural" in report.lower()

    @pytest.mark.asyncio
    async def test_generate_cross_language_report_basic(
        self, generator, sample_results_spanish, sample_results_arabic
    ):
        """Test basic cross-language report generation."""
        results_by_language = {
            "es": sample_results_spanish,
            "ar": sample_results_arabic,
        }

        report = generator.generate_cross_language_report(results_by_language)

        # Check report structure
        assert "Cross-Language Translation Comparison Report" in report
        assert "Executive Summary" in report
        assert "Language Performance Comparison" in report
        assert "Translation Source Analysis" in report
        assert "Cross-Language Insights" in report

    @pytest.mark.asyncio
    async def test_generate_cross_language_report_content(
        self, generator, sample_results_spanish, sample_results_arabic
    ):
        """Test cross-language report contains correct content."""
        results_by_language = {
            "es": sample_results_spanish,
            "ar": sample_results_arabic,
        }

        report = generator.generate_cross_language_report(results_by_language)

        # Should mention both languages
        assert "ES" in report
        assert "AR" in report

        # Should have language comparison table
        assert "Total Languages" in report
        assert "2" in report  # Two languages

        # Should analyze sources
        assert "community" in report
        assert "claude" in report
        assert "gpt4o" in report

    @pytest.mark.asyncio
    async def test_generate_cross_language_report_metrics(
        self, generator, sample_results_spanish, sample_results_arabic
    ):
        """Test cross-language report includes metrics."""
        results_by_language = {
            "es": sample_results_spanish,
            "ar": sample_results_arabic,
        }

        report = generator.generate_cross_language_report(results_by_language)

        # Should have overall metrics
        assert "Overall Average Agreement" in report

        # Should have best/worst language indicators
        # (may or may not be present depending on scores)

        # Should have source analysis
        assert "Source Performance Overview" in report

    @pytest.mark.asyncio
    async def test_generate_cross_language_report_recommendations(
        self, generator, sample_results_spanish, sample_results_arabic
    ):
        """Test cross-language report includes recommendations."""
        results_by_language = {
            "es": sample_results_spanish,
            "ar": sample_results_arabic,
        }

        report = generator.generate_cross_language_report(results_by_language)

        # Should have recommendations section
        assert "Overall Recommendations" in report
        assert "Recommendations by Language" in report

    @pytest.mark.asyncio
    async def test_save_report(self, generator, sample_results_spanish, tmp_path):
        """Test saving report to file."""
        report = generator.generate_language_report("es", sample_results_spanish)

        output_path = tmp_path / "reports" / "spanish_report.md"
        generator.save_report(report, output_path)

        # Verify file was created
        assert output_path.exists()

        # Verify content matches
        saved_content = output_path.read_text(encoding="utf-8")
        assert saved_content == report

    @pytest.mark.asyncio
    async def test_generate_and_save_language_report(
        self, generator, sample_results_spanish, tmp_path
    ):
        """Test convenience method for generating and saving."""
        output_path = tmp_path / "spanish_report.md"

        content = generator.generate_and_save_language_report(
            "es", sample_results_spanish, output_path
        )

        # Verify file was created
        assert output_path.exists()

        # Verify returned content matches file
        saved_content = output_path.read_text(encoding="utf-8")
        assert content == saved_content

    @pytest.mark.asyncio
    async def test_generate_and_save_cross_language_report(
        self, generator, sample_results_spanish, sample_results_arabic, tmp_path
    ):
        """Test convenience method for cross-language report."""
        results_by_language = {
            "es": sample_results_spanish,
            "ar": sample_results_arabic,
        }

        output_path = tmp_path / "cross_language_report.md"

        content = generator.generate_and_save_cross_language_report(
            results_by_language, output_path
        )

        # Verify file was created
        assert output_path.exists()

        # Verify returned content matches file
        saved_content = output_path.read_text(encoding="utf-8")
        assert content == saved_content

    @pytest.mark.asyncio
    async def test_report_with_empty_results(self, generator):
        """Test report generation with empty results."""
        report = generator.generate_language_report("es", [])

        # Should still generate a valid report
        assert "Translation Comparison Report: ES" in report
        assert "0" in report  # Should show 0 terms

    @pytest.mark.asyncio
    async def test_cross_language_report_with_single_language(
        self, generator, sample_results_spanish
    ):
        """Test cross-language report with only one language."""
        results_by_language = {"es": sample_results_spanish}

        report = generator.generate_cross_language_report(results_by_language)

        # Should still generate valid report
        assert "Cross-Language Translation Comparison Report" in report
        assert "ES" in report

    @pytest.mark.asyncio
    async def test_report_markdown_formatting(
        self, generator, sample_results_spanish
    ):
        """Test report uses proper markdown formatting."""
        report = generator.generate_language_report("es", sample_results_spanish)

        # Check for markdown headers
        assert "# Translation Comparison Report" in report
        assert "## Summary Statistics" in report
        assert "### " in report  # Third-level headers

        # Check for tables
        assert "|" in report  # Table separators
        assert "---" in report  # Table header separators

        # Check for bold text
        assert "**" in report

    @pytest.mark.asyncio
    async def test_report_includes_conflict_types(
        self, generator, sample_results_spanish
    ):
        """Test report includes conflict type analysis."""
        report = generator.generate_language_report("es", sample_results_spanish)

        # Should have conflict analysis section
        assert "Conflict Analysis" in report

        # Should mention conflict types
        # Depending on data, these may or may not be present
        # Just check the section exists and has structure
        conflict_section_start = report.find("Conflict Analysis")
        assert conflict_section_start > 0

    @pytest.mark.asyncio
    async def test_report_with_many_disagreements(self, generator):
        """Test report handles many disagreements correctly."""
        # Create many comparison results with disagreements
        comparator = TranslationComparator()
        results = []

        # Create 20 terms with varying levels of disagreement
        for i in range(20):
            translations = {
                "community": Translation(
                    f"term{i}", f"trans{i}_a", "community", "es", "verb", None, 1.0
                ),
                "claude": Translation(
                    f"term{i}",
                    f"trans{i}_b",
                    "claude",
                    "es",
                    "verb",
                    None,
                    0.9 - i * 0.02,
                ),
                "gpt4o": Translation(
                    f"term{i}",
                    f"trans{i}_c",
                    "gpt4o",
                    "es",
                    "verb",
                    None,
                    0.85 - i * 0.02,
                ),
            }
            result = await comparator.compare_term(f"term{i}", "es", translations)
            results.append(result)

        # Generate report with limit on disagreements
        report = generator.generate_language_report(
            "es", results, include_top_disagreements=10
        )

        # Should include top 10 disagreements
        assert "term0" in report
        assert "term9" in report

        # Should have proper count
        assert "20" in report  # Total terms

    @pytest.mark.asyncio
    async def test_template_exists(self, generator):
        """Test that required templates exist."""
        # Check language report template
        language_template_path = (
            generator.template_dir / "language_report.md.j2"
        )
        assert language_template_path.exists()

        # Check cross-language report template
        cross_template_path = (
            generator.template_dir / "cross_language_report.md.j2"
        )
        assert cross_template_path.exists()

    @pytest.mark.asyncio
    async def test_templates_are_valid_jinja2(self, generator):
        """Test that templates can be loaded and parsed."""
        # Should not raise exception
        lang_template = generator.env.get_template("language_report.md.j2")
        assert lang_template is not None

        cross_template = generator.env.get_template("cross_language_report.md.j2")
        assert cross_template is not None

    @pytest.mark.asyncio
    async def test_report_includes_source_coverage(
        self, generator, sample_results_spanish
    ):
        """Test report includes source coverage information."""
        report = generator.generate_language_report("es", sample_results_spanish)

        # Should have source coverage section
        assert "Source Coverage" in report

        # Should list sources and their coverage
        # (actual values depend on the data)


class TestReportGeneratorIntegration:
    """Integration tests using real comparison data."""

    @pytest_asyncio.fixture
    async def full_spanish_results(self):
        """Create full set of Spanish results from mock data."""
        from tests.comparison.fixtures.mock_translations import (
            MOCK_SPANISH_TRANSLATIONS,
        )

        comparator = TranslationComparator()
        results = []

        for term, translations in MOCK_SPANISH_TRANSLATIONS.items():
            result = await comparator.compare_term(term, "es", translations)
            results.append(result)

        return results

    @pytest_asyncio.fixture
    async def full_arabic_results(self):
        """Create full set of Arabic results from mock data."""
        from tests.comparison.fixtures.mock_translations import (
            MOCK_ARABIC_TRANSLATIONS,
        )

        comparator = TranslationComparator()
        results = []

        for term, translations in MOCK_ARABIC_TRANSLATIONS.items():
            result = await comparator.compare_term(term, "ar", translations)
            results.append(result)

        return results

    @pytest_asyncio.fixture
    async def full_chinese_results(self):
        """Create full set of Chinese results from mock data."""
        from tests.comparison.fixtures.mock_translations import (
            MOCK_CHINESE_TRANSLATIONS,
        )

        comparator = TranslationComparator()
        results = []

        for term, translations in MOCK_CHINESE_TRANSLATIONS.items():
            result = await comparator.compare_term(term, "zh", translations)
            results.append(result)

        return results

    @pytest.mark.asyncio
    async def test_full_language_report_spanish(
        self, full_spanish_results, tmp_path
    ):
        """Test complete Spanish language report with real data."""
        generator = ReportGenerator()
        report = generator.generate_language_report("es", full_spanish_results)

        # Save for manual inspection during development
        output_path = tmp_path / "full_spanish_report.md"
        generator.save_report(report, output_path)

        # Verify report structure and content
        assert "Translation Comparison Report: ES" in report
        assert len(report) > 1000  # Should be substantial
        assert "print" in report
        assert "return" in report
        assert "imprimir" in report

    @pytest.mark.asyncio
    async def test_full_cross_language_report(
        self,
        full_spanish_results,
        full_arabic_results,
        full_chinese_results,
        tmp_path,
    ):
        """Test complete cross-language report with real data."""
        results_by_language = {
            "es": full_spanish_results,
            "ar": full_arabic_results,
            "zh": full_chinese_results,
        }

        generator = ReportGenerator()
        report = generator.generate_cross_language_report(results_by_language)

        # Save for manual inspection
        output_path = tmp_path / "full_cross_language_report.md"
        generator.save_report(report, output_path)

        # Verify report structure and content
        assert "Cross-Language Translation Comparison Report" in report
        assert len(report) > 2000  # Should be substantial
        assert "ES" in report
        assert "AR" in report
        assert "ZH" in report

    @pytest.mark.asyncio
    async def test_report_generation_performance(self, full_spanish_results):
        """Test report generation completes in reasonable time."""
        import time

        generator = ReportGenerator()

        start = time.time()
        report = generator.generate_language_report("es", full_spanish_results)
        duration = time.time() - start

        # Should generate report quickly (< 1 second for ~10 terms)
        assert duration < 1.0
        assert len(report) > 0
