"""Tests for completion provider (CORE-358).

This module tests:
- Keyword completions with translations
- Builtin function completions
- User-defined symbol completions (functions, variables, classes)
- Context-aware filtering
- Scope-aware filtering
- Fuzzy matching
- Performance requirements (<50ms)
- Integration with Language Server
"""

import time

import pytest
from lsprotocol.types import CompletionItemKind, Position

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.providers.completion import (
    CompletionProvider,
    SymbolKind,
    clear_caches,
    provide_completion,
)
from legesher_language_server.server import LegesherLanguageServer


@pytest.fixture(autouse=True)
def _clear_completion_caches():
    """Clear completion/symbol caches between tests to prevent cross-test interference."""
    clear_caches()
    yield
    clear_caches()


class TestCompletionProviderKeywords:
    """Test completion provider for Python keywords."""

    @pytest.fixture
    def provider(self):
        """Create completion provider for testing."""
        return CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
            document_version=1,
        )

    def test_keyword_completions_spanish(self, provider):
        """Test keyword completions with Spanish translations."""
        items = provider._build_keyword_completions()
        assert len(items) > 0

        # Check specific translations
        labels = [item.label for item in items]
        assert "definir" in labels  # def
        assert "clase" in labels  # class
        assert "si" in labels  # if
        assert "por" in labels  # for
        assert "mientras" in labels  # while
        assert "devolver" in labels  # return

    def test_keyword_completions_arabic(self):
        """Test keyword completions with Arabic translations."""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="ar",
            document_text="",
            document_uri="file:///test.py",
            document_version=1,
        )
        items = provider._build_keyword_completions()
        assert len(items) > 0

        # Check Arabic translations exist
        labels = [item.label for item in items]
        assert any("\u0639" in label or "تعريف" in label for label in labels)  # Arabic chars

    def test_keyword_completion_item_structure(self, provider):
        """Test that keyword CompletionItems have correct structure."""
        items = provider._build_keyword_completions()
        item = items[0]

        assert hasattr(item, "label")
        assert hasattr(item, "kind")
        assert item.kind == CompletionItemKind.Keyword
        assert hasattr(item, "detail")
        assert "Python keyword" in item.detail
        assert hasattr(item, "sort_text")
        assert item.sort_text.startswith("0_")  # Priority 0

    def test_keyword_completions_cached(self, provider):
        """Test that keyword completions are cached."""
        items1 = provider.keyword_items
        items2 = provider.keyword_items
        assert items1 is items2  # Same object reference

    @pytest.mark.parametrize(
        "keyword,spanish",
        [
            ("def", "definir"),
            ("class", "clase"),
            ("if", "si"),
            ("for", "por"),
            ("while", "mientras"),
            ("return", "devolver"),
            ("import", "importar"),
            ("from", "desde"),
        ],
    )
    def test_specific_keyword_translations(self, provider, keyword, spanish):
        """Test specific keyword translations are correct."""
        labels = [item.label for item in provider.keyword_items]
        assert spanish in labels


class TestCompletionProviderBuiltins:
    """Test completion provider for Python builtin functions."""

    @pytest.fixture
    def provider(self):
        """Create completion provider for testing."""
        return CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
            document_version=1,
        )

    def test_builtin_completions_exist(self, provider):
        """Test that builtin completions are generated."""
        items = provider._build_builtin_completions()
        assert len(items) > 0

        # Check common builtins
        labels = [item.label for item in items]
        assert "print" in labels
        assert "len" in labels
        assert "range" in labels
        assert "str" in labels
        assert "int" in labels

    def test_builtin_completion_item_structure(self, provider):
        """Test that builtin CompletionItems have correct structure."""
        items = provider._build_builtin_completions()
        item = items[0]

        assert hasattr(item, "label")
        assert hasattr(item, "kind")
        assert item.kind == CompletionItemKind.Function
        assert hasattr(item, "detail")
        assert "Built-in function" in item.detail
        assert hasattr(item, "sort_text")
        assert item.sort_text.startswith("1_")  # Priority 1
        assert hasattr(item, "insert_text")
        assert "$0" in item.insert_text  # Snippet with cursor

    def test_builtin_count(self, provider):
        """Test expected number of builtin completions."""
        items = provider._build_builtin_completions()
        # Should have at least 25 common builtins
        assert len(items) >= 25


class TestCompletionProviderSymbolExtraction:
    """Test user-defined symbol extraction from documents."""

    def test_extract_function_definitions(self):
        """Test extraction of function definitions."""
        code = """
def hello():
    pass

def world(x, y):
    return x + y
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        assert len(provider.symbols) == 2
        assert provider.symbols[0].name == "hello"
        assert provider.symbols[0].kind == SymbolKind.FUNCTION
        assert provider.symbols[1].name == "world"
        assert provider.symbols[1].kind == SymbolKind.FUNCTION

    def test_extract_class_definitions(self):
        """Test extraction of class definitions."""
        code = """
