"""Legesher Core - Token-based translation engine for multilingual Python.

This package provides the core translation functionality for Legesher,
enabling developers to write Python code in their native language.

Public API:
    - TokenTranslator: Main translation engine
    - TokenMapper: Language map abstraction
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
"""

from .exceptions import (
    EncodingError,
    InvalidCodeError,
    TranslationError,
    UnsupportedLanguageError,
)
from .token_mapper import TokenMapper
from .transformer import TokenTranslator

__version__ = "0.0.1"

__all__ = [
    "TokenTranslator",
    "TokenMapper",
    "TranslationError",
    "InvalidCodeError",
    "UnsupportedLanguageError",
    "EncodingError",
]
