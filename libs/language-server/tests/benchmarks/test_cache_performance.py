"""Performance benchmarks for CORE-446 cache improvements.

This validates that refactored code meets performance targets:
- Cold cache pack load: <500ms (relaxed for CI; local dev typically <50ms)
- Warm cache pack load: served from the lru_cache (asserted by its hit
  count), at least WARM_SPEEDUP_FLOOR times faster than the cold load
  measured in the same test, and under WARM_CEILING_MS
- Cache hit rate: >95% after warmup
- Completion latency with warm cache: <50ms

Warm-path assertions are by state first, timing second (CORE-2129). A
cached load is a dict hit that takes microseconds, so the former sub-10ms
absolute ceilings measured the runner's scheduling jitter rather than the
cache: one preempted timer crossed them. Each warm test now asserts that the
lru_cache hit count moved (the proof the cache path was taken), then compares
the warm timing with a cold load taken in the same test on the same machine,
so the bound scales with the runner, plus an absolute ceiling as a backstop.

Run with: uv run pytest tests/benchmarks/test_cache_performance.py -v -s
"""

import time

import pytest

#: Backstop only. The proof that a warm load took the cache path is the
#: lru_cache hit count (:func:`cache_hits`), asserted by state in every warm
#: test. A timing ratio cannot prove it: ``load`` is lru_cache'd but pack
#: discovery is a separate per-instance cache, so a load that misses the
#: lru_cache while keeping its discovery is a parse-only reload, about 10x
#: faster than the full cold load it is compared with (about 4.6 ms vs 45 ms
#: here) and past any floor a jittery runner can hold. 2x is therefore a
#: sanity bound on the warm side only (local ratios run 800x to 90,000x),
#: chosen so that a single 12 ms scheduler preemption on the warm read
#: cannot fail a test against a 45 ms cold reference; it is not the cache
#: assertion.
WARM_SPEEDUP_FLOOR = 2

#: Backstop for the relative bound: however slow the cold load was, a cache
#: hit that takes longer than this is broken regardless of the ratio.
WARM_CEILING_MS = 100


def assert_warm(warm_ms: float, cold_ms: float, what: str) -> None:
    """Assert a warm timing against its cold reference and the ceiling."""
    bound_ms = cold_ms / WARM_SPEEDUP_FLOOR
    assert warm_ms < bound_ms, (
        f"{what} took {warm_ms:.3f}ms warm vs {cold_ms:.2f}ms cold; "
        f"expected at least {WARM_SPEEDUP_FLOOR}x faster (<{bound_ms:.2f}ms)"
    )
    assert warm_ms < WARM_CEILING_MS, (
        f"{what} took {warm_ms:.3f}ms warm, expected <{WARM_CEILING_MS}ms"
    )


def cache_hits() -> int:
    """The lru_cache hit count for ``LanguagePackLoader.load``.

    ``load`` is decorated on the unbound method, so one cache serves every
    loader instance (``self`` is part of the key) and this count is
    class-wide. ``clear_cache()`` on any instance resets it.
    """
    from legesher_i18n import LanguagePackLoader

    return LanguagePackLoader.load.cache_info().hits


def assert_cache_hit(hits_before: int, what: str, expected: int = 1) -> None:
    """Assert at least ``expected`` lru_cache hits landed since ``hits_before``.

    This is the cache assertion; :func:`assert_warm` is only the backstop.
    """
    gained = cache_hits() - hits_before
    assert gained >= expected, (
        f"{what} produced {gained} lru_cache hit(s), expected at least "
        f"{expected}: the load did not take the cache path"
    )


