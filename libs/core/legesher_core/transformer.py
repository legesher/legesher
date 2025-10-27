"""Token-based code transformer for multilingual Python translation.

This module implements the core translation engine using Python's tokenize module
to transform Python code between natural languages while preserving formatting,
whitespace, comments, and code structure.
"""

import io
import logging
import tokenize
from pathlib import Path

from .exceptions import InvalidCodeError
from .token_mapper import TokenMapper
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
        self, source_code: str, source_lang: str = "en", target_lang: str = "es"
    ) -> str:
        """Translate Python source code from one language to another.

        This method translates Python keywords and builtin function names while
        preserving all formatting, whitespace, comments, and code structure.

        Translation process:
        1. Normalize line endings (\\r\\n → \\n)
        2. Tokenize source code using Python's tokenize module
        3. For each NAME token, check if it's a keyword or builtin
        4. Replace with translated version if found in maps
        5. Reconstruct code using untokenize, preserving formatting

        Args:
            source_code: Python source code to translate
            source_lang: Source language code (currently unused, for future)
            target_lang: Target language code (currently unused, for future)

        Returns:
            Translated Python source code with preserved formatting

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
            - Incomplete code is handled gracefully (translates valid portion)
            - Syntax errors return original code unchanged
        """
        # Handle empty input
        if not source_code or not source_code.strip():
            return source_code

        # Normalize line endings for consistent processing
        source_code = normalize_newlines(source_code)

        try:
            # Tokenize the source code
            tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)

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

            return result

        except tokenize.TokenError as e:
            # Handle incomplete code gracefully (expected during real-time editing)
            logger.info(f"Incomplete code handled gracefully: {e}")
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
