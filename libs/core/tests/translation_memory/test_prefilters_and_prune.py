"""suggest() prefilters (CORE-1709) and dead-node pruning (CORE-1708).

The prefilters must be *transparent*: they exist to skip work, never to
change an answer. Every gate is an exact upper bound on the score, so
the suggestion set is identical to the unfiltered scan — asserted here
against a reference implementation rather than assumed.
"""

import random
from difflib import SequenceMatcher

import pytest

from legesher_core.translation_memory import (
    DEFAULT_STALE_HISTORY,
    LONG_SEGMENT_CHARS,
    SHORT_SEGMENT_CHARS,
    SHORT_SEGMENT_FLOOR,
    TranslationMemory,
    TranslationMemoryDocument,
    effective_threshold,
    length_band,
    live_node_ids,
)
from legesher_core.translation_memory.model import normalize_text


def reference_suggest(store, source_text, target_lang, floor):
    """The pre-CORE-1709 implementation, verbatim — the oracle."""
    needle = normalize_text(source_text)
    scored = []
    for segment in store.segments.values():
        if segment.target_lang != target_lang:
            continue
        score = SequenceMatcher(a=needle, b=segment.source_text, autojunk=False).ratio()
        if score >= floor:
            scored.append((score, segment))
    scored.sort(key=lambda pair: (-pair[0], pair[1].key))
    return scored


WORDS = "compute the tax rate for each customer record in a batch job".split()


def corpus(size: int, seed: int = 1709) -> TranslationMemory:
    rng = random.Random(seed)
    store = TranslationMemory()
    for index in range(size):
        text = "# " + " ".join(rng.choice(WORDS) for _ in range(rng.randint(2, 14)))
        store.add(f"n{index:06d}", text, "es", f"trad {index}", minted_by="model")
    return store


class TestLengthBand:
    @pytest.mark.parametrize("floor", [0.6, 0.75, 0.85, 0.95])
    @pytest.mark.parametrize("needle_length", [5, 20, 80, 300])
    def test_band_never_excludes_a_reachable_candidate(self, floor, needle_length):
        """The bound must be exact: any length outside the band is
        genuinely unreachable, for every possible content."""
        low, high = length_band(needle_length, floor)
        for candidate_length in range(1, needle_length * 4 + 8):
            # The best a candidate of this length could ever score.
            best = (
                2
                * min(needle_length, candidate_length)
                / (needle_length + candidate_length)
            )
            if best >= floor:
                assert low <= candidate_length <= high, (
                    f"length {candidate_length} could reach {best:.3f} "
                    f"but the band is [{low}, {high}]"
                )

    def test_band_is_narrower_than_everything(self):
        low, high = length_band(20, 0.85)
        assert low > 1 and high < 100


class TestEffectiveThreshold:
    def test_short_segments_are_gated(self):
        assert effective_threshold(0.85, 8) == SHORT_SEGMENT_FLOOR

    def test_long_segments_are_untouched(self):
        assert effective_threshold(0.85, 200) == 0.85

    def test_scaling_is_monotonic(self):
        values = [effective_threshold(0.85, n) for n in range(1, 80)]
        assert values == sorted(values, reverse=True)

    def test_never_loosens_an_explicit_threshold(self):
        for length in (1, 15, 40, 500):
            assert effective_threshold(0.99, length) >= 0.99

    def test_boundaries(self):
        assert effective_threshold(0.85, SHORT_SEGMENT_CHARS) == SHORT_SEGMENT_FLOOR
        assert effective_threshold(0.85, LONG_SEGMENT_CHARS) == 0.85


class TestShortStringFloor:
    def test_step_1_vs_step_2_is_not_suggested(self):
        """The review-note case: 0.875, semantically a different step."""
        store = TranslationMemory()
        store.add("n000001", "# step 1", "es", "# paso 1", minted_by="model")
        assert store.suggest("# step 2", "es") == []

    def test_a_typo_fix_is_still_suggested(self):
        """Same length class, higher score — the floor sits between."""
        store = TranslationMemory()
        store.add("n000001", "# hello", "es", "# hola", minted_by="model")
        assert store.suggest("# helo", "es")

    def test_a_genuine_edit_is_still_suggested(self):
        store = TranslationMemory()
        store.add("n000001", "# compute the tax", "es", "# calcular", minted_by="model")
        assert store.suggest("# compute the tax rate", "es")

    def test_scaling_can_be_disabled(self):
        store = TranslationMemory()
        store.add("n000001", "# step 1", "es", "# paso 1", minted_by="model")
        assert store.suggest("# step 2", "es", scale_floor=False)


class TestPrefiltersAreTransparent:
    @pytest.mark.parametrize("floor", [0.6, 0.7, 0.85, 0.9])
    def test_results_match_the_unfiltered_scan(self, floor):
        store = corpus(400)
        needles = [
            segment.source_text for segment in list(store.segments.values())[:25]
        ]
        # Mutate each needle so the corpus is exercised, not just hit.
        rng = random.Random(11)
        for needle in needles:
            chars = list(needle)
            chars[rng.randrange(len(chars))] = "x"
            mutated = "".join(chars)
            expected = reference_suggest(store, mutated, "es", floor)
            actual = store.suggest(mutated, "es", threshold=floor, scale_floor=False)
            assert [(round(s, 12), seg.key) for s, seg in actual] == [
                (round(s, 12), seg.key) for s, seg in expected
            ]

    def test_exact_matches_still_score_one(self):
        store = corpus(120)
        target = next(iter(store.segments.values()))
        top = store.suggest(target.source_text, "es", scale_floor=False)[0]
        assert top[0] == 1.0

    def test_other_languages_are_still_excluded(self):
        store = TranslationMemory()
        store.add("n000001", "# a comment here", "fr", "# un", minted_by="model")
        assert store.suggest("# a comment here", "es") == []

    def test_stale_segments_are_still_offered(self):
        store = TranslationMemory()
        store.add("n000001", "# a comment here", "es", "# un", minted_by="model")
        store.invalidate_node("n000001")
        assert store.suggest("# a comment here", "es")

    def test_counter_still_increments(self):
        store = TranslationMemory()
        store.add("n000001", "# a comment here", "es", "# un", minted_by="model")
        store.suggest("# a comment here", "es")
        assert store.fuzzy_suggestions == 1


