"""Dump the Legesher MCP server's advertised surface as MCP JSON (CORE-1423).

What a client — or an enterprise MCP scanner — sees before it calls
anything: the tool list, the prompt list, and the resource list/templates,
in the shape ``tools/list``, ``prompts/list`` and ``resources/list`` put on
the wire. Written to a directory as three files so a static scanner can
read them without starting the server:

    uv run python scripts/dump_mcp_surface.py build/mcp-surface

The MCP surface scan workflow runs this and hands the result to an offline
analyzer. It is also the fastest way to eyeball what the package publishes:
descriptions are a public API, and this is them.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp.shared.memory import create_connected_server_and_client_session

from legesher_mcp.server import mcp as server


def _dump(items: list[Any]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json", exclude_none=True) for item in items]


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {path}")


async def dump_surface(out: Path) -> None:
    """Write tools.json, prompts.json and resources.json into ``out``."""
    out.mkdir(parents=True, exist_ok=True)
    async with create_connected_server_and_client_session(server) as session:
        tools = await session.list_tools()
        prompts = await session.list_prompts()
        resources = await session.list_resources()
        templates = await session.list_resource_templates()
    _write(out / "tools.json", {"tools": _dump(list(tools.tools))})
    _write(out / "prompts.json", {"prompts": _dump(list(prompts.prompts))})
    _write(
        out / "resources.json",
        {
            "resources": _dump(list(resources.resources)),
            "resourceTemplates": _dump(list(templates.resourceTemplates)),
        },
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: dump_mcp_surface.py <output-directory>", file=sys.stderr)
        return 2
    asyncio.run(dump_surface(Path(argv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
