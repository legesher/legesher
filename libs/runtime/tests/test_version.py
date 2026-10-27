"""One version, read from the distribution (CORE-2359).

``legesher-runtime`` has no release train: ``project.version`` in
``pyproject.toml`` is bumped by hand before the ``runtime`` target of
``publish-pypi.yml`` is dispatched. ``__version__`` used to be a literal copy
of it, bumped by hand alongside it with nothing checking the two, so a bump in
one place and not the other would have shipped a wheel whose ``__version__``
disagreed with its own metadata. ``__version__`` now reads the
installed distribution's metadata, as ``legesher-mcp`` and
``legesher-language-server`` do, and these tests keep a literal from coming
back. Each compares against ``importlib.metadata``, not a literal, so a bump
never has to edit this file.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pytest

import legesher_runtime

DISTRIBUTION = "legesher-runtime"
PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"

#: ``version = "..."`` at the start of a line: the [project] table's entry.
#: ``python_version`` under [tool.mypy] does not match, because of the anchor.
PROJECT_VERSION = re.compile(r'^version = "([^"]+)"$', re.MULTILINE)

#: A three-part version anywhere in a string. The digits and dots on either
#: side are excluded so that the uninstalled-tree fallback ``"0.0.0.dev0"``
#: does not match.
VERSION_IN_STRING = re.compile(r"(?<![\d.])v?\d+\.\d+\.\d+(?![\d.])")


def _installed_version() -> str:
    try:
        return version(DISTRIBUTION)
    except PackageNotFoundError:
        pytest.fail(f"{DISTRIBUTION} is not installed in this environment; run `uv sync`")


def test_dunder_version_is_the_distribution_version() -> None:
    installed = _installed_version()
    assert legesher_runtime.__version__ == installed, (
        f"__version__ is {legesher_runtime.__version__!r} but the installed "
        f"{DISTRIBUTION} metadata says {installed!r}; __version__ must read the "
        "metadata, not a literal"
    )


def test_pyproject_version_is_the_distribution_version() -> None:
    """The hand-bumped field and the installed metadata agree.

    A bump that is not followed by a sync leaves the environment, and so
    ``__version__``, on the old number while the wheel would carry the new one.
    """
    match = PROJECT_VERSION.search(PYPROJECT.read_text(encoding="utf-8"))
    assert match is not None, f"no project.version in {PYPROJECT}"
    installed = _installed_version()
    assert match.group(1) == installed, (
        f"pyproject.toml says {match.group(1)!r} but the installed {DISTRIBUTION} "
        f"metadata says {installed!r}; run `uv sync` after bumping the version"
    )


def _string_constants(source: str) -> Iterator[tuple[int, str]]:
    """Every string constant in the code, f-string parts included, docstrings excluded."""
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            yield node.lineno, node.value


def test_no_version_literal_in_the_package_source() -> None:
    """A hard-coded version could drift from the metadata; keep one from coming back.

    Checks string constants, so a reintroduced ``__version__ = "0.1.0"`` is
    caught even while it happens to equal the metadata. Comments and docstrings
    are not checked: they can mention a version without reporting one.
    """
    init = legesher_runtime.__file__
    assert init is not None
    package = Path(init).parent
    offenders = [
        f"{path.relative_to(package)}:{number}: {value!r}"
        for path in sorted(package.rglob("*.py"))
        for number, value in _string_constants(path.read_text(encoding="utf-8"))
        if VERSION_IN_STRING.search(value)
    ]
    assert offenders == [], "hard-coded version literals:\n" + "\n".join(offenders)
