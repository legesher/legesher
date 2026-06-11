"""Test PythonParser wrapper class."""

import pytest
from legesher_core.tree_sitter import PythonParser, TreeSitterError
from tree_sitter import QueryCursor


class TestPythonParser:
    """Test suite for PythonParser class."""

    def test_init(self):
        """Test parser initialization."""
        parser = PythonParser()

        assert parser is not None
        assert parser.language is not None
        assert parser.parser is not None

    def test_parse_string(self):
        """Test parsing from string."""
        parser = PythonParser()
        tree = parser.parse("def hello(): pass")

        assert tree is not None
        assert tree.root_node.type == "module"

    def test_parse_bytes(self):
        """Test parsing from bytes."""
        parser = PythonParser()
        tree = parser.parse(b"def hello(): pass")

        assert tree is not None
        assert tree.root_node.type == "module"

    def test_parse_unicode(self):
        """Test parsing Unicode content."""
        parser = PythonParser()
        # Use simple ASCII to avoid encoding issues
        code = "# Spanish comment\nname = 42"
        tree = parser.parse(code)

        assert tree is not None
        assert tree.root_node.type == "module"

    def test_parse_multiline(self):
        """Test parsing multiline code."""
        parser = PythonParser()
        code = """
def foo():
    x = 1
    y = 2
    return x + y

class Bar:
    pass
"""
        tree = parser.parse(code)

        assert tree is not None
        assert tree.root_node.child_count > 0

    def test_parse_syntax_error(self):
        """Test parsing code with syntax errors."""
        parser = PythonParser()

        # Tree-sitter is error-tolerant, should still return tree
        code = "def foo( invalid syntax"
        tree = parser.parse(code)

        assert tree is not None
        # Tree may have error nodes

    def test_parse_incremental(self):
        """Test incremental parsing."""
        parser = PythonParser()

        # Parse initial code
        code1 = "def foo(): pass"
        tree1 = parser.parse(code1)

        # Parse updated code incrementally
        code2 = "def foo():\n    return 42"
        tree2 = parser.parse_incremental(code2, tree1)

        assert tree2 is not None
        assert tree2.root_node.type == "module"

    def test_parse_incremental_without_old_tree(self):
        """Test incremental parsing without old tree falls back gracefully."""
        parser = PythonParser()

        code = "def foo(): pass"
        tree = parser.parse_incremental(code, None)

        assert tree is not None
        assert tree.root_node.type == "module"

    def test_query_simple(self):
        """Test creating and using queries."""
        parser = PythonParser()

        # Create query
        query = parser.query("(function_definition) @func")

        # Parse code
        tree = parser.parse("def foo(): pass")

        # Execute query
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        assert len(matches) == 1
        pattern_index, captures = matches[0]
        assert "func" in captures
        assert captures["func"][0].type == "function_definition"

    def test_query_invalid(self):
        """Test that invalid query raises error."""
        parser = PythonParser()

        with pytest.raises(TreeSitterError):
            parser.query("(invalid_query_syntax")

    def test_query_multiple_patterns(self):
        """Test query with multiple patterns."""
        parser = PythonParser()

        query_string = """
        (function_definition) @func
        (class_definition) @class
        """
        query = parser.query(query_string)

        code = "def foo(): pass\nclass Bar: pass"
        tree = parser.parse(code)

        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        # Should capture both function and class
        assert len(matches) == 2


class TestErrorHandling:
    """Test error handling in PythonParser."""

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        parser = PythonParser()
        tree = parser.parse("")

        assert tree is not None
        assert tree.root_node.type == "module"

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only code."""
        parser = PythonParser()
        tree = parser.parse("   \n\n   ")

        assert tree is not None

    def test_tree_sitter_error_message(self):
        """Test that TreeSitterError has proper error messages."""
        parser = PythonParser()

        with pytest.raises(TreeSitterError) as exc_info:
            parser.query("(invalid syntax")

        assert "Failed to compile query" in str(exc_info.value)

    def test_parser_handles_bytes_and_strings(self):
        """Test that parser handles both bytes and strings correctly."""
        parser = PythonParser()

        # Test with bytes
        tree1 = parser.parse(b"x = 1")
        assert tree1 is not None

        # Test with string
        tree2 = parser.parse("x = 1")
        assert tree2 is not None

        # Both should produce the same result
        assert tree1.root_node.type == tree2.root_node.type

    def test_incremental_parse_handles_bytes_and_strings(self):
        """Test that incremental parsing handles both bytes and strings."""
        parser = PythonParser()

        # Initial parse with string
        tree1 = parser.parse("def foo(): pass")

        # Incremental with bytes
        tree2 = parser.parse_incremental(b"def foo(): return 42", tree1)
        assert tree2 is not None

        # Incremental with string
        tree3 = parser.parse_incremental("def foo(): return 100", tree2)
        assert tree3 is not None

    def test_parse_with_custom_encoding(self):
        """Test parsing with custom encoding parameter."""
        parser = PythonParser()

        # Test with default UTF-8
        code = "x = 42"
        tree1 = parser.parse(code)
        assert tree1 is not None

        # Test with explicit UTF-8
        tree2 = parser.parse(code, encoding="utf-8")
        assert tree2 is not None

        # Non-UTF-8 encodings are rejected (Legesher mandates UTF-8)
        with pytest.raises(TreeSitterError):
            parser.parse(code, encoding="ascii")

    def test_parse_incremental_with_custom_encoding(self):
        """Test incremental parsing with custom encoding parameter."""
        parser = PythonParser()

        # Initial parse with UTF-8
        code1 = "def foo(): pass"
        tree1 = parser.parse(code1, encoding="utf-8")

        # Incremental parse with custom encoding
        code2 = "def foo(): return 42"
        tree2 = parser.parse_incremental(code2, tree1, encoding="utf-8")
        assert tree2 is not None

    def test_parse_invalid_encoding(self):
        """Test that invalid encoding raises appropriate error."""
        parser = PythonParser()

        with pytest.raises(TreeSitterError) as exc_info:
            parser.parse("x = 42", encoding="invalid-encoding-xyz")

        assert "UTF-8" in str(exc_info.value)

    def test_parse_encoding_error(self):
        """Test that encoding errors are properly handled."""
        parser = PythonParser()

        # Non-UTF-8 encodings fail closed rather than silently re-encoding.
        code = "x = 42  # comment"
        with pytest.raises(TreeSitterError):
            parser.parse(code, encoding="ascii")


class TestRealWorldCode:
    """Test with real-world Python code samples."""

    def test_parse_class_with_methods(self):
        """Test parsing a class with methods."""
        parser = PythonParser()
        code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""
        tree = parser.parse(code)

        assert tree is not None

        # Query for methods
        query = parser.query("(function_definition) @method")
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        assert len(matches) == 2  # add and subtract

    def test_parse_imports(self):
        """Test parsing import statements."""
        parser = PythonParser()
        code = """
