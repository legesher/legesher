"""Performance benchmarks for import hook LRU cache."""

from legesher.runtime.import_hook import _TranslationCache


class TestCachePerformance:
    """Benchmark cache performance."""

    def test_benchmark_cache_hit(self, benchmark):
        """Benchmark cache hit performance (warm cache)."""
        cache = _TranslationCache(max_size=128)
        key = ("test.py", 123456)
        cache.set(key, b"cached content" * 1000)  # ~14KB

        # Benchmark cache hit (should be very fast)
        result = benchmark(cache.get, key)
        assert result is not None

    def test_benchmark_cache_miss(self, benchmark):
        """Benchmark cache miss performance."""
        cache = _TranslationCache(max_size=128)

        # Benchmark cache miss
        result = benchmark(cache.get, ("missing.py", 999999))
        assert result is None

    def test_benchmark_cache_set(self, benchmark):
        """Benchmark cache set performance."""
        cache = _TranslationCache(max_size=128)
        content = b"translated content" * 1000  # ~18KB

        key_counter = [0]

        def set_item():
            key = (f"file{key_counter[0]}.py", key_counter[0])
            key_counter[0] += 1
            cache.set(key, content)

        # Benchmark cache set
        benchmark(set_item)

    def test_benchmark_eviction_overhead(self, benchmark):
        """Benchmark LRU eviction overhead."""
        cache = _TranslationCache(max_size=128)
        content = b"content"

        # Pre-fill cache to capacity
        for i in range(128):
            cache.set((f"file{i}.py", i), content)

        key_counter = [128]

        def add_with_eviction():
            """Add item that triggers eviction."""
            key = (f"file{key_counter[0]}.py", key_counter[0])
            key_counter[0] += 1
            cache.set(key, content)

        # Benchmark adding with eviction
        benchmark(add_with_eviction)

        # Verify evictions occurred
        stats = cache.get_stats()
        assert stats["evictions"] > 0

    def test_benchmark_statistics_overhead(self, benchmark):
        """Benchmark statistics retrieval overhead."""
        cache = _TranslationCache(max_size=128)

        # Add some entries
        for i in range(50):
            cache.set((f"file{i}.py", i), b"content")
            cache.get((f"file{i}.py", i))

        # Benchmark get_stats
        result = benchmark(cache.get_stats)
        assert "hits" in result

    def test_cache_memory_usage(self):
        """Test that cache entry count stays bounded."""
        cache = _TranslationCache(max_size=128)
        large_content = b"x" * 100_000  # 100KB per entry

        # Fill cache
        for i in range(128):
            cache.set((f"file{i}.py", i), large_content)

        # Verify cache is at max capacity
        stats = cache.get_stats()
        assert stats["size"] == 128
        assert stats["evictions"] == 0

        # Add more items - cache should evict and stay bounded
        for i in range(128, 256):
            cache.set((f"file{i}.py", i), large_content)

        # Verify size is still bounded and evictions occurred
        stats = cache.get_stats()
        assert stats["size"] == 128  # Still at max capacity
        assert stats["evictions"] == 128  # One eviction per new item

    def test_cache_hit_rate_realistic_workflow(self):
        """Test cache hit rate in realistic development workflow."""
        cache = _TranslationCache(max_size=128)

        # Simulate importing 50 files repeatedly (like in dev server)
        files = [f"module{i}.py" for i in range(50)]
        content = b"def foo(): pass" * 100

        # Initial imports (all misses - check cache, then add)
        for i, filename in enumerate(files):
            result = cache.get((filename, i))  # Miss
            assert result is None
            cache.set((filename, i), content)

        initial_stats = cache.get_stats()
        assert initial_stats["misses"] == 50
        assert initial_stats["hits"] == 0

        # Repeated imports (all hits)
        for i, filename in enumerate(files):
            result = cache.get((filename, i))
            assert result is not None

        final_stats = cache.get_stats()
        assert final_stats["hits"] == 50
        assert final_stats["hit_rate"] == 0.5  # 50 hits / 100 total = 50%

    def test_benchmark_concurrent_access(self, benchmark):
        """Benchmark concurrent cache access performance."""
        import threading

        cache = _TranslationCache(max_size=128)

        # Pre-fill cache
        for i in range(100):
            cache.set((f"file{i}.py", i), b"content")

        def concurrent_access():
            """Simulate concurrent reads and writes."""
            threads = []

            def worker(thread_id):
                for i in range(10):
                    key = (f"file{thread_id}_{i}.py", i)
                    cache.set(key, f"content_{thread_id}".encode())
                    cache.get(key)

            for i in range(5):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

        # Benchmark concurrent access
        benchmark(concurrent_access)
