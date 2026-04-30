"""Tests for the ``forbidden_values`` kwarg on ``build_identifier_prompt``.

CORE-710 introduced ``reserved_words`` (e.g. Spanish ``self -> mismo``,
Urdu ``self -> خود``). When the LLM proposes an identifier translation
that matches a reserved-word value, the result silently breaks round-trip
translation -- the reverse mapper can't tell which source key the value
maps back to.

The defense is two-layer (CORE-950):

1. Prompt: ``forbidden_values`` lists every reserved value the LLM must
   avoid, so a collision is unlikely to be proposed in the first place.
2. Translator: pack-aware ``IdentifierMap.add()`` (CORE-710) rejects the
   collision if it does land, and ``LLMTranslator`` retries-or-suffixes.

These tests cover layer 1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from legesher_i18n.prompt_builder import PromptBuilder
from legesher_i18n.style_guides import StyleGuideLoader

_STYLE_GUIDES_DIR = Path(__file__).parent.parent / "style-guides"


@pytest.fixture
def builder() -> PromptBuilder:
    return PromptBuilder(StyleGuideLoader(style_guides_dir=_STYLE_GUIDES_DIR))


@pytest.fixture
def sample_identifiers() -> list[dict[str, Any]]:
    return [{"text": "e", "role": "variable", "context": {}}]


class TestForbiddenValuesKwarg:
    """``build_identifier_prompt`` accepts a ``forbidden_values`` kwarg."""

    def test_signature_accepts_forbidden_values_kwarg(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        # Must not raise TypeError on the new kwarg.
        builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
            forbidden_values=["mismo", "definir"],
        )

    def test_omitting_forbidden_values_still_works(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        # Backward compat: existing 3-arg callers must keep working.
        system, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        assert system and user

    def test_forbidden_values_appear_in_prompt(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        system, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
            forbidden_values=["mismo", "misma_clase", "definir"],
        )
        combined = system + user
        assert "mismo" in combined
        assert "misma_clase" in combined
        assert "definir" in combined

    def test_no_forbidden_section_when_kwarg_omitted(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
        )
        # Heading is gated by the kwarg, so it must not appear.
        assert "reserved" not in user.lower() or "do not use" not in user.lower()

    def test_no_forbidden_section_when_kwarg_empty(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
            forbidden_values=[],
        )
        # Empty list is treated the same as None — no section emitted.
        assert "reserved" not in user.lower() or "do not use" not in user.lower()

    def test_forbidden_section_is_in_user_prompt_not_system(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        """Forbidden values change per-call, so they belong in the user
        prompt -- the system prompt stays cacheable per-language.
        """
        forbidden = ["unique_marker_xyz"]
        system, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
            forbidden_values=forbidden,
        )
        assert "unique_marker_xyz" in user
        assert "unique_marker_xyz" not in system

    def test_forbidden_values_dedupe(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        """Duplicates in the input list shouldn't appear duplicated in
        the rendered prompt -- saves tokens and reads cleanly.
        """
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
            forbidden_values=["mismo", "mismo", "definir", "mismo"],
        )
        assert user.count("mismo") == 1

    def test_forbidden_values_truncation_cap(
        self, builder: PromptBuilder, sample_identifiers: list[dict[str, Any]]
    ) -> None:
        """Pathologically large forbidden lists must be capped to keep
        prompt size bounded. Cap matches the glossary-table convention.
        """
        from legesher_i18n.prompt_builder import PromptBuilder as _PB

        cap = _PB._MAX_FORBIDDEN_VALUES
        oversized = [f"unique_value_{i}" for i in range(cap + 50)]
        _, user = builder.build_identifier_prompt(
            identifiers=sample_identifiers,
            target_lang="es",
            existing_glossary={},
            forbidden_values=oversized,
        )
        # First entries appear; beyond-cap entries do not.
        assert "unique_value_0" in user
        assert f"unique_value_{cap - 1}" in user
        assert f"unique_value_{cap}" not in user
        assert f"unique_value_{cap + 49}" not in user


class TestForbiddenValuesFromRealPack:
    """End-to-end: caller computes flat list from a real pack."""

    def test_es_pack_self_value_appears_in_prompt(self, builder: PromptBuilder) -> None:
        from legesher_i18n.pack_loader import LanguagePackLoader

        loader = LanguagePackLoader()
        es_pack = loader.load("es", target="python", version="3.10")
        # Sanity: confirm the actual shipped value (corrected from
        # description's `propio` placeholder).
        assert es_pack.get_reserved_word_translation("self") == "mismo"

        forbidden = (
            list(es_pack.keywords.values())
            + list(es_pack.builtins.values())
            + list(es_pack.exceptions.values())
            + list(es_pack.reserved_words.values())
        )
        assert "mismo" in forbidden

        system, user = builder.build_identifier_prompt(
            identifiers=[{"text": "e", "role": "variable", "context": {}}],
            target_lang="es",
            existing_glossary={},
            forbidden_values=forbidden,
        )
        combined = system + user
        assert "mismo" in combined, (
            "Reserved-word value 'mismo' missing from prompt — "
            "forbidden-values plumbing not wired correctly"
        )

    def test_ur_pack_self_value_appears_in_prompt(self, builder: PromptBuilder) -> None:
        from legesher_i18n.pack_loader import LanguagePackLoader

        loader = LanguagePackLoader()
        ur_pack = loader.load("ur", target="python", version="3.10")
        assert ur_pack.get_reserved_word_translation("self") == "خود"

        forbidden = list(ur_pack.reserved_words.values())
        _, user = builder.build_identifier_prompt(
            identifiers=[{"text": "e", "role": "variable", "context": {}}],
            target_lang="ur",
            existing_glossary={},
            forbidden_values=forbidden,
        )
        assert "خود" in user
