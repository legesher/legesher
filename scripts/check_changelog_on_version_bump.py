#!/usr/bin/env python3
"""Pre-commit hook: ensure CHANGELOG is updated when package version changes.

Checks that if a pyproject.toml or package.json version field is modified,
the corresponding CHANGELOG.md (and root CHANGELOG.md) also has changes
in the same commit.
"""

import re
import subprocess
import sys

# Map from version file to its changelog
PACKAGE_MAP = {
    "libs/core/pyproject.toml": "libs/core/CHANGELOG.md",
    "libs/i18n/pyproject.toml": "libs/i18n/CHANGELOG.md",
    "libs/legesher/pyproject.toml": "libs/legesher/CHANGELOG.md",
    "libs/language-server/pyproject.toml": "libs/language-server/CHANGELOG.md",
    "libs/home/pyproject.toml": "libs/home/CHANGELOG.md",
    "libs/vs-code/package.json": "libs/vs-code/CHANGELOG.md",
}

ROOT_CHANGELOG = "CHANGELOG.md"


def get_staged_files() -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return set(result.stdout.strip().splitlines())


def has_version_change(filepath: str) -> bool:
    """Check if the staged diff for this file includes a version field change."""
    result = subprocess.run(
        ["git", "diff", "--cached", "-U0", filepath],
        capture_output=True,
        text=True,
        check=True,
    )
    diff = result.stdout
    is_toml = filepath.endswith(".toml")
    # Match the package version field specifically:
    #   pyproject.toml: version = "x.y.z" (top-level, not python_version etc.)
    #   package.json:   "version": "x.y.z"
    pattern = re.compile(r"^version\s*=" if is_toml else r'^\s*"version"\s*:')
    for line in diff.splitlines():
        if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
            continue
        # Strip the leading +/- for matching
        content = line[1:]
        if pattern.match(content):
            return True
    return False


def main() -> int:
    staged = get_staged_files()
    errors = []
    any_version_bumped = False

    for version_file, changelog_file in PACKAGE_MAP.items():
        if version_file not in staged:
            continue
        if not has_version_change(version_file):
            continue

        any_version_bumped = True

        # Version was bumped — check changelog is also staged
        if changelog_file not in staged:
            errors.append(
                f"  {version_file} has a version bump but {changelog_file} is not updated"
            )

    # Check root CHANGELOG once, after processing all packages
    if any_version_bumped and ROOT_CHANGELOG not in staged:
        errors.append(
            f"  {ROOT_CHANGELOG} should be updated with a package version table"
        )

    if errors:
        print("CHANGELOG check failed:")
        print()
        for err in errors:
            print(err)
        print()
        print("When bumping a package version, update both its CHANGELOG.md")
        print("and the root CHANGELOG.md with the package version manifest table.")
        print()
        print("To bypass this check: git commit --no-verify")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
