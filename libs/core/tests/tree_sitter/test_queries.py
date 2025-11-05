"""Test pre-defined query patterns."""

from legesher_core.tree_sitter import PythonParser
from legesher_core.tree_sitter import queries
from tree_sitter import QueryCursor


class TestQueryPatterns:
    """Test that pre-defined query patterns work correctly."""

    def test_function_definitions_query(self):
        """Test FUNCTION_DEFINITIONS query pattern."""
        parser = PythonParser()
        query = parser.query(queries.FUNCTION_DEFINITIONS)

        code = """
def foo():
    pass

def bar(x, y):
    return x + y
"""
        tree = parser.parse(code)
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        assert len(matches) == 2  # Two functions

    def test_class_definitions_query(self):
        """Test CLASS_DEFINITIONS query pattern."""
        parser = PythonParser()
        query = parser.query(queries.CLASS_DEFINITIONS)

        code = """
class Foo:
    pass

class Bar:
    def __init__(self):
        pass
"""
        tree = parser.parse(code)
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        assert len(matches) == 2  # Two classes

    def test_keywords_query(self):
        """Test KEYWORDS_QUERY pattern."""
        # Test that the query string is accessible
        assert queries.KEYWORDS_QUERY is not None
        assert "def" in queries.KEYWORDS_QUERY
        assert "class" in queries.KEYWORDS_QUERY
        assert "return" in queries.KEYWORDS_QUERY

        # The actual keyword matching will be used in CORE-414
        # For now, just verify the query string is valid
        assert len(queries.KEYWORDS_QUERY) > 0

    def test_import_statements_query(self):
        """Test IMPORT_STATEMENTS query pattern."""
        parser = PythonParser()
        query = parser.query(queries.IMPORT_STATEMENTS)

        code = """
import os
from pathlib import Path
import sys
"""
        tree = parser.parse(code)
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        assert len(matches) == 3  # Three import statements

    def test_control_flow_query(self):
        """Test CONTROL_FLOW query pattern."""
        parser = PythonParser()
        query = parser.query(queries.CONTROL_FLOW)

        code = """
if x > 0:
    pass

for i in range(10):
    pass

while True:
    break

try:
    risky()
except:
    pass

with open('f') as f:
    pass
"""
        tree = parser.parse(code)
        cursor = QueryCursor(query)
        matches = list(cursor.matches(tree.root_node))

        # Should find: if, for, while, try, with
        assert len(matches) == 5
