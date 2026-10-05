"""Tests for hover provider (CORE-357).

This module tests:
- Keyword hover with translations
- Builtin function hover
- User-defined function hover
- Cultural comment hover
- Performance requirements (<100ms)
"""

import time

import pytest
from lsprotocol.types import Position

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.providers.hover import (
    HoverProvider,
    _extract_word_at_position,
    provide_hover,
)
from legesher_language_server.server import LegesherLanguageServer
from tests.timing import assert_within


class TestExtractWordAtPosition:
    """Test word extraction at cursor position."""

    def test_extract_word_start_of_line(self):
        """Test extracting word at start of line."""
        text = "def hello():\n    pass"
        position = Position(line=0, character=0)
        word = _extract_word_at_position(text, position)
        assert word == "def"

    def test_extract_word_middle_of_word(self):
        """Test extracting word when cursor in middle."""
        text = "print('hello')"
        position = Position(line=0, character=2)  # "pr|int"
        word = _extract_word_at_position(text, position)
        assert word == "print"

    def test_extract_word_end_of_word(self):
        """Test extracting word at end boundary."""
        text = "return 42"
        position = Position(line=0, character=5)  # "retur|n"
        word = _extract_word_at_position(text, position)
        assert word == "return"

    def test_extract_word_with_underscore(self):
        """Test extracting identifier with underscores."""
        text = "my_function_name = 10"
        position = Position(line=0, character=5)
        word = _extract_word_at_position(text, position)
        assert word == "my_function_name"

    def test_extract_word_invalid_position(self):
        """Test extraction with invalid position."""
        text = "hello"
        position = Position(line=10, character=0)
        word = _extract_word_at_position(text, position)
        assert word is None

    def test_extract_word_no_word_at_position(self):
        """Test extraction when cursor on whitespace."""
        text = "def    hello"
        position = Position(line=0, character=4)  # On space
        word = _extract_word_at_position(text, position)
        assert word is None


class TestHoverProviderKeywords:
    """Test hover provider for Python keywords."""

    @pytest.fixture
    def provider(self):
        """Create hover provider for testing."""
        return HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

    def test_hover_keyword_spanish(self, provider):
        """Test keyword hover with Spanish translation."""
        content = provider._hover_keyword("def")
        assert content is not None
        assert "def" in content
        assert "Python keyword" in content
        assert "Definir una función" in content

    def test_hover_keyword_arabic(self):
        """Test keyword hover with Arabic translation."""
        provider = HoverProvider(
            source_lang="en",
            target_lang="ar",
            document_text="",
            document_uri="file:///test.py",
        )
        content = provider._hover_keyword("class")
        assert content is not None
        assert "class" in content
        assert "تعريف فئة" in content

    def test_hover_keyword_fallback_to_english(self):
        """Test keyword hover falls back to English for unsupported language."""
        provider = HoverProvider(
            source_lang="en",
            target_lang="fr",  # Not supported
            document_text="",
            document_uri="file:///test.py",
        )
        content = provider._hover_keyword("def")
        assert content is not None
        assert "Define a function" in content

    @pytest.mark.parametrize(
        "keyword",
        [
            "def",
            "class",
            "if",
            "elif",
            "else",
            "for",
            "while",
            "return",
            "import",
            "from",
            "try",
            "except",
            "finally",
            "raise",
            "with",
            "lambda",
            "yield",
            "async",
            "await",
            "match",
            "case",
        ],
    )
    def test_hover_all_keywords(self, provider, keyword):
        """Test hover works for all documented keywords."""
        content = provider._hover_keyword(keyword)
        assert content is not None
        assert keyword in content


class TestHoverProviderBuiltins:
    """Test hover provider for builtin functions."""

    @pytest.fixture
    def provider(self):
        """Create hover provider for testing."""
        return HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text="",
            document_uri="file:///test.py",
        )

    @pytest.mark.asyncio
    async def test_hover_print_builtin(self, provider):
        """Test hover on print builtin."""
        content = await provider._hover_builtin("print")
        assert content is not None
        assert "print" in content
        assert "```python" in content  # Should have code block with signature
        # Should contain part of print's docstring
        assert "objects" in content.lower() or "print" in content.lower()

    @pytest.mark.asyncio
    async def test_hover_len_builtin(self, provider):
        """Test hover on len builtin."""
        content = await provider._hover_builtin("len")
        assert content is not None
        assert "len" in content
        assert "```python" in content  # Should have code block with signature

    @pytest.mark.asyncio
    async def test_hover_list_builtin(self, provider):
        """Test hover on list builtin."""
        content = await provider._hover_builtin("list")
        assert content is not None
        assert "list" in content
        assert "```python" in content  # Should have code block with signature

    @pytest.mark.asyncio
    async def test_hover_builtin_caching(self, provider):
        """Test builtin hover uses caching."""
        # First call
        content1 = await provider._hover_builtin("print")

        # Second call should use cache
        content2 = await provider._hover_builtin("print")

        assert content1 == content2

    @pytest.mark.asyncio
    async def test_hover_invalid_builtin(self, provider):
        """Test hover on non-existent builtin."""
        content = await provider._hover_builtin("not_a_builtin_12345")
        assert content is None

    def test_is_builtin(self, provider):
        """Test builtin detection."""
        assert provider._is_builtin("print") is True
        assert provider._is_builtin("len") is True
        assert provider._is_builtin("list") is True
        assert provider._is_builtin("not_builtin") is False


