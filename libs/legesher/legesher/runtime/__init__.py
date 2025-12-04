"""Legesher runtime package for native language Python execution.

This package provides the revolutionary import hook system that enables
seamless execution of Python code written in any natural language.

Components:
- Import hooks for native language modules (import_hook.py)
- Source mapping for accurate error reporting (source_mapper.py)
- Error translation for native language exceptions (error_handler.py)

Example:
    >>> from legesher.runtime import install_import_hook, install_error_handler
    >>> install_import_hook("es")  # Spanish
    >>> install_error_handler("es")
    >>> import mi_modulo  # Works seamlessly!
"""

from legesher.runtime.error_handler import LegesherErrorHandler, install_error_handler
from legesher.runtime.import_hook import (
    LegesherLoader,
    LegesherMetaPathFinder,
    clear_cache,
    get_cache_stats,
    install_import_hook,
    uninstall_import_hook,
)
from legesher.runtime.source_mapper import (
    LegesherSourceMapper,
    SourceMapping,
    get_source_mapper,
)

__all__ = [
    # Import hook
    "install_import_hook",
    "uninstall_import_hook",
    "LegesherMetaPathFinder",
    "LegesherLoader",
    # Cache management
    "get_cache_stats",
    "clear_cache",
    # Source mapper
    "get_source_mapper",
    "LegesherSourceMapper",
    "SourceMapping",
    # Error handler
    "install_error_handler",
    "LegesherErrorHandler",
]
