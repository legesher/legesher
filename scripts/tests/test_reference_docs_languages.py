"""Every published language is covered by the REFERENCE.md generator's maps.

``scripts/generate_reference_docs.py`` keeps two hand-written per-language
tables: ``LANGUAGE_SCRIPTS`` (the Script row and badge) and ``EXAMPLE_TEXT``
(the identifiers, comments and messages in the example program). A language
missing from either does not fail the generator. It falls back to "Unknown" and
to Spanish, which is how the first Ukrainian REFERENCE.md shipped a Spanish
example under a Ukrainian heading. This module reads the registry the
generator serves and requires both entries for every published language.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "libs" / "i18n" / "legesher_i18n" / "languages.json"

#: The canonical language ships no REFERENCE.md, so it needs no example text.
CANONICAL = json.loads(REGISTRY.read_text(encoding="utf-8"))["canonical_language"]


def _generator():
    spec = importlib.util.spec_from_file_location(
        "generate_reference_docs", ROOT / "scripts" / "generate_reference_docs.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR = _generator()
LANGUAGES = sorted(json.loads(REGISTRY.read_text(encoding="utf-8"))["languages"])


@pytest.mark.parametrize("code", LANGUAGES)
def test_language_has_a_script(code: str) -> None:
    assert code in GENERATOR.LANGUAGE_SCRIPTS, (
        f"{code!r} is published but has no LANGUAGE_SCRIPTS entry; its "
        "REFERENCE.md would say 'Script: Unknown'"
    )


@pytest.mark.parametrize("code", [c for c in LANGUAGES if c != CANONICAL])
def test_language_has_example_text(code: str) -> None:
    assert code in GENERATOR.EXAMPLE_TEXT, (
        f"{code!r} is published but has no EXAMPLE_TEXT entry; its "
        "REFERENCE.md example would fall back to Spanish"
    )
    assert set(GENERATOR.EXAMPLE_TEXT[code]) == set(GENERATOR.EXAMPLE_TEXT["es"])
