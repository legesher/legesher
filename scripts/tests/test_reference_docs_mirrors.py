"""The two mirrors of the generated REFERENCE.md files carry the same bytes (CORE-1702).

The monorepo generates ``libs/i18n/language-packs/python/<code>/REFERENCE.md``.
The preview repository mirrors it at ``languages/<code>/REFERENCE.md`` and
language-packs at ``reference/<bcp47>.md``. Point ``LEGESHER_PREVIEW_ROOT`` or
``LEGESHER_LANGUAGE_PACKS_ROOT`` at a checkout and this module diffs every
registry language's file against the committed one here. Unset, the tests
skip and say so (the CI posture, as the preview repo's engine round-trip
does); set but wrong fails instead of skipping.

A mirror may trail the registry (preview ships 51 of 56 languages): a file the
mirror does not have is reported as missing by a separate test, never as a
drift of the files it does have.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = ROOT / "libs" / "i18n" / "language-packs" / "python"
REGISTRY = json.loads(
    (ROOT / "libs" / "i18n" / "legesher_i18n" / "languages.json").read_text(encoding="utf-8")
)["languages"]
CODES = sorted(REGISTRY)

MIRRORS = {
    "preview": ("LEGESHER_PREVIEW_ROOT", lambda code: Path("languages") / code / "REFERENCE.md"),
    "language-packs": (
        "LEGESHER_LANGUAGE_PACKS_ROOT",
        lambda code: Path("reference") / f"{REGISTRY[code]['bcp47']}.md",
    ),
}


def _mirror_root(name: str) -> Path:
    variable, _ = MIRRORS[name]
    value = os.environ.get(variable, "")
    if not value:
        pytest.skip(f"{variable} is not set; the {name} mirror is not checked in this run")
    root = Path(value)
    assert root.is_dir(), f"{variable}={value} is not a directory"
    return root


def _mirror_path(name: str, code: str) -> Path:
    _, relative = MIRRORS[name]
    return _mirror_root(name) / relative(code)


@pytest.mark.parametrize("name", sorted(MIRRORS))
def test_mirror_root_holds_at_least_one_reference(name: str) -> None:
    present = [code for code in CODES if _mirror_path(name, code).is_file()]
    assert present, f"no REFERENCE.md mirror found under {_mirror_root(name)}"


@pytest.mark.parametrize("code", CODES)
@pytest.mark.parametrize("name", sorted(MIRRORS))
def test_mirror_matches_the_generated_file(name: str, code: str) -> None:
    mirror = _mirror_path(name, code)
    if not mirror.is_file():
        pytest.skip(f"{name} has no file for {code} yet ({mirror})")
    expected = (PACKS_DIR / code / "REFERENCE.md").read_bytes()
    assert mirror.read_bytes() == expected, (
        f"{mirror} differs from {PACKS_DIR / code / 'REFERENCE.md'}; "
        "copy the generated file over it"
    )


@pytest.mark.parametrize("name", sorted(MIRRORS))
def test_mirror_reports_which_languages_it_lacks(name: str) -> None:
    missing = [code for code in CODES if not _mirror_path(name, code).is_file()]
    # Informational until the mirror carries every registry language; the
    # count is asserted so a regression from a fuller mirror is loud.
    allowed = {"preview": 5, "language-packs": 0}[name]
    assert len(missing) <= allowed, f"{name} lacks {missing}"
