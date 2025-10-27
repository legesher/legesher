"""Unit tests for TokenMapper class."""

import pytest

from legesher_core.token_mapper import TokenMapper


class TestTokenMapper:
    """Test suite for TokenMapper functionality."""

    def test_initialization_valid(self):
        """Test TokenMapper initialization with valid maps."""
        keyword_map = {"def": "definir", "return": "retornar"}
        builtin_map = {"print": "imprimir"}

        mapper = TokenMapper(keyword_map, builtin_map)

        assert mapper.keyword_map == keyword_map
        assert mapper.builtin_map == builtin_map

    def test_initialization_empty_keyword_map(self):
        """Test that empty keyword map raises ValueError."""
        with pytest.raises(ValueError, match="keyword_map cannot be empty"):
            TokenMapper({}, {"print": "imprimir"})

    def test_initialization_empty_builtin_map(self):
        """Test that empty builtin map raises ValueError."""
        with pytest.raises(ValueError, match="builtin_map cannot be empty"):
            TokenMapper({"def": "definir"}, {})

    def test_get_keyword_found(self):
        """Test getting a keyword that exists."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        result = mapper.get_keyword("def")
        assert result == "definir"

    def test_get_keyword_not_found(self):
        """Test getting a keyword that doesn't exist."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        result = mapper.get_keyword("nonexistent")
        assert result is None

    def test_get_builtin_found(self):
        """Test getting a builtin that exists."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        result = mapper.get_builtin("print")
        assert result == "imprimir"

    def test_get_builtin_not_found(self):
        """Test getting a builtin that doesn't exist."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        result = mapper.get_builtin("nonexistent")
        assert result is None

    def test_is_keyword_true(self):
        """Test is_keyword returns True for existing keyword."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        assert mapper.is_keyword("def") is True

    def test_is_keyword_false(self):
        """Test is_keyword returns False for non-keyword."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        assert mapper.is_keyword("nonexistent") is False

    def test_is_builtin_true(self):
        """Test is_builtin returns True for existing builtin."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        assert mapper.is_builtin("print") is True

    def test_is_builtin_false(self):
        """Test is_builtin returns False for non-builtin."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})

        assert mapper.is_builtin("nonexistent") is False
