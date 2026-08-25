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


class UnicodeGuardError(TranslationError):
    """Raised when a codepoint fails the engine's Unicode defense.

    The fail-closed counterpart to :func:`legesher_core.unicode_guard.scan_text`,
    which reports findings instead of raising. Carries the first offending
    codepoint and its character offset so an editor can point at it. Named to
    match ``UnicodeGuardError`` in ``@legesher/core`` so the two engines report
    the same class of refusal under the same name.

    Example:
        >>> assert_identifier_safe("to\\u2d7ftal")
        UnicodeGuardError: disallowed codepoint U+2D7F at offset 2
    """

    def __init__(self, message: str, *, codepoint: str = "", offset: int = -1) -> None:
        super().__init__(message)
        self.codepoint = codepoint
        self.offset = offset


class EncodingError(TranslationError):
    """Raised when file encoding is not UTF-8 or cannot be decoded.

    Legesher requires all source files to be UTF-8 encoded to properly
    handle multilingual code, especially RTL languages like Arabic.

    Example:
        >>> translator.translate_file(Path("latin1_file.py"), "es")
        EncodingError: File must be UTF-8 encoded, found: latin-1
    """

    pass
