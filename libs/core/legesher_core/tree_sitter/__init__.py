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

from .parser import PythonParser, TreeSitterError
from .translator import TreeSitterTranslator

__all__ = [
    "PythonParser",
    "TreeSitterError",
    "TreeSitterTranslator",
]
