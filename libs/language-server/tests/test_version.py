"""One version, read from the distribution (CORE-2203).

The release train (semantic-release, tag ``language-server-v{version}``)
rewrites exactly one place: ``project.version`` in ``pyproject.toml``. Every
surface that reports a version has to follow it, or the published wheel says
one thing and the running server another. Before this module three literals
disagreed: ``--version`` and the startup log said 0.1.0, ``__version__`` said
0.1.2, and ``pyproject.toml`` said 0.1.3.

Each test compares against ``importlib.metadata``, not against a literal, so a
release bump never has to edit this file.
"""

import ast
import re
import subprocess
import sys
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path

import pytest
from lsprotocol.types import ClientCapabilities, InitializeParams

import legesher_language_server
from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy
from legesher_language_server.server import LegesherLanguageServer

DISTRIBUTION = "legesher-language-server"


@pytest.fixture
def config() -> LanguageServerConfig:
    return LanguageServerConfig(source_language="en", target_language="es", python_version="3.10")


def test_dunder_version_is_the_distribution_version() -> None:
    assert legesher_language_server.__version__ == version(DISTRIBUTION)


async def test_initialize_reports_the_distribution_version(config: LanguageServerConfig) -> None:
    server = LegesherLanguageServer(config)
    result = await server.on_initialize(
        InitializeParams(
            process_id=None, root_uri="file:///test", capabilities=ClientCapabilities()
        )
    )
    assert result.server_info is not None
    assert result.server_info["version"] == version(DISTRIBUTION)


def test_the_pygls_server_carries_the_distribution_version(config: LanguageServerConfig) -> None:
    assert LegesherLanguageServer(config).version == version(DISTRIBUTION)


def test_version_flag_prints_the_distribution_version() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "legesher_language_server", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == f"legesher-lsp {version(DISTRIBUTION)}"


async def test_backend_initialize_sends_the_distribution_version(
    config: LanguageServerConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clientInfo the proxy gives pyright-langserver is a version surface too."""
    proxy = EnhancedIntelligenceProxy(config)
    sent: dict[str, dict] = {}

    async def fake_send_request(method: str, params: dict, timeout: float = 5.0) -> dict:
        sent[method] = params
        return {"result": {"capabilities": {}}}

    async def fake_send_notification(method: str, params: dict) -> None:
        return None

    monkeypatch.setattr(proxy, "_send_request", fake_send_request)
    monkeypatch.setattr(proxy, "_send_notification", fake_send_notification)

    assert await proxy._initialize_server()
    assert sent["initialize"]["clientInfo"] == {
        "name": "legesher",
        "version": version(DISTRIBUTION),
    }


#: A three-part version anywhere in a string, such as ``0.1.0`` in
#: ``"legesher-lsp 0.1.0"``. The digits and dots on either side are excluded so
#: that the uninstalled-tree fallback ``"0.0.0.dev0"`` and an address such as
#: ``"127.0.0.1"`` do not match.
VERSION_IN_STRING = re.compile(r"(?<![\d.])v?\d+\.\d+\.\d+(?![\d.])")


def _string_constants(source: str) -> Iterator[tuple[int, str]]:
    """Every string constant in the code, f-string parts included, docstrings excluded."""
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            yield node.lineno, node.value


def test_no_version_literal_in_the_package_source() -> None:
    """A hard-coded version is what drifted three ways; keep one from coming back.

    Checks string constants, so ``"0.1.0"`` and ``"legesher-lsp 0.1.0"`` (the
    form ``--version`` used) are both caught. Comments and docstrings are not
    checked: they can mention a version without reporting one.
    """
    init = legesher_language_server.__file__
    assert init is not None
    package = Path(init).parent
    offenders = [
        f"{path.relative_to(package)}:{number}: {value!r}"
        for path in sorted(package.rglob("*.py"))
        for number, value in _string_constants(path.read_text(encoding="utf-8"))
        if VERSION_IN_STRING.search(value)
    ]
    assert offenders == [], "hard-coded version literals:\n" + "\n".join(offenders)
