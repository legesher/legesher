"""Diagnostic provider for translated error messages.

This module translates Python error messages and warnings:
- Syntax errors
- Type errors
- Runtime errors
- Linting warnings

STUB: Full implementation in CORE-359.
TODO: Implement diagnostic translator.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import Diagnostic


async def provide_diagnostics(server: "LegesherLanguageServer", uri: str) -> list[Diagnostic]:
    """Provide diagnostics for document.

    Args:
        server: Language server instance
        uri: Document URI

    Returns:
        List of diagnostics (empty until CORE-359)

    Note:
        STUB - Returns empty list until CORE-359 implementation.
    """
    # TODO (CORE-359): Implement diagnostic translator
    # 1. Get document at URI
    # 2. Get diagnostics from Pylance
    # 3. Translate error messages to target language
    # 4. Return translated Diagnostic list
    return []
