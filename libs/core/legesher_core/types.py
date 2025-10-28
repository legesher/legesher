"""Type definitions for Legesher Core translation engine.

This module provides type hints and Protocols for type safety
and better IDE autocomplete support throughout the legesher-core package.

Note: We use standard dict[str, str] for translation maps instead of TypedDict
because Python keywords cannot be used as TypedDict field names.
"""

from dataclasses import dataclass, field
from typing import Protocol


# Type aliases for translation maps
# We use dict[str, str] instead of TypedDict because Python keywords
# (like 'def', 'class', 'if', etc.) cannot be TypedDict field names.
# This provides type safety while allowing any string keys.
KeywordMap = dict[str, str]
BuiltinMap = dict[str, str]


# Cultural comment types
@dataclass(frozen=True)
class CulturalComment:
    """Immutable cultural comment metadata.

    Cultural comments use special syntax: #@culture[lang]: explanation
    They provide context that should never be machine-translated.

    Attributes:
        language: ISO 639-1 language code (e.g., "es", "en", "ar")
        content: The explanation text (can be empty)
        line_number: 1-indexed line number where comment appears
        column_offset: 0-indexed column offset in the line
        raw_text: Original raw comment string for lossless preservation

    Example:
        >>> comment = CulturalComment(
        ...     language="es",
        ...     content="'rango' puede significar 'rank' o 'range'",
        ...     line_number=5,
        ...     column_offset=4,
        ...     raw_text="#@culture[es]: 'rango' puede significar 'rank' o 'range'"
        ... )
    """

    language: str
    content: str
    line_number: int
    column_offset: int
    raw_text: str

    def __post_init__(self):
        """Validate cultural comment fields."""
        # Validate language code is 2 lowercase letters
        if not isinstance(self.language, str) or len(self.language) != 2:
            raise ValueError(
                f"Language code must be 2 characters, got: {self.language!r}"
            )
        if not self.language.islower():
            raise ValueError(f"Language code must be lowercase, got: {self.language!r}")

        # Validate line number is positive
        if self.line_number < 1:
            raise ValueError(f"Line number must be >= 1, got: {self.line_number}")

        # Validate column offset is non-negative
        if self.column_offset < 0:
            raise ValueError(f"Column offset must be >= 0, got: {self.column_offset}")


@dataclass
class CulturalCommentMetadata:
    """Container for all cultural comments in a source file.

    Provides efficient querying by line number and language for IDE integration.
    Uses internal indexing for O(1) language queries.

    Attributes:
        comments: Mapping from line number to list of cultural comments on that line

    Example:
        >>> metadata = CulturalCommentMetadata()
        >>> comment = CulturalComment("es", "explanation", 5, 0, "#@culture[es]: explanation")
        >>> metadata.add_comment(comment)
        >>> metadata.get_for_line(5)
        [CulturalComment(...)]
    """

    comments: dict[int, list[CulturalComment]] = field(default_factory=dict)
    # Performance: Language index for O(1) lookups instead of O(n) iteration
    _language_index: dict[str, list[CulturalComment]] = field(
        default_factory=lambda: {}, init=False, repr=False
    )

    def add_comment(self, comment: CulturalComment) -> None:
        """Add a cultural comment to the metadata.

        Updates both line-based and language-based indexes for efficient queries.

        Args:
            comment: The cultural comment to add
        """
        # Add to line-based index
        if comment.line_number not in self.comments:
            self.comments[comment.line_number] = []
        self.comments[comment.line_number].append(comment)

        # Add to language-based index for O(1) language queries
        if comment.language not in self._language_index:
            self._language_index[comment.language] = []
        self._language_index[comment.language].append(comment)

    def get_for_line(self, line_number: int) -> list[CulturalComment]:
        """Get all cultural comments for a specific line.

        Args:
            line_number: 1-indexed line number

        Returns:
            List of cultural comments on that line (empty if none)
        """
        return self.comments.get(line_number, [])

    def get_for_language(self, language: str) -> list[CulturalComment]:
        """Get all cultural comments in a specific language.

        Performance: O(1) lookup using language index instead of O(n) iteration.

        Args:
            language: ISO 639-1 language code (e.g., "es")

        Returns:
            List of cultural comments in that language
        """
        return self._language_index.get(language, [])

    def has_comments(self) -> bool:
        """Check if any cultural comments exist.

        Returns:
            True if at least one cultural comment exists
        """
        return bool(self.comments)

    def get_all_languages(self) -> set[str]:
        """Get set of all language codes present in comments.

        Performance: O(1) using cached language index keys.

        Returns:
            Set of ISO 639-1 language codes used in cultural comments

        Example:
            >>> metadata.get_all_languages()
            {'es', 'en', 'ar'}
        """
        return set(self._language_index.keys())

    def to_dict(self) -> dict:
        """Serialize to dictionary for storage (e.g., git metadata).

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "comments": {
                str(line_num): [
                    {
                        "language": c.language,
                        "content": c.content,
                        "line_number": c.line_number,
                        "column_offset": c.column_offset,
                        "raw_text": c.raw_text,
                    }
                    for c in comments_list
                ]
                for line_num, comments_list in self.comments.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CulturalCommentMetadata":
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation (from to_dict())

        Returns:
            CulturalCommentMetadata instance
        """
        metadata = cls()
        for line_str, comments_list in data.get("comments", {}).items():
            for comment_dict in comments_list:
                comment = CulturalComment(
                    language=comment_dict["language"],
                    content=comment_dict["content"],
                    line_number=comment_dict["line_number"],
                    column_offset=comment_dict["column_offset"],
                    raw_text=comment_dict["raw_text"],
                )
                metadata.add_comment(comment)
        return metadata


class Translator(Protocol):
    """Protocol defining the translator interface.

    This protocol allows type checking for any class that implements
    the translator interface, supporting dependency injection and testing.

    Example:
        >>> def process_code(translator: Translator, code: str) -> str:
        ...     return translator.translate_code(code, "en", "es")
    """

    def translate_code(
        self, source_code: str, source_lang: str = "en", target_lang: str = "es"
    ) -> str:
        """Translate Python source code from one language to another.

        Args:
            source_code: Python source code to translate
            source_lang: Source language code (default: "en")
            target_lang: Target language code (default: "es")

        Returns:
            Translated Python source code
        """
        ...
