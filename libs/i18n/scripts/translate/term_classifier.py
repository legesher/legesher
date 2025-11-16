"""Term classification for Python programming terms.

This module provides comprehensive classification of Python terms into categories:
- Keywords (version-aware)
- Built-in functions
- Built-in types
- Exceptions
- Special constants
- Helper/meta terms

Used by YAML exporter to properly structure language packs.
"""

from typing import List, Literal

# Python Keywords - Base (all Python 3.x versions)
KEYWORDS_BASE = [
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
]

# Python 3.10+ Keywords (PEP 634: Structural Pattern Matching)
KEYWORDS_3_10 = [
    "match",
    "case",
]

# Python 3.11+ Keywords (PEP 654: Exception Groups)
KEYWORDS_3_11 = [
    "except*",
]

# Python 3.12+ Keywords (PEP 695: Type Parameter Syntax)
KEYWORDS_3_12 = [
    "type",  # Note: 'type' is also a builtin, but becomes keyword in 3.12
]

# Special Values (also considered keywords in Python)
SPECIAL_VALUES = [
    "None",
    "True",
    "False",
]

# Built-in Functions
BUILTIN_FUNCTIONS = [
    "abs",
    "aiter",
    "all",
    "anext",
    "any",
    "ascii",
    "bin",
    "breakpoint",
    "callable",
    "chr",
    "compile",
    "delattr",
    "dir",
    "divmod",
    "enumerate",
    "eval",
    "exec",
    "filter",
    "format",
    "getattr",
    "globals",
    "hasattr",
    "hash",
    "help",
    "hex",
    "id",
    "input",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "locals",
    "map",
    "max",
    "min",
    "next",
    "oct",
    "open",
    "ord",
    "pow",
    "print",
    "range",
    "repr",
    "reversed",
    "round",
    "setattr",
    "slice",
    "sorted",
    "sum",
    "vars",
    "zip",
]

# Built-in Types (constructors)
BUILTIN_TYPES = [
    "bool",
    "bytearray",
    "bytes",
    "classmethod",
    "complex",
    "dict",
    "float",
    "frozenset",
    "int",
    "list",
    "memoryview",
    "object",
    "property",
    "set",
    "staticmethod",
    "str",
    "super",
    "tuple",
    # Note: 'type' moves to KEYWORDS_3_12 in Python 3.12+
]

# Common Exceptions
EXCEPTIONS = [
    "attributeerror",
    "baseexception",
    "exception",
    "indexerror",
    "keyerror",
    "nameerror",
    "runtimeerror",
    "stopiteration",
    "typeerror",
    "valueerror",
]

# Special Constants
SPECIAL_CONSTANTS = [
    "ellipsis",
    "notimplemented",
]

# Helper/Meta Terms (not part of Python, but useful for documentation/tooling)
HELPER_TERMS = [
    "README",
    "underscore",
]


TermCategory = Literal[
    "keyword",
    "builtin_func",
    "builtin_type",
    "exception",
    "special_constant",
    "helper",
    "unknown",
]


def get_keywords_for_version(version: str = "3.10") -> List[str]:
    """Get all keywords applicable to a specific Python version.

    Args:
        version: Python version string (e.g., '3.10', '3.11', '3.12', '3.13')

    Returns:
        List of keyword strings for that version
    """
    keywords = KEYWORDS_BASE.copy() + SPECIAL_VALUES.copy()

    # Add version-specific keywords
    if version >= "3.10":
        keywords.extend(KEYWORDS_3_10)

    if version >= "3.11":
        keywords.extend(KEYWORDS_3_11)

    if version >= "3.12":
        keywords.extend(KEYWORDS_3_12)

    return keywords


def classify_term(term: str, python_version: str = "3.10") -> TermCategory:
    """Classify a Python term into its category.

    Args:
        term: The term to classify (case-insensitive for most terms)
        python_version: Python version for keyword classification

    Returns:
        Category string: 'keyword', 'builtin_func', 'builtin_type',
                        'exception', 'special_constant', 'helper', or 'unknown'
    """
    term_lower = term.lower()

    # Check if it's a keyword (version-aware)
    all_keywords = get_keywords_for_version(python_version)
    if term in all_keywords or term_lower in [k.lower() for k in all_keywords]:
        return "keyword"

    # Check built-in functions
    if term_lower in [f.lower() for f in BUILTIN_FUNCTIONS]:
        return "builtin_func"

    # Check built-in types
    if term_lower in [t.lower() for t in BUILTIN_TYPES]:
        return "builtin_type"

    # Check exceptions
    if term_lower in EXCEPTIONS:
        return "exception"

    # Check special constants
    if term_lower in SPECIAL_CONSTANTS:
        return "special_constant"

    # Check helper terms
    if term in HELPER_TERMS or term_lower in [h.lower() for h in HELPER_TERMS]:
        return "helper"

    # Unknown term
    return "unknown"


def get_all_terms_by_category(
    python_version: str = "3.10",
) -> dict[TermCategory, List[str]]:
    """Get all terms organized by category.

    Args:
        python_version: Python version for keyword classification

    Returns:
        Dictionary mapping category -> list of terms
    """
    return {
        "keyword": get_keywords_for_version(python_version),
        "builtin_func": BUILTIN_FUNCTIONS.copy(),
        "builtin_type": BUILTIN_TYPES.copy(),
        "exception": EXCEPTIONS.copy(),
        "special_constant": SPECIAL_CONSTANTS.copy(),
        "helper": HELPER_TERMS.copy(),
    }


def is_python_term(term: str, python_version: str = "3.10") -> bool:
    """Check if a term is a valid Python term (excludes helper terms).

    Args:
        term: The term to check
        python_version: Python version for keyword classification

    Returns:
        True if term is a Python keyword, builtin, exception, or special constant
    """
    category = classify_term(term, python_version)
    return category not in ("helper", "unknown")


# Export all for convenience
__all__ = [
    "KEYWORDS_BASE",
    "KEYWORDS_3_10",
    "KEYWORDS_3_11",
    "KEYWORDS_3_12",
    "SPECIAL_VALUES",
    "BUILTIN_FUNCTIONS",
    "BUILTIN_TYPES",
    "EXCEPTIONS",
    "SPECIAL_CONSTANTS",
    "HELPER_TERMS",
    "TermCategory",
    "get_keywords_for_version",
    "classify_term",
    "get_all_terms_by_category",
    "is_python_term",
]
