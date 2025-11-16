"""Semantic tokens provider for syntax highlighting translated keywords.

This module provides LSP semantic token highlighting for translated Python keywords.
Uses Python's tokenize module for accurate, fast token parsing that automatically
handles strings, comments, and other edge cases.

Implementation for CORE-450.
"""

import io
import logging
import tokenize
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import SemanticTokens

logger = logging.getLogger(__name__)

# Semantic token types (indices must match the legend order in server.py)
TOKEN_TYPE_KEYWORD = 0
TOKEN_TYPE_CLASS = 1
TOKEN_TYPE_FUNCTION = 2
TOKEN_TYPE_VARIABLE = 3
TOKEN_TYPE_PARAMETER = 4


def provide_semantic_tokens(server: "LegesherLanguageServer", uri: str) -> SemanticTokens | None:
    """Provide semantic tokens for entire document.

    Args:
        server: Language server instance
        uri: Document URI

    Returns:
        Semantic tokens encoded in LSP delta format, or None if document not found

    Note:
        Implementation for CORE-450 - Phase 1: Basic keyword highlighting
    """
    # Get document
    doc = server.document_manager.get_document(uri)
    if not doc:
        return None

    # Create semantic tokens provider
    provider = SemanticTokensProvider(
        source_lang=server.config.source_language,
        target_lang=server.config.target_language,
        document_text=doc.text,
        document_uri=uri,
    )

    # Get tokens (synchronous)
    tokens = provider.get_semantic_tokens()

    # Encode in LSP delta format
    encoded_data = provider.encode_tokens(tokens)

    return SemanticTokens(data=encoded_data)


class SemanticTokensProvider:
    """Provides semantic tokens for syntax highlighting.

    This provider identifies translated Python keywords and encodes them
    as semantic tokens for LSP-based syntax highlighting.
    """

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        document_text: str,
        document_uri: str,
    ):
        """Initialize semantic tokens provider.

        Args:
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es', 'ar')
            document_text: Full document text
            document_uri: Document URI for context
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.document_text = document_text
        self.document_uri = document_uri

        # Lazy-load keyword mappings
        self._translated_keywords: set[str] | None = None
        self._reverse_keyword_map: dict[str, str] | None = None

    def _load_keyword_mappings(self) -> None:
        """Load keyword mappings from language pack (lazy initialization).

        This loads the language pack on first use to avoid initialization overhead.
        Creates both a set for fast lookup and reverse map for translation.
        """
        if self._translated_keywords is not None:
            return  # Already loaded

        from legesher_i18n import LanguagePackLoader

        try:
            # Load language pack for target language
            # Use version 3.10 as base (compatible with all Python 3.x)
            loader = LanguagePackLoader()
            pack = loader.load(language=self.target_lang, target="python", version="3.10")

            # Build reverse keyword map: translated -> english
            self._reverse_keyword_map = {
                translated: english for english, translated in pack.keywords.items()
            }

            # Also include English keywords (for mixed-language code)
            for english in pack.keywords.keys():
                if english not in self._reverse_keyword_map:
                    self._reverse_keyword_map[english] = english

            # Create fast lookup set
            self._translated_keywords = set(self._reverse_keyword_map.keys())

            logger.debug(
                f"Loaded {len(self._translated_keywords)} keywords "
                f"for language '{self.target_lang}'"
            )

        except Exception as e:
            logger.warning(f"Failed to load language pack for '{self.target_lang}': {e!r}")
            # Fallback to empty sets
            self._translated_keywords = set()
            self._reverse_keyword_map = {}

    def get_semantic_tokens(self) -> list[tuple[int, int, int, int, int]]:
        """Parse document and extract semantic tokens.

        Returns:
            List of tokens as tuples: (line, char, length, token_type, modifiers)

        Note:
            Uses Python's tokenize module for accurate parsing that:
            - Automatically skips strings and comments
            - Handles all Python syntax edge cases
            - Fast (O(n) single pass)
        """
        # Ensure keyword mappings are loaded
        self._load_keyword_mappings()

        if not self._translated_keywords:
            # No keywords loaded - return empty list
            return []

        tokens: list[tuple[int, int, int, int, int]] = []

        try:
            # Tokenize document
            # tokenize requires bytes, convert to StringIO wrapped in BytesIO
            readline = io.BytesIO(self.document_text.encode("utf-8")).readline

            for tok in tokenize.tokenize(readline):
                # Only process NAME tokens (identifiers/keywords)
                if tok.type != tokenize.NAME:
                    continue

                # Check if token is a translated keyword
                if tok.string in self._translated_keywords:
                    # Token is a keyword! Add to semantic tokens
                    # LSP uses 0-based line numbers, tokenize uses 1-based
                    line = tok.start[0] - 1
                    char = tok.start[1]
                    length = len(tok.string)
                    token_type = TOKEN_TYPE_KEYWORD
                    modifiers = 0  # No modifiers in Phase 1

                    tokens.append((line, char, length, token_type, modifiers))

        except tokenize.TokenError as e:
            # Document has syntax errors - tokenize fails
            logger.debug(f"Tokenize error for {self.document_uri}: {e!r}")
            # Return partial tokens collected so far
            return tokens

        except Exception as e:
            logger.error(
                f"Unexpected error tokenizing document {self.document_uri}: {e!r}",
                exc_info=True,
            )
            return []

        return tokens

    def encode_tokens(self, tokens: list[tuple[int, int, int, int, int]]) -> list[int]:
        """Encode tokens in LSP delta format.

        LSP semantic tokens are encoded as a flat array of integers using delta encoding:
        [deltaLine, deltaChar, length, tokenType, tokenModifiers]

        Delta encoding means:
        - First token: absolute position
        - Subsequent tokens on same line: deltaLine=0, deltaChar=relative to previous
        - Subsequent tokens on new line: deltaLine=difference, deltaChar=absolute column

        Args:
            tokens: List of (line, char, length, token_type, modifiers) tuples

        Returns:
            Encoded token data as flat integer array

        Example:
            Input:  [(0, 0, 3, 0, 0), (0, 10, 5, 0, 0), (2, 4, 6, 0, 0)]
            Output: [0, 0, 3, 0, 0,  0, 10, 5, 0, 0,  2, 4, 6, 0, 0]
                     ^  ^  ^  ^  ^   ^   ^  ^  ^  ^   ^  ^  ^  ^  ^
                     |  |  |  |  |   |   |  |  |  |   |  |  |  |  |
                     L  C  L  T  M   ΔL  ΔC L  T  M   ΔL C  L  T  M
        """
        if not tokens:
            return []

        # Sort tokens by line, then by character position
        sorted_tokens = sorted(tokens, key=lambda t: (t[0], t[1]))

        encoded: list[int] = []
        prev_line = 0
        prev_char = 0

        for line, char, length, token_type, modifiers in sorted_tokens:
            # Calculate deltas
            delta_line = line - prev_line
            delta_char = char - prev_char if delta_line == 0 else char

            # Append encoded token (5 integers per token)
            encoded.extend([delta_line, delta_char, length, token_type, modifiers])

            # Update previous position
            prev_line = line
            prev_char = char

        return encoded
