"""Legesher Core - Token-based translation engine for multilingual Python.

This package provides the core translation functionality for Legesher,
enabling developers to write Python code in their native language.

Public API:
    Translation Engine:
        - TokenTranslator: Main translation engine
        - TokenMapper: Language map abstraction

    Cultural Comments (MLCP Protocol):
        - CulturalComment: Immutable cultural comment metadata
        - CulturalCommentMetadata: Container for all cultural comments
        - CulturalCommentParser: Parser for extracting cultural comments
        - CulturalCommentProvider: High-level IDE integration API

    Git Integration & Metadata Tracking:
        - TranslationTracker: High-level API for tracking translations
        - MetadataManager: Low-level metadata persistence (internal)

    Exceptions:
        - TranslationError: Base exception class
        - InvalidCodeError: Raised for unparseable code
        - UnsupportedLanguageError: Raised for unsupported languages
        - EncodingError: Raised for non-UTF-8 files

Example:
    >>> from legesher_core import TokenTranslator
    >>> spanish_keywords = {"def": "definir", "return": "retornar"}
    >>> spanish_builtins = {"print": "imprimir"}
    >>> translator = TokenTranslator(spanish_keywords, spanish_builtins)
    >>> code = "def greet():\\n    print('Hello')"
    >>> spanish_code = translator.translate_code(code, "en", "es")

    >>> # With cultural comments
    >>> code_with_cultural = '''
    ... #@culture[es]: "hola" is informal, "buenos días" is formal
    ... def greet(): print("hola")
    ... '''
    >>> translated, metadata = translator.translate_code(
    ...     code_with_cultural, "en", "es", return_metadata=True
    ... )
    >>> metadata.has_comments()
    True

    >>> # Track translations
    >>> from pathlib import Path
    >>> from legesher_core import TranslationTracker, MetadataManager
    >>> manager = MetadataManager(Path(".legesher/metadata"))
    >>> tracker = TranslationTracker(manager)
    >>> tracker.track_clean(Path("src/main.py"), "es", "en")
"""

from .cultural_comments import CulturalCommentParser
from .exceptions import (
    EncodingError,
    InvalidCodeError,
    TranslationError,
    UnsupportedLanguageError,
)
from .ide_support import CulturalCommentProvider
from .metadata import MetadataManager
from .token_mapper import TokenMapper
from .transformer import TokenTranslator
from .translation_tracker import TranslationTracker
from .types import CulturalComment, CulturalCommentMetadata

__version__ = "0.0.1"

__all__ = [
    # Translation engine
    "TokenTranslator",
    "TokenMapper",
    # Cultural comments (MLCP)
    "CulturalComment",
    "CulturalCommentMetadata",
    "CulturalCommentParser",
    "CulturalCommentProvider",
    # Git integration & metadata
    "TranslationTracker",
    "MetadataManager",
    # Exceptions
    "TranslationError",
    "InvalidCodeError",
    "UnsupportedLanguageError",
    "EncodingError",
]