class TestHoverProviderUserDefined:
    """Test hover provider for user-defined functions/classes."""

    def test_hover_user_function(self):
        """Test hover on user-defined function."""
        document = """
def calculate_tax(income, rate):
    \"\"\"Calculate income tax.

    Args:
        income: Annual income
        rate: Tax rate

    Returns:
        Tax amount
    \"\"\"
    return income * rate
"""
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._hover_user_defined("calculate_tax")
        assert content is not None
        assert "calculate_tax" in content
        assert "income, rate" in content
        assert "Calculate income tax" in content
        assert "User-defined function" in content

    def test_hover_user_class(self):
        """Test hover on user-defined class."""
        document = """
class Calculator:
    \"\"\"Simple calculator class.

    Performs basic arithmetic operations.
    \"\"\"
    def __init__(self):
        pass
"""
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._hover_user_defined("Calculator")
        assert content is not None
        assert "Calculator" in content
        assert "Simple calculator class" in content
        assert "User-defined class" in content

    def test_hover_async_function(self):
        """Test hover on async function."""
        document = """
async def fetch_data(url):
    \"\"\"Fetch data from URL asynchronously.\"\"\"
    pass
"""
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._hover_user_defined("fetch_data")
        assert content is not None
        assert "fetch_data" in content
        assert "async" in content
        assert "Fetch data" in content

    def test_hover_function_no_docstring(self):
        """Test hover on function without docstring."""
        document = "def no_doc():\n    pass"
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._hover_user_defined("no_doc")
        assert content is None

    def test_hover_function_not_found(self):
        """Test hover on non-existent function."""
        document = "def hello(): pass"
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._hover_user_defined("goodbye")
        assert content is None

    def test_hover_syntax_error(self):
        """Test hover handles syntax errors gracefully."""
        document = "def broken( pass"  # Invalid syntax
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._hover_user_defined("broken")
        assert content is None


class TestHoverProviderCulturalComments:
    """Test hover provider for cultural comments."""

    def test_hover_cultural_comment(self):
        """Test hover on line with cultural comment."""
        document = """
def example():
    #@culture[es]: En español, "ejemplo" significa "example"
    pass
"""
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._get_cultural_comment(2)  # Line with cultural comment
        assert content is not None
        assert "💬" in content
        assert "Cultural Context" in content
        assert "ES" in content
        assert "ejemplo" in content

    def test_hover_no_cultural_comment(self):
        """Test hover on line without cultural comment."""
        document = "def hello():\n    # Regular comment\n    pass"
        provider = HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._get_cultural_comment(1)
        assert content is None

    def test_hover_cultural_comment_arabic(self):
        """Test cultural comment with Arabic language tag."""
        document = """#@culture[ar]: في العربية، نستخدم "قائمة" للتعبير عن "list"
my_list = [1, 2, 3]"""
        provider = HoverProvider(
            source_lang="en",
            target_lang="ar",
            document_text=document,
            document_uri="file:///test.py",
        )

        content = provider._get_cultural_comment(0)  # Line 0 now has the comment
        assert content is not None
        assert "AR" in content
        assert "قائمة" in content


