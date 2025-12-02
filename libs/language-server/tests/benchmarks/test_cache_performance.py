"""Performance benchmarks for CORE-446 cache improvements.

This validates that refactored code meets performance targets:
- Cold cache pack load: <100ms
- Warm cache pack load: <1ms
- Cache hit rate: >95% after warmup
- Completion latency with warm cache: <50ms

Run with: uv run pytest tests/benchmarks/test_cache_performance.py -v -s
"""

import time

import pytest


class TestLanguagePackLoaderCache:
    """Test LanguagePackLoader LRU cache performance (CORE-446)."""

    def test_cold_cache_pack_load(self):
        """Test first load of language pack (cold cache).

        Success Criteria:
            - First load completes in <100ms
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
        print("Target: <100ms")
        print(f"Status: {'✓ PASS' if elapsed_ms < 100 else '✗ FAIL'}")
        print(f"Keywords loaded: {len(pack.keywords)}")
        print(f"{'=' * 60}\n")

        assert pack is not None
        assert len(pack.keywords) > 30
        assert elapsed_ms < 100, f"Cold load took {elapsed_ms:.2f}ms, expected <100ms"

    def test_warm_cache_pack_load(self):
        """Test cached load of language pack (warm cache).

        Success Criteria:
            - Cached load completes in <1ms
            - Pack is identical to first load
        """
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()

        # First load to warm cache
        pack1 = loader.load(language="es", target="python", version="3.10")

        # Measure cached load
        start = time.perf_counter()
        pack2 = loader.load(language="es", target="python", version="3.10")
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n{'=' * 60}")
        print("CORE-446: Warm cache pack load")
        print(f"{'=' * 60}")
        print(f"Time: {elapsed_ms:.2f}ms")
        print("Target: <1ms")
        print(f"Status: {'✓ PASS' if elapsed_ms < 1 else '✗ FAIL'}")
        print(f"Cache speedup: {100 / elapsed_ms if elapsed_ms > 0 else 'infinite'}x faster")
        print(f"{'=' * 60}\n")

        assert pack1 is pack2  # Should return same object from cache
        assert elapsed_ms < 1, f"Cached load took {elapsed_ms:.2f}ms, expected <1ms"

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

        loader = LanguagePackLoader()
        loader.clear_cache()

        languages = ["es", "ar", "zh"]

        # Load all languages
        packs = {}
        for lang in languages:
            pack = loader.load(language=lang, target="python", version="3.10")
            packs[lang] = pack

        # Verify all cached
        for lang in languages:
            start = time.perf_counter()
            cached_pack = loader.load(language=lang, target="python", version="3.10")
            elapsed_ms = (time.perf_counter() - start) * 1000

            assert cached_pack is packs[lang]  # Same object from cache
            assert elapsed_ms < 1, f"Cached load for {lang} took {elapsed_ms:.2f}ms"

        # Verify packs are different
        assert packs["es"].keywords["def"] == "definir"
        assert packs["ar"].keywords["def"] == "تعريف"
        assert packs["zh"].keywords["def"] == "定义"

        print(f"\n{'=' * 60}")
        print("CORE-446: Multi-language caching")
        print(f"{'=' * 60}")
        print(f"Languages cached: {len(languages)}")
        print("All loads from cache: <1ms each")
        print("Status: ✓ PASS")
        print(f"{'=' * 60}\n")


class TestKeywordDocsCache:
    """Test keyword_docs.py cache performance after refactoring."""

    def test_keyword_translation_with_cache(self):
        """Test keyword translation performance with LanguagePackLoader cache.

        Success Criteria:
            - Repeated lookups use cache
            - Second lookup significantly faster
        """
        from legesher_language_server.utils.keyword_docs import KeywordDocumentation

        docs = KeywordDocumentation()

        # First lookup (may load pack)
        start = time.perf_counter()
        result1 = docs.get_keyword_translation("def", "es")
        first_time = (time.perf_counter() - start) * 1000

        # Second lookup (should use cache)
        start = time.perf_counter()
        result2 = docs.get_keyword_translation("class", "es")
        second_time = (time.perf_counter() - start) * 1000

        print(f"\n{'=' * 60}")
        print("CORE-446: keyword_docs cache performance")
        print(f"{'=' * 60}")
        print(f"First lookup: {first_time:.2f}ms")
        print(f"Second lookup: {second_time:.2f}ms")
        print(f"Status: {'✓ PASS' if second_time < 1 else '✗ FAIL'}")
        print(f"{'=' * 60}\n")

        assert result1 == "definir"
        assert result2 == "clase"
        assert second_time < 1, f"Cached lookup took {second_time:.2f}ms, expected <1ms"


class TestPylanceProxyCache:
    """Test pylance_proxy.py cache performance after refactoring."""

    def test_keyword_map_initialization_with_cache(self):
        """Test PylanceProxy initialization uses cached language pack.

        Success Criteria:
            - Second initialization significantly faster
            - Keyword maps are identical
        """
        from legesher_language_server.config import LanguageServerConfig
        from legesher_language_server.pylance_proxy import PylanceProxy

        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=False
        )

        # First initialization (may load pack)
        start = time.perf_counter()
        proxy1 = PylanceProxy(config)
        first_time = (time.perf_counter() - start) * 1000

        # Second initialization (should use cache)
        start = time.perf_counter()
        proxy2 = PylanceProxy(config)
        second_time = (time.perf_counter() - start) * 1000

        print(f"\n{'=' * 60}")
        print("CORE-446: PylanceProxy initialization cache performance")
        print(f"{'=' * 60}")
        print(f"First init: {first_time:.2f}ms")
        print(f"Second init: {second_time:.2f}ms")
        print(f"Speedup: {first_time / second_time if second_time > 0 else 'infinite'}x")
        print("Target second init: <10ms")
        print(f"Status: {'✓ PASS' if second_time < 10 else '✗ FAIL'}")
        print(f"{'=' * 60}\n")

        # Verify keyword maps are identical
        assert proxy1.translator.keyword_map == proxy2.translator.keyword_map
        assert len(proxy1.translator.keyword_map) > 30
        assert second_time < 10, f"Cached init took {second_time:.2f}ms, expected <10ms"


class TestCompletionLatency:
    """Test end-to-end completion latency (CORE-446 primary goal)."""

    def test_completion_latency_warm_cache(self):
        """Test completion latency with warm cache.

        Success Criteria:
            - Completion latency <50ms with warm cache
            - This is the primary CORE-446 performance target
        """
        from legesher_language_server.utils.keyword_docs import KeywordDocumentation

        docs = KeywordDocumentation()

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
        print(f"Avg latency: {avg_latency:.2f}ms")
        print(f"Max latency: {max_latency:.2f}ms")
        print(f"P95 latency: {p95_latency:.2f}ms")
        print("Target: <50ms per completion")
        print(f"Status: {'✓ PASS' if max_latency < 50 else '✗ FAIL'}")
        print(f"{'=' * 60}\n")

        assert max_latency < 50, f"Max latency {max_latency:.2f}ms, expected <50ms"
        assert avg_latency < 1, f"Avg latency {avg_latency:.2f}ms, expected <1ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
