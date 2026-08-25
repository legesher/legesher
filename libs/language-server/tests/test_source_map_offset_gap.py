"""Regression placeholder for the deferred source_map offset rework.

SourceMap maps interior positions *proportionally* across a span whose source
and translated lengths differ (e.g. "definir" 7 chars -> "def" 3 chars), so a
round-trip ``to_original(to_translated(pos))`` is not the identity even for
plain BMP text. The same rework must also reconcile units: SourceMap counts
Python str characters while LSP ``Position.character`` is commonly UTF-16 code
units, which additionally desyncs on non-BMP characters. The full rework is out
of scope for the Unicode-guard PR; this xfail captures the gap so it is tracked
rather than silently shipped.
"""

import pytest

from legesher_language_server.source_map import (
    Position,
    PositionMapping,
    SourceMap,
)


@pytest.mark.xfail(
    reason="Deferred: proportional interior mapping does not round-trip "
    "(and counts Python-str, not UTF-16, units). Known gap noted in document.py.",
    strict=False,
)
def test_proportional_interior_mapping_round_trips():
    # A span that changes length (7 -> 3) makes interior positions map
    # proportionally; round-tripping an interior position is lossy today. The
    # deferred rework fixes both the rounding and the UTF-16-vs-str unit gap
    # (the latter only bites non-BMP text, which all 51 scripts avoid).
    mapping = PositionMapping(
        original_start=Position(0, 0),
        original_end=Position(0, 7),  # "definir"
        translated_start=Position(0, 0),
        translated_end=Position(0, 3),  # "def"
    )
    smap = SourceMap([mapping])
    pos = Position(0, 5)
    mapped = smap.to_translated(pos)
    assert smap.to_original(mapped) == pos
