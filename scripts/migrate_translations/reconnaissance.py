#!/usr/bin/env python3
"""
Reconnaissance script for legesher-translations repository.

This script analyzes the old legesher-translations repo to understand:
1. What branches exist
2. What translation data exists on each branch
3. File formats and structure
4. Community review comments/PRs

Usage:
    uv run python scripts/migrate_translations/reconnaissance.py
"""

import json
import subprocess
from pathlib import Path
from typing import Any

# Configuration
OLD_REPO_URL = "https://github.com/legesher/legesher-translations.git"
WORK_DIR = Path(__file__).parent / "migration_data"
CLONE_DIR = WORK_DIR / "legesher-translations-clone"
OUTPUT_DIR = WORK_DIR / "analysis"


def setup_directories() -> None:
    """Create working directories."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created work directories in {WORK_DIR}")


def clone_repository() -> None:
    """Clone the old legesher-translations repository."""
    if CLONE_DIR.exists():
        print(f"✓ Repository already cloned at {CLONE_DIR}")
        return

    print(f"Cloning {OLD_REPO_URL}...")
    subprocess.run(
        ["git", "clone", OLD_REPO_URL, str(CLONE_DIR)],
        check=True,
        capture_output=True,
    )
    print(f"✓ Cloned repository to {CLONE_DIR}")


def get_all_branches() -> list[str]:
    """Get list of all branches in the repository."""
    result = subprocess.run(
        ["git", "branch", "-r"],
        cwd=CLONE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )

    branches = []
    for line in result.stdout.split("\n"):
        line = line.strip()
        if line and "origin/" in line and "HEAD" not in line:
            branch = line.replace("origin/", "")
            branches.append(branch)

    print(f"✓ Found {len(branches)} branches")
    return sorted(branches)


def analyze_branch(branch_name: str) -> dict[str, Any]:
    """Analyze a single branch to see what translation data exists."""
    print(f"\nAnalyzing branch: {branch_name}")

    # Checkout the branch
    subprocess.run(
        ["git", "checkout", branch_name],
        cwd=CLONE_DIR,
        capture_output=True,
        check=True,
    )

    analysis = {
        "branch": branch_name,
        "files": [],
        "directories": [],
        "translation_files": [],
        "file_formats": set(),
        "estimated_keywords": 0,
        "estimated_builtins": 0,
        "notes": [],
    }

    # Analyze directory structure
    for item in CLONE_DIR.rglob("*"):
        if item.is_file() and ".git" not in str(item):
            rel_path = item.relative_to(CLONE_DIR)
            analysis["files"].append(str(rel_path))

            # Check for translation-related files
            if any(
                keyword in str(rel_path).lower()
                for keyword in ["translation", "locale", "python", "keyword", "builtin"]
            ):
                analysis["translation_files"].append(str(rel_path))

            # Track file formats
            suffix = item.suffix.lower()
            if suffix:
                analysis["file_formats"].add(suffix)

    # Look for specific patterns
    locale_dir = CLONE_DIR / "locale"
    if locale_dir.exists():
        analysis["notes"].append(f"Has /locale directory with {len(list(locale_dir.rglob('*')))} items")

    # Check for Python-specific files
    python_files = list(CLONE_DIR.rglob("*python*.json")) + list(CLONE_DIR.rglob("*python*.yml"))
    if python_files:
        analysis["notes"].append(f"Found {len(python_files)} Python translation files")

    # Convert set to list for JSON serialization
    analysis["file_formats"] = sorted(list(analysis["file_formats"]))

    print(f"  → {len(analysis['files'])} files, {len(analysis['translation_files'])} translation files")

    return analysis


def generate_summary_report(analyses: list[dict[str, Any]]) -> None:
    """Generate a summary report of all branches."""
    report_path = OUTPUT_DIR / "reconnaissance_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Legesher-Translations Repository Reconnaissance Report\n\n")
        f.write(f"**Total Branches Analyzed**: {len(analyses)}\n\n")

        f.write("## Branch Summary\n\n")
        f.write("| Branch | Files | Translation Files | Formats | Notes |\n")
        f.write("|--------|-------|-------------------|---------|-------|\n")

        for analysis in analyses:
            formats = ", ".join(analysis["file_formats"][:3])  # Show first 3 formats
            notes = analysis["notes"][0] if analysis["notes"] else "No notes"
            f.write(
                f"| {analysis['branch']} | "
                f"{len(analysis['files'])} | "
                f"{len(analysis['translation_files'])} | "
                f"{formats} | "
                f"{notes} |\n"
            )

        f.write("\n## Detailed Analysis\n\n")
        for analysis in analyses:
            f.write(f"### {analysis['branch']}\n\n")
            f.write(f"**Files**: {len(analysis['files'])}\n\n")

            if analysis['translation_files']:
                f.write("**Translation Files**:\n")
                for tf in analysis['translation_files'][:10]:  # Show first 10
                    f.write(f"- `{tf}`\n")
                if len(analysis['translation_files']) > 10:
                    f.write(f"- _(and {len(analysis['translation_files']) - 10} more)_\n")
                f.write("\n")

            if analysis['notes']:
                f.write("**Notes**:\n")
                for note in analysis['notes']:
                    f.write(f"- {note}\n")
                f.write("\n")

    print(f"\n✓ Summary report written to {report_path}")


def save_detailed_data(analyses: list[dict[str, Any]]) -> None:
    """Save detailed analysis data as JSON."""
    data_path = OUTPUT_DIR / "detailed_analysis.json"

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(analyses, f, indent=2, ensure_ascii=False)

    print(f"✓ Detailed data saved to {data_path}")


def main() -> None:
    """Main reconnaissance workflow."""
    print("=" * 70)
    print("LEGESHER-TRANSLATIONS REPOSITORY RECONNAISSANCE")
    print("=" * 70)

    # Setup
    setup_directories()
    clone_repository()

    # Get all branches
    branches = get_all_branches()

    # Analyze each branch (focus on translation branches first)
    translation_branches = [b for b in branches if "translation" in b.lower()]
    other_branches = [b for b in branches if "translation" not in b.lower()]

    print(f"\n📊 Analyzing {len(translation_branches)} translation branches...")
    print(f"   ({len(other_branches)} non-translation branches will be analyzed after)\n")

    analyses = []

    # Analyze translation branches first
    for branch in translation_branches[:5]:  # Start with first 5 to test
        try:
            analysis = analyze_branch(branch)
            analyses.append(analysis)
        except Exception as e:
            print(f"  ⚠️  Error analyzing {branch}: {e}")

    # Generate reports
    if analyses:
        generate_summary_report(analyses)
        save_detailed_data(analyses)

        print("\n" + "=" * 70)
        print("RECONNAISSANCE COMPLETE")
        print("=" * 70)
        print(f"\nNext steps:")
        print(f"1. Review the report: {OUTPUT_DIR / 'reconnaissance_report.md'}")
        print(f"2. Check detailed data: {OUTPUT_DIR / 'detailed_analysis.json'}")
        print(f"3. Run full analysis on all branches (currently analyzed {len(analyses)}/{len(branches)})")
    else:
        print("\n⚠️  No analyses completed successfully")


if __name__ == "__main__":
    main()
