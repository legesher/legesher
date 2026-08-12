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


# ---------------------------------------------------------------------------
# wire contract <-> schema drift (CORE-1838)
# ---------------------------------------------------------------------------


def _sql_check_values(sql: str, table: str, column: str) -> set[str]:
    """The literal set from `<table>.<column> ... CHECK (column IN (...))`.

    Scoped to one CREATE TABLE block: `kind`, `field`, `reason` and `topic`
    each name a column in more than one table, so an unscoped search silently
    reads the wrong vocabulary (which is how this helper first went wrong).
    """
    import re

    block = re.search(rf"CREATE TABLE {table} \((?P<body>.*?)\n\);", sql, re.S)
    assert block, f"no CREATE TABLE {table}"
    match = re.search(
        rf"\b{column}\b.*?CHECK\s*\(\s*{column}\s+IN\s*\((?P<vals>.*?)\)\s*\)",
        block.group("body"),
        re.S,
    )
    assert match, f"no CHECK ... IN found for {table}.{column}"
    return set(re.findall(r"'([^']+)'", match.group("vals")))


def test_the_bundle_schema_enums_match_the_database_vocabularies() -> None:
    """The wire contract restates vocabularies the schema also declares.

    Nothing tied them together, so a CHECK could gain a value the forms and the
    validator would then reject — or lose one they would keep accepting. This
    is the tie: the JSON Schema enum must equal the SQL CHECK set exactly.
    """
    import json

    from legesher_i18n.db.schema_v2 import SCHEMA_V2_PATH
    from legesher_i18n.intake.pipeline import _SCHEMA_PATH

    sql = SCHEMA_V2_PATH.read_text(encoding="utf-8")
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    response = schema["properties"]["responses"]["items"]["properties"]

    pairs = {
        "option_annotations.kind": (
            set(schema["$defs"]["annotation_kind"]["enum"]),
            _sql_check_values(sql, "option_annotations", "kind"),
        ),
        "option_flags.reason": (
            set(response["flags"]["items"]["properties"]["reason"]["enum"]),
            _sql_check_values(sql, "option_flags", "reason"),
        ),
        "concept_commentary.topic": (
            set(response["commentary"]["items"]["properties"]["topic"]["enum"]),
            _sql_check_values(sql, "concept_commentary", "topic"),
        ),
        "style_ratifications.field": (
            set(
                schema["properties"]["style_answers"]["items"]["properties"]["field"][
                    "enum"
                ]
            ),
            _sql_check_values(sql, "style_ratifications", "field"),
        ),
        "review_sessions.track": (
            set(schema["properties"]["track"]["enum"]),
            _sql_check_values(sql, "review_sessions", "track"),
        ),
    }
    for name, (wire, db) in pairs.items():
        assert wire == db, (
            f"{name}: the bundle schema and schema_v2.sql disagree. "
            f"wire-only={sorted(wire - db)} db-only={sorted(db - wire)}. "
            "Change both together, or a submission the DB accepts is refused "
            "at the wire (or vice versa)."
        )
