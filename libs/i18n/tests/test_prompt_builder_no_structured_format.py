"""Tests for the no-structured/labeled-output-format rule in PromptBuilder.

CORE-1048 follow-up to CORE-950. Smaller models (notably ``tiny-aya-global``,
3.35B params) follow the CORE-950 "no explanation" rule but still emit
structured/labeled mappings of the form
``original_name_<en>_translated_name_<tgt>``. This is a separate
prompt-following failure from the trace-wrapper one — it produces a valid
Python identifier that round-trips through AST validation, just an unusable
translation.

The rule must:

* Forbid wrapping the translation in any structured key/value, label, JSON,
  or paired format.
* Forbid joining the original identifier to the translation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from legesher_i18n.prompt_builder import PromptBuilder
from legesher_i18n.style_guides import StyleGuideLoader

# Path to the real style-guides directory shipped with the package.
_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"


@pytest.fixture
def builder() -> PromptBuilder:
    """PromptBuilder backed by the real style guides."""
    return PromptBuilder(StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR))


def test_critical_rules_forbid_labeled_mapping_format(
    builder: PromptBuilder,
) -> None:
    """The system prompt must include a phrase that forbids structured /
    labeled output formats for identifier translations.
    """
    system, _ = builder.build_identifier_prompt(
        identifiers=[{"text": "calculate_tax", "role": "function_name", "context": {}}],
        target_lang="ur",
        existing_glossary={},
    )
    s = system.lower()
    assert any(
        p in s
        for p in [
            "no structured",
            "no labeled",
            "no key/value",
            "bare translated identifier",
            "no paired format",
        ]
    ), "Prompt is missing the no-structured-format instruction"


def test_critical_rules_forbid_original_translation_pairing(
    builder: PromptBuilder,
) -> None:
    """The system prompt must explicitly cite the labeled-mapping pattern
    so the rule is unambiguous to the model.

    Anchors on the literal example string ``original_name_X_translated_name_Y``
    that the new bullet calls out by name. This is unique to the CORE-1048
    rule -- no other section of the prompt contains it -- so the test will
    fail loudly if the rule is removed or watered down to omit the example.
    """
    system, _ = builder.build_identifier_prompt(
        identifiers=[{"text": "x", "role": "variable", "context": {}}],
        target_lang="zh",
        existing_glossary={},
    )
    s = system.lower()
    # Anchor on the literal labeled-mapping example, which is unique to the
    # CORE-1048 bullet. Loose pairing assertions like
    #   ("original" in s and "not" in s)
    # would also pass on the existing CORE-950 rule, so they don't actually
    # guard this rule's presence.
    assert "original_name_x_translated_name_y" in s, (
        "Prompt is missing the literal labeled-mapping example "
        "`original_name_X_translated_name_Y` that the rule calls out"
    )


def test_critical_rules_present_in_text_prompt(
    builder: PromptBuilder,
) -> None:
    """The rule lives in ``_CRITICAL_RULES`` so it must apply to text-element
    prompts as well as identifier prompts. The ticket explicitly calls out
    that comments and docstrings can also exhibit labeled-mapping behavior
    in worse cases on small models.
    """
    system, _ = builder.build_text_prompt(
        texts=[{"text": "Compute the tax.", "kind": "docstring", "context": {}}],
        target_lang="ur",
        identifier_glossary={},
    )
    s = system.lower()
    # Same anchor phrases as the identifier-prompt test -- the rule renders
    # identically in both prompt types because both flow through
    # `_build_system_prompt -> _build_critical_rules_section`.
    assert any(
        p in s
        for p in [
            "no structured",
            "no labeled",
            "no key/value",
            "bare translated identifier",
            "no paired format",
        ]
    ), "Text prompt is missing the no-structured-format instruction"
    assert "original_name_x_translated_name_y" in s, (
        "Text prompt is missing the literal labeled-mapping example"
    )
