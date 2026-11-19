"""Regenerate the pinned versions inside the one-line installers.

``install/requirements.in`` names the two tools the installers put on a machine,
each at an exact version. This compiles it with uv for every platform, writes
the result to ``install/constraints.txt``, and copies that list into
``install/install.sh`` and ``install/install.ps1`` between their
``BEGIN CONSTRAINTS`` and ``END CONSTRAINTS`` lines. The installers carry the
list inline because they are run from a single downloaded file.

``scripts/tests/test_installers.py`` fails when the three copies differ, or when
the installers' own pins disagree with ``requirements.in``.

Run with:  uv run python scripts/update_installer_constraints.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INSTALL = REPO / "install"
REQUIREMENTS = INSTALL / "requirements.in"
CONSTRAINTS = INSTALL / "constraints.txt"
SCRIPTS = (INSTALL / "install.sh", INSTALL / "install.ps1")
SERVER_PYTHON = "3.12"

BLOCK = re.compile(r"(# BEGIN CONSTRAINTS\n)(.*?)(# END CONSTRAINTS)", re.S)


def compile_constraints() -> str:
    """Every package the tools need, pinned, for every platform, with no build."""
    result = subprocess.run(
        [
            "uv",
            "pip",
            "compile",
            "--quiet",
            "--universal",
            "--no-build",
            "--no-config",
            "--no-header",
            "--no-annotate",
            "--python-version",
            SERVER_PYTHON,
            str(REQUIREMENTS),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def replace_block(text: str, constraints: str) -> str:
    """``text`` with its constraints block set to ``constraints``."""
    if len(BLOCK.findall(text)) != 1:
        raise SystemExit("expected exactly one BEGIN/END CONSTRAINTS block")
    return BLOCK.sub(lambda match: match.group(1) + constraints + match.group(3), text)


def main() -> int:
    constraints = compile_constraints()
    CONSTRAINTS.write_text(constraints, encoding="utf-8", newline="\n")
    for script in SCRIPTS:
        script.write_text(
            replace_block(script.read_text(encoding="utf-8"), constraints),
            encoding="utf-8",
            newline="\n",
        )
    print(
        f"{len(constraints.splitlines())} pins written to {CONSTRAINTS.relative_to(REPO)} and both installers"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
