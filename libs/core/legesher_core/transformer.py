"""Token-based code transformer for multilingual Python translation.

This module implements the core translation engine using Python's tokenize module
to transform Python code between natural languages while preserving formatting,
whitespace, comments, and code structure.
"""

import io
import logging
import sys
import tokenize
from pathlib import Path
from typing import Optional, Union

from .cultural_comments import CulturalCommentParser
from .exceptions import InvalidCodeError
from .token_mapper import TokenMapper
from .types import CulturalCommentMetadata
from .utils import validate_utf8_encoding, normalize_newlines

# Configure logger
logger = logging.getLogger(__name__)


class TokenTranslator:
    """Translate Python code between natural languages using token-based transformation.

    This class provides the main translation engine for Legesher, converting Python
    keywords and builtin function names between languages (e.g., English to Spanish)
    while perfectly preserving all formatting, whitespace, comments, and code structure.

    The translator uses Python's tokenize module for parsing, which:
    - Preserves exact formatting (whitespace, indentation, blank lines)
    - Handles incomplete code gracefully (for real-time editing)
    - Works line-by-line for fast performance
    - Doesn't require semantic understanding of code

    Attributes:
        mapper: TokenMapper instance for translation lookups
        python_version: Target Python version (e.g., "3.13")

    Example:
        >>> spanish_keywords = {"def": "definir", "return": "retornar"}
        >>> spanish_builtins = {"print": "imprimir", "len": "longitud"}
        >>> translator = TokenTranslator(
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

        Example:
            >>> translator = TokenTranslator(
            ...     keyword_map={"def": "definir", "return": "retornar"},
            ...     builtin_map={"print": "imprimir"},
            ...     python_version="3.13"
            ... )
        """
        self.mapper = TokenMapper(keyword_map, builtin_map)
        self.python_version = python_version

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
        2. Tokenize source code using Python's tokenize module
        3. Optionally extract cultural comment metadata (for IDE integration)
        4. For each NAME token, check if it's a keyword or builtin
        5. Replace with translated version if found in maps
        6. Reconstruct code using untokenize, preserving formatting

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

            >>> # With metadata for IDE integration
            >>> code_with_cultural = '''
            ... #@culture[es]: explanation
            ... def foo(): pass
            ... '''
            >>> translated, metadata = translator.translate_code(
            ...     code_with_cultural, "en", "es", return_metadata=True
            ... )
            >>> metadata.has_comments()
            True

        Note:
            - Comments and docstrings are NOT translated (preserved as-is)
            - Cultural comments (#@culture[lang]: ...) are extracted when
              return_metadata=True for IDE tooltip/decoration support
            - Variable and function names are NOT translated (out of scope)
            - Incomplete code is handled gracefully (translates valid portion)
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
            # Tokenize the source code
            tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))

            # Extract cultural comment metadata if requested (for IDE integration)
            cultural_metadata = None
            if return_metadata:
                parser = CulturalCommentParser()
                cultural_metadata = parser.parse_from_tokens(iter(tokens))
                logger.debug(
                    f"Extracted {len(cultural_metadata.comments)} "
                    f"cultural comment(s) from source"
                )

            # Translate tokens
            translated_tokens = []
            for tok in tokens:
                # Check if this is a NAME token (keyword, builtin, or identifier)
                if tok.type == tokenize.NAME:
                    # Try to translate as keyword first
                    translated = self.mapper.get_keyword(tok.string)
                    if translated and translated != tok.string:
                        # Create new token only when translation changes the string
                        new_tok = tokenize.TokenInfo(
                            tok.type, translated, tok.start, tok.end, tok.line
                        )
                        translated_tokens.append(new_tok)
                        continue

                    # Try to translate as builtin
                    translated = self.mapper.get_builtin(tok.string)
                    if translated and translated != tok.string:
                        # Create new token only when translation changes the string
                        new_tok = tokenize.TokenInfo(
                            tok.type, translated, tok.start, tok.end, tok.line
                        )
                        translated_tokens.append(new_tok)
                        continue

                # Keep token unchanged (identifiers, operators, etc.)
                translated_tokens.append(tok)

            # Reconstruct code from translated tokens
            result = tokenize.untokenize(translated_tokens)

            # untokenize returns bytes in some cases, decode to string
            if isinstance(result, bytes):
                result = result.decode("utf-8")

            # Return with or without metadata based on request
            if return_metadata:
                return result, cultural_metadata
            return result

        except tokenize.TokenError as e:
            # Handle incomplete code gracefully (expected during real-time editing)
            logger.info(f"Incomplete code handled gracefully: {e}")
            if return_metadata:
                return source_code, CulturalCommentMetadata()
            return source_code

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Translation failed unexpectedly: {e}")
            raise InvalidCodeError(f"Failed to translate code: {e}") from e

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

    def reverse(self) -> "TokenTranslator":
        """Create a reversed translator (target → source language).

        Returns a new TokenTranslator with reversed translation maps, enabling
        bidirectional translation (e.g., Spanish → English).

        Returns:
            New TokenTranslator with reversed maps

        Example:
            >>> en_to_es = TokenTranslator.from_language_pack("es")
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
        return TokenTranslator(
            keyword_map=reversed_mapper.keyword_map,
            builtin_map=reversed_mapper.builtin_map,
            python_version=self.python_version,
        )

    @classmethod
    def from_language_pack(
        cls,
        language: str,
        python_version: Optional[str] = None,
    ) -> "TokenTranslator":
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
            Configured TokenTranslator ready for code translation

        Raises:
            PackNotFoundError: If language pack doesn't exist for this version
                              (includes list of available languages)
            PackValidationError: If pack file is corrupted or invalid

        Example:
            >>> # Auto-detect version from runtime
            >>> translator = TokenTranslator.from_language_pack("es")
            >>> code = "def greet(): print('Hello')"
            >>> spanish = translator.translate_code(code)
            >>> print(spanish)
            definir greet(): imprimir('Hello')

            >>> # Pin to specific version
            >>> translator = TokenTranslator.from_language_pack("es", "3.10")

            >>> # Round-trip translation
            >>> en_to_es = TokenTranslator.from_language_pack("es")
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
            >>> TokenTranslator.list_available_languages()
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
            >>> translator = TokenTranslator.from_language_pack("es")
            >>> info = translator.get_pack_info()
            >>> info
            {'python_version': '3.13', 'keyword_count': 35, 'builtin_count': 69}
        """
        return {
            "python_version": self.python_version,
            "keyword_count": len(self.mapper.keyword_map),
            "builtin_count": len(self.mapper.builtin_map),
        }
