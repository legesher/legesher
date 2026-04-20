"""Cultural comment parser for Legesher translation engine.

This module implements parsing and extraction of cultural context comments
that use the special syntax: #@culture[lang]: explanation

Cultural comments provide linguistic/cultural context that should never be
machine-translated, as specified in the MLCP (Multilingual Code Protocol).

The parser is designed to work with both token-based (current) and tree-sitter
(future) transformation approaches by accepting multiple input types.

Example:
    >>> parser = CulturalCommentParser()
    >>> code = '''
    ... #@culture[es]: "rango" puede significar "rank" o "range"
    ... para i en rango(10):
    ...     imprimir(i)
    ... '''
    >>> metadata = parser.parse_from_source(code)
    >>> metadata.has_comments()
    True
    >>> comments = metadata.get_for_line(2)
    >>> comments[0].language
    'es'
"""

import io
import logging
import re
import tokenize
from collections.abc import Iterable

from .types import CulturalComment, CulturalCommentMetadata

# Configure logger
logger = logging.getLogger(__name__)


class CulturalCommentParser:
    """Parser for cultural context comments in source code.

    Extracts cultural comments from Python source code using the syntax:
        #@culture[lang]: explanation

    Designed to be transformation-agnostic - works with both token-based
    (current) and tree-sitter (future) approaches.

    The parser can process comments from:
    1. Token stream (efficient, no double-tokenization)
    2. Source code string (convenience method)

    Attributes:
        language: Programming language being parsed (default: "python")
        pattern: Compiled regex pattern for cultural comment syntax

    Example:
        >>> parser = CulturalCommentParser()
        >>> # From source code
        >>> metadata = parser.parse_from_source(code)
        >>> # From token stream (more efficient)
        >>> tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        >>> metadata = parser.parse_from_tokens(tokens)
    """

    # Maximum length for cultural comment content (prevent ReDoS and memory issues)
    MAX_CONTENT_LENGTH = 10000  # 10K characters should be more than enough

    # Extensible pattern dictionary for future multi-language support
    # Each language has its own comment syntax
    # Note: Using limited quantifier {0,MAX} instead of * to prevent ReDoS attacks
    PATTERNS = {
        "python": r"#@culture\[([a-z]{2})\]:\s*(.{0,10000})$",
        # Future support:
        # "javascript": r"//\s*@culture\[([a-z]{2})\]:\s*(.{0,10000})$",
        # "rust": r"//\s*@culture\[([a-z]{2})\]:\s*(.{0,10000})$",
    }

    # Valid ISO 639-1 language codes (2-letter lowercase)
    # This is a curated list of commonly used languages
    # Full list: https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    # Using frozenset for immutability (class constant should not be modified)
    VALID_LANG_CODES = frozenset(
        {
            "en",  # English
            "es",  # Spanish
            "ar",  # Arabic
            "zh",  # Chinese
            "hi",  # Hindi
            "pt",  # Portuguese
            "ru",  # Russian
            "ja",  # Japanese
            "de",  # German
            "fr",  # French
            "ko",  # Korean
            "it",  # Italian
            "tr",  # Turkish
            "vi",  # Vietnamese
            "pl",  # Polish
            "uk",  # Ukrainian
            "nl",  # Dutch
            "th",  # Thai
            "id",  # Indonesian
            "ro",  # Romanian
            # Add more as needed for community language packs
        }
    )

    def __init__(self, language: str = "python"):
        """Initialize parser for specific programming language.

        Args:
            language: Programming language to parse (default: "python")

        Raises:
            ValueError: If language is not supported
        """
        if language not in self.PATTERNS:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported: {list(self.PATTERNS.keys())}"
            )

        self.language = language
        self.pattern = re.compile(self.PATTERNS[language])

    def parse_from_tokens(
        self, tokens: Iterable[tokenize.TokenInfo]
    ) -> CulturalCommentMetadata:
        """Extract cultural comments from token stream.

        This is the most efficient method as it processes tokens directly
        without requiring double-tokenization. Designed to integrate with
        TokenTranslator's existing tokenization pass.

        Args:
            tokens: Iterable of TokenInfo objects from tokenize.generate_tokens()

        Returns:
            CulturalCommentMetadata containing all parsed cultural comments

        Example:
            >>> tokens = tokenize.generate_tokens(io.StringIO(code).readline)
            >>> metadata = parser.parse_from_tokens(tokens)
        """
        metadata = CulturalCommentMetadata()

        for tok in tokens:
            # Only process COMMENT tokens
            if tok.type == tokenize.COMMENT:
                # Check if this is a cultural comment
                is_valid, result = self.validate_syntax(tok.string)

                if is_valid and result is not None:
                    lang_code, content = result
                    # Note: Content length is already bounded by regex pattern
                    # (max 10,000 chars) to prevent ReDoS and memory exhaustion

                    # tok.start is a tuple: (line_number, column_offset)
                    # line_number is 1-indexed, column_offset is 0-indexed
                    comment = CulturalComment(
                        language=lang_code,
                        content=content,
                        line_number=tok.start[0],
                        column_offset=tok.start[1],
                        raw_text=tok.string,
                    )
                    metadata.add_comment(comment)
                    logger.debug(
                        f"Parsed cultural comment: lang={lang_code}, "
                        f"line={tok.start[0]}, content={content[:50]}..."
                    )

        return metadata

    def parse_from_source(self, source_code: str) -> CulturalCommentMetadata:
        """Extract cultural comments from source code string.

        Convenience method that tokenizes the source code internally.
        Less efficient than parse_from_tokens() if you already have tokens.

        Args:
            source_code: Python source code as string

        Returns:
            CulturalCommentMetadata containing all parsed cultural comments

        Example:
            >>> code = '''
            ... #@culture[es]: explanation
            ... def foo(): pass
            ... '''
            >>> metadata = parser.parse_from_source(code)
        """
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)
            return self.parse_from_tokens(tokens)
        except tokenize.TokenError as e:
            # Handle incomplete code gracefully
            logger.info(f"Tokenization error (incomplete code?): {e}")
            return CulturalCommentMetadata()

    def validate_syntax(self, comment: str) -> tuple[bool, tuple[str, str] | None]:
        """Validate cultural comment syntax.

        Checks if a comment string matches the cultural comment pattern
        and validates the language code.

        Args:
            comment: Comment string to validate (e.g., "#@culture[es]: text")

        Returns:
            Tuple of (is_valid, result) where:
            - is_valid: True if syntax is valid
            - result: (lang_code, content) if valid, None otherwise

        Example:
            >>> parser.validate_syntax("#@culture[es]: explanation")
            (True, ('es', 'explanation'))
            >>> parser.validate_syntax("#@culture[zz]: invalid")
            (False, None)
            >>> parser.validate_syntax("# regular comment")
            (False, None)
        """
        match = self.pattern.match(comment)

        if not match:
            # Not a cultural comment (regular comment or malformed)
            return False, None

        lang_code, content = match.groups()

        # Validate language code
        if lang_code not in self.VALID_LANG_CODES:
            logger.warning(
                f"Invalid language code in cultural comment: {lang_code!r}. "
                f"Valid codes: {sorted(self.VALID_LANG_CODES)}"
            )
            return False, None

        # Content can be empty - that's valid
        # (developer might fill it in later)
        return True, (lang_code, content.strip())

    def is_cultural_comment(self, comment: str) -> bool:
        """Quick check if a comment is a cultural comment.

        Faster than validate_syntax() when you only need to know
        if it's a cultural comment, not extract the data.

        Args:
            comment: Comment string to check

        Returns:
            True if comment matches cultural comment syntax (and has valid lang code)

        Example:
            >>> parser.is_cultural_comment("#@culture[es]: text")
            True
            >>> parser.is_cultural_comment("# regular comment")
            False
        """
        is_valid, _ = self.validate_syntax(comment)
        return is_valid
