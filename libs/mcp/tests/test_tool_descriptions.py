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

import json
import re
from pathlib import Path

import pytest
from legesher_core.round_trip import FOLD_LAYERS, Layer
from mcp import ClientSession

pytestmark = pytest.mark.anyio

_MCP_ROOT = Path(__file__).resolve().parents[1]
SKILL = _MCP_ROOT / "skills" / "legesher-localized-code" / "SKILL.md"
AGENTS_TEMPLATE = _MCP_ROOT / "templates" / "AGENTS-template.md"

TRANSLATE_TOOLS = ("translate_to_native", "translate_to_source")

#: Every layer the engine can report, read from the engine itself, so a layer
#: added there fails here until each agent-facing surface names it.
ENGINE_LAYERS = frozenset(layer.value for layer in Layer)
FOLDS = sorted(layer.value for layer in FOLD_LAYERS)


def _skill_playbook_routes() -> dict[str, str]:
    """Each layer the skill's "When something doesn't map" list routes,
    mapped to the text of the bullet that routes it."""
    text = SKILL.read_text(encoding="utf-8")
    section = text.split("## When something doesn't map", 1)[1].split("\n## ", 1)[0]
    routes: dict[str, str] = {}
    for bullet in re.split(r"\n(?=- \*\*)", section):
        head = re.match(r"- \*\*(.+?)\*\*", bullet)
        if head is None:
            continue
        for name in re.findall(r"`([^`]+)`", head.group(1)):
            assert name not in routes, f"skill routes layer {name!r} twice"
            routes[name] = bullet
    return routes


def _agents_rule(number: int) -> str:
    text = AGENTS_TEMPLATE.read_text(encoding="utf-8")
    match = re.search(rf"^{number}\. .*?(?=^\d+\. |^## |\Z)", text, re.M | re.S)
    assert match is not None, f"AGENTS template has no rule {number}"
    return match.group(0)


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


class TestLayerVocabulary:
    """The engine's layers, named the same way on every surface an agent
    reads (CORE-1192 and CORE-493 added two the docs did not name)."""

    def test_skill_playbook_routes_exactly_the_engine_layers(self) -> None:
        routed = set(_skill_playbook_routes())
        assert routed == ENGINE_LAYERS, (
            f"skill playbook misses {sorted(ENGINE_LAYERS - routed)}, "
            f"names unknown {sorted(routed - ENGINE_LAYERS)}"
        )

    @pytest.mark.parametrize("layer", FOLDS)
    def test_skill_says_a_fold_layer_changes_nothing(self, layer: str) -> None:
        bullet = _skill_playbook_routes()[layer]
        assert "by design" in bullet
        assert "Change nothing" in bullet

    @pytest.mark.parametrize("layer", FOLDS)
    def test_agents_round_trip_rule_exempts_the_fold_layer(self, layer: str) -> None:
        rule = _agents_rule(8)
        assert "Round-trip guarantee" in rule
        assert f"`{layer}`" in rule
        assert "by design" in rule

    @pytest.mark.parametrize("tool_name", TRANSLATE_TOOLS)
    async def test_published_layer_description_lists_exactly_the_engine_layers(
        self, client: ClientSession, tool_name: str
    ) -> None:
        # The output schema the client receives, not the model in-process.
        result = await client.list_tools()
        tool = next(t for t in result.tools if t.name == tool_name)
        assert tool.outputSchema is not None
        defs = json.loads(json.dumps(tool.outputSchema))["$defs"]
        description = defs["DivergenceModel"]["properties"]["layer"]["description"]
        listed = {name.strip() for name in description.split(". ", 1)[0].split("|")}
        assert listed == ENGINE_LAYERS, (
            f"{tool_name} layer description misses {sorted(ENGINE_LAYERS - listed)}, "
            f"names unknown {sorted(listed - ENGINE_LAYERS)}"
        )
        for layer in FOLDS:
            assert layer in description.split(". ", 1)[1], (
                f"{tool_name} layer description never routes {layer!r}"
            )


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
