"""Canonical-JSON serialization: the bytes that mint a session uid.

RFC 8785-style: object keys sorted by code point, no insignificant whitespace,
UTF-8 output without needless ``\\uXXXX`` escaping. One deliberate narrowing:
**floats are refused outright.** RFC 8785's number serialization (shortest
round-trip, ECMAScript rules) is the one part different languages get subtly
wrong, and the bundle contract has no legitimate float — durations are integer
milliseconds. Refusing is safer than being almost-compatible.

The digest of these bytes is the session's identity
(:func:`legesher_i18n.db.schema_v2.session_uid`), so this module is FROZEN the
same way the uid formulae are: a serialization change re-keys every session.
"""

from __future__ import annotations

import json
from typing import Any

__all__ = ["canonicalize"]


def _refuse_floats(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        raise ValueError(
            f"canonical bundle JSON may not contain floats ({path} = {value!r}): "
            "float rendering is serializer-dependent and would fork session "
            "uids across implementations. Durations are integer milliseconds."
        )
    if isinstance(value, dict):
        for key, item in value.items():
            _refuse_floats(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _refuse_floats(item, f"{path}[{index}]")


def canonicalize(bundle: Any) -> bytes:
    """Serialize ``bundle`` to its canonical UTF-8 bytes.

    Args:
        bundle: The parsed bundle (dicts/lists/strings/ints/bools/None).

    Returns:
        Deterministic bytes: sorted keys, ``,``/``:`` separators, raw UTF-8.

    Raises:
        ValueError: if any float (including NaN/Infinity) appears anywhere.
    """
    _refuse_floats(bundle)
    return json.dumps(
        bundle,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
