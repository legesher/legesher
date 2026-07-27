"""Tests for the canonical translation selection rule (CORE-1400).

The selection rule is the publish gate between the (intentionally messy)
``translations`` candidate pool and the (always clean)
``selected_translations`` table that packs are exported from.
"""

import pytest

from legesher_i18n.selection import (
    SOURCE_TRUST,
    SelectionResult,
    confidence_score,
    is_valid_pack_value,
    select_canonical,
    source_trust_rank,
)


class TestValidityGate:
    """Rule 1: only valid Python identifiers may be published."""

    def test_clean_identifier_passes(self):
        assert is_valid_pack_value("arithmeticerror", "erreurarithmétique")

    def test_space_containing_value_rejected(self):
        # The exact defect class CORE-1400 exists to stop: raw Aya output.
        assert not is_valid_pack_value("arithmeticerror", "erreur arithmétique")

    def test_empty_and_whitespace_rejected(self):
        assert not is_valid_pack_value("def", "")
        assert not is_valid_pack_value("def", "  définir")
        assert not is_valid_pack_value("def", "définir ")

    def test_non_string_rejected(self):
        assert not is_valid_pack_value("def", None)
        assert not is_valid_pack_value("def", 3)

    def test_punctuation_rejected(self):
        assert not is_valid_pack_value("def", "défi-nir")
        assert not is_valid_pack_value("def", "def\\inir")

    def test_unicode_identifiers_pass(self):
        # PEP 3131: non-Latin scripts are first-class identifiers.
        assert is_valid_pack_value("class", "كائن")
        assert is_valid_pack_value("type", "型")
        assert is_valid_pack_value("print", "छापें")

    def test_except_star_soft_keyword_forms(self):
        # 'except*' translations may carry the trailing star...
        assert is_valid_pack_value("except*", "except*")
        assert is_valid_pack_value("except*", "excepter*")
        # ...or omit it (both forms ship today, e.g. ru 'кроме').
        assert is_valid_pack_value("except*", "кроме")
        # But a star on a non-soft-keyword term is invalid.
        assert not is_valid_pack_value("except", "excepter*")

    def test_underscore_compounds_pass(self):
        assert is_valid_pack_value("type", "tipus_")
        assert is_valid_pack_value("__import__", "__importer__")


class TestSourceTrust:
    def test_order_is_human_before_machine(self):
        assert SOURCE_TRUST.index("community_review") < SOURCE_TRUST.index("aya")
        assert SOURCE_TRUST.index("community") < SOURCE_TRUST.index("claude")
        assert SOURCE_TRUST.index("yaml_pack") < SOURCE_TRUST.index("aya")

    def test_unknown_source_ranks_last(self):
        assert source_trust_rank("some-new-source") == len(SOURCE_TRUST)
        assert source_trust_rank(None) == len(SOURCE_TRUST)
        assert source_trust_rank("aya") < source_trust_rank("unknown-thing")

    def test_confidence_scores(self):
        assert confidence_score("high") > confidence_score("medium")
        assert confidence_score("medium") > confidence_score("low")
        assert confidence_score("low") > confidence_score(None)
        assert confidence_score("HIGH") == confidence_score("high")


class TestShippedPackAnchor:
    """Rule 2: a valid shipped pack value is canonical."""

    def test_pack_value_beats_higher_confidence_candidate(self):
        # The exact CORE-1400 scenario: dirty aya candidate has 'high'
        # confidence, the shipped pack carries the cleaned value.
        result = select_canonical(
            "arithmeticerror",
            candidates=[
                {
                    "translation": "erreur arithmétique",
                    "source": "aya",
                    "confidence": "high",
                },
                {
                    "translation": "erreurarithmétique",
                    "source": "yaml_pack",
                    "confidence": None,
                },
            ],
            pack_value="erreurarithmétique",
        )
        assert result == SelectionResult(
            translation="erreurarithmétique",
            reason="shipped-pack-value",
            source="yaml_pack",
        )

    def test_pack_value_wins_even_without_matching_candidate(self):
        # su ships 'iwal*' for except* but only 'iwal' exists as a
        # candidate; the shipped value still anchors.
        result = select_canonical(
            "except*",
            candidates=[{"translation": "iwal", "source": "yaml-import"}],
            pack_value="iwal*",
        )
        assert result is not None
        assert result.translation == "iwal*"
        assert result.reason == "shipped-pack-value"
        assert result.source is None

    def test_invalid_pack_value_does_not_anchor(self):
        # If a pack value ever fails the gate it must not be re-selected.
        result = select_canonical(
            "print",
            candidates=[{"translation": "imprimer", "source": "community"}],
            pack_value="im primer",
        )
        assert result is not None
        assert result.translation == "imprimer"
        assert result.reason.startswith("source-trust:")


