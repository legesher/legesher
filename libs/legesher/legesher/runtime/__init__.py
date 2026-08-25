"""Import and traceback support for running localized Python.

This package is what ``legesher run`` installs. The import hook translates a
localized module to canonical Python at import time, and the source mapper
keeps a record of where each translated line came from so tracebacks can point
back at the file the developer actually wrote.

Components:
- Import hooks for native language modules (``import_hook``)
- Source mapping for accurate error reporting (``source_mapper``)
- Traceback frames rendered against the localized source (``error_handler``)

Exception *messages* are a separate concern, handled by the ``legesher_runtime``
package, which renders type names and message text from the language pack.

Example:
    >>> from legesher.runtime import install_import_hook, install_error_handler
    >>> install_import_hook("es")  # Spanish
    >>> install_error_handler("es")
    >>> import mi_modulo
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
