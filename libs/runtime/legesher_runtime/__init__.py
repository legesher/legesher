"""Legesher runtime — localized tracebacks for Python.

``legesher_runtime`` re-renders uncaught-exception tracebacks in the
developer's natural language: structural strings and message templates come
from the Legesher message catalog (``legesher_i18n.messages``), exception
TYPE names from the python language pack for that language. Unmatched
messages pass through untranslated, PEP 657 caret lines are preserved
verbatim, and the hooks never raise — the worst case is CPython's own
traceback.

Example:
    >>> import legesher_runtime
    >>> legesher_runtime.install(lang="es")
    >>> 1 / 0  # ZeroDivisionError renders as errordedivisiónporcero: división por cero
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

from .hooks import install, uninstall
from .renderer import TracebackRenderer

try:
    #: Read from the installed distribution's metadata rather than hand-kept
    #: here, so the wheel's own version (project.version in pyproject.toml,
    #: bumped by hand) is the only one. A literal copy would have to be bumped
    #: by hand alongside project.version, and nothing checked that (CORE-2359).
    __version__ = _distribution_version("legesher-runtime")
except PackageNotFoundError:  # pragma: no cover (running from an uninstalled tree)
    __version__ = "0.0.0.dev0"

__all__ = ["TracebackRenderer", "install", "uninstall", "__version__"]
