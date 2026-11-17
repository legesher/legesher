"""Build ``libs/mcp/Dockerfile`` and drive a session against the image.

A directory that builds the server from source starts the container and runs
the protocol's introspection exchange (``tools/list``, ``resources/list``,
``prompts/list``). This module does the same on a laptop, twice: over stdio,
which is the image's default, and over HTTP through mcp-proxy, which is the
command a listing runs.

The image installs the published package, not this checkout, so the two
sessions are compared with each other and with the version the Dockerfile
names. Comparing them with the server in the working tree would fail every
time the tree gains a tool that is not released yet.

Marked ``docker`` and deselected by default: it needs a Docker daemon and
pulls images, npm and PyPI packages. Run it with ``make test-mcp-docker``.
Asked for without Docker, it fails; a skip would read as a pass.
"""

from __future__ import annotations

import shutil
import subprocess
import time
import unicodedata
import urllib.request
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from tests.conftest import call_ok
from tests.container_image import (
    DOCKERFILE,
    LISTING_COMMAND,
    PROXY_PORT,
    build_arguments,
    image_references,
)
from tests.corpus import corpus_for

pytestmark = [pytest.mark.anyio, pytest.mark.docker]

#: Packs whose keywords are written with combining marks (vocalised Arabic,
#: Devanagari), so the text that crosses the container boundary is not ASCII.
#: Two are enough here; the every-pack sweep is the scheduled tier.
LANGUAGES = ("ar", "hi")

#: The grammar the image's interpreter compiles: its ``X.Y``.
IMAGE_PYTHON = ".".join(str(build_arguments()["PYTHON_VERSION"]).split(".")[:2])

CORPUS_FILE = "control_flow.py"

#: How long mcp-proxy gets to answer its health check after the container starts.
STARTUP_SECONDS = 60


def _docker(*args: str, stdin: bytes | None = None, timeout: float = 600) -> str:
    completed = subprocess.run(
        ["docker", *args], input=stdin, capture_output=True, timeout=timeout, check=False
    )
    assert completed.returncode == 0, (
        f"`docker {' '.join(args)}` exited {completed.returncode}:\n"
        f"{completed.stderr.decode(errors='replace')[-2000:]}"
    )
    return completed.stdout.decode().strip()


def _remove_container(name: str) -> None:
    """Remove a container and wait for it: an image cannot go while one holds it."""
    subprocess.run(["docker", "rm", "--force", name], capture_output=True, check=False)


def _logs(name: str) -> str:
    completed = subprocess.run(
        ["docker", "logs", name], capture_output=True, text=True, check=False
    )
    return (completed.stdout + completed.stderr)[-2000:]


@pytest.fixture(scope="module")
def image() -> Iterator[str]:
    """Build the image the way the file's header says: with no build context."""
    assert shutil.which("docker") is not None, (
        "the docker tier needs the `docker` command on PATH; it does not skip"
    )
    tag = f"legesher-mcp-test:{uuid.uuid4().hex[:12]}"
    _docker("build", "--tag", tag, "-", stdin=DOCKERFILE.read_bytes())
    try:
        yield tag
    finally:
        subprocess.run(["docker", "image", "rm", "--force", tag], capture_output=True, check=False)


