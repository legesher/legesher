"""The VS Code language settings list every published language, each labelled as itself.

``libs/vs-code/package.json`` carries two hand-kept parallel arrays per language
setting: ``enum`` (the codes) and ``enumDescriptions`` (the labels shown in the
settings UI). Nothing tied them to the registry or to each other, so a label
inserted one place off showed Swahili for ``sv`` and Swedish for ``sw``. This
module reads the registry and requires every setting to list exactly the
published codes, with each label naming its own language.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = json.loads(
    (ROOT / "libs" / "i18n" / "legesher_i18n" / "languages.json").read_text(
        encoding="utf-8"
    )
)["languages"]
PACKAGE = json.loads(
    (ROOT / "libs" / "vs-code" / "package.json").read_text(encoding="utf-8")
)


def _language_settings() -> dict[str, dict]:
    """Every contributed setting whose enum is a list of language codes."""
    properties = PACKAGE["contributes"]["configuration"]
    if isinstance(properties, list):
        merged: dict[str, dict] = {}
        for block in properties:
            merged.update(block.get("properties", {}))
        properties = merged
    else:
        properties = properties["properties"]
    return {
        key: spec
        for key, spec in properties.items()
        if isinstance(spec.get("enum"), list) and "ar" in spec["enum"]
    }


SETTINGS = _language_settings()


def test_there_are_language_settings() -> None:
    # A guard on the guard: an empty sweep would pass everything below.
    assert len(SETTINGS) >= 2, sorted(SETTINGS)


@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_setting_lists_exactly_the_published_codes(setting: str) -> None:
    codes = SETTINGS[setting]["enum"]
    assert sorted(codes) == sorted(REGISTRY), (
        f"{setting}: missing {sorted(set(REGISTRY) - set(codes))}, "
        f"unpublished {sorted(set(codes) - set(REGISTRY))}"
    )
    assert len(codes) == len(set(codes)), f"{setting}: duplicate codes"


@pytest.mark.parametrize("setting", sorted(SETTINGS))
def test_each_label_names_its_own_language(setting: str) -> None:
    spec = SETTINGS[setting]
    labels = spec.get("enumDescriptions")
    assert labels is not None and len(labels) == len(spec["enum"]), setting
    crossed = [
        (code, label)
        for code, label in zip(spec["enum"], labels)
        if not label.startswith(REGISTRY[code]["name"])
    ]
    assert crossed == [], f"{setting}: labels that name another language: {crossed}"
