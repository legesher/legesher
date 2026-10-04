"""The real editor install path: locally built wheels, fresh venv (CORE-2203).

Every other test in this suite runs inside the monorepo workspace, where the
packs and every dependency are already importable. An editor does none of
that. It runs ``legesher-lsp`` from whatever directory the user opened, with
whatever environment the editor passes down, against whatever the package
index served.

This module builds the wheels, installs them into an empty virtualenv, and
drives a stdio LSP session through the installed ``legesher-lsp`` console
script from an unrelated directory with a stripped environment. That is the
path the VS Code extension's ``legesher.serverCommand`` default takes, and the
one a Neovim, Helix, Zed or JetBrains user takes after installing
``legesher-language-server`` from the index (CORE-2294). It is the publish gate
for that package, the same role ``libs/mcp/tests/test_clean_environment.py``
plays for ``legesher-mcp``.

Marked ``scheduled``: building wheels and creating a venv costs far too much
for a per-commit run. Run it with ``make test-language-server-scheduled`` (or
``uv run pytest -m scheduled``) before publishing.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.scheduled,
    # The venv layout (`bin/`) and the PATH separator below are POSIX. CI and
    # the release gate run on Linux; Windows would need both rewritten.
    pytest.mark.skipif(sys.platform == "win32", reason="POSIX venv layout"),
]

#: The runtime packages an editor user gets from the index. The language packs
#: are not installed separately: legesher-i18n bundles them, which the live
#: session below depends on.
WHEEL_PACKAGES = ("legesher-i18n", "legesher-language-server")

#: One Latin pack and two that are not: Ethiopic, and Arabic, which is
#: right-to-left. ``def`` is the first word of each document.
LIVE_DOCUMENTS = {
    "es": ("definir", "definir saludar(nombre):\n    devolver nombre\n"),
    "am": ("ግለጽ", "ግለጽ ሰላም(ስም):\n    መልስ ስም\n"),
    "ar": ("تعريف", "تعريف تحية(اسم):\n    إرجاع اسم\n"),
}

RESPONSE_TIMEOUT = 60.0


def _monorepo_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "libs" / "language-server").is_dir() and (parent / "uv.lock").is_file():
            return parent
    return None


def _minimal_env(venv: Path) -> dict[str, str]:
    """What an editor that passes a bare environment leaves behind.

    No PYTHONPATH, no VIRTUAL_ENV, no workspace markers: if the server needs
    any of them to find its packs, this is where that shows up.
    """
    return {"PATH": f"{venv / 'bin'}:/usr/bin:/bin"}


def _run(command: list[str], cwd: Path | None = None) -> None:
    """Run a build step, and on failure show uv's own output, not only an exit status."""
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    assert completed.returncode == 0, (
        f"{' '.join(command)} exited {completed.returncode}:\n{completed.stdout}{completed.stderr}"
    )


@pytest.fixture(scope="module")
def clean_install(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, str]:
    """Build the wheels, install them into a fresh venv.

    Returns the installed ``legesher-lsp`` script, an empty working directory
    with no relationship to the repo, and the version in the server wheel's
    file name.
    """
    root = _monorepo_root()
    if root is None:  # pragma: no cover (only when run from an installed wheel)
        pytest.skip("needs the monorepo checkout to build wheels")
    if shutil.which("uv") is None:  # pragma: no cover (uv is the repo's toolchain)
        pytest.skip("needs `uv` on PATH to build wheels and create the venv")

    base = tmp_path_factory.mktemp("clean-env")
    wheelhouse = base / "wheelhouse"
    venv = base / "venv"
    workdir = base / "elsewhere"
    workdir.mkdir()

    for package in WHEEL_PACKAGES:
        _run(
            ["uv", "build", "--package", package, "--wheel", "--out-dir", str(wheelhouse)],
            cwd=root,
        )

    wheels = sorted(wheelhouse.glob("*.whl"))
    assert len(wheels) == len(WHEEL_PACKAGES), f"expected one wheel per package, got {wheels}"
    (server_wheel,) = [w for w in wheels if w.name.startswith("legesher_language_server-")]
    wheel_version = server_wheel.name.split("-")[1]

    _run(["uv", "venv", str(venv)])
    _run(["uv", "pip", "install", "--python", str(venv / "bin" / "python"), *map(str, wheels)])
    return venv / "bin" / "legesher-lsp", workdir, wheel_version


