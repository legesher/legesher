"""Import overhead of the runtime import hook (CORE-2205).

Each data point is a fresh interpreter. Both arms load the pack and build
the finder, so they pay the same fixed cost; only the hook arm inserts the
finder into sys.meta_path. Each child purges the target's top-level
package from sys.modules before timing, so both arms import the same set
of modules from scratch (email.parser, for one, is already loaded by the
time the finder is built).

Under the default run (`--benchmark-disable`) each case takes one sample
per arm as a smoke test. `make bench` takes SAMPLES samples per arm and
records the medians, and how many modules the hook claimed, in the
benchmark's extra_info. The file measures only: it runs unchanged against
the code before and after CORE-2205, so the before/after table comes from
one method. What the hook claims and caches is asserted structurally in
tests/unit/runtime/test_import_hook.py.
"""

import json
import statistics
import subprocess
import sys
import textwrap

import pytest

SAMPLES = 15

STDLIB_TARGETS = [
    "asyncio",
    "unittest",
    "logging.config",
    "email.parser",
    "concurrent.futures",
]

CHILD = textwrap.dedent(
    """
    import importlib, json, sys, time
    arm, target, extra_path = sys.argv[1], sys.argv[2], sys.argv[3]
    if extra_path:
        sys.path.insert(0, extra_path)
    from legesher.runtime.import_hook import LegesherLoader, LegesherMetaPathFinder
    finder = LegesherMetaPathFinder("es")
    top = target.partition(".")[0]
    for name in list(sys.modules):
        if name == top or name.startswith(top + "."):
            del sys.modules[name]
    if arm == "hook":
        sys.meta_path.insert(0, finder)
    start = time.perf_counter_ns()
    module = importlib.import_module(target)
    elapsed_ms = (time.perf_counter_ns() - start) / 1e6
    claimed = sorted(
        name for name, mod in list(sys.modules.items())
        if isinstance(getattr(getattr(mod, "__spec__", None), "loader", None),
                      LegesherLoader)
    )
    print(json.dumps({"ms": elapsed_ms, "claimed": claimed,
                      "file": getattr(module, "__file__", None)}))
    """
)


def _sample(arm, target, extra_path=""):
    result = subprocess.run(
        [sys.executable, "-c", CHILD, arm, target, extra_path],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def _median_ms(arm, target, rounds, extra_path=""):
    samples = [_sample(arm, target, extra_path) for _ in range(rounds)]
    return statistics.median(s["ms"] for s in samples), samples[-1]


@pytest.mark.parametrize("target", STDLIB_TARGETS)
def test_stdlib_import_overhead(benchmark, target):
    """Hook versus no hook for a standard-library import, fresh process each."""
    rounds = 1 if benchmark.disabled else SAMPLES
    results = {}

    def measure():
        results["no_hook"], _ = _median_ms("none", target, rounds)
        results["hook"], last = _median_ms("hook", target, rounds)
        results["claimed"] = last["claimed"]

    benchmark.pedantic(measure, rounds=1, iterations=1)
    benchmark.extra_info.update(
        target=target,
        samples_per_arm=rounds,
        no_hook_median_ms=round(results["no_hook"], 2),
        hook_median_ms=round(results["hook"], 2),
        factor=round(results["hook"] / results["no_hook"], 2),
        modules_claimed=len(results["claimed"]),
    )


def test_translated_module_cold_then_warm(benchmark, tmp_path):
    """A translated module: first process compiles, second hits the cache."""
    from legesher.runtime.import_hook import LegesherMetaPathFinder

    native = LegesherMetaPathFinder("es").translator.translate_code(
        "def value(n):\n"
        "    total = 0\n"
        "    for i in range(n):\n"
        "        if i % 2 == 0:\n"
        "            total += i\n"
        "        else:\n"
        "            total -= 1\n"
        "    return total\n"
    )
    body = "\n\n".join(native.replace("value", f"value_{i}") for i in range(200))
    (tmp_path / "bench_native_es.py").write_text(body, encoding="utf-8")
    rounds = 1 if benchmark.disabled else SAMPLES
    results = {}

    def cache_files():
        pycache = tmp_path / "__pycache__"
        return sorted(p.name for p in pycache.iterdir()) if pycache.exists() else []

    def measure():
        cold = []
        warm = []
        for _ in range(rounds):
            for path in (tmp_path / "__pycache__").glob("*"):
                path.unlink()
            cold.append(_sample("hook", "bench_native_es", str(tmp_path)))
            warm.append(_sample("hook", "bench_native_es", str(tmp_path)))
        results["cold"] = statistics.median(s["ms"] for s in cold)
        results["warm"] = statistics.median(s["ms"] for s in warm)
        results["claimed"] = warm[-1]["claimed"]

    benchmark.pedantic(measure, rounds=1, iterations=1)
    benchmark.extra_info.update(
        samples=rounds,
        cold_median_ms=round(results["cold"], 2),
        warm_median_ms=round(results["warm"], 2),
        cache_files=cache_files(),
    )
    # The module under measurement must be the translated one.
    assert "bench_native_es" in results["claimed"], results["claimed"]
