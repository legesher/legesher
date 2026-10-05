"""Identifier quality validation suite (CORE-710).

Tests that translated implicit_params and identifiers in language packs meet
the four AC categories from CORE-710:

1. **Identifier validation** — valid Python identifiers, no whitespace, no
   chain-of-thought reasoning markers, length sanity for short variables.
2. **Script/character validation** — no Arabic comma `،`, Arabic semicolon
   `؛`, RTL question mark `؟`, no CJK fullwidth punctuation.
3. **Structural validation** — `__main__` never translated, module names
   from imports never translated, round-trip preserves structure.
4. **Consistency validation** — same identifier maps to same value within
   a file, no duplicate values within a pack section.

Tests parametrize over all 51 supported languages from
``legesher_i18n.language_registry.get_available_language_codes()``. The
LLM-driven round-trip tests (``TestRoundTripPreservesSelfCls``) are
gated by ``@pytest.mark.slow`` and run synthetically (constructed
translators with fixed maps) so they don't require an external API.
"""

from __future__ import annotations

import sys

import pytest

from legesher_core.transformer import TokenTranslator
from legesher_core.tree_sitter.translator import TreeSitterTranslator
from legesher_i18n.language_registry import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader

# All 51 supported language codes from languages.json. Uses the "active"
# accessor (available + experimental) since all current packs are
# experimental status until community validation lands them as available.
ALL_LANGS = sorted(get_active_language_codes())

# The tier this interpreter is served, as the CLI and the import hook pick it.
# A fixed "3.13" made the 3.10 leg load the ja and si files whose renderings
# are identifiers only under Unicode 15.1, and left the 3.10 compat forms,
# the ones 3.10 users get, unchecked (CORE-2334).
RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

# Subset of priority languages used for round-trip integration tests
# (matches the AYA-213 Cycle-4 pilot subset + a Latin-script anchor)
ROUND_TRIP_LANGS = ("es", "zh", "ur")

# Characters that must never appear in code positions (identifiers or values)
# because they're language-specific punctuation that would break Python.
FORBIDDEN_PUNCTUATION = {
    # Arabic-script punctuation
    "،": "Arabic comma",
    "؛": "Arabic semicolon",
    "؟": "Arabic question mark",
    "۔": "Urdu full stop",
    # CJK fullwidth punctuation (must use ASCII in code)
    "，": "fullwidth comma",
    "。": "ideographic full stop",
    "、": "ideographic comma",
    "；": "fullwidth semicolon",
    "：": "fullwidth colon",
    "！": "fullwidth exclamation",
    "？": "fullwidth question mark",
    "（": "fullwidth left parenthesis",
    "）": "fullwidth right parenthesis",
}

# Markers indicating chain-of-thought leakage (model output pollution)
TRACE_MARKERS = (
    "Explanation_",
    "translation_",
    "_translated_",
    "<reasoning>",
    "</reasoning>",
)


@pytest.fixture(scope="module")
def loader() -> LanguagePackLoader:
    """Module-scoped pack loader so tests don't re-discover packs per case."""
    return LanguagePackLoader()


# ---------------------------------------------------------------------------
# Category 1: Identifier validation
# ---------------------------------------------------------------------------


