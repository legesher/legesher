"""translate_to_native / translate_to_source through the MCP layer."""

from __future__ import annotations

import pytest
from mcp import ClientSession

import legesher_mcp.engine as engine_mod
from legesher_mcp.schemas import SOURCE_MAX_CHARS
from tests.conftest import assert_sanitized, call_err, call_ok

pytestmark = pytest.mark.anyio

ENGLISH = "def greet(name):\n    print(name)\n    return True\n"


async def test_en_to_es_translates_keywords_and_builtins(client: ClientSession) -> None:
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": ENGLISH, "target_lang": "es"},
    )
    assert "definir greet(name):" in result["translated_source"]
    assert "imprimir(name)" in result["translated_source"]
    assert result["source_lang"] == "en"
    assert result["target_lang"] == "es"
    assert result["python_version"] == "3.13"
    assert result["pivoted"] is False


async def test_fragments_translate_without_a_snippet_mode(client: ClientSession) -> None:
    """A fragment (not a valid module) rides the same tool as a full file."""
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": "return value + 1\n", "target_lang": "es"},
    )
    assert result["translated_source"] == "devolver value + 1\n"


async def test_round_trip_via_translate_to_source(client: ClientSession) -> None:
    native = await call_ok(client, "translate_to_native", {"source": ENGLISH, "target_lang": "es"})
    back = await call_ok(
        client,
        "translate_to_source",
        {"source": native["translated_source"], "source_lang": "es"},
    )
    assert back["translated_source"] == ENGLISH
    assert back["target_lang"] == "en"
    assert back["pivoted"] is False


async def test_x_to_y_pivots_through_english(client: ClientSession) -> None:
    """es→fr has no direct engine path: it pivots and says so."""
    native = await call_ok(client, "translate_to_native", {"source": ENGLISH, "target_lang": "es"})
    pivoted = await call_ok(
        client,
        "translate_to_native",
        {
            "source": native["translated_source"],
            "source_lang": "es",
            "target_lang": "fr",
        },
    )
    direct = await call_ok(client, "translate_to_native", {"source": ENGLISH, "target_lang": "fr"})
    assert pivoted["pivoted"] is True
    assert pivoted["translated_source"] == direct["translated_source"]


async def test_same_language_is_identity(client: ClientSession) -> None:
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": ENGLISH, "source_lang": "en", "target_lang": "en"},
    )
    assert result["translated_source"] == ENGLISH
    assert result["pivoted"] is False


async def test_unknown_language_is_a_clean_machine_coded_error(
    client: ClientSession,
) -> None:
    message = await call_err(
        client, "translate_to_native", {"source": ENGLISH, "target_lang": "xx"}
    )
    assert "unsupported_language" in message
    assert "legesher://languages" in message
    assert_sanitized(message)


async def test_registry_language_without_a_pack_is_a_clean_error(
    client: ClientSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a registry entry whose pack is not installed (future state:
    packs ship as separate packages, so a user can have the registry without
    a given pack). The loader's message embeds filesystem paths — the tool
    error must not."""
    monkeypatch.setattr(
        engine_mod,
        "LANGUAGE_METADATA",
        {
            **engine_mod.LANGUAGE_METADATA,
            "zz": {"name": "Fake", "native": "Fake", "rtl": False, "status": "experimental"},
        },
    )
    message = await call_err(
        client, "translate_to_native", {"source": ENGLISH, "target_lang": "zz"}
    )
    assert "language_pack_not_found" in message
    assert "'zz'" in message
    assert_sanitized(message)


async def test_oversized_source_is_rejected_at_the_schema(client: ClientSession) -> None:
    message = await call_err(
        client,
        "translate_to_native",
        {"source": "x" * (SOURCE_MAX_CHARS + 1), "target_lang": "es"},
    )
    assert message  # schema validation error, not a crash
    assert_sanitized(message)


async def test_malformed_arguments_are_rejected(client: ClientSession) -> None:
    # Wrong type
    message = await call_err(client, "translate_to_native", {"source": 42, "target_lang": "es"})
    assert_sanitized(message)
    # Missing required field
    message = await call_err(client, "translate_to_native", {"source": "x = 1"})
    assert_sanitized(message)
    # Language code failing the registry pattern (path-traversal guard)
    message = await call_err(
        client,
        "translate_to_native",
        {"source": "x = 1", "target_lang": "../../etc"},
    )
    assert_sanitized(message)


async def test_incomplete_code_is_handled_gracefully(client: ClientSession) -> None:
    """The token engine tolerates incomplete code instead of crashing."""
    result = await call_ok(
        client, "translate_to_native", {"source": "def f(:", "target_lang": "es"}
    )
    assert result["translated_source"]  # best-effort, never an exception
