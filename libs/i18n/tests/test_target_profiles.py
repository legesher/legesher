"""Tests for the target-profile slice (CORE-1608).

Two guarantees:

1. Python stays byte-identical -- no ``spec/targets/python/`` exists, so the
   default builder emits exactly the historical wording, with no Target
   Guide section.
2. ``target="javascript"`` seasons the prompts: the Target Guide section,
   the JS identifier/casing rules, and the display name all reach the
   prompt the model sees.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from legesher_i18n.prompt_builder import PromptBuilder
from legesher_i18n.style_guides import StyleGuideLoader
from legesher_i18n.target_profiles import TargetProfileLoader

_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"
_TARGETS_DIR = Path(__file__).parent.parent / "spec" / "targets"

IDENTIFIERS: list[dict[str, Any]] = [
    {"text": "addTwo", "role": "function_name", "context": {}},
]


@pytest.fixture
def loader() -> StyleGuideLoader:
    """Return a StyleGuideLoader pointed at the real style-guides dir."""
    return StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR)


@pytest.fixture
def js_builder(loader: StyleGuideLoader) -> PromptBuilder:
    """Return a PromptBuilder seasoned with the shipped javascript target."""
    return PromptBuilder(loader, target="javascript")


class TestTargetProfileLoader:
    """The loader half: spec directories in, data out."""

    def test_javascript_loads_profile_and_guide(self) -> None:
        spec = TargetProfileLoader(targets_dir=_TARGETS_DIR).load("javascript")
        assert spec["profile"]["display_name"] == "JavaScript"
        assert spec["profile"]["version_token_pattern"] == "^es\\d{4}$"
        assert spec["profile"]["partitions"] == ["keywords", "builtins", "members"]
        assert "of" in spec["profile"]["contextual_keywords"]
        assert "property names" in spec["guide"]

    def test_guide_provenance_comment_is_stripped(self) -> None:
        spec = TargetProfileLoader(targets_dir=_TARGETS_DIR).load("javascript")
        assert "<!--" not in spec["guide"]
        assert spec["guide"].startswith("### Vocabulary shape")

    def test_target_without_spec_dir_resolves_empty(self) -> None:
        assert TargetProfileLoader(targets_dir=_TARGETS_DIR).load("python") == {}

    def test_invalid_target_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid target name"):
            TargetProfileLoader(targets_dir=_TARGETS_DIR).load("Java Script")

    def test_malformed_profile_fails_loud(self, tmp_path: Path) -> None:
        # A skipped-but-present profile would hand a generation run another
        # language's instincts, so the loader must raise, not warn.
        target = tmp_path / "badlang"
        target.mkdir()
        (target / "profile.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError, match="Unreadable target profile"):
            TargetProfileLoader(targets_dir=tmp_path).load("badlang")

    def test_cache_returns_same_object(self) -> None:
        single = TargetProfileLoader(targets_dir=_TARGETS_DIR)
        assert single.load("javascript") is single.load("javascript")

    def test_multiple_leading_comments_are_stripped(self, tmp_path: Path) -> None:
        # A lint directive rides in its own comment ahead of the provenance
        # comment; both must be stripped before the guide reaches a prompt.
        target = tmp_path / "commented"
        target.mkdir()
        (target / "GUIDE.md").write_text(
            "<!-- markdownlint-disable MD041 -->\n<!-- provenance -->\n\n### Rules\n",
            encoding="utf-8",
        )
        spec = TargetProfileLoader(targets_dir=tmp_path).load("commented")
        assert spec["guide"] == "### Rules"


class TestPythonByteIdentical:
    """The default target keeps the pre-target-aware wording exactly."""

    def test_default_equals_explicit_python(self, loader: StyleGuideLoader) -> None:
        default_pair = PromptBuilder(loader).build_identifier_prompt(
            identifiers=IDENTIFIERS, target_lang="ar", existing_glossary={}
        )
        explicit_pair = PromptBuilder(loader, target="python").build_identifier_prompt(
            identifiers=IDENTIFIERS, target_lang="ar", existing_glossary={}
        )
        assert default_pair == explicit_pair

    def test_historical_wording_survives(self, loader: StyleGuideLoader) -> None:
        system, user = PromptBuilder(loader).build_identifier_prompt(
            identifiers=IDENTIFIERS, target_lang="ar", existing_glossary={}
        )
        assert "designing Python code" in system
        assert (
            "All translations MUST be valid Python identifiers -- "
            "no spaces, no punctuation." in system
        )
        assert (
            "snake_case identifiers stay snake_case, PascalCase stays PascalCase."
            in system
        )
        assert "## Target Guide" not in system
        assert "Translate the following Python identifiers into" in user

    def test_forbidden_section_keeps_python_wording(
        self, loader: StyleGuideLoader
    ) -> None:
        _, user = PromptBuilder(loader).build_identifier_prompt(
            identifiers=IDENTIFIERS,
            target_lang="ar",
            existing_glossary={},
            forbidden_values=["مثال"],
        )
        assert "already used for Python keywords" in user


class TestJavascriptSeasoning:
    """target="javascript" reaches every prompt surface it should."""

    def test_system_prompt_carries_guide_and_rules(
        self, js_builder: PromptBuilder
    ) -> None:
        system, user = js_builder.build_identifier_prompt(
            identifiers=IDENTIFIERS, target_lang="ar", existing_glossary={}
        )
        assert "designing JavaScript code" in system
        assert "## Target Guide (JavaScript)" in system
        assert "property names" in system
        assert "valid JavaScript identifiers" in system
        assert "camelCase identifiers stay camelCase" in system
        assert "valid Python identifiers" not in system
        assert "snake_case identifiers stay snake_case" not in system
        assert "Translate the following JavaScript identifiers into" in user

    def test_target_guide_sits_between_style_guide_and_critical_rules(
        self, js_builder: PromptBuilder
    ) -> None:
        system = js_builder.build_identifier_prompt(
            identifiers=IDENTIFIERS, target_lang="ar", existing_glossary={}
        )[0]
        assert (
            system.index("## Style Guide")
            < system.index("## Target Guide")
            < system.index("## Critical Rules")
        )

    def test_forbidden_section_names_the_target(
        self, js_builder: PromptBuilder
    ) -> None:
        _, user = js_builder.build_identifier_prompt(
            identifiers=IDENTIFIERS,
            target_lang="ar",
            existing_glossary={},
            forbidden_values=["مثال"],
        )
        assert "already used for JavaScript keywords" in user

    def test_arabic_bare_form_note_reaches_the_prompt(
        self, js_builder: PromptBuilder
    ) -> None:
        system = js_builder.build_identifier_prompt(
            identifiers=IDENTIFIERS, target_lang="ar", existing_glossary={}
        )[0]
        assert "bare (unvocalized)" in system
