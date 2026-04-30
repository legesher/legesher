"""Term classification for Python programming terms.

BACKWARDS COMPATIBILITY MODULE
==============================
This module re-exports from legesher_i18n.term_definitions for backwards compatibility.

The source of truth for all Python term definitions is now:
    legesher_i18n/term_definitions.py

This file can be imported directly from scripts that need term classification,
but all definitions are maintained in the main package.

Usage (both work):
    # Direct import (preferred for new code)
    from legesher_i18n.term_definitions import classify_term, KEYWORDS_BASE

    # Legacy import (still works)
    from scripts.translate.term_classifier import classify_term, KEYWORDS_BASE
"""

# Re-export everything from the canonical source
from legesher_i18n.term_definitions import (  # noqa: F401
    # Term lists
    KEYWORDS_BASE,
    KEYWORDS_3_10,
    KEYWORDS_3_11,
    KEYWORDS_3_12,
    SPECIAL_VALUES,
    BUILTIN_FUNCTIONS,
    BUILTIN_TYPES,
    EXCEPTIONS,
    EXCEPTIONS_3_11,
    SPECIAL_CONSTANTS,
    RESERVED_WORDS,
    HELPER_TERMS,
    # Type system
    TermCategory,
    TERM_TYPE_YAML_SECTIONS,
    # Functions
    get_keywords_for_version,
    get_builtins_for_version,
    get_exceptions_for_version,
    get_reserved_words_for_version,
    classify_term,
    get_all_terms_by_category,
    is_python_term,
    get_yaml_section_for_term_type,
    is_valid_term_type,
)

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
    "RESERVED_WORDS",
    "HELPER_TERMS",
    # Type system
    "TermCategory",
    "TERM_TYPE_YAML_SECTIONS",
    # Functions
    "get_keywords_for_version",
    "get_builtins_for_version",
    "get_exceptions_for_version",
    "get_reserved_words_for_version",
    "classify_term",
    "get_all_terms_by_category",
    "is_python_term",
    "get_yaml_section_for_term_type",
    "is_valid_term_type",
]
