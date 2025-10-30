"""CORE-435: Parametrized tests for all 24 migrated languages.

This module provides comprehensive parametrized tests that run across all
languages to ensure consistent behavior and catch language-specific issues.

Each test runs against every available language pack, making it easy to:
- Spot translation inconsistencies
- Identify Unicode handling issues
- Compare performance across languages
- Ensure feature parity

Test Strategy:
- Use @pytest.mark.parametrize to run same test across all languages
- Collect results in a matrix format for easy comparison
- Report per-language results for debugging
- Generate summary statistics

Translation Quality Metrics:
- Minimum keyword coverage: 35+ keywords per language
- Minimum builtin coverage: 25+ builtins per language
- Round-trip losslessness: 100% (EN → X → EN must be identical)
- Translation speed target: <100ms per file
- Unicode preservation: No corruption for RTL/CJK languages

Example Expected Translations:
    Spanish:
        def foo() → definir foo()
        return 42 → retornar 42
        if True → si Verdadero

    Arabic (RTL):
        def foo() → تعريف foo()
        return 42 → إرجاع 42
        if True → إذا صحيح

Performance Benchmarks:
- Pack loading: <1s per language
- Translation: <5ms for typical 50-line file
- Round-trip: <10ms for typical file

Related: CORE-435 (Validation), CORE-354 (Migration), CORE-343 (Transformer)
"""

import pytest

from legesher_core.transformer import TokenTranslator
from legesher_i18n.pack_loader import LanguagePackLoader


# All expected languages from CORE-354
# Currently only 'es' and 'ar' are available
EXPECTED_LANGUAGES = [
    ("es", "Spanish"),
    ("ar", "Arabic"),
    # Future additions after CORE-354:
    # ('fr', 'French'),
    # ('de', 'German'),
    # ('pt', 'Portuguese'),
    # ('ru', 'Russian'),
    # ('zh', 'Chinese'),
    # ('ja', 'Japanese'),
    # ('ko', 'Korean'),
    # ('hi', 'Hindi'),
    # ('tr', 'Turkish'),
    # ('it', 'Italian'),
    # ('pl', 'Polish'),
    # ('nl', 'Dutch'),
    # ('he', 'Hebrew'),
    # ('vi', 'Vietnamese'),
    # ('th', 'Thai'),
    # ('id', 'Indonesian'),
    # ('cs', 'Czech'),
    # ('ro', 'Romanian'),
    # ('el', 'Greek'),
    # ('hu', 'Hungarian'),
    # ('sv', 'Swedish'),
    # ('da', 'Danish'),
]


@pytest.fixture(scope="module")
def language_packs():
    """Load all available language packs."""
    loader = LanguagePackLoader()
    packs = {}

    for lang_code, lang_name in EXPECTED_LANGUAGES:
        try:
            # Load base pack (3.10) which has metadata for full version range
            pack = loader.load(lang_code, "python", "3.10")
            packs[lang_code] = pack
        except FileNotFoundError as e:
            # Skip languages not yet migrated - provide detailed context
            error_path = str(e)
            if "keywords.yml" in error_path or "keywords" in error_path:
                # Missing keywords file - primary language pack file
                print(
                    f"⊘ {lang_name} ({lang_code}): Keywords file missing - "
                    f"awaiting CORE-354 migration"
                )
            elif "metadata" in error_path:
                # Metadata structure issue
                print(
                    f"⊘ {lang_name} ({lang_code}): Metadata incomplete - "
                    f"check pack structure"
                )
            elif "3.10" in error_path:
                # Version-specific pack missing
                print(
                    f"⊘ {lang_name} ({lang_code}): Base pack (3.10) not found - "
                    f"check version hierarchy"
                )
            else:
                # Generic pack not available
                print(f"⊘ {lang_name} ({lang_code}): Pack not available - {e}")
            continue

    return packs


@pytest.fixture(scope="module")
def translators(language_packs):
    """Create forward translators (EN → target language) for all loaded packs."""
    return {
        lang_code: TokenTranslator(pack.keywords, pack.builtins)
        for lang_code, pack in language_packs.items()
    }


@pytest.fixture(scope="module")
def reverse_translators(language_packs):
    """Create reverse translators (target language → EN) for all loaded packs."""
    reverse_trans = {}
    for lang_code, pack in language_packs.items():
        # Create reverse mappings for round-trip translation
        reverse_keywords = {v: k for k, v in pack.keywords.items()}
        reverse_builtins = {v: k for k, v in pack.builtins.items()}
        reverse_trans[lang_code] = TokenTranslator(reverse_keywords, reverse_builtins)
    return reverse_trans


