"""The advertised surface: five tools, two resources, three prompts, stdio."""

from __future__ import annotations

import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

pytestmark = pytest.mark.anyio

EXPECTED_TOOLS = {
    "translate_to_native",
    "translate_to_source",
    "explain_in_language",
    "lookup_keyword_mapping",
    "map_existing_codebase",
}


async def test_exactly_five_coarse_tools(client: ClientSession) -> None:
    result = await client.list_tools()
    assert {tool.name for tool in result.tools} == EXPECTED_TOOLS


async def test_every_tool_has_description_and_schemas(client: ClientSession) -> None:
    result = await client.list_tools()
    for tool in result.tools:
        assert tool.description, f"{tool.name} has no description"
        assert tool.inputSchema.get("properties"), f"{tool.name} has no input schema"
        assert tool.outputSchema, f"{tool.name} publishes no output schema"


async def test_catalog_resource_and_terms_template_listed(client: ClientSession) -> None:
    resources = await client.list_resources()
    assert [str(r.uri) for r in resources.resources] == ["legesher://languages"]
    templates = await client.list_resource_templates()
    assert [t.uriTemplate for t in templates.resourceTemplates] == [
        "legesher://languages/{lang}/terms"
    ]


async def test_prompts_listed(client: ClientSession) -> None:
    prompts = await client.list_prompts()
    assert {p.name for p in prompts.prompts} == {
        "explain-in",
        "translate-review",
        "legibility-report",
    }


async def test_stdio_entry_point_serves_the_same_tools() -> None:
    """`python -m legesher_mcp` (what the console script runs) over real stdio."""
    params = StdioServerParameters(command=sys.executable, args=["-m", "legesher_mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            assert {tool.name for tool in result.tools} == EXPECTED_TOOLS
