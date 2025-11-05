"""Tree-sitter integration for Legesher.

This module provides tree-sitter-based parsing for Python code translation.
Tree-sitter offers performance benefits and incremental parsing capabilities
for real-time IDE integration.

See: https://tree-sitter.github.io/tree-sitter/
"""

from .parser import PythonParser, TreeSitterError

__all__ = [
    "PythonParser",
    "TreeSitterError",
]
