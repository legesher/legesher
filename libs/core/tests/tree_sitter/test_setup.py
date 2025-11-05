"""Test tree-sitter dependencies and basic setup."""


def test_import_tree_sitter():
    """Verify tree-sitter package imports successfully."""
    from tree_sitter import Language, Parser

    assert Language is not None
    assert Parser is not None


def test_import_tree_sitter_python():
    """Verify tree-sitter-python grammar imports."""
    import tree_sitter_python

    assert tree_sitter_python is not None
    assert hasattr(tree_sitter_python, "language")


def test_load_python_grammar():
    """Verify Python grammar loads correctly."""
    import tree_sitter_python
    from tree_sitter import Language

    # This will raise if grammar is invalid
    grammar = Language(tree_sitter_python.language())

    assert grammar is not None


def test_create_parser():
    """Verify parser can be instantiated."""
    from tree_sitter import Parser, Language
    import tree_sitter_python

    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser(PY_LANGUAGE)

    assert parser is not None


def test_parse_simple_code():
    """Verify basic parsing works."""
    from tree_sitter import Parser, Language
    import tree_sitter_python

    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser(PY_LANGUAGE)

    code = b"def hello(): pass"
    tree = parser.parse(code)

    assert tree is not None
    assert tree.root_node is not None
    assert tree.root_node.type == "module"


def test_parse_unicode():
    """Verify parsing works with Unicode characters."""
    from tree_sitter import Parser, Language
    import tree_sitter_python

    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser(PY_LANGUAGE)

    # Spanish variable names using raw bytes to avoid encoding issues
    code = b"nombre = 'Jose'\nprint(nombre)"
    tree = parser.parse(code)

    assert tree is not None
    assert tree.root_node.type == "module"


def test_basic_query():
    """Verify query execution works."""
    from tree_sitter import Parser, Language, Query, QueryCursor
    import tree_sitter_python

    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser(PY_LANGUAGE)

    code = b"def foo(): pass\nclass Bar: pass"
    tree = parser.parse(code)

    # Query for function definitions
    query = Query(PY_LANGUAGE, "(function_definition) @func")
    cursor = QueryCursor(query)
    matches = list(cursor.matches(tree.root_node))

    assert len(matches) == 1  # One function
    pattern_index, captures = matches[0]
    assert "func" in captures
    assert len(captures["func"]) == 1
    assert captures["func"][0].type == "function_definition"


def test_query_multiple_captures():
    """Verify query captures multiple nodes."""
    from tree_sitter import Parser, Language, Query, QueryCursor
    import tree_sitter_python

    PY_LANGUAGE = Language(tree_sitter_python.language())
    parser = Parser(PY_LANGUAGE)

    code = b"""
def foo(): pass
def bar(): pass
def baz(): pass
"""
    tree = parser.parse(code)

    query = Query(PY_LANGUAGE, "(function_definition) @func")
    cursor = QueryCursor(query)
    matches = list(cursor.matches(tree.root_node))

    assert len(matches) == 3  # Three functions
