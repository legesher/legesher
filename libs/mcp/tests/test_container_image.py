"""``libs/mcp/Dockerfile`` downloads only what it names.

A directory that builds the server from source runs whatever the recipe
fetches on the day of the build. The checked-in Dockerfile exists so that
build can be reproduced, which holds only while each image carries a digest,
each tool an exact version, and each dependency resolution a date.

The checks are an allowlist, not a search for known mistakes: the file may
use only the instructions, images and commands listed here, so anything new
(another install, another image, a download in a ``RUN`` step) fails until
it is reviewed and added. Building the image and driving a session is
``tests/test_container_session.py``.
"""

from __future__ import annotations

import datetime
import re
import sys
from typing import Any

import pytest
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from tests.container_image import (
    DOCKERFILE,
    LISTING_COMMAND,
    PACKAGE_DIR,
    SERVER_EXECUTABLE,
    build_arguments,
    command,
    image_references,
    instructions,
    run_commands,
)

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10 (tomli ships with pytest there)
    import tomli as tomllib  # type: ignore[import-not-found,unused-ignore]

LISTINGS_DOC = PACKAGE_DIR / "docs" / "registry-listings.md"

#: The only instructions the file may use. ``ADD``, ``ENTRYPOINT``, ``SHELL``
#: and the rest each change what is fetched or what runs.
ALLOWED_INSTRUCTIONS = {"FROM", "COPY", "ARG", "ENV", "RUN", "USER", "WORKDIR", "CMD"}

#: The only image repositories the build may pull, each once.
ALLOWED_IMAGES = ["node", "ghcr.io/astral-sh/uv"]

#: Every command the build may run, in order. Each install names its version
#: argument, and each one that resolves dependencies names the date.
EXPECTED_COMMANDS = [
    'npm install --global --before="${RESOLVED_BEFORE}" "mcp-proxy@${MCP_PROXY_VERSION}"',
    "npm cache clean --force",
    'uv python install "${PYTHON_VERSION}"',
    "uv venv /opt/legesher-mcp",
    "uv pip install --python /opt/legesher-mcp/bin/python"
    ' --exclude-newer "${RESOLVED_BEFORE}" "legesher-mcp==${LEGESHER_MCP_VERSION}"',
]

#: The build arguments, and nothing else.
EXPECTED_ARGUMENTS = {
    "RESOLVED_BEFORE",
    "PYTHON_VERSION",
    "MCP_PROXY_VERSION",
    "LEGESHER_MCP_VERSION",
}

#: The environment the file may set. None of these is a version or an index.
ALLOWED_ENVIRONMENT = {
    "UV_PYTHON": "${PYTHON_VERSION}",
    "UV_PYTHON_INSTALL_DIR": "/opt/python",
    "UV_NO_CACHE": "1",
    "NPM_CONFIG_UPDATE_NOTIFIER": "false",
    "NPM_CONFIG_FUND": "false",
}

_PINNED_IMAGE = re.compile(
    r"^(?P<repository>[^:@]+):(?P<tag>\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?)@sha256:[0-9a-f]{64}$"
)
_EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+$")

IMAGES = image_references()
ARGUMENTS = build_arguments()
VERSION_ARGUMENTS = sorted(name for name in ARGUMENTS if name.endswith("_VERSION"))


def _project() -> dict[str, Any]:
    loaded: dict[str, Any] = tomllib.loads(
        (PACKAGE_DIR / "pyproject.toml").read_text(encoding="utf-8")
    )
    project: dict[str, Any] = loaded["project"]
    return project


def test_it_uses_only_the_reviewed_instructions() -> None:
    used = {keyword for keyword, _ in instructions()}
    assert used <= ALLOWED_INSTRUCTIONS, (
        f"{DOCKERFILE.name} uses {sorted(used - ALLOWED_INSTRUCTIONS)}, outside the reviewed "
        f"set {sorted(ALLOWED_INSTRUCTIONS)}"
    )


def test_it_pulls_exactly_the_reviewed_images() -> None:
    """A dropped or added image changes this list, so neither goes unseen."""
    repositories = [image.split("@")[0].rsplit(":", 1)[0] for image in IMAGES]
    assert repositories == ALLOWED_IMAGES, (
        f"{DOCKERFILE.name} pulls {IMAGES}; the reviewed images are {ALLOWED_IMAGES}"
    )


@pytest.mark.parametrize("image", IMAGES)
def test_every_image_is_pinned_by_digest_and_exact_tag(image: str) -> None:
    assert _PINNED_IMAGE.match(image), (
        f"{image!r} is not written as repository:1.2.3@sha256:<digest>, so the build "
        "pulls whatever the name points at on the day"
    )


