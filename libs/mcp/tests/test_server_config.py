"""Server self-reporting and logging posture: version truth, quiet stderr."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import legesher_mcp

pytestmark = pytest.mark.anyio


async def test_initialize_reports_the_package_version() -> None:
    """serverInfo must carry legesher_mcp's own version, not the SDK's."""
    params = StdioServerParameters(command=sys.executable, args=["-m", "legesher_mcp"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.serverInfo.name == "legesher"
            assert init.serverInfo.version == legesher_mcp.__version__


async def test_stdio_default_is_quiet_on_stderr(tmp_path: Path) -> None:
    """A normal session must not spray log lines onto stderr by default."""
    errfile = tmp_path / "server-stderr.log"
    params = StdioServerParameters(command=sys.executable, args=["-m", "legesher_mcp"])
    with errfile.open("w", encoding="utf-8") as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # Triggers both SDK request logging and the engine's
                # pack-load logging, the two INFO sources.
                await session.call_tool(
                    "lookup_keyword_mapping", {"language": "es", "terms": ["def"]}
                )
    assert errfile.read_text(encoding="utf-8") == ""


def test_log_level_defaults_to_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    from legesher_mcp.server import _log_level_from_env

    monkeypatch.delenv("LEGESHER_MCP_LOG_LEVEL", raising=False)
    assert _log_level_from_env() == "WARNING"


def test_log_level_env_override_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    from legesher_mcp.server import _log_level_from_env

    monkeypatch.setenv("LEGESHER_MCP_LOG_LEVEL", "debug")
    assert _log_level_from_env() == "DEBUG"


def test_log_level_invalid_value_falls_back_to_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    from legesher_mcp.server import _log_level_from_env

    monkeypatch.setenv("LEGESHER_MCP_LOG_LEVEL", "verbose")
    assert _log_level_from_env() == "WARNING"
