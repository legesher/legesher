"""Committed localized code runs with no account, no credential and no network.

CORE-2242. The open runtime that executes a repository written in a
Legesher language (the import hook and `legesher run`, with the language
packs) needs nothing from outside the machine: no network, no API key, no
sign-in and no per-user state. An unchanged repository runs the same way on
any machine.

Each scenario runs in a fresh interpreter, so nothing this test session
imported or cached earlier can hide a call:

- The environment is an allowlist. HOME, USERPROFILE and the per-user
  config, cache and data directories point into an empty directory, and no
  other variable is inherited, so no credential of any name reaches the
  runtime.
- The interpreter runs isolated (`-I -S`) and receives its package paths as
  an argument, so neither the caller's environment nor a `.pth` file runs
  code before the guard.
- The working directory is a temporary repository holding the Spanish
  sources and its own `.legesher/config.yml`, which is where the language
  comes from.
- An audit hook is installed before anything from Legesher is imported. It
  records and refuses the standard library's socket, name-lookup and
  process-launch functions, and any import of multiprocessing, and writes
  each attempt straight to stderr, so an attempt that a caller swallows, or
  one made while the interpreter exits, still fails the test. Native code
  (ctypes, or a C extension making its own calls) is outside what an audit
  hook can see.
"""

from __future__ import annotations

import ast
import functools
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

_LANGUAGE = "es"

#: What the child refuses. All but the last are CPython audit events (the
#: audit events table; each one observed under this name on Python 3.10 to
#: 3.14) raised by the standard library's socket, name-lookup and
#: process-launch functions. `gethostbyname_ex` raises
#: `socket.gethostbyname`; `create_connection` and `urlopen` raise
#: `socket.getaddrinfo`, then `socket.connect`. `os.spawn` is raised where the
#: C spawn functions exist (Windows); elsewhere `os.spawnv` forks in Python,
#: which `os.fork` covers.
#:
#: `import multiprocessing` is the child's name for the `import` event of
#: multiprocessing or any of its submodules: the `spawn` start method (the
#: default on macOS and Windows) launches through `_posixsubprocess.fork_exec`,
#: which raises no event, into an interpreter without the hook.
#:
#: Native code (ctypes, or a C extension making its own calls) raises no event
#: and is outside what an audit hook can see. `ctypes.dlopen` is not refused:
#: on Windows, click's console support loads kernel32 through ctypes.
_WATCHED_EVENTS = (
    "socket.connect",
    "socket.getaddrinfo",
    "socket.gethostbyname",
    "socket.gethostbyaddr",
    "socket.getnameinfo",
    "socket.sendto",
    "socket.sendmsg",
    "subprocess.Popen",
    "os.system",
    "os.exec",
    "os.posix_spawn",
    "os.spawn",
    "os.fork",
    "os.forkpty",
    "import multiprocessing",
)

#: The child writes this, the event and its arguments for each refusal.
_REFUSED = "offline-guard refused:"
#: The child's last line, printed only after its own check found nothing.
_DONE = "offline-guard: no attempt recorded"

_CHILD_BODY = r"""
import os
import sys

WATCHED = frozenset(sys.argv[1].split(","))
attempts = []


def refuse(event, args):
    if event == "import" and str(args[0]).split(".")[0] == "multiprocessing":
        event = "import multiprocessing"
    if event in WATCHED:
        attempts.append(event)
        # Straight to the stderr descriptor, so the attempt is reported even
        # when a caller swallows the exception or the interpreter is exiting.
        line = "%s %s %.300r\n" % (REFUSED, event, args)
        os.write(2, line.encode("utf-8", "backslashreplace"))
        raise PermissionError("offline: " + event)


sys.addaudithook(refuse)
# Nothing from Legesher is imported above this line.

import json

sys.path[:] = json.loads(sys.argv[2])
scenario = sys.argv[3]

if scenario == "import-hook":
    sys.path.insert(0, os.getcwd())
    from legesher.runtime.import_hook import (
        get_bytecode_cache_stats,
        install_import_hook,
    )

    install_import_hook()  # the language comes from .legesher/config.yml
    import modulo_espanol

    print(modulo_espanol.resultado)
    print(modulo_espanol.suma)
    print("bytecode cache hits:", get_bytecode_cache_stats()["hits"])
elif scenario == "legesher-run":
    from legesher.cli.main import cli

    cli.main(
        args=["run", "principal.py"], prog_name="legesher", standalone_mode=False
    )
elif scenario == "route":
    try:
        exec(sys.argv[4], {})
    except Exception:
        pass  # a best-effort caller: the check below must still fail the run
    else:
        print("route completed")
else:
    raise SystemExit("unknown scenario: " + scenario)

if attempts:
    raise SystemExit(
        "offline-guard: %d refused attempt(s): %s" % (len(attempts), ", ".join(attempts))
    )
print(DONE, flush=True)
"""