@pytest.mark.asyncio
class TestHoverProviderIntegration:
    """Integration tests for full hover flow.

    Note: Skipped due to pygls Python 3.13 compatibility issue.
    These tests will be enabled once pygls supports Python 3.13.
    """

    @pytest.fixture
    def server(self):
        """Create language server for testing."""
        config = LanguageServerConfig(
            source_language="en",
            target_language="es",
            python_version="3.11",
            cache_size=100,
            cache_ttl=3600,
            log_level="INFO",
        )
        return LegesherLanguageServer(config)

    async def test_provide_hover_keyword(self, server):
        """Test full hover flow for keyword."""
        document_text = "def hello():\n    pass"

        # Open document
        server.document_manager.open_document(
            uri="file:///test.py",
            text=document_text,
            version=1,
            language_id="python",
        )

        # Request hover on "def"
        position = Position(line=0, character=1)
        hover = await provide_hover(server, "file:///test.py", position)

        assert hover is not None
        assert hover.contents.value is not None
        assert "def" in hover.contents.value
        assert "Definir una función" in hover.contents.value

    async def test_provide_hover_builtin(self, server):
        """Test full hover flow for builtin."""
        document_text = "result = len([1, 2, 3])"

        server.document_manager.open_document(
            uri="file:///test.py",
            text=document_text,
            version=1,
            language_id="python",
        )

        # Request hover on "len"
        position = Position(line=0, character=10)
        hover = await provide_hover(server, "file:///test.py", position)

        assert hover is not None
        assert "len" in hover.contents.value

    async def test_provide_hover_user_function(self, server):
        """Test full hover flow for user function."""
        document_text = """
def greet(name):
    \"\"\"Greet a person by name.\"\"\"
    return f"Hello, {name}"

greet("World")
"""

        server.document_manager.open_document(
            uri="file:///test.py",
            text=document_text,
            version=1,
            language_id="python",
        )

        # Request hover on "greet" function definition
        position = Position(line=1, character=5)
        hover = await provide_hover(server, "file:///test.py", position)

        assert hover is not None
        assert "greet" in hover.contents.value
        assert "Greet a person" in hover.contents.value

    async def test_provide_hover_invalid_position(self, server):
        """Test hover with invalid document position."""
        document_text = "print('hello')"

        server.document_manager.open_document(
            uri="file:///test.py",
            text=document_text,
            version=1,
            language_id="python",
        )

        # Request hover on invalid line
        position = Position(line=100, character=0)
        hover = await provide_hover(server, "file:///test.py", position)

        assert hover is None

    async def test_provide_hover_document_not_found(self, server):
        """Test hover with non-existent document."""
        position = Position(line=0, character=0)
        hover = await provide_hover(server, "file:///nonexistent.py", position)

        assert hover is None


@pytest.mark.timing
class TestHoverProviderPerformance:
    """Performance tests for hover provider."""

    @pytest.fixture
    def provider(self):
        """Create hover provider with realistic document."""
        document = """
import os
import sys

def calculate_tax(income, rate):
    \"\"\"Calculate income tax based on rate.

    Args:
        income: Annual income
        rate: Tax rate

    Returns:
        Tax amount
    \"\"\"
    return income * rate

class TaxCalculator:
    \"\"\"Tax calculator class.\"\"\"

    def __init__(self):
        self.rates = {}

    def add_rate(self, bracket, rate):
        self.rates[bracket] = rate

# Cultural note
#@culture[es]: "impuesto" significa "tax" en español
"""
        return HoverProvider(
            source_lang="en",
            target_lang="es",
            document_text=document,
            document_uri="file:///test.py",
        )

    def test_keyword_hover_performance(self, provider):
        """Test keyword hover completes in <50ms."""
        start = time.perf_counter()
        content = provider._hover_keyword("def")
        duration = (time.perf_counter() - start) * 1000  # Convert to ms

        assert content is not None
        assert_within(duration, 50, "Keyword hover")

    @pytest.mark.asyncio
    async def test_builtin_hover_performance(self, provider):
        """Test builtin hover completes in <100ms."""
        start = time.perf_counter()
        content = await provider._hover_builtin("print")
        duration = (time.perf_counter() - start) * 1000

        assert content is not None
        assert_within(duration, 100, "Builtin hover")

    def test_user_function_hover_performance(self, provider):
        """Test user function hover completes in <200ms."""
        start = time.perf_counter()
        content = provider._hover_user_defined("calculate_tax")
        duration = (time.perf_counter() - start) * 1000

        assert content is not None
        assert_within(duration, 200, "User function hover")

    @pytest.mark.asyncio
    async def test_overall_hover_performance(self, provider):
        """Test overall hover performance meets <100ms target for 90% of cases."""
        position = Position(line=0, character=0)
        durations = []

        # Run 100 iterations
        for _ in range(100):
            start = time.perf_counter()
            await provider.get_hover_content("def", position)
            duration = (time.perf_counter() - start) * 1000
            durations.append(duration)

        # Sort to get percentile
        durations.sort()
        p90_duration = durations[89]  # 90th percentile

        assert_within(p90_duration, 100, "Hover at the 90th percentile")
