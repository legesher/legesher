"""`legesher run` reports a script's error the way `python script.py` does.

The traceback starts at the script's own first frame: the console script,
click and the ``run`` command above it are this tool's machinery, which
``python script.py`` never shows (CORE-2552). Each case runs the real CLI in a
subprocess, because the hooks it installs are process-wide.

Spanish and Arabic, one left-to-right and one right-to-left pack: the
trimming does not depend on the language, the scripts do.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from legesher_core import TokenTranslator

#: A frame header in any language: two spaces, a word, a quoted path.
FRAME = re.compile(r'^  \S+ "(?P<file>[^"]+)"')

RUNTIME_ERROR = "def dividir(a, b):\n    return a / b\n\ndividir(1, 0)\n"
SYNTAX_ERROR = "return (1, 2\n"


def native(english: str, lang: str) -> str:
    """The English source written in ``lang``'s keywords."""
    return TokenTranslator.from_language_pack(lang).translate_code(english)


#: The console script's body. Not ``-m legesher.cli.main``: runpy warns on
#: stderr about the module already being imported, ahead of the traceback.
CLI = "from legesher.cli.main import cli; cli()"


def run_cli(tmp_path: Path, script: Path, lang: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-c", CLI, "run", str(script), "--lang", lang],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=tmp_path,
        env=env,
        check=False,
    )


def frame_files(stderr: str) -> list[str]:
    return [m.group("file") for line in stderr.splitlines() if (m := FRAME.match(line))]


@pytest.mark.parametrize("lang", ["es", "ar"])
def test_runtime_error_starts_at_the_script(tmp_path: Path, lang: str):
    script = tmp_path / "programa.py"
    script.write_text(native(RUNTIME_ERROR, lang), encoding="utf-8")
    result = run_cli(tmp_path, script, lang)
    assert result.returncode == 1
    # Two frames, both the script's: the module-level call and dividir.
    assert frame_files(result.stderr) == [str(script), str(script)]
    assert os.path.join("click", "core.py") not in result.stderr
    assert os.path.join("cli", "run.py") not in result.stderr


@pytest.mark.parametrize("lang", ["es", "ar"])
def test_syntax_error_prints_as_cpython_does(tmp_path: Path, lang: str):
    script = tmp_path / "programa.py"
    script.write_text(native(SYNTAX_ERROR, lang), encoding="utf-8")
    result = run_cli(tmp_path, script, lang)
    assert result.returncode == 1
    # CPython prints a syntax error in the main script with no traceback
    # header: the first line is already the script's frame.
    first = result.stderr.splitlines()[0]
    assert FRAME.match(first) and FRAME.match(first).group("file") == str(script)
    assert frame_files(result.stderr) == [str(script)]


def test_an_error_before_the_script_runs_keeps_every_frame(tmp_path: Path):
    # Undecodable bytes fail in `run` itself, before any script frame exists.
    # That error is the tool's own, so its frames stay.
    script = tmp_path / "programa.py"
    script.write_bytes(b'x = "\xff"\n')
    result = run_cli(tmp_path, script, "es")
    assert result.returncode == 1
    assert os.path.join("cli", "run.py") in result.stderr
    assert "can't decode byte 0xff" in result.stderr
