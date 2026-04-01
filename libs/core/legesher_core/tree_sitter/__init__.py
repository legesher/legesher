"""Tree-sitter integration for Legesher.

This module provides tree-sitter-based parsing and translation for Python code.
Tree-sitter offers performance benefits and incremental parsing capabilities
for real-time IDE integration.

Components:
    - PythonParser: Tree-sitter wrapper for parsing Python code
    - TreeSitterTranslator: Tree-sitter-based code translator (≥2x faster than token-based)
    - TreeSitterError: Exception for tree-sitter operations

See: https://tree-sitter.github.io/tree-sitter/
"""

from .extractor import TranslatableExtractor
from .identifier_map import IdentifierMap
from .identifier_validator import IdentifierValidator
from .llm_translator import LLMTranslator
from .parser import PythonParser, TreeSitterError
from .translation_logger import TranslationLogger
from .translator import TreeSitterTranslator

__all__ = [
    "IdentifierMap",
    "IdentifierValidator",
    "LLMTranslator",
    "PythonParser",
    "TranslatableExtractor",
    "TranslationLogger",
    "TreeSitterError",
    "TreeSitterTranslator",
]
