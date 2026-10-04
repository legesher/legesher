"""Legesher Language Server.

Language Server Protocol (LSP) implementation that gives IDEs multilingual
Python awareness — hover tooltips, completions, diagnostics, and syntax
highlighting that follow the user's configured language pack.

Launched by IDEs over stdio via the ``legesher-lsp`` console entry point;
not typically imported directly. Built on pygls 2.0 and supports Python
3.10 and newer.

Capabilities:
    Hover: Translated docstrings, keyword documentation, and cultural
        comments displayed on hover.
    Completion: Localized keyword and builtin completion with fuzzy
        matching against the user's target language pack.
    Diagnostics: Translated error messages with 41 templates across 17
        error types, mapped from Python's syntax/runtime errors.
    Semantic tokens: Syntax highlighting for translated keywords so
        Spanish ``definir`` renders with the same color as English ``def``.

Configuration (via environment variables):
    LEGESHER_SOURCE_LANG: Source language code (default: ``"en"``).
    LEGESHER_TARGET_LANG: Target language code (default: ``"en"``).
    LEGESHER_PYTHON_VERSION: Python version; auto-detected if unset.
    LEGESHER_CACHE_SIZE: LRU cache size for pack lookups (default: 1000).
    LEGESHER_CACHE_TTL: Cache TTL in seconds (default: 3600).
    LEGESHER_LOG_LEVEL: Log level (default: ``"INFO"``).

Example:
    Start the server directly from a shell::

        $ LEGESHER_TARGET_LANG=es legesher-lsp

    Then point your IDE at the ``legesher-lsp`` binary as an LSP backend
    for Python.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

try:
    #: Read from the installed distribution's metadata rather than hand-kept
    #: here, so `--version`, the `initialize` handshake and the release train
    #: all report the version in `pyproject.toml`, which is the wheel's own.
    #: Three literals used to disagree (0.1.0, 0.1.2 and 0.1.3) (CORE-2203).
    __version__ = _distribution_version("legesher-language-server")
except PackageNotFoundError:  # pragma: no cover (running from an uninstalled tree)
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
