"""Tests for the no-explanation / no-trace-wrapper rule in PromptBuilder.

Empirical findings on CORE-950 (gemma3:12b, Tiny Aya GGUF, Cohere V2 fallback)
showed that without an explicit "respond with only the translation" rule in
``_CRITICAL_RULES``, lower-resource targets (zh, ur) trigger the model's
"let me explain my reasoning" mode — producing output polluted with trace
markers (e.g., ``__original_X_translation_Y_Explanation_<long_essay>``) or
SDK template residue (e.g., ``____translated_identifier_X____``).

The rule must:

* Forbid prefixes, suffixes, explanations, and markup wrappers.
* Apply across target languages (rule is in ``_CRITICAL_RULES`` so the
  system prompt always carries it).
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


class TestNoExplanationRule:
    """The system prompt must instruct the model to emit only the translation."""

    def test_critical_rules_forbid_explanation_for_ur(
        self, builder: PromptBuilder
    ) -> None:
        """Urdu was the worst offender — gemma3:12b produced essay-length
        Explanation_<...> markers. The no-explanation rule must be present
        in the system prompt for ur target.
        """
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "selected_index", "role": "variable", "context": {}}],
            target_lang="ur",
            existing_glossary={},
        )
        s = system.lower()
        assert any(
            phrase in s
            for phrase in (
                "only the translation",
                "no prefix",
                "no explanation",
                "no markup",
                "no trace",
            )
        ), (
            "Prompt is missing the no-explanation instruction. "
            "System prompt sample:\n"
            f"{system[:500]}"
        )

    def test_critical_rules_forbid_trace_wrappers_for_zh(
        self, builder: PromptBuilder
    ) -> None:
        """Chinese also triggered trace-format pollution on gemma3:12b.
        Same rule must apply.
        """
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="zh",
            existing_glossary={},
        )
        s = system.lower()
        assert "wrapper" in s or "trace" in s or "no markup" in s, (
            "Prompt is missing the no-wrapper / no-trace instruction. "
            "System prompt sample:\n"
            f"{system[:500]}"
        )

    def test_rule_applies_across_targets(self, builder: PromptBuilder) -> None:
        """Sanity: the rule lives in _CRITICAL_RULES, so it must appear
        in the system prompt regardless of target.
        """
        for lang in ("es", "ja", "fa", "ur", "zh"):
            system, _ = builder.build_identifier_prompt(
                identifiers=[{"text": "x", "role": "variable", "context": {}}],
                target_lang=lang,
                existing_glossary={},
            )
            s = system.lower()
            assert any(
                phrase in s
                for phrase in (
                    "only the translation",
                    "no prefix",
                    "no explanation",
                )
            ), f"No-explanation rule missing from {lang!r} system prompt"
