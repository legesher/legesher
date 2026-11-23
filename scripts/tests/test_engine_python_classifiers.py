"""The engine packages declare the same Python versions, through the newest one registered.

Six distributions make up the engine (the packs are separate and declare
their own tiers). Each carries a hand-kept list of
``Programming Language :: Python :: 3.X`` classifiers. A new Python release
has to reach all six; this guard fails when one is forgotten, when a list has
a hole in it, or when the lists stop short of the newest release the term
inventory registers. The inventory has a row for every release it has been
checked against, including one that added no word, so "newest registered" is
not "newest that added something".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from legesher_i18n.term_definitions import NEWEST_REGISTERED_VERSION

ROOT = Path(__file__).resolve().parents[2]
ENGINE_PACKAGES = (
    "core",
    "i18n",
    "language-server",
    "legesher",
    "mcp",
    "runtime",
)
#: ``libs/vs-code`` also has a ``pyproject.toml``: a dependency bundle for the
#: editor extension that is never published to an index, so its classifiers
#: are shown nowhere. It moves with the extension, not with the engine.
NOT_PUBLISHED = ("vs-code",)
CLASSIFIER = re.compile(
    r'^\s*"Programming Language :: Python :: (\d+)\.(\d+)",\s*$', re.M
)
FLOOR = re.compile(r'^requires-python\s*=\s*">=(\d+)\.(\d+)', re.M)


def _pyproject(package: str) -> str:
    return (ROOT / "libs" / package / "pyproject.toml").read_text(encoding="utf-8")


def _declared(package: str) -> list[tuple[int, int]]:
    return [
        (int(major), int(minor))
        for major, minor in CLASSIFIER.findall(_pyproject(package))
    ]


def _floor(package: str) -> tuple[int, int]:
    match = FLOOR.search(_pyproject(package))
    assert match, f"libs/{package}/pyproject.toml: no requires-python floor found"
    return int(match[1]), int(match[2])


def test_every_engine_package_directory_is_listed() -> None:
    # The six are named, not globbed, so that a seventh Python package cannot
    # arrive without someone deciding which list it belongs to.
    on_disk = sorted(
        path.parent.name for path in (ROOT / "libs").glob("*/pyproject.toml")
    )
    assert on_disk == sorted(ENGINE_PACKAGES + NOT_PUBLISHED)


@pytest.mark.parametrize("package", ENGINE_PACKAGES)
def test_classifiers_run_from_the_floor_without_a_gap(package: str) -> None:
    declared = _declared(package)
    assert declared, f"libs/{package}/pyproject.toml declares no Python minor version"
    assert declared == sorted(set(declared)), (
        f"libs/{package}: unordered or repeated: {declared}"
    )
    major, first_minor = _floor(package)
    expected = [(major, minor) for minor in range(first_minor, declared[-1][1] + 1)]
    assert declared == expected, (
        f"libs/{package}/pyproject.toml: classifiers {declared} are not every "
        f"minor from the requires-python floor {major}.{first_minor}"
    )


def test_all_engine_packages_declare_the_same_versions() -> None:
    by_package = {package: _declared(package) for package in ENGINE_PACKAGES}
    reference = by_package[ENGINE_PACKAGES[0]]
    differing = {
        f"libs/{package}/pyproject.toml": declared
        for package, declared in by_package.items()
        if declared != reference
    }
    assert differing == {}, f"expected {reference} everywhere, got {differing}"


@pytest.mark.parametrize("package", ENGINE_PACKAGES)
def test_classifiers_reach_the_newest_release_the_inventory_registers(
    package: str,
) -> None:
    major, minor = NEWEST_REGISTERED_VERSION.split(".")
    newest = (int(major), int(minor))
    assert _declared(package)[-1] >= newest, (
        f"libs/{package}/pyproject.toml stops at {_declared(package)[-1]}; the term "
        f"inventory registers Python {newest[0]}.{newest[1]}"
    )
