"""Legesher Core - Translation engine for multilingual Python.

This package provides the core translation functionality for Legesher,
enabling developers to write Python code in their native language.

Public API:
    Translation Engine:
        - TokenTranslator: Token-based translation engine (simple, stable)
        - TreeSitterTranslator: Tree-sitter translation engine (4x faster, AST-based)
        - TokenMapper: Language map abstraction

    Language Abstraction Interface (CORE-415):
        - Translator: Protocol defining translator interface
        - create_translator: Factory function for creating translators
        - create_translator_from_language_pack: Convenience factory for language packs
        - get_default_backend: Query default backend from environment
        - get_supported_languages: List supported programming languages
        - TranslatorBackend: Type alias for backend selection

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

    >>> # Using factory function (CORE-415)
    >>> from legesher_core import create_translator
    >>> translator = create_translator("python", spanish_keywords, spanish_builtins)
    >>> # Or use environment variable: export LEGESHER_USE_TREE_SITTER=true
    >>> translator = create_translator("python", spanish_keywords, spanish_builtins)

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

from .ai_context import (
    AIContextGenerator,
    generate_bilingual_examples,
    generate_builtin_table,
    generate_exception_table,
    generate_keyword_table,
)
from .cultural_comments import CulturalCommentParser
from .exceptions import (
    EncodingError,
    InvalidCodeError,
    TranslationError,
    UnsupportedLanguageError,
)
from .ide_support import CulturalCommentProvider
from .language_interface import (
    TranslatorBackend,
    TranslatorConfig,
    create_translator,
    create_translator_from_config,
    create_translator_from_language_pack,
    get_default_backend,
    get_supported_languages,
)
from .metadata import MetadataManager
from .token_mapper import TokenMapper
from .transformer import TokenTranslator
from .translation_tracker import TranslationTracker
from .tree_sitter.translator import TreeSitterTranslator
from .types import CulturalComment, CulturalCommentMetadata, Translator

__version__ = "0.7.0"

__all__ = [
    # Translation engine
    "TokenTranslator",
    "TreeSitterTranslator",
    "TokenMapper",
    # Language abstraction interface (CORE-415)
    "Translator",
    "TranslatorBackend",
    "TranslatorConfig",
    "create_translator",
    "create_translator_from_config",
    "create_translator_from_language_pack",
    "get_default_backend",
    "get_supported_languages",
    # AI context generation
    "AIContextGenerator",
    "generate_keyword_table",
    "generate_builtin_table",
    "generate_exception_table",
    "generate_bilingual_examples",
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
