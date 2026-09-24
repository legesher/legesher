"""Repo-hygiene guard against the 2026-09-22 worm signature (CORE-2214).

On 2026-09-22 a stolen contributor token force-pushed every branch of three
organisation repositories with one commit that added a hidden VS Code task set
to run when the folder opens, a settings file that switches such automatic
tasks on, a file carrying a web-font name whose bytes are not a font, and a
``.gitignore`` edit that stopped ignoring ``.env``. Those repositories are
repaired; this module fails on any tracked file that carries that shape again,
whichever path it arrives by. It reads git's index and the first bytes of
font-named files, and never executes anything it finds.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

FONT_SUFFIXES = frozenset({".woff", ".woff2", ".ttf", ".otf"})
FONT_MAGIC = frozenset({b"wOF2", b"wOFF", b"\x00\x01\x00\x00", b"true", b"OTTO"})
# ``.env`` itself, or ``.env`` widened with ``*``, optionally anchored. A
# narrower pattern such as ``.env.local`` does not count: it leaves ``.env``
# committable, which is the state the worm created.
DOTENV_IGNORE = re.compile(r"(?:\*\*/|/)?\.env\**")


def _repo_root() -> Path | None:
    """The work tree containing this file, or ``None`` outside git."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return Path(proc.stdout.strip())


_ROOT = _repo_root()
if _ROOT is None:
    pytest.skip(
        "repo-hygiene guard needs a git work tree: `git rev-parse --show-toplevel`"
        " failed from the test directory",
        allow_module_level=True,
    )
REPO: Path = _ROOT


def _tracked_files() -> tuple[str, ...]:
    """Every path in git's index, relative to the repo root, POSIX separators."""
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-z"],
        capture_output=True,
        check=True,
    ).stdout
    return tuple(p.decode("utf-8") for p in out.split(b"\0") if p)


TRACKED = _tracked_files()


def _tracked_named(directory: str, filename: str) -> list[str]:
    """Tracked paths ``<anything>/<directory>/<filename>`` at any depth."""
    return [
        path
        for path in TRACKED
        if PurePosixPath(path).name == filename
        and PurePosixPath(path).parent.name == directory
    ]


def _strip_comments(text: str) -> str:
    """Drop ``//`` and ``/* */`` comments that sit outside string literals."""
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _strip_trailing_commas(text: str) -> str:
    """Drop a comma that only whitespace separates from ``}`` or ``]``."""
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
        elif ch == ",":
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            if j < n and text[j] in "}]":
                i += 1
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _load_jsonc(path: Path) -> Any:
    """Parse a VS Code JSON-with-comments file (comments, trailing commas)."""
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(_strip_trailing_commas(_strip_comments(text)))


def _runs_on_folder_open(node: Any) -> bool:
    """True when any object in ``node`` carries ``runOn: folderOpen``.

    VS Code reads the key from ``runOptions``; the walk is recursive so a copy
    placed under a platform override (``windows``, ``linux``, ``osx``) counts
    too.
    """
    if isinstance(node, dict):
        run_on = node.get("runOn")
        if isinstance(run_on, str) and run_on.lower() == "folderopen":
            return True
        return any(_runs_on_folder_open(value) for value in node.values())
    if isinstance(node, list):
        return any(_runs_on_folder_open(value) for value in node)
    return False


def _enables_automatic_tasks(settings: Any) -> bool:
    """True when ``task.allowAutomaticTasks`` is ``true`` or ``"on"``."""
    if not isinstance(settings, dict):
        return False
    nested = settings.get("task")
    candidates = [
        settings.get("task.allowAutomaticTasks"),
        nested.get("allowAutomaticTasks") if isinstance(nested, dict) else None,
    ]
    return any(
        value is True or (isinstance(value, str) and value.lower() == "on")
        for value in candidates
    )


def _ignores_dotenv(gitignore: Path) -> bool:
    """True when one non-negated, non-comment line ignores ``.env`` itself."""
    for raw in gitignore.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "!")):
            continue
        if DOTENV_IGNORE.fullmatch(line):
            return True
    return False


def test_no_task_runs_on_folder_open() -> None:
    """(a) No tracked ``.vscode/tasks.json`` carries a folder-open task."""
    offenders: list[str] = []
    for rel in _tracked_named(".vscode", "tasks.json"):
        try:
            document = _load_jsonc(REPO / rel)
        except ValueError as exc:
            pytest.fail(f"{rel}: not parseable as JSON with comments: {exc}")
        if _runs_on_folder_open(document):
            offenders.append(rel)
    assert not offenders, (
        f"tasks that run when the folder opens (the CORE-2214 signature): {offenders}"
    )


def test_no_settings_enable_automatic_tasks() -> None:
    """(b) No tracked ``.vscode/settings.json`` switches automatic tasks on."""
    offenders: list[str] = []
    for rel in _tracked_named(".vscode", "settings.json"):
        try:
            document = _load_jsonc(REPO / rel)
        except ValueError as exc:
            pytest.fail(f"{rel}: not parseable as JSON with comments: {exc}")
        if _enables_automatic_tasks(document):
            offenders.append(rel)
    assert not offenders, (
        f"settings that allow automatic tasks (the CORE-2214 signature): {offenders}"
    )


def test_font_named_files_are_fonts() -> None:
    """(c) Every tracked ``.woff``/``.woff2``/``.ttf``/``.otf`` starts as a font."""
    offenders: list[str] = []
    for rel in TRACKED:
        if PurePosixPath(rel).suffix.lower() not in FONT_SUFFIXES:
            continue
        with (REPO / rel).open("rb") as handle:
            head = handle.read(4)
        if head not in FONT_MAGIC:
            offenders.append(f"{rel} (first bytes {head.hex() or 'none'})")
    assert not offenders, (
        "font-named files that do not start with a font signature "
        f"(the CORE-2214 signature): {offenders}"
    )


def test_gitignore_ignores_dotenv() -> None:
    """(d) The root ``.gitignore`` has a line that ignores ``.env``."""
    gitignore = REPO / ".gitignore"
    assert gitignore.is_file(), (
        f"{gitignore}: no root .gitignore, so .env is committable"
    )
    assert _ignores_dotenv(gitignore), (
        f"{gitignore}: no line ignoring .env (the CORE-2214 signature removed it)"
    )


def test_no_tracked_dotenv() -> None:
    """(e) No tracked file is named ``.env``."""
    offenders = [rel for rel in TRACKED if PurePosixPath(rel).name == ".env"]
    assert not offenders, f"tracked .env files: {offenders}"
