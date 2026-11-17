"""`legesher run` runs a script whose numbers are typed in the language's digits.

Every language whose registry entry names a native digit block. The script's
literals are written in those digits; its string keeps them as text. Each case
runs the real CLI in a subprocess, as ``test_cli_run.py`` does.

The script calls ``print`` by its English name, which a native file may do and
the run path leaves alone. That keeps the case about digits alone: on CPython
3.10 and 3.11 the token backend cannot read a pack rendering with vowel signs
(the interpreter gap pinned in ``libs/core/tests/interpreter_gaps.py``), so a
translated ``print`` would fail there for a reason unrelated to digits.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from legesher_i18n.language_registry import (
    get_active_language_codes,
    get_native_digits,
)

NATIVE = [code for code in get_active_language_codes() if get_native_digits(code)]
CLI = "from legesher.cli.main import cli; cli()"


@pytest.mark.parametrize("lang", NATIVE)
def test_native_digit_literals_run(tmp_path: Path, lang: str) -> None:
    digits = get_native_digits(lang)
    assert digits is not None

    def n(text: str) -> str:
        return text.translate(str.maketrans("0123456789", digits))

    script = tmp_path / "script.py"
    script.write_text(
        f'total = {n("120")} + {n("35")}\nprint(total * 2, "{n("12")}")\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-c", CLI, "run", str(script), "--lang", lang],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=tmp_path,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"310 {n('12')}\n"
