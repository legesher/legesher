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

#: What makes a fold-only failure safe to leave alone. Each surface that tells
#: an agent to change nothing must state every one, or the instruction blesses
#: a form that does not compile, a vacuous result or a hidden name finding.
FOLD_EXCEPTION_CONDITIONS = (
    ("forward_valid", "is true"),
    ("finding_count", "is 0"),
    ("divergence_count", "equals the number listed"),
)


def _states(text: str, condition: str) -> bool:
    """``condition`` appears as a whole clause: followed by punctuation, so
    "is true or null" or "is 0 or more" does not count as stating it."""
    return re.search(re.escape(condition) + r"[,;.)]", text) is not None


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
        bullet = " ".join(_skill_playbook_routes()[layer].split())
        assert "by design" in bullet, f"skill {layer} entry is not routed as by design"
        assert "change nothing" in bullet.lower(), f"skill {layer} entry never says change nothing"
        assert "never rewrite the marks or digits to ascii" in bullet.lower(), (
            f"skill {layer} entry never forbids rewriting to ASCII"
        )
        for name, phrase in FOLD_EXCEPTION_CONDITIONS:
            assert _states(bullet, f"`{name}` {phrase}"), (
                f"skill {layer} entry omits `{name}` {phrase}"
            )
        assert "at least one" in bullet, f"skill {layer} entry allows an empty list"

    @pytest.mark.parametrize("layer", FOLDS)
    def test_agents_round_trip_rule_exempts_the_fold_layer(self, layer: str) -> None:
        rule = " ".join(_agents_rule(8).split())
        assert "Round-trip guarantee" in rule
        exception = rule.split("The one exception", 1)
        assert len(exception) == 2, "AGENTS rule 8 has no fold exception"
        sentence = exception[1]
        assert f"`{layer}`" in sentence, f"AGENTS rule 8 exception omits {layer}"
        assert "change nothing" in sentence.lower(), (
            "AGENTS rule 8 exception never says change nothing"
        )
        for name, phrase in FOLD_EXCEPTION_CONDITIONS:
            assert _states(sentence, f"`{name}` {phrase}"), f"AGENTS rule 8 omits `{name}` {phrase}"
        assert "at least one" in sentence, "AGENTS rule 8 allows an empty list"

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
        routing = description.split(". ", 1)[1]
        assert "are by design" in routing
        routed = routing.split(" are by design", 1)[0].rsplit(". ", 1)[-1]
        assert set(routed.split("/")) == set(FOLDS), (
            f"{tool_name} layer description routes {routed!r} as by design, not {FOLDS}"
        )
        assert "never rewrite the marks or digits to ascii" in routing.lower(), (
            f"{tool_name} layer description never forbids rewriting to ASCII"
        )
        assert routing.lower().rstrip(".").endswith("change nothing"), (
            f"{tool_name} layer description does not end in change nothing"
        )
        for name, phrase in FOLD_EXCEPTION_CONDITIONS:
            assert _states(routing, f"{name} {phrase}"), (
                f"{tool_name} layer description omits {name} {phrase}"
            )
        assert "at least one divergence is listed" in routing, (
            f"{tool_name} layer description allows an empty list"
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
