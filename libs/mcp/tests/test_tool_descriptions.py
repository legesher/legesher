"""The agent-facing surfaces route verification through the call (CORE-1813).

The skill and the AGENTS template used to instruct agents to round-trip by
hand — call both translate tools and compare the renderings themselves.
That judgement is exactly what ``verify_round_trip`` exists to replace, so
these tests pin the routing in both directions: the flag is named on every
surface, and the old eyeball-the-output instruction is gone. The tripwire
strings are substrings that existed in the pre-flag documents, so a revert
of the doc edit fails here rather than passing silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp import ClientSession

pytestmark = pytest.mark.anyio

_MCP_ROOT = Path(__file__).resolve().parents[1]
SKILL = _MCP_ROOT / "skills" / "legesher-localized-code" / "SKILL.md"
AGENTS_TEMPLATE = _MCP_ROOT / "templates" / "AGENTS-template.md"

TRANSLATE_TOOLS = ("translate_to_native", "translate_to_source")


class TestSkillDocument:
    def test_routes_verification_through_the_flag(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        assert "verify_round_trip" in text

    def test_manual_comparison_instruction_is_gone(self) -> None:
        # Tripwire: the pre-flag step 3 told the agent to translate both
        # ways and judge byte-identity itself. This exact substring exists
        # in that wording and in no other sentence of the file.
        text = SKILL.read_text(encoding="utf-8")
        assert "Byte-identical output is the" not in text

    def test_instructs_quoting_the_verdict(self) -> None:
        # The verdict line is quoted, never restated — restating is the
        # same by-eye judgement the flag removes.
        text = SKILL.read_text(encoding="utf-8")
        assert "quote" in text.lower()
        assert "verdict" in text.lower()

    def test_playbook_covers_the_collision_layer(self) -> None:
        # The layer-keyed playbook must route collisions to a rename, not
        # a pack bug report (CORE-1840's misattribution).
        text = SKILL.read_text(encoding="utf-8")
        assert "`collision`" in text


class TestAgentsTemplate:
    def test_routes_verification_through_the_flag(self) -> None:
        text = AGENTS_TEMPLATE.read_text(encoding="utf-8")
        assert "verify_round_trip" in text

    def test_forbids_comparing_renderings_by_hand(self) -> None:
        text = AGENTS_TEMPLATE.read_text(encoding="utf-8")
        assert "never by comparing the two renderings yourself" in text


class TestToolSurface:
    async def test_tool_count_tripwire(self, client: ClientSession) -> None:
        # The skill's tool table is written against this surface; a grown
        # surface means the table (and this file) need a deliberate pass.
        result = await client.list_tools()
        assert len(result.tools) <= 8

    async def test_every_tool_has_a_description(self, client: ClientSession) -> None:
        result = await client.list_tools()
        for tool in result.tools:
            assert tool.description, f"{tool.name} has no description"

    @pytest.mark.parametrize("tool_name", TRANSLATE_TOOLS)
    async def test_flag_description_owns_the_by_eye_judgement(
        self, client: ClientSession, tool_name: str
    ) -> None:
        # The published schema is the surface agents actually read; it must
        # say why the flag replaces manual comparison.
        result = await client.list_tools()
        tool = next(t for t in result.tools if t.name == tool_name)
        description = tool.inputSchema["properties"]["verify_round_trip"]["description"]
        assert "by eye" in description