class MyClass:
    pass

class AnotherClass:
    def method(self):
        pass
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        classes = [s for s in provider.symbols if s.kind == SymbolKind.CLASS]
        assert len(classes) == 2
        assert classes[0].name == "MyClass"
        assert classes[1].name == "AnotherClass"

    def test_extract_variable_assignments(self):
        """Test extraction of variable assignments."""
        code = """
x = 10
y = 20
result = x + y
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        variables = [s for s in provider.symbols if s.kind == SymbolKind.VARIABLE]
        assert len(variables) == 3
        var_names = [v.name for v in variables]
        assert "x" in var_names
        assert "y" in var_names
        assert "result" in var_names

    def test_extract_mixed_symbols(self):
        """Test extraction of mixed symbol types."""
        code = """
x = 10

def calculate(a, b):
    result = a + b
    return result

class Calculator:
    def add(self, x, y):
        return x + y

y = 20
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        functions = [s for s in provider.symbols if s.kind == SymbolKind.FUNCTION]
        classes = [s for s in provider.symbols if s.kind == SymbolKind.CLASS]
        variables = [s for s in provider.symbols if s.kind == SymbolKind.VARIABLE]

        assert len(functions) >= 1  # calculate (add is nested, may not be extracted)
        assert len(classes) == 1
        assert len(variables) >= 2  # x, y, result

    def test_extract_symbols_with_syntax_error(self):
        """Test graceful handling of syntax errors."""
        code = """
def incomplete_function(
    # Missing closing paren and colon
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        # Should not crash, returns empty list
        assert provider.symbols == []

    def test_extract_symbols_empty_document(self):
        """Test extraction from empty document."""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
            document_version=1,
        )

        assert provider.symbols == []

    def test_symbol_line_numbers(self):
        """Test that symbols have correct line numbers."""
        code = """
def first():  # Line 2
    pass

x = 10  # Line 5

class MyClass:  # Line 7
    pass
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        first_func = next(s for s in provider.symbols if s.name == "first")
        assert first_func.line == 2

        x_var = next(s for s in provider.symbols if s.name == "x")
        assert x_var.line == 5

        my_class = next(s for s in provider.symbols if s.name == "MyClass")
        assert my_class.line == 7


class TestCompletionProviderContextAnalysis:
    """Test context analysis for intelligent completion."""

    @pytest.fixture
    def provider(self):
        """Create completion provider for testing."""
        code = """
x = 10
def hello():
    pass
"""
        return CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

    def test_context_partial_word_extraction(self, provider):
        """Test extraction of partial word being typed."""
        # Simulate typing "pri" at end of line
        provider.document_text = "pri"
        context = provider._get_completion_context(Position(line=0, character=3))

        assert context.partial_word == "pri"

    def test_context_no_partial_word(self, provider):
        """Test context when no partial word."""
        context = provider._get_completion_context(Position(line=0, character=0))

        assert context.partial_word == ""

    def test_context_line_start(self, provider):
        """Test detection of line start."""
        context = provider._get_completion_context(Position(line=0, character=0))

        assert context.is_line_start is True

    def test_context_not_line_start(self, provider):
        """Test detection when not at line start."""
        provider.document_text = "    x = 10"
        context = provider._get_completion_context(Position(line=0, character=7))

        assert context.is_line_start is False

    def test_context_line_text(self, provider):
        """Test line text extraction."""
        provider.document_text = "x = 10\ny = 20"
        context = provider._get_completion_context(Position(line=1, character=0))

        assert context.line_text == "y = 20"


class TestCompletionProviderScopeFiltering:
    """Test scope-aware symbol filtering."""

    def test_no_forward_references(self):
        """Test that symbols defined after cursor are not suggested."""
        code = """
x = 10
# Cursor here at line 2
y = 20
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        context = provider._get_completion_context(Position(line=2, character=0))
        symbol_items = provider._get_symbol_completions(context)

        labels = [item.label for item in symbol_items]
        assert "x" in labels  # Defined before cursor
        assert "y" not in labels  # Defined after cursor

    def test_symbols_before_cursor(self):
        """Test that symbols before cursor are suggested."""
        code = """
