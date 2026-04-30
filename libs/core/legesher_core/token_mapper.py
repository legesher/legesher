"""Token mapper abstraction for language translation maps.

This module provides the TokenMapper class which abstracts language map lookups,
preparing for future integration with the version-aware language pack system (CORE-345).
"""


class TokenMapper:
    """Abstract translation map lookup for keywords, builtins, and reserved words.

    This class provides a clean interface for looking up keyword, builtin, and
    reserved word translations, abstracting the underlying map implementation.

    Attributes:
        keyword_map: Dictionary mapping English keywords to target language
        builtin_map: Dictionary mapping English builtins to target language
        reserved_word_map: Dictionary mapping Python convention names like
            ``self`` and ``cls`` (CORE-710) to target-language equivalents.
            Optional; defaults to empty.

    Example:
        >>> spanish_keywords = {"def": "definir", "return": "retornar"}
        >>> spanish_builtins = {"print": "imprimir", "len": "longitud"}
        >>> spanish_reserved = {"self": "propio", "cls": "clase"}
        >>> mapper = TokenMapper(spanish_keywords, spanish_builtins, spanish_reserved)
        >>> mapper.get_keyword("def")
        'definir'
        >>> mapper.get_reserved_word("self")
        'propio'
        >>> mapper.is_builtin("print")
        True
    """

    def __init__(
        self,
        keyword_map: dict[str, str],
        builtin_map: dict[str, str],
        reserved_word_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize TokenMapper with translation maps.

        Args:
            keyword_map: Mapping of English keywords to target language
            builtin_map: Mapping of English builtins to target language
            reserved_word_map: Optional mapping of Python conventions like
                ``self`` and ``cls`` to target language. Defaults to empty
                so existing callers don't need to change. Empty is allowed
                (unlike keyword_map / builtin_map) because most existing
                packs don't yet have a reserved_words section.

        Raises:
            ValueError: If keyword_map or builtin_map is empty or None.
                reserved_word_map is allowed to be empty.

        Example:
            >>> mapper = TokenMapper(
            ...     keyword_map={"def": "definir"},
            ...     builtin_map={"print": "imprimir"},
            ...     reserved_word_map={"self": "propio"},
            ... )
        """
        if not keyword_map:
            raise ValueError("keyword_map cannot be empty or None")
        if not builtin_map:
            raise ValueError("builtin_map cannot be empty or None")

        self.keyword_map = keyword_map
        self.builtin_map = builtin_map
        self.reserved_word_map = reserved_word_map or {}

    def get_keyword(self, keyword: str) -> str | None:
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

    def get_builtin(self, builtin: str) -> str | None:
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

    def get_reserved_word(self, reserved_word: str) -> str | None:
        """Get translated reserved word, or None if not found (CORE-710).

        Reserved words are Python conventions like ``self`` and ``cls`` that
        Legesher translates deterministically through the language pack
        rather than via LLM identifier translation. The translator's
        substitution path consults this lookup AFTER ``get_keyword`` and
        ``get_builtin`` so true Python keywords always win on conflict.

        Args:
            reserved_word: English reserved word to translate (e.g., 'self', 'cls')

        Returns:
            Translated reserved word if found, None otherwise

        Example:
            >>> mapper.get_reserved_word("self")
            'propio'
            >>> mapper.get_reserved_word("unknown")
            None
        """
        return self.reserved_word_map.get(reserved_word)

    def is_reserved_word(self, token: str) -> bool:
        """Check if token is a reserved word in the translation map (CORE-710).

        Args:
            token: Token string to check

        Returns:
            True if token is in reserved_word_map, False otherwise

        Example:
            >>> mapper.is_reserved_word("self")
            True
            >>> mapper.is_reserved_word("def")
            False
        """
        return token in self.reserved_word_map

    def reverse(self) -> "TokenMapper":
        """Create a reversed mapper (target → source language).

        Returns a new TokenMapper with reversed translation maps, enabling
        bidirectional translation (e.g., Spanish → English).

        Returns:
            New TokenMapper with reversed maps

        Example:
            >>> en_to_es = TokenMapper({"def": "definir"}, {"print": "imprimir"})
            >>> es_to_en = en_to_es.reverse()
            >>> es_to_en.get_keyword("definir")
            'def'

        Note:
            If multiple English keywords map to the same target keyword,
            only one will be preserved in the reversed map (dict behavior).
        """
        reversed_keywords = {v: k for k, v in self.keyword_map.items()}
        reversed_builtins = {v: k for k, v in self.builtin_map.items()}
        reversed_reserved = {v: k for k, v in self.reserved_word_map.items()}
        return TokenMapper(reversed_keywords, reversed_builtins, reversed_reserved)
