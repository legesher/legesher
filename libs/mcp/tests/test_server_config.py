"""Server self-reporting and logging posture: version truth, quiet stderr."""

from __future__ import annotations

import os
import sys
from importlib.metadata import version as distribution_version
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import legesher_mcp

pytestmark = pytest.mark.anyio

#: Tokens that mark a line as chatty logging rather than a real problem.
_NOISY_LEVELS = ("DEBUG", "INFO")

#: Variables these tests control themselves — never inherited from the shell.
_OWNED_VARS = frozenset({"LEGESHER_MCP_LOG_LEVEL"})


def _spawn_params(**env: str) -> StdioServerParameters:
    """`python -m legesher_mcp` over stdio, with extra env vars merged in.

    The ambient environment is inherited (the child needs PATH and the
    interpreter's own variables) but LEGESHER_MCP_LOG_LEVEL is always
    stripped first: otherwise a developer who exports it makes the
    quiet-default test fail, and — worse — a test that means to assert the
    *default* would quietly be asserting their setting instead.
    """
    inherited = {key: value for key, value in os.environ.items() if key not in _OWNED_VARS}
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "legesher_mcp"],
        env={**inherited, **env},
    )


def _noisy_lines(stderr_text: str) -> list[str]:
    """Stderr lines that carry an INFO/DEBUG level token."""
    return [
        line for line in stderr_text.splitlines() if any(level in line for level in _NOISY_LEVELS)
    ]


async def _drive_one_session(params: StdioServerParameters, errlog: object) -> None:
    """Initialize and make one tool call — the two INFO-emitting moments."""
    async with stdio_client(params, errlog=errlog) as (read, write):  # type: ignore[arg-type]
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Triggers both SDK request logging and the engine's pack-load
            # logging, the two INFO sources.
            await session.call_tool("lookup_keyword_mapping", {"language": "es", "terms": ["def"]})


async def test_initialize_reports_the_distribution_version() -> None:
    """serverInfo must carry legesher-mcp's own version, not the SDK's.

    Asserted against the installed distribution metadata (which comes from
    `libs/mcp/pyproject.toml`), not against `legesher_mcp.__version__` —
    otherwise the test would compare the value to itself and pass even if
    both had drifted from the shipped wheel.
    """
    params = _spawn_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.serverInfo.name == "legesher"
            assert init.serverInfo.version == distribution_version("legesher-mcp")
            # The bug this guards (CORE-1737): reporting the SDK's version.
            assert init.serverInfo.version != distribution_version("mcp")


def test_dunder_version_tracks_the_distribution() -> None:
    """`__version__` is the distribution's version, not a hand-kept copy."""
    assert legesher_mcp.__version__ == distribution_version("legesher-mcp")


async def test_stdio_default_is_quiet_on_stderr(tmp_path: Path) -> None:
    """A normal session must not log INFO/DEBUG noise to stderr by default.

    The shipped invariant is "no chatty logging", not "stderr is byte-empty"
    — a genuine warning or a traceback from the runtime is allowed through.
    """
    errfile = tmp_path / "server-stderr.log"
    params = _spawn_params()
    with errfile.open("w", encoding="utf-8") as errlog:
        await _drive_one_session(params, errlog)
    stderr_text = errfile.read_text(encoding="utf-8")
    assert _noisy_lines(stderr_text) == [], f"unexpected log noise: {stderr_text!r}"


async def test_stdio_log_level_env_var_restores_logging(tmp_path: Path) -> None:
    """LEGESHER_MCP_LOG_LEVEL=INFO must actually reach the running server.

    The positive control for the quiet-default test above: without this, a
    server that logged nothing under any setting would pass both.
    """
    errfile = tmp_path / "server-stderr-info.log"
    params = _spawn_params(LEGESHER_MCP_LOG_LEVEL="INFO")
    with errfile.open("w", encoding="utf-8") as errlog:
        await _drive_one_session(params, errlog)
    stderr_text = errfile.read_text(encoding="utf-8")
    assert stderr_text.strip(), "INFO level produced no stderr output at all"
    assert _noisy_lines(stderr_text), f"no INFO/DEBUG lines at INFO level: {stderr_text!r}"


def test_log_level_defaults_to_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    from legesher_mcp.server import _log_level_from_env

    monkeypatch.delenv("LEGESHER_MCP_LOG_LEVEL", raising=False)
    assert _log_level_from_env() == "WARNING"


def test_log_level_env_override_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    from legesher_mcp.server import _log_level_from_env

    monkeypatch.setenv("LEGESHER_MCP_LOG_LEVEL", "debug")
    assert _log_level_from_env() == "DEBUG"


def test_log_level_tolerates_surrounding_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    """Padded values (a stray space in a client config) still resolve."""
    from legesher_mcp.server import _log_level_from_env

    monkeypatch.setenv("LEGESHER_MCP_LOG_LEVEL", "  debug  ")
    assert _log_level_from_env() == "DEBUG"


def test_log_level_invalid_value_falls_back_to_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    from legesher_mcp.server import _log_level_from_env

    monkeypatch.setenv("LEGESHER_MCP_LOG_LEVEL", "verbose")
    assert _log_level_from_env() == "WARNING"


def test_accepted_log_levels_are_derived_from_the_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every name in the _LogLevel Literal must be accepted verbatim."""
    from legesher_mcp.server import _LOG_LEVELS, _log_level_from_env

    assert _LOG_LEVELS == ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    for level in _LOG_LEVELS:
        monkeypatch.setenv("LEGESHER_MCP_LOG_LEVEL", level)
        assert _log_level_from_env() == level
