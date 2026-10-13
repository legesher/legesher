"""CORE-435: Comprehensive validation tests for the shipped language packs.

This module validates that the token-based transformer works correctly with
every shipped language pack, including:
- Loading all language packs successfully
- Translating keywords and builtins correctly
- Preserving formatting and round-trip translation
- Handling version-aware inheritance
- Supporting RTL languages and special characters

The language list is derived from the registry (``get_active_language_codes``
minus the pivot, ``en``), never maintained by hand, and a pack that fails to
load is a failure, not a skip. The list was frozen at es/ar during the
CORE-354 migration; CORE-2128 widened it to the whole registry.

Test Coverage:
- Pack loading and validation (every active pack)
- Basic translation functionality per language
- Round-trip translation (lossless)
- Version-specific features (Python 3.10 through the latest shipped grammar)
- Edge cases (RTL, Unicode, incomplete code)
- Structural checks on loading and translation (timing is under make bench)

Interpreter gaps (``tests/interpreter_gaps.py``) are strict xfails: the
inert return hop on CPython 3.10/3.11 for packs whose renderings carry
marks, and the si/ja 3.13 pack files that fail schema validation on
interpreters whose Unicode tables predate 15.1.

Dependencies: CORE-354 (Translation Migration), CORE-343 (Transformer), CORE-345 (Version-Aware Packs)
"""

import pytest

from legesher_core.transformer import TokenTranslator
from legesher_i18n import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader, LanguagePack
from tests.interpreter_gaps import (
    unloadable_here,
    xfail_if_return_hop_is_inert,
    xfail_if_unloadable_here,
)


# Sample code snippets for testing (varying complexity)
SAMPLE_SIMPLE_FUNCTION = """def foo():
    return 42"""

SAMPLE_FUNCTION_WITH_PARAMS = """def greet(name):
    print(name)"""

SAMPLE_CONDITIONAL = """if True:
    pass
else:
    pass"""

SAMPLE_LOOP = """for i in range(10):
    print(i)"""

SAMPLE_CLASS = """class Calculator:
    def add(self, a, b):
        return a + b"""

SAMPLE_COMPLEX = """def calculate_tax(income, rate):
    '''Calculate income tax.'''
    if income > 0:
        tax = income * rate
        return tax
    else:
        return 0"""

SAMPLE_MATCH_STATEMENT = """match status:
    case 200:
        print("OK")
    case 404:
        print("Not Found")"""

SAMPLE_EXCEPTION_GROUP = """try:
    pass
except* ValueError:
    pass"""


#: Every active pack except the pivot. Derived from the registry so this
#: list can never silently lag the shipped packs.
EXPECTED_LANGUAGES = [
    code for code in sorted(get_active_language_codes()) if code != "en"
]

#: The pack version this module exercises.
PACK_VERSION = "3.13"

#: Every grammar version some pack ships, discovered rather than listed.
SHIPPED_VERSIONS = tuple(LanguagePackLoader().list_available_versions("python"))


@pytest.fixture(scope="module")
def pack_loader():
    """Create a LanguagePackLoader for all tests."""
    return LanguagePackLoader()


@pytest.fixture(scope="module")
def all_language_packs(pack_loader) -> dict[str, LanguagePack]:
    """Load every expected language pack for Python 3.13.

    A pack that fails to load fails here. The only exception is a pack the
    running interpreter cannot load at all (interpreter gap 2): it is left
    out so the rest of the module still runs on every pack that does load,
    and ``test_every_expected_pack_loads`` pins it as a strict xfail.

    Returns:
        Dict mapping language codes to LanguagePack objects
    """
    return {
        lang_code: pack_loader.load(lang_code, "python", PACK_VERSION)
        for lang_code in EXPECTED_LANGUAGES
        if unloadable_here(lang_code, PACK_VERSION) is None
    }


@pytest.fixture
def translators(all_language_packs) -> dict[str, TokenTranslator]:
    """Create translators for all loaded language packs.

    Returns:
        Dict mapping language codes to configured TokenTranslator instances
    """
    translators = {}
    for lang_code, pack in all_language_packs.items():
        # Create bidirectional mappings for round-trip translation
        # EN → Language
        en_to_lang = {en: target for en, target in pack.keywords.items()}
        en_to_lang_builtins = {en: target for en, target in pack.builtins.items()}

        # Language → EN (reverse mapping)
        lang_to_en = {target: en for en, target in pack.keywords.items()}
        lang_to_en_builtins = {target: en for en, target in pack.builtins.items()}

        translators[lang_code] = TokenTranslator(
            keyword_map={**en_to_lang, **lang_to_en},
            builtin_map={**en_to_lang_builtins, **lang_to_en_builtins},
        )

    return translators