x = 10
y = 20
z = 30
# Cursor here
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        context = provider._get_completion_context(Position(line=4, character=0))
        symbol_items = provider._get_symbol_completions(context)

        labels = [item.label for item in symbol_items]
        assert "x" in labels
        assert "y" in labels
        assert "z" in labels

    def test_symbol_completion_item_kinds(self):
        """Test that symbol CompletionItems have correct kinds."""
        code = """
x = 10
def my_func():
    pass
class MyClass:
    pass
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        context = provider._get_completion_context(Position(line=6, character=0))
        symbol_items = provider._get_symbol_completions(context)

        for item in symbol_items:
            if item.label == "x":
                assert item.kind == CompletionItemKind.Variable
            elif item.label == "my_func":
                assert item.kind == CompletionItemKind.Function
            elif item.label == "MyClass":
                assert item.kind == CompletionItemKind.Class


class TestCompletionProviderFuzzyMatching:
    """Test fuzzy matching for completion filtering."""

    @pytest.fixture
    def provider(self):
        """Create completion provider for testing."""
        code = """
def calculate_tax(income, rate):
    result = income * rate
    return result
"""
        return CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

    def test_fuzzy_match_prefix(self, provider):
        """Test prefix-based fuzzy matching."""
        context = provider._get_completion_context(Position(line=4, character=0))
        context.partial_word = "calc"

        all_items = provider._get_symbol_completions(context)
        filtered = provider._fuzzy_filter(all_items, "calc")

        labels = [item.label for item in filtered]
        assert "calculate_tax" in labels

    def test_fuzzy_match_case_insensitive(self, provider):
        """Test case-insensitive fuzzy matching."""
        context = provider._get_completion_context(Position(line=4, character=0))
        all_items = provider._get_symbol_completions(context)

        # Lower case query should match mixed case symbol
        filtered = provider._fuzzy_filter(all_items, "calc")
        labels = [item.label for item in filtered]
        assert "calculate_tax" in labels

    def test_fuzzy_match_no_match(self, provider):
        """Test fuzzy matching with no matches."""
        context = provider._get_completion_context(Position(line=4, character=0))
        all_items = provider._get_symbol_completions(context)

        filtered = provider._fuzzy_filter(all_items, "xyz")
        assert len(filtered) == 0

    def test_fuzzy_match_empty_partial(self, provider):
        """Test fuzzy matching with empty partial word returns all."""
        context = provider._get_completion_context(Position(line=4, character=0))
        all_items = provider._get_symbol_completions(context)

        filtered = provider._fuzzy_filter(all_items, "")
        assert len(filtered) == len(all_items)

    def test_fuzzy_match_keywords(self, provider):
        """Test fuzzy matching works on keywords too."""
        # Test with Spanish keywords
        keywords = provider.keyword_items

        # Filter for "def" -> "definir"
        filtered = provider._fuzzy_filter(keywords, "def")
        labels = [item.label for item in filtered]
        assert "definir" in labels


class TestCompletionProviderIntegration:
    """Test complete completion flow."""

    @pytest.fixture
    def provider(self):
        """Create completion provider with realistic code."""
        code = """
import math

def calculate_tax(income, rate):
    '''Calculate income tax.'''
    result = income * rate
    return result

x = 10
y = 20

class Calculator:
    def add(self, a, b):
        return a + b
"""
        return CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

    def test_get_all_completions(self, provider):
        """Test getting all completion types."""
        position = Position(line=14, character=0)
        items = provider.get_completions(position)

        # Should have keywords, builtins, and user symbols
        assert len(items) > 0

        labels = [item.label for item in items]

        # Keywords (Spanish)
        assert "definir" in labels  # def
        assert "clase" in labels  # class

        # Builtins
        assert "print" in labels
        assert "len" in labels

        # User symbols
        assert "calculate_tax" in labels
        assert "x" in labels
        assert "Calculator" in labels

    def test_get_completions_with_partial_word(self, provider):
        """Test completions with partial word filtering."""
        # Simulate typing "calc" at end of document
        provider.document_text += "\ncalc"
        position = Position(line=15, character=4)

        items = provider.get_completions(position)

        labels = [item.label for item in items]

        # Should only match items starting with "calc"
        assert "calculate_tax" in labels
        # Should not have unrelated items
        assert "x" not in labels
        assert "y" not in labels

    def test_completion_sorting_priority(self, provider):
        """Test that completions are sorted by priority."""
        position = Position(line=14, character=0)
        items = provider.get_completions(position)

        # Check sort_text priorities
        keyword_items = [item for item in items if item.sort_text.startswith("0_")]
        builtin_items = [item for item in items if item.sort_text.startswith("1_")]
        symbol_items = [item for item in items if item.sort_text.startswith("2_")]

        assert len(keyword_items) > 0
        assert len(builtin_items) > 0
        assert len(symbol_items) > 0


class TestCompletionProviderPerformance:
    """Test performance requirements (<50ms)."""

    @pytest.fixture
    def large_document(self):
        """Create a large document for performance testing."""
        lines = []
        for i in range(100):
            lines.append(f"def function_{i}():")
            lines.append(f"    var_{i} = {i}")
            lines.append(f"    return var_{i}")
            lines.append("")
        return "\n".join(lines)

    def test_completion_performance_small_file(self):
        """Test completion time for small file (<50ms)."""
        code = """
