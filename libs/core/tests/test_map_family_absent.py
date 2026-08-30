"""The map family stays out of the free engine — the import gate.

The map — register map, mapping log, replay, `translate_code_with_map`,
the `legesher map` CLI — is the commercial capability [CORE-2011] and
lives outside this repository [CORE-2027]. These tests keep the boundary
from regressing: nothing here may import the moved surfaces, and the free
packages must not grow references to them.
"""

import pathlib
import re
import subprocess
import sys

import pytest

import legesher_core

MOVED_MODULES = [
    "legesher_core.register_map",
    "legesher_core.register_map.model",
    "legesher_core.translation_memory.replay",
    "legesher.cli.map_cmd",
]


@pytest.mark.parametrize("module", MOVED_MODULES)
def test_moved_modules_are_absent(module):
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, f"{module} is importable — the boundary regressed"
    assert "ModuleNotFoundError" in result.stderr


def test_translator_has_no_map_method():
    from legesher_core.transformer import TokenTranslator

    assert not hasattr(TokenTranslator, "translate_code_with_map")


def test_no_source_references_to_moved_surfaces():
    """Grep-level gate: free package sources never name the moved modules."""
    core_root = pathlib.Path(legesher_core.__file__).parent
    roots = [core_root, core_root.parent.parent / "legesher" / "legesher"]
    offenders = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for needle in (
                r"\bregister_map\b",
                r"translation_memory\.replay",
                r"\bmap_cmd\b",
            ):
                if re.search(needle, text):
                    offenders.append(f"{path}: {needle}")
    assert not offenders, "\n".join(offenders)
