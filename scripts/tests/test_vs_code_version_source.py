"""The legesher-vs-code Python bundle's version follows the extension's (CORE-2416).

``libs/vs-code/package.json`` is the extension's one version source:
``release-apps.yml`` tags the extension ``vscode-v<version>`` from it, and the
``check-changelog-on-version-bump`` hook pairs it with the extension changelog.
``libs/vs-code/pyproject.toml``, the ``legesher-vs-code`` dependency bundle
built from the same directory, carries its own ``project.version`` that no
train bumps and the hook does not watch, so the two drifted (0.1.0 against
0.1.5). This guard is what now holds them together: a bump to either file
without the other fails here, naming both files and both values.

Run with:  uv run pytest scripts/tests -q
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

REPO = Path(__file__).resolve().parents[2]
PACKAGE_JSON = "libs/vs-code/package.json"
PYPROJECT = "libs/vs-code/pyproject.toml"


def _extension_version() -> str:
    manifest = json.loads((REPO / PACKAGE_JSON).read_text(encoding="utf-8"))
    return manifest["version"]


def _bundle_version() -> str:
    pyproject = tomllib.loads((REPO / PYPROJECT).read_text(encoding="utf-8"))
    return pyproject["project"]["version"]


def test_python_bundle_version_follows_package_json() -> None:
    """``project.version`` in the pyproject equals ``version`` in package.json."""
    extension = _extension_version()
    bundle = _bundle_version()
    assert bundle == extension, (
        f"{PYPROJECT} says version {bundle!r} but {PACKAGE_JSON} says {extension!r}:"
        " the Python bundle's version follows the extension's, so bump the"
        " pyproject to match package.json (CORE-2416)"
    )
