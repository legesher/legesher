"""lookup_keyword_mapping: quick reference over the pack dictionaries."""

from __future__ import annotations

import pytest
from mcp import ClientSession

from legesher_mcp.engine import get_engine
from tests.conftest import assert_sanitized, call_err, call_ok

pytestmark = pytest.mark.anyio


async def test_omitting_terms_returns_the_full_mapping(client: ClientSession) -> None:
    result = await call_ok(client, "lookup_keyword_mapping", {"language": "es"})
    engine = get_engine()
    expected = engine.pack_categories(engine.load_pack("es", "3.13"))
    assert result["mappings"]["keywords"] == expected["keywords"]
    assert result["mappings"]["builtins"] == expected["builtins"]
    assert result["mappings"]["exceptions"] == expected["exceptions"]
    assert result["mappings"]["implicit_params"] == expected["implicit_params"]
    assert result["unmatched_terms"] == []
    assert result["language"] == "es"
    assert result["python_version"] == "3.13"


async def test_filtered_terms_across_categories(client: ClientSession) -> None:
    result = await call_ok(
        client,
        "lookup_keyword_mapping",
        {
            "language": "ar",
            "terms": ["def", "print", "ValueError", "self", "no_such_term"],
        },
    )
    mappings = result["mappings"]
    assert list(mappings["keywords"]) == ["def"]
    assert list(mappings["builtins"]) == ["print"]
    # Canonical PascalCase spelling matches what appears in code.
    assert list(mappings["exceptions"]) == ["ValueError"]
    assert list(mappings["implicit_params"]) == ["self"]
    assert result["unmatched_terms"] == ["no_such_term"]


async def test_unknown_language_is_a_clean_error(client: ClientSession) -> None:
    message = await call_err(client, "lookup_keyword_mapping", {"language": "xx", "terms": ["def"]})
    assert "unsupported_language" in message
    assert_sanitized(message)
