#!/usr/bin/env python3
"""Stamp changelogs on foundation release.

After semantic-release bumps versions, this script:
1. Reads the new version from root pyproject.toml
2. Stamps [Unreleased] -> [x.y.z] - date in all changelogs
3. Updates the Package Versions table in root CHANGELOG.md

Usage:
    python scripts/stamp-changelog-release.py           # stamp with current version
    python scripts/stamp-changelog-release.py --dry-run  # preview changes

Designed to run in the release-foundation.yml workflow after
semantic-release bumps versions. Can also be run manually.

Refs: CORE-608, CORE-612
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Foundation changelogs to stamp
CHANGELOGS = [
    Path("CHANGELOG.md"),
    Path("libs/core/CHANGELOG.md"),
    Path("libs/i18n/CHANGELOG.md"),
    Path("libs/legesher/CHANGELOG.md"),
]

# Package version sources for the root CHANGELOG table
PACKAGE_VERSIONS = {
    "legesher-core": Path("libs/core/pyproject.toml"),
    "legesher-i18n": Path("libs/i18n/pyproject.toml"),
    "legesher (CLI)": Path("libs/legesher/pyproject.toml"),
    "legesher-language-server": Path("libs/language-server/pyproject.toml"),
    "legesher-vscode": Path("libs/vs-code/package.json"),
}


def get_version_from_toml(path: Path) -> str | None:
    """Read version from a pyproject.toml file."""
    if not path.exists():
        return None
    match = re.search(r'^version = "([^"]+)"', path.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def get_version_from_json(path: Path) -> str | None:
    """Read version from a package.json file."""
    if not path.exists():
        return None
    match = re.search(r'"version":\s*"([^"]+)"', path.read_text())
    return match.group(1) if match else None


def get_package_version(path: Path) -> str | None:
    """Get version for a package from its config file."""
    if path.name == "package.json":
        return get_version_from_json(path)
    return get_version_from_toml(path)


def stamp_unreleased(content: str, version: str, date: str) -> str:
    """Replace ## [Unreleased] with ## [Unreleased] + ## [version] - date.

    Idempotent: returns content unchanged if the version heading already exists.
    """
    if f"## [{version}]" in content:
        return content
    return content.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{version}] - {date}",
        1,  # Only replace the first occurrence
    )


def update_version_table(content: str) -> str:
    """Update the Package Versions table in root CHANGELOG with actual versions.

    Finds the FIRST Package Versions table (under [Unreleased]) and updates
    version numbers from each package's config file.
    """
    lines = content.split("\n")
    in_table = False
    table_start = -1

    for i, line in enumerate(lines):
        if "### Package Versions" in line:
            table_start = i
            continue
        if table_start >= 0 and line.startswith("| ") and "---" not in line:
            if "Package" in line and "Version" in line:
                continue  # Skip header row
            in_table = True

            # Parse the package name from the table row
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 4:
                pkg_name = cols[1]
                for name, path in PACKAGE_VERSIONS.items():
                    if pkg_name == name:
                        actual_version = get_package_version(path)
                        if actual_version:
                            lines[i] = re.sub(
                                r"\|\s*[\d.]+\s*\|",
                                f"| {actual_version:<7} |",
                                line,
                                count=1,
                            )
                        break
        elif in_table and not line.startswith("| "):
            break  # End of first table

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Stamp changelogs on release")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without modifying"
    )
    parser.add_argument(
        "--version",
        help="Version to stamp (default: read from root pyproject.toml)",
    )
    parser.add_argument(
        "--date",
        help="Release date YYYY-MM-DD (default: today UTC)",
    )
    args = parser.parse_args()

    # Get version
    version = args.version
    if not version:
        version = get_version_from_toml(Path("pyproject.toml"))
        if not version:
            print("Could not read version from pyproject.toml")
            return 1

    if not re.match(r"^\d+\.\d+\.\d+", version):
        print(f"Invalid version format: {version}")
        return 1

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: {args.date}. Expected YYYY-MM-DD.")
            return 1

    print(f"Stamping changelogs with v{version} ({date})")
    if args.dry_run:
        print("DRY RUN - no files will be modified\n")

    modified_files: list[Path] = []

    # Step 1: Update root CHANGELOG version table
    root_cl = Path("CHANGELOG.md")
    if root_cl.exists():
        content = root_cl.read_text()
        updated = update_version_table(content)
        if updated != content:
            if not args.dry_run:
                root_cl.write_text(updated)
            print(f"  Updated version table in {root_cl}")
            modified_files.append(root_cl)

    # Step 2: Stamp [Unreleased] in all changelogs
    for cl_path in CHANGELOGS:
        if not cl_path.exists():
            print(f"  Skipping {cl_path} (not found)")
            continue

        content = cl_path.read_text()
        if "## [Unreleased]" not in content:
            print(f"  Skipping {cl_path} (no [Unreleased] section)")
            continue

        stamped = stamp_unreleased(content, version, date)
        if stamped != content:
            if not args.dry_run:
                cl_path.write_text(stamped)
            print(f"  Stamped {cl_path}")
            if cl_path not in modified_files:
                modified_files.append(cl_path)

    if modified_files:
        print(f"\nStamped {len(modified_files)} file(s) with v{version}")
        if args.dry_run:
            print("Run without --dry-run to apply changes.")
    else:
        print("\nNo changelogs needed stamping.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