class TestSourceTrustSelection:
    """Rule 3: without a pack anchor, best valid candidate wins."""

    def test_dirty_candidates_never_selected(self):
        result = select_canonical(
            "arithmeticerror",
            candidates=[
                {
                    "translation": "erreur arithmétique",
                    "source": "aya",
                    "confidence": "high",
                },
                {
                    "translation": "erreurarithmétique",
                    "source": "yaml-import",
                    "confidence": "high",
                },
            ],
        )
        assert result is not None
        assert result.translation == "erreurarithmétique"

    def test_trusted_source_beats_confident_machine_output(self):
        result = select_canonical(
            "while",
            candidates=[
                {"translation": "mientras", "source": "community", "confidence": "low"},
                {"translation": "durante", "source": "aya", "confidence": "high"},
            ],
        )
        assert result is not None
        assert result.translation == "mientras"
        assert result.reason == "source-trust:community/low"

    def test_confidence_breaks_source_ties(self):
        result = select_canonical(
            "while",
            candidates=[
                {"translation": "durante", "source": "aya", "confidence": "low"},
                {"translation": "mientras", "source": "aya", "confidence": "high"},
            ],
        )
        assert result is not None
        assert result.translation == "mientras"

    def test_deterministic_lexicographic_tiebreak(self):
        candidates = [
            {"translation": "zeta", "source": "aya", "confidence": "high"},
            {"translation": "alfa", "source": "aya", "confidence": "high"},
        ]
        result = select_canonical("while", candidates=candidates)
        assert result is not None
        assert result.translation == "alfa"
        # Same result regardless of candidate order.
        result2 = select_canonical("while", candidates=list(reversed(candidates)))
        assert result2 is not None
        assert result2.translation == "alfa"

    def test_no_valid_candidate_returns_none(self):
        # Rule 4: never fall back to a dirty value.
        result = select_canonical(
            "arithmeticerror",
            candidates=[
                {"translation": "erreur arithmétique", "source": "aya"},
                {"translation": "arith metic", "source": "community"},
            ],
        )
        assert result is None

    def test_empty_candidates_returns_none(self):
        assert select_canonical("def", candidates=[]) is None


class TestSelectedTranslationsGate:
    """The DB layer enforces the gate on write (set_selected)."""

    @pytest.fixture
    def db(self, tmp_path):
        from legesher_i18n.db import TranslationDatabase

        db = TranslationDatabase(db_path=str(tmp_path / "test.db"))
        conn = db._get_connection()
        conn.executemany(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            [("es", "Spanish", "Español"), ("fr", "French", "Français")],
        )
        conn.commit()
        return db

    def test_set_selected_rejects_invalid_identifier(self, db):
        term_id = db.get_or_create_term("arithmeticerror", "python", "exception")
        with pytest.raises(ValueError, match="not a valid"):
            db.set_selected(
                term_id=term_id,
                language_code="fr",
                translation="erreur arithmétique",
            )

    def test_set_selected_accepts_clean_identifier(self, db):
        term_id = db.get_or_create_term("arithmeticerror", "python", "exception")
        assert db.set_selected(
            term_id=term_id,
            language_code="fr",
            translation="erreurarithmétique",
        )

    def test_set_selected_allows_soft_keyword_star(self, db):
        term_id = db.get_or_create_term("except*", "python", "keyword")
        assert db.set_selected(
            term_id=term_id, language_code="fr", translation="excepter*"
        )

    def test_same_name_terms_do_not_collide(self, db):
        # 'type' exists both as the 3.10 builtin and the 3.12 soft
        # keyword. The same surface token mapping to the same translation
        # in both slots is NOT a round-trip collision.
        builtin_id = db.get_or_create_term("type", "python", "builtin_type")
        keyword_id = db.get_or_create_term(
            "type", "python", "keyword", allow_duplicate_name=True
        )
        assert builtin_id != keyword_id
        db.set_selected(term_id=builtin_id, language_code="es", translation="tipo")
        # Must not raise a collision error.
        db.set_selected(term_id=keyword_id, language_code="es", translation="tipo")
        assert db.find_collisions(language_code="es") == []

    def test_distinct_terms_still_collide(self, db):
        id1 = db.get_or_create_term("if", "python", "keyword")
        id2 = db.get_or_create_term("while", "python", "keyword")
        db.set_selected(term_id=id1, language_code="es", translation="si")
        with pytest.raises(ValueError, match="Collision"):
            db.set_selected(term_id=id2, language_code="es", translation="si")