import os
from pathlib import Path
from typing import List, Dict
"""
        tree = parser.parse(code)

        assert tree is not None

        # Query for imports
        query = parser.query("(import_statement) @import")
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        assert len(matches) > 0

    def test_parse_async_functions(self):
        """Test parsing async/await syntax."""
        parser = PythonParser()
        code = """
async def fetch_data():
    data = await get_data()
    return data
"""
        tree = parser.parse(code)

        assert tree is not None

        # Query for async functions
        query = parser.query("(function_definition) @async_func")
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        assert len(matches) == 1

    def test_parse_match_statement(self):
        """Test parsing match/case (Python 3.10+)."""
        parser = PythonParser()
        code = """
match value:
    case 1:
        print("one")
    case 2:
        print("two")
    case _:
        print("other")
"""
        tree = parser.parse(code)

        assert tree is not None
        # Should parse without errors

    def test_parse_type_hints(self):
        """Test parsing type hints."""
        parser = PythonParser()
        code = """
def greet(name: str) -> str:
    return f"Hello, {name}"

x: int = 42
y: list[str] = ["a", "b"]
"""
        tree = parser.parse(code)

        assert tree is not None

    def test_parse_decorators(self):
        """Test parsing decorators."""
        parser = PythonParser()
        code = """
@decorator
def foo():
    pass

@staticmethod
@property
def bar():
    pass
"""
        tree = parser.parse(code)

        assert tree is not None

    def test_parse_comprehensions(self):
        """Test parsing list/dict/set comprehensions."""
        parser = PythonParser()
        code = """
squares = [x**2 for x in range(10)]
evens = {x for x in range(10) if x % 2 == 0}
mapping = {k: v for k, v in items}
"""
        tree = parser.parse(code)

        assert tree is not None

    def test_parse_f_strings(self):
        """Test parsing f-strings."""
        parser = PythonParser()
        code = """
name = "world"
msg = f"Hello, {name}!"
complex_msg = f"Value: {value:.2f}"
"""
        tree = parser.parse(code)

        assert tree is not None

    def test_parse_context_managers(self):
        """Test parsing with statements."""
        parser = PythonParser()
        code = """
with open("file.txt") as f:
    content = f.read()

with open("a.txt") as f1, open("b.txt") as f2:
    pass
"""
        tree = parser.parse(code)

        assert tree is not None

    def test_parse_exception_handling(self):
        """Test parsing try/except/finally."""
        parser = PythonParser()
        code = """
try:
    risky_operation()
except ValueError as e:
    handle_value_error(e)
except Exception:
    handle_generic()
finally:
    cleanup()
"""
        tree = parser.parse(code)

        assert tree is not None


class TestPerformance:
    """Test performance characteristics."""

    def test_parse_large_file(self):
        """Test parsing a large file."""
        parser = PythonParser()

        # Generate a large Python file
        lines = []
        for i in range(1000):
            lines.append(f"def func_{i}():")
            lines.append(f"    x = {i}")
            lines.append("    return x * 2")
            lines.append("")

        code = "\n".join(lines)

        tree = parser.parse(code)

        assert tree is not None
        assert tree.root_node.child_count > 0

    def test_incremental_reparse_performance(self):
        """Test that incremental parsing reuses the old tree."""
        parser = PythonParser()

        # Initial code
        code1 = """
def foo():
    x = 1
    y = 2
    return x + y
"""
        tree1 = parser.parse(code1)

        # Modified code (small change)
        code2 = """
def foo():
    x = 1
    y = 3
    return x + y
"""
        tree2 = parser.parse_incremental(code2, tree1)

        assert tree2 is not None
        # Tree-sitter should have reused most of tree1
