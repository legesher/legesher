"""Type definitions for Legesher Core translation engine.

This module provides type hints and Protocols for type safety
and better IDE autocomplete support throughout the legesher-core package.

Note: We use standard dict[str, str] for translation maps instead of TypedDict
because Python keywords cannot be used as TypedDict field names.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional, Protocol, TypedDict, Union, runtime_checkable

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


# Metadata tracking constants
METADATA_VERSION = "1.0"
TRANSLATION_METHODS = ["token_transformer", "tree_sitter", "manual"]


class TranslationRecord(TypedDict):
    """Record of a single translation operation.

    Tracks when and how a file was translated to a specific language.
    Used for debugging, auditing, and understanding translation history.

    Attributes:
        language: Target language code (e.g., "en", "es", "ar")
        method: Translation method used (see TRANSLATION_METHODS constant)
        timestamp: ISO 8601 timestamp of translation (e.g., "2025-11-06T10:30:00Z")
        commit_sha: Git commit SHA if available, None otherwise
        translator_version: Version of legesher-core that performed translation
        python_version: Python version used (e.g., "3.13", "3.12")

    Example:
        >>> record: TranslationRecord = {
        ...     "language": "es",
        ...     "method": "token_transformer",
        ...     "timestamp": "2025-11-06T10:30:00Z",
        ...     "commit_sha": "a91228a",
        ...     "translator_version": "0.1.0",
        ...     "python_version": "3.13"
        ... }
    """

    language: str
    method: str
    timestamp: str
    commit_sha: str | None
    translator_version: str
    python_version: str


class HistoryEntry(TypedDict):
    """Single entry in translation history log.

    Records git filter operations (clean/smudge) for audit trail.
    Helps understand how files move between languages during git operations.

    Attributes:
        action: Git filter action - "clean" (working → git) or "smudge" (git → working)
        from_language: Source language code before translation
        to_language: Target language code after translation
        timestamp: ISO 8601 timestamp of operation
        commit_sha: Git commit SHA if available, None otherwise

    Example:
        >>> entry: HistoryEntry = {
        ...     "action": "clean",
        ...     "from_language": "es",
        ...     "to_language": "en",
        ...     "timestamp": "2025-11-06T10:30:00Z",
        ...     "commit_sha": "a91228a"
        ... }
    """

    action: str
    from_language: str
    to_language: str
    timestamp: str
    commit_sha: str | None


class FileMetadata(TypedDict):
    """Complete metadata for a single translated file.

    Stored in .legesher/metadata/<file>.yaml to track translation state,
    history, and configuration for each file in the repository.

    Attributes:
        file: Relative path from repository root (e.g., "src/main.py")
        original_language: Language file was originally authored in
        canonical_language: Language stored in git (usually "en")
        python_version: Python version for this file (e.g., "3.13")
        created_at: ISO 8601 timestamp when metadata was first created
        updated_at: ISO 8601 timestamp of last metadata update
        translations: List of all translation operations performed
        history: Log of git filter operations (clean/smudge)

    Example:
        >>> metadata: FileMetadata = {
        ...     "file": "src/calculator.py",
        ...     "original_language": "es",
        ...     "canonical_language": "en",
        ...     "python_version": "3.13",
        ...     "created_at": "2025-11-06T10:00:00Z",
        ...     "updated_at": "2025-11-06T10:30:00Z",
        ...     "translations": [
        ...         {
        ...             "language": "en",
        ...             "method": "token_transformer",
        ...             "timestamp": "2025-11-06T10:30:00Z",
        ...             "commit_sha": "a91228a",
        ...             "translator_version": "0.1.0",
        ...             "python_version": "3.13"
        ...         }
        ...     ],
        ...     "history": [
        ...         {
        ...             "action": "clean",
        ...             "from_language": "es",
        ...             "to_language": "en",
        ...             "timestamp": "2025-11-06T10:30:00Z",
        ...             "commit_sha": "a91228a"
        ...         }
        ...     ]
        ... }
    """

    file: str
    original_language: str
    canonical_language: str
    python_version: str
    created_at: str
    updated_at: str
    translations: list[TranslationRecord]
    history: list[HistoryEntry]


@runtime_checkable
class Translator(Protocol):
    """Protocol defining the translator interface.

    This protocol allows type checking for any class that implements
    the translator interface, supporting dependency injection and testing.

    All translator implementations (TokenTranslator, TreeSitterTranslator, etc.)
    must implement these methods to ensure polymorphic usage.

    Example:
        >>> def process_code(translator: Translator, code: str) -> str:
        ...     return translator.translate_code(code, "en", "es")

        >>> # Both translators implement this protocol
        >>> from legesher_core import TokenTranslator, create_translator
        >>> translator = create_translator("python", keyword_map, builtin_map)
        >>> result = translator.translate_code(code, "en", "es")
    """

    def translate_code(
        self,
        source_code: str,
        source_lang: str = "en",
        target_lang: str = "es",
        return_metadata: bool = False,
    ) -> Union[str, tuple[str, "CulturalCommentMetadata"]]:
        """Translate Python source code from one language to another.

        Args:
            source_code: Python source code to translate
            source_lang: Source language code (default: "en")
            target_lang: Target language code (default: "es")
            return_metadata: If True, return tuple of (translated_code, metadata)

        Returns:
            If return_metadata is False: Translated Python source code
            If return_metadata is True: Tuple of (translated_code, cultural_comment_metadata)

        Raises:
            TranslationError: If translation fails
            InvalidCodeError: If source code is invalid
        """
        ...

    def translate_file(self, file_path: Path, target_lang: str) -> str:
        """Translate a Python file to the target language.

        Args:
            file_path: Path to Python file to translate
            target_lang: Target language code (e.g., "es", "ar")

        Returns:
            Translated Python source code

        Raises:
            FileNotFoundError: If file doesn't exist
            TranslationError: If translation fails
        """
        ...

    def reverse(self) -> "Translator":
        """Create a reverse translator (swaps source and target languages).

        Returns:
            New Translator instance with reversed language mapping

        Example:
            >>> es_to_en = translator.reverse()
            >>> english_code = es_to_en.translate_code(spanish_code, "es", "en")
        """
        ...

    @classmethod
    def from_language_pack(
        cls, language: str, python_version: Optional[str] = None
    ) -> "Translator":
        """Create translator from a language pack.

        Args:
            language: Natural language code (e.g., "es", "ar", "zh")
            python_version: Python version for version-aware packs (e.g., "3.13")
                          If None, auto-detects from environment

        Returns:
            Translator instance configured for the language pack

        Raises:
            UnsupportedLanguageError: If language pack not found

        Example:
            >>> translator = TokenTranslator.from_language_pack("es", "3.13")
            >>> code = translator.translate_code("def hello(): pass", "en", "es")
        """
        ...

    @classmethod
    def list_available_languages(cls) -> list[tuple[str, str]]:
        """List all available language packs.

        Returns:
            List of tuples (language_code, language_name)
            Example: [("es", "Spanish"), ("ar", "Arabic"), ("zh", "Chinese")]
        """
        ...

    def get_pack_info(self) -> dict[str, Union[str, int]]:
        """Get information about the loaded language pack.

        Returns:
            Dictionary containing:
                - language: Natural language code (e.g., "es")
                - python_version: Python version (e.g., "3.13")
                - keyword_count: Number of keywords in pack
                - builtin_count: Number of builtins in pack

        Example:
            >>> info = translator.get_pack_info()
            >>> print(f"Language: {info['language']}, Keywords: {info['keyword_count']}")
        """
        ...


# Translatable element types for LLM-powered full translation
ElementKind = Literal["identifier", "comment", "docstring", "string"]
IdentifierRole = Literal[
    "function_name",
    "class_name",
    "parameter",
    "variable",
    "attribute",
    "module",
    "decorator_arg",
    "other",
]


@dataclass(frozen=True)
class TranslatableElement:
    """A single translatable element extracted from the AST.

    Represents an identifier, comment, docstring, or string literal
    that can be translated by an LLM backend.
    """

    kind: ElementKind
    text: str
    start_byte: int
    end_byte: int
    role: IdentifierRole
    context: dict[str, Any]
    # For strings/docstrings: quote style and prefix
    quote_style: Optional[str] = None  # "'", '"', '"""', "'''"
    prefix: Optional[str] = None  # "f", "r", "b", etc.


