"""Custom exceptions for Legesher Core translation engine.

This module defines exception hierarchy for translation errors,
enabling graceful error handling and clear error messages.
"""


class TranslationError(Exception):
    """Base exception for all translation-related errors.

    All custom exceptions in legesher-core inherit from this base class,
    making it easy to catch any translation-related error.
    """

    pass


class InvalidCodeError(TranslationError):
    """Raised when source code is invalid or unparseable.

    This exception is raised when the Python tokenizer cannot parse
    the provided source code, typically due to syntax errors.

    Example:
        >>> translator.translate_code("def foo)(:", "en", "es")
        InvalidCodeError: Cannot parse invalid Python syntax
    """

    pass


class UnsupportedLanguageError(TranslationError):
    """Raised when a language is not supported or has no translation map.

    This exception is raised when attempting to translate to/from
    a language that doesn't have a registered translation map.

    Example:
        >>> translator.translate_code(code, "en", "unsupported")
        UnsupportedLanguageError: Language 'unsupported' not supported
    """

    pass


class EncodingError(TranslationError):
    """Raised when file encoding is not UTF-8 or cannot be decoded.

    Legesher requires all source files to be UTF-8 encoded to properly
    handle multilingual code, especially RTL languages like Arabic.

    Example:
        >>> translator.translate_file(Path("latin1_file.py"), "es")
        EncodingError: File must be UTF-8 encoded, found: latin-1
    """

    pass