class TestLanguagePackLoaderCache:
    """Test LanguagePackLoader LRU cache performance (CORE-446)."""

    def test_cold_cache_pack_load(self):
        """Test first load of language pack (cold cache).

        Success Criteria:
            - First load completes in <500ms (relaxed for Windows CI)
            - Pack is successfully loaded
        """
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()

        # Clear cache to ensure cold start
        loader.clear_cache()

        # Measure cold load
        start = time.perf_counter()
        pack = loader.load(language="es", target="python", version="3.10")
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n{'=' * 60}")
        print("CORE-446: Cold cache pack load")
        print(f"{'=' * 60}")
        print(f"Time: {elapsed_ms:.2f}ms")
        print("Target: <500ms")
        print(f"Status: {'✓ PASS' if elapsed_ms < 500 else '✗ FAIL'}")
        print(f"Keywords loaded: {len(pack.keywords)}")
        print(f"{'=' * 60}\n")

        assert pack is not None
        assert len(pack.keywords) > 30
        assert elapsed_ms < 500, f"Cold load took {elapsed_ms:.2f}ms, expected <500ms"

    def test_warm_cache_pack_load(self):
        """Test cached load of language pack (warm cache).

        Success Criteria:
            - Cached load is at least WARM_SPEEDUP_FLOOR times faster than the
              cold load measured here, and under WARM_CEILING_MS
            - Pack is identical to first load
        """
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()

        # Cold reference: clear, then time the first load
        loader.clear_cache()
        start = time.perf_counter()
        pack1 = loader.load(language="es", target="python", version="3.10")
        cold_ms = (time.perf_counter() - start) * 1000

        # Measure cached load
        hits_before = cache_hits()
        start = time.perf_counter()
        pack2 = loader.load(language="es", target="python", version="3.10")
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n{'=' * 60}")
        print("CORE-446: Warm cache pack load")
        print(f"{'=' * 60}")
        print(f"Cold: {cold_ms:.2f}ms")
        print(f"Warm: {elapsed_ms:.3f}ms")
        print(f"Target: <{cold_ms / WARM_SPEEDUP_FLOOR:.2f}ms and <{WARM_CEILING_MS}ms")
        print(f"Cache speedup: {cold_ms / elapsed_ms if elapsed_ms > 0 else 'infinite'}x faster")
        print(f"{'=' * 60}\n")

        assert pack1 is pack2  # Should return same object from cache
        assert_cache_hit(hits_before, "Cached load")
        assert_warm(elapsed_ms, cold_ms, "Cached load")

    def test_cache_hit_rate(self):
        """Test cache hit rate after warmup.

        Success Criteria:
            - Cache hit rate >95% after warmup
            - All languages accessible from cache
        """
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()
        loader.clear_cache()

        languages = ["es", "ar", "zh", "fr", "en"]
        iterations = 20  # Simulates 20 completion requests

        # Warmup - load each language once
        for lang in languages:
            loader.load(language=lang, target="python", version="3.10")

        # Get initial cache stats
        initial_stats = loader.get_cache_stats()
        initial_hits = initial_stats.get("hits", 0)
        initial_misses = initial_stats.get("misses", 0)

        # Simulate realistic access pattern (repeated requests)
        for i in range(iterations):
            lang = languages[i % len(languages)]
            loader.load(language=lang, target="python", version="3.10")

        # Get final cache stats
        final_stats = loader.get_cache_stats()
        final_hits = final_stats.get("hits", 0)
        final_misses = final_stats.get("misses", 0)

        # Calculate hit rate for this test
        test_hits = final_hits - initial_hits
        test_misses = final_misses - initial_misses
        total_requests = test_hits + test_misses
        hit_rate = (test_hits / total_requests * 100) if total_requests > 0 else 0

        print(f"\n{'=' * 60}")
        print("CORE-446: Cache hit rate")
        print(f"{'=' * 60}")
        print(f"Total requests: {total_requests}")
        print(f"Cache hits: {test_hits}")
        print(f"Cache misses: {test_misses}")
        print(f"Hit rate: {hit_rate:.1f}%")
        print("Target: >95%")
        print(f"Status: {'✓ PASS' if hit_rate > 95 else '✗ FAIL'}")
        print(f"{'=' * 60}\n")

        assert hit_rate > 95, f"Cache hit rate {hit_rate:.1f}%, expected >95%"

    def test_multi_language_caching(self):
        """Test that multiple languages cache independently.

        Success Criteria:
            - Each language cached separately
            - No cache collisions
            - All packs accessible from cache
        """
        from legesher_i18n import LanguagePackLoader

        languages = ["es", "ar", "zh"]

        # Cold references on a throwaway loader, clearing before EACH load so
        # every language pays discovery + parse. Loading the three back to
        # back into one loader would charge discovery to es only, leaving ar
        # and zh with parse-only references a few ms above the warm path.
        reference = LanguagePackLoader()
        cold_ms = {}
        for lang in languages:
            reference.clear_cache()
            start = time.perf_counter()
            reference.load(language=lang, target="python", version="3.10")
            cold_ms[lang] = (time.perf_counter() - start) * 1000

        # Loader under test: clear once, load every language
        loader = LanguagePackLoader()
        loader.clear_cache()
        packs = {
            lang: loader.load(language=lang, target="python", version="3.10") for lang in languages
        }

        # Verify all cached
        for lang in languages:
            hits_before = cache_hits()
            start = time.perf_counter()
            cached_pack = loader.load(language=lang, target="python", version="3.10")
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert cached_pack is packs[lang]  # Same object from cache
            assert_cache_hit(hits_before, f"Cached load for {lang}")
            assert_warm(elapsed_ms, cold_ms[lang], f"Cached load for {lang}")

        # Verify packs are different
        assert packs["es"].keywords["def"] == "definir"
        assert packs["ar"].keywords["def"] == "تعريف"
        assert packs["zh"].keywords["def"] == "定义"

        print(f"\n{'=' * 60}")
        print("CORE-446: Multi-language caching")
        print(f"{'=' * 60}")
        print(f"Languages cached: {len(languages)}")
        print(f"All loads from cache: {WARM_SPEEDUP_FLOOR}x faster than cold, <{WARM_CEILING_MS}ms")
        print("Status: ✓ PASS")
        print(f"{'=' * 60}\n")


