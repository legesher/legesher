"""Tests for the query-before-model API and precise invalidation
(CORE-411 items 2 and 4).

lookup() answers exactly or misses — never fuzzily. Counters instrument
the hit rate; invalidation is entry-scoped: a source edit or a map
correction affects only the segments it names, and stale segments are
retained as history, never returned.
"""

import pytest

from legesher_core.translation_memory.model import TranslationMemory

# ---------------------------------------------------------------------------
# Exact lookup + counters
# ---------------------------------------------------------------------------


class TestLookup:
    def test_exact_hit_returns_cached_translation(self):
        tm = TranslationMemory()
        tm.add("n000001", "# compute the tax", "es", "# calcular", minted_by="model")
        segment = tm.lookup("n000001", "# compute the tax", "es")
        assert segment is not None
        assert segment.translated_text == "# calcular"
        assert tm.hits == 1
        assert tm.misses == 0

    def test_hit_matches_canonically_equivalent_source(self):
        """compare-NFC: a decomposed rendering of the same source hits."""
        tm = TranslationMemory()
        tm.add("n000001", "# café", "es", "# cafetería", minted_by="model")
        assert tm.lookup("n000001", "# café", "es") is not None  # decomposed

    def test_unknown_node_misses(self):
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        assert tm.lookup("n000099", "# hello", "es") is None
        assert tm.misses == 1

    def test_other_language_misses(self):
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        assert tm.lookup("n000001", "# hello", "ar") is None
        assert tm.misses == 1

    def test_same_text_under_other_node_is_not_a_hit(self):
        """The key is node-scoped: identical prose on a different node is
        fuzzy-suggestion territory, never an exact hit."""
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        assert tm.lookup("n000002", "# hello", "es") is None

    def test_stats_dict_exposes_counters_and_hit_rate(self):
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        tm.lookup("n000001", "# hello", "es")
        tm.lookup("n000001", "# hello", "es")
        tm.lookup("n000001", "# edited", "es")
        tm.suggest("# helo", "es")
        stats = tm.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["lookups"] == 3
        assert stats["hit_rate"] == pytest.approx(2 / 3)
        assert stats["fuzzy_suggestions"] == 1
        assert stats["segments"] == 1

    def test_hit_rate_is_none_before_any_lookup(self):
        assert TranslationMemory().stats()["hit_rate"] is None

    def test_lookup_never_mutates_store_except_counters(self):
        tm = TranslationMemory()
        tm.add("n000001", "# hello", "es", "# hola", minted_by="model")
        before = tm.to_dict()
        tm.lookup("n000001", "# hello", "es")
        tm.lookup("n000001", "# edited", "es")
        tm.lookup("n000042", "# hello", "ar")
        assert tm.to_dict() == before
        assert (tm.hits, tm.misses) == (1, 2)


# ---------------------------------------------------------------------------
# Precise invalidation — source edits (hash mismatch)
# ---------------------------------------------------------------------------


class TestSourceEditInvalidation:
    def test_edited_source_misses_but_history_is_retained(self):
        tm = TranslationMemory()
        original = tm.add(
            "n000001", "# compute the tax", "es", "# calcular", minted_by="model"
        )
        # The source prose was edited: the hash no longer matches.
        assert tm.lookup("n000001", "# compute the tax rate", "es") is None
        assert tm.misses == 1
        # The stale segment is retained as history for fuzzy matching.
        assert original.key in tm.segments
        suggestions = tm.suggest("# compute the tax rate", "es")
        assert [s for _, s in suggestions] == [original]

    def test_retranslation_after_edit_keeps_old_segment_as_history(self):
        tm = TranslationMemory()
        old = tm.add("n000001", "# old text here", "es", "# viejo", minted_by="model")
        new = tm.add("n000001", "# old text here!", "es", "# nuevo", minted_by="model")
        assert old.key != new.key
        assert len(tm.segments) == 2
        # Only the segment matching the current source is returned.
        hit = tm.lookup("n000001", "# old text here!", "es")
        assert hit is new


# ---------------------------------------------------------------------------
# Precise invalidation — map corrections (entry-scoped, no over-invalidation)
# ---------------------------------------------------------------------------


class TestMapCorrectionInvalidation:
    def build_store(self):
        tm = TranslationMemory()
        tm.add("n000001", "# tax helper", "es", "# ayudante-es", minted_by="model")
        tm.add("n000001", "# tax helper", "ar", "# ayudante-ar", minted_by="model")
        tm.add("n000002", "# unrelated", "es", "# sin-relacion", minted_by="model")
        return tm

    def test_invalidate_node_is_lang_scoped(self):
        tm = self.build_store()
        count = tm.invalidate_node("n000001", target_lang="es")
        assert count == 1
        # The corrected node+lang no longer hits...
        assert tm.lookup("n000001", "# tax helper", "es") is None
        # ...but the same node in another language still does,
        assert tm.lookup("n000001", "# tax helper", "ar") is not None
        # ...and unrelated entries' cached prose is untouched.
        assert tm.lookup("n000002", "# unrelated", "es") is not None

    def test_invalidate_node_all_languages(self):
        tm = self.build_store()
        count = tm.invalidate_node("n000001")
        assert count == 2
        assert tm.lookup("n000001", "# tax helper", "es") is None
        assert tm.lookup("n000001", "# tax helper", "ar") is None
        assert tm.lookup("n000002", "# unrelated", "es") is not None

    def test_stale_segments_are_history_not_answers(self):
        tm = self.build_store()
        tm.invalidate_node("n000001", target_lang="es")
        stale = [s for s in tm.segments.values() if s.status == "stale"]
        assert len(stale) == 1
        # Retained for fuzzy matching...
        suggestions = tm.suggest("# tax helper", "es")
        assert stale[0] in [s for _, s in suggestions]
        # ...but lookup never returns a stale segment.
        assert tm.lookup("n000001", "# tax helper", "es") is None

    def test_invalidation_survives_serialization(self):
        tm = self.build_store()
        tm.invalidate_node("n000001", target_lang="es")
        restored = TranslationMemory.from_dict(tm.to_dict())
        assert restored.lookup("n000001", "# tax helper", "es") is None
        assert restored.lookup("n000001", "# tax helper", "ar") is not None

    def test_fresh_translation_replaces_stale_segment(self):
        tm = self.build_store()
        tm.invalidate_node("n000001", target_lang="es")
        tm.add("n000001", "# tax helper", "es", "# corregido", minted_by="human")
        hit = tm.lookup("n000001", "# tax helper", "es")
        assert hit is not None
        assert hit.translated_text == "# corregido"
        assert hit.status == "active"
