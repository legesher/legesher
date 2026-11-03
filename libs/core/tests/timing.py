"""Wall-clock bounds, enforced only on request.

The testing contract in the repository's CLAUDE.md keeps the default run
structural: a test proves a cache by its hit count, not by how fast it was, and
absolute bounds run only under ``make bench``. A bound in the default run
measures the machine's load as much as the code. With the suite on one pytest
worker per CPU, a 500-line translation that takes a few milliseconds idle took
152 ms on a three-core runner, against a 100 ms bound.

So a test that measures latency still runs its code and its functional
assertions in every run, and hands its measurement to :func:`assert_within`.
The bound is enforced only when pytest is started with ``--timing``, which
``make bench`` passes, selecting these tests by their ``timing`` marker. The
report header says which mode a run is in. The language server's
``tests/timing.py`` is the same helper.
"""

#: Set from the ``--timing`` option by ``tests/conftest.py``.
ENFORCED = False


def assert_within(elapsed_ms: float, bound_ms: float, what: str) -> None:
    """Assert ``elapsed_ms < bound_ms``, when bounds are being enforced."""
    if ENFORCED:
        assert elapsed_ms < bound_ms, (
            f"{what} took {elapsed_ms:.2f}ms, expected <{bound_ms:.2f}ms"
        )
