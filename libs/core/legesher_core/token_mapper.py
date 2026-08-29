"""Token mapper abstraction for language translation maps.

This module provides the TokenMapper class which abstracts language map lookups,
preparing for future integration with the version-aware language pack system (CORE-345).
"""

import logging
import unicodedata

logger = logging.getLogger(__name__)


class TokenMapper:
    """Abstract translation map lookup for keywords, builtins, and implicit params.

    This class provides a clean interface for looking up keyword, builtin, and
    reserved word translations, abstracting the underlying map implementation.

    Attributes:
        keyword_map: Dictionary mapping English keywords to target language
        builtin_map: Dictionary mapping English builtins to target language
        implicit_param_map: Dictionary mapping Python convention names like
            ``self`` and ``cls`` (CORE-710) to target-language equivalents.
            Optional; defaults to empty.

    Example:
        >>> spanish_keywords = {"def": "definir", "return": "retornar"}
        >>> spanish_builtins = {"print": "imprimir", "len": "longitud"}
        >>> spanish_reserved = {"self": "propio", "cls": "clase"}
        >>> mapper = TokenMapper(spanish_keywords, spanish_builtins, spanish_reserved)
        >>> mapper.get_keyword("def")
        'definir'
        >>> mapper.get_implicit_param("self")
        'propio'
        >>> mapper.is_builtin("print")
        True
    """

    def __init__(
        self,
        keyword_map: dict[str, str],
        builtin_map: dict[str, str],
        implicit_param_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize TokenMapper with translation maps.

        Args:
            keyword_map: Mapping of English keywords to target language
            builtin_map: Mapping of English builtins to target language
            implicit_param_map: Optional mapping of Python conventions like
                ``self`` and ``cls`` to target language. Defaults to empty
                so existing callers don't need to change. Empty is allowed
                (unlike keyword_map / builtin_map) because most existing
                packs don't yet have a implicit_params section.

        Raises:
            ValueError: If keyword_map or builtin_map is empty or None.
                implicit_param_map is allowed to be empty.

        Example:
            >>> mapper = TokenMapper(
            ...     keyword_map={"def": "definir"},
            ...     builtin_map={"print": "imprimir"},
            ...     implicit_param_map={"self": "propio"},
            ... )
        """
        if not keyword_map:
            raise ValueError("keyword_map cannot be empty or None")
        if not builtin_map:
            raise ValueError("builtin_map cannot be empty or None")

        self.keyword_map = keyword_map
        self.builtin_map = builtin_map
        self.implicit_param_map = implicit_param_map or {}

        # Additive NFKC-normalized indexes. Exact lookups still win; these are
        # consulted only as a fallback so the packs that already match exactly
        # are unaffected. Fixes silent breaks like the Thai SARA-AM (U+0E33)
        # round-trip and the fullwidth 'ｉｆ' -> 'if' spoof.
        self._keyword_nfkc = self._build_nfkc_index(self.keyword_map)
        self._builtin_nfkc = self._build_nfkc_index(self.builtin_map)
        self._reserved_nfkc = self._build_nfkc_index(self.implicit_param_map)

    @staticmethod
    def _build_nfkc_index(mapping: dict[str, str]) -> dict[str, str]:
        """Build an NFKC-normalized view of ``mapping``'s keys.

        If two distinct source keys collapse to the same NFKC form with
        *different* targets, keep the first and log a warning rather than
        silently shadowing.
        """
        index: dict[str, str] = {}
        for key, value in mapping.items():
            norm = unicodedata.normalize("NFKC", key)
            existing = index.get(norm)
            if existing is not None and existing != value:
                logger.warning(
                    "NFKC normalization collision: keys collapse to %r with "
                    "differing targets (%r vs %r); keeping first",
                    norm,
                    existing,
                    value,
                )
                continue
            index[norm] = value
        return index

    def _normalized_get(
        self, token: str, exact: dict[str, str], normalized: dict[str, str]
    ) -> str | None:
        """Try an exact lookup, then fall back to an NFKC-normalized one."""
        hit = exact.get(token)
        if hit is not None:
            return hit
        return normalized.get(unicodedata.normalize("NFKC", token))

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
        return self._normalized_get(keyword, self.keyword_map, self._keyword_nfkc)

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
        return self._normalized_get(builtin, self.builtin_map, self._builtin_nfkc)

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

    def get_implicit_param(self, implicit_param: str) -> str | None:
        """Get translated reserved word, or None if not found (CORE-710).

        Reserved words are Python conventions like ``self`` and ``cls`` that
        Legesher translates deterministically through the language pack
        rather than via LLM identifier translation. The translator's
        substitution path consults this lookup AFTER ``get_keyword`` and
        ``get_builtin`` so true Python keywords always win on conflict.

        Args:
            implicit_param: English reserved word to translate (e.g., 'self', 'cls')

        Returns:
            Translated reserved word if found, None otherwise

        Example:
            >>> mapper.get_implicit_param("self")
            'propio'
            >>> mapper.get_implicit_param("unknown")
            None
        """
        return self._normalized_get(
            implicit_param, self.implicit_param_map, self._reserved_nfkc
        )

    def is_implicit_param(self, token: str) -> bool:
        """Check if token is a reserved word in the translation map (CORE-710).

        Args:
            token: Token string to check

        Returns:
            True if token is in implicit_param_map, False otherwise

        Example:
            >>> mapper.is_implicit_param("self")
            True
            >>> mapper.is_implicit_param("def")
            False
        """
        return token in self.implicit_param_map

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

        Raises:
            ValueError: If two source keys map to the same target (a lossy
                collision). Rather than silently dropping an entry — which is
                how a round-trip can corrupt code — the inversion fails with a
                clear diagnostic naming the colliding keys.
        """
        reversed_keywords = self._invert_checked(self.keyword_map, "keyword")
        reversed_builtins = self._invert_checked(self.builtin_map, "builtin")
        reversed_reserved = self._invert_checked(
            self.implicit_param_map, "implicit_param"
        )
        return TokenMapper(reversed_keywords, reversed_builtins, reversed_reserved)

    @staticmethod
    def _invert_checked(mapping: dict[str, str], label: str) -> dict[str, str]:
        """Invert ``mapping`` (target -> source), failing on lossy collisions.

        The naive ``{v: k for k, v in m.items()}`` silently drops entries when
        two source keys share a target — exactly how a round-trip can corrupt
        code. Detect duplicate targets and raise a clear diagnostic instead.
        """
        inverted: dict[str, str] = {}
        collisions: dict[str, list[str]] = {}
        for source, target in mapping.items():
            if target in inverted:
                collisions.setdefault(target, [inverted[target]]).append(source)
            else:
                inverted[target] = source
        if collisions:
            detail = "; ".join(
                f"{target!r} <- {sorted(sources)}"
                for target, sources in sorted(collisions.items())
            )
            raise ValueError(
                f"Cannot reverse {label} map: multiple source keys map to the "
                f"same target, which would silently drop entries: {detail}"
            )
        return inverted