@dataclass
class TranslationScope:
    """Configuration for which element types to translate.

    Allows toggling translation of each category independently.
    Supports future partial translation modes (e.g., translate identifiers
    but annotate comments instead of replacing them).
    """

    translate_identifiers: bool = True
    translate_comments: bool = True
    translate_docstrings: bool = True
    translate_strings: bool = True


@runtime_checkable
class TextTranslationBackend(Protocol):
    """Protocol for LLM-based text translation backends.

    Defines a synchronous interface for translating text using LLM models.
    Core defines this protocol; concrete implementations live in libs/i18n/
    (e.g., Anthropic, Cohere Aya, OpenAI-compatible local models).

    Implementations should handle async LLM calls internally
    (e.g., via asyncio.run()) to satisfy this sync interface.

    Example:
        >>> class MockBackend:
        ...     def translate_text(self, text, source_lang, target_lang, context=None):
        ...         return f"translated_{text}"
        ...     def translate_batch(self, items, source_lang, target_lang):
        ...         return [f"translated_{item['text']}" for item in items]
        >>> backend = MockBackend()
        >>> isinstance(backend, TextTranslationBackend)
        True
    """

    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Translate a single piece of text.

        Args:
            text: The text to translate (identifier, comment, string, etc.)
            source_lang: Source language code (e.g., "en")
            target_lang: Target language code (e.g., "es", "zh", "ur")
            context: Optional translation context with keys like:
                - role: Identifier role (function_name, parameter, etc.)
                - surrounding_code: Code snippet for semantic context
                - naming_convention: snake_case, PascalCase, etc.
                - type_hint: Type annotation if available
                - docstring: Related docstring if available
                - glossary: Dict of already-translated identifiers

        Returns:
            Translated text string
        """
        ...

    def translate_batch(
        self,
        items: list[dict[str, Any]],
        source_lang: str,
        target_lang: str,
    ) -> list[str]:
        """Translate a batch of items for efficiency.

        Each item is a dict with at least a "text" key and optional "context" key.

        Args:
            items: List of dicts, each with:
                - text (str): The text to translate
                - context (dict, optional): Translation context (see translate_text)
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            List of translated strings in the same order as input items
        """
        ...
