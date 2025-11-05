"""Hover provider for translated docstrings and tooltips.

This module provides hover information showing:
- Translated function/class docstrings
- Type hints in target language
- Quick documentation for builtins

STUB: Full implementation in CORE-357.
TODO: Implement hover provider with translation integration.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import Hover, Position


async def provide_hover(
    server: "LegesherLanguageServer", uri: str, position: Position
) -> Hover | None:
    """Provide hover information at cursor position.

    Args:
        server: Language server instance
        uri: Document URI
        position: Cursor position

    Returns:
        Hover information or None

    Note:
        STUB - Returns None until CORE-357 implementation.
    """
    # TODO (CORE-357): Implement hover provider
    # 1. Get document at URI
    # 2. Extract symbol at position
    # 3. Get docstring/type hint from Pylance
    # 4. Translate to target language
    # 5. Return Hover with translated content
    return None
