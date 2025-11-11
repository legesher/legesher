#!/usr/bin/env python3
"""Demo script to generate sample translation comparison reports."""

import asyncio
from pathlib import Path

from legesher_i18n.reports.generator import ReportGenerator
from legesher_i18n.comparison.comparator import TranslationComparator
from tests.comparison.fixtures.mock_translations import (
    MOCK_SPANISH_TRANSLATIONS,
    MOCK_ARABIC_TRANSLATIONS,
    MOCK_CHINESE_TRANSLATIONS,
)


async def generate_sample_reports():
    """Generate sample reports using mock translation data."""
    print("Generating sample translation comparison reports...")

    # Create comparator and generator
    comparator = TranslationComparator()
    generator = ReportGenerator()

    # Generate comparison results for each language
    print("\n1. Analyzing Spanish translations...")
    spanish_results = []
    for term, translations in MOCK_SPANISH_TRANSLATIONS.items():
        result = await comparator.compare_term(term, "es", translations)
        spanish_results.append(result)

    print("2. Analyzing Arabic translations...")
    arabic_results = []
    for term, translations in MOCK_ARABIC_TRANSLATIONS.items():
        result = await comparator.compare_term(term, "ar", translations)
        arabic_results.append(result)

    print("3. Analyzing Chinese translations...")
    chinese_results = []
    for term, translations in MOCK_CHINESE_TRANSLATIONS.items():
        result = await comparator.compare_term(term, "zh", translations)
        chinese_results.append(result)

    # Create output directory
    output_dir = Path("sample_reports")
    output_dir.mkdir(exist_ok=True)

    # Generate language-specific reports
    print("\n4. Generating language reports...")

    generator.generate_and_save_language_report(
        "es", spanish_results, output_dir / "spanish_report.md"
    )
    print(f"   ✓ Spanish report saved to {output_dir / 'spanish_report.md'}")

    generator.generate_and_save_language_report(
        "ar", arabic_results, output_dir / "arabic_report.md"
    )
    print(f"   ✓ Arabic report saved to {output_dir / 'arabic_report.md'}")

    generator.generate_and_save_language_report(
        "zh", chinese_results, output_dir / "chinese_report.md"
    )
    print(f"   ✓ Chinese report saved to {output_dir / 'chinese_report.md'}")

    # Generate cross-language report
    print("\n5. Generating cross-language comparison report...")
    results_by_language = {
        "es": spanish_results,
        "ar": arabic_results,
        "zh": chinese_results,
    }

    generator.generate_and_save_cross_language_report(
        results_by_language, output_dir / "cross_language_report.md"
    )
    print(
        f"   ✓ Cross-language report saved to {output_dir / 'cross_language_report.md'}"
    )

    # Print summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    for lang, results in results_by_language.items():
        stats = comparator.get_summary_statistics(results)
        print(f"\n{lang.upper()}:")
        print(f"  Total Terms: {stats['total_terms']}")
        print(
            f"  Perfect Agreement: {stats['perfect_agreement']} ({stats['perfect_agreement_pct']:.1f}%)"
        )
        print(
            f"  High Agreement: {stats['high_agreement']} ({stats['high_agreement_pct']:.1f}%)"
        )
        print(
            f"  Needs Review: {stats['needs_review']} ({stats['needs_review_pct']:.1f}%)"
        )
        print(f"  Average Agreement: {stats['average_agreement']:.3f}")

    print("\n" + "=" * 70)
    print(f"\nAll reports generated successfully in '{output_dir}/' directory!")
    print("\nPreview of Spanish report (first 50 lines):")
    print("-" * 70)

    # Print summary
    print(f"\nGenerated 4 comprehensive reports in {output_dir}/")


if __name__ == "__main__":
    asyncio.run(generate_sample_reports())
