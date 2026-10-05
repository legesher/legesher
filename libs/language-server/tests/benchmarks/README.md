# Performance Benchmarks

Performance tests for the language server's language-pack caching (CORE-446).

## How these tests run

Two modes (CORE-2321), following the testing contract in the repository's `CLAUDE.md`: performance assertions
in the default run are structural, and timing runs only under `make bench`.

- **The default run** (`make test-language-server`, and every merge-evidence run) executes every test here. It
  asserts by state: lru_cache hit and miss counts, object identity, and a warm-over-cold ratio floor that is
  documented where it is defined. No absolute wall-clock bound in this directory is enforced, and the report
  header says so: `timing: assert_within bounds not enforced (make bench enforces them)`.
- **`make bench`** runs every test marked `timing` in the language-server suite with `--timing`, which enforces
  the bounds those tests pass to `assert_within` in [`tests/timing.py`](../timing.py). That covers this
  directory, the latency tests in the provider suites (completion, hover, diagnostics, semantic tokens), and
  three cache tests elsewhere whose old time limits now back up a load or hit count.

## Files

### [`test_baseline_performance.py`](test_baseline_performance.py)

Records a keyword lookup time, the `EnhancedIntelligenceProxy` initialization time and the language pack file
sizes, for comparison with the figures from before CORE-446. It asserts only that each measurement was taken;
it has no thresholds.

### [`test_cache_performance.py`](test_cache_performance.py)

| Test | Every run | Also under `make bench` |
| --- | --- | --- |
| `test_cold_cache_pack_load` | The load after `clear_cache()` is one lru_cache miss and no hit, and returns the parsed `es` pack | Under 500 ms |
| `test_warm_cache_pack_load` | An lru_cache hit returning the same object; warm floor | Warm load under 100 ms |
| `test_cache_hit_rate` | Over 95% hits after warmup | |
| `test_multi_language_caching` | A hit per language, distinct packs per language; warm floor | Each warm load under 100 ms |
| `test_keyword_translation_with_cache` | An lru_cache hit on the second lookup; warm floor | Second lookup under 100 ms |
| `test_keyword_map_initialization_with_cache` | An lru_cache hit on the second proxy; warm floor | Second init under 100 ms |
| `test_completion_latency_warm_cache` | Ten requests, ten lru_cache hits; the average meets the warm floor | Slowest request under 50 ms; average under 100 ms |

The **warm floor** is the one timing assertion left in the default run: a cached load must be at least
`WARM_SPEEDUP_FLOOR` (2) times faster than a cold load measured in the same test. It is a ratio, not an absolute
bound, and a backstop behind the hit count, set so that a single scheduler preemption cannot trip it; the
comment on `WARM_SPEEDUP_FLOOR` gives the reasoning (CORE-2129). Its absolute companion, `WARM_CEILING_MS`
(100 ms), is enforced only under `make bench`.

## Running

```bash
# The default run, from the repository root (-s prints each test's measurements)
uv run --package legesher-language-server pytest libs/language-server/tests/benchmarks -v -s --no-cov

# Bounds on: every timing test in the package
cd libs/language-server && uv run pytest tests/ -m timing --timing --no-cov

# Bounds on for every package that has timing tests
make bench
```

## Adding a performance test

1. Prove the fast path by state, in the default run: `cache_info()` hits or misses, object identity, or a count
   of loads.
2. Pass any wall-clock measurement to `assert_within(elapsed_ms, bound_ms, what)` from `tests/timing.py`, and
   mark the test `@pytest.mark.timing` so `make bench` selects it.
3. A timing comparison that runs in the default run needs a comment saying why scheduler noise cannot trip it.
