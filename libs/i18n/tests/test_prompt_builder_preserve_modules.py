"""Tests for the ``preserve_module_names`` flag on PromptBuilder.

Cond-5 (full translation for training data) wants every identifier
including module/library names translated -- ``torch`` becomes the
target-language equivalent. Execution-targeted use cases (running
translated code against a real Python interpreter) need module names
to stay LITERAL so the import resolves at runtime.

The flag is per-builder-instance because it changes the system prompt
shape, which is meant to be cacheable per language.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from legesher_i18n.prompt_builder import PromptBuilder
from legesher_i18n.style_guides import StyleGuideLoader

_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"

# Unique marker the new rule must contain. Distinct from any pre-existing
# style-guide phrasing so tests don't pass accidentally.
_PRESERVE_MARKER = "preserve module names"


@pytest.fixture
def loader() -> StyleGuideLoader:
    return StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR)


class TestPreserveModuleNamesFlag:
    def test_default_off_no_preservation_rule(self, loader: StyleGuideLoader) -> None:
        """Default behavior (full translation) -- the system prompt must
        not contain the preservation directive.
        """
        builder = PromptBuilder(loader)
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "torch", "role": "module", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert _PRESERVE_MARKER not in system.lower(), (
            "Default builder must not emit the preserve-module-names rule"
        )

    def test_flag_on_emits_preservation_rule(self, loader: StyleGuideLoader) -> None:
        """When the flag is on, the system prompt must include the
        preservation directive so module names round-trip unchanged.
        """
        builder = PromptBuilder(loader, preserve_module_names=True)
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "torch", "role": "module", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert _PRESERVE_MARKER in system.lower(), (
            "preserve_module_names=True must emit the preservation rule"
        )

    def test_flag_on_for_non_cased_target_still_works(
        self, loader: StyleGuideLoader
    ) -> None:
        """Composes with step 4 -- ur target with preserve_module_names
        gets BOTH the script-aware substitute rule AND the preservation
        rule.
        """
        builder = PromptBuilder(loader, preserve_module_names=True)
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "torch", "role": "module", "context": {}}],
            target_lang="ur",
            existing_glossary={},
        )
        s = system.lower()
        assert _PRESERVE_MARKER in s
        # Step 4's marker should also be present for ur.
        assert "substitute snake_case" in system

    def test_flag_off_does_not_break_text_prompt(
        self, loader: StyleGuideLoader
    ) -> None:
        """The flag controls identifier prompts -- text prompts should be
        unaffected (default off, default on -- both fine).
        """
        for flag in (False, True):
            builder = PromptBuilder(loader, preserve_module_names=flag)
            system, user = builder.build_text_prompt(
                texts=[
                    {
                        "text": "Process the data.",
                        "kind": "comment",
                        "context": {},
                    }
                ],
                target_lang="es",
                identifier_glossary={},
            )
            assert system and user  # smoke