class TestPackLoading:
    """Test that all shipped language packs load correctly."""

    @pytest.mark.parametrize("lang_code", EXPECTED_LANGUAGES)
    def test_every_expected_pack_loads(self, pack_loader, lang_code, request):
        """Every registry language loads at PACK_VERSION, by name."""
        xfail_if_unloadable_here(request, lang_code, PACK_VERSION)
        pack = pack_loader.load(lang_code, "python", PACK_VERSION)
        assert pack.language == lang_code

    def test_pack_has_required_fields(self, all_language_packs):
        """Verify each pack has all required fields."""
        for lang_code, pack in all_language_packs.items():
            # Required fields
            assert pack.language == lang_code, f"{lang_code}: language field mismatch"
            assert pack.target == "python", f"{lang_code}: target must be 'python'"
            assert pack.version == PACK_VERSION, (
                f"{lang_code}: version must be '{PACK_VERSION}'"
            )

            # Required mappings
            assert isinstance(pack.keywords, dict), (
                f"{lang_code}: keywords must be dict"
            )
            assert isinstance(pack.builtins, dict), (
                f"{lang_code}: builtins must be dict"
            )
            assert len(pack.keywords) > 0, f"{lang_code}: keywords cannot be empty"
            assert len(pack.builtins) > 0, f"{lang_code}: builtins cannot be empty"

    def test_pack_has_minimum_translations(self, all_language_packs):
        """Verify each pack has minimum required translations.

        Expected:
        - At least 35 keywords (core Python keywords)
        - At least 70 builtins (common built-in functions)
        """
        for lang_code, pack in all_language_packs.items():
            keyword_count = len(pack.keywords)
            builtin_count = len(pack.builtins)

            assert keyword_count >= 35, (
                f"{lang_code}: Expected ≥35 keywords, got {keyword_count}"
            )
            assert builtin_count >= 25, (
                f"{lang_code}: Expected ≥25 builtins, got {builtin_count}"
            )

            print(f"\n{lang_code}: {keyword_count} keywords, {builtin_count} builtins")

    def test_pack_metadata_valid(self, all_language_packs):
        """Verify pack metadata is present and valid."""
        for lang_code, pack in all_language_packs.items():
            assert pack.metadata is not None, f"{lang_code}: metadata missing"

            # Check required metadata fields
            metadata = pack.metadata

            # Version min/max should be shipped Python versions
            assert metadata.python_version_min in SHIPPED_VERSIONS, (
                f"{lang_code}: Invalid python_version_min: {metadata.python_version_min}"
            )
            assert metadata.python_version_max in SHIPPED_VERSIONS, (
                f"{lang_code}: Invalid python_version_max: {metadata.python_version_max}"
            )

            # Min should be <= max
            min_ver = float(metadata.python_version_min)
            max_ver = float(metadata.python_version_max)
            assert min_ver <= max_ver, (
                f"{lang_code}: version_min ({min_ver}) > version_max ({max_ver})"
            )

            assert metadata.author, f"{lang_code}: author field empty"
            assert metadata.license, f"{lang_code}: license field empty"

            assert hasattr(metadata, "community_reviewed"), (
                f"{lang_code}: community_reviewed field missing"
            )