def test_it_declares_exactly_the_reviewed_arguments() -> None:
    assert set(ARGUMENTS) == EXPECTED_ARGUMENTS, (
        f"{DOCKERFILE.name} declares {sorted(ARGUMENTS)}, not {sorted(EXPECTED_ARGUMENTS)}"
    )


@pytest.mark.parametrize("name", VERSION_ARGUMENTS)
def test_every_version_argument_defaults_to_one_exact_release(name: str) -> None:
    default = ARGUMENTS[name]
    assert default is not None and _EXACT_VERSION.match(default), (
        f"ARG {name} defaults to {default!r}; it must name one release, as 1.2.3"
    )


def test_the_resolution_date_is_one_calendar_day() -> None:
    default = ARGUMENTS["RESOLVED_BEFORE"]
    try:
        datetime.date.fromisoformat(str(default))
    except ValueError:
        pytest.fail(f"ARG RESOLVED_BEFORE defaults to {default!r}; it must be a date, YYYY-MM-DD")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(default)), (
        f"ARG RESOLVED_BEFORE defaults to {default!r}; write it as YYYY-MM-DD"
    )


def test_it_runs_exactly_the_reviewed_commands() -> None:
    """Any other command is a download or a change nobody reviewed."""
    ran = run_commands()
    unexpected = [step for step in ran if step not in EXPECTED_COMMANDS]
    missing = [step for step in EXPECTED_COMMANDS if step not in ran]
    assert ran == EXPECTED_COMMANDS, (
        f"{DOCKERFILE.name} runs commands outside the reviewed list.\n"
        f"  not reviewed: {unexpected}\n  reviewed but gone: {missing}"
    )


def test_the_environment_sets_only_the_reviewed_variables() -> None:
    """``ENV MCP_PROXY_VERSION=latest`` would override a pinned argument."""
    declared: dict[str, str] = {}
    for keyword, rest in instructions():
        if keyword == "ENV":
            for pair in rest.split():
                name, _, value = pair.partition("=")
                declared[name] = value
    assert declared == ALLOWED_ENVIRONMENT, (
        f"{DOCKERFILE.name} sets {declared}; the reviewed environment is {ALLOWED_ENVIRONMENT}"
    )


def test_the_python_it_installs_is_one_the_package_supports() -> None:
    python = str(ARGUMENTS["PYTHON_VERSION"])
    requires = SpecifierSet(_project()["requires-python"])
    assert requires.contains(python), (
        f"the image installs Python {python}, outside the package's requires-python ({requires})"
    )


def test_the_server_version_is_not_ahead_of_the_package() -> None:
    """The image installs from the index, so it can only name a published version."""
    image_version = Version(str(ARGUMENTS["LEGESHER_MCP_VERSION"]))
    package_version = Version(_project()["version"])
    assert image_version <= package_version, (
        f"the image installs legesher-mcp {image_version}, newer than the package's own "
        f"version {package_version}; raise it only after that version is on PyPI"
    )


def test_it_starts_the_stdio_server_as_an_unprivileged_user() -> None:
    """The default is stdio: the HTTP proxy has no authentication to offer."""
    assert command() == [SERVER_EXECUTABLE], (
        f"{DOCKERFILE.name} starts {command()} by default, not the stdio server "
        f"{[SERVER_EXECUTABLE]}"
    )
    users = [rest for keyword, rest in instructions() if keyword == "USER"]
    assert users == ["node"], f"{DOCKERFILE.name} sets USER {users}, not the one user 'node'"


def test_the_listings_page_prints_this_recipe() -> None:
    """One recipe in two places: the page a maintainer copies from, and the file."""
    page = LISTINGS_DOC.read_text(encoding="utf-8")
    printed = "[" + ", ".join(f'"{part}"' for part in LISTING_COMMAND) + "]"
    assert printed in page, f"{LISTINGS_DOC.name} does not print the command {printed}"
    for step in (
        "uv venv /opt/legesher-mcp",
        "uv pip install --python /opt/legesher-mcp/bin/python",
    ):
        assert any(ran.startswith(step) for ran in run_commands()), (
            f"{DOCKERFILE.name} no longer runs {step!r}"
        )
        assert step in page, f"{LISTINGS_DOC.name} does not print the build step {step!r}"
    minor = ".".join(str(ARGUMENTS["PYTHON_VERSION"]).split(".")[:2])
    assert f"| Python version | {minor} |" in page, (
        f"{LISTINGS_DOC.name} does not give the Python version as {minor}, the one the "
        f"image installs"
    )
