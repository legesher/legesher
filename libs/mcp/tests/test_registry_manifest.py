"""The registry manifest describes the package that ships, and nothing else.

``server.json`` is what the official MCP registry reads at submission. It
repeats facts that live elsewhere: the distribution name and version come
from ``pyproject.toml``; the server name is checked by the registry against
an ``mcp-name:`` marker in the README that PyPI publishes as the package
description; and the registry enforces a shape on the name, a bound on the
description, and exact (never ranged) versions. Nothing runs the manifest
until submission day, so any of these can drift silently. The drift is
pinned here instead.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10 (tomli ships with pytest there)
    import tomli as tomllib  # type: ignore[import-not-found,unused-ignore]

from legesher_mcp import server as server_module

PACKAGE_DIR = Path(__file__).resolve().parents[1]
MANIFEST = PACKAGE_DIR / "server.json"
PYPROJECT = PACKAGE_DIR / "pyproject.toml"
README = PACKAGE_DIR / "README.md"
SERVER_SOURCE = PACKAGE_DIR / "legesher_mcp" / "server.py"

#: Facts the registry enforces, from server.schema.json (2025-12-11).
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+$")
DESCRIPTION_MAX = 100
#: One exact version: digits and dots, then an optional pre-release or build
#: tag introduced by `-` or `+`. Range syntax (^, ~, >=, 1.x, 1.*) is
#: rejected by the registry, and by this pattern.
EXACT_VERSION = re.compile(r"^\d+(\.\d+)*([-+][0-9A-Za-z.-]+)?$")
MARKER = re.compile(r"mcp-name:\s*(\S+)")
#: Every environment variable the server module reads, by either access form.
ENVIRONMENT_READ = re.compile(r'os\.environ(?:\.get\(|\[)"([A-Z0-9_]+)"')


@pytest.fixture(scope="module")
def manifest() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture(scope="module")
def project() -> dict[str, Any]:
    loaded: dict[str, Any] = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    return loaded


def test_the_manifest_carries_the_registry_required_fields(manifest: dict[str, Any]) -> None:
    for field in ("name", "description", "version"):
        assert manifest.get(field), f"server.json: required field {field!r} is missing or empty"
    assert manifest.get("$schema", "").startswith(
        "https://static.modelcontextprotocol.io/schemas/"
    ), "server.json: $schema must point at the registry's published schema"


def test_the_server_name_has_the_registry_shape(manifest: dict[str, Any]) -> None:
    name = manifest["name"]
    assert NAME_PATTERN.match(name), f"server.json: name {name!r} is not namespace/server"
    assert name.count("/") == 1, f"server.json: name {name!r} must contain exactly one slash"
    assert 3 <= len(name) <= 200


def test_the_description_fits_the_registry_bound(manifest: dict[str, Any]) -> None:
    description = manifest["description"]
    assert 1 <= len(description) <= DESCRIPTION_MAX, (
        f"server.json: description is {len(description)} characters; "
        f"the registry allows at most {DESCRIPTION_MAX}"
    )


def test_the_manifest_version_is_the_package_version(
    manifest: dict[str, Any], project: dict[str, Any]
) -> None:
    assert manifest["version"] == project["version"], (
        f"server.json version {manifest['version']!r} != pyproject.toml version "
        f"{project['version']!r}"
    )
    assert EXACT_VERSION.match(manifest["version"]), (
        f"server.json: version {manifest['version']!r} is not one exact version"
    )


def test_the_package_entry_is_this_distribution_on_pypi(
    manifest: dict[str, Any], project: dict[str, Any]
) -> None:
    packages = manifest.get("packages", [])
    assert len(packages) == 1, f"server.json: expected one package entry, found {len(packages)}"
    package = packages[0]
    assert package["registryType"] == "pypi"
    assert package["registryBaseUrl"] == "https://pypi.org"
    assert package["identifier"] == project["name"], (
        f"server.json package identifier {package['identifier']!r} != "
        f"pyproject.toml name {project['name']!r}"
    )
    assert package["version"] == project["version"], (
        f"server.json package version {package['version']!r} != "
        f"pyproject.toml version {project['version']!r}"
    )
    assert package["runtimeHint"] == "uvx"
    assert package["transport"] == {"type": "stdio"}


def test_the_readme_carries_the_matching_ownership_marker(manifest: dict[str, Any]) -> None:
    """The registry proves PyPI ownership by finding ``mcp-name: <name>`` in
    the README that PyPI shows as the package description. A marker that
    names anything other than the manifest's name fails the submission."""
    markers = MARKER.findall(README.read_text(encoding="utf-8"))
    assert markers == [manifest["name"]], (
        f"README mcp-name markers {markers!r} must be exactly [{manifest['name']!r}]"
    )


def test_the_repository_points_at_this_package(manifest: dict[str, Any]) -> None:
    repository = manifest["repository"]
    assert repository["source"] == "github"
    assert repository["url"].startswith("https://github.com/")
    expected = f"{PACKAGE_DIR.parent.name}/{PACKAGE_DIR.name}"
    assert repository["subfolder"] == expected, (
        f"server.json repository.subfolder {repository['subfolder']!r} != {expected!r}"
    )


def test_the_listed_environment_variables_are_the_ones_the_server_reads(
    manifest: dict[str, Any],
) -> None:
    read_by_server = set(ENVIRONMENT_READ.findall(SERVER_SOURCE.read_text(encoding="utf-8")))
    variables = manifest["packages"][0].get("environmentVariables", [])
    assert variables, "server.json: the log-level variable should be listed"
    listed = {variable["name"] for variable in variables}
    assert listed == read_by_server, (
        f"server.json lists {sorted(listed)} but legesher_mcp/server.py reads "
        f"{sorted(read_by_server)}; the two must match"
    )
    for variable in variables:
        assert variable.get("isSecret", False) is False, (
            f"{variable['name']}: nothing the server reads is a secret"
        )
    by_name = {variable["name"]: variable for variable in variables}
    log_level = by_name["LEGESHER_MCP_LOG_LEVEL"]
    assert tuple(log_level["choices"]) == server_module._LOG_LEVELS, (
        "server.json: LEGESHER_MCP_LOG_LEVEL choices drifted from the server's accepted levels"
    )
    assert log_level["default"] == server_module._DEFAULT_LOG_LEVEL
