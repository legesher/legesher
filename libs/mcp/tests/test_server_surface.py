"""The advertised surface: six tools, two resources, three prompts, stdio."""

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
    "validate_identifier_translations",
}


async def test_exactly_six_coarse_tools(client: ClientSession) -> None:
    result = await client.list_tools()
    assert {tool.name for tool in result.tools} == EXPECTED_TOOLS


async def test_every_tool_has_description_and_schemas(client: ClientSession) -> None:
    result = await client.list_tools()
    for tool in result.tools:
        assert tool.description, f"{tool.name} has no description"
        assert tool.inputSchema.get("properties"), f"{tool.name} has no input schema"
        assert tool.outputSchema, f"{tool.name} publishes no output schema"


async def test_catalog_resource_and_terms_templates_listed(client: ClientSession) -> None:
    resources = await client.list_resources()
    assert [str(r.uri) for r in resources.resources] == ["legesher://languages"]
    templates = await client.list_resource_templates()
    assert {t.uriTemplate for t in templates.resourceTemplates} == {
        "legesher://languages/{lang}/terms",
        "legesher://languages/{lang}/terms/{python_version}",
    }


async def test_every_tool_is_annotated_read_only(client: ClientSession) -> None:
    """The six tools declare the posture they actually have.

    Read-only, idempotent, closed-world (no network) — asserted here so a
    future tool that writes, mutates, or reaches outside the local packs
    cannot inherit the hints by accident. Changing this test is the
    deliberate act that a change in posture requires.
    """
    result = await client.list_tools()
    assert {tool.name for tool in result.tools} == EXPECTED_TOOLS
    for tool in result.tools:
        annotations = tool.annotations
        assert annotations is not None, f"{tool.name} declares no annotations"
        assert annotations.readOnlyHint is True, f"{tool.name} is not marked read-only"
        assert annotations.idempotentHint is True, f"{tool.name} is not marked idempotent"
        assert annotations.openWorldHint is False, f"{tool.name} is not marked closed-world"
        assert annotations.destructiveHint is False, f"{tool.name} is not marked non-destructive"


async def test_published_version_enum_matches_the_pack_index(client: ClientSession) -> None:
    """Every tool publishes the versions the installed packs actually cover.

    Guards the derivation (CORE-1806): the enum is built from the pack
    version index, so a hand-edited list here would diverge from disk.
    """
    from legesher_i18n.pack_loader import LanguagePackLoader

    from legesher_mcp.schemas import SUPPORTED_PYTHON_VERSIONS

    on_disk = set(LanguagePackLoader().list_available_versions("python"))
    assert set(SUPPORTED_PYTHON_VERSIONS) == on_disk

    result = await client.list_tools()
    for tool in result.tools:
        published = tool.inputSchema["properties"]["python_version"]
        assert set(published["enum"]) == on_disk, f"{tool.name} publishes a stale version enum"


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
