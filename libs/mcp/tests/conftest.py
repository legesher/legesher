"""Shared fixtures: every test exercises the server THROUGH the MCP layer.

The ``client`` fixture connects a real MCP client session to the server
over the SDK's in-memory transport — the same request/response framing a
stdio client produces, without the subprocess (one stdio subprocess test
lives in test_server_surface.py).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from mcp import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import CallToolResult

from legesher_mcp.server import mcp as server


@pytest.fixture
def anyio_backend() -> str:
    """Run anyio-marked tests on asyncio only."""
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[ClientSession]:
    """In-memory MCP client session connected to the real server."""
    async with create_connected_server_and_client_session(server) as session:
        yield session


async def call_ok(client: ClientSession, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """Call a tool, assert success, and return its structured content."""
    result = await client.call_tool(tool, args)
    assert not result.isError, f"{tool} errored: {result.content}"
    assert result.structuredContent is not None
    return result.structuredContent


async def call_err(client: ClientSession, tool: str, args: dict[str, Any]) -> str:
    """Call a tool, assert an isError result, and return its message text."""
    result = await client.call_tool(tool, args)
    assert result.isError, f"{tool} unexpectedly succeeded: {result.structuredContent}"
    return _error_text(result)


def _error_text(result: CallToolResult) -> str:
    parts = [content.text for content in result.content if hasattr(content, "text")]
    return "\n".join(parts)


def assert_sanitized(message: str) -> None:
    """Error text must never leak filesystem paths or stack traces."""
    assert "/Users/" not in message
    assert ".yml" not in message
    assert "Traceback" not in message
