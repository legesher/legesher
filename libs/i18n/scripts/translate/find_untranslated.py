#!/usr/bin/env python
"""Find untranslated entries in language packs.

This script scans all language pack YAML files and identifies entries where
the translation equals the original term (key == value), indicating the
term was not translated into the target language.

Usage:
    # Show summary report
    python find_untranslated.py

    # Show detailed output for a specific language
    python find_untranslated.py --language es

    # Export to JSON
    python find_untranslated.py --output-json untranslated.json

    # Export to CSV
    python find_untranslated.py --output-csv untranslated.csv

    # Show only languages with untranslated terms
    python find_untranslated.py --only-incomplete
"""

import argparse
import csv
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Path to language packs
LANGUAGE_PACKS_DIR = Path(__file__).parent.parent.parent / "language-packs" / "python"

# Languages to skip (reference implementations or already complete)
SKIP_LANGUAGES = {"en"}  # English is the reference, not a translation


@dataclass
class UntranslatedEntry:
    """Represents a single untranslated entry."""

    language: str
    term: str
    section: str
    python_version: str
    file_path: str


@dataclass
class LanguageReport:
    """Report for a single language."""

    language: str
    untranslated: list[UntranslatedEntry] = field(default_factory=list)
    total_terms: int = 0

    @property
    def untranslated_count(self) -> int:
        return len(self.untranslated)

    @property
    def is_complete(self) -> bool:
        return self.untranslated_count == 0

    @property
    def completion_percentage(self) -> float:
        if self.total_terms == 0:
            return 100.0
        return (1 - self.untranslated_count / self.total_terms) * 100


def find_untranslated_in_yaml(
    yaml_path: Path, language: str
) -> list[UntranslatedEntry]:
    """Find untranslated entries in a single YAML file.

    Args:
        yaml_path: Path to the YAML file
        language: Language code

    Returns:
        List of untranslated entries
    """
    untranslated = []

    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return untranslated

        version = data.get("version", "unknown")
        sections = ["keywords", "builtins", "exceptions"]

        for section in sections:
            section_data = data.get(section, {})
            if not isinstance(section_data, dict):
                continue

            for term, translation in section_data.items():
                # Skip comment lines (start with #)
                if term.startswith("#"):
                    continue

                # Check if translation equals original (untranslated)
                if translation is not None and term == translation:
                    untranslated.append(
                        UntranslatedEntry(
                            language=language,
                            term=term,
                            section=section,
                            python_version=version,
                            file_path=str(yaml_path),
                        )
                    )

    except yaml.YAMLError as e:
        logger.warning(f"YAML error in {yaml_path}: {e}")
    except Exception as e:
        logger.warning(f"Error reading {yaml_path}: {e}")

    return untranslated


def count_terms_in_yaml(yaml_path: Path) -> int:
    """Count total terms in a YAML file."""
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return 0

        count = 0
        sections = ["keywords", "builtins", "exceptions"]

        for section in sections:
            section_data = data.get(section, {})
            if isinstance(section_data, dict):
                # Don't count comment keys
                count += sum(1 for k in section_data if not k.startswith("#"))

        return count

    except Exception:
        return 0


def scan_language(lang_dir: Path, language: str) -> LanguageReport:
    """Scan a language pack directory for untranslated entries.

    Args:
        lang_dir: Path to the language pack directory
        language: Language code

    Returns:
        LanguageReport with untranslated entries
    """
    report = LanguageReport(language=language)

    # Find the packs directory
    pack_name = f"legesher_i18n_python_{language}"
    packs_dir = lang_dir / pack_name / "packs"

    if not packs_dir.exists():
        logger.warning(f"Packs directory not found: {packs_dir}")
        return report

    # Scan base file (3.10.yml) for main terms
    base_file = packs_dir / "3.10.yml"
    if base_file.exists():
        report.total_terms = count_terms_in_yaml(base_file)
        report.untranslated.extend(find_untranslated_in_yaml(base_file, language))

    # Also check higher version files for version-specific terms
    for version_file in sorted(packs_dir.glob("3.*.yml")):
        if version_file.name == "3.10.yml":
            continue  # Already processed

        version_untranslated = find_untranslated_in_yaml(version_file, language)
        # Only add unique terms not already in the list
        existing_terms = {e.term for e in report.untranslated}
        for entry in version_untranslated:
            if entry.term not in existing_terms:
                report.untranslated.append(entry)

    return report


