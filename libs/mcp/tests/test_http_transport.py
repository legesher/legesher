"""The streamable HTTP entry (CORE-1420): stateless, JSON, loopback-first.

Everything runs in process: the ASGI app from ``create_http_app`` is
driven through httpx's ASGI transport — the SDK's streamable HTTP client
for full sessions, raw POSTs for the transport-level assertions. What is
pinned here:

- the same six tools serve over HTTP as over stdio, end to end against
  the local engine;
- the posture is stateless with plain JSON responses: every request is
  self-contained (no session id to acquire or replay) and responses are
  ``application/json``, not SSE;
- the Origin header is validated when present — a cross-origin browser
  page (the DNS-rebinding vector) is rejected, while clients that send
  no Origin pass;
- the CLI refuses wildcard binds and defaults to loopback;
- a wrapping ASGI middleware can supply per-request context that the
  entitlement gate reads — the mechanism a hosted deployment uses.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version as distribution_version
from typing import Any

import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from starlette.applications import Starlette
from starlette.types import Receive, Scope, Send

from legesher_mcp.gate import ALLOW, GateDecision, request_context
from legesher_mcp.server import _parse_args, create_http_app, create_server
from tests.conftest import call_ok

pytestmark = pytest.mark.anyio

BASE_URL = "http://127.0.0.1:8000"
MCP_URL = f"{BASE_URL}/mcp"

#: The transport's required headers for a raw JSON-RPC POST.
_RPC_HEADERS = {
    "accept": "application/json, text/event-stream",
    "content-type": "application/json",
    "mcp-protocol-version": "2025-06-18",
}

_LIST_TOOLS = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

EXPECTED_TOOLS = {
    "translate_to_native",
    "translate_to_source",
    "explain_in_language",
    "lookup_keyword_mapping",
    "map_existing_codebase",
    "validate_identifier_translations",
}


@asynccontextmanager
async def _serving(
    app: Starlette, *, lifespan_app: Starlette | None = None, **client_kwargs: Any
) -> AsyncIterator[httpx.AsyncClient]:
    """Serve an ASGI app in process, with its lifespan running.

    httpx's ASGITransport never sends the lifespan scope, and the SDK's
    session manager refuses requests until its lifespan task group is up —
    so the lifespan is entered explicitly here. ``lifespan_app`` names the
    Starlette app owning the lifespan when ``app`` is a wrapper around it.
    """
    inner = lifespan_app if lifespan_app is not None else app
    async with inner.router.lifespan_context(inner):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url=BASE_URL, **client_kwargs
        ) as client:
            yield client


@asynccontextmanager
async def _http_session(client: httpx.AsyncClient) -> AsyncIterator[ClientSession]:
    """A fully initialized MCP session over the in-process HTTP transport."""
    async with streamable_http_client(MCP_URL, http_client=client) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


# -- the served surface -----------------------------------------------------


async def test_http_serves_the_same_six_tools() -> None:
    async with _serving(create_http_app()) as client:
        async with _http_session(client) as session:
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == EXPECTED_TOOLS


async def test_http_initialize_reports_the_server_identity() -> None:
    async with _serving(create_http_app()) as client:
        async with streamable_http_client(MCP_URL, http_client=client) as (read, write, _):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                assert init.serverInfo.name == "legesher"
                assert init.serverInfo.version == distribution_version("legesher-mcp")


async def test_http_translates_end_to_end_with_the_local_backend() -> None:
    async with _serving(create_http_app()) as client:
        async with _http_session(client) as session:
            result = await call_ok(
                session,
                "translate_to_native",
                {"source": "def greet(name):\n    print(name)\n", "target_lang": "es"},
            )
            assert "definir greet(name):" in result["translated_source"]
            assert result["pivoted"] is False


# -- stateless, JSON --------------------------------------------------------


async def test_each_request_is_self_contained_and_answered_as_json() -> None:
    """No initialize, no session id — a lone tools/list POST just works.

    That is the stateless contract: nothing about an earlier request is
    needed for the next one. The JSON contract rides the same assertion:
    the answer is a plain ``application/json`` body, not an SSE stream.
    """
    async with _serving(create_http_app()) as client:
        response = await client.post(MCP_URL, headers=_RPC_HEADERS, json=_LIST_TOOLS)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert "mcp-session-id" not in response.headers
        payload = response.json()
        names = {tool["name"] for tool in payload["result"]["tools"]}
        assert names == EXPECTED_TOOLS


# -- Origin validation (DNS-rebinding defense) -------------------------------


async def test_a_cross_origin_request_is_rejected() -> None:
    async with _serving(create_http_app()) as client:
        response = await client.post(
            MCP_URL,
            headers={**_RPC_HEADERS, "origin": "http://evil.example"},
            json=_LIST_TOOLS,
        )
        assert response.status_code == 403


async def test_a_loopback_origin_is_accepted() -> None:
    async with _serving(create_http_app()) as client:
        response = await client.post(
            MCP_URL,
            headers={**_RPC_HEADERS, "origin": f"{BASE_URL}"},
            json=_LIST_TOOLS,
        )
        assert response.status_code == 200


async def test_an_absent_origin_is_accepted() -> None:
    """Non-browser MCP clients send no Origin; they must not be locked out."""
    async with _serving(create_http_app()) as client:
        response = await client.post(MCP_URL, headers=_RPC_HEADERS, json=_LIST_TOOLS)
        assert response.status_code == 200


async def test_a_non_loopback_bind_derives_its_own_allowlist() -> None:
    """Origin/Host validation follows the bound interface, not a fixed list."""
    app = create_http_app(host="192.0.2.7")  # TEST-NET-1: never routable
    async with _serving(app) as client:
        own_origin = await client.post(
            "http://192.0.2.7:8000/mcp",
            headers={**_RPC_HEADERS, "origin": "http://192.0.2.7:8000"},
            json=_LIST_TOOLS,
        )
        assert own_origin.status_code == 200
        foreign_origin = await client.post(
            "http://192.0.2.7:8000/mcp",
            headers={**_RPC_HEADERS, "origin": "http://127.0.0.1:8000"},
            json=_LIST_TOOLS,
        )
        assert foreign_origin.status_code == 403


# -- per-request context for the gate ----------------------------------------


class _EntitlementsFromHeader:
    """Stand-in for a deployment wrapper: reads a header, sets the context.

    This is the documented integration shape: an ASGI middleware resolves
    the caller (here: a test header; in a real deployment, its auth) and
    exposes the result to the gate through ``request_context`` for exactly
    the duration of the request.
    """

    def __init__(self, app: Starlette) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        headers = {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        entitled = headers.get("x-test-entitled") == "yes"
        with request_context({"entitled": entitled}):
            await self._app(scope, receive, send)


def _account_gate(tool: str, context: Any) -> GateDecision:
    if isinstance(context, dict) and context.get("entitled"):
        return ALLOW
    return GateDecision(allowed=False)


MAP_ARGS = {"files": [{"path": "a.py", "source": "x = 1\n"}], "target_lang": "es"}


async def test_middleware_supplied_context_reaches_the_gate_per_request() -> None:
    # A fresh app per serving block: the SDK's session manager runs once
    # per instance, and each block runs its own lifespan.
    def build() -> tuple[Starlette, _EntitlementsFromHeader]:
        inner = create_http_app(gate=_account_gate)
        return inner, _EntitlementsFromHeader(inner)

    inner, wrapped = build()
    async with _serving(wrapped, lifespan_app=inner) as anonymous:  # type: ignore[arg-type]
        async with _http_session(anonymous) as session:
            denied = await session.call_tool("map_existing_codebase", MAP_ARGS)
            assert denied.isError
            text = "".join(getattr(content, "text", "") for content in denied.content)
            assert text.startswith("entitlement_required:")

    inner, wrapped = build()
    async with _serving(
        wrapped, lifespan_app=inner, headers={"x-test-entitled": "yes"}
    ) as entitled:  # type: ignore[arg-type]
        async with _http_session(entitled) as session:
            allowed = await call_ok(session, "map_existing_codebase", MAP_ARGS)
            assert allowed["summary"]["files_total"] == 1


# -- CLI surface -------------------------------------------------------------


def test_cli_defaults_to_stdio_on_loopback() -> None:
    args = _parse_args([])
    assert args.transport == "stdio"
    assert args.host == "127.0.0.1"
    assert args.port == 8000


def test_cli_parses_the_http_flags() -> None:
    args = _parse_args(["--transport", "streamable-http", "--host", "192.0.2.7", "--port", "9132"])
    assert args.transport == "streamable-http"
    assert args.host == "192.0.2.7"
    assert args.port == 9132


@pytest.mark.parametrize("host", ["0.0.0.0", "::", ""])  # noqa: S104
def test_cli_refuses_wildcard_binds(host: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        _parse_args(["--transport", "streamable-http", "--host", host])
    assert "wildcard" in capsys.readouterr().err


def test_the_server_binds_loopback_by_default() -> None:
    assert create_server().settings.host == "127.0.0.1"


def test_the_http_posture_is_stateless_json() -> None:
    server = create_server()
    assert server.settings.stateless_http is True
    assert server.settings.json_response is True
