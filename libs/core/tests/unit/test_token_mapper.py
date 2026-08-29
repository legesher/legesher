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


class TestReservedWordMap:
    """Test implicit_param_map support (CORE-710)."""

    def test_default_implicit_param_map_is_empty(self):
        """Backward-compat: omitting implicit_param_map defaults to empty."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})
        assert mapper.implicit_param_map == {}

    def test_implicit_param_map_accepts_self_cls(self):
        """Constructor accepts and stores implicit_param_map."""
        mapper = TokenMapper(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio", "cls": "clase"},
        )
        assert mapper.implicit_param_map == {"self": "propio", "cls": "clase"}

    def test_get_implicit_param_returns_translation(self):
        """get_implicit_param returns mapped value."""
        mapper = TokenMapper(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio"},
        )
        assert mapper.get_implicit_param("self") == "propio"

    def test_get_implicit_param_returns_none_for_missing(self):
        """get_implicit_param returns None for unmapped keys."""
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})
        assert mapper.get_implicit_param("self") is None

    def test_is_implicit_param_true_when_present(self):
        """is_implicit_param predicate returns True when key is mapped."""
        mapper = TokenMapper(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio"},
        )
        assert mapper.is_implicit_param("self") is True
        assert mapper.is_implicit_param("def") is False

    def test_reverse_reverses_implicit_param_map(self):
        """reverse() also reverses the implicit_param_map for round-trip."""
        en_to_es = TokenMapper(
            keyword_map={"def": "definir"},
            builtin_map={"print": "imprimir"},
            implicit_param_map={"self": "propio"},
        )
        es_to_en = en_to_es.reverse()
        assert es_to_en.get_implicit_param("propio") == "self"

    def test_empty_implicit_param_map_does_not_raise(self):
        """Unlike keyword_map/builtin_map, implicit_param_map can be empty.

        Most existing callers won't pass implicit_param_map; default of None
        and explicit {} should both be accepted without ValueError.
        """
        # Both None and {} are accepted without raising
        TokenMapper({"def": "definir"}, {"print": "imprimir"}, None)
        TokenMapper({"def": "definir"}, {"print": "imprimir"}, {})