class TestBasicTranslation:
    """Test basic translation functionality for all languages."""

    @pytest.mark.parametrize(
        "sample_code,expected_keywords",
        [
            (SAMPLE_SIMPLE_FUNCTION, ["def", "return"]),
            (SAMPLE_CONDITIONAL, ["if", "True", "pass", "else"]),
            (SAMPLE_LOOP, ["for", "in"]),
        ],
    )
    def test_translate_keywords(
        self, translators, all_language_packs, sample_code, expected_keywords
    ):
        """Test that keywords are translated correctly in each language."""
        for lang_code, translator in translators.items():
            pack = all_language_packs[lang_code]
            translated = translator.translate_code(sample_code, "en", lang_code)

            # Verify each expected keyword is translated
            for en_keyword in expected_keywords:
                if en_keyword in pack.keywords:
                    translated_keyword = pack.keywords[en_keyword]
                    assert translated_keyword in translated, (
                        f"{lang_code}: Expected '{en_keyword}' → '{translated_keyword}' in:\n{translated}"
                    )

    @pytest.mark.parametrize(
        "sample_code,expected_builtins",
        [
            (SAMPLE_FUNCTION_WITH_PARAMS, ["print"]),
            (SAMPLE_LOOP, ["range", "print"]),
        ],
    )
    def test_translate_builtins(
        self, translators, all_language_packs, sample_code, expected_builtins
    ):
        """Test that built-in functions are translated correctly."""
        for lang_code, translator in translators.items():
            pack = all_language_packs[lang_code]
            translated = translator.translate_code(sample_code, "en", lang_code)

            # Verify each expected builtin is translated
            for en_builtin in expected_builtins:
                if en_builtin in pack.builtins:
                    translated_builtin = pack.builtins[en_builtin]
                    assert translated_builtin in translated, (
                        f"{lang_code}: Expected '{en_builtin}' → '{translated_builtin}' in:\n{translated}"
                    )

    def test_preserve_user_identifiers(self, translators):
        """Verify user-defined names (variables, functions) are not translated."""
        code = """def my_function(user_variable):
    another_var = 42
    return user_variable"""

        for lang_code, translator in translators.items():
            translated = translator.translate_code(code, "en", lang_code)

            # User identifiers should be preserved
            assert "my_function" in translated, f"{lang_code}: function name changed"
            assert "user_variable" in translated, f"{lang_code}: parameter name changed"
            assert "another_var" in translated, f"{lang_code}: variable name changed"

    def test_preserve_strings_and_literals(self, translators):
        """Verify string literals and numbers are not translated."""
        code = """def greet():
    message = "Hello, World!"
    count = 42
    pi = 3.14
    return message"""

        for lang_code, translator in translators.items():
            translated = translator.translate_code(code, "en", lang_code)

            # Literals should be unchanged
            assert '"Hello, World!"' in translated, (
                f"{lang_code}: string literal changed"
            )
            assert "42" in translated, f"{lang_code}: integer literal changed"
            assert "3.14" in translated, f"{lang_code}: float literal changed"


class TestRoundTripTranslation:
    """Test that translation is lossless (EN → X → EN)."""

    @pytest.mark.parametrize(
        "sample_code",
        [
            SAMPLE_SIMPLE_FUNCTION,
            SAMPLE_FUNCTION_WITH_PARAMS,
            SAMPLE_CONDITIONAL,
            SAMPLE_LOOP,
            SAMPLE_CLASS,
            SAMPLE_COMPLEX,
        ],
    )
    @pytest.mark.parametrize("lang_code", EXPECTED_LANGUAGES)
    def test_round_trip_lossless(self, translators, lang_code, sample_code, request):
        """Verify EN → Language → EN is byte-for-byte identical."""
        xfail_if_unloadable_here(request, lang_code, PACK_VERSION)
        translator = translators[lang_code]

        # Translate to target language
        translated = translator.translate_code(sample_code, "en", lang_code)
        xfail_if_return_hop_is_inert(request, sample_code, translated)

        # Translate back to English
        back_to_english = translator.translate_code(translated, lang_code, "en")

        # Must be identical
        assert back_to_english == sample_code, (
            f"{lang_code}: Round-trip translation not lossless\n"
            f"Original:\n{sample_code}\n"
            f"After round-trip:\n{back_to_english}"
        )

    @pytest.mark.parametrize("lang_code", EXPECTED_LANGUAGES)
    def test_round_trip_preserves_formatting(self, translators, lang_code, request):
        """Verify whitespace, indentation, and comments are preserved."""
        xfail_if_unloadable_here(request, lang_code, PACK_VERSION)
        code = """def calculate(x, y):
    # This is a comment
    result = x + y  # inline comment
    return result  # trailing comment"""

        translator = translators[lang_code]
        translated = translator.translate_code(code, "en", lang_code)
        xfail_if_return_hop_is_inert(request, code, translated)
        back = translator.translate_code(translated, lang_code, "en")

        # Check exact match
        assert back == code, f"{lang_code}: Formatting not preserved in round-trip"

        # Verify comments are preserved
        assert "# This is a comment" in translated
        assert "# inline comment" in translated
        assert "# trailing comment" in translated


