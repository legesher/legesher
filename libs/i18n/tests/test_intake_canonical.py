"""Canonical-JSON serialization for review bundles (CORE-1688).

The canonical bytes are what mint ``ses_<24hex>`` (schema_v2.session_uid), so
serialization must be deterministic across interpreters and re-imports: sorted
keys, no insignificant whitespace, UTF-8 with no needless escaping, and NO
floats — a float's shortest-round-trip rendering is the one place JSON
serializers legitimately disagree, so the wire contract simply forbids them
(durations are integer milliseconds).
"""

from __future__ import annotations

import pytest

from legesher_i18n.intake.canonical import canonicalize


def test_key_order_and_whitespace_are_canonical() -> None:
    a = canonicalize({"b": 1, "a": [1, 2], "c": {"y": None, "x": True}})
    b = canonicalize({"c": {"x": True, "y": None}, "a": [1, 2], "b": 1})
    assert a == b == b'{"a":[1,2],"b":1,"c":{"x":true,"y":null}}'


def test_non_ascii_stays_utf8_not_escaped() -> None:
    # The bundle carries native-script surface forms; \uXXXX-escaping them
    # would make the canonical bytes depend on the serializer's escape policy.
    assert canonicalize({"w": "ورنہ_اگر"}) == '{"w":"ورنہ_اگر"}'.encode()


def test_floats_are_refused() -> None:
    with pytest.raises(ValueError, match="float"):
        canonicalize({"durations_ms": {"elif": 74000.5}})


def test_nan_and_infinity_are_refused() -> None:
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match="float"):
            canonicalize({"x": bad})


def test_canonical_bytes_round_trip_the_session_uid() -> None:
    from legesher_i18n.db.schema_v2 import session_uid

    bundle = {"bundle_version": "1.0", "locale": "ur"}
    assert session_uid(canonicalize(bundle)) == session_uid(canonicalize(bundle))
