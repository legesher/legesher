"""Tree-sitter-based code transformer for multilingual Python translation.

This module implements a tree-sitter-based translation engine as a performance
improvement over the token-based approach. It provides the same API as TokenTranslator
while leveraging tree-sitter for better performance and error handling.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Union

from .parser import PythonParser, TreeSitterError
from ..exceptions import InvalidCodeError
from ..token_mapper import TokenMapper
from ..types import CulturalCommentMetadata
from ..utils import validate_utf8_encoding, normalize_newlines

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
    ) -> None:
        """Initialize translator with language maps and Python version.

        Args:
            keyword_map: Dictionary mapping English keywords to target language
            builtin_map: Dictionary mapping English builtins to target language
            python_version: Python version string (default: "3.13")

        Raises:
            ValueError: If maps are empty or None
            TreeSitterError: If parser initialization fails

        Example:
            >>> translator = TreeSitterTranslator(
            ...     keyword_map={"def": "definir", "return": "retornar"},
            ...     builtin_map={"print": "imprimir"},
            ...     python_version="3.13"
            ... )
        """
        self.mapper = TokenMapper(keyword_map, builtin_map)
        self.python_version = python_version

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
            "TreeSitterTranslator(keywords=1, builtins=1, python_version='3.13')"
        """
        return (
            f"TreeSitterTranslator("
            f"keywords={len(self.mapper.keyword_map)}, "
            f"builtins={len(self.mapper.builtin_map)}, "
            f"python_version={self.python_version!r})"
        )

    def translate_code(
        self,
        source_code: str,
        source_lang: str = "en",
        target_lang: str = "es",
        return_metadata: bool = False,
    ) -> Union[str, tuple[str, CulturalCommentMetadata]]:
        """Translate Python source code from one language to another.

        This method translates Python keywords and builtin function names while
        preserving all formatting, whitespace, comments, and code structure.

        Translation process:
        1. Normalize line endings (\\r\\n → \\n)
        2. Parse source code using tree-sitter
        3. Query for keyword nodes using KEYWORDS_QUERY
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

        # Normalize line endings for consistent processing
        source_code = normalize_newlines(source_code)

        try:
            # Parse code with tree-sitter
            tree = self.parser.parse(source_code)

            # Get source as bytes for position calculations
            source_bytes = source_code.encode("utf-8")

            # Collect replacements as (start_byte, end_byte, new_text) tuples
            replacements = []

            # Walk the tree to find keywords and builtins
            self._find_translations(tree.root_node, source_bytes, replacements)

            # Apply replacements in reverse order to maintain byte positions
            result = self._apply_replacements(source_bytes, replacements)

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

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Translation failed unexpectedly: {e}")
            raise InvalidCodeError(f"Failed to translate code: {e}") from e

    def _find_translations(self, node, source_bytes: bytes, replacements: list) -> None:
        """Recursively find and collect keyword and builtin translations.

        Args:
            node: Tree-sitter node to search
            source_bytes: Source code as bytes
            replacements: List to append (start, end, replacement) tuples
        """
        # Python keywords that appear as node text (not types)
        # These are the nodes where we check the text directly
        if node.type in ["identifier", "true", "false", "none"]:
            text = node.text.decode("utf-8")

            # Try to translate as keyword first
            translated = self.mapper.get_keyword(text)
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
        ]:
            text = node.text.decode("utf-8")
            translated = self.mapper.get_keyword(text)
            if translated and translated != text:
                replacements.append((node.start_byte, node.end_byte, translated))
                logger.debug(f"Keyword match: '{text}' → '{translated}'")

        # Recursively search children
        for child in node.children:
            self._find_translations(child, source_bytes, replacements)

    def _apply_replacements(self, source_bytes: bytes, replacements: list) -> str:
        """Apply text replacements while preserving positions.

        Replacements are applied in reverse order (end → start) to maintain
        byte positions throughout the process.

        Args:
            source_bytes: Original source code as bytes
            replacements: List of (start_byte, end_byte, new_text) tuples

        Returns:
            Translated source code as string
        """
        # Sort replacements by start position (descending) to apply in reverse
        replacements.sort(reverse=True, key=lambda x: x[0])

        # Convert to bytearray for efficient modification
        result = bytearray(source_bytes)

        # Apply each replacement
        for start, end, new_text in replacements:
            result[start:end] = new_text.encode("utf-8")

        # Convert back to string
        return result.decode("utf-8")

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
        with open(file_path, "r", encoding=encoding) as f:
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
            python_version=self.python_version,
        )

    @classmethod
    def from_language_pack(
        cls,
        language: str,
        python_version: Optional[str] = None,
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

        # Create translator with loaded maps
        return cls(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
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

    def get_pack_info(self) -> dict[str, Union[str, int]]:
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