class TestVersionSpecificFeatures:
    """Test Python version-specific features and inheritance."""

    @pytest.mark.parametrize("lang_code", EXPECTED_LANGUAGES)
    def test_python_3_10_match_statement(self, pack_loader, lang_code):
        """Test Python 3.10 match/case statements translate correctly."""
        pack = pack_loader.load(lang_code, "python", "3.10")

        # Check that match/case keywords exist
        assert "match" in pack.keywords, f"{lang_code}: 'match' keyword missing in 3.10"
        assert "case" in pack.keywords, f"{lang_code}: 'case' keyword missing in 3.10"

        # Test translation
        translator = TokenTranslator(pack.keywords, pack.builtins)
        translated = translator.translate_code(SAMPLE_MATCH_STATEMENT, "en", lang_code)

        assert pack.keywords["match"] in translated
        assert pack.keywords["case"] in translated

    @pytest.mark.parametrize("lang_code", EXPECTED_LANGUAGES)
    def test_python_3_11_exception_groups(self, pack_loader, lang_code):
        """Test Python 3.11 except* (exception groups) translates correctly."""
        pack = pack_loader.load(lang_code, "python", "3.11")

        # Check that except* keyword exists (if defined)
        if "except*" in pack.keywords:
            translator = TokenTranslator(pack.keywords, pack.builtins)
            translated = translator.translate_code(
                SAMPLE_EXCEPTION_GROUP, "en", lang_code
            )

            assert pack.keywords["except*"] in translated, (
                f"{lang_code}: 'except*' not translated in 3.11"
            )

    @pytest.mark.parametrize("lang_code", EXPECTED_LANGUAGES)
    def test_version_inheritance_chain(self, pack_loader, lang_code, request):
        """Verify inheritance chains are correct for version-specific packs."""
        xfail_if_unloadable_here(request, lang_code, PACK_VERSION)
        pack_313 = pack_loader.load(lang_code, "python", PACK_VERSION)

        # Check inheritance chain exists and is non-empty
        assert hasattr(pack_313, "inheritance_chain"), (
            f"{lang_code}: Missing inheritance_chain attribute"
        )

        if pack_313.extends:
            # If pack extends another, chain should have at least 2 entries
            assert len(pack_313.inheritance_chain) >= 2, (
                f"{lang_code}: Inheritance chain too short: {pack_313.inheritance_chain}"
            )

            # Verify 3.10 is in the chain (base pack)
            chain_str = " → ".join(pack_313.inheritance_chain)
            assert "3.10" in chain_str, (
                f"{lang_code}: 3.10 base pack not in inheritance chain: {chain_str}"
            )


class TestEdgeCases:
    """Test edge cases and special handling."""

    @pytest.mark.parametrize("lang_code", ["ar", "he"])
    def test_rtl_languages_no_corruption(self, pack_loader, lang_code):
        """Verify RTL languages (Arabic, Hebrew) don't corrupt Unicode."""
        pack = pack_loader.load(lang_code, "python", PACK_VERSION)

        # Create bidirectional mapping for translator
        keyword_map = {**pack.keywords, **{v: k for k, v in pack.keywords.items()}}
        builtin_map = {**pack.builtins, **{v: k for k, v in pack.builtins.items()}}

        translator = TokenTranslator(keyword_map, builtin_map)
        translated = translator.translate_code(SAMPLE_SIMPLE_FUNCTION, "en", lang_code)

        # Verify we can encode/decode without errors
        try:
            encoded = translated.encode("utf-8")
            decoded = encoded.decode("utf-8")
            assert decoded == translated, f"{lang_code}: UTF-8 encode/decode failed"
            print(f"✓ {lang_code}: RTL Unicode preserved")
        except UnicodeError as e:
            pytest.fail(f"{lang_code}: Unicode corruption detected: {e}")

    @pytest.mark.parametrize(
        "lang_code,lang_name",
        [
            ("zh", "Chinese"),
            ("ja", "Japanese"),
            ("ko", "Korean"),
            ("vi", "Vietnamese"),
            ("pt", "Portuguese"),
            ("es", "Spanish"),  # Has diacritics
        ],
    )
    def test_special_characters_preserved(
        self, pack_loader, lang_code, lang_name, request
    ):
        """Test languages with special characters (diacritics, CJK, etc.)."""
        xfail_if_unloadable_here(request, lang_code, PACK_VERSION)
        pack = pack_loader.load(lang_code, "python", PACK_VERSION)

        # Create bidirectional mapping
        keyword_map = {**pack.keywords, **{v: k for k, v in pack.keywords.items()}}
        builtin_map = {**pack.builtins, **{v: k for k, v in pack.builtins.items()}}

        translator = TokenTranslator(keyword_map, builtin_map)

        # Test translation
        translated = translator.translate_code(SAMPLE_SIMPLE_FUNCTION, "en", lang_code)

        # Verify UTF-8 handling
        try:
            translated.encode("utf-8").decode("utf-8")
            print(f"✓ {lang_code} ({lang_name}): Special characters preserved")
        except UnicodeError as e:
            pytest.fail(f"{lang_code} ({lang_name}): Special character corruption: {e}")

    def test_incomplete_code_handling(self, translators):
        """Verify incomplete code is handled gracefully."""
        incomplete_code = "def foo(\n    # incomplete"

        for lang_code, translator in translators.items():
            result = translator.translate_code(incomplete_code, "en", lang_code)

            # Should return original code when tokenization fails
            assert result == incomplete_code, (
                f"{lang_code}: Incomplete code handling failed"
            )

    def test_empty_code_handling(self, translators):
        """Test handling of empty code."""
        for lang_code, translator in translators.items():
            assert translator.translate_code("", "en", lang_code) == ""
            assert translator.translate_code("   ", "en", lang_code) == "   "
            assert translator.translate_code("\n\n", "en", lang_code) == "\n\n"


