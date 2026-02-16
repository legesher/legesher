#!/usr/bin/env python3
"""CLI script for running translation comparisons.

This script compares translations from multiple sources (Claude, GPT-4o, Aya 23, community)
and generates detailed comparison reports with metrics and recommendations.

Usage:
    # Compare Spanish translations using mock data
    python compare_translations.py compare --language es --mock

    # Compare specific term
    python compare_translations.py compare --language es --term def --mock

    # Generate report file
    python compare_translations.py compare --language es --mock --output spanish_report.md

    # Generate JSON output
    python compare_translations.py compare --language es --mock --format json --output results.json

    # Compare multiple languages
    python compare_translations.py compare --language es ar zh --mock --output comparison_report.md
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from legesher_i18n.comparison.comparator import TranslationComparator
from legesher_i18n.comparison.metrics import MetricsCalculator
from legesher_i18n.comparison.models import ComparisonResult, Translation
from legesher_i18n.reports.generator import ReportGenerator
from legesher_i18n.api.providers.anthropic import AnthropicProvider

# Import mock data
from tests.comparison.fixtures import (
    get_all_mock_translations,
    get_mock_translations_for_term,
    get_mock_terms_for_language,
    get_available_languages,
)

console = Console()


class CostTracker:
    """Track and enforce cost budgets."""

    def __init__(self, warning_threshold: float = 50.0, stop_threshold: float = 100.0):
        self.warning_threshold = warning_threshold
        self.stop_threshold = stop_threshold
        self.total_cost = 0.0
        self.warned = False

    def add_cost(self, cost: float):
        """Add cost and check thresholds."""
        self.total_cost += cost

        if self.total_cost >= self.stop_threshold:
            console.print(
                f"[bold red]❌ Cost limit reached: ${self.total_cost:.2f}[/bold red]"
            )
            console.print(
                f"[yellow]Stopping to prevent exceeding ${self.stop_threshold:.2f} budget[/yellow]"
            )
            raise click.Abort()

        if not self.warned and self.total_cost >= self.warning_threshold:
            console.print(
                f"[bold yellow]⚠️  Cost warning: ${self.total_cost:.2f} (threshold: ${self.warning_threshold:.2f})[/bold yellow]"
            )
            self.warned = True

    def get_summary(self) -> Dict:
        """Get cost summary."""
        return {
            "total_cost": self.total_cost,
            "warning_threshold": self.warning_threshold,
            "stop_threshold": self.stop_threshold,
            "warning_reached": self.warned,
            "stop_reached": self.total_cost >= self.stop_threshold,
        }


def load_mock_translations(
    language: str, term: Optional[str] = None
) -> Dict[str, Dict[str, Translation]]:
    """
    Load mock translation data.

    Args:
        language: Language code (es, ar, zh)
        term: Optional specific term to load

    Returns:
        Dict of term -> (source -> Translation)
    """
    if term:
        translations = get_mock_translations_for_term(term, language)
        if not translations:
            console.print(
                f"[bold red]Error: No mock translations found for term '{term}' in language '{language}'[/bold red]"
            )
            raise click.Abort()
        return {term: translations}
    else:
        all_translations = get_all_mock_translations()
        # Get translations for the specified language
        return all_translations.get(language, {})


async def run_comparison(
    language: str,
    term: Optional[str],
    use_mock: bool,
    use_anthropic: bool,
    cost_tracker: CostTracker,
) -> List[ComparisonResult]:
    """
    Run translation comparison for a language.

    Args:
        language: Language code
        term: Optional specific term
        use_mock: Whether to use mock data
        use_anthropic: Whether to use Anthropic for semantic analysis
        cost_tracker: Cost tracking instance

    Returns:
        List of ComparisonResult objects
    """
    # Load translations
    if use_mock:
        translations_by_term = load_mock_translations(language, term)
    else:
        console.print(
            "[bold red]Error: Real translation loading not yet implemented[/bold red]"
        )
        console.print("[yellow]Please use --mock flag for now[/yellow]")
        raise click.Abort()

    if not translations_by_term:
        console.print(
            f"[bold yellow]No translations found for language '{language}'[/bold yellow]"
        )
        return []

    # Initialize comparator
    anthropic_provider = None
    if use_anthropic:
        anthropic_provider = AnthropicProvider()
        console.print(
            "[yellow]⚠️  Using Anthropic provider - API costs will apply[/yellow]"
        )

    comparator = TranslationComparator(anthropic_provider=anthropic_provider)

    # Run comparisons
    results = []
    terms = list(translations_by_term.keys())

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Comparing {len(terms)} terms in {language}...", total=len(terms)
        )

        for term, translations in translations_by_term.items():
            result = await comparator.compare_term(term, language, translations)
            results.append(result)

            # Track costs if using real API
            if use_anthropic and anthropic_provider:
                # Estimate cost (rough estimate: ~$0.01 per comparison)
                estimated_cost = 0.01
                cost_tracker.add_cost(estimated_cost)

            progress.advance(task)

    return results


def display_results_table(results: List[ComparisonResult], language: str):
    """Display results in a rich table."""
    table = Table(title=f"Translation Comparison Results - {language.upper()}")

    table.add_column("Term", style="cyan", no_wrap=True)
    table.add_column("Agreement", style="magenta")
    table.add_column("Translations", style="green")
    table.add_column("Needs Review", style="yellow")

    for result in results:
        unique_trans = result.get_unique_translations()
        translations_str = ", ".join(unique_trans[:3])
        if len(unique_trans) > 3:
            translations_str += "..."

        agreement_color = "green" if result.agreement_score >= 0.75 else "yellow"
        if result.agreement_score < 0.5:
            agreement_color = "red"

        table.add_row(
            result.term,
            f"[{agreement_color}]{result.agreement_score:.1%}[/{agreement_color}]",
            translations_str,
            "⚠️" if result.needs_review() else "✓",
        )

    console.print(table)


def display_metrics_summary(metrics, language: str):
    """Display metrics summary in a panel."""
    distribution = metrics.get_agreement_distribution()

    summary_text = f"""
