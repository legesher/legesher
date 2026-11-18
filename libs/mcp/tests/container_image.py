"""What ``libs/mcp/Dockerfile`` says, read without building it.

``tests/test_container_image.py`` holds the file to its pins in the default
run. ``tests/test_container_session.py`` builds the image and drives a session
against it (``make test-mcp-docker``) and reads the same facts from here, so
the two cannot disagree about what the file declares.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]
DOCKERFILE = PACKAGE_DIR / "Dockerfile"

#: The stdio server inside the image, and the image's default command.
SERVER_EXECUTABLE = "/opt/legesher-mcp/bin/legesher-mcp"

#: The command a directory's build settings run: mcp-proxy serving the stdio
#: server over HTTP. ``docs/registry-listings.md`` prints the same array.
LISTING_COMMAND = ["mcp-proxy", "--", SERVER_EXECUTABLE]

#: The port mcp-proxy listens on when it is given none.
PROXY_PORT = 8080

_CONTINUATION = re.compile(r"\\\n\s*")
#: A parser directive: a comment Docker reads as configuration. ``syntax=``
#: names an image that runs the whole build, so it is a download too.
_DIRECTIVE = re.compile(r"^\s*#\s*(?P<name>syntax|escape|check)\s*=", re.I)
_ARG = re.compile(r"^ARG (?P<name>[A-Za-z0-9_]+)(?:=(?P<default>\S*))?$")
_FROM = re.compile(r"^FROM (?:--platform=\S+ )?(?P<image>\S+)(?: AS (?P<stage>\S+))?$", re.I)
_ANY_FROM = re.compile(r"\bfrom=(?P<image>[^\s,]+)", re.I)


def instructions(text: str | None = None) -> list[tuple[str, str]]:
    """Each instruction as ``(KEYWORD, rest)``, comments and blank lines dropped.

    The keyword is upper-cased, because Docker reads ``from`` as ``FROM``, and
    a check that only knew the upper-case spelling would miss the other.
    """
    source = DOCKERFILE.read_text(encoding="utf-8") if text is None else text
    lines = (
        line for line in source.splitlines() if line.strip() and not line.lstrip().startswith("#")
    )
    joined = _CONTINUATION.sub(" ", "\n".join(lines))
    parsed: list[tuple[str, str]] = []
    for line in joined.splitlines():
        keyword, _, rest = line.strip().partition(" ")
        parsed.append((keyword.upper(), " ".join(rest.split())))
    return parsed


def parser_directives(text: str | None = None) -> list[str]:
    """Every comment line Docker could read as a parser directive.

    Docker reads directives only at the top of the file; every such line is
    reported wherever it sits, so moving one up cannot slip past a check.
    """
    source = DOCKERFILE.read_text(encoding="utf-8") if text is None else text
    return [line.strip() for line in source.splitlines() if _DIRECTIVE.match(line)]


def image_references(text: str | None = None) -> list[str]:
    """Every image the build pulls.

    Each ``FROM``, and each ``from=`` on any instruction: ``COPY --from=`` and
    ``RUN --mount=...,from=`` both pull one. A ``from=`` that names an earlier
    stage or a stage number pulls nothing and is left out.
    """
    references: list[str] = []
    stages: set[str] = set()
    for keyword, rest in instructions(text):
        if keyword == "FROM":
            base = _FROM.match(f"FROM {rest}")
            assert base, f"cannot read the image in 'FROM {rest}'"
            references.append(base["image"])
            if base["stage"]:
                stages.add(base["stage"].lower())
            continue
        for found in _ANY_FROM.finditer(rest):
            image = found["image"]
            if image.lower() not in stages and not image.isdigit():
                references.append(image)
    return references


def build_arguments(text: str | None = None) -> dict[str, str | None]:
    """Each ``ARG`` and its default, None when the file gives it none."""
    arguments: dict[str, str | None] = {}
    for keyword, rest in instructions(text):
        if keyword == "ARG":
            declared = _ARG.match(f"ARG {rest}")
            assert declared, f"cannot read 'ARG {rest}'"
            arguments[declared["name"]] = declared["default"]
    return arguments


def run_commands(text: str | None = None) -> list[str]:
    """Every shell command the build runs, in order, one per ``&&`` step."""
    commands: list[str] = []
    for keyword, rest in instructions(text):
        if keyword == "RUN":
            commands.extend(step.strip() for step in rest.split("&&"))
    return commands


def command(text: str | None = None) -> list[str]:
    """The image's ``CMD``, which must be written in the JSON form."""
    commands = [rest for keyword, rest in instructions(text) if keyword == "CMD"]
    assert len(commands) == 1, f"expected one CMD in {DOCKERFILE.name}, got {commands}"
    parsed: list[str] = json.loads(commands[0])
    return parsed
