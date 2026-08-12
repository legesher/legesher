"""The real host install path: locally built wheels, fresh venv (CORE-1746).

Every other test in this suite runs inside the monorepo workspace, where
every pack and dependency is already importable and the working directory
is the repo. A real MCP host does none of that: it spawns the server from
an arbitrary directory, with a stripped environment, against whatever the
package index served.

This module builds the wheels, installs them into an empty virtualenv in an
empty directory, and drives a stdio session against that — so the artifact
is proven to work outside the workspace *before* an index ever serves it.
That is why it is a publish gate for CORE-626 and not merely a nice check.

Marked ``scheduled``: building wheels and creating a venv costs far too much
for a per-commit run. Run it with ``make test-mcp-scheduled`` (or
``uv run pytest -m scheduled``) before publishing.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

pytestmark = [pytest.mark.anyio, pytest.mark.scheduled]

#: Only the runtime packages a host would get from an index. The language
#: packs are deliberately NOT installed separately — legesher-i18n bundles
#: them, which is exactly the property this module verifies.
WHEEL_PACKAGES = ("legesher-core", "legesher-i18n", "legesher-mcp")

#: A language the registry knows and a pack exists for, used for the live call.
LIVE_LANGUAGE = "es"


def _monorepo_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "libs" / "mcp").is_dir() and (parent / "uv.lock").is_file():
            return parent
    return None


def _minimal_env(venv: Path) -> dict[str, str]:
    """What a host that strips the environment actually leaves behind.

    No PYTHONPATH, no VIRTUAL_ENV, no workspace markers — if the server needs
    any of them to find its packs, this is where that shows up.
    """
    env = {"PATH": f"{venv / 'bin'}:/usr/bin:/bin"}
    # Windows needs SYSTEMROOT for sockets; harmless to carry when present.
    if "SYSTEMROOT" in os.environ:  # pragma: no cover — not exercised on CI
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return env


@pytest.fixture(scope="module")
def clean_install(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Build the wheels, install them into a fresh venv, return (python, cwd).

    Synchronous and module-scoped on purpose: the work is subprocess-bound
    and far too slow to repeat per test.
    """
    root = _monorepo_root()
    if root is None:  # pragma: no cover — only when run from an installed wheel
        pytest.skip("needs the monorepo checkout to build wheels")
    if shutil.which("uv") is None:  # pragma: no cover — uv is the repo's toolchain
        pytest.skip("needs `uv` on PATH to build wheels and create the venv")

    base = tmp_path_factory.mktemp("clean-env")
    wheelhouse = base / "wheelhouse"
    venv = base / "venv"
    # An empty directory with no relationship to the repo: the server's cwd.
    workdir = base / "elsewhere"
    workdir.mkdir()

    for package in WHEEL_PACKAGES:
        subprocess.run(
            ["uv", "build", "--package", package, "--wheel", "--out-dir", str(wheelhouse)],
            cwd=root,
            check=True,
            capture_output=True,
        )

    wheels = sorted(str(path) for path in wheelhouse.glob("*.whl"))
    assert len(wheels) == len(WHEEL_PACKAGES), f"expected one wheel per package, got {wheels}"

    subprocess.run(["uv", "venv", str(venv)], check=True, capture_output=True)
    python = venv / "bin" / "python"
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), *wheels],
        check=True,
        capture_output=True,
    )
    return python, workdir


def _run_in_venv(python: Path, cwd: Path, code: str) -> str:
    """Execute a snippet inside the clean venv, with the stripped env."""
    completed = subprocess.run(
        [str(python), "-c", code],
        cwd=cwd,
        env=_minimal_env(python.parent.parent),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _server_params(python: Path, cwd: Path) -> StdioServerParameters:
    """Exactly what a host does: run the module, elsewhere, with no env."""
    return StdioServerParameters(
        command=str(python),
        args=["-m", "legesher_mcp"],
        env=_minimal_env(python.parent.parent),
        cwd=str(cwd),
    )


# -- the install itself ----------------------------------------------------


def test_the_wheel_installs_and_imports(clean_install: tuple[Path, Path]) -> None:
    python, workdir = clean_install
    version = _run_in_venv(
        python,
        workdir,
        "import legesher_mcp; print(legesher_mcp.__version__)",
    )
    assert version and version != "0.0.0.dev0", (
        "the installed wheel reports no distribution version — "
        "importlib.metadata could not see itself"
    )


def test_packs_are_discoverable_without_the_workspace(
    clean_install: tuple[Path, Path],
) -> None:
    """Discovery must not depend on the cwd, the env, or the repo layout.

    legesher-i18n ships the packs inside the wheel, so a bare install can
    translate. If this regresses, `uvx legesher-mcp` becomes useless until
    the user hunts down pack packages by hand.
    """
    python, workdir = clean_install
    payload = _run_in_venv(
        python,
        workdir,
        "import json\n"
        "from legesher_i18n.pack_loader import LanguagePackLoader\n"
        "loader = LanguagePackLoader()\n"
        "print(json.dumps({\n"
        "    'languages': [code for code, _ in loader.list_available_languages('python')],\n"
        "    'versions': loader.list_available_versions('python'),\n"
        "    'roots': sorted({str(p) for p in loader._discover_packs().values()})[:1],\n"
        "}))",
    )
    discovered = json.loads(payload)
    assert LIVE_LANGUAGE in discovered["languages"]
    assert len(discovered["languages"]) > 10, "only a handful of packs shipped in the wheel"
    assert discovered["versions"], "no pack versions visible outside the workspace"
    # The packs must come from the install, not from a stray repo checkout.
    (sample_root,) = discovered["roots"]
    assert "site-packages" in sample_root, f"packs resolved outside the install: {sample_root}"


def test_the_version_enum_is_derived_in_a_clean_install(
    clean_install: tuple[Path, Path],
) -> None:
    """The derived enum (CORE-1806) must survive leaving the workspace."""
    python, workdir = clean_install
    payload = _run_in_venv(
        python,
        workdir,
        "import json\n"
        "from legesher_mcp.schemas import SUPPORTED_PYTHON_VERSIONS, DEFAULT_PYTHON_VERSION\n"
        "print(json.dumps({'supported': list(SUPPORTED_PYTHON_VERSIONS),\n"
        "                  'default': DEFAULT_PYTHON_VERSION}))",
    )
    versions = json.loads(payload)
    assert versions["default"] in versions["supported"]
    assert len(versions["supported"]) > 1


# -- a real stdio session --------------------------------------------------


async def test_a_host_can_initialize_list_and_translate(
    clean_install: tuple[Path, Path],
) -> None:
    """The whole host handshake, from an unrelated directory with no env."""
    python, workdir = clean_install
    async with stdio_client(_server_params(python, workdir)) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.serverInfo.name == "legesher"
            assert init.serverInfo.version

            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "translate_to_native",
                "translate_to_source",
                "explain_in_language",
                "lookup_keyword_mapping",
                "map_existing_codebase",
            }

            result = await session.call_tool(
                "translate_to_native",
                {"source": "def greet():\n    return True\n", "target_lang": LIVE_LANGUAGE},
            )
            assert not result.isError, result.content
            assert result.structuredContent is not None
            translated = result.structuredContent["translated_source"]
            assert translated != "def greet():\n    return True\n", "nothing was translated"
            assert "definir" in translated