@pytest.fixture(scope="module")
def proxy_url(image: str) -> Iterator[str]:
    """Start the listing's command, published on loopback, and wait for the proxy."""
    name = f"legesher-mcp-test-proxy-{uuid.uuid4().hex[:12]}"
    try:
        _docker(
            "run", "--detach", "--name", name,
            "--publish", f"127.0.0.1::{PROXY_PORT}", image, *LISTING_COMMAND,
        )  # fmt: skip
        address = _docker("port", name, f"{PROXY_PORT}/tcp").splitlines()[0]
        base = f"http://127.0.0.1:{address.rsplit(':', 1)[1]}"
        deadline = time.monotonic() + STARTUP_SECONDS
        while True:
            try:
                with urllib.request.urlopen(f"{base}/ping", timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            running = _docker("inspect", "--format", "{{.State.Running}}", name)
            assert running == "true", (
                f"the container stopped before answering /ping:\n{_logs(name)}"
            )
            assert time.monotonic() < deadline, (
                f"mcp-proxy did not answer /ping within {STARTUP_SECONDS} seconds:\n{_logs(name)}"
            )
            time.sleep(0.5)
        yield base
    finally:
        _remove_container(name)


@pytest.fixture
async def stdio_session(image: str) -> AsyncIterator[ClientSession]:
    """The image's default command, the way a desktop client runs the container."""
    name = f"legesher-mcp-test-stdio-{uuid.uuid4().hex[:12]}"
    params = StdioServerParameters(
        command="docker", args=["run", "--interactive", "--name", name, image]
    )
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                yield session
    finally:
        _remove_container(name)


@pytest.fixture
async def http_session(proxy_url: str) -> AsyncIterator[ClientSession]:
    """The listing's command: the same server through mcp-proxy, over HTTP."""
    async with streamable_http_client(f"{proxy_url}/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            yield session


async def _introspect(session: ClientSession) -> dict[str, object]:
    """Initialize, then the exchange a directory runs, as one comparable value."""
    init = await session.initialize()
    return {
        "name": init.serverInfo.name,
        "version": init.serverInfo.version,
        "tools": sorted(tool.name for tool in (await session.list_tools()).tools),
        "resources": sorted(str(r.uri) for r in (await session.list_resources()).resources),
        "templates": sorted(
            t.uriTemplate for t in (await session.list_resource_templates()).resourceTemplates
        ),
        "prompts": sorted(prompt.name for prompt in (await session.list_prompts()).prompts),
    }


async def _assert_round_trip(session: ClientSession, language: str) -> None:
    (entry,) = (e for e in corpus_for(IMAGE_PYTHON) if e.name == CORPUS_FILE)
    native = (
        await call_ok(
            session,
            "translate_to_native",
            {"source": entry.source, "target_lang": language, "python_version": IMAGE_PYTHON},
        )
    )["translated_source"]
    assert any(unicodedata.category(char).startswith("M") for char in native), (
        f"[{language}] the translation carries no combining mark, so this proves nothing "
        "about text crossing the container boundary"
    )
    assert unicodedata.is_normalized("NFC", native), f"[{language}] the translation is not NFC"
    back = (
        await call_ok(
            session,
            "translate_to_source",
            {"source": native, "source_lang": language, "python_version": IMAGE_PYTHON},
        )
    )["translated_source"]
    assert back.encode() == entry.source.encode(), (
        f"[{language}] {entry.name} did not come back byte for byte through the container"
    )
    compile(back, entry.name, "exec")


async def test_stdio_and_http_serve_the_same_non_empty_surface(
    stdio_session: ClientSession, http_session: ClientSession
) -> None:
    over_stdio = await _introspect(stdio_session)
    over_http = await _introspect(http_session)
    assert over_stdio == over_http, "the proxy serves a different surface from the server behind it"
    assert over_stdio["version"] == build_arguments()["LEGESHER_MCP_VERSION"], (
        f"the image serves legesher-mcp {over_stdio['version']}, not the version its "
        "Dockerfile names"
    )
    empty = [kind for kind, served in over_stdio.items() if not served]
    assert not empty, f"the image served nothing for {empty}: {over_stdio}"


@pytest.mark.parametrize("language", LANGUAGES)
async def test_a_translation_round_trips_over_stdio(
    stdio_session: ClientSession, language: str
) -> None:
    await stdio_session.initialize()
    await _assert_round_trip(stdio_session, language)


@pytest.mark.parametrize("language", LANGUAGES)
async def test_a_translation_round_trips_over_http(
    http_session: ClientSession, language: str
) -> None:
    await http_session.initialize()
    await _assert_round_trip(http_session, language)


def test_the_container_runs_unprivileged(image: str) -> None:
    uid = _docker("run", "--rm", image, "id", "-u")
    assert uid != "0", "the image runs as root"


def _tag(repository: str) -> str:
    """The version tag the Dockerfile gives an image, without its variant."""
    (image,) = (
        ref for ref in image_references() if ref.split("@")[0].rsplit(":", 1)[0] == repository
    )
    return image.split("@")[0].rsplit(":", 1)[1].split("-")[0]


def test_the_tools_are_the_versions_the_tags_name(image: str) -> None:
    """A digest is what Docker pulls; the tag beside it is only a label.

    So the label is checked against what the pulled image actually holds.
    """
    script = (
        "node --version; uv --version; mcp-proxy --version; /opt/legesher-mcp/bin/python --version"
    )
    node, uv, proxy, python = _docker("run", "--rm", image, "sh", "-c", script).splitlines()
    arguments = build_arguments()
    assert node == f"v{_tag('node')}", f"the node image holds {node}, tagged {_tag('node')}"
    assert uv.split()[1] == _tag("ghcr.io/astral-sh/uv"), (
        f"the uv image holds {uv}, tagged {_tag('ghcr.io/astral-sh/uv')}"
    )
    assert proxy == arguments["MCP_PROXY_VERSION"], f"mcp-proxy is {proxy}"
    assert python == f"Python {arguments['PYTHON_VERSION']}", f"the server runs on {python}"