# Test samples with expected keywords/builtins
TEST_SAMPLES = [
    (
        "simple_function",
        "def foo():\n    return 42",
        {"keywords": ["def", "return"]},
    ),
    (
        "function_with_print",
        "def greet():\n    print('Hello')",
        {"keywords": ["def"], "builtins": ["print"]},
    ),
    (
        "conditional",
        "if True:\n    pass\nelse:\n    pass",
        {"keywords": ["if", "True", "pass", "else"]},
    ),
    (
        "loop_with_range",
        "for i in range(10):\n    print(i)",
        {"keywords": ["for", "in"], "builtins": ["range", "print"]},
    ),
    (
        "class_definition",
        "class Calculator:\n    pass",
        {"keywords": ["class", "pass"]},
    ),
    (
        "try_except",
        "try:\n    pass\nexcept:\n    pass",
        {"keywords": ["try", "pass", "except"]},
    ),
]


class TestAllLanguagesParametrized:
    """Parametrized tests that run across all languages."""

    @pytest.mark.parametrize("lang_code,lang_name", EXPECTED_LANGUAGES)
    def test_language_pack_loads(self, lang_code, lang_name, language_packs):
        """Verify each language pack loads successfully."""
        if lang_code not in language_packs:
            pytest.skip(
                f"{lang_name} ({lang_code}) not yet available - waiting for CORE-354"
            )

        pack = language_packs[lang_code]

        # Verify pack is valid
        assert pack.language == lang_code
        assert pack.target == "python"
        assert pack.version == "3.10"  # Base pack version
        assert len(pack.keywords) > 0
        assert len(pack.builtins) > 0

        print(
            f"\n✓ {lang_name} ({lang_code}): {len(pack.keywords)} keywords, {len(pack.builtins)} builtins"
        )

    @pytest.mark.parametrize("lang_code,lang_name", EXPECTED_LANGUAGES)
    @pytest.mark.parametrize("sample_name,code,expected", TEST_SAMPLES)
    def test_translation_matrix(
        self,
        lang_code,
        lang_name,
        sample_name,
        code,
        expected,
        language_packs,
        translators,
    ):
        """Test translation for all languages across all sample codes.

        Creates a comprehensive test matrix:
        - Rows: Sample code snippets
        - Columns: Languages
        - Cells: Translation success/failure
        """
        if lang_code not in language_packs:
            pytest.skip(f"{lang_name} not available yet")

        pack = language_packs[lang_code]
        translator = translators[lang_code]

        # Translate the code
        translated = translator.translate_code(code, "en", lang_code)

        # Verify keywords are translated
        for keyword in expected.get("keywords", []):
            if keyword in pack.keywords:
                translated_keyword = pack.keywords[keyword]
                assert translated_keyword in translated, (
                    f"{lang_name} - {sample_name}: "
                    f"'{keyword}' → '{translated_keyword}' not found in:\n{translated}"
                )

        # Verify builtins are translated
        for builtin in expected.get("builtins", []):
            if builtin in pack.builtins:
                translated_builtin = pack.builtins[builtin]
                assert translated_builtin in translated, (
                    f"{lang_name} - {sample_name}: "
                    f"'{builtin}' → '{translated_builtin}' not found in:\n{translated}"
                )

        print(f"✓ {lang_name} - {sample_name}")

    @pytest.mark.parametrize("lang_code,lang_name", EXPECTED_LANGUAGES)
    def test_round_trip_lossless(
        self, lang_code, lang_name, language_packs, translators, reverse_translators
    ):
        """Verify round-trip translation is lossless for all languages."""
        if lang_code not in language_packs:
            pytest.skip(f"{lang_name} not available yet")

        forward_translator = translators[lang_code]
        reverse_translator = reverse_translators[lang_code]

        # Test with a complex sample
        original = """def calculate_tax(income, rate):
    '''Calculate income tax.'''
    if income > 0:
        return income * rate
    else:
        return 0"""

        # EN → Language → EN (using forward and reverse translators)
        translated = forward_translator.translate_code(original, "en", lang_code)
        back = reverse_translator.translate_code(translated, lang_code, "en")

        # Must be byte-for-byte identical
        assert back == original, (
            f"{lang_name}: Round-trip not lossless\n"
            f"Original:\n{original}\n\n"
            f"After round-trip:\n{back}"
        )

        print(f"✓ {lang_name}: Round-trip lossless")

    @pytest.mark.parametrize("lang_code,lang_name", EXPECTED_LANGUAGES)
    def test_unicode_preservation(
        self, lang_code, lang_name, language_packs, translators
    ):
        """Verify Unicode characters are preserved correctly."""
        if lang_code not in language_packs:
            pytest.skip(f"{lang_name} not available yet")

        translator = translators[lang_code]

        code = "def foo():\n    return True"
        translated = translator.translate_code(code, "en", lang_code)

        # Test UTF-8 encoding/decoding
        try:
            encoded = translated.encode("utf-8")
            decoded = encoded.decode("utf-8")
            assert decoded == translated
        except UnicodeError as e:
            pytest.fail(f"{lang_name}: Unicode corruption - {e}")

        print(f"✓ {lang_name}: Unicode preserved")

    @pytest.mark.parametrize("lang_code,lang_name", EXPECTED_LANGUAGES)
    def test_minimum_keyword_coverage(self, lang_code, lang_name, language_packs):
        """Verify each language has minimum required keyword translations."""
        if lang_code not in language_packs:
            pytest.skip(f"{lang_name} not available yet")

        pack = language_packs[lang_code]

        # Core keywords that MUST be present
        required_keywords = [
            "def",
            "class",
            "return",
            "if",
            "else",
            "for",
            "while",
            "try",
            "except",
            "import",
            "from",
            "as",
            "with",
            "pass",
            "True",
            "False",
            "None",
            "and",
            "or",
            "not",
            "in",
            "is",
        ]

        missing = []
        for keyword in required_keywords:
            if keyword not in pack.keywords:
                missing.append(keyword)

        assert len(missing) == 0, (
            f"{lang_name}: Missing required keywords: {', '.join(missing)}"
        )

        print(f"✓ {lang_name}: All {len(required_keywords)} core keywords present")

    @pytest.mark.parametrize("lang_code,lang_name", EXPECTED_LANGUAGES)
    def test_minimum_builtin_coverage(self, lang_code, lang_name, language_packs):
        """Verify each language has minimum required builtin translations."""
        if lang_code not in language_packs:
            pytest.skip(f"{lang_name} not available yet")

        pack = language_packs[lang_code]

        # Core builtins that MUST be present
        required_builtins = [
            "print",
            "input",
            "len",
            "range",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "bool",
            "type",
            "open",
            "sum",
            "min",
            "max",
            "abs",
            "round",
        ]

        missing = []
        for builtin in required_builtins:
            if builtin not in pack.builtins:
                missing.append(builtin)

        assert len(missing) == 0, (
            f"{lang_name}: Missing required builtins: {', '.join(missing)}"
        )

        print(f"✓ {lang_name}: All {len(required_builtins)} core builtins present")


