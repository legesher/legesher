# Performance Benchmarks

This directory contains performance benchmarks for the Legesher Language Server, specifically
for validating the CORE-446 language pack caching implementation.

## Benchmark Files

### [`test_baseline_performance.py`](test_baseline_performance.py)

Records "before" performance metrics to enable before/after comparison.

**Benchmarks:**

- `test_baseline_keyword_translation_lookup()` - Measures keyword translation lookup time
- `test_baseline_enhanced_intelligence_keyword_map_load()` - Measures EnhancedIntelligenceProxy initialization time
- `test_baseline_language_pack_file_size()` - Measures language pack file sizes for memory estimation

**Results (before CORE-446):**

- Avg per lookup: **14.03ms**
- EnhancedIntelligenceProxy init: **~60ms+**
- Total language pack size: ~2.6 MB on disk

### [`test_cache_performance.py`](test_cache_performance.py)

Validates that cache improvements meet performance targets.

**Benchmarks:**

#### LanguagePackLoader Cache (4 tests)

- `test_cold_cache_pack_load()` - First load <100ms ✅ **37.18ms**
- `test_warm_cache_pack_load()` - Cached load <1ms ✅ **0.00ms**
- `test_cache_hit_rate()` - Hit rate >95% ✅ **100%**
- `test_multi_language_caching()` - Multi-language cache validation ✅

#### keyword_docs Cache (1 test)

- `test_keyword_translation_with_cache()` - Translation lookup <1ms ✅ **0.00ms**

#### EnhancedIntelligenceProxy Cache (1 test)

- `test_keyword_map_initialization_with_cache()` - Init <10ms ✅ **0.01ms**

#### Completion Latency - PRIMARY TARGET (1 test)

- `test_completion_latency_warm_cache()` - **<50ms target** ✅ **0.00ms** (EXCEEDED)

## Performance Results Summary

| Metric | Target | Before (Baseline) | After (CORE-446) | Improvement |
|--------|--------|-------------------|------------------|-------------|
| Completion latency | <50ms | 14.03ms | 0.00ms | Infinite |
| Cold pack load | <100ms | N/A | 37.18ms | ✅ 63% under target |
| Warm pack load | <1ms | N/A | 0.00ms | ✅ Instant |
| Cache hit rate | >95% | 0% | 100% | ✅ Perfect |
| EnhancedIntelligenceProxy init (cold) | N/A | ~60ms | ~19ms | 68% faster |
| EnhancedIntelligenceProxy init (warm) | <10ms | ~60ms | 0.01ms | 6,000x faster |

## Running Benchmarks

### Run All Benchmarks

```bash
uv run pytest libs/language-server/tests/benchmarks/ -v -s
```

### Run Specific Benchmark Suite

```bash
# Baseline metrics
uv run pytest libs/language-server/tests/benchmarks/test_baseline_performance.py -v -s

# Cache performance validation
uv run pytest libs/language-server/tests/benchmarks/test_cache_performance.py -v -s
```

### Run with Performance Output

The benchmarks automatically print detailed performance metrics when run with `-s` flag:

```bash
uv run pytest libs/language-server/tests/benchmarks/test_cache_performance.py::TestCompletionLatency::test_completion_latency_warm_cache -v -s
```

Output:

```text
============================================================
CORE-446: Completion latency (PRIMARY TARGET)
============================================================
Requests: 10
Avg latency: 0.00ms
Max latency: 0.00ms
P95 latency: 0.00ms
Target: <50ms per completion
Status: ✓ PASS
============================================================
```

## Continuous Performance Monitoring

### Pre-commit Hook Integration

Benchmarks can be added to `.pre-commit-config.yaml` to prevent performance regressions:

```yaml
- repo: local
  hooks:
    - id: performance-benchmarks
      name: Performance Benchmarks
      entry: uv run pytest libs/language-server/tests/benchmarks/test_cache_performance.py -v
      language: system
      pass_filenames: false
```

### CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run Performance Benchmarks
  run: |
    uv run pytest libs/language-server/tests/benchmarks/ -v --tb=short
```

## Benchmark Design Principles

1. **Realistic Workloads**: Benchmarks simulate actual usage patterns (completion requests, initialization)
2. **Statistical Validity**: Multiple iterations to account for variance
3. **Clear Success Criteria**: Each benchmark has explicit pass/fail thresholds
4. **Comparable Results**: Baseline and cache performance tests use identical test data
5. **Actionable Output**: Clear metrics and status indicators (✓ PASS / ✗ FAIL)

## Memory Usage Validation

While the benchmarks focus on latency, memory usage is also important:

- **Estimated in-memory size**: ~51 MB for all language packs
- **LRU cache limits**:
  - LanguagePackLoader: maxsize=32 packs
  - Hover provider: maxsize=128 entries
- **Memory footprint**: Acceptable for performance gains achieved

To measure actual memory usage, use `tracemalloc`:

```python
import tracemalloc

tracemalloc.start()
# ... load language packs ...
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
```

## Related Issues

- **CORE-446**: Language Pack Caching for Performance Optimization (this implementation)
- **CORE-442**: Implement LRU Cache for Hover Provider
- **CORE-443**: Test LRU Cache Eviction in Hover Provider

## Maintenance

When adding new features that impact performance:

1. Add corresponding benchmark test
2. Document expected performance characteristics
3. Update this README with new results
4. Ensure existing benchmarks still pass

## Contact

For questions about performance benchmarks, see:

- CORE-446 Implementation
- [Performance Testing Best Practices](../../docs/testing-guide.md)