_CHILD = f"REFUSED = {_REFUSED!r}\nDONE = {_DONE!r}\n{_CHILD_BODY}"


@functools.cache
def _pack_mapper():
    """The pack's native-to-English maps, exactly as the import hook loads them."""
    from legesher.runtime.import_hook import LegesherMetaPathFinder

    return LegesherMetaPathFinder(language=_LANGUAGE).reverse_translator.mapper


def _native(english: str, table: str = "keyword_map") -> str:
    """The pack's own form of an English keyword or builtin (read from the
    pack, never a frozen list, so the test follows the pack)."""
    forms = [n for n, en in getattr(_pack_mapper(), table).items() if en == english]
    assert forms, f"the {_LANGUAGE} pack has no {table} form for {english!r}"
    return forms[0]


def _functions_source() -> str:
    k = {word: _native(word) for word in ("def", "return", "for", "in", "if")}
    return (
        f"{k['def']} saludar(nombre):\n"
        f'    {k["return"]} f"Hola, {{nombre}}"\n'
        "\n"
        f"{k['def']} sumar_positivos(números):\n"
        "    total = 0\n"
        f"    {k['for']} número {k['in']} números:\n"
        f"        {k['if']} número > 0:\n"
        "            total = total + número\n"
        f"    {k['return']} total\n"
    )


def _module_source() -> str:
    """A module in its stored Spanish form: pack keywords, the author's own
    accented names, a docstring and an f-string."""
    return (
        '"""Un módulo escrito en español, tal como se guarda en el repositorio."""\n'
        "\n" + _functions_source() + "\n"
        'resultado = saludar("Mundo")\n'
        "suma = sumar_positivos([3, -1, 4])\n"
    )


def _program_source() -> str:
    """A single-file program in its stored Spanish form, printing through the
    pack's own name for `print`."""
    si, imprimir = _native("if"), _native("print", "builtin_map")
    return (
        '"""Un programa escrito en español, tal como se guarda en el repositorio."""\n'
        "\n" + _functions_source() + "\n"
        f'{si} __name__ == "__main__":\n'
        f'    {imprimir}(saludar("Mundo"))\n'
        f"    {imprimir}(sumar_positivos([3, -1, 4]))\n"
    )


def _offline_env(home: Path) -> dict[str, str]:
    """The child's whole environment: per-user locations inside an empty
    directory, and nothing else the caller had."""
    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        # The Windows per-user config and cache roots, inside it as well.
        "APPDATA": str(home / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(home / "AppData" / "Local"),
    }
    if sys.platform == "win32" and "SYSTEMROOT" in os.environ:
        # The Windows interpreter needs it to load system libraries.
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return env


def _run_offline(
    cwd: Path, home: Path, scenario: str, *extra: str
) -> subprocess.CompletedProcess[str]:
    """Run one scenario of the child in a fresh, isolated interpreter."""
    package_paths = [p for p in sys.path if os.path.isabs(p)]
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            _CHILD,
            ",".join(_WATCHED_EVENTS),
            json.dumps(package_paths),
            scenario,
            *extra,
        ],
        cwd=cwd,
        env=_offline_env(home),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="backslashreplace",
        timeout=120,
        check=False,
    )


def _report(result: subprocess.CompletedProcess[str]) -> str:
    """The child's exit status and last stderr line first, then everything."""
    last = (result.stderr.strip().splitlines() or ["no stderr"])[-1]
    return (
        f"exit status {result.returncode}: {last}\n"
        f"--- stdout\n{result.stdout}\n--- stderr\n{result.stderr}"
    )


def _assert_ran_offline(
    result: subprocess.CompletedProcess[str], expected_lines: list[str]
) -> None:
    refused = [line for line in result.stderr.splitlines() if _REFUSED in line]
    assert not refused, "\n".join(refused) + "\n" + _report(result)
    assert result.returncode == 0, _report(result)
    assert result.stdout.splitlines() == [*expected_lines, _DONE], _report(result)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """A repository as it is stored: Spanish sources and its own config."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)  # the root marker LegesherConfig finds
    (repo / ".legesher").mkdir()
    (repo / ".legesher" / "config.yml").write_text(
        f"language: {_LANGUAGE}\n", encoding="utf-8"
    )
    (repo / "modulo_espanol.py").write_text(_module_source(), encoding="utf-8")
    (repo / "principal.py").write_text(_program_source(), encoding="utf-8")
    return repo


@pytest.fixture
def empty_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def test_the_import_hook_runs_a_committed_spanish_module_offline(
    repository: Path, empty_home: Path
) -> None:
    """Twice: a cold start translates and compiles the module, a warm start
    loads the hook's cached bytecode. Neither may reach outside the machine."""
    for hits in (0, 1):
        result = _run_offline(repository, empty_home, "import-hook")
        _assert_ran_offline(
            result, ["Hola, Mundo", "7", f"bytecode cache hits: {hits}"]
        )


