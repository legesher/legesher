"""Token mapper abstraction for language translation maps.

This module provides the TokenMapper class which abstracts language map lookups,
preparing for future integration with the version-aware language pack system (CORE-345).
"""

from typing import Optional


class TokenMapper:
    """Abstract translation map lookup for keywords and builtins.

    This class provides a clean interface for looking up keyword and builtin
    translations, abstracting the underlying map implementation. In the future,
    this will integrate with the version-aware language pack system.

    Attributes:
        keyword_map: Dictionary mapping English keywords to target language
        builtin_map: Dictionary mapping English builtins to target language

    Example:
        >>> spanish_keywords = {"def": "definir", "return": "retornar"}
        >>> spanish_builtins = {"print": "imprimir", "len": "longitud"}
        >>> mapper = TokenMapper(spanish_keywords, spanish_builtins)
        >>> mapper.get_keyword("def")
        'definir'
        >>> mapper.is_builtin("print")
        True
    """

    def __init__(
        self, keyword_map: dict[str, str], builtin_map: dict[str, str]
    ) -> None:
        """Initialize TokenMapper with translation maps.

        Args:
            keyword_map: Mapping of English keywords to target language
            builtin_map: Mapping of English builtins to target language

        Raises:
            ValueError: If either map is empty or None

        Example:
            >>> mapper = TokenMapper(
            ...     keyword_map={"def": "definir"},
            ...     builtin_map={"print": "imprimir"}
            ... )
        """
        if not keyword_map:
            raise ValueError("keyword_map cannot be empty or None")
        if not builtin_map:
            raise ValueError("builtin_map cannot be empty or None")

        self.keyword_map = keyword_map
        self.builtin_map = builtin_map

    def get_keyword(self, keyword: str) -> Optional[str]:
        """Get translated keyword, or None if not found.

        Args:
            keyword: English keyword to translate (e.g., "def", "return")

        Returns:
            Translated keyword if found, None otherwise

        Example:
            >>> mapper.get_keyword("def")
            'definir'
            >>> mapper.get_keyword("unknown_keyword")
            None
        """
        return self.keyword_map.get(keyword)

    def get_builtin(self, builtin: str) -> Optional[str]:
        """Get translated builtin function name, or None if not found.

        Args:
            builtin: English builtin name to translate (e.g., "print", "len")

        Returns:
            Translated builtin name if found, None otherwise

        Example:
            >>> mapper.get_builtin("print")
            'imprimir'
            >>> mapper.get_builtin("my_custom_function")
            None
        """
        return self.builtin_map.get(builtin)

    def is_keyword(self, token: str) -> bool:
        """Check if token is a keyword in the translation map.

        Args:
            token: Token string to check

        Returns:
            True if token is in keyword_map, False otherwise

        Example:
            >>> mapper.is_keyword("def")
            True
            >>> mapper.is_keyword("my_function")
            False
        """
        return token in self.keyword_map

    def is_builtin(self, token: str) -> bool:
        """Check if token is a builtin in the translation map.

        Args:
            token: Token string to check

        Returns:
            True if token is in builtin_map, False otherwise

        Example:
            >>> mapper.is_builtin("print")
            True
            >>> mapper.is_builtin("my_function")
            False
        """
        return token in self.builtin_map
