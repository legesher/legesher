"""Token mapper: the lookup contract for pack words.

``TokenMapper`` answers one question for both translator backends: is this
name a pack word, and if so, what does it translate to. How it compares the
name with the table is the engine's half of the text-identity contract
(store NFC, compare NFKC), and this module is where that half is stated.

**The contract.** Every lookup (keyword, builtin or exception, implicit
parameter) tries the name it is given against its own table and, only when
that misses, tries the name's NFKC form against an index of that table's
keys folded the same way. That is "normalize both sides before comparing",
done at the lookup and not at the lexer. (The token backend hands the mapper
the NFC form of each token; the tree-sitter backend hands it the token as
written. Both reach the same entry for a table whose keys are NFC-stable,
which the pack validator requires of every value.)

- The relation is Python's own. Python folds identifiers with NFKC when it
  parses them (PEP 3131), so two NFKC-equal spellings are one name to the
  interpreter. Reading them as one pack word keeps the engine from splitting
  a name Python would not split.
- The source text is never rewritten to a normal form. A name that is not a
  pack word keeps its bytes, and a name that is one is replaced by the
  table's target. Normalizing at the lexer would change text the author
  wrote, which the round trip has to return byte for byte.
- Within a table an exact match wins, so a pack whose words already match
  byte for byte behaves as it would with no fallback. Across tables the
  translators' order holds: keyword, then builtin, then implicit parameter.
- Case is not folded. Case distinguishes Python names (``Print`` is not
  ``print``), so the lookup must not merge them.
  ``text_identity.compare_key`` adds a case fold for a different question:
  whether two coined names are too alike to coexist.

**What the fallback reaches.** Decomposed text (NFD, as macOS produces),
compatibility forms (fullwidth letters, Arabic and Hebrew presentation
forms), ligatures, and Thai SARA AM (U+0E33), which NFKC decomposes.
``tests/unit/test_denormalized_spellings.py`` holds every word of every
shipped pack to this in both backends.

**Collisions.** Two keys of one table that fold to the same NFKC form with
different targets cannot both be reached through the fallback; the index
keeps the first and logs a warning. The pack validator refuses a value that
is not already stable under NFC and NFKC
(``legesher_i18n.schema_validator.SchemaValidator.check_normalization``,
finding code ``nfkc-instability``), so that rule is the authoring-time
check, and for a stable value NFKC-equal means byte-equal. Its one allowance
is SARA AM: a Thai value may carry U+0E33, so two values that differ only in
how SARA AM is written would pass the validator and collide here. The
warning is the load-time backstop for that case and for a table built by
hand, and the same test module fails any shipped pack that triggers it.

The ``is_*`` predicates are exact-match membership tests on the table as
given. They do not apply the fallback; use the ``get_*`` lookups to decide
how a name in source text translates.
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

        # Additive NFKC-normalized indexes (the contract in the module
        # docstring). Exact lookups still win; these are consulted only as a
        # fallback so the packs that already match exactly are unaffected.
        # Fixes silent breaks like the Thai SARA-AM (U+0E33) round-trip and
        # the fullwidth 'ｉｆ' -> 'if' spoof.
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
