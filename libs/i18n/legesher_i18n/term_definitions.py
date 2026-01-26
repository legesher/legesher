"""Python term definitions - single source of truth for all Python terms.

This module is the canonical source for:
- All Python keywords (base + version-specific)
- All built-in functions
- All built-in types
- All exceptions
- All special constants

The version_index.py module imports these base terms and applies version deltas
from version-index.yml to provide complete term sets for any Python version.

Term type to YAML section mapping is also defined here for consistency across
the translation pipeline.
"""

from typing import Literal

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

# All Python Built-in Exceptions (Python 3.13)
# Organized by hierarchy for clarity
# See: https://docs.python.org/3/library/exceptions.html
EXCEPTIONS = [
    # Base exception classes
    "baseexception",
    "basegeneratorexit",  # 3.12+ internal
    "exception",
    "generatorexit",
    # System-related exceptions
    "systemexit",
    "keyboardinterrupt",
    # Arithmetic exceptions
    "arithmeticerror",
    "floatingpointerror",
    "overflowerror",
    "zerodivisionerror",
    # Lookup exceptions
    "lookuperror",
    "indexerror",
    "keyerror",
    # Name/Attribute exceptions
    "attributeerror",
    "nameerror",
    "unboundlocalerror",
    # OS/IO exceptions
    "oserror",
    "blockingioerror",
    "childprocesserror",
    "connectionerror",
    "brokenpipeerror",
    "connectionabortederror",
    "connectionrefusederror",
    "connectionreseterror",
    "fileexistserror",
    "filenotfounderror",
    "interruptederror",
    "isadirectoryerror",
    "notadirectoryerror",
    "permissionerror",
    "processlookuperror",
    "timeouterror",
    # Import exceptions
    "importerror",
    "modulenotfounderror",
    # Iteration exceptions
    "stopiteration",
    "stopasynciteration",
    # Type/Value exceptions
    "typeerror",
    "valueerror",
    "unicodeerror",
    "unicodedecodeerror",
    "unicodeencodeerror",
    "unicodetranslateerror",
    # Runtime exceptions
    "runtimeerror",
    "notimplementederror",
    "recursionerror",
    # Reference exceptions
    "referenceerror",
    # Assertion exceptions
    "assertionerror",
    # Memory exceptions
    "memoryerror",
    # Buffer exceptions
    "buffererror",
    # EOF exceptions
    "eoferror",
    # Syntax exceptions
    "syntaxerror",
    "indentationerror",
    "taberror",
    # Environment exceptions
    "environmenterror",  # Alias for OSError
    "ioerror",  # Alias for OSError
    # Warning classes (also exceptions)
    "warning",
    "userwarning",
    "deprecationwarning",
    "pendingdeprecationwarning",
    "syntaxwarning",
    "runtimewarning",
    "futurewarning",
    "importwarning",
    "unicodewarning",
    "byteswarning",
    "encodingwarning",
    "resourcewarning",
    # Exception groups (Python 3.11+)
    "exceptiongroup",
    "baseexceptiongroup",
]

# Exceptions added in specific Python versions
EXCEPTIONS_3_11 = [
    "exceptiongroup",
    "baseexceptiongroup",
    "encodingwarning",
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

# Mapping: term_type -> YAML section name
# This is the SINGLE SOURCE OF TRUTH for how term types map to YAML sections.
TERM_TYPE_YAML_SECTIONS: dict[str, str | None] = {
    "keyword": "keywords",
    "builtin_func": "builtins",
    "builtin_type": "builtins",
    "exception": "exceptions",
    "special_constant": "builtins",
    "helper": None,  # Excluded from YAML export
    "unknown": None,  # Excluded from YAML export
    # Future term types (not yet implemented):
    # "dunder_method": "dunder_methods",  # Magic methods: __init__, __str__, __add__, etc.
    # "numeric_literal": "numeric_literals",  # Number prefixes: 0x (hex), 0b (binary), 0o (octal)
    # "string_prefix": "string_prefixes",  # String prefixes: f, r, b, fr, etc.
    # "decorator": "decorators",  # Common decorators: @property, @staticmethod, @classmethod
    # "protocol": "protocols",  # Protocol/ABC methods: __iter__, __next__, __enter__, __exit__
}


def get_keywords_for_version(version: str = "3.10") -> list[str]:
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


def get_builtins_for_version(version: str = "3.10") -> list[str]:
    """Get all builtins applicable to a specific Python version.

    Args:
        version: Python version string (e.g., '3.10', '3.11', '3.12', '3.13')

    Returns:
        List of builtin strings for that version
    """
    # All builtins are available in 3.10+
    # aiter/anext were added in 3.10 but are in our base list
    return BUILTIN_FUNCTIONS.copy() + BUILTIN_TYPES.copy() + SPECIAL_CONSTANTS.copy()


def get_exceptions_for_version(version: str = "3.10") -> list[str]:
    """Get all exceptions applicable to a specific Python version.

    Args:
        version: Python version string (e.g., '3.10', '3.11', '3.12', '3.13')

    Returns:
        List of exception strings for that version
    """
    exceptions = EXCEPTIONS.copy()

    # 3.11+ has exceptiongroup, baseexceptiongroup, encodingwarning
    # These are already in our base list for simplicity
    return exceptions


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
) -> dict[TermCategory, list[str]]:
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


def get_yaml_section_for_term_type(term_type: str) -> str | None:
    """Get the YAML section name for a given term type.

    This is the canonical way to map term_type values to YAML sections.
    Used by yaml_exporter to determine which section a term belongs to.

    Args:
        term_type: The term type (e.g., 'keyword', 'builtin_func', 'exception')

    Returns:
        The YAML section name (e.g., 'keywords', 'builtins', 'exceptions'),
        or None if the term type should be excluded from YAML export.
    """
    return TERM_TYPE_YAML_SECTIONS.get(term_type)


def is_valid_term_type(term_type: str) -> bool:
    """Check if a term_type value is valid (known to the system).

    Used for validation and fallback logic in yaml_exporter.

    Args:
        term_type: The term type to validate

    Returns:
        True if the term_type is in TERM_TYPE_YAML_SECTIONS
    """
    return term_type in TERM_TYPE_YAML_SECTIONS


# Export all for convenience
__all__ = [
    # Term lists
    "KEYWORDS_BASE",
    "KEYWORDS_3_10",
    "KEYWORDS_3_11",
    "KEYWORDS_3_12",
    "SPECIAL_VALUES",
    "BUILTIN_FUNCTIONS",
    "BUILTIN_TYPES",
    "EXCEPTIONS",
    "EXCEPTIONS_3_11",
    "SPECIAL_CONSTANTS",
    "HELPER_TERMS",
    # Type system
    "TermCategory",
    "TERM_TYPE_YAML_SECTIONS",
    # Functions
    "get_keywords_for_version",
    "get_builtins_for_version",
    "get_exceptions_for_version",
    "classify_term",
    "get_all_terms_by_category",
    "is_python_term",
    "get_yaml_section_for_term_type",
    "is_valid_term_type",
]
