"""Tests for the optional ``examples`` kwarg on the public build methods.

Few-shot examples let callers say "here's how `selected_index` should
look in the target language" right inside the prompt. Today there's no
way to inject this; ``existing_glossary`` covers the consistency angle
but only after a translation has happened.

Decision (CORE-950 refinements D1): add an ``examples`` parameter to
``build_identifier_prompt`` / ``build_text_prompt`` rather than loading
per-language ``examples.yml`` files via StyleGuideLoader. Less coupled,
no schema work, easier to test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from legesher_i18n.prompt_builder import PromptBuilder
from legesher_i18n.style_guides import StyleGuideLoader

_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"

# Unique marker the new section must contain. "Examples" alone is too
# common in style-guide-rendered text, so use the heading verbatim.
_EXAMPLES_HEADING = "### Few-Shot Examples"


@pytest.fixture
def builder() -> PromptBuilder:
    return PromptBuilder(StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR))


class TestExamplesKwargIdentifier:
    def test_omitting_examples_still_works(self, builder: PromptBuilder) -> None:
        # Backward compat: existing callers pass 3 args.
        system, user = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert system and user

    def test_no_section_when_kwarg_omitted(self, builder: PromptBuilder) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert _EXAMPLES_HEADING not in user

    def test_no_section_when_kwarg_empty(self, builder: PromptBuilder) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
            examples=[],
        )
        assert _EXAMPLES_HEADING not in user

    def test_malformed_examples_log_warning(
        self, builder: PromptBuilder, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Self-review item A on PR #237: silently skipping malformed
        entries gave callers no signal when they had a typo (e.g.
        ``origin`` instead of ``original``). Now logs a warning.
        """
        import logging

        with caplog.at_level(logging.WARNING, logger="legesher_i18n.prompt_builder"):
            _, user = builder.build_identifier_prompt(
                identifiers=[{"text": "x", "role": "variable", "context": {}}],
                target_lang="es",
                existing_glossary={},
                examples=[
                    {"foo": "bar"},  # missing keys
                    {"original": "good", "translation": "bueno"},
                    {"original": "", "translation": "empty"},  # empty original
                ],
            )

        # Section still rendered for the one valid entry.
        assert _EXAMPLES_HEADING in user
        assert "bueno" in user

        # Warning was logged for the 2 skipped entries.
        warnings = [r for r in caplog.records if "malformed" in r.message.lower()]
        assert warnings, "Expected a warning for the skipped malformed entries"
        assert "2" in warnings[0].message, (
            "Warning should mention the skipped count (2)"
        )

    def test_examples_render_in_user_prompt(self, builder: PromptBuilder) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
            examples=[
                {"original": "selected_index", "translation": "indice_seleccionado"},
                {"original": "user_count", "translation": "conteo_usuarios"},
            ],
        )
        assert _EXAMPLES_HEADING in user
        assert "selected_index" in user
        assert "indice_seleccionado" in user
        assert "user_count" in user
        assert "conteo_usuarios" in user

    def test_examples_in_user_not_system(self, builder: PromptBuilder) -> None:
        """Examples vary per call -- belong in the user prompt to keep the
        system prompt cacheable per-language.
        """
        system, user = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
            examples=[{"original": "unique_marker", "translation": "marcador_unico"}],
        )
        assert "unique_marker" not in system
        assert "unique_marker" in user


class TestExamplesKwargText:
    def test_text_prompt_accepts_examples(self, builder: PromptBuilder) -> None:
        _, user = builder.build_text_prompt(
            texts=[{"text": "Process the data.", "kind": "comment", "context": {}}],
            target_lang="es",
            identifier_glossary={},
            examples=[
                {
                    "original": "Returns the user count.",
                    "translation": "Devuelve el conteo de usuarios.",
                }
            ],
        )
        assert _EXAMPLES_HEADING in user
        assert "Devuelve el conteo de usuarios." in user

    def test_text_prompt_omitting_examples_works(self, builder: PromptBuilder) -> None:
        # Backward compat for text path.
        system, user = builder.build_text_prompt(
            texts=[{"text": "Process.", "kind": "comment", "context": {}}],
            target_lang="es",
            identifier_glossary={},
        )
        assert system and user
