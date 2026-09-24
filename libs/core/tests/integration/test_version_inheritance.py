"""CORE-435: Tests for version-aware language pack inheritance.

This module specifically tests the version inheritance system to ensure:
- Every shipped version-specific pack (3.10 through the latest) loads
- Inheritance chains resolve properly (3.10 → 3.11 → … → latest)
- Version-specific keywords are available in correct versions
- Child packs properly inherit and override parent translations

The language list is derived from the registry (``get_active_language_codes``
minus the pivot, ``en``) and the version list from what the packs ship,
neither maintained by hand. A pack that fails to load is a failure, not a
skip. The list was frozen at es/ar during the CORE-354 migration; CORE-2128
widened it to the whole registry.

Python Version Features:
- 3.10: match/case (PEP 634 - Structural Pattern Matching)
- 3.11: except* (PEP 654 - Exception Groups)
- 3.12: type parameter syntax (PEP 695)
- 3.13+: Latest additions

Interpreter gap (``tests/interpreter_gaps.py``): the si and ja 3.13/3.14
pack files need Unicode 15.1 identifier rules and cannot load on CPython
before 3.13; those cases are strict xfails there.

Related: CORE-435 (Validation), CORE-345 (Version-Aware Packs), CORE-354 (Migration)
"""

import re

import pytest

from legesher_i18n import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_core.transformer import TokenTranslator
from tests.interpreter_gaps import xfail_if_unloadable_here


#: Every active pack except the pivot.
LANGUAGES = [code for code in sorted(get_active_language_codes()) if code != "en"]

#: Every grammar version some pack ships, ascending.
PYTHON_VERSIONS = tuple(LanguagePackLoader().list_available_versions("python"))
BASE_VERSION = PYTHON_VERSIONS[0]
CHILD_VERSIONS = PYTHON_VERSIONS[1:]
LATEST_VERSION = PYTHON_VERSIONS[-1]

_VERSION_IN_PATH = re.compile(r"(\d+\.\d+)\.yml$")


def _versions_in(chain: list[str]) -> list[str]:
    """The ``X.Y`` each chain entry's file name carries, in chain order."""
    found = []
    for path in chain:
        match = _VERSION_IN_PATH.search(path)
        assert match, f"chain entry without a version in its name: {path}"
        found.append(match.group(1))
    return found


def _sort_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


@pytest.fixture(scope="module")
def pack_loader():
    """Create a pack loader for all tests."""
    return LanguagePackLoader()


class TestVersionLoading:
    """Test loading version-specific packs."""

    def test_version_discovery_is_not_vacuous(self):
        assert BASE_VERSION == "3.10"
        assert {"3.11", "3.12", "3.13", "3.14"} <= set(CHILD_VERSIONS)
        assert len(LANGUAGES) >= 50

    @pytest.mark.parametrize("version", PYTHON_VERSIONS)
    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_load_version_specific_pack(self, pack_loader, lang_code, version, request):
        """Verify each version-specific pack can be loaded."""
        xfail_if_unloadable_here(request, lang_code, version)
        pack = pack_loader.load(lang_code, "python", version)

        assert pack.language == lang_code
        assert pack.target == "python"
        assert pack.version == version
        assert len(pack.keywords) > 0
        assert len(pack.builtins) > 0

        print(
            f"✓ {lang_code} - Python {version}: {len(pack.keywords)} keywords, {len(pack.builtins)} builtins"
        )

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_base_pack_has_no_extends(self, pack_loader, lang_code):
        """Verify base packs don't extend anything."""
        pack = pack_loader.load(lang_code, "python", BASE_VERSION)

        # Base pack should not extend anything
        assert pack.extends is None, (
            f"{lang_code} {BASE_VERSION}: Base pack should not extend anything, "
            f"but extends: {pack.extends}"
        )

        print(f"✓ {lang_code} {BASE_VERSION}: Base pack (no extends)")

    @pytest.mark.parametrize("version", CHILD_VERSIONS)
    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_child_packs_extend_parent(self, pack_loader, lang_code, version, request):
        """Verify non-base packs (3.11+) extend their parent version."""
        xfail_if_unloadable_here(request, lang_code, version)
        pack = pack_loader.load(lang_code, "python", version)

        # Child pack must extend something
        assert pack.extends is not None, (
            f"{lang_code} {version}: Should extend parent pack, but extends is None"
        )

        # Verify extends points to parent version
        assert "yml" in pack.extends.lower(), (
            f"{lang_code} {version}: extends should be a .yml file path"
        )

        print(f"✓ {lang_code} {version}: Extends {pack.extends}")


