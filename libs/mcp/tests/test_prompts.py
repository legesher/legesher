"""Prompt templates ship with the open package (§5.2 of the design)."""

from __future__ import annotations

import pytest
from mcp import ClientSession

pytestmark = pytest.mark.anyio

PROMPT_TOOL_PAIRS = [
    ("explain-in", {"language": "Arabic"}, "explain_in_language"),
    ("translate-review", {"target_lang": "es"}, "translate_to_native"),
    ("legibility-report", {"target_lang": "fr"}, "map_existing_codebase"),
]


async def test_prompts_declare_their_arguments(client: ClientSession) -> None:
    result = await client.list_prompts()
    args_by_name = {p.name: [a.name for a in (p.arguments or [])] for p in result.prompts}
    assert args_by_name["explain-in"] == ["language"]
    assert args_by_name["translate-review"] == ["target_lang"]
    assert args_by_name["legibility-report"] == ["target_lang"]


async def test_each_prompt_steers_to_its_tool(client: ClientSession) -> None:
    for name, arguments, tool in PROMPT_TOOL_PAIRS:
        result = await client.get_prompt(name, arguments)
        (message,) = result.messages
        text = message.content.text  # type: ignore[union-attr]
        assert tool in text, f"{name} does not mention {tool}"
        for value in arguments.values():
            assert value in text, f"{name} does not interpolate {value!r}"


async def test_explain_prompt_separates_facts_from_narration(
    client: ClientSession,
) -> None:
    result = await client.get_prompt("explain-in", {"language": "Spanish"})
    text = result.messages[0].content.text  # type: ignore[union-attr]
    assert "engine facts" in text
    assert "do not invent translations" in text