[bold]Language:[/bold] {language.upper()}
[bold]Total Terms:[/bold] {metrics.total_terms}
[bold]Average Agreement:[/bold] {metrics.average_agreement:.1%}

[bold cyan]Agreement Distribution:[/bold cyan]
  • Perfect (100%): {metrics.perfect_agreement} ({distribution["perfect"]:.1f}%)
  • High (75-99%): {metrics.high_agreement} ({distribution["high"]:.1f}%)
  • Medium (50-74%): {metrics.medium_agreement} ({distribution["medium"]:.1f}%)
  • Low (<50%): {metrics.low_agreement} ({distribution["low"]:.1f}%)

[bold yellow]Issues:[/bold yellow]
  • Needs Review: {metrics.needs_review} ({metrics.get_review_percentage():.1f}%)
  • Word Type Conflicts: {metrics.word_type_conflicts}
  • Form Conflicts: {metrics.form_conflicts}
  • Length Conflicts: {metrics.length_conflicts}
  • Semantic Conflicts: {metrics.semantic_conflicts}
    """.strip()

    console.print(Panel(summary_text, title="📊 Metrics Summary", expand=False))


def generate_json_output(
    results: List[ComparisonResult], metrics, language: str
) -> str:
    """Generate JSON output from results."""
    output = {
        "language": language,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_terms": metrics.total_terms,
            "average_agreement": metrics.average_agreement,
            "perfect_agreement": metrics.perfect_agreement,
            "high_agreement": metrics.high_agreement,
            "medium_agreement": metrics.medium_agreement,
            "low_agreement": metrics.low_agreement,
            "needs_review": metrics.needs_review,
            "agreement_distribution": metrics.get_agreement_distribution(),
        },
        "conflicts": {
            "word_type": metrics.word_type_conflicts,
            "form": metrics.form_conflicts,
            "length": metrics.length_conflicts,
            "semantic": metrics.semantic_conflicts,
        },
        "results": [result.to_dict() for result in results],
    }
    return json.dumps(output, indent=2, ensure_ascii=False)


@click.group()
def cli():
    """Translation comparison CLI tool."""
    pass


@cli.command()
@click.option(
    "--language",
    "-l",
    multiple=True,
    required=True,
    type=click.Choice(["es", "ar", "zh"], case_sensitive=False),
    help="Language(s) to compare (es=Spanish, ar=Arabic, zh=Chinese). Can specify multiple.",
)
@click.option(
    "--term",
    "-t",
    default=None,
    help="Specific term to compare (optional). If not provided, compares all terms.",
)
@click.option(
    "--mock",
    is_flag=True,
    default=False,
    help="Use mock test data instead of real translations.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path for report (optional).",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "json"], case_sensitive=False),
    default="markdown",
    help="Report format (markdown or json).",
)
@click.option(
    "--use-anthropic",
    is_flag=True,
    default=False,
    help="Use Anthropic API for semantic analysis (costs will apply).",
)
@click.option(
    "--cost-warning",
    type=float,
    default=50.0,
    help="Cost warning threshold in USD (default: $50).",
)
@click.option(
    "--cost-limit",
    type=float,
    default=100.0,
    help="Cost limit threshold in USD (default: $100).",
)
def compare(
    language: tuple,
    term: Optional[str],
    mock: bool,
    output: Optional[str],
    format: str,
    use_anthropic: bool,
    cost_warning: float,
    cost_limit: float,
):
    """
    Compare translations from multiple sources.

    This command compares translations from Claude, GPT-4o, Aya 23, and community
    sources, calculating agreement metrics and generating recommendations.

    Examples:

        # Compare Spanish translations using mock data
        python compare_translations.py compare --language es --mock

        # Compare specific term in multiple languages
        python compare_translations.py compare -l es -l ar -l zh --term def --mock

        # Generate markdown report
        python compare_translations.py compare --language es --mock --output report.md

        # Generate JSON output
        python compare_translations.py compare --language es --mock --format json --output results.json
    """
    console.print("[bold blue]🔍 Translation Comparison Tool[/bold blue]\n")

    # Convert tuple to list
    languages = list(language)

    # Initialize cost tracker
    cost_tracker = CostTracker(
        warning_threshold=cost_warning, stop_threshold=cost_limit
    )

    # Display configuration
    console.print(
        f"[bold]Languages:[/bold] {', '.join(lang.upper() for lang in languages)}"
    )
    if term:
        console.print(f"[bold]Term:[/bold] {term}")
    console.print(f"[bold]Data Source:[/bold] {'Mock' if mock else 'Real'}")
    console.print(
        f"[bold]Semantic Analysis:[/bold] {'Enabled (costs apply)' if use_anthropic else 'Disabled'}"
    )
    if output:
        console.print(f"[bold]Output:[/bold] {output} ({format})")
    console.print()

    # Run comparisons for each language
    results_by_language = {}
    metrics_calculator = MetricsCalculator()

    try:
        for lang in languages:
            console.print(f"\n[bold cyan]Processing {lang.upper()}...[/bold cyan]")

            # Run comparison
            results = asyncio.run(
                run_comparison(lang, term, mock, use_anthropic, cost_tracker)
            )

            if not results:
                continue

            results_by_language[lang] = results

            # Calculate metrics
            metrics = metrics_calculator.calculate_language_metrics(results)

            # Display results
            display_results_table(results, lang)
            console.print()
            display_metrics_summary(metrics, lang)

    except click.Abort:
        console.print("\n[bold red]Operation aborted.[/bold red]")
        return

    # Display cost summary
    if use_anthropic:
        cost_summary = cost_tracker.get_summary()
        console.print(
            f"\n[bold]💰 Total Cost:[/bold] ${cost_summary['total_cost']:.2f}"
        )

    # Generate report if output specified
    if output and results_by_language:
        console.print(f"\n[bold]Generating {format} report...[/bold]")

        output_path = Path(output)
        report_generator = ReportGenerator()

        try:
            if len(languages) == 1:
                # Single language report
                lang = languages[0]
                results = results_by_language[lang]
                metrics = metrics_calculator.calculate_language_metrics(results)

                if format == "json":
                    content = generate_json_output(results, metrics, lang)
                    output_path.write_text(content, encoding="utf-8")
                else:
                    report_generator.generate_and_save_language_report(
                        lang, results, output_path
                    )
            else:
                # Cross-language report
                if format == "json":
                    # Generate JSON for multiple languages
                    all_output = {}
                    for lang, results in results_by_language.items():
                        metrics = metrics_calculator.calculate_language_metrics(results)
                        all_output[lang] = json.loads(
                            generate_json_output(results, metrics, lang)
                        )
                    content = json.dumps(all_output, indent=2, ensure_ascii=False)
                    output_path.write_text(content, encoding="utf-8")
                else:
                    report_generator.generate_and_save_cross_language_report(
                        results_by_language, output_path
                    )

            console.print(f"[bold green]✓ Report saved to {output_path}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error generating report: {e}[/bold red]")
            raise

    console.print("\n[bold green]✓ Comparison complete![/bold green]")


@cli.command()
def list_languages():
    """List available languages in mock data."""
    languages = get_available_languages()
    console.print("[bold]Available Languages:[/bold]")
    for lang in languages:
        console.print(f"  • {lang}")


@cli.command()
@click.option(
    "--language",
    "-l",
    required=True,
    type=click.Choice(["es", "ar", "zh"], case_sensitive=False),
    help="Language code",
)
def list_terms(language: str):
    """List available terms for a language in mock data."""
    terms = get_mock_terms_for_language(language)
    console.print(f"[bold]Available Terms for {language.upper()}:[/bold]")
    for term in terms:
        console.print(f"  • {term}")


if __name__ == "__main__":
    cli()
