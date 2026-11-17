"""The declared ranges keep releases with published advisories out of an install.

``tests/dependency_floors.py`` holds the ledger and says why the declared
range, and not the lock file, is what protects someone installing the wheel.
The cases come from ``pyproject.toml`` itself, so a requirement added later is
checked without anyone remembering to list it here.
"""

from __future__ import annotations

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from tests.dependency_floors import (
    REVIEWED,
    declared_requirements,
    newest_covered_release_below_the_floor,
    problems,
)

REQUIREMENTS = declared_requirements()
DECLARED_NAMES = {canonicalize_name(requirement.name) for requirement in REQUIREMENTS}


def test_the_wheel_declares_third_party_requirements() -> None:
    """An empty parametrization below would pass while checking nothing."""
    assert "mcp" in DECLARED_NAMES, f"pyproject.toml no longer requires the SDK: {REQUIREMENTS}"


@pytest.mark.parametrize("requirement", REQUIREMENTS, ids=str)
def test_every_requirement_line_keeps_to_the_ledger(requirement: Requirement) -> None:
    found = problems(requirement)
    assert not found, "\n".join(found)


@pytest.mark.parametrize("name", sorted(REVIEWED))
def test_the_ledger_names_only_current_requirements(name: str) -> None:
    assert name in DECLARED_NAMES, (
        f"REVIEWED still lists {name!r}, which pyproject.toml no longer requires"
    )


@pytest.mark.parametrize("name", sorted(REVIEWED))
def test_each_ledger_entry_agrees_with_itself(name: str) -> None:
    """A floor no advisory covers, and one its own check accepts."""
    reviewed = REVIEWED[name]
    assert reviewed.floor not in reviewed.covered, (
        f"REVIEWED[{name!r}] names {reviewed.floor} as both the floor and a covered release"
    )
    assert not problems(Requirement(f"{name}=={reviewed.floor}")), (
        f"REVIEWED[{name!r}] rejects its own floor {reviewed.floor}"
    )


def test_the_sdk_entry_names_an_older_release_to_install_over() -> None:
    """The scheduled install test starts from a covered SDK release below the floor."""
    older = newest_covered_release_below_the_floor("mcp")
    assert Version(older) < Version(REVIEWED["mcp"].floor)