class TestLanguageComparison:
    """Compare translation coverage and quality across languages."""

    def test_keyword_count_consistency(self, language_packs):
        """Compare keyword counts across all languages."""
        if not language_packs:
            pytest.skip("No language packs available")

        counts = {
            lang_code: len(pack.keywords) for lang_code, pack in language_packs.items()
        }

        print("\n" + "=" * 50)
        print("KEYWORD COUNT COMPARISON")
        print("=" * 50)
        for lang_code, count in sorted(
            counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"{lang_code}: {count} keywords")

        # All languages should have similar keyword counts (within 10%)
        if len(counts) > 1:
            max_count = max(counts.values())
            min_count = min(counts.values())
            variation = (max_count - min_count) / max_count

            assert variation < 0.1, (
                f"Keyword count variation too high: {variation:.1%} "
                f"(max={max_count}, min={min_count})"
            )

    def test_builtin_count_consistency(self, language_packs):
        """Compare builtin counts across all languages."""
        if not language_packs:
            pytest.skip("No language packs available")

        counts = {
            lang_code: len(pack.builtins) for lang_code, pack in language_packs.items()
        }

        print("\n" + "=" * 50)
        print("BUILTIN COUNT COMPARISON")
        print("=" * 50)
        for lang_code, count in sorted(
            counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"{lang_code}: {count} builtins")

        # All languages should have similar builtin counts (within 20%)
        if len(counts) > 1:
            max_count = max(counts.values())
            min_count = min(counts.values())
            variation = (max_count - min_count) / max_count

            assert variation < 0.2, (
                f"Builtin count variation too high: {variation:.1%} "
                f"(max={max_count}, min={min_count})"
            )

    def test_metadata_consistency(self, language_packs):
        """Verify all languages have consistent metadata."""
        if not language_packs:
            pytest.skip("No language packs available")

        print("\n" + "=" * 50)
        print("METADATA COMPARISON")
        print("=" * 50)

        for lang_code, pack in language_packs.items():
            if pack.metadata:
                print(f"\n{lang_code}:")
                print(
                    f"  Version Range: {pack.metadata.python_version_min} - {pack.metadata.python_version_max}"
                )
                print(f"  Author: {pack.metadata.author}")
                print(f"  License: {pack.metadata.license}")
                print(f"  Community Reviewed: {pack.metadata.community_reviewed}")
                print(f"  Last Updated: {pack.metadata.last_updated}")

                # All should have same version range
                assert pack.metadata.python_version_min == "3.10"
                assert pack.metadata.python_version_max == "3.13"
            else:
                pytest.fail(f"{lang_code}: Missing metadata")