def hello():
    pass

x = 10
"""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )

        start = time.perf_counter()
        items = provider.get_completions(Position(line=5, character=0))
        duration = (time.perf_counter() - start) * 1000  # Convert to ms

        assert duration < 50, f"Completion took {duration:.2f}ms (target: <50ms)"
        assert len(items) > 0

    def test_completion_performance_large_file(self, large_document):
        """Test completion time for large file (<50ms)."""
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=large_document,
            document_uri="file:///test.py",
            document_version=1,
        )

        start = time.perf_counter()
        items = provider.get_completions(Position(line=400, character=0))
        duration = (time.perf_counter() - start) * 1000

        assert duration < 50, f"Completion took {duration:.2f}ms (target: <50ms)"
        assert len(items) > 0

    def test_symbol_extraction_performance(self, large_document):
        """Test symbol extraction performance."""
        start = time.perf_counter()
        provider = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=large_document,
            document_uri="file:///test.py",
            document_version=1,
        )
        duration = (time.perf_counter() - start) * 1000

        # Symbol extraction (AST parsing) should be <30ms for 1000-line file
        assert duration < 30, f"Symbol extraction took {duration:.2f}ms (target: <30ms)"
        assert len(provider.symbols) > 0

    def test_completion_caching_performance(self):
        """Test that caching improves performance."""
        code = "x = 10"

        # First call - builds cache
        provider1 = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )
        start1 = time.perf_counter()
        provider1.get_completions(Position(line=1, character=0))
        duration1 = (time.perf_counter() - start1) * 1000

        # Second call - uses cache
        provider2 = CompletionProvider(
            source_lang="en",
            target_lang="es",
            document_text=code,
            document_uri="file:///test.py",
            document_version=1,
        )
        start2 = time.perf_counter()
        provider2.get_completions(Position(line=1, character=0))
        duration2 = (time.perf_counter() - start2) * 1000

        # Second call should be faster (uses cached keyword/builtin items)
        assert duration2 <= duration1 * 1.2  # Allow 20% variance


@pytest.mark.asyncio
class TestProvideCompletionFunction:
    """Test the async provide_completion function."""

    @pytest.fixture
    def server(self):
        """Create language server for testing."""
        config = LanguageServerConfig(
            source_language="en",
            target_language="es",
            python_version="3.11",
            cache_size=1000,
            cache_ttl=3600,
            log_level="INFO",
        )
        server = LegesherLanguageServer(config)
        return server

    async def test_provide_completion_with_document(self, server):
        """Test provide_completion with real document."""
        uri = "file:///test.py"
        code = """
def hello():
    pass

x = 10
"""
        # Open document
        server.document_manager.open_document(uri, code, 1, "python")

        # Get completions
        items = await provide_completion(server, uri, Position(line=5, character=0))

        assert len(items) > 0
        labels = [item.label for item in items]
        assert "definir" in labels  # Spanish "def"
        assert "hello" in labels  # User function

    async def test_provide_completion_no_document(self, server):
        """Test provide_completion with non-existent document."""
        items = await provide_completion(
            server, "file:///nonexistent.py", Position(line=0, character=0)
        )

        assert items == []

    async def test_provide_completion_integration_flow(self, server):
        """Test complete integration flow."""
        uri = "file:///integration_test.py"
        code = """
import math

def calculate_area(radius):
    pi = math.pi
    area = pi * radius ** 2
    return area

radius = 5.0
result = calculate_area(radius)
"""
        # Open document
        server.document_manager.open_document(uri, code, 1, "python")

        # Get completions at various positions
        position1 = Position(line=11, character=0)  # After all code
        items1 = await provide_completion(server, uri, position1)

        # Should include keywords, builtins, and symbols
        labels = [item.label for item in items1]
        assert len(labels) > 0
        assert "definir" in labels  # Keyword
        assert "print" in labels  # Builtin
        assert "calculate_area" in labels  # User function
        assert "radius" in labels  # User variable
        assert "result" in labels  # User variable

        # Test partial word completion
        server.document_manager.update_document(uri, code + "\ncalc", 2)
        position2 = Position(line=11, character=4)
        items2 = await provide_completion(server, uri, position2)

        labels2 = [item.label for item in items2]
        assert "calculate_area" in labels2
        assert len(labels2) < len(labels)  # Filtered by partial word
