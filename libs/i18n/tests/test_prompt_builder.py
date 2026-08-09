"""Tests for PromptBuilder.

Covers prompt construction for identifiers and text elements,
system prompt content, user prompt formatting, token estimation,
language framing with/without precedent, and glossary handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from legesher_i18n.prompt_builder import (
    NATIVE_LANG_EXAMPLES,
    PromptBuilder,
)
from legesher_i18n.style_guides import StyleGuideLoader

# Path to the real style-guides directory shipped with the package.
_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def loader() -> StyleGuideLoader:
    """Return a StyleGuideLoader pointed at the real style-guides dir."""
    return StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR)


@pytest.fixture
def builder(loader: StyleGuideLoader) -> PromptBuilder:
    """Return a PromptBuilder backed by the real style guides."""
    return PromptBuilder(loader)


@pytest.fixture
def sample_identifiers() -> list[dict[str, Any]]:
    """A small set of identifiers for testing."""
    return [
        {"text": "add_two", "role": "function_name", "context": {}},
        {"text": "result", "role": "variable", "context": {}},
        {"text": "Calculator", "role": "class_name", "context": {}},
    ]


@pytest.fixture
def sample_glossary() -> dict[str, str]:
    """A pre-existing glossary for consistency testing."""
    return {
        "get_value": "obtener_valor",
        "set_value": "establecer_valor",
    }


@pytest.fixture
def sample_texts() -> list[dict[str, Any]]:
    """A small set of text elements for testing."""
    return [
        {
            "text": "Calculate the sum of two numbers.",
            "kind": "docstring",
            "context": {},
        },
        {"text": "# increment counter", "kind": "comment", "context": {}},
    ]


# ------------------------------------------------------------------
# 1. test_build_identifier_prompt_returns_tuple
# ------------------------------------------------------------------


class TestBuildIdentifierPromptReturnsTuple:
    """build_identifier_prompt returns a (str, str) tuple."""

    def test_returns_tuple_of_two_strings(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        result = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)

    def test_both_parts_are_nonempty(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert len(system) > 0
        assert len(user) > 0


# ------------------------------------------------------------------
# 2. test_system_prompt_contains_framing
# ------------------------------------------------------------------


class TestSystemPromptContainsFraming:
    """System prompt contains persona framing with language name."""

    def test_contains_professor(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "computer science professor" in system

    def test_contains_language_name(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "Spanish" in system

    def test_urdu_framing_uses_urdu_name(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="ur",
            existing_glossary={},
        )
        assert "Urdu" in system


# ------------------------------------------------------------------
# 3. test_system_prompt_contains_style_guide
# ------------------------------------------------------------------


class TestSystemPromptContainsStyleGuide:
    """System prompt includes style guide sections."""

    def test_contains_style_guide_header(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "## Style Guide" in system

    def test_contains_naming_conventions(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "Naming Conventions" in system

    def test_contains_script_section(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "### Script" in system
        assert "Writing system: Latin" in system

    def test_contains_script_constraints(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        # A leaf guide's script.constraints reach the prompt verbatim (here es's
        # digits line — Spanish has no native digits, so it prescribes ASCII 0-9).
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "ASCII 0-9" in system

    def test_capabilities_reflect_supports_flags(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        # A cased script (es) can express all four conventions — assert the whole
        # rendered line so a dropped convention or reordering is caught.
        cased, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers, target_lang="es", existing_glossary={}
        )
        assert (
            "Conventions this script can express: "
            "snake_case, UPPER_SNAKE_CASE, CapWords, camelCase." in cased
        )
        # ... a caseless one only snake_case.
        caseless, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers, target_lang="zh", existing_glossary={}
        )
        assert "Conventions this script can express: snake_case." in caseless

    def test_caseless_target_emits_morphology_note(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers, target_lang="zh", existing_glossary={}
        )
        assert "This script has no letter case" in system

    def test_word_formation_rules_reach_the_prompt(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        # naming.word_formation carries how terms are COINED (CORE-1706, si).
        # The field is optional and language-level, so it is easy to add to a
        # guide and never render — assert every rule si declares arrives.
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers, target_lang="si", existing_glossary={}
        )
        guide = builder._loader.load("si")
        rules = guide["naming"]["word_formation"]
        assert rules, "si must declare word_formation rules for this test to bite"
        for rule in rules:
            assert rule.strip() in system

    def test_word_formation_absent_when_not_declared(
        self,
        builder: PromptBuilder,
    ) -> None:
        # es declares no word_formation; the Naming section must not grow an
        # empty bullet or a stray heading for it.
        guide = builder._loader.load("es")
        assert "word_formation" not in guide.get("naming", {})
        section = builder._build_style_guide_section("es")
        assert "- \n" not in section and not section.endswith("- ")

    def test_no_translation_conventions_section(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        # Vocabulary moved to the packs (CORE-1398); the prompt no longer renders
        # a translation-conventions block from the style guide (CORE-1395).
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers, target_lang="es", existing_glossary={}
        )
        assert "Translation Conventions" not in system

    def test_structural_only_guide_reports_unavailable(
        self,
        builder: PromptBuilder,
    ) -> None:
        # A code with no dedicated guide ("xx") resolves to base + direction
        # structural nodes only (no naming/script/formatting), so the section
        # reports unavailable rather than emitting an empty Style Guide block.
        section = builder._build_style_guide_section("xx")
        assert (
            section == "## Style Guide\n\nNo style guide available for this language."
        )


# ------------------------------------------------------------------
# 4. test_system_prompt_contains_critical_rules
# ------------------------------------------------------------------


class TestSystemPromptContainsCriticalRules:
    """System prompt includes critical rules about valid Python identifiers."""

    def test_contains_valid_python_identifiers(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "valid Python identifiers" in system

    def test_contains_critical_rules_header(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "## Critical Rules" in system

    def test_contains_snake_case_rule(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "snake_case" in system


# ------------------------------------------------------------------
# 5. test_system_prompt_same_for_same_language
# ------------------------------------------------------------------


class TestSystemPromptSameForSameLanguage:
    """Two calls with the same language produce identical system prompts."""

    def test_identical_system_prompts(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system1, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        system2, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "foo", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={"bar": "baz"},
        )
        assert system1 == system2

    def test_different_languages_produce_different_prompts(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system_es, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        system_ur, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="ur",
            existing_glossary={},
        )
        assert system_es != system_ur


# ------------------------------------------------------------------
# 6. test_user_prompt_contains_identifiers
# ------------------------------------------------------------------


class TestUserPromptContainsIdentifiers:
    """User prompt lists the identifiers with their roles."""

    def test_identifiers_appear_in_table(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "`add_two`" in user
        assert "`result`" in user
        assert "`Calculator`" in user

    def test_roles_appear_in_table(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "function_name" in user
        assert "variable" in user
        assert "class_name" in user

    def test_table_has_header_row(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "Identifier" in user
        assert "Role" in user


# ------------------------------------------------------------------
# 7. test_user_prompt_contains_glossary
# ------------------------------------------------------------------


class TestUserPromptContainsGlossary:
    """When a glossary is provided, user prompt includes the glossary table."""

    def test_glossary_table_present(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
        sample_glossary: dict[str, str],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary=sample_glossary,
        )
        assert "already been translated" in user

    def test_glossary_entries_in_table(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
        sample_glossary: dict[str, str],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary=sample_glossary,
        )
        assert "`get_value`" in user
        assert "`obtener_valor`" in user
        assert "`set_value`" in user
        assert "`establecer_valor`" in user

    def test_glossary_table_has_headers(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
        sample_glossary: dict[str, str],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary=sample_glossary,
        )
        assert "Original" in user
        assert "Translation" in user


# ------------------------------------------------------------------
# 8. test_user_prompt_pattern_consistency
# ------------------------------------------------------------------


class TestUserPromptPatternConsistency:
    """User prompt includes 'SAME verb' instruction for pattern consistency."""

    def test_same_verb_instruction(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "SAME verb" in user


# ------------------------------------------------------------------
# 9. test_text_prompt_contains_identifier_glossary
# ------------------------------------------------------------------


class TestTextPromptContainsIdentifierGlossary:
    """build_text_prompt includes identifier glossary for consistency."""

    def test_glossary_present_in_text_prompt(
        self,
        builder: PromptBuilder,
        sample_texts: list[dict[str, Any]],
    ) -> None:
        glossary = {"counter": "contador", "increment": "incrementar"}
        _, user = builder.build_text_prompt(
            texts=sample_texts,
            target_lang="es",
            identifier_glossary=glossary,
        )
        assert "`counter`" in user
        assert "`contador`" in user

    def test_consistency_instruction(
        self,
        builder: PromptBuilder,
        sample_texts: list[dict[str, Any]],
    ) -> None:
        glossary = {"counter": "contador"}
        _, user = builder.build_text_prompt(
            texts=sample_texts,
            target_lang="es",
            identifier_glossary=glossary,
        )
        assert "SAME terms" in user


# ------------------------------------------------------------------
# 10. test_text_prompt_contains_items
# ------------------------------------------------------------------


class TestTextPromptContainsItems:
    """User prompt lists text items with their kind."""

    def test_items_listed_with_kind(
        self,
        builder: PromptBuilder,
        sample_texts: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_text_prompt(
            texts=sample_texts,
            target_lang="es",
            identifier_glossary={},
        )
        assert "docstring" in user
        assert "comment" in user

    def test_text_content_appears(
        self,
        builder: PromptBuilder,
        sample_texts: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_text_prompt(
            texts=sample_texts,
            target_lang="es",
            identifier_glossary={},
        )
        assert "Calculate the sum of two numbers." in user
        assert "# increment counter" in user

    def test_item_numbering(
        self,
        builder: PromptBuilder,
        sample_texts: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_text_prompt(
            texts=sample_texts,
            target_lang="es",
            identifier_glossary={},
        )
        assert "Item 1" in user
        assert "Item 2" in user


# ------------------------------------------------------------------
# 11. test_estimate_tokens
# ------------------------------------------------------------------


class TestEstimateTokens:
    """estimate_tokens returns a reasonable positive integer."""

    def test_returns_positive_int(self, builder: PromptBuilder) -> None:
        result = builder.estimate_tokens("system prompt text", "user prompt text")
        assert isinstance(result, int)
        assert result > 0

    def test_scales_with_length(self, builder: PromptBuilder) -> None:
        short = builder.estimate_tokens("a", "b")
        long = builder.estimate_tokens("a" * 1000, "b" * 1000)
        assert long > short

    def test_empty_strings(self, builder: PromptBuilder) -> None:
        result = builder.estimate_tokens("", "")
        assert result == 0

    def test_approximation_reasonable(self, builder: PromptBuilder) -> None:
        # 400 chars should be approximately 100 tokens (400/4)
        result = builder.estimate_tokens("x" * 200, "y" * 200)
        assert result == 100


# ------------------------------------------------------------------
# 12. test_language_framing_with_precedent
# ------------------------------------------------------------------


class TestLanguageFramingWithPrecedent:
    """Languages with known precedent include specific framing."""

    def test_spanish_mentions_latino_and_lexico(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "Latino" in system
        assert "Lexico" in system

    def test_chinese_mentions_wenyan(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="zh",
            existing_glossary={},
        )
        assert "wenyan" in system.lower() or "\u6587\u8a00" in system

    def test_arabic_mentions_qalb(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="ar",
            existing_glossary={},
        )
        assert "Qalb" in system or "\u0642\u0644\u0628" in system

    def test_all_precedent_languages_have_entries(self) -> None:
        """Verify all NATIVE_LANG_EXAMPLES keys are present."""
        expected = {"zh", "es", "ar", "hi", "fr", "ru", "ja", "ko"}
        assert set(NATIVE_LANG_EXAMPLES.keys()) == expected


# ------------------------------------------------------------------
# 13. test_language_framing_without_precedent
# ------------------------------------------------------------------


class TestLanguageFramingWithoutPrecedent:
    """Languages without precedent get 'first programming experience' framing."""

    def test_finnish_gets_first_experience_framing(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="fi",
            existing_glossary={},
        )
        assert "first" in system.lower()
        assert "Finnish" in system

    def test_bengali_gets_first_experience_framing(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="bn",
            existing_glossary={},
        )
        assert "first" in system.lower()
        assert "Bengali" in system

    def test_no_precedent_does_not_mention_existing_languages(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        system, _ = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="fi",
            existing_glossary={},
        )
        # Should not mention "already exist" since there is no precedent
        assert "already exist" not in system


# ------------------------------------------------------------------
# 14. test_empty_glossary
# ------------------------------------------------------------------


class TestEmptyGlossary:
    """No glossary section when the glossary is empty."""

    def test_no_glossary_section_for_identifiers(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert "already been translated" not in user
        assert "Original" not in user

    def test_no_glossary_section_for_texts(
        self,
        builder: PromptBuilder,
        sample_texts: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_text_prompt(
            texts=sample_texts,
            target_lang="es",
            identifier_glossary={},
        )
        # No identifier glossary table when empty
        assert "SAME terms" not in user

    def test_glossary_present_when_nonempty(
        self,
        builder: PromptBuilder,
        sample_identifiers: list[dict[str, Any]],
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={"foo": "bar"},
        )
        assert "already been translated" in user


# ------------------------------------------------------------------
# 15. test_text_prompt_string_preservation
# ------------------------------------------------------------------


class TestTextPromptStringPreservation:
    """Text prompts should instruct the LLM to preserve technical values."""

    def test_contains_do_not_translate_instruction(self, builder):
        """Text prompt should contain instruction to NOT translate technical values."""
        system, user = builder.build_text_prompt(
            texts=[{"text": "Hello world", "kind": "string", "context": {}}],
            target_lang="es",
            identifier_glossary={},
        )
        assert "Do NOT translate technical values" in user

    def test_mentions_digits(self, builder):
        """Should explicitly mention digits as non-translatable."""
        _, user = builder.build_text_prompt(
            texts=[{"text": "test", "kind": "string", "context": {}}],
            target_lang="es",
            identifier_glossary={},
        )
        assert '"1"' in user or "digits" in user.lower()

    def test_mentions_main(self, builder):
        """Should explicitly mention __main__ as non-translatable."""
        _, user = builder.build_text_prompt(
            texts=[{"text": "test", "kind": "string", "context": {}}],
            target_lang="es",
            identifier_glossary={},
        )
        assert "__main__" in user

    def test_mentions_operators(self, builder):
        """Should explicitly mention operators as non-translatable."""
        _, user = builder.build_text_prompt(
            texts=[{"text": "test", "kind": "string", "context": {}}],
            target_lang="es",
            identifier_glossary={},
        )
        assert "+" in user and "-" in user

    def test_mentions_comment_instruction_rule(self, builder):
        """Should instruct LLM to translate comment TEXT, not execute instructions."""
        _, user = builder.build_text_prompt(
            texts=[
                {"text": "legesher translate foo.py", "kind": "comment", "context": {}}
            ],
            target_lang="es",
            identifier_glossary={},
        )
        assert "not executing" in user.lower() or "not execute" in user.lower()
        assert "command syntax" in user.lower() or "PRESERVE" in user


class TestSingleLetterVariableConventions:
    """Critical rules should include single-letter variable guidance."""

    def test_mentions_exception_variable(self, builder):
        """Should mention e as exception instance."""
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "e", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert "`e`" in system and "exception" in system.lower()

    def test_mentions_file_handle(self, builder):
        """Should mention f as file handle."""
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "f", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert "`f`" in system and "file" in system.lower()

    def test_mentions_loop_indices(self, builder):
        """Should mention i, j, k as loop indices."""
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "i", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert "`i`" in system and "loop" in system.lower()

    def test_instructs_keep_short(self, builder):
        """Should instruct to keep translations short (1-3 chars)."""
        system, _ = builder.build_identifier_prompt(
            identifiers=[{"text": "e", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
        )
        assert "1-3" in system or "SHORT" in system
