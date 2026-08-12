"""Legesher MCP server — the engine's translation capability over MCP.

This package exposes the Legesher translation engine as a Model Context
Protocol (MCP) stdio server: five coarse, task-shaped tools
(``translate_to_native``, ``translate_to_source``, ``explain_in_language``,
``lookup_keyword_mapping``, ``map_existing_codebase``), read-only
``legesher://`` resources for the language catalog and per-language term
dictionaries, and a small set of prompt templates.

The server runs entirely against the locally installed engine
(``legesher-core`` + ``legesher-i18n`` + language packs): no network calls,
no account, no telemetry. Free forever, Apache-2.0.

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