class TestInheritanceChains:
    """Test that inheritance chains are built correctly."""

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_chain_present(self, pack_loader, lang_code, request):
        """Verify the latest packs have a complete inheritance chain."""
        xfail_if_unloadable_here(request, lang_code, LATEST_VERSION)
        pack = pack_loader.load(lang_code, "python", LATEST_VERSION)

        # Should have inheritance_chain attribute
        assert hasattr(pack, "inheritance_chain"), (
            f"{lang_code}: Missing inheritance_chain attribute"
        )

        # Chain should be a list
        assert isinstance(pack.inheritance_chain, list), (
            f"{lang_code}: inheritance_chain should be a list"
        )

        # Should have at least the base pack in chain
        assert len(pack.inheritance_chain) > 0, (
            f"{lang_code}: inheritance_chain is empty"
        )

        print(f"\n{lang_code} inheritance chain:")
        for i, pack_path in enumerate(pack.inheritance_chain):
            print(f"  {i + 1}. {pack_path}")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_chain_order(self, pack_loader, lang_code, request):
        """Verify inheritance chain goes from base (3.10) to the latest version."""
        xfail_if_unloadable_here(request, lang_code, LATEST_VERSION)
        pack = pack_loader.load(lang_code, "python", LATEST_VERSION)

        versions = _versions_in(pack.inheritance_chain)

        # Every shipped version, base first, latest last, ascending.
        assert versions == list(PYTHON_VERSIONS), (
            f"{lang_code}: Inheritance chain is {versions}, expected {list(PYTHON_VERSIONS)}"
        )
        assert versions == sorted(versions, key=_sort_key)

        print(f"✓ {lang_code}: Chain in correct order: {' → '.join(versions)}")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_merges_keywords(self, pack_loader, lang_code, request):
        """Verify child packs inherit all parent keywords."""
        xfail_if_unloadable_here(request, lang_code, LATEST_VERSION)
        pack_base = pack_loader.load(lang_code, "python", BASE_VERSION)
        pack_latest = pack_loader.load(lang_code, "python", LATEST_VERSION)

        # The latest pack should have all keywords from the base
        for keyword in pack_base.keywords:
            assert keyword in pack_latest.keywords, (
                f"{lang_code}: Keyword '{keyword}' from {BASE_VERSION} not "
                f"inherited in {LATEST_VERSION}"
            )

        # The latest pack should have same or more keywords than the base
        assert len(pack_latest.keywords) >= len(pack_base.keywords), (
            f"{lang_code}: {LATEST_VERSION} has fewer keywords than {BASE_VERSION} "
            f"({len(pack_latest.keywords)} vs {len(pack_base.keywords)})"
        )

        print(
            f"✓ {lang_code}: {LATEST_VERSION} inherits all {len(pack_base.keywords)} "
            f"keywords from {BASE_VERSION}"
        )

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_merges_builtins(self, pack_loader, lang_code, request):
        """Verify child packs inherit all parent builtins."""
        xfail_if_unloadable_here(request, lang_code, LATEST_VERSION)
        pack_base = pack_loader.load(lang_code, "python", BASE_VERSION)
        pack_latest = pack_loader.load(lang_code, "python", LATEST_VERSION)

        # The latest pack should have all builtins from the base
        for builtin in pack_base.builtins:
            assert builtin in pack_latest.builtins, (
                f"{lang_code}: Builtin '{builtin}' from {BASE_VERSION} not "
                f"inherited in {LATEST_VERSION}"
            )

        # The latest pack should have same or more builtins than the base
        assert len(pack_latest.builtins) >= len(pack_base.builtins), (
            f"{lang_code}: {LATEST_VERSION} has fewer builtins than {BASE_VERSION} "
            f"({len(pack_latest.builtins)} vs {len(pack_base.builtins)})"
        )

        print(
            f"✓ {lang_code}: {LATEST_VERSION} inherits all {len(pack_base.builtins)} "
            f"builtins from {BASE_VERSION}"
        )