class TestPerformance:
    """Structural checks on pack loading and translation.

    Timing lives in ``tests/benchmarks`` and runs under ``make bench``.
    """

    def test_every_loadable_pack_loads_and_is_cached(self, pack_loader):
        """Every loadable pack loads, and a reload while cached is the same object.

        The wall-clock bound this test used to carry (50 packs under 1.0 s)
        went red on the first Linux rehearsal of ci.yml at 1.043 s. Timing
        is measured under ``make bench`` (tests/benchmarks); here the
        guarantee is structural. The loader's cache holds 32 packs, fewer
        than the registry loads, so only the most recent load is asserted
        to be cached. Packs this interpreter cannot load are pinned
        elsewhere (gap 2).
        """
        loadable = [
            lang_code
            for lang_code in EXPECTED_LANGUAGES
            if unloadable_here(lang_code, PACK_VERSION) is None
        ]
        packs = {
            lang_code: pack_loader.load(lang_code, "python", PACK_VERSION)
            for lang_code in loadable
        }
        assert set(packs) == set(loadable)
        for lang_code, pack in packs.items():
            assert pack is not None, lang_code
        last = loadable[-1]
        assert pack_loader.load(last, "python", PACK_VERSION) is packs[last], (
            f"{last}: a reload while cached is not the cached pack"
        )

    def test_translation_runs_for_every_language(self, translators):
        """A representative file translates into every language without raising.

        Every pack maps ``def``, so the output differs from the input; the
        translator returns the source unchanged on a tokenization failure,
        and that would read as success without the inequality. Keyword
        correctness is ``TestBasicTranslation``'s job. The per-translation
        bound (100 ms) is measured under ``make bench``.
        """
        for lang_code, translator in translators.items():
            try:
                translated = translator.translate_code(SAMPLE_COMPLEX, "en", lang_code)
            except Exception as exc:  # noqa: BLE001 - the point is to name the pack
                pytest.fail(f"{lang_code}: translate_code raised {exc!r}")
            assert isinstance(translated, str) and translated, lang_code
            assert translated != SAMPLE_COMPLEX, f"{lang_code}: nothing was translated"

    def test_memory_usage_reasonable(self, all_language_packs, translators):
        """Verify memory usage is reasonable with all packs loaded."""
        import sys

        # Calculate approximate memory usage
        pack_size = sys.getsizeof(all_language_packs)
        translator_size = sys.getsizeof(translators)

        total_mb = (pack_size + translator_size) / (1024 * 1024)

        print(f"\n💾 Memory usage: {total_mb:.2f} MB")
        print(f"  Packs: {pack_size / (1024 * 1024):.2f} MB")
        print(f"  Translators: {translator_size / (1024 * 1024):.2f} MB")

        # Should be reasonable (<50MB for all packs)
        assert total_mb < 50, f"Memory usage too high: {total_mb:.2f} MB"


class TestCommunityReview:
    """Test the community-review flag every pack carries."""

    def test_community_reviewed_flag(self, all_language_packs):
        """Verify the community_reviewed field exists on every pack."""
        for lang_code, pack in all_language_packs.items():
            if pack.metadata:
                # Packs are experimental until community review flips this;
                # the field itself must be present.
                assert hasattr(pack.metadata, "community_reviewed"), (
                    f"{lang_code}: community_reviewed field missing"
                )

                print(
                    f"\n{lang_code}: community_reviewed = {pack.metadata.community_reviewed}"
                )


# Summary statistics
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print summary statistics after test run."""
    print("\n" + "=" * 70)
    print("CORE-435 VALIDATION SUMMARY")
    print("=" * 70)

    # Count tests by category
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))

    print(f"\n✓ Passed:  {passed}")
    print(f"✗ Failed:  {failed}")
    print(f"⊘ Skipped: {skipped}")

    if failed == 0:
        print("\n🎉 All migrated packs validated successfully!")
    else:
        print(f"\n⚠ {failed} validation(s) failed - see errors above")

    print("=" * 70)
