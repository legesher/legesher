"""Legesher runtime — localized tracebacks for Python (CORE-1679).

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

from .hooks import install, uninstall
from .renderer import TracebackRenderer

__version__ = "0.1.0"

__all__ = ["TracebackRenderer", "install", "uninstall", "__version__"]
