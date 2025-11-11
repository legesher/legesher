"""Report generation for translation comparison analysis.

This module generates markdown reports from comparison results using Jinja2 templates.
Reports can be generated for individual languages or cross-language comparisons.
"""

from typing import List, Dict, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

from ..comparison.models import ComparisonResult
from ..comparison.metrics import (
    MetricsCalculator,
    LanguageMetrics,
    CrossLanguageMetrics,
    SourceMetrics,
)


class ReportGenerator:
    """Generate markdown reports from translation comparison results."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            template_dir: Optional custom template directory.
                         If not provided, uses default templates.
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.metrics_calculator = MetricsCalculator()

        # Add custom filters
        self.env.filters['percentage'] = self._format_percentage
        self.env.filters['decimal'] = self._format_decimal

    def _format_percentage(self, value: float) -> str:
        """Format float as percentage string (0.75 -> 75.0%)."""
        return f"{value * 100:.1f}%"

    def _format_decimal(self, value: float, decimals: int = 2) -> str:
        """Format float with specified decimal places."""
        return f"{value:.{decimals}f}"

    def generate_language_report(
        self,
        language: str,
        results: List[ComparisonResult],
        include_top_disagreements: int = 10,
    ) -> str:
        """
        Generate a markdown report for a single language.

        Args:
            language: Language code (e.g., "es", "ar", "zh")
            results: List of ComparisonResult for this language
            include_top_disagreements: Number of top disagreements to include

        Returns:
            str: Markdown report content

        Example:
            >>> generator = ReportGenerator()
            >>> results = [...]  # ComparisonResult objects
            >>> report = generator.generate_language_report("es", results)
            >>> print(report)
        """
        # Calculate metrics
        metrics = self.metrics_calculator.calculate_language_metrics(results)

        # Get top disagreements
        top_disagreements = self.metrics_calculator.get_top_disagreements(
            results, limit=include_top_disagreements
        )

        # Get terms needing review
        needs_review = self.metrics_calculator.get_terms_needing_review(results)

        # Get conflict summary
        conflict_summary = self.metrics_calculator.get_conflict_summary(results)

        # Load template
        template = self.env.get_template("language_report.md.j2")

        # Render report
        return template.render(
            language=language,
            metrics=metrics,
            results=results,
            top_disagreements=top_disagreements,
            needs_review=needs_review,
            conflict_summary=conflict_summary,
            agreement_distribution=metrics.get_agreement_distribution(),
        )

    def generate_cross_language_report(
        self,
        results_by_language: Dict[str, List[ComparisonResult]],
        include_top_per_language: int = 5,
    ) -> str:
        """
        Generate a markdown report comparing across multiple languages.

        Args:
            results_by_language: Dict of language -> List[ComparisonResult]
            include_top_per_language: Top disagreements per language to include

        Returns:
            str: Markdown report content

        Example:
            >>> generator = ReportGenerator()
            >>> results_by_lang = {
            ...     "es": [...],  # Spanish results
            ...     "ar": [...],  # Arabic results
            ...     "zh": [...],  # Chinese results
            ... }
            >>> report = generator.generate_cross_language_report(results_by_lang)
            >>> print(report)
        """
        # Calculate cross-language metrics
        cross_metrics = self.metrics_calculator.calculate_cross_language_metrics(
            results_by_language
        )

        # Calculate per-language metrics
        language_metrics = {}
        for lang, results in results_by_language.items():
            language_metrics[lang] = self.metrics_calculator.calculate_language_metrics(
                results
            )

        # Get source metrics
        all_results = [r for results in results_by_language.values() for r in results]
        sources = set()
        for result in all_results:
            sources.update(result.translations.keys())

        source_metrics = {}
        for source in sources:
            source_metrics[source] = self.metrics_calculator.calculate_source_metrics(
                source, all_results
            )

        # Get top disagreements per language
        top_disagreements_by_language = {}
        for lang, results in results_by_language.items():
            top_disagreements_by_language[lang] = (
                self.metrics_calculator.get_top_disagreements(
                    results, limit=include_top_per_language
                )
            )

        # Load template
        template = self.env.get_template("cross_language_report.md.j2")

        # Render report
        return template.render(
            cross_metrics=cross_metrics,
            language_metrics=language_metrics,
            source_metrics=source_metrics,
            results_by_language=results_by_language,
            top_disagreements_by_language=top_disagreements_by_language,
        )

    def save_report(self, content: str, output_path: Path) -> None:
        """
        Save report to file.

        Args:
            content: Report markdown content
            output_path: Path to save report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    def generate_and_save_language_report(
        self,
        language: str,
        results: List[ComparisonResult],
        output_path: Path,
        include_top_disagreements: int = 10,
    ) -> str:
        """
        Generate and save a language report.

        Args:
            language: Language code
            results: Comparison results
            output_path: Path to save report
            include_top_disagreements: Number of top disagreements to include

        Returns:
            str: Report content
        """
        content = self.generate_language_report(
            language, results, include_top_disagreements
        )
        self.save_report(content, output_path)
        return content

    def generate_and_save_cross_language_report(
        self,
        results_by_language: Dict[str, List[ComparisonResult]],
        output_path: Path,
        include_top_per_language: int = 5,
    ) -> str:
        """
        Generate and save a cross-language report.

        Args:
            results_by_language: Results grouped by language
            output_path: Path to save report
            include_top_per_language: Top disagreements per language

        Returns:
            str: Report content
        """
        content = self.generate_cross_language_report(
            results_by_language, include_top_per_language
        )
        self.save_report(content, output_path)
        return content
