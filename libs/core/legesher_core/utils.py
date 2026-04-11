"""Utility functions for Legesher Core translation engine.

This module provides helper functions for encoding detection, validation,
and other common operations used throughout the translation pipeline.
"""

import ast
from pathlib import Path


def validate_utf8_encoding(file_path: Path) -> str:
    """Validate that a Python source file is UTF-8 encoded.

    Note: This function validates UTF-8 encoding rather than detecting
    arbitrary encodings, as Legesher mandates UTF-8 for all files to
    properly handle multilingual code, especially RTL languages like Arabic.

    Args:
        file_path: Path to the Python source file

    Returns:
        Encoding string ('utf-8') if validation succeeds

    Raises:
        EncodingError: If file is not UTF-8 encoded

    Example:
        >>> encoding = validate_utf8_encoding(Path("my_code.py"))
        >>> assert encoding == "utf-8"
    """
    from .exceptions import EncodingError

    try:
        # Try to read file as UTF-8
        with open(file_path, encoding="utf-8") as f:
            f.read()
        return "utf-8"
    except UnicodeDecodeError as e:
        raise EncodingError(
            f"File '{file_path}' must be UTF-8 encoded. Detected encoding error: {e}"
        ) from e


# Backwards compatibility alias
detect_encoding = validate_utf8_encoding


def validate_python_code(code: str) -> bool:
    """Check if code is syntactically valid Python.

    Uses Python's AST parser to validate syntax without executing code.
    Note: This validates complete syntax, but incomplete code (like a user
    typing in real-time) may fail validation even though tokenization can
    handle it gracefully.

    Args:
        code: Python source code string

    Returns:
        True if code is syntactically valid, False otherwise

    Example:
        >>> validate_python_code("def foo(): return 42")
        True
        >>> validate_python_code("def foo)(:")
        False
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def normalize_newlines(code: str) -> str:
    """Normalize line endings to Unix-style (\\n).

    Converts Windows (\\r\\n) and old Mac (\\r) line endings to Unix (\\n)
    for consistent processing across platforms.

    Args:
        code: Source code with potentially mixed line endings

    Returns:
        Source code with normalized \\n line endings

    Example:
        >>> normalize_newlines("line1\\r\\nline2\\rline3\\n")
        'line1\\nline2\\nline3\\n'
    """
    # Replace Windows CRLF with LF
    code = code.replace("\r\n", "\n")
    # Replace old Mac CR with LF
    code = code.replace("\r", "\n")
    return code


def is_rtl_language(lang_code: str) -> bool:
    """Check if a language is right-to-left (RTL).

    RTL languages require special handling for Unicode preservation,
    though the actual visual rendering is the IDE's responsibility.

    Args:
        lang_code: ISO 639-1 or custom language code (e.g., "ar", "he")

    Returns:
        True if language is RTL, False otherwise

    Example:
        >>> is_rtl_language("ar")  # Arabic
        True
        >>> is_rtl_language("he")  # Hebrew
        True
        >>> is_rtl_language("en")  # English
        False
        >>> is_rtl_language("es")  # Spanish
        False
    """
    # Common RTL language codes
    RTL_LANGUAGES = {
        "ar",  # Arabic
        "he",  # Hebrew
        "ur",  # Urdu
        "fa",  # Persian/Farsi
        "yi",  # Yiddish
        "ji",  # Yiddish (alternate code)
    }

    return lang_code.lower() in RTL_LANGUAGES


def merge_exception_translations(
    builtin_map: dict[str, str],
    exceptions: dict[str, str],
) -> dict[str, str]:
    """Merge exception translations into a builtin map with PascalCase keys.

    Language packs store exception keys lowercase (``valueerror``) but Python
    uses PascalCase (``ValueError``).  This function remaps using Python's
    actual builtin exception names.

    Args:
        builtin_map: Existing builtin translations (will not be mutated).
        exceptions: Exception translations from the language pack (lowercase keys).

    Returns:
        New dict with builtins + exceptions merged.
    """
    import builtins as _builtins

    merged = dict(builtin_map)

    # Build lowercase → PascalCase lookup from Python's actual exception names
    pascal_map = {}
    for name in dir(_builtins):
        obj = getattr(_builtins, name, None)
        if isinstance(obj, type) and issubclass(obj, BaseException):
            pascal_map[name.lower()] = name

    for lower_name, translation in exceptions.items():
        canonical = pascal_map.get(lower_name, lower_name)
        merged[canonical] = translation

    return merged