class TestKeywordDocsCache:
    """Test keyword_docs.py cache performance after refactoring."""

    def test_keyword_translation_with_cache(self):
        """Test keyword translation performance with LanguagePackLoader cache.

        Success Criteria:
            - Repeated lookups use cache
            - Second lookup at least WARM_SPEEDUP_FLOOR times faster than the
              first, and under WARM_CEILING_MS
        """
        from legesher_language_server.utils.keyword_docs import (
            KeywordDocumentation,
            _get_pack_loader,
        )

        docs = KeywordDocumentation()

        # keyword_docs holds a module-level loader. Clearing THAT instance also
        # drops its pack discovery, so the first lookup below is a full cold
        # load (discovery + parse) rather than a parse-only reload that lands
        # within a few ms of the warm path.
        _get_pack_loader().clear_cache()

        # First lookup (loads pack)
        start = time.perf_counter()
        result1 = docs.get_keyword_translation("def", "es")
        first_time = (time.perf_counter() - start) * 1000

        # Second lookup (should use cache). get_keyword_translation calls
        # loader.load on every call with no memo of its own, so the hit
        # count is the direct evidence.
        hits_before = cache_hits()
        start = time.perf_counter()
        result2 = docs.get_keyword_translation("class", "es")
        second_time = (time.perf_counter() - start) * 1000

        print(f"\n{'=' * 60}")
        print("CORE-446: keyword_docs cache performance")
        print(f"{'=' * 60}")
        print(f"First lookup: {first_time:.2f}ms")
        print(f"Second lookup: {second_time:.3f}ms")
        print(f"Target: <{first_time / WARM_SPEEDUP_FLOOR:.2f}ms and <{WARM_CEILING_MS}ms")
        print(f"{'=' * 60}\n")

        assert result1 == "definir"
        assert result2 == "clase"
        assert_cache_hit(hits_before, "Cached lookup")
        assert_warm(second_time, first_time, "Cached lookup")