async def test_the_catalog_resource_works_in_a_clean_install(
    clean_install: tuple[Path, Path],
) -> None:
    """Pack availability is reported truthfully outside the workspace."""
    from pydantic import AnyUrl

    python, workdir = clean_install
    async with stdio_client(_server_params(python, workdir)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.read_resource(AnyUrl("legesher://languages"))
            catalog = json.loads(str(result.contents[0].text))
            available = [entry for entry in catalog if entry["pack_available"]]
            assert available, "the clean install reports no packs available"
            assert any(entry["code"] == LIVE_LANGUAGE for entry in available)


async def test_a_missing_pack_is_a_sanitized_error_not_a_crash(
    clean_install: tuple[Path, Path],
) -> None:
    """The failure mode a host is most likely to hit, from a clean install.

    Sanitization matters more here than in-workspace: the paths that could
    leak are the user's site-packages, and the server must stay up.
    """
    python, workdir = clean_install
    async with stdio_client(_server_params(python, workdir)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "translate_to_native", {"source": "x = 1\n", "target_lang": "zz"}
            )
            assert result.isError
            message = "\n".join(
                content.text for content in result.content if hasattr(content, "text")
            )
            assert "unsupported_language" in message
            assert "site-packages" not in message
            assert "Traceback" not in message
            assert str(workdir) not in message

            # The session survived the error and still serves requests.
            ok = await session.call_tool(
                "lookup_keyword_mapping", {"language": LIVE_LANGUAGE, "terms": ["def"]}
            )
            assert not ok.isError


async def test_the_console_script_is_installed(clean_install: tuple[Path, Path]) -> None:
    """Hosts run `legesher-mcp`, not `python -m legesher_mcp`."""
    python, workdir = clean_install
    script = python.parent / "legesher-mcp"
    assert script.is_file(), "the legesher-mcp console script was not installed"

    params = StdioServerParameters(
        command=str(script),
        args=[],
        env=_minimal_env(python.parent.parent),
        cwd=str(workdir),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.serverInfo.name == "legesher"


async def test_a_clean_install_is_quiet_on_stderr(
    clean_install: tuple[Path, Path], tmp_path: Path
) -> None:
    """The quiet default has to hold for the artifact, not just the source tree."""
    python, workdir = clean_install
    errfile = tmp_path / "clean-stderr.log"
    with errfile.open("w", encoding="utf-8") as errlog:
        async with stdio_client(_server_params(python, workdir), errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                await session.call_tool(
                    "lookup_keyword_mapping", {"language": LIVE_LANGUAGE, "terms": ["def"]}
                )
    stderr_text = errfile.read_text(encoding="utf-8")
    noisy = [line for line in stderr_text.splitlines() if "INFO" in line or "DEBUG" in line]
    assert noisy == [], f"unexpected log noise from a clean install: {stderr_text!r}"


def test_the_wheel_does_not_ship_tests(clean_install: tuple[Path, Path]) -> None:
    """A published wheel carries the package, not this suite."""
    python, workdir = clean_install
    listing = _run_in_venv(
        python,
        workdir,
        "import legesher_mcp, pathlib, json\n"
        "root = pathlib.Path(legesher_mcp.__file__).parent\n"
        "print(json.dumps(sorted(p.name for p in root.iterdir())))",
    )
    names = json.loads(listing)
    assert "tests" not in names
    assert {"server.py", "engine.py", "schemas.py", "versions.py"} <= set(names)
