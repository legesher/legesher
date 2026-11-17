"""The reviewed minimum for each third-party requirement the wheel declares.

A lock file never reaches someone who installs the published wheel: their
resolver reads the wheel's ``Requires-Dist`` and keeps whatever release an
environment already holds, as long as the declared range admits it. The
declared range is therefore the only lever that keeps a release with a
published advisory out of an install.

``REVIEWED`` is the ledger. For every third-party package ``pyproject.toml``
declares, it records what the GitHub Advisory Database showed on the date
beside the entry: the first release outside every advisory published for the
package, and releases that an advisory still covers, on every release line.
``tests/test_dependency_floors.py`` checks the declared ranges against it in
the default run, and ``tests/test_clean_environment.py`` checks the built
wheel's own metadata against it in the scheduled run.

When a new advisory is published for one of these packages, raise the entry's
floor to the release that fixes it, add the newest release it covers, and
change the range in ``pyproject.toml`` with them.

The ledger covers what this package declares. A package the SDK brings in is
held to the SDK's own range, not to one written here.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10 (tomli ships with pytest there)
    import tomli as tomllib  # type: ignore[import-not-found,unused-ignore]

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


@dataclass(frozen=True)
class Reviewed:
    """What the advisory database showed for one package."""

    #: The lowest release a declared range may start at: the first release
    #: outside every published advisory on the release line the range uses.
    floor: str
    #: Releases an advisory still covers, at least the newest one on each
    #: release line that has any. A declared range must admit none of them.
    #: Empty for a package with no published advisory.
    covered: tuple[str, ...] = ()


#: Canonical package name -> what was read, and when.
REVIEWED: dict[str, Reviewed] = {
    # Read 2026-11-17. Advisories cover 1.x below 1.30.0 and 2.x below 2.2.0,
    # so the cap matters as much as the floor: the range has to stay off the
    # 2.x releases below 2.2.0 if it is ever widened.
    "mcp": Reviewed(floor="1.30.0", covered=("1.29.1", "2.0.0", "2.1.1")),
    # Read 2026-11-17. The 2.x advisory ends at 2.4.0; the 1.x one at 1.10.13.
    "pydantic": Reviewed(floor="2.4.0", covered=("1.10.12", "2.3.0")),
}

#: Operators that put a lower bound on a version range.
_LOWER_BOUND_OPERATORS = frozenset({">=", ">", "==", "~=", "==="})


def _pyproject() -> dict[str, Any]:
    loaded: dict[str, Any] = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return loaded


def _workspace_packages() -> frozenset[str]:
    """The sibling packages, which this repository releases itself."""
    sources: dict[str, Any] = _pyproject().get("tool", {}).get("uv", {}).get("sources", {})
    return frozenset(
        canonicalize_name(name)
        for name, source in sources.items()
        if isinstance(source, dict) and source.get("workspace") is True
    )


def third_party(lines: Iterable[str]) -> list[Requirement]:
    """The requirement lines that name a package this repository does not release."""
    siblings = _workspace_packages()
    requirements = (Requirement(line) for line in lines)
    return [
        requirement
        for requirement in requirements
        if canonicalize_name(requirement.name) not in siblings
    ]


def declared_requirements() -> list[Requirement]:
    """Every third-party requirement line in ``pyproject.toml``, extras included.

    A list, not a mapping by name: a package may be required on two lines
    (one per environment marker, or once with an extra), and each line ships
    in the wheel, so each one is checked.
    """
    project: dict[str, Any] = _pyproject()["project"]
    lines: list[str] = list(project["dependencies"])
    for extra in project.get("optional-dependencies", {}).values():
        lines.extend(extra)
    return third_party(lines)


def declared_floor(requirement: Requirement) -> Version | None:
    """The highest lower bound a requirement states, or None when it has none.

    An exclusive bound (``>1.2``) counts as its own version, so a range has to
    be written ``>=`` the reviewed floor to pass. That is stricter than the
    resolver and keeps the check free of any list of published releases.
    """
    bounds = [
        Version(specifier.version.removesuffix(".*"))
        for specifier in requirement.specifier
        if specifier.operator in _LOWER_BOUND_OPERATORS
    ]
    return max(bounds) if bounds else None


def problems(requirement: Requirement) -> list[str]:
    """Why a requirement line fails the ledger; empty when it passes."""
    name = canonicalize_name(requirement.name)
    line = str(requirement)
    reviewed = REVIEWED.get(name)
    if reviewed is None:
        return [
            f"{line!r}: {name} has no entry in REVIEWED (tests/dependency_floors.py); "
            "read its published advisories and record the first release outside all of them"
        ]
    found: list[str] = []
    floor = declared_floor(requirement)
    if floor is None:
        found.append(f"{line!r} has no lower bound, so an install may keep any older release")
    elif floor < Version(reviewed.floor):
        found.append(
            f"{line!r} puts its lower bound at {name} {floor}, below {reviewed.floor}, the "
            "reviewed floor (the first release outside every published advisory on its "
            f"line): an install into an environment that already holds an older {name} "
            f"could keep it. Write the range as >={reviewed.floor} or later"
        )
    found.extend(
        f"{line!r} admits {name} {release}, which a published advisory covers"
        for release in reviewed.covered
        if requirement.specifier.contains(release, prereleases=True)
    )
    return found


def newest_covered_release_below_the_floor(name: str) -> str:
    """The release an older environment would hold: the newest one below the floor."""
    reviewed = REVIEWED[name]
    below = [release for release in reviewed.covered if Version(release) < Version(reviewed.floor)]
    assert below, f"REVIEWED[{name!r}] lists no covered release below its floor {reviewed.floor}"
    return max(below, key=Version)
