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

    # Gate mode (pre-commit passes changed pack files as arguments)
    python find_untranslated.py --warn-only path/to/packs/3.10.yml ...

Exit code is non-zero when findings remain after the intentional-loanword
allowlist (``untranslated_allowlist.yml`` next to this script) is applied.
``--warn-only`` (report mode) exits 0 for pack findings; usage errors — an
unknown ``--language``, a malformed allowlist — still exit non-zero.
"""

import argparse
import csv
import json
import logging
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

# The identity-compare rule (NFKC + casefold, policy 2026-07-05) has exactly
# one implementation: legesher_i18n.db.schema_v2.is_identity_translation.
# The pre-commit hook runs this script via `uv run`, where the package is
# importable — a local mirror would be a second policy that can drift
# (post-merge review finding, 2026-08-09).
from legesher_i18n.db.schema_v2 import is_identity_translation

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Path to language packs
LANGUAGE_PACKS_DIR = Path(__file__).parent.parent.parent / "language-packs" / "python"

# Languages to skip (reference implementations or already complete)
SKIP_LANGUAGES = {"en"}  # English is the reference, not a translation

# Intentional key == value entries (loanwords / policy keeps, CORE-1318).
# Entries are "<lang>:<term>" strings; see the file's header comment for the
# evidence bar. Findings matching the allowlist are not reported.
ALLOWLIST_PATH = Path(__file__).parent / "untranslated_allowlist.yml"

# The v1 corpus DB the allowlist is drift-checked against (--check-db,
# CORE-1355). The v2 identity_ok marker is populated from these same rows by
# migrate_to_v2.py using the same compare rule — one policy, two layers.
DEFAULT_DB_PATH = (
    Path(__file__).parent.parent.parent / "legesher_i18n" / "db" / "translations.db"
)


def check_db_drift(
    db_path: Path, allowlist_pairs: frozenset[tuple[str, str]] | set[tuple[str, str]]
) -> list[str]:
    """Verify every allowlist entry is an identity translation in the DB.

    Two drift shapes, both errors (CORE-1355 "drift fails the check"):
    an allowlist entry with no DB selection at all for that (term, language),
    and one whose DB-selected translation is NOT the term itself under the
    NFKC+casefold rule (i.e. the DB translated it, so the pack-layer
    "intentional loanword" claim is stale).
    """
    errors: list[str] = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        for language, term in sorted(allowlist_pairs):
            rows = conn.execute(
                "SELECT t.name AS name, st.translation AS translation "
                "FROM selected_translations st JOIN terms t ON t.id = st.term_id "
                "WHERE st.language_code = ?",
                (language,),
            ).fetchall()
            matches = [r for r in rows if is_identity_translation(r["name"], term)]
            if not matches:
                errors.append(
                    f"{language}:{term} — allowlist entry has no selected "
                    "translation in the DB; prune the entry or select the "
                    "loanword (CORE-1355)"
                )
            elif not any(
                is_identity_translation(r["translation"], term) for r in matches
            ):
                got = ", ".join(repr(r["translation"]) for r in matches)
                errors.append(
                    f"{language}:{term} — DB selected translation is {got}, "
                    "not the identity loanword the allowlist claims; the "
                    "allowlist entry is stale (CORE-1355)"
                )
    finally:
        conn.close()
    return errors


def count_allowlisted_cognates_in_yaml(yaml_path: Path, language: str) -> set[str]:
    """Terms in *yaml_path* that are key == value AND allowlisted.

    These are the deliberate-cognate class (identity_ok at the DB layer,
    CORE-1355) — reported as their own line in the summary, never as gaps.
    """
    cognates: set[str] = set()
    try:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return cognates
        for section in ["keywords", "builtins", "exceptions"]:
            section_data = data.get(section, {})
            if not isinstance(section_data, dict):
                continue
            for term, translation in section_data.items():
                if (
                    not term.startswith("#")
                    and term == translation
                    and (language, term) in load_allowlist()
                ):
                    cognates.add(term)
    except (OSError, yaml.YAMLError):
        pass
    return cognates


@cache
def load_allowlist() -> frozenset[tuple[str, str]]:
    """Load the intentional key == value allowlist as (language, term) pairs."""
    if not ALLOWLIST_PATH.exists():
        return frozenset()

    with open(ALLOWLIST_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    pairs = set()
    for raw in data.get("entries") or []:
        # Accept both spellings: the "lang:term" string and the natural YAML
        # mapping form "lang: term" (a single-key dict). Anything else is a
        # mistake — fail loudly rather than silently skipping a gate entry.
        if isinstance(raw, dict) and len(raw) == 1:
            language, term = next(iter(raw.items()))
            language, term = str(language), str(term)
        elif isinstance(raw, str):
            language, _, term = raw.partition(":")
        else:
            raise SystemExit(
                f"Malformed allowlist entry {raw!r} in {ALLOWLIST_PATH}: "
                'expected "lang:term" or "lang: term"'
            )
        language, term = language.strip(), term.strip()
        if not language or not term or ":" in term:
            raise SystemExit(
                f"Malformed allowlist entry {raw!r} in {ALLOWLIST_PATH}: "
                'expected "lang:term" or "lang: term"'
            )
        pairs.add((language, term))
    return frozenset(pairs)


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
    # Deliberate cognates/loanwords (allowlisted key == value) — their own
    # class, never counted as gaps (CORE-1355).
    cognate_terms: set[str] = field(default_factory=set)

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

                # Skip intentional loanwords / policy keeps
                if (language, term) in load_allowlist():
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
        report.cognate_terms |= count_allowlisted_cognates_in_yaml(base_file, language)

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
        report.cognate_terms |= count_allowlisted_cognates_in_yaml(
            version_file, language
        )

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


def _language_from_pack_path(path: Path) -> str | None:
    """Derive the language code from a pack file path, or None if not a
    python pack file (layout: .../python/<lang>/legesher_i18n_python_<lang>/packs/*.yml)."""
    for parent in path.resolve().parents:
        if parent.name.startswith("legesher_i18n_python_"):
            return parent.name.removeprefix("legesher_i18n_python_")
    return None


def scan_paths(paths: list[Path]) -> dict[str, LanguageReport]:
    """Scan specific pack files (pre-commit filename mode).

    Files whose path does not identify a python language pack, and files for
    languages in SKIP_LANGUAGES (the English reference), are ignored.
    """
    reports: dict[str, LanguageReport] = {}

    for path in paths:
        language = _language_from_pack_path(path)
        if language is None:
            logger.debug(f"Skipping non-pack path: {path}")
            continue
        if language in SKIP_LANGUAGES:
            continue

        report = reports.setdefault(language, LanguageReport(language=language))
        report.total_terms += count_terms_in_yaml(path)

        existing_terms = {e.term for e in report.untranslated}
        for entry in find_untranslated_in_yaml(path, language):
            if entry.term not in existing_terms:
                report.untranslated.append(entry)
                existing_terms.add(entry.term)
        report.cognate_terms |= count_allowlisted_cognates_in_yaml(path, language)

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
    # Deliberate cognates are their own class, not gaps (CORE-1355).
    total_cognates = sum(len(r.cognate_terms) for r in reports.values())
    if total_cognates:
        langs = sorted(r.language for r in reports.values() if r.cognate_terms)
        print(
            f"Intentional cognates (allowlisted, identity_ok class): "
            f"{total_cognates} across {', '.join(langs)}"
        )
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
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Report pack findings but exit 0 for them (report mode for the "
        "find-untranslated-terms pre-commit gate; usage errors still exit 1)",
    )
    parser.add_argument(
        "--check-db",
        action="store_true",
        help="Drift-check the allowlist against the corpus DB's selected "
        "translations (CORE-1355: one policy, two layers). Drift always "
        "exits non-zero, even with --warn-only. If the database is not "
        "present the check is skipped with a notice — it is gitignored, so "
        "a clean checkout never has it. A boolean on purpose: pre-commit "
        "appends filenames, so an optional-value flag would swallow the "
        "first pack path.",
    )
    parser.add_argument(
        "--check-db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        metavar="DB",
        help="Database for --check-db (default: the in-repo translations.db)",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Pack YAML files to scan (as passed by pre-commit); "
        "default: scan all language packs",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Scan the given pack files (pre-commit mode) or all languages
    reports = scan_paths(args.paths) if args.paths else scan_all_languages()

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
            return 1

    # Show summary
    print_summary(reports, only_incomplete=args.only_incomplete)

    # Allowlist <-> DB reconciliation (CORE-1355): drift is a data-consistency
    # failure, blocking regardless of --warn-only.
    if args.check_db:
        if not args.check_db_path.exists():
            # translations.db is gitignored (libs/i18n/.gitignore) and lives in
            # the private data repo, so a clean checkout — CI included — never
            # has it. Absence is an environment fact, not allowlist drift:
            # skip the reconciliation and say so, rather than failing a build
            # over a file that cannot be present. Drift itself still blocks
            # wherever the DB IS available, which is the developer machine that
            # can actually act on it (CORE-1899; the gate itself is CORE-1355).
            print(
                f"NOTICE: --check-db skipped, database not present: "
                f"{args.check_db_path}"
            )
        else:
            drift = check_db_drift(args.check_db_path, load_allowlist())
            for error in drift:
                print(f"  [drift] {error}")
            print(
                f"Allowlist <-> DB reconciliation: {len(load_allowlist())} "
                f"entries checked, {len(drift)} drift error(s)"
            )
            if drift:
                return 1

    # Return exit code based on completeness
    incomplete = sum(1 for r in reports.values() if not r.is_complete)
    if incomplete and args.warn_only:
        print(
            "\n--warn-only: findings reported above are pending native-review "
            "triage (see libs/i18n/docs/quality-gates.md); exiting 0."
        )
        return 0
    return 0 if incomplete == 0 else 1


if __name__ == "__main__":
    exit(main())
