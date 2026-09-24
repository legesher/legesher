"""Tree-sitter-based code transformer for multilingual Python translation.

This module implements a tree-sitter-based translation engine as a performance
improvement over the token-based approach. It provides the same API as TokenTranslator
while leveraging tree-sitter for better performance and error handling.
"""

import logging
import sys
import unicodedata
from pathlib import Path

from .parser import PythonParser, TreeSitterError
from ..exceptions import InvalidCodeError
from ..token_mapper import TokenMapper
from ..types import CulturalCommentMetadata
from ..utils import (
    validate_utf8_encoding,
    normalize_newlines,
    strip_bom,
    check_coding_declaration,
)

# Configure logger
logger = logging.getLogger(__name__)


class TreeSitterTranslator:
    """Translate Python code between natural languages using tree-sitter.

    This class provides an alternative translation engine for Legesher using
    tree-sitter for parsing instead of the tokenize module. It offers:
    - Better performance (≥2x faster than token-based)
    - More robust error handling for incomplete code
    - AST-aware translation (understands code structure)
    - Incremental parsing support (for future IDE integration)

    The API is designed to be 100% compatible with TokenTranslator, enabling
    drop-in replacement and A/B testing.

    Attributes:
        mapper: TokenMapper instance for translation lookups
        python_version: Target Python version (e.g., "3.13")
        parser: PythonParser instance for tree-sitter operations

    Example:
        >>> spanish_keywords = {"def": "definir", "return": "retornar"}
        >>> spanish_builtins = {"print": "imprimir", "len": "longitud"}
        >>> translator = TreeSitterTranslator(
        ...     keyword_map=spanish_keywords,
        ...     builtin_map=spanish_builtins,
        ...     python_version="3.13"
        ... )
        >>> code = "def greet():\\n    print('Hello')"
        >>> spanish_code = translator.translate_code(code, "en", "es")
        >>> print(spanish_code)
        definir greet():
            imprimir('Hello')
    """

    def __init__(
        self,
        keyword_map: dict[str, str],
        builtin_map: dict[str, str],
        python_version: str = "3.13",
        implicit_param_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize translator with language maps and Python version.

        Args:
            keyword_map: Dictionary mapping English keywords to target language
            builtin_map: Dictionary mapping English builtins to target language
            python_version: Python version string (default: "3.13")
            implicit_param_map: Optional mapping of Python conventions like
                ``self`` and ``cls`` to target language (CORE-710). Defaults
                to empty so existing callers don't need to change.

        Raises:
            ValueError: If keyword_map or builtin_map is empty or None
            TreeSitterError: If parser initialization fails

        Example:
            >>> translator = TreeSitterTranslator(
            ...     keyword_map={"def": "definir", "return": "retornar"},
            ...     builtin_map={"print": "imprimir"},
            ...     implicit_param_map={"self": "propio"},
            ...     python_version="3.13"
            ... )
        """
        self.mapper = TokenMapper(keyword_map, builtin_map, implicit_param_map)
        self.python_version = python_version

        # Texts that could start a `<keyword>*` compound entry. Checking these
        # before touching node.next_sibling keeps the compound lookup off the
        # hot path: reading a sibling allocates a node through the FFI
        # boundary, and every identifier in the file would otherwise pay it.
        # The NFKC set mirrors TokenMapper's exact-then-normalized lookup, so
        # gating here cannot reject a spelling the mapper would have resolved.
        self._star_prefixes = {
            key[:-1] for key in self.mapper.keyword_map if key.endswith("*")
        }
        self._star_prefixes_nfkc = {
            unicodedata.normalize("NFKC", prefix) for prefix in self._star_prefixes
        }

        # Initialize tree-sitter parser
        try:
            self.parser = PythonParser()
            logger.debug("TreeSitterTranslator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter parser: {e}")
            raise TreeSitterError(f"Failed to initialize parser: {e}") from e

    def __repr__(self) -> str:
        """Return a developer-friendly string representation for debugging.

        Example:
            >>> translator = TreeSitterTranslator({"def": "definir"}, {"print": "imprimir"})
            >>> repr(translator)
            "TreeSitterTranslator(keywords=1, builtins=1, implicit_params=0, python_version='3.13')"
        """
        return (
            f"TreeSitterTranslator("
            f"keywords={len(self.mapper.keyword_map)}, "
            f"builtins={len(self.mapper.builtin_map)}, "
            f"implicit_params={len(self.mapper.implicit_param_map)}, "
            f"python_version={self.python_version!r})"
        )

    def translate_code(
        self,
        source_code: str,
        source_lang: str = "en",
        target_lang: str = "es",
        return_metadata: bool = False,
    ) -> str | tuple[str, CulturalCommentMetadata]:
        """Translate Python source code from one language to another.

        This method translates Python keywords and builtin function names while
        preserving all formatting, whitespace, comments, and code structure.

        Translation process:
        1. Normalize line endings (\\r\\n → \\n)
        2. Parse source code using tree-sitter
        3. Walk the parse tree for keyword and identifier nodes
        4. Identify builtin function calls in the AST
        5. Replace keywords/builtins with translated versions
        6. Reconstruct code preserving exact formatting

        Args:
            source_code: Python source code to translate
            source_lang: Source language code (currently unused, for future)
            target_lang: Target language code (currently unused, for future)
            return_metadata: If True, return tuple of (code, cultural_metadata)

        Returns:
            If return_metadata=False: Translated source code (default)
            If return_metadata=True: Tuple of (translated code, cultural metadata)

        Raises:
            InvalidCodeError: If code has severe syntax errors

        Example:
            >>> code = "def calculate_tax(income, rate):\\n    return income * rate"
            >>> translated = translator.translate_code(code, "en", "es")
            >>> print(translated)
            definir calculate_tax(income, rate):
                retornar income * rate

        Note:
            - Comments and docstrings are NOT translated (preserved as-is)
            - Variable and function names are NOT translated (out of scope)
            - Incomplete code is handled gracefully (returns original)
            - Syntax errors return original code unchanged
        """
        # Handle empty input
        if not source_code or not source_code.strip():
            if return_metadata:
                return source_code, CulturalCommentMetadata()
            return source_code

        # Strip a leading BOM and warn on a non-UTF-8 coding declaration before
        # processing — Legesher mandates UTF-8.
        source_code = strip_bom(source_code)
        bad_coding = check_coding_declaration(source_code)
        if bad_coding is not None:
            logger.warning(
                "Non-UTF-8 PEP 263 coding declaration %r ignored; Legesher "
                "mandates UTF-8 source",
                bad_coding,
            )

        # Normalize line endings for consistent processing
        source_code = normalize_newlines(source_code)

        try:
            # Parse code with tree-sitter
            tree = self.parser.parse(source_code)

            # Build byte→char mapping for character-level replacement
            byte_to_char = self._build_byte_to_char_map(source_code)

            # Collect replacements as (start_byte, end_byte, new_text) tuples
            replacements = []

            # Walk the tree to find keywords and builtins
            self._find_translations(tree.root_node, replacements)

            # Apply replacements at character level to avoid UTF-8 round-trip issues
            result = self._apply_replacements(source_code, byte_to_char, replacements)

            # Handle metadata if requested
            if return_metadata:
                # Extract cultural comments using existing parser
                # For now, return empty metadata (can be enhanced later)
                cultural_metadata = CulturalCommentMetadata()
                logger.debug(
                    "Cultural comment extraction not yet implemented for tree-sitter"
                )
                return result, cultural_metadata

            return result

        except TreeSitterError as e:
            # Tree-sitter specific errors - return original code
            logger.info(f"Tree-sitter error handled gracefully: {e}")
            if return_metadata:
                return source_code, CulturalCommentMetadata()
            return source_code

        except UnicodeError as e:
            # Safety net: encode("utf-8") can fail on surrogate characters
            logger.warning(
                f"Unicode error during tree-sitter translation, "
                f"returning original code: {e}"
            )
            if return_metadata:
                return source_code, CulturalCommentMetadata()
            return source_code

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Translation failed unexpectedly: {e}")
            raise InvalidCodeError(f"Failed to translate code: {e}") from e

    def _find_translations(self, node, replacements: list) -> None:
        """Recursively find and collect keyword and builtin translations.

        Args:
            node: Tree-sitter node to search
            replacements: List to append (start, end, replacement) tuples
        """
        # Python keywords that appear as node text (not types)
        # These are the nodes where we check the text directly
        if node.type in ["identifier", "true", "false", "none"]:
            try:
                text = node.text.decode("utf-8")
            except UnicodeDecodeError:
                logger.debug(f"Skipping node with non-UTF-8 content: {node.type}")
                return

            # Try to translate as keyword first. A `*` sibling means this may
            # be a native rendering of `except*` (PEP 654), which packs key as
            # one compound entry — that lookup wins over the bare keyword.
            translated = self._star_compound_keyword(
                node, text
            ) or self.mapper.get_keyword(text)
            if translated and translated != text:
                replacements.append((node.start_byte, node.end_byte, translated))
                logger.debug(f"Keyword match: '{text}' → '{translated}'")
                return  # Don't check builtin if it's a keyword

            # Try to translate as builtin (for identifiers only)
            if node.type == "identifier":
                translated = self.mapper.get_builtin(text)
                if translated and translated != text:
                    replacements.append((node.start_byte, node.end_byte, translated))
                    logger.debug(f"Builtin match: '{text}' → '{translated}'")
                # CORE-710 dispatch: implicit params (self, cls) AFTER builtins.
                # Short-circuit on empty map to avoid the per-identifier dict
                # lookup overhead for packs that don't ship implicit_params.
                # Keywords still win on conflict (handled above with early return).
                elif implicit_param_map := self.mapper.implicit_param_map:
                    translated = implicit_param_map.get(text)
                    if translated and translated != text:
                        replacements.append(
                            (node.start_byte, node.end_byte, translated)
                        )
                        logger.debug(f"Implicit param match: '{text}' → '{translated}'")

        # Special handling for keyword nodes that are part of statements
        # These keywords appear as terminal nodes with specific text
        elif node.type in [
            "def",
            "class",
            "if",
            "elif",
            "else",
            "for",
            "while",
            "return",
            "yield",
            "import",
            "from",
            "as",
            "pass",
            "break",
            "continue",
            "raise",
            "try",
            "except",
            "finally",
            "with",
            "assert",
            "lambda",
            "and",
            "or",
            "not",
            "is",
            "in",
            "async",
            "await",
            "global",
            "nonlocal",
            "del",
            "match",
            "case",
            # PEP 695 (3.12+) soft keyword. Only the ANONYMOUS `type` token —
            # the one introducing a `type_alias_statement` — is the keyword;
            # the grammar also emits *named* `type` nodes wrapping arbitrary
            # type expressions (`list[float]`, the annotation in `x: int`),
            # which must not be rewritten. The `is_named` test on this same
            # condition excludes them; it stays on the condition rather than
            # returning early, so their inner identifiers still translate.
            "type",
        ] and not (node.type == "type" and node.is_named):
            try:
                text = node.text.decode("utf-8")
            except UnicodeDecodeError:
                logger.debug(f"Skipping node with non-UTF-8 content: {node.type}")
                return
            # `except*` (PEP 654, 3.11+) reaches the grammar as an `except`
            # token followed by a `*` token, but packs key it as one compound
            # entry — so the compound lookup wins when a `*` sibling is there.
            translated = self._star_compound_keyword(
                node, text
            ) or self.mapper.get_keyword(text)
            if translated and translated != text:
                replacements.append((node.start_byte, node.end_byte, translated))
                logger.debug(f"Keyword match: '{text}' → '{translated}'")

        # Recursively search children
        for child in node.children:
            self._find_translations(child, replacements)

    def _star_compound_keyword(self, node, text: str) -> str | None:
        """Resolve a ``<keyword>*`` compound entry for ``node`` (PEP 654).

        ``except*`` is one keyword, but the grammar splits it into an
        ``except`` token and a ``*`` token, and a native rendering parses as
        an identifier followed by ``*``. Language packs key the construct as a
        single ``"except*"`` entry, so whenever ``node`` is immediately
        followed by a ``*`` the compound entry is consulted first. The
        trailing ``*`` is stripped from the translation because the ``*`` node
        itself is left untouched — the same contract the token backend
        implements via token lookahead, which is what keeps the two backends
        byte-identical on ``except*`` (CORE-1345).

        Args:
            node: Tree-sitter node being translated
            text: Already-decoded text of ``node``

        Returns:
            The compound translation without its trailing ``*``, or None when
            there is no ``*`` sibling or the pack has no compound entry — in
            which case the caller falls back to the plain keyword lookup.
        """
        if text not in self._star_prefixes:
            # ASCII is NFKC-stable, so only a non-ASCII miss can still match
            # through the mapper's normalized index.
            if text.isascii():
                return None
            if unicodedata.normalize("NFKC", text) not in self._star_prefixes_nfkc:
                return None
        sibling = node.next_sibling
        if sibling is None or sibling.type != "*":
            return None
        compound = self.mapper.get_keyword(f"{text}*")
        if not compound:
            return None
        return compound[:-1] if compound.endswith("*") else compound

    @staticmethod
    def _build_byte_to_char_map(source_code: str) -> dict[int, int]:
        """Build a mapping from UTF-8 byte offsets to character offsets.

        Since tree-sitter works at the byte level but Python strings are
        character-indexed, this mapping allows converting tree-sitter's byte
        positions to string positions for character-level replacement.

        Args:
            source_code: Source code as Python str

        Returns:
            Dict mapping byte offset → character offset
        """
        byte_to_char = {}
        byte_idx = 0
        for char_idx, char in enumerate(source_code):
            byte_to_char[byte_idx] = char_idx
            byte_idx += len(char.encode("utf-8"))
        byte_to_char[byte_idx] = len(source_code)  # End sentinel
        return byte_to_char

    def _apply_replacements(
        self,
        source_code: str,
        byte_to_char: dict[int, int],
        replacements: list,
    ) -> str:
        """Apply text replacements using character-level positions.

        Converts tree-sitter byte positions to character positions via
        byte_to_char mapping, then applies replacements on the Python str
        directly. This avoids UTF-8 encode/decode round-trips that can fail
        on source files containing unusual byte sequences.

        Replacements are applied in reverse order (end → start) to maintain
        position validity throughout the process.

        Args:
            source_code: Original source code as str
            byte_to_char: Mapping from byte offsets to character offsets
            replacements: List of (start_byte, end_byte, new_text) tuples

        Returns:
            Translated source code as string
        """
        # Sort replacements by start position (descending) to apply in reverse
        replacements.sort(reverse=True, key=lambda x: x[0])

        result = source_code
        for start_byte, end_byte, new_text in replacements:
            start_char = byte_to_char[start_byte]
            end_char = byte_to_char[end_byte]
            result = result[:start_char] + new_text + result[end_char:]

        return result

    def translate_file(self, file_path: Path, target_lang: str) -> str:
        """Translate a Python file to target language.

        Reads a Python file from disk, detects encoding, and translates
        the code to the target language.

        Args:
            file_path: Path to Python source file
            target_lang: Target language code (e.g., "es", "ar")

        Returns:
            Translated Python source code

        Raises:
            EncodingError: If file is not UTF-8 encoded
            FileNotFoundError: If file doesn't exist

        Example:
            >>> result = translator.translate_file(
            ...     Path("my_code.py"),
            ...     target_lang="es"
            ... )
        """
        # Verify encoding is UTF-8
        encoding = validate_utf8_encoding(file_path)

        # Read file contents
        with open(file_path, encoding=encoding) as f:
            source_code = f.read()

        # Translate code (source_lang defaults to "en")
        return self.translate_code(
            source_code, source_lang="en", target_lang=target_lang
        )

    def reverse(self) -> "TreeSitterTranslator":
        """Create a reversed translator (target → source language).

        Returns a new TreeSitterTranslator with reversed translation maps, enabling
        bidirectional translation (e.g., Spanish → English).

        Returns:
            New TreeSitterTranslator with reversed maps

        Example:
            >>> en_to_es = TreeSitterTranslator.from_language_pack("es")
            >>> es_to_en = en_to_es.reverse()
            >>> spanish = "definir greet(): retornar 42"
            >>> english = es_to_en.translate_code(spanish)
            >>> "def greet(): return 42" in english
            True

        Note:
            If multiple English keywords map to the same target keyword,
            only one will be preserved in the reversed map (dict behavior).
        """
        reversed_mapper = self.mapper.reverse()
        return TreeSitterTranslator(
            keyword_map=reversed_mapper.keyword_map,
            builtin_map=reversed_mapper.builtin_map,
            implicit_param_map=reversed_mapper.implicit_param_map,
            python_version=self.python_version,
        )

    @classmethod
    def from_language_pack(
        cls,
        language: str,
        python_version: str | None = None,
    ) -> "TreeSitterTranslator":
        """Create translator from language pack with version awareness.

        Loads the appropriate language pack for the specified language and
        Python version, with automatic version detection if not specified.

        The language pack system supports inheritance, so newer Python
        versions automatically inherit translations from earlier versions.

        Args:
            language: ISO 639-1 language code (e.g., 'es', 'ar', 'hi')
            python_version: Python version string (e.g., '3.10', '3.13')
                           If None, auto-detects from runtime (sys.version_info)

        Returns:
            Configured TreeSitterTranslator ready for code translation

        Raises:
            PackNotFoundError: If language pack doesn't exist for this version
                              (includes list of available languages)
            PackValidationError: If pack file is corrupted or invalid

        Example:
            >>> # Auto-detect version from runtime
            >>> translator = TreeSitterTranslator.from_language_pack("es")
            >>> code = "def greet(): print('Hello')"
            >>> spanish = translator.translate_code(code)
            >>> print(spanish)
            definir greet(): imprimir('Hello')

            >>> # Pin to specific version
            >>> translator = TreeSitterTranslator.from_language_pack("es", "3.10")

            >>> # Round-trip translation
            >>> en_to_es = TreeSitterTranslator.from_language_pack("es")
            >>> es_to_en = en_to_es.reverse()

        See Also:
            - reverse(): Create bidirectional translator
            - list_available_languages(): Get available language packs

        Note:
            Language packs are cached after first load for performance.
            Concurrent calls are thread-safe.
        """
        # Import here to avoid circular dependency
        from legesher_i18n import LanguagePackLoader

        # Auto-detect Python version if not provided
        if python_version is None:
            version_info = sys.version_info
            python_version = f"{version_info.major}.{version_info.minor}"
            logger.debug(f"Auto-detected Python version: {python_version}")

        # Load language pack
        loader = LanguagePackLoader()
        pack = loader.load(language, target="python", version=python_version)

        logger.info(
            f"Loaded language pack: {pack.language} ({len(pack.keywords)} keywords, "
            f"{len(pack.builtins)} builtins) for Python {pack.version}"
        )

        # Merge exceptions into builtin_map (PascalCase remapping)
        from ..utils import merge_exception_translations

        builtin_map = pack.builtins
        if hasattr(pack, "exceptions") and pack.exceptions:
            builtin_map = merge_exception_translations(pack.builtins, pack.exceptions)
            logger.debug(
                f"Merged {len(pack.exceptions)} exception translations into builtin map"
            )

        # CORE-710: pull implicit_params from the pack if present (defaults to {})
        implicit_param_map = getattr(pack, "implicit_params", {}) or {}

        return cls(
            keyword_map=pack.keywords,
            builtin_map=builtin_map,
            implicit_param_map=implicit_param_map,
            python_version=python_version,
        )

    @classmethod
    def list_available_languages(cls) -> list[tuple[str, str]]:
        """Get list of available language packs.

        Returns:
            List of (language_code, language_name) tuples

        Example:
            >>> TreeSitterTranslator.list_available_languages()
            [('ar', 'Arabic'), ('es', 'Spanish'), ('hi', 'Hindi')]

        Note:
            This scans the language pack directory to find all available
            languages for Python.
        """
        # Import here to avoid circular dependency
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()
        return loader.list_available_languages(target="python")

    def get_pack_info(self) -> dict[str, str | int]:
        """Get information about the translator's language maps.

        Returns:
            Dictionary with translation map metadata

        Example:
            >>> translator = TreeSitterTranslator.from_language_pack("es")
            >>> info = translator.get_pack_info()
            >>> info
            {'python_version': '3.13', 'keyword_count': 35, 'builtin_count': 69}
        """
        return {
            "python_version": self.python_version,
            "keyword_count": len(self.mapper.keyword_map),
            "builtin_count": len(self.mapper.builtin_map),
        }