def scan_all_languages(
    skip_languages: set[str] | None = None,
) -> dict[str, LanguageReport]:
    """Scan all language packs for untranslated entries.

    Args:
        skip_languages: Set of language codes to skip

    Returns:
        Dictionary mapping language code to LanguageReport
    """
    if skip_languages is None:
        skip_languages = SKIP_LANGUAGES

    reports: dict[str, LanguageReport] = {}

    for lang_dir in sorted(LANGUAGE_PACKS_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue

        language = lang_dir.name

        # Skip non-language directories
        if language in ("version-index.yml",) or len(language) != 2:
            continue

        if language in skip_languages:
            logger.debug(f"Skipping {language} (in skip list)")
            continue

        report = scan_language(lang_dir, language)
        reports[language] = report

    return reports


def print_summary(reports: dict[str, LanguageReport], only_incomplete: bool = False):
    """Print a summary of untranslated entries."""
    print("\n" + "=" * 70)
    print("UNTRANSLATED ENTRIES REPORT")
    print("=" * 70)

    # Sort by untranslated count (descending)
    sorted_reports = sorted(
        reports.values(), key=lambda r: r.untranslated_count, reverse=True
    )

    # Separate complete and incomplete
    complete = [r for r in sorted_reports if r.is_complete]
    incomplete = [r for r in sorted_reports if not r.is_complete]

    # Print incomplete languages
    if incomplete:
        print(f"\n{'INCOMPLETE LANGUAGES':-^70}")
        print(f"{'Language':<10} {'Untranslated':>12} {'Total':>8} {'Complete':>10}")
        print("-" * 70)

        total_untranslated = 0
        for report in incomplete:
            total_untranslated += report.untranslated_count
            print(
                f"{report.language:<10} {report.untranslated_count:>12} "
                f"{report.total_terms:>8} {report.completion_percentage:>9.1f}%"
            )

        print("-" * 70)
        print(f"{'TOTAL':<10} {total_untranslated:>12}")

    # Print complete languages (if not --only-incomplete)
    if complete and not only_incomplete:
        print(f"\n{'COMPLETE LANGUAGES':-^70}")
        for report in complete:
            print(f"  {report.language} - {report.total_terms} terms (100%)")

    # Summary stats
    print("\n" + "-" * 70)
    print(f"Total languages scanned: {len(reports)}")
    print(f"Complete: {len(complete)}")
    print(f"Incomplete: {len(incomplete)}")
    print("=" * 70)


def print_language_detail(report: LanguageReport):
    """Print detailed untranslated entries for a language."""
    print(f"\n{'=' * 70}")
    print(f"UNTRANSLATED ENTRIES FOR: {report.language.upper()}")
    print(f"{'=' * 70}")
    print(f"Total untranslated: {report.untranslated_count}")
    print(f"Completion: {report.completion_percentage:.1f}%")
    print("-" * 70)

    # Group by section
    by_section: dict[str, list[UntranslatedEntry]] = defaultdict(list)
    for entry in report.untranslated:
        by_section[entry.section].append(entry)

    for section, entries in sorted(by_section.items()):
        print(f"\n{section.upper()} ({len(entries)} untranslated):")
        for entry in sorted(entries, key=lambda e: e.term):
            print(f"  - {entry.term}")


def export_json(reports: dict[str, LanguageReport], output_path: Path):
    """Export untranslated entries to JSON."""
    data = {}
    for language, report in reports.items():
        if report.untranslated:
            data[language] = {
                "untranslated_count": report.untranslated_count,
                "total_terms": report.total_terms,
                "completion_percentage": round(report.completion_percentage, 1),
                "entries": [
                    {
                        "term": e.term,
                        "section": e.section,
                        "python_version": e.python_version,
                    }
                    for e in report.untranslated
                ],
            }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Exported to {output_path}")


def export_csv(reports: dict[str, LanguageReport], output_path: Path):
    """Export untranslated entries to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["language", "term", "section", "python_version"])

        for report in sorted(reports.values(), key=lambda r: r.language):
            for entry in sorted(report.untranslated, key=lambda e: e.term):
                writer.writerow(
                    [entry.language, entry.term, entry.section, entry.python_version]
                )

    print(f"Exported to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find untranslated entries in language packs"
    )
    parser.add_argument(
        "--language",
        "-l",
        help="Show detailed output for a specific language",
    )
    parser.add_argument(
        "--output-json",
        "-j",
        type=Path,
        help="Export results to JSON file",
    )
    parser.add_argument(
        "--output-csv",
        "-c",
        type=Path,
        help="Export results to CSV file",
    )
    parser.add_argument(
        "--only-incomplete",
        "-i",
        action="store_true",
        help="Only show languages with untranslated entries",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Scan all languages
    reports = scan_all_languages()

    # Export if requested
    if args.output_json:
        export_json(reports, args.output_json)

    if args.output_csv:
        export_csv(reports, args.output_csv)

    # Show detailed output for specific language
    if args.language:
        if args.language in reports:
            print_language_detail(reports[args.language])
        else:
            print(f"Language '{args.language}' not found")
            return

    # Show summary
    print_summary(reports, only_incomplete=args.only_incomplete)

    # Return exit code based on completeness
    incomplete = sum(1 for r in reports.values() if not r.is_complete)
    return 0 if incomplete == 0 else 1


if __name__ == "__main__":
    exit(main())