class TestReservedWordIdentifierValidity:
    """Per-language identifier-validity invariants for self/cls."""

    @pytest.mark.parametrize("lang", ALL_LANGS)
    @pytest.mark.parametrize("term", ["self", "cls"])
    def test_translation_is_valid_python_identifier(
        self, loader: LanguagePackLoader, lang: str, term: str
    ) -> None:
        """value.isidentifier() must hold (Unicode-aware per PEP 3131)."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        value = pack.get_implicit_param_translation(term)
        if value is None:
            pytest.skip(f"{lang}: no {term} translation in pack (yet)")
        assert value.isidentifier(), (
            f"{lang}: {term} -> {value!r} is not a valid Python identifier"
        )

    @pytest.mark.parametrize("lang", ALL_LANGS)
    @pytest.mark.parametrize("term", ["self", "cls"])
    def test_translation_is_single_word(
        self, loader: LanguagePackLoader, lang: str, term: str
    ) -> None:
        """No whitespace anywhere — must be exactly one token."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        value = pack.get_implicit_param_translation(term)
        if value is None:
            pytest.skip(f"{lang}: no {term} translation in pack (yet)")
        assert len(value.split()) == 1, (
            f"{lang}: {term} -> {value!r} contains whitespace"
        )

    @pytest.mark.parametrize("lang", ALL_LANGS)
    @pytest.mark.parametrize("term", ["self", "cls"])
    def test_translation_has_no_trace_markers(
        self, loader: LanguagePackLoader, lang: str, term: str
    ) -> None:
        """No chain-of-thought / reasoning leakage in the value."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        value = pack.get_implicit_param_translation(term)
        if value is None:
            pytest.skip(f"{lang}: no {term} translation in pack (yet)")
        for marker in TRACE_MARKERS:
            assert marker not in value, (
                f"{lang}: {term} -> {value!r} contains trace marker {marker!r}"
            )

    @pytest.mark.parametrize("lang", ALL_LANGS)
    @pytest.mark.parametrize("term", ["self", "cls"])
    def test_translation_length_sanity(
        self, loader: LanguagePackLoader, lang: str, term: str
    ) -> None:
        """Reserved-word translations should be reasonably short (<25 chars).

        self and cls are 4 and 3 chars in English. A translation longer
        than 25 characters likely indicates a multi-word phrase that
        slipped past the single-word check or trace-marker pollution.
        """
        pack = loader.load(lang, "python", RUNNING_VERSION)
        value = pack.get_implicit_param_translation(term)
        if value is None:
            pytest.skip(f"{lang}: no {term} translation in pack (yet)")
        assert len(value) < 25, (
            f"{lang}: {term} -> {value!r} is suspiciously long ({len(value)} chars)"
        )


# ---------------------------------------------------------------------------
# Category 2: Script / character validation
# ---------------------------------------------------------------------------


class TestForbiddenPunctuation:
    """No language-specific punctuation in code-position values across packs."""

    @pytest.mark.parametrize("lang", ALL_LANGS)
    def test_no_forbidden_punctuation_in_implicit_params(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """Reserved-word translations must use only Unicode letters/digits/underscore."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        for term, value in pack.implicit_params.items():
            for char, char_name in FORBIDDEN_PUNCTUATION.items():
                assert char not in value, (
                    f"{lang}: {term} -> {value!r} contains forbidden "
                    f"{char_name} ({char!r})"
                )

    @pytest.mark.parametrize("lang", ALL_LANGS)
    def test_no_forbidden_punctuation_in_keywords(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """Sanity: also check existing keyword translations for the same issue."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        for keyword, value in pack.keywords.items():
            for char, char_name in FORBIDDEN_PUNCTUATION.items():
                assert char not in value, (
                    f"{lang}: keyword {keyword} -> {value!r} contains "
                    f"forbidden {char_name} ({char!r})"
                )


# ---------------------------------------------------------------------------
# Category 3: Structural validation
# ---------------------------------------------------------------------------


class TestStructuralInvariants:
    """Translation preserves code structure."""

    @pytest.mark.parametrize("lang", ROUND_TRIP_LANGS)
    def test_dunder_main_never_translated(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """`__main__` must survive translation untouched (dunder pattern)."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        translator = TokenTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            implicit_param_map=pack.implicit_params,
        )
        code = 'if __name__ == "__main__":\n    pass\n'
        translated = translator.translate_code(code, "en", lang)
        assert "__main__" in translated, (
            f"{lang}: __main__ was translated to something else: {translated!r}"
        )

    @pytest.mark.parametrize("lang", ROUND_TRIP_LANGS)
    def test_function_class_count_preserved(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """Translation must preserve the number of `def`/`class` declarations."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        translator = TokenTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            implicit_param_map=pack.implicit_params,
        )
        code = (
            "class Foo:\n"
            "    def __init__(self): pass\n"
            "    def bar(self): pass\n"
            "\n"
            "class Baz:\n"
            "    def qux(self): pass\n"
        )
        translated = translator.translate_code(code, "en", lang)
        # Same number of def/class declarations should appear (translated)
        def_translated = pack.get_keyword_translation("def") or "def"
        class_translated = pack.get_keyword_translation("class") or "class"
        assert translated.count(def_translated) == 3, (
            f"{lang}: expected 3 def occurrences, got {translated.count(def_translated)}"
        )
        assert translated.count(class_translated) == 2, (
            f"{lang}: expected 2 class occurrences, got {translated.count(class_translated)}"
        )


# ---------------------------------------------------------------------------
# Category 4: Consistency validation
# ---------------------------------------------------------------------------


class TestConsistencyInvariants:
    """Same identifier always maps to same value; no pack-level duplicates."""

    @pytest.mark.parametrize("lang", ALL_LANGS)
    def test_no_duplicate_values_within_implicit_params(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """`self` and `cls` must map to DIFFERENT values within a pack."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        if not pack.implicit_params:
            pytest.skip(f"{lang}: no implicit_params section yet")
        values = list(pack.implicit_params.values())
        assert len(values) == len(set(values)), (
            f"{lang}: duplicate values in implicit_params: {pack.implicit_params}"
        )

    @pytest.mark.parametrize("lang", ALL_LANGS)
    def test_implicit_param_does_not_collide_with_keyword(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """A reserved-word translation must not match any keyword translation.

        This is the AYA-213 Cycle-4 failure-mode safeguard: if `self`
        translates to the same value as keyword `in` (or any keyword),
        round-trip translation breaks because the reverse mapper can't
        tell which English term to map back to.
        """
        pack = loader.load(lang, "python", RUNNING_VERSION)
        if not pack.implicit_params:
            pytest.skip(f"{lang}: no implicit_params section yet")
        keyword_values = set(pack.keywords.values())
        for term, rw_value in pack.implicit_params.items():
            assert rw_value not in keyword_values or rw_value == term, (
                f"{lang}: implicit_param {term} -> {rw_value!r} collides "
                f"with a keyword translation"
            )

    @pytest.mark.parametrize("lang", ALL_LANGS)
    def test_implicit_param_does_not_collide_with_builtin_or_exception(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """Same check, broadened to builtins + exceptions."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        if not pack.implicit_params:
            pytest.skip(f"{lang}: no implicit_params section yet")
        forbidden = set(pack.builtins.values()) | set(pack.exceptions.values())
        for term, rw_value in pack.implicit_params.items():
            assert rw_value not in forbidden, (
                f"{lang}: implicit_param {term} -> {rw_value!r} collides "
                f"with a builtin or exception translation"
            )


# ---------------------------------------------------------------------------
# Urdu collision regression — the original AYA-213 Cycle-4 failure mode
# ---------------------------------------------------------------------------


class TestUrduCollisionRegression:
    """Pin the specific failure mode from the AYA-213 Cycle-4 pilot.

    Pre-CORE-710: LLM translated self → میں which matches the Urdu
    keyword translation of `in`. Round-trip then mapped `میں` back to
    `in`, producing `def __init__(in, ...)` which is a SyntaxError.
    """

    def test_urdu_self_is_not_in(self, loader: LanguagePackLoader) -> None:
        pack = loader.load("ur", "python", RUNNING_VERSION)
        self_val = pack.get_implicit_param_translation("self")
        assert self_val is not None, "Urdu pack missing self translation"
        in_val = pack.get_keyword_translation("in")
        assert self_val != in_val, (
            f"Cycle-4 failure mode regressed: self={self_val!r}, in={in_val!r}"
        )
        assert self_val != "میں", (
            "self specifically must not be 'میں' (collides with `in`)"
        )

    def test_urdu_self_is_reflexive_pronoun(self, loader: LanguagePackLoader) -> None:
        """Urdu self should be a reflexive pronoun like خود (oneself).

        Not requiring the literal string خود — just confirming that the
        translation is non-trivial and doesn't fall back to a first-person
        or demonstrative pronoun. This is a soft quality check that
        accepts خود, خودی, آپ, نمونہ, or similar reflexive choices.
        """
        pack = loader.load("ur", "python", RUNNING_VERSION)
        self_val = pack.get_implicit_param_translation("self")
        assert self_val is not None
        # Negative checks — known wrong patterns
        forbidden = {"میں", "آنے", "اب", "یہاں"}  # in, this, now, here
        assert self_val not in forbidden, (
            f"Urdu self -> {self_val!r} is a known-wrong choice; should be reflexive"
        )


# ---------------------------------------------------------------------------
# Round-trip integration tests (synthetic, no external API needed)
# ---------------------------------------------------------------------------


class TestRoundTripPreservesSelfCls:
    """Round-trip translation preserves self/cls consistency.

    These tests use the actual TokenTranslator + TreeSitterTranslator with
    pack data — no LLM calls needed because the substitution is purely
    table-driven via implicit_param_map. The @slow marker is a hint for
    CI prioritization, not because they're actually slow.
    """

    @pytest.mark.parametrize("lang", ROUND_TRIP_LANGS)
    @pytest.mark.parametrize("translator_cls", [TokenTranslator, TreeSitterTranslator])
    def test_self_consistent_in_signature_and_body(
        self,
        loader: LanguagePackLoader,
        lang: str,
        translator_cls: type,
    ) -> None:
        """`def foo(self): self.x = x` → all three `self` substitute to same value."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        translator = translator_cls(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            implicit_param_map=pack.implicit_params,
        )
        code = "def foo(self, x):\n    self.x = x\n    return self\n"
        translated = translator.translate_code(code, "en", lang)
        self_val = pack.get_implicit_param_translation("self")
        assert self_val is not None, f"{lang}: missing self translation"
        # All three `self` references should render to the same value
        assert translated.count(self_val) == 3, (
            f"{lang}/{translator_cls.__name__}: expected 3 occurrences of "
            f"{self_val!r}, got {translated.count(self_val)}. Output: {translated!r}"
        )

    @pytest.mark.parametrize("lang", ROUND_TRIP_LANGS)
    @pytest.mark.parametrize("translator_cls", [TokenTranslator, TreeSitterTranslator])
    def test_cls_consistent_in_classmethod(
        self,
        loader: LanguagePackLoader,
        lang: str,
        translator_cls: type,
    ) -> None:
        """`def make(cls): return cls()` → both `cls` references match."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        translator = translator_cls(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            implicit_param_map=pack.implicit_params,
        )
        code = "def make(cls):\n    return cls()\n"
        translated = translator.translate_code(code, "en", lang)
        cls_val = pack.get_implicit_param_translation("cls")
        assert cls_val is not None, f"{lang}: missing cls translation"
        assert translated.count(cls_val) == 2, (
            f"{lang}/{translator_cls.__name__}: expected 2 occurrences of "
            f"{cls_val!r}, got {translated.count(cls_val)}. Output: {translated!r}"
        )

    @pytest.mark.parametrize("lang", ROUND_TRIP_LANGS)
    def test_round_trip_preserves_self(
        self, loader: LanguagePackLoader, lang: str
    ) -> None:
        """en → target → en restores `self` via `reverse()` mapper."""
        pack = loader.load(lang, "python", RUNNING_VERSION)
        en_to_target = TokenTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            implicit_param_map=pack.implicit_params,
        )
        target_to_en = en_to_target.reverse()

        original = "def foo(self, x):\n    return self.x\n"
        translated = en_to_target.translate_code(original, "en", lang)
        round_tripped = target_to_en.translate_code(translated, lang, "en")

        assert "self" in round_tripped, (
            f"{lang}: round-trip lost self. Translated: {translated!r}, "
            f"Round-tripped: {round_tripped!r}"
        )

    def test_urdu_round_trip_does_not_produce_syntax_error_on_in(
        self, loader: LanguagePackLoader
    ) -> None:
        """The original Cycle-4 failure mode: `def __init__(میں, ...)` would
        round-trip to `def __init__(in, ...)` which is a SyntaxError.

        With CORE-710, self translates to خود (not میں), so the round-trip
        is correct.
        """
        pack = loader.load("ur", "python", RUNNING_VERSION)
        en_to_ur = TokenTranslator(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            implicit_param_map=pack.implicit_params,
        )
        ur_to_en = en_to_ur.reverse()

        original = "def __init__(self, x):\n    self.x = x\n"
        urdu = en_to_ur.translate_code(original, "en", "ur")
        back_to_en = ur_to_en.translate_code(urdu, "ur", "en")

        # Critical: round-tripped Urdu must NOT contain `def __init__(in, ...)`
        # which would be a SyntaxError.
        assert "(in" not in back_to_en, (
            f"Cycle-4 failure mode regressed: round-trip produced "
            f"`(in` in {back_to_en!r}"
        )
        assert "self" in back_to_en, (
            f"Round-trip lost `self` in Urdu pipeline: {back_to_en!r}"
        )
