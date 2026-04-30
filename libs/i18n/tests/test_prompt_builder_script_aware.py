"""Tests for the script-aware naming-convention fallback (CORE-950).

Empirical Cohere finding (2026-04-29): both ``c4ai-aya-expanse-32b`` and
``command-a-translate-08-2025`` received ``naming_convention=PascalCase``
for ``PaymentProcessor`` and returned underscore-joined output (e.g.
``پرداخت_پردازشگر``, ``ادائیگی_پروشَر``) -- because Arabic/Urdu/Hebrew
script has no upper/lowercase distinction, PascalCase has no native
equivalent. The model's spontaneous fallback (snake_case) is correct;
the prompt should make this explicit so the LLM doesn't waste tokens
inventing the rule on every call.

Implementation (post-PR #237 review): the ``has_case_distinction``
boolean lives in ``languages.json`` next to ``rtl`` -- single source of
truth for language script properties. ``PromptBuilder`` reads it via
``LANGUAGE_CASE_DISTINCTION``; per-language style guides can still
override by setting ``script.has_case_distinction``. The substitute
rule fires for all 17 non-cased supported languages (Arabic family,
Brahmic, CJK, SE-Asian, Ge'ez).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from legesher_i18n.prompt_builder import PromptBuilder
from legesher_i18n.style_guides import StyleGuideLoader

_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"


@pytest.fixture
def builder() -> PromptBuilder:
    return PromptBuilder(StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR))


# Unique sentinel phrases the new substitute rule must contain. These are
# deliberately distinct from any pre-existing style-guide phrasing so the
# tests fail until the rule is actually wired (the `_format_naming_rules`
# block already mentions "non-Latin scripts have no case", which would
# otherwise cause weak-string matchers to pass accidentally).
_SUBSTITUTE_RULE_MARKER = "substitute snake_case"
_HAS_CASE_FALSE_MARKER = "target script has no case distinction"


class TestScriptAwareNamingFallback:
    def test_pascalcase_for_non_cased_script_emits_substitute_rule(
        self, builder: PromptBuilder
    ) -> None:
        """Urdu has no case distinction. The system prompt's Critical
        Rules section must contain an explicit substitute rule that
        overrides the base "PascalCase stays PascalCase" critical rule.
        """
        system, _ = builder.build_identifier_prompt(
            identifiers=[
                {
                    "text": "PaymentProcessor",
                    "role": "class_name",
                    "context": {"naming_convention": "PascalCase"},
                }
            ],
            target_lang="ur",
            existing_glossary={},
        )
        # The unique markers MUST appear -- the pre-existing style-guide
        # naming-rules section uses different phrasing ("non-Latin scripts
        # have no case"), so these sentinels can only come from the new
        # critical-rules entry.
        assert _SUBSTITUTE_RULE_MARKER in system, (
            f"Critical Rules section missing {_SUBSTITUTE_RULE_MARKER!r}. "
            f"System prompt tail:\n{system[-1500:]}"
        )
        assert _HAS_CASE_FALSE_MARKER in system, (
            f"Critical Rules section missing {_HAS_CASE_FALSE_MARKER!r}"
        )

    def test_arabic_target_emits_rule_via_languages_json(
        self, builder: PromptBuilder
    ) -> None:
        """Arabic has ``has_case_distinction: false`` in ``languages.json``
        (Arabic script has no upper/lowercase). PromptBuilder reads
        directly from the registry -- no per-language style guide
        required.
        """
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="ar",
            existing_glossary={},
        )
        assert _SUBSTITUTE_RULE_MARKER in system, (
            "ar must emit no-case rule from languages.json -- substitute "
            "rule sentinel missing from system prompt"
        )

    def test_chinese_target_emits_rule_via_languages_json(
        self, builder: PromptBuilder
    ) -> None:
        """Chinese is LTR but ``languages.json`` declares
        ``has_case_distinction: false`` (CJK has no case).
        """
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="zh",
            existing_glossary={},
        )
        assert _SUBSTITUTE_RULE_MARKER in system, (
            "zh: languages.json should drive the no-case rule"
        )

    def test_substitute_rule_absent_for_cased_target(
        self, builder: PromptBuilder
    ) -> None:
        """Negative regression: case-distinguishing targets (Latin/Cyrillic
        scripts) must NOT see the substitute rule -- their PascalCase
        identifiers should stay PascalCase per the base critical rule.
        """
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert _SUBSTITUTE_RULE_MARKER not in system, (
            "Spanish (Latin script, case-distinguishing) must NOT get "
            "the substitute rule -- PascalCase should stay PascalCase"
        )
        assert _HAS_CASE_FALSE_MARKER not in system

    def test_pascalcase_critical_rule_still_present_for_cased_target(
        self, builder: PromptBuilder
    ) -> None:
        """Sanity: the base critical rule survives for case-distinguishing
        targets so PascalCase identifiers still get PascalCase guidance.
        """
        system, _ = builder.build_identifier_prompt(
            identifiers=[
                {
                    "text": "PaymentProcessor",
                    "role": "class_name",
                    "context": {"naming_convention": "PascalCase"},
                }
            ],
            target_lang="es",
            existing_glossary={},
        )
        assert "PascalCase stays PascalCase" in system


class TestAllNonCasedLanguagesCovered:
    """The substitute rule must fire for every supported language whose
    script lacks case distinction. Empirical PR #237 finding: hi, ja,
    ko, bn, kn, ml, te, th and others used to fall through to the base
    PascalCase rule because they had no per-language style guide. After
    moving the metadata to ``languages.json``, all 17 non-cased
    languages get the rule via the registry.
    """

    # All 51 supported languages, partitioned by case distinction.
    _NO_CASE_LANGS = (
        # Arabic family (RTL).
        "ar",
        "fa",
        "he",
        "ur",
        # Brahmic.
        "bn",
        "gu",
        "hi",
        "kn",
        "ml",
        "te",
        # CJK.
        "ja",
        "ko",
        "zh",
        # Southeast Asian.
        "my",
        "si",
        "th",
        # Ge'ez.
        "am",
    )
    # Sample of cased Latin/Cyrillic/Greek languages, plus an unknown
    # code (``xx``) to verify the safe ``True`` default for languages
    # not in the registry.
    _CASED_LANGS = (
        "en",
        "es",
        "fr",
        "de",
        "ru",
        "el",
        "xx",  # Unknown code -- must default to True (case-distinguishing)
    )

    def test_all_17_non_cased_languages_fire_substitute_rule(
        self, builder: PromptBuilder
    ) -> None:
        """Every non-cased supported language must emit the substitute
        rule via ``languages.json``.
        """
        for lang in self._NO_CASE_LANGS:
            system, _ = builder.build_identifier_prompt(
                identifiers=[
                    {
                        "text": "PaymentProcessor",
                        "role": "class_name",
                        "context": {"naming_convention": "PascalCase"},
                    }
                ],
                target_lang=lang,
                existing_glossary={},
            )
            assert _SUBSTITUTE_RULE_MARKER in system, (
                f"{lang!r} (script lacks case distinction) must get the "
                f"substitute rule from languages.json"
            )

    def test_cased_languages_do_not_fire_substitute_rule(
        self, builder: PromptBuilder
    ) -> None:
        """Negative regression: Latin/Cyrillic/Greek languages -- and
        unknown languages defaulting to True -- must NOT see the rule.
        """
        for lang in self._CASED_LANGS:
            system, _ = builder.build_identifier_prompt(
                identifiers=[{"text": "x", "role": "variable", "context": {}}],
                target_lang=lang,
                existing_glossary={},
            )
            assert _SUBSTITUTE_RULE_MARKER not in system, (
                f"{lang!r} (cased script or unknown) must NOT get the substitute rule"
            )

    def test_languages_json_mapping_loaded_at_import(self) -> None:
        """The ``LANGUAGE_CASE_DISTINCTION`` constant must be populated
        from ``languages.json`` at import time (not lazily); empty would
        mean the loader silently failed.
        """
        from legesher_i18n.prompt_builder import LANGUAGE_CASE_DISTINCTION

        assert LANGUAGE_CASE_DISTINCTION, (
            "LANGUAGE_CASE_DISTINCTION is empty -- languages.json failed "
            "to load or none of its entries have has_case_distinction set"
        )
        # Spot-checks against known values.
        assert LANGUAGE_CASE_DISTINCTION.get("en") is True
        assert LANGUAGE_CASE_DISTINCTION.get("ar") is False
        assert LANGUAGE_CASE_DISTINCTION.get("zh") is False
        assert LANGUAGE_CASE_DISTINCTION.get("hi") is False
        # 51 supported languages must all have the field set.
        assert len(LANGUAGE_CASE_DISTINCTION) == 51, (
            f"Expected 51 entries, got {len(LANGUAGE_CASE_DISTINCTION)}"
        )

    def test_style_guide_can_override_languages_json(self, tmp_path) -> None:
        """If a style guide explicitly sets ``script.has_case_distinction``,
        that wins over ``languages.json``. Defensive contract for future
        per-language overrides.
        """
        sg_dir = tmp_path / "style-guides"
        sg_dir.mkdir()
        # Minimal hierarchy.
        (sg_dir / "python.yml").write_text(
            "language: python\nextends: []\nversion: 0.1.0\n"
            "naming: {snake_case: {usage: vars}}\nscript: {native_required: true}\n"
        )
        (sg_dir / "_ltr.yml").write_text(
            "language: _ltr\nextends: [python.yml]\nversion: 0.1.0\nscript: {}\n"
        )
        (sg_dir / "_rtl.yml").write_text(
            "language: _rtl\nextends: [python.yml]\nversion: 0.1.0\nscript: {}\n"
        )
        # Override for ar: explicit True (overrides the False in
        # languages.json).
        (sg_dir / "ar.yml").write_text(
            "language: ar\nextends: [python.yml, _rtl.yml]\nversion: 0.1.0\n"
            "script: {has_case_distinction: true}\n"
        )

        override_builder = PromptBuilder(StyleGuideLoader(style_guides_dir=sg_dir))
        system, _ = override_builder.build_identifier_prompt(
            identifiers=[{"text": "x", "role": "variable", "context": {}}],
            target_lang="ar",
            existing_glossary={},
        )
        assert _SUBSTITUTE_RULE_MARKER not in system, (
            "Style-guide explicit `has_case_distinction: true` must "
            "override languages.json's `false` for ar"
        )
