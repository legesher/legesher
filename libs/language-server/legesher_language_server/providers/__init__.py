"""LSP feature providers for Legesher Language Server.

This package contains provider modules for various LSP features:
- hover: Hover tooltips with translated docstrings (CORE-357)
- completion: IntelliSense with localized keywords (CORE-358)
- diagnostic: Translated error messages (CORE-359)
- semantic_tokens: Syntax highlighting for translated keywords (CORE-450)

All providers are currently stubs and will be implemented in subsequent issues.
"""

from .completion import provide_completion
from .diagnostic import provide_diagnostics
from .hover import provide_hover
from .semantic_tokens import provide_semantic_tokens

__all__ = [
    "provide_hover",
    "provide_completion",
    "provide_diagnostics",
    "provide_semantic_tokens",
]