class TestPrune:
    def _store(self) -> TranslationMemory:
        store = TranslationMemory(file="src/tax.py")
        for index in range(1, 6):
            store.add(
                f"n{index:06d}",
                f"# comment number {index} in the file",
                "es",
                f"# comentario {index}",
                minted_by="model",
                minted_at=f"2026-08-0{index}T00:00:00+00:00",
            )
        return store

    def test_dead_node_segments_are_demoted(self):
        store = self._store()
        stats = store.prune({"n000001", "n000002"})
        assert stats.demoted == 3
        statuses = {
            segment.node_id: segment.status for segment in store.segments.values()
        }
        assert statuses["n000001"] == "active"
        assert statuses["n000005"] == "stale"

    def test_live_segments_are_untouched(self):
        store = self._store()
        live = next(
            segment
            for segment in store.segments.values()
            if segment.node_id == "n000001"
        )
        snapshot = live.to_dict()
        store.prune({"n000001"})
        assert live.to_dict() == snapshot

    def test_replay_for_live_nodes_is_unchanged(self):
        store = self._store()
        live = {"n000001", "n000002"}
        before = {
            key: segment.to_dict()
            for key, segment in store.segments.items()
            if segment.node_id in live
        }
        store.prune(live)
        after = {
            key: segment.to_dict()
            for key, segment in store.segments.items()
            if segment.node_id in live
        }
        assert before == after

    def test_dead_segments_stay_reachable_as_fuzzy_history(self):
        """The retention decision: a deleted docstring often returns, and
        its old translation is then the best candidate available."""
        store = self._store()
        store.prune({"n000001"})
        assert store.suggest("# comment number 5 in the file", "es")

    def test_dead_segments_never_hit_lookup(self):
        store = self._store()
        store.prune({"n000001"})
        assert store.lookup("n000005", "# comment number 5 in the file", "es") is None

    def test_history_is_capped(self):
        store = self._store()
        stats = store.prune(set(), keep_history=2)
        assert stats.demoted == 5
        assert stats.dropped == 3
        assert stats.retained == 2
        assert len(store.segments) == 2

    def test_cap_keeps_the_most_recent(self):
        store = self._store()
        store.prune(set(), keep_history=2)
        kept = sorted(segment.node_id for segment in store.segments.values())
        assert kept == ["n000004", "n000005"]

    def test_zero_history_drops_everything_dead(self):
        store = self._store()
        stats = store.prune({"n000001"}, keep_history=0)
        assert len(store.segments) == 1
        assert stats.dropped == 4

    def test_artifact_shrinks(self):
        document = TranslationMemoryDocument()
        document.files["src/tax.py"] = self._store()
        before = len(document.to_dict()["files"]["src/tax.py"]["segments"])
        document.prune({"src/tax.py": {"n000001"}}, keep_history=1)
        after = len(document.to_dict()["files"]["src/tax.py"]["segments"])
        assert after < before

    def test_prune_is_idempotent(self):
        store = self._store()
        store.prune({"n000001"}, keep_history=2)
        snapshot = store.to_dict()
        store.prune({"n000001"}, keep_history=2)
        assert store.to_dict() == snapshot

    def test_nothing_to_do_reports_zero(self):
        store = self._store()
        stats = store.prune({f"n{i:06d}" for i in range(1, 6)})
        assert (stats.demoted, stats.dropped) == (0, 0)

    def test_default_cap(self):
        assert DEFAULT_STALE_HISTORY == 200


class TestDocumentPrune:
    def test_aggregates_across_files(self):
        document = TranslationMemoryDocument()
        for path in ("src/a.py", "src/b.py"):
            store = document.get_or_create(path)
            store.add("n000001", "# a comment here", "es", "# x", minted_by="model")
            store.add("n000002", "# another comment", "es", "# y", minted_by="model")
        stats = document.prune({"src/a.py": {"n000001"}, "src/b.py": {"n000001"}})
        assert stats.demoted == 2

    def test_a_file_absent_from_the_map_has_every_segment_dead(self):
        """The file was deleted or renamed — its store should collapse to
        bounded history rather than persist in full."""
        document = TranslationMemoryDocument()
        store = document.get_or_create("src/gone.py")
        store.add("n000001", "# a comment here", "es", "# x", minted_by="model")
        stats = document.prune({})
        assert stats.demoted == 1

    def test_live_node_ids_reads_the_register_map(self, mapper):
        from legesher_core.register_map import RegisterMapDocument, build_register_map

        document = RegisterMapDocument()
        document.files["src/tax.py"] = build_register_map(
            "def f():\n    # hi\n    return 1\n", mapper, file="src/tax.py"
        )
        live = live_node_ids(document)
        assert set(live) == {"src/tax.py"}
        assert live["src/tax.py"] == set(document.files["src/tax.py"].entries)