class TestVersionSpecificFeatures:
    """Test version-specific Python features are translated correctly."""

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_python_3_10_match_case(self, pack_loader, lang_code):
        """Test Python 3.10+ match/case structural pattern matching."""
        test_code = """match status:
    case 200:
        print("OK")
    case 404:
        print("Not Found")
    case _:
        print("Other")"""

        pack = pack_loader.load(lang_code, "python", "3.10")

        # Verify match/case keywords exist
        assert "match" in pack.keywords, f"{lang_code} 3.10: Missing 'match' keyword"
        assert "case" in pack.keywords, f"{lang_code} 3.10: Missing 'case' keyword"

        # Test translation
        translator = TokenTranslator(pack.keywords, pack.builtins)
        translated = translator.translate_code(test_code, "en", lang_code)

        # Verify translations are present
        assert pack.keywords["match"] in translated, (
            f"{lang_code}: 'match' not translated in:\n{translated}"
        )
        assert pack.keywords["case"] in translated, (
            f"{lang_code}: 'case' not translated in:\n{translated}"
        )

        print(f"✓ {lang_code} 3.10: match/case working")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_python_3_11_exception_groups(self, pack_loader, lang_code):
        """Test Python 3.11+ except* exception groups.

        ``except*`` is the keyword 3.11 adds (version-index.yml), so every
        3.11 pack must carry it; the old "optional" branch let a pack that
        dropped it pass.
        """
        test_code = """try:
    raise ExceptionGroup("errors", [ValueError(), TypeError()])
except* ValueError as e:
    print("ValueError")
except* TypeError as e:
    print("TypeError")"""

        pack = pack_loader.load(lang_code, "python", "3.11")

        assert "except*" in pack.keywords, f"{lang_code} 3.11: Missing 'except*'"

        translator = TokenTranslator(pack.keywords, pack.builtins)
        translated = translator.translate_code(test_code, "en", lang_code)

        assert pack.keywords["except*"] in translated, (
            f"{lang_code}: 'except*' not translated"
        )

        print(f"✓ {lang_code} 3.11: except* working")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_version_features_not_in_earlier_versions(self, pack_loader, lang_code):
        """Verify version-specific features aren't in earlier versions.

        Validates that:
        - Python 3.10+ features (match/case) are not in base 3.9 packs
        - Python 3.11+ features (except*) don't leak into 3.10 packs
        - Each version only adds features appropriate to that Python version
        """
        version_specific_features = {
            "3.10": ["match", "case"],  # PEP 634: Structural Pattern Matching
            "3.11": ["except*"],  # PEP 654: Exception Groups
        }

        # Load the base pack (3.10)
        pack_310 = pack_loader.load(lang_code, "python", "3.10")

        # Check that 3.10 features are present
        for feature in version_specific_features["3.10"]:
            assert feature in pack_310.keywords, (
                f"{lang_code} 3.10: Missing expected feature '{feature}'"
            )

        # ...and that 3.11 features have not leaked into 3.10
        for feature in version_specific_features["3.11"]:
            assert feature not in pack_310.keywords, (
                f"{lang_code} 3.10: 3.11 feature '{feature}' leaked into the base pack"
            )

        # Child packs (3.11+) inherit the base features and add their own
        pack_311 = pack_loader.load(lang_code, "python", "3.11")
        for feature in version_specific_features["3.10"]:
            assert feature in pack_311.keywords, (
                f"{lang_code} 3.11: Should inherit 3.10 feature '{feature}'"
            )
        for feature in version_specific_features["3.11"]:
            assert feature in pack_311.keywords, (
                f"{lang_code} 3.11: Missing expected feature '{feature}'"
            )

        print(
            f"✓ {lang_code}: Version-specific features correctly scoped "
            f"(3.10: {', '.join(version_specific_features['3.10'])}; "
            f"3.11: {', '.join(version_specific_features['3.11'])})"
        )


