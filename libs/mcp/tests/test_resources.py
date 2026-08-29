"""legesher:// resources: the catalog and per-language dictionaries."""

from __future__ import annotations

import json

import pytest
from mcp import ClientSession, McpError
from pydantic import AnyUrl

from legesher_mcp.engine import get_engine
from tests.conftest import assert_sanitized

pytestmark = pytest.mark.anyio


async def test_language_catalog(client: ClientSession) -> None:
    result = await client.read_resource(AnyUrl("legesher://languages"))
    (content,) = result.contents
    assert content.mimeType == "application/json"
    catalog = json.loads(content.text)
    engine = get_engine()
    assert len(catalog) == len(engine.list_languages())
    by_code = {entry["code"]: entry for entry in catalog}
    assert by_code["ar"]["rtl"] is True
    assert by_code["ar"]["pack_available"] is True
    assert by_code["es"]["native"] == "Español"
    assert set(by_code["es"]) == {"code", "name", "native", "rtl", "status", "pack_available"}


async def test_terms_dictionary_for_a_language(client: ClientSession) -> None:
    result = await client.read_resource(AnyUrl("legesher://languages/es/terms"))
    (content,) = result.contents
    terms = json.loads(content.text)
    engine = get_engine()
    expected = engine.pack_categories(engine.load_pack("es", "3.13"))
    assert terms["language"] == "es"
    assert terms["python_version"] == "3.13"
    assert terms["keywords"] == expected["keywords"]
    assert terms["builtins"] == expected["builtins"]
    assert terms["exceptions"] == expected["exceptions"]
    assert terms["implicit_params"] == expected["implicit_params"]


async def test_terms_for_unknown_language_is_a_clean_error(
    client: ClientSession,
) -> None:
    with pytest.raises(McpError) as excinfo:
        await client.read_resource(AnyUrl("legesher://languages/xx/terms"))
    message = str(excinfo.value)
    assert "unsupported_language" in message
    assert_sanitized(message)
