"""The pack validator must survive a stdout that is not UTF-8 (CORE-1927).

Windows Python does not default ``sys.stdout`` to UTF-8. Piped — which is
what pre-commit, a subprocess and a CI step all do — it falls back to the
machine's ANSI code page, and every status marker the validator prints is
outside it. The script therefore died *reporting its own result*:

    print("\N{WHITE HEAVY CHECK MARK} All language packs valid")
    UnicodeEncodeError: 'charmap' codec can't encode character '\\u2705'

with two consequences, both worse than a crash usually is. A valid pack
exited 1 with an empty stdout, so the hook reported it invalid. And an
*invalid* pack printed no errors at all, because the same crash landed on
the line that prints them — leaving a contributor with a traceback about a
code page instead of the collision they needed to fix.

These tests force the failing encoding via ``PYTHONIOENCODING`` so they
reproduce it on any platform, and run on every platform for that reason.
They caught nothing before CORE-1921 made the Windows job report the i18n
suite at all: it had never once executed there.
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_VALIDATOR = _REPO_ROOT / "libs" / "i18n" / "scripts" / "validate_language_pack_yaml.py"

#: The code page GitHub's Windows runners fall back to. Any single-byte
#: encoding reproduces the bug; this is the one that actually bit us.
_WINDOWS_ANSI_CODEPAGE = "cp1252"


def _pack_dir(tmp_path: Path) -> Path:
    """A layout the validator recognises (needs ``language-packs`` and
    ``packs`` in the path)."""
    pack_dir = (
        tmp_path
        / "libs"
        / "i18n"
        / "language-packs"
        / "python"
        / "ur"
        / "legesher_i18n_python_ur"
        / "packs"
    )
    pack_dir.mkdir(parents=True, exist_ok=True)
    return pack_dir


def _run_under_ansi_codepage(pack_yaml: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": _WINDOWS_ANSI_CODEPAGE}
    return subprocess.run(
        ["uv", "run", "python", str(_VALIDATOR), str(pack_yaml)],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
        env=env,
    )


def _write(pack_dir: Path, keywords: str) -> Path:
    pack_yml = pack_dir / "3.13.yml"
    pack_yml.write_text(
        textwrap.dedent(f"""
            language: ur
            target: python
            version: "3.13"
            keywords:
            {keywords}
            builtins:
              print: "چھاپ"
            """).strip()
        + "\n",
        encoding="utf-8",
    )
    return pack_yml


class TestNonUtf8Stdout:
    def test_a_valid_pack_is_not_reported_as_invalid(self, tmp_path: Path) -> None:
        """The regression proper: passing validation, then dying on the
        line that says so."""
        pack_yml = _write(
            _pack_dir(tmp_path),
            '  in: "میں"\n              def: "تعریف"',
        )

        result = _run_under_ansi_codepage(pack_yml)

        assert result.returncode == 0, (
            f"a valid pack was rejected on a {_WINDOWS_ANSI_CODEPAGE} stdout.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "UnicodeEncodeError" not in result.stderr
        assert result.stdout.strip(), "exited 0 but said nothing"

    def test_an_invalid_pack_still_shows_the_contributor_the_error(
        self, tmp_path: Path
    ) -> None:
        """The half that matters more. The crash used to land on the line
        that prints the errors, so the one output a contributor actually
        needs was the one guaranteed to be missing."""
        pack_yml = _write(
            _pack_dir(tmp_path),
            '  in: "میں"\n              def: "میں"',  # same translation twice
        )

        result = _run_under_ansi_codepage(pack_yml)

        assert result.returncode != 0, "a colliding pack was accepted"
        assert "UnicodeEncodeError" not in result.stderr
        combined = (result.stdout + result.stderr).lower()
        assert "collision" in combined, (
            f"the collision was detected but never reported.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_the_native_text_survives_rather_than_being_dropped(
        self, tmp_path: Path
    ) -> None:
        """A collision message names the offending translation. On a
        narrow stdout the Urdu cannot be represented, and ``errors=
        "replace"`` is what keeps the message printable — the report has
        to arrive even when a glyph cannot."""
        pack_yml = _write(
            _pack_dir(tmp_path),
            '  in: "میں"\n              def: "میں"',
        )

        result = _run_under_ansi_codepage(pack_yml)

        # The terms are named regardless of whether the glyphs render.
        assert "keywords.def" in result.stdout and "keywords.in" in result.stdout
