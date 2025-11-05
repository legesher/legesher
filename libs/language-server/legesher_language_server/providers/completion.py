"""Completion provider for localized IntelliSense.

This module provides completion items including:
- Keywords in target language
- Builtins in target language
- Context-aware suggestions from Pylance

STUB: Full implementation in CORE-358.
TODO: Implement completion provider with keyword translation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import CompletionItem, Position


async def provide_completion(
    server: "LegesherLanguageServer", uri: str, position: Position
) -> list[CompletionItem]:
    """Provide completion items at cursor position.

    Args:
        server: Language server instance
        uri: Document URI
        position: Cursor position

    Returns:
        List of completion items (empty until CORE-358)

    Note:
        STUB - Returns empty list until CORE-358 implementation.
    """
    # TODO (CORE-358): Implement completion provider
    # 1. Get document at URI
    # 2. Get context at position
    # 3. Determine completion type (keyword, builtin, identifier)
    # 4. Get suggestions from Pylance
    # 5. Translate keywords/builtins to target language
    # 6. Return CompletionItem list
    return []
