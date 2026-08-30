"""suggest() prefilters (CORE-1709).

The dead-node pruning half (CORE-1708) moved with the map family
[CORE-2011][CORE-2027]: live-ness is defined by the register map.

The prefilters must be *transparent*: they exist to skip work, never to
change an answer. Every gate is an exact upper bound on the score, so
the suggestion set is identical to the unfiltered scan — asserted here
against a reference implementation rather than assumed.
"""

import random
from difflib import SequenceMatcher

import pytest

from legesher_core.translation_memory import (
    LONG_SEGMENT_CHARS,
    SHORT_SEGMENT_CHARS,
    SHORT_SEGMENT_FLOOR,
    TranslationMemory,
    effective_threshold,
    length_band,
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