class _LspSession:
    """A minimal LSP client over the server's stdio: framing, ids, timeouts.

    Written out rather than borrowed from pygls so the check does not share
    code with the server it checks.
    """

    def __init__(self, command: list[str], cwd: Path, env: dict[str, str]) -> None:
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        self._messages: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self._stderr: list[bytes] = []
        self._next_id = 0
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    @property
    def stderr(self) -> str:
        return b"".join(self._stderr).decode("utf-8", errors="replace")

    def _read_stdout(self) -> None:
        stream = self.process.stdout
        assert stream is not None
        # The sentinel goes out however this ends, a malformed frame included,
        # so a waiting request fails at once with the server's stderr rather
        # than sitting out the whole timeout.
        try:
            while True:
                headers: dict[str, str] = {}
                while True:
                    line = stream.readline()
                    if not line:
                        return
                    text = line.decode("ascii").strip()
                    if not text:
                        break
                    name, _, value = text.partition(":")
                    headers[name.strip().lower()] = value.strip()
                body = stream.read(int(headers["content-length"]))
                self._messages.put(json.loads(body))
        finally:
            self._messages.put(None)

    def _read_stderr(self) -> None:
        stream = self.process.stderr
        assert stream is not None
        for chunk in iter(lambda: os.read(stream.fileno(), 4096), b""):
            self._stderr.append(chunk)

    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        stdin = self.process.stdin
        assert stdin is not None
        stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        stdin.flush()

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self._next_id += 1
        request_id = self._next_id
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + RESPONSE_TIMEOUT
        while (remaining := deadline - time.monotonic()) > 0:
            try:
                message = self._messages.get(timeout=remaining)
            except queue.Empty:
                break
            if message is None:
                raise AssertionError(f"server exited before answering {method}:\n{self.stderr}")
            if "method" in message and "id" in message:
                # A request from the server (registerCapability and the like).
                # Answer it so nothing on the server side waits on us.
                self._send({"jsonrpc": "2.0", "id": message["id"], "result": None})
            elif message.get("id") == request_id:
                assert "error" not in message, f"{method} failed: {message['error']}"
                return message.get("result")
            # Anything else is a notification (logMessage, status): not what
            # this check is about.
        raise AssertionError(f"no answer to {method} within {RESPONSE_TIMEOUT}s:\n{self.stderr}")

    def close(self) -> int:
        """Shut down the way an editor does, and return the exit code."""
        if self.process.poll() is None:
            try:
                self.request("shutdown")
                self.notify("exit")
                return self.process.wait(timeout=RESPONSE_TIMEOUT)
            finally:
                if self.process.poll() is None:
                    self.process.kill()
                    self.process.wait()
        return self.process.returncode


@contextmanager
def _session(clean_install: tuple[Path, Path, str]) -> Generator[_LspSession]:
    script, workdir, _ = clean_install
    session = _LspSession([str(script)], workdir, _minimal_env(script.parent.parent))
    try:
        yield session
    finally:
        if session.process.poll() is None:
            session.process.kill()
            session.process.wait()


def _initialize(session: _LspSession, language: str) -> dict[str, Any]:
    """The handshake the VS Code client sends, with its role slots (CORE-1760)."""
    result = session.request(
        "initialize",
        {
            "processId": None,
            "rootUri": None,
            "capabilities": {},
            "initializationOptions": {
                "sourceLanguage": "en",
                "fileLanguage": language,
                "workingLanguage": language,
            },
        },
    )
    session.notify("initialized", {})
    return result


# -- the install itself ----------------------------------------------------


def test_the_console_script_reports_the_wheel_version(
    clean_install: tuple[Path, Path, str],
) -> None:
    """`legesher-lsp` is on the venv's PATH and knows which release it is."""
    script, workdir, wheel_version = clean_install
    assert script.is_file(), "the legesher-lsp console script was not installed"
    completed = subprocess.run(
        [str(script), "--version"],
        cwd=workdir,
        env=_minimal_env(script.parent.parent),
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == f"legesher-lsp {wheel_version}"


def test_the_wheel_does_not_ship_tests(clean_install: tuple[Path, Path, str]) -> None:
    """A published wheel carries the package, not this suite."""
    script, workdir, _ = clean_install
    listing = subprocess.run(
        [
            str(script.parent / "python"),
            "-c",
            "import json, pathlib, legesher_language_server as p;"
            "print(json.dumps(sorted(x.name for x in pathlib.Path(p.__file__).parent.iterdir())))",
        ],
        cwd=workdir,
        env=_minimal_env(script.parent.parent),
        capture_output=True,
        text=True,
        check=True,
    )
    names = set(json.loads(listing.stdout))
    assert "tests" not in names
    assert {"__main__.py", "server.py", "providers"} <= names


# -- a real stdio session --------------------------------------------------


@pytest.mark.parametrize("language", sorted(LIVE_DOCUMENTS))
def test_an_editor_gets_highlighting_hover_and_completion(
    clean_install: tuple[Path, Path, str], language: str
) -> None:
    """The whole editor path, from an unrelated directory with no env.

    Non-empty semantic tokens are the proof that the packs were found inside
    the install: with no pack, the server answers every request successfully
    and with nothing in it, which is the failure CORE-1976 describes.
    """
    keyword, text = LIVE_DOCUMENTS[language]
    uri = f"file:///elsewhere/lesson_{language}.py"
    _, _, wheel_version = clean_install
    with _session(clean_install) as session:
        init = _initialize(session, language)
        assert init["serverInfo"] == {"name": "legesher-lsp", "version": wheel_version}
        capabilities = init["capabilities"]
        assert capabilities["hoverProvider"] is True
        assert capabilities["completionProvider"] is not None
        assert capabilities["semanticTokensProvider"]["full"] is True

        session.notify(
            "textDocument/didOpen",
            {"textDocument": {"uri": uri, "languageId": "python", "version": 1, "text": text}},
        )

        tokens = session.request("textDocument/semanticTokens/full", {"textDocument": {"uri": uri}})
        assert tokens is not None and tokens["data"], f"no semantic tokens for {language}"
        # The first token is the keyword that opens the document, at 0:0.
        delta_line, delta_start, length = tokens["data"][:3]
        assert (delta_line, delta_start) == (0, 0)
        assert length == len(keyword.encode("utf-16-le")) // 2

        hover = session.request(
            "textDocument/hover",
            {"textDocument": {"uri": uri}, "position": {"line": 0, "character": 1}},
        )
        assert hover is not None, f"no hover on {keyword!r}"
        assert "def" in json.dumps(hover["contents"], ensure_ascii=False)

        completion = session.request(
            "textDocument/completion",
            {"textDocument": {"uri": uri}, "position": {"line": 1, "character": 4}},
        )
        labels = {item["label"] for item in completion["items"]}
        assert keyword in labels

        assert session.close() == 0
        assert "Traceback" not in session.stderr, session.stderr
