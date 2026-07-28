"""explain_in_language: engine facts, never prose."""

from __future__ import annotations

import pytest
from mcp import ClientSession

from tests.conftest import assert_sanitized, call_err, call_ok

pytestmark = pytest.mark.anyio

ENGLISH = 'try:\n    print(int("1"))\nexcept ValueError:\n    pass\n'


async def test_constructs_and_validation_for_english_code(client: ClientSession) -> None:
    result = await call_ok(client, "explain_in_language", {"source": ENGLISH, "explain_in": "es"})
    by_term = {c["construct"]: c for c in result["constructs"]}
    assert by_term["try"]["category"] == "keywords"
    assert by_term["print"]["category"] == "builtins"
    assert by_term["int"]["category"] == "builtins"
    assert by_term["ValueError"]["category"] == "exceptions"
    # Code is English, so the code-language spelling is the English term.
    assert by_term["try"]["in_code_lang"] == "try"
    assert by_term["try"]["in_explain_lang"] == "probar"
    assert by_term["print"]["in_explain_lang"] == "imprimir"
    assert result["validation"] == {"valid": True, "issue": None}
    assert result["translated_source"] is None  # facts only, unless requested


async def test_native_code_explained_with_both_spellings(client: ClientSession) -> None:
    native = await call_ok(client, "translate_to_native", {"source": ENGLISH, "target_lang": "es"})
    result = await call_ok(
        client,
        "explain_in_language",
        {
            "source": native["translated_source"],
            "code_lang": "es",
            "explain_in": "fr",
        },
    )
    fr_try = await call_ok(client, "lookup_keyword_mapping", {"language": "fr", "terms": ["try"]})
    by_term = {c["construct"]: c for c in result["constructs"]}
    assert by_term["try"]["in_code_lang"] == "probar"  # how the code spells it
    assert by_term["try"]["in_explain_lang"] == fr_try["mappings"]["keywords"]["try"]
    assert result["validation"]["valid"] is True


async def test_include_translation_adds_translated_source(client: ClientSession) -> None:
    result = await call_ok(
        client,
        "explain_in_language",
        {"source": ENGLISH, "explain_in": "es", "include_translation": True},
    )
    assert result["translated_source"] is not None
    assert "probar:" in result["translated_source"]


async def test_syntax_error_is_a_validation_result_not_an_error(
    client: ClientSession,
) -> None:
    result = await call_ok(
        client, "explain_in_language", {"source": "def f(:\n", "explain_in": "es"}
    )
    assert result["validation"]["valid"] is False
    assert result["validation"]["issue"]["message"]
    assert result["constructs"] == []  # nothing tokenizable to map


async def test_unknown_explain_language_is_a_clean_error(client: ClientSession) -> None:
    message = await call_err(client, "explain_in_language", {"source": ENGLISH, "explain_in": "xx"})
    assert "unsupported_language" in message
    assert_sanitized(message)
