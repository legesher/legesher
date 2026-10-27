"""Legesher MCP server — the engine's translation capability over MCP.

This package exposes the Legesher translation engine as a Model Context
Protocol (MCP) server: six coarse, task-shaped tools
(``translate_to_native``, ``translate_to_source``, ``explain_in_language``,
``lookup_keyword_mapping``, ``validate_identifier_translations``,
``map_existing_codebase``), read-only ``legesher://`` resources for the
language catalog and per-language term dictionaries, and a small set of
prompt templates. It serves stdio by default; ``--transport
streamable-http`` serves the same tools over HTTP on one interface,
loopback by default.

Using the MCP server is free forever (Apache-2.0). The local server runs
entirely against the locally installed engine (``legesher-core`` +
``legesher-i18n`` + language packs): it needs no account, and every tool
call is served locally. Optional usage telemetry is planned and will be
off unless enabled; the README's Privacy section says what it would send.
Some capabilities require a Legesher account on the hosted instance.

Run it:

    uvx legesher-mcp
    # or, inside the monorepo workspace:
    uv run legesher-mcp
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

try:
    #: Read from the installed distribution's metadata rather than hand-kept
    #: here, so the `initialize` handshake can never report a version that
    #: drifts from the one in `pyproject.toml` (the wheel's actual version).
    __version__ = _distribution_version("legesher-mcp")
except PackageNotFoundError:  # pragma: no cover — running from an uninstalled tree
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