class TestEnhancedIntelligenceProxyCache:
    """Test enhanced_intelligence.py cache performance after refactoring."""

    def test_keyword_map_initialization_with_cache(self):
        """Test EnhancedIntelligenceProxy initialization uses cached language pack.

        Success Criteria:
            - Second initialization at least WARM_SPEEDUP_FLOOR times faster
              than the first, and under WARM_CEILING_MS
            - Keyword maps are identical
        """
        from legesher_language_server.config import LanguageServerConfig
        from legesher_language_server.enhanced_intelligence import (
            EnhancedIntelligenceProxy,
            _get_pack_loader,
        )

        config = LanguageServerConfig(
            source_language="es", target_language="en", enhanced_intelligence_enabled=False
        )

        # Same reasoning as test_keyword_translation_with_cache: clear the
        # module-level loader so the first init is a full cold load.
        _get_pack_loader().clear_cache()

        # First initialization (loads pack)
        start = time.perf_counter()
        proxy1 = EnhancedIntelligenceProxy(config)
        first_time = (time.perf_counter() - start) * 1000

        # Second initialization (should use cache)
        hits_before = cache_hits()
        start = time.perf_counter()
        proxy2 = EnhancedIntelligenceProxy(config)
        second_time = (time.perf_counter() - start) * 1000

        print(f"\n{'=' * 60}")
        print("CORE-446: EnhancedIntelligenceProxy initialization cache performance")
        print(f"{'=' * 60}")
        print(f"First init: {first_time:.2f}ms")
        print(f"Second init: {second_time:.3f}ms")
        print(f"Speedup: {first_time / second_time if second_time > 0 else 'infinite'}x")
        bound_ms = first_time / WARM_SPEEDUP_FLOOR
        print(f"Target second init: <{bound_ms:.2f}ms and <{WARM_CEILING_MS}ms")
        print(f"{'=' * 60}\n")

        # Verify keyword maps are identical
        assert proxy1.translator.keyword_map == proxy2.translator.keyword_map
        assert len(proxy1.translator.keyword_map) > 30
        assert_cache_hit(hits_before, "Cached init")
        assert_warm(second_time, first_time, "Cached init")


class TestCompletionLatency:
    """Test end-to-end completion latency (CORE-446 primary goal)."""

    def test_completion_latency_warm_cache(self):
        """Test completion latency with warm cache.

        Success Criteria:
            - Completion latency <50ms with warm cache
            - Average latency at least WARM_SPEEDUP_FLOOR times faster than
              the cold lookup measured here
            - This is the primary CORE-446 performance target
        """
        from legesher_language_server.utils.keyword_docs import (
            KeywordDocumentation,
            _get_pack_loader,
        )

        docs = KeywordDocumentation()

        # Cold reference: a full cold lookup (see test_keyword_translation_with_cache)
        _get_pack_loader().clear_cache()
        start = time.perf_counter()
        docs.get_keyword_translation("def", "es")
        cold_ms = (time.perf_counter() - start) * 1000

        # Warmup cache
        for _ in range(3):
            docs.get_keyword_translation("def", "es")

        # Simulate 10 completion requests
        keywords = [
            "def",
            "class",
            "if",
            "for",
            "while",
            "return",
            "import",
            "try",
            "except",
            "with",
        ]
        latencies = []

        hits_before = cache_hits()
        for keyword in keywords:
            start = time.perf_counter()
            result = docs.get_keyword_translation(keyword, "es")
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
            assert result is not None  # Should find translation

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\n{'=' * 60}")
        print("CORE-446: Completion latency (PRIMARY TARGET)")
        print(f"{'=' * 60}")
        print(f"Requests: {len(keywords)}")
        print(f"Cold lookup: {cold_ms:.2f}ms")
        print(f"Avg latency: {avg_latency:.3f}ms")
        print(f"Max latency: {max_latency:.3f}ms")
        print(f"P95 latency: {p95_latency:.3f}ms")
        print("Target: <50ms per completion")
        print(f"Status: {'✓ PASS' if max_latency < 50 else '✗ FAIL'}")
        print(f"{'=' * 60}\n")

        assert max_latency < 50, f"Max latency {max_latency:.2f}ms, expected <50ms"
        # One load per request, so every request must have been a hit
        assert_cache_hit(hits_before, "Completion requests", expected=len(keywords))
        assert_warm(avg_latency, cold_ms, "Average completion latency")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