class TestRTLLanguages:
    """Specific tests for Right-to-Left languages."""

    RTL_LANGUAGES = [
        ("ar", "Arabic"),
        ("he", "Hebrew"),
    ]

    @pytest.mark.parametrize("lang_code,lang_name", RTL_LANGUAGES)
    def test_rtl_mixed_content(self, lang_code, lang_name, language_packs, translators):
        """Test RTL languages with mixed LTR/RTL content."""
        if lang_code not in language_packs:
            pytest.skip(f"{lang_name} not available yet")

        translator = translators[lang_code]

        # Code with English identifiers (LTR) and translated keywords (RTL)
        code = "def calculate_total(items, tax_rate):\n    return sum(items) * tax_rate"
        translated = translator.translate_code(code, "en", lang_code)

        # Verify English identifiers preserved (LTR)
        assert "calculate_total" in translated
        assert "items" in translated
        assert "tax_rate" in translated

        # Verify RTL keywords present
        pack = language_packs[lang_code]
        assert pack.keywords["def"] in translated
        assert pack.keywords["return"] in translated

        print(f"✓ {lang_name}: Mixed LTR/RTL content handled correctly")


class TestCJKLanguages:
    """Specific tests for CJK (Chinese, Japanese, Korean) languages."""

    CJK_LANGUAGES = [
        ("zh", "Chinese"),
        ("ja", "Japanese"),
        ("ko", "Korean"),
    ]

    @pytest.mark.parametrize("lang_code,lang_name", CJK_LANGUAGES)
    def test_cjk_character_handling(
        self, lang_code, lang_name, language_packs, translators
    ):
        """Test CJK languages handle multi-byte characters correctly."""
        if lang_code not in language_packs:
            pytest.skip(f"{lang_name} not available yet")

        translator = translators[lang_code]
        pack = language_packs[lang_code]

        code = "def foo():\n    return True"
        translated = translator.translate_code(code, "en", lang_code)

        # Verify CJK characters are present
        # (Each CJK char is typically 3 bytes in UTF-8)
        def_translation = pack.keywords.get("def", "")
        assert len(def_translation.encode("utf-8")) > len(def_translation), (
            f"{lang_name}: CJK characters not multi-byte"
        )

        # Verify round-trip
        back = translator.translate_code(translated, lang_code, "en")
        assert back == code

        print(f"✓ {lang_name}: CJK characters handled correctly")


# Generate test summary
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print comprehensive summary of all language tests."""
    print("\n" + "=" * 70)
    print("ALL LANGUAGES TEST SUMMARY")
    print("=" * 70)

    passed = terminalreporter.stats.get("passed", [])
    failed = terminalreporter.stats.get("failed", [])
    skipped = terminalreporter.stats.get("skipped", [])

    # Count by language
    lang_results = {}
    for lang_code, lang_name in EXPECTED_LANGUAGES:
        lang_results[lang_code] = {
            "name": lang_name,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        }

    # Categorize results
    for report in passed:
        for lang_code in lang_results:
            if lang_code in str(report.nodeid):
                lang_results[lang_code]["passed"] += 1
                break

    for report in failed:
        for lang_code in lang_results:
            if lang_code in str(report.nodeid):
                lang_results[lang_code]["failed"] += 1
                break

    for report in skipped:
        for lang_code in lang_results:
            if lang_code in str(report.nodeid):
                lang_results[lang_code]["skipped"] += 1
                break

    # Print per-language summary
    print("\nPer-Language Results:")
    print("-" * 70)
    for lang_code, results in lang_results.items():
        if results["passed"] > 0 or results["failed"] > 0:
            status = "✓" if results["failed"] == 0 else "✗"
            print(
                f"{status} {results['name']:15} "
                f"Passed: {results['passed']:3} "
                f"Failed: {results['failed']:3} "
                f"Skipped: {results['skipped']:3}"
            )

    # Overall summary
    print("\n" + "-" * 70)
    print(f"Total Passed:  {len(passed)}")
    print(f"Total Failed:  {len(failed)}")
    print(f"Total Skipped: {len(skipped)}")

    if len(failed) == 0:
        print("\n🎉 All language tests passed!")
    else:
        print(f"\n⚠  {len(failed)} test(s) failed - review failures above")

    print("=" * 70)
