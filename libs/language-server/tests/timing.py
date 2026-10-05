"""Wall-clock bounds, enforced only on request (CORE-2321).

The testing contract in the repository's CLAUDE.md keeps the default run
structural: a test proves a cache by its hit count, not by how fast it was, and
timing runs only under ``make bench``. An absolute bound in the default run
measures the machine's load as much as the code. ``test_cold_cache_pack_load``
crossed its 500 ms bound at 576 ms on a loaded machine, against about 45 ms
idle.

So a test that measures latency still runs its code and its functional
assertions in every run, and hands its measurement to :func:`assert_within`.
The bound is enforced only when pytest is started with ``--timing``, which
``make bench`` passes, selecting these tests by their ``timing`` marker. The
report header says which mode a run is in. Bounds outside this helper, such as
the transport tests' event-loop stall limit, detect a blocked event loop, have
wide margins, and run in every run.
"""

#: Set from the ``--timing`` option by ``tests/conftest.py``.
ENFORCED = False


def assert_within(elapsed_ms: float, bound_ms: float, what: str) -> None:
    """Assert ``elapsed_ms < bound_ms``, when bounds are being enforced."""
    if ENFORCED:
        assert elapsed_ms < bound_ms, f"{what} took {elapsed_ms:.2f}ms, expected <{bound_ms:.2f}ms"
