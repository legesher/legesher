"""The entitlement seam (CORE-1420): default-open, listed-not-hidden.

Semantics decided on CORE-2008:

- gated tools stay LISTED for every caller — entitlement is checked only
  when a gated tool is called, never by hiding it;
- a denial is an actionable message (what the tool does, that it needs a
  Legesher account on the hosted instance, where to go) — never an opaque
  failure;
- only ``map_existing_codebase`` can ever be gated, and only by a
  deployment that installs a gate. ``validate_identifier_translations``
  is permanently free by construction: the gate is never consulted for
  any tool outside :data:`GATEABLE_TOOLS`;
- the default policy allows everything, and the stdio entry never
  installs a gate — local and self-hosted use is never gated.
"""

from __future__ import annotations

from typing import Any

import pytest
from mcp import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from legesher_mcp.gate import (
    ALLOW,
    GATEABLE_TOOLS,
    GateDecision,
    allow_all,
    request_context,
)
from legesher_mcp.server import create_server
from tests.conftest import call_err, call_ok

pytestmark = pytest.mark.anyio

MAP_ARGS = {"files": [{"path": "a.py", "source": "x = 1\n"}], "target_lang": "es"}
VALIDATE_ARGS = {
    "proposals": [{"source": "greet", "translation": "saludar"}],
    "target_lang": "es",
}
TRANSLATE_ARGS = {"source": "x = 1\n", "target_lang": "es"}


def deny_everything(tool: str, context: Any) -> GateDecision:
    """A hostile policy: denies every tool it is ever asked about."""
    return GateDecision(allowed=False)


# -- the seam's shape -------------------------------------------------------


def test_only_map_existing_codebase_is_gateable() -> None:
    """The open package, not the deployment, bounds what can be gated."""
    assert GATEABLE_TOOLS == frozenset({"map_existing_codebase"})


def test_validate_identifier_translations_is_permanently_free() -> None:
    assert "validate_identifier_translations" not in GATEABLE_TOOLS


def test_the_default_policy_allows_everything() -> None:
    assert allow_all("map_existing_codebase", None) == ALLOW
    assert allow_all("anything_else", {"user": "u"}) == ALLOW


# -- default-open behavior --------------------------------------------------


async def test_no_gate_means_every_tool_works(client: ClientSession) -> None:
    """The module-level (stdio) server installs no gate: nothing is gated."""
    result = await call_ok(client, "map_existing_codebase", MAP_ARGS)
    assert result["summary"]["files_total"] == 1


# -- deny-with-message behavior ---------------------------------------------


async def test_a_gated_tool_stays_listed() -> None:
    """Denial happens at call time; the tool list never hides a tool."""
    server = create_server(gate=deny_everything)
    async with create_connected_server_and_client_session(server) as session:
        tools = await session.list_tools()
        assert "map_existing_codebase" in {tool.name for tool in tools.tools}
        assert len(tools.tools) == 6


async def test_an_unentitled_call_gets_the_actionable_message() -> None:
    server = create_server(gate=deny_everything)
    async with create_connected_server_and_client_session(server) as session:
        message = await call_err(session, "map_existing_codebase", MAP_ARGS)
    # Machine code first, in the server's error voice.
    assert message.startswith("entitlement_required:")
    # What the tool does…
    assert "map_existing_codebase" in message
    # …that it needs an account on the hosted instance…
    assert "Legesher account" in message
    # …and where to go.
    assert "legesher.io" in message


async def test_a_gate_denial_can_carry_a_deployment_detail() -> None:
    def deny_with_detail(tool: str, context: Any) -> GateDecision:
        return GateDecision(allowed=False, detail="Sign-in code: ABCD-1234.")

    server = create_server(gate=deny_with_detail)
    async with create_connected_server_and_client_session(server) as session:
        message = await call_err(session, "map_existing_codebase", MAP_ARGS)
    assert "Sign-in code: ABCD-1234." in message
    # The package's own copy still leads; the detail only extends it.
    assert message.startswith("entitlement_required:")


async def test_a_deny_everything_gate_cannot_touch_the_free_tools() -> None:
    """Tools outside GATEABLE_TOOLS never see the gate — by construction."""
    server = create_server(gate=deny_everything)
    async with create_connected_server_and_client_session(server) as session:
        validated = await call_ok(session, "validate_identifier_translations", VALIDATE_ARGS)
        assert validated["accepted"] == {"greet": "saludar"}
        translated = await call_ok(session, "translate_to_native", TRANSLATE_ARGS)
        assert translated["translated_source"]


async def test_the_gate_is_not_consulted_for_ungated_tools() -> None:
    seen: list[str] = []

    def recording(tool: str, context: Any) -> GateDecision:
        seen.append(tool)
        return ALLOW

    server = create_server(gate=recording)
    async with create_connected_server_and_client_session(server) as session:
        await call_ok(session, "translate_to_native", TRANSLATE_ARGS)
        await call_ok(session, "validate_identifier_translations", VALIDATE_ARGS)
        assert seen == []
        await call_ok(session, "map_existing_codebase", MAP_ARGS)
    assert seen == ["map_existing_codebase"]


# -- per-request context ----------------------------------------------------


async def test_the_gate_receives_the_ambient_request_context() -> None:
    """A wrapper (e.g. ASGI middleware) supplies context via request_context.

    The gate reads whatever the surrounding execution context carries; the
    HTTP transport test proves the same mechanism per-request through real
    middleware.
    """
    seen: list[tuple[str, Any]] = []

    def recording(tool: str, context: Any) -> GateDecision:
        seen.append((tool, context))
        return ALLOW

    server = create_server(gate=recording)
    with request_context({"subject": "key:abc123"}):
        async with create_connected_server_and_client_session(server) as session:
            await call_ok(session, "map_existing_codebase", MAP_ARGS)
    assert seen == [("map_existing_codebase", {"subject": "key:abc123"})]


async def test_the_context_defaults_to_none() -> None:
    seen: list[Any] = []

    def recording(tool: str, context: Any) -> GateDecision:
        seen.append(context)
        return ALLOW

    server = create_server(gate=recording)
    async with create_connected_server_and_client_session(server) as session:
        await call_ok(session, "map_existing_codebase", MAP_ARGS)
    assert seen == [None]
