"""Type definitions for Legesher Core translation engine.

This module provides type hints and Protocols for type safety
and better IDE autocomplete support throughout the legesher-core package.

Note: We use standard dict[str, str] for translation maps instead of TypedDict
because Python keywords cannot be used as TypedDict field names.
"""

from typing import Protocol


# Type aliases for translation maps
# We use dict[str, str] instead of TypedDict because Python keywords
# (like 'def', 'class', 'if', etc.) cannot be TypedDict field names.
# This provides type safety while allowing any string keys.
KeywordMap = dict[str, str]
BuiltinMap = dict[str, str]


class Translator(Protocol):
    """Protocol defining the translator interface.

    This protocol allows type checking for any class that implements
    the translator interface, supporting dependency injection and testing.

    Example:
        >>> def process_code(translator: Translator, code: str) -> str:
        ...     return translator.translate_code(code, "en", "es")
    """

    def translate_code(
        self, source_code: str, source_lang: str = "en", target_lang: str = "es"
    ) -> str:
        """Translate Python source code from one language to another.

        Args:
            source_code: Python source code to translate
            source_lang: Source language code (default: "en")
            target_lang: Target language code (default: "es")

        Returns:
            Translated Python source code
        """
        ...
