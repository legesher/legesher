#!/usr/bin/env python3
"""Pre-commit hook: prevent MIT packages from importing proprietary legesher-home.

libs/home/ (legesher-home) is proprietary (LicenseRef-Proprietary). MIT-licensed
packages must not import from it to avoid license contamination.
"""

import re
import sys
from pathlib import Path

# MIT-licensed package directories (must not import legesher_home)
MIT_PACKAGES = [
    "libs/core",
    "libs/i18n",
    "libs/language-server",
    "libs/vs-code",
    "libs/legesher",
]

IMPORT_PATTERN = re.compile(r"^\s*(?:from\s+legesher_home\b|import\s+legesher_home\b)")

DEP_PATTERN = re.compile(r"legesher[-_]home")


def check_python_imports(files: list[str]) -> tuple[list[str], list[str]]:
    """Check .py files for imports from legesher_home."""
    violations = []
    errors = []
    for filepath in files:
        if not filepath.endswith(".py"):
            continue
        if not any(filepath.startswith(pkg) for pkg in MIT_PACKAGES):
            continue
        try:
            content = Path(filepath).read_text()
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"  {filepath}: {exc}")
            continue
        for i, line in enumerate(content.splitlines(), 1):
            if IMPORT_PATTERN.match(line):
                violations.append(f"  {filepath}:{i}: {line.strip()}")
    return violations, errors


def check_dependency_refs(files: list[str]) -> tuple[list[str], list[str]]:
    """Check pyproject.toml files for dependency references to legesher-home."""
    violations = []
    errors = []
    for filepath in files:
        if not filepath.endswith("pyproject.toml"):
            continue
        if not any(filepath.startswith(pkg) for pkg in MIT_PACKAGES):
            continue
        try:
            content = Path(filepath).read_text()
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"  {filepath}: {exc}")
            continue
        for i, line in enumerate(content.splitlines(), 1):
            if DEP_PATTERN.search(line):
                violations.append(f"  {filepath}:{i}: {line.strip()}")
    return violations, errors


def main() -> int:
    files = sys.argv[1:]
    if not files:
        return 0

    import_violations, import_errors = check_python_imports(files)
    dep_violations, dep_errors = check_dependency_refs(files)
    all_errors = import_errors + dep_errors

    if not import_violations and not dep_violations and not all_errors:
        return 0

    if import_violations or dep_violations:
        print(
            "License boundary violation: MIT packages must not depend on legesher-home"
        )
        print("(libs/home/ is proprietary — LicenseRef-Proprietary)")
        print()

    if import_violations:
        print("Prohibited imports found:")
        for v in import_violations:
            print(v)
        print()

    if dep_violations:
        print("Prohibited dependency references found:")
        for v in dep_violations:
            print(v)
        print()

    if all_errors:
        print("Files could not be read (failing closed):")
        for e in all_errors:
            print(e)
        print()

    print("See CLAUDE.md 'License Boundary' section for details.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
