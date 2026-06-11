"""Tests for NFKC-normalization-safe matching and collision-safe reverse()."""

import logging
import unicodedata

import pytest

from legesher_core.token_mapper import TokenMapper


class TestNormalizationFallback:
    def test_exact_match_still_wins(self):
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})
        assert mapper.get_keyword("def") == "definir"
        assert mapper.get_builtin("print") == "imprimir"

    def test_fullwidth_if_resolves_to_keyword(self):
        mapper = TokenMapper({"if": "si"}, {"print": "imprimir"})
        fullwidth_if = "ｉｆ"  # fullwidth 'ｉｆ'
        assert unicodedata.normalize("NFKC", fullwidth_if) == "if"
        assert mapper.get_keyword(fullwidth_if) == "si"

    def test_thai_sara_am_roundtrip_matches_nfkc_form(self):
        # U+0E33 SARA AM decomposes under NFKC. Key stored composed; lookup via
        # NFKC form must still match.
        sara_am_key = "nำ"
        nfkc_form = unicodedata.normalize("NFKC", sara_am_key)
        mapper = TokenMapper({sara_am_key: "X"}, {"print": "p"})
        assert mapper.get_keyword(nfkc_form) == "X"

    def test_unknown_token_still_returns_none(self):
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})
        assert mapper.get_keyword("nonexistent") is None

    def test_reserved_word_normalized_lookup(self):
        mapper = TokenMapper(
            {"def": "d"}, {"print": "p"}, reserved_word_map={"self": "propio"}
        )
        assert mapper.get_reserved_word("self") == "propio"


class TestRealPackExactMatchUnaffected:
    def test_spanish_pack_exact_matches(self, spanish_keywords, spanish_builtins):
        mapper = TokenMapper(spanish_keywords, spanish_builtins)
        assert mapper.get_keyword("def") == spanish_keywords["def"]
        assert mapper.get_builtin("print") == spanish_builtins["print"]

    def test_english_identity_pack_exact(self):
        mapper = TokenMapper({"def": "def"}, {"print": "print"})
        assert mapper.get_keyword("def") == "def"


class TestReverseCollisionSafety:
    def test_reverse_lossless_roundtrips(self):
        mapper = TokenMapper({"def": "definir"}, {"print": "imprimir"})
        rev = mapper.reverse()
        assert rev.get_keyword("definir") == "def"
        assert rev.get_builtin("imprimir") == "print"

    def test_reverse_raises_on_duplicate_target(self):
        mapper = TokenMapper({"def": "x", "class": "x"}, {"print": "p"})
        with pytest.raises(ValueError, match="multiple source keys map to the same"):
            mapper.reverse()

    def test_reverse_duplicate_in_builtins_raises(self):
        mapper = TokenMapper({"def": "d"}, {"print": "y", "input": "y"})
        with pytest.raises(ValueError, match="builtin"):
            mapper.reverse()


class TestNfkcIndexCollisionLogged:
    def test_collision_logs_warning(self, caplog):
        fullwidth_if = "ｉｆ"  # NFKC -> "if"
        with caplog.at_level(logging.WARNING):
            TokenMapper({"if": "si", fullwidth_if: "OTHER"}, {"print": "p"})
        assert any("NFKC normalization collision" in r.message for r in caplog.records)