def test_legesher_run_executes_a_committed_spanish_program_offline(
    repository: Path, empty_home: Path
) -> None:
    result = _run_offline(repository, empty_home, "legesher-run")
    _assert_ran_offline(result, ["Hola, Mundo", "7"])


@pytest.mark.parametrize(
    "source", [_module_source, _program_source], ids=["module", "program"]
)
def test_the_sources_are_stored_spanish_not_english(source) -> None:
    """Non-vacuity: neither source parses as plain Python, so the runtime
    must translate it, or the scenarios above would prove nothing."""
    with pytest.raises(SyntaxError):
        ast.parse(source())


_UDP_RECEIVER = (
    "import socket\n"
    "receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
    "receiver.bind(('127.0.0.1', 0))\n"
    "sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
)

#: For each watched event, a call that raises it and would succeed if the
#: guard let it through. Socket routes aim at listeners on the loopback.
_ROUTES = {
    "socket.connect": (
        "import socket\n"
        "server = socket.socket()\n"
        "server.bind(('127.0.0.1', 0))\n"
        "server.listen()\n"
        "socket.socket().connect(server.getsockname())\n"
    ),
    "socket.getaddrinfo": "import socket\nsocket.getaddrinfo('localhost', 80)\n",
    "socket.gethostbyname": "import socket\nsocket.gethostbyname('localhost')\n",
    "socket.gethostbyaddr": "import socket\nsocket.gethostbyaddr('127.0.0.1')\n",
    "socket.getnameinfo": "import socket\nsocket.getnameinfo(('127.0.0.1', 80), 0)\n",
    "socket.sendto": _UDP_RECEIVER + "sender.sendto(b'x', receiver.getsockname())\n",
    "socket.sendmsg": _UDP_RECEIVER
    + "sender.sendmsg([b'x'], [], 0, receiver.getsockname())\n",
    "subprocess.Popen": (
        "import subprocess, sys\n"
        "subprocess.run([sys.executable, '-c', 'pass'], check=True)\n"
    ),
    "os.system": "import os\nos.system('exit 0')\n",
    "os.exec": (
        "import os, sys\nos.execv(sys.executable, [sys.executable, '-c', 'pass'])\n"
    ),
    "os.posix_spawn": (
        "import os, sys\n"
        "pid = os.posix_spawn(sys.executable, [sys.executable, '-c', 'pass'], {})\n"
        "os.waitpid(pid, 0)\n"
    ),
    "os.spawn": (
        "import os, sys\n"
        "os.spawnv(os.P_WAIT, sys.executable, [sys.executable, '-c', 'pass'])\n"
    ),
    "os.fork": (
        "import os\npid = os.fork()\nif pid == 0:\n    os._exit(0)\nos.waitpid(pid, 0)\n"
    ),
    "os.forkpty": (
        "import os\n"
        "pid, fd = os.forkpty()\n"
        "if pid == 0:\n"
        "    os._exit(0)\n"
        "os.waitpid(pid, 0)\n"
    ),
    "import multiprocessing": (
        "import multiprocessing, os\n"
        "worker = multiprocessing.get_context('spawn').Process(target=os.getpid)\n"
        "worker.start()\n"
        "worker.join()\n"
        "assert worker.exitcode == 0, worker.exitcode\n"
    ),
}

#: Events whose call does not exist on this platform.
_NO_CALL_HERE = {
    "socket.sendmsg": not hasattr(socket.socket, "sendmsg"),
    "os.posix_spawn": not hasattr(os, "posix_spawn"),
    "os.fork": not hasattr(os, "fork"),
    "os.forkpty": not hasattr(os, "forkpty"),
}


@pytest.mark.parametrize("event", _WATCHED_EVENTS)
def test_the_guard_refuses_each_watched_event(event: str, tmp_path: Path) -> None:
    """The guard is real: each watched call is refused before it acts, and a
    caller that swallows the refusal still fails the run."""
    route = _ROUTES[event]  # every watched event needs a route here
    if _NO_CALL_HERE.get(event):
        pytest.skip(f"{event} has no call on {sys.platform}")
    # Off Windows, os.spawnv forks in Python before it executes anything.
    raised = "os.fork" if event == "os.spawn" and sys.platform != "win32" else event
    result = _run_offline(tmp_path, tmp_path, "route", route)
    assert f"{_REFUSED} {raised} " in result.stderr, _report(result)
    assert "route completed" not in result.stdout, _report(result)
    assert result.returncode != 0, _report(result)
    assert _DONE not in result.stdout, _report(result)
