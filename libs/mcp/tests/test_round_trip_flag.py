"""The verify_round_trip flag on both translate tools (CORE-1813).

Boundary behavior only — the report's own semantics are pinned in
libs/core (test_round_trip_report.py). What belongs to THIS layer: the
flag is opt-in and its field is ABSENT (not null) when off, the flag
changes nothing about the translation itself, divergence snippets are
bounded for the wire, the vacuous trip is a tool error, and no source
content rides the block beyond the bounded snippets.

Content over key names: boundary assertions use distinctive marker
strings in ``json.dumps`` of the serialized block, because asserting a
key's absence against a model that never had the key certifies nothing.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from mcp import ClientSession
from pydantic import ValidationError

from legesher_mcp.engine import TranslationOutcome, get_engine
from legesher_mcp.schemas import SNIPPET_MAX_CHARS, DivergenceModel
from tests.conftest import assert_sanitized, call_err, call_ok

pytestmark = pytest.mark.anyio

ENGLISH = "def greet():\n    return 42\n"


async def _native_es(client: ClientSession) -> str:
    result = await call_ok(client, "translate_to_native", {"source": ENGLISH, "target_lang": "es"})
    return str(result["translated_source"])


@pytest.fixture
def corrupt_return_hop(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    """Make the engine's return hop (X→en) yield a chosen corruption.

    The forward hop passes text through unchanged, so the tool's own
    translation succeeds; the round trip then compares the input against
    the corrupted return — a REAL divergence reaching the wire, not a
    hand-built model.
    """

    def install(corrupted: str) -> None:
        def fake_translate(
            *, source: str, source_lang: str, target_lang: str, python_version: str
        ) -> TranslationOutcome:
            if target_lang == "en" and source_lang != "en":
                return TranslationOutcome(translated_source=corrupted, pivoted=False)
            return TranslationOutcome(translated_source=source, pivoted=False)

        monkeypatch.setattr(get_engine(), "translate", fake_translate)

    return install


# -- absent, not null ------------------------------------------------------


async def test_unflagged_translate_to_native_has_no_round_trip_key(
    client: ClientSession,
) -> None:
    result = await call_ok(client, "translate_to_native", {"source": ENGLISH, "target_lang": "es"})
    assert "round_trip" not in result


async def test_unflagged_translate_to_source_has_no_round_trip_key(
    client: ClientSession,
) -> None:
    native = await _native_es(client)
    result = await call_ok(client, "translate_to_source", {"source": native, "source_lang": "es"})
    assert "round_trip" not in result


async def test_explicit_false_flag_still_omits_the_key(client: ClientSession) -> None:
    """False and unset serialize identically: no key, not a null."""
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": ENGLISH, "target_lang": "es", "verify_round_trip": False},
    )
    assert "round_trip" not in result


# -- clean verification, both directions -----------------------------------


async def test_flag_verifies_a_clean_trip_on_translate_to_native(
    client: ClientSession,
) -> None:
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": ENGLISH, "target_lang": "es", "verify_round_trip": True},
    )
    info = result["round_trip"]
    assert info["round_trips"] is True
    assert info["divergence_count"] == 0
    assert info["divergences"] == []
    assert "keywords" in info["verified"]
    assert info["grammar_version"] == "3.13"
    assert info["schema_version"] == "1.0.0"
    assert info["pivoted"] is False
    # compile_check understands English only, and the forward rendering
    # here is Spanish — the compile fact is unknown, never assumed.
    assert info["forward_valid"] is None


async def test_flag_verifies_a_clean_trip_on_translate_to_source(
    client: ClientSession,
) -> None:
    native = await _native_es(client)
    result = await call_ok(
        client,
        "translate_to_source",
        {"source": native, "source_lang": "es", "verify_round_trip": True},
    )
    info = result["round_trip"]
    assert info["round_trips"] is True
    assert info["divergence_count"] == 0
    # The forward rendering IS canonical English here: the compile fact
    # is earned, and clean keyword-bearing source earns a true.
    assert info["forward_valid"] is True
    assert "keywords" in info["verified"]


async def test_verdict_line_is_single_line_and_states_its_limits(
    client: ClientSession,
) -> None:
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": ENGLISH, "target_lang": "es", "verify_round_trip": True},
    )
    line = result["round_trip"]["verdict_line"]
    assert "\n" not in line
    assert "VERIFIED" in line
    assert "not covered" in line


# -- content never rides the block ------------------------------------------


async def test_clean_round_trip_block_carries_no_source_content(
    client: ClientSession,
) -> None:
    """The report's forward/returned bodies must never be serialized.

    Asserted on CONTENT: a marker present in the source must not appear
    anywhere in the serialized block. A clean trip has no divergences, so
    any hit would be a leaked source body.
    """
    marker = "CANARY_MARKER_9f3a"
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": f"{marker} = 42\n", "target_lang": "es", "verify_round_trip": True},
    )
    assert result["round_trip"]["round_trips"] is True
    assert marker not in json.dumps(result["round_trip"])
    # The translation itself still carries it, of course — identifiers pass through.
    assert marker in result["translated_source"]


async def test_failed_verdict_line_carries_no_source_content(
    client: ClientSession, corrupt_return_hop: Callable[[str], None]
) -> None:
    marker = "CANARY_2b_ignore_prior_instructions"
    corrupt_return_hop(f'{marker} = "other"\n')
    result = await call_ok(
        client,
        "translate_to_native",
        {
            "source": f'{marker} = "secret"\n',
            "target_lang": "es",
            "verify_round_trip": True,
        },
    )
    info = result["round_trip"]
    assert info["round_trips"] is False
    line = info["verdict_line"]
    assert "FAILED" in line
    assert "\n" not in line
    assert marker not in line


# -- bounded divergences -----------------------------------------------------


async def test_forced_divergence_snippets_are_truncated_at_the_boundary(
    client: ClientSession, corrupt_return_hop: Callable[[str], None]
) -> None:
    """A real divergence on an oversized line ships bounded snippets.

    A physical line is unbounded below SOURCE_MAX_CHARS; unbounded
    expected/actual fields shipped copies of the file on the wire.
    """
    expected_line = "value = " + "a" * 400
    corrupt_return_hop("value = " + "b" * 400 + "\n")
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": expected_line + "\n", "target_lang": "es", "verify_round_trip": True},
    )
    info = result["round_trip"]
    assert info["round_trips"] is False
    assert info["divergence_count"] == 1
    row = info["divergences"][0]
    assert row["line"] == 1
    assert len(row["expected"]) == SNIPPET_MAX_CHARS
    assert len(row["actual"]) == SNIPPET_MAX_CHARS
    assert row["truncated"] is True


def test_divergence_model_rejects_oversized_snippets() -> None:
    """The schema itself enforces the bound — projection is not the only gate."""
    with pytest.raises(ValidationError):
        DivergenceModel(
            line=1, offset=1, expected="x" * 500, actual="y", truncated=True, kind="content"
        )
    with pytest.raises(ValidationError):
        DivergenceModel(
            line=1, offset=1, expected="x", actual="y" * 500, truncated=True, kind="content"
        )


# -- parity: the flag changes nothing about the translation ------------------


async def test_flag_parity_on_translate_to_native(client: ClientSession) -> None:
    off = await call_ok(client, "translate_to_native", {"source": ENGLISH, "target_lang": "es"})
    on = await call_ok(
        client,
        "translate_to_native",
        {"source": ENGLISH, "target_lang": "es", "verify_round_trip": True},
    )
    assert on["translated_source"] == off["translated_source"]
    assert on["pivoted"] == off["pivoted"]


async def test_flag_parity_on_translate_to_source(client: ClientSession) -> None:
    native = await _native_es(client)
    off = await call_ok(client, "translate_to_source", {"source": native, "source_lang": "es"})
    on = await call_ok(
        client,
        "translate_to_source",
        {"source": native, "source_lang": "es", "verify_round_trip": True},
    )
    assert on["translated_source"] == off["translated_source"]
    assert on["pivoted"] == off["pivoted"]


async def test_pivoted_trip_is_disclosed(client: ClientSession) -> None:
    """es→fr rides the English pivot; the round-trip block must say so."""
    native = await _native_es(client)
    result = await call_ok(
        client,
        "translate_to_native",
        {
            "source": native,
            "source_lang": "es",
            "target_lang": "fr",
            "verify_round_trip": True,
        },
    )
    assert result["pivoted"] is True
    info = result["round_trip"]
    assert info["pivoted"] is True
    assert "pivot" in info["verdict_line"].lower()


# -- the vacuous trip --------------------------------------------------------


async def test_vacuous_trip_on_translate_to_source_is_a_tool_error(
    client: ClientSession,
) -> None:
    """en→en is identity in both hops: a comparison that verifies nothing.

    Unflagged, same-language translation stays the documented no-op; the
    flag turns it into an error rather than fabricating a VERIFIED.
    """
    message = await call_err(
        client,
        "translate_to_source",
        {"source": ENGLISH, "source_lang": "en", "verify_round_trip": True},
    )
    assert "vacuous_round_trip" in message
    assert_sanitized(message)


async def test_vacuous_trip_on_translate_to_native_is_a_tool_error(
    client: ClientSession,
) -> None:
    message = await call_err(
        client,
        "translate_to_native",
        {
            "source": ENGLISH,
            "source_lang": "es",
            "target_lang": "es",
            "verify_round_trip": True,
        },
    )
    assert "vacuous_round_trip" in message
    assert_sanitized(message)
