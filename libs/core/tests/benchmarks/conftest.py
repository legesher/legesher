"""Fixtures shared by the benchmark modules.

Timing runs only under ``make bench`` (CORE-2129). The default run passes
``--benchmark-disable``, under which pytest-benchmark would run each benchmark
once as a plain test; ``timing_on`` skips it instead, so a wall-clock bound
never decides a per-commit run on a loaded runner.
"""

import pytest


@pytest.fixture
def timing_on(request):
    config = request.config
    if config.getoption("benchmark_disable") and not config.getoption(
        "benchmark_enable"
    ):
        pytest.skip("timing runs only under make bench")
