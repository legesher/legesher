#!/usr/bin/env python3
"""Pre-commit hook: internal legesher-* dependencies must carry version bounds.

In-repo, the root [tool.uv.sources] workspace override masks any missing
constraint. Wheel metadata does not: the declared range is all a published
wheel carries, so an unconstrained (or unbounded) sibling dependency resolves
to whatever is newest on the index, including a future incompatible major
(CORE-1569, CORE-1598).

Checks every workspace member pyproject.toml. Each dependency on another
workspace member must declare a specifier with an upper bound
(e.g. ">=0.22.0,<1.0.0"). The root pyproject.toml (legesher-monorepo) is
exempt: it is the unpublished workspace virtual package.
"""

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

REPO_ROOT = Path(__file__).resolve().parent.parent

UPPER_BOUND_OPERATORS = {"<", "<=", "==", "~="}


def member_pyprojects() -> list[Path]:
    root = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    members = root["tool"]["uv"]["workspace"]["members"]
    paths = []
    for pattern in members:
        for match in sorted(REPO_ROOT.glob(pattern)):
            pyproject = match / "pyproject.toml"
            if pyproject.is_file():
                paths.append(pyproject)
    return paths


def main() -> int:
    projects: dict[Path, dict] = {}
    internal_names: set[str] = set()
    for path in member_pyprojects():
        project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})
        projects[path] = project
        internal_names.add(canonicalize_name(project["name"]))

    errors = []
    for path, project in projects.items():
        dep_lists = [project.get("dependencies", [])]
        dep_lists.extend(project.get("optional-dependencies", {}).values())
        for dep in (dep for deps in dep_lists for dep in deps):
            req = Requirement(dep)
            if canonicalize_name(req.name) not in internal_names:
                continue
            has_upper_bound = any(
                spec.operator in UPPER_BOUND_OPERATORS for spec in req.specifier
            )
            if not has_upper_bound:
                rel_path = path.relative_to(REPO_ROOT)
                problem = "no version constraint" if not req.specifier else "no upper bound"
                errors.append(f'  {rel_path}: "{dep}" has {problem}')

    if errors:
        print("Internal dependency constraint check failed:")
        print()
        for err in errors:
            print(err)
        print()
        print("Internal legesher-* dependencies ship in wheel metadata, where the")
        print("[tool.uv.sources] workspace override does not exist. Declare a bounded")
        print('range, e.g. "legesher-i18n>=0.22.0,<1.0.0" (see CORE-1598).')
        print()
        print("To bypass this check: git commit --no-verify")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
