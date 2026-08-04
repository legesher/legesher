"""Tests for score-tiered fuzzy matching (CORE-411 item 5).

suggest() surfaces near-identical cached segments as scored candidates.
Suggestions are NEVER applied automatically: lookup() answers only from
the exact (node, hash, lang) key, so anything below identity must pass
through a human or an explicit add().
"""

import pytest

from legesher_core.translation_memory.model import (
    DEFAULT_FUZZY_THRESHOLD,
    TranslationMemory,
)


class TestSuggest:
    def build_store(self):
        tm = TranslationMemory()
        tm.add(
            "n000001",
            "# compute the yearly tax total",
            "es",
            "# calcular el total anual de impuestos",
            minted_by="model",
        )
        tm.add(
            "n000002",
            "# something completely different",
            "es",
            "# algo completamente distinto",
            minted_by="model",
        )
        tm.add(
            "n000003",
            "# compute the yearly tax totals",
            "ar",
            "# احسب مجاميع الضرائب السنوية",
            minted_by="human",
        )
        return tm

    def test_default_threshold_is_conservative(self):
        assert DEFAULT_FUZZY_THRESHOLD == 0.85

    def test_near_identical_segment_is_suggested_with_score(self):
        tm = self.build_store()
        suggestions = tm.suggest("# compute the yearly tax totals", "es")
        assert len(suggestions) == 1
        score, segment = suggestions[0]
        assert segment.node_id == "n000001"
        assert 0.85 <= score < 1.0

    def test_weak_matches_are_excluded_by_threshold(self):
        tm = self.build_store()
        suggestions = tm.suggest("# compute the yearly tax totals", "es")
        assert all(s.node_id != "n000002" for _, s in suggestions)

    def test_threshold_is_configurable(self):
        tm = self.build_store()
        everything = tm.suggest("# compute the yearly tax totals", "es", threshold=0.0)
        assert {s.node_id for _, s in everything} == {"n000001", "n000002"}
        store_level = TranslationMemory(fuzzy_threshold=0.99)
        store_level.add("n000001", "# hello there", "es", "# hola", minted_by="model")
        assert store_level.suggest("# hello therX", "es") == []

    def test_suggestions_are_language_scoped(self):
        tm = self.build_store()
        suggestions = tm.suggest("# compute the yearly tax totals", "es")
        assert all(s.target_lang == "es" for _, s in suggestions)

    def test_suggestions_sorted_by_score_descending(self):
        tm = TranslationMemory()
        tm.add("n000001", "# compute the tax", "es", "# a", minted_by="model")
        tm.add("n000002", "# compute the taxes now", "es", "# b", minted_by="model")
        suggestions = tm.suggest("# compute the tax", "es", threshold=0.0)
        scores = [score for score, _ in suggestions]
        assert scores == sorted(scores, reverse=True)
        assert suggestions[0][1].node_id == "n000001"
        assert suggestions[0][0] == pytest.approx(1.0)

    def test_long_prose_near_identical_suggestion_surfaces(self):
        """Regression: difflib's autojunk heuristic demotes any character
        appearing in >1% of a sequence longer than 199 chars to junk. On
        repetitive long prose (boilerplate comments, docstrings) that can
        leave no anchor characters at all, cratering a near-identical
        segment to ~0.14 and silently disabling fuzzy matching for the
        highest-value segment class. suggest() must pass autojunk=False:
        this probe scores 0.1411 with autojunk on, 0.9834 without."""
        base = "# " + " ".join(["update the totals table for the yearly tax data"] * 5)
        assert len(base) > 200
        edited = base.replace("yearly", "annual", 1)
        tm = TranslationMemory()
        tm.add("n000001", base, "es", "# traducción larga", minted_by="model")
        suggestions = tm.suggest(edited, "es")
        assert len(suggestions) == 1
        score, segment = suggestions[0]
        assert segment.node_id == "n000001"
        assert score >= 0.85

    def test_suggest_counter_increments_per_surfaced_suggestion(self):
        tm = self.build_store()
        tm.suggest("# compute the yearly tax totals", "es")
        assert tm.fuzzy_suggestions == 1
        tm.suggest("# no such prose anywhere", "es")
        assert tm.fuzzy_suggestions == 1

    def test_suggest_does_not_mutate_segments_or_hit_counters(self):
        tm = self.build_store()
        before = tm.to_dict()
        tm.suggest("# compute the yearly tax totals", "es")
        assert tm.to_dict() == before
        assert (tm.hits, tm.misses) == (0, 0)


class TestNeverSilentlyReused:
    """The load-bearing property: a fuzzy match is a suggestion, not an
    answer. Nothing below the exact key is ever applied automatically."""

    def test_near_identical_source_still_misses_lookup(self):
        tm = TranslationMemory()
        tm.add("n000001", "# compute the yearly tax", "es", "# c", minted_by="model")
        edited = "# compute the yearly tax!"
        # A high-scoring fuzzy candidate exists...
        suggestions = tm.suggest(edited, "es")
        assert suggestions and suggestions[0][0] >= 0.85
        # ...and lookup STILL misses: the suggestion was not auto-applied.
        assert tm.lookup("n000001", edited, "es") is None
        assert tm.misses == 1
        # Suggesting again yields the same candidate — nothing was cached.
        assert [s for _, s in tm.suggest(edited, "es")] == [s for _, s in suggestions]

    def test_reuse_requires_an_explicit_add(self):
        tm = TranslationMemory()
        tm.add("n000001", "# compute the yearly tax", "es", "# c", minted_by="model")
        edited = "# compute the yearly tax!"
        (score, candidate) = tm.suggest(edited, "es")[0]
        assert score < 1.0
        # The caller decides: only an explicit add() promotes the candidate.
        tm.add(
            "n000001",
            edited,
            "es",
            candidate.translated_text,
            minted_by="human",
            attribution="reviewed fuzzy suggestion",
        )
        hit = tm.lookup("n000001", edited, "es")
        assert hit is not None
        assert hit.minted_by == "human"