class TestVersionCompatibility:
    """Test that packs work across Python version ranges."""

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_metadata_version_ranges(self, pack_loader, lang_code, request):
        """Verify metadata specifies correct Python version ranges."""
        xfail_if_unloadable_here(request, lang_code, LATEST_VERSION)
        pack = pack_loader.load(lang_code, "python", LATEST_VERSION)

        assert pack.metadata, f"{lang_code}: Missing metadata"

        # Should specify minimum and maximum versions
        assert pack.metadata.python_version_min, (
            f"{lang_code}: Missing python_version_min"
        )
        assert pack.metadata.python_version_max, (
            f"{lang_code}: Missing python_version_max"
        )

        # Min should be <= max
        min_ver = _sort_key(pack.metadata.python_version_min)
        max_ver = _sort_key(pack.metadata.python_version_max)

        assert min_ver <= max_ver, (
            f"{lang_code}: version_min ({min_ver}) > version_max ({max_ver})"
        )

        print(
            f"✓ {lang_code}: Version range {pack.metadata.python_version_min} - {pack.metadata.python_version_max}"
        )

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_compatibility_tested_versions(self, pack_loader, lang_code, request):
        """Verify pack metadata lists tested Python versions."""
        xfail_if_unloadable_here(request, lang_code, LATEST_VERSION)
        pack = pack_loader.load(lang_code, "python", LATEST_VERSION)

        assert pack.metadata, f"{lang_code}: Missing metadata"
        tested = pack.metadata.compatibility_tested

        # Should be a list
        assert isinstance(tested, list), (
            f"{lang_code}: compatibility_tested should be a list"
        )

        # Should have at least one version
        assert len(tested) > 0, f"{lang_code}: compatibility_tested is empty"

        # All entries should be shipped version strings
        for version in tested:
            assert version in PYTHON_VERSIONS, (
                f"{lang_code}: Invalid version in compatibility_tested: {version}"
            )

        print(
            f"✓ {lang_code}: Tested on {len(tested)} Python versions: {', '.join(tested)}"
        )


class TestCircularInheritance:
    """Test protection against circular inheritance."""

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_no_circular_references(self, pack_loader, lang_code, request):
        """Verify pack loader prevents circular inheritance."""
        # This is more of a pack loader test, but important for validation
        # The pack loader should detect and prevent circular inheritance chains
        xfail_if_unloadable_here(request, lang_code, LATEST_VERSION)

        try:
            # If this loads successfully, no circular reference exists
            pack = pack_loader.load(lang_code, "python", LATEST_VERSION)
        except RecursionError:
            pytest.fail(f"{lang_code}: Circular inheritance detected!")

        # Check inheritance chain doesn't have duplicates
        chain = pack.inheritance_chain
        unique_chain = list(set(chain))

        assert len(chain) == len(unique_chain), (
            f"{lang_code}: Duplicate packs in inheritance chain: {chain}"
        )

        print(f"✓ {lang_code}: No circular inheritance detected")


# Generate test summary
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print summary of version inheritance tests."""
    print("\n" + "=" * 70)
    print("VERSION INHERITANCE TEST SUMMARY")
    print("=" * 70)

    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))

    print(f"\n✓ Passed:  {passed}")
    print(f"✗ Failed:  {failed}")
    print(f"⊘ Skipped: {skipped}")

    if failed == 0:
        print("\n🎉 All version inheritance tests passed!")
        print(f"✓ Base packs ({BASE_VERSION}) validated")
        print(
            f"✓ Child packs ({'-'.join((CHILD_VERSIONS[0], LATEST_VERSION))}) inherit correctly"
        )
        print("✓ Inheritance chains resolve properly")
        print("✓ Version-specific features working")
    else:
        print(f"\n⚠  {failed} test(s) failed")

    print("=" * 70)
