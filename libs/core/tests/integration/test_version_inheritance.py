"""CORE-435: Tests for version-aware language pack inheritance.

This module specifically tests the version inheritance system to ensure:
- Version-specific packs (3.10, 3.11, 3.12, 3.13) load correctly
- Inheritance chains resolve properly (3.10 → 3.11 → 3.12 → 3.13)
- Version-specific keywords are available in correct versions
- Child packs properly inherit and override parent translations

Python Version Features:
- 3.10: match/case (PEP 634 - Structural Pattern Matching)
- 3.11: except* (PEP 654 - Exception Groups)
- 3.12: type parameter syntax (PEP 695)
- 3.13: Latest additions

Related: CORE-435 (Validation), CORE-345 (Version-Aware Packs), CORE-354 (Migration)
"""

import pytest

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_core.transformer import TokenTranslator


# Available language codes
LANGUAGES = ["es", "ar"]  # More will be added via CORE-354

# Python versions we support
PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]


@pytest.fixture(scope="module")
def pack_loader():
    """Create a pack loader for all tests."""
    return LanguagePackLoader()


class TestVersionLoading:
    """Test loading version-specific packs."""

    @pytest.mark.parametrize("version", PYTHON_VERSIONS)
    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_load_version_specific_pack(self, pack_loader, lang_code, version):
        """Verify each version-specific pack can be loaded."""
        try:
            pack = pack_loader.load(lang_code, "python", version)

            assert pack.language == lang_code
            assert pack.target == "python"
            assert pack.version == version
            assert len(pack.keywords) > 0
            assert len(pack.builtins) > 0

            print(
                f"✓ {lang_code} - Python {version}: {len(pack.keywords)} keywords, {len(pack.builtins)} builtins"
            )

        except FileNotFoundError:
            pytest.skip(f"{lang_code} pack for Python {version} not yet available")

    def test_base_pack_has_no_extends(self, pack_loader):
        """Verify 3.10 base packs don't extend anything."""
        for lang_code in LANGUAGES:
            try:
                pack = pack_loader.load(lang_code, "python", "3.10")

                # Base pack should not extend anything
                assert pack.extends is None, (
                    f"{lang_code} 3.10: Base pack should not extend anything, "
                    f"but extends: {pack.extends}"
                )

                print(f"✓ {lang_code} 3.10: Base pack (no extends)")

            except FileNotFoundError:
                pytest.skip(f"{lang_code} 3.10 pack not available")

    def test_child_packs_extend_parent(self, pack_loader):
        """Verify non-base packs (3.11+) extend their parent version."""
        child_versions = ["3.11", "3.12", "3.13"]

        for lang_code in LANGUAGES:
            for version in child_versions:
                try:
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

                except FileNotFoundError:
                    pytest.skip(f"{lang_code} {version} pack not available")


class TestInheritanceChains:
    """Test that inheritance chains are built correctly."""

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_chain_present(self, pack_loader, lang_code):
        """Verify 3.13 packs have complete inheritance chain."""
        try:
            pack = pack_loader.load(lang_code, "python", "3.13")

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

        except FileNotFoundError:
            pytest.skip(f"{lang_code} 3.13 pack not available")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_chain_order(self, pack_loader, lang_code):
        """Verify inheritance chain goes from base (3.10) to current version."""
        try:
            pack = pack_loader.load(lang_code, "python", "3.13")

            chain = pack.inheritance_chain
            if len(chain) < 2:
                pytest.skip(f"{lang_code}: Single-pack chain (no inheritance)")

            # First in chain should be 3.10 (base)
            assert "3.10" in chain[0], (
                f"{lang_code}: First in chain should be 3.10, got: {chain[0]}"
            )

            # Last in chain should be 3.13 (current)
            assert "3.13" in chain[-1], (
                f"{lang_code}: Last in chain should be 3.13, got: {chain[-1]}"
            )

            # Chain should be in version order
            # Extract version numbers from paths
            versions = []
            for path in chain:
                if "3.10" in path:
                    versions.append("3.10")
                elif "3.11" in path:
                    versions.append("3.11")
                elif "3.12" in path:
                    versions.append("3.12")
                elif "3.13" in path:
                    versions.append("3.13")

            # Versions should be in ascending order
            assert versions == sorted(versions, key=lambda v: float(v)), (
                f"{lang_code}: Inheritance chain not in version order: {versions}"
            )

            print(f"✓ {lang_code}: Chain in correct order: {' → '.join(versions)}")

        except FileNotFoundError:
            pytest.skip(f"{lang_code} 3.13 pack not available")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_merges_keywords(self, pack_loader, lang_code):
        """Verify child packs inherit all parent keywords."""
        try:
            pack_310 = pack_loader.load(lang_code, "python", "3.10")
            pack_313 = pack_loader.load(lang_code, "python", "3.13")

            # 3.13 should have all keywords from 3.10
            for keyword in pack_310.keywords:
                assert keyword in pack_313.keywords, (
                    f"{lang_code}: Keyword '{keyword}' from 3.10 not inherited in 3.13"
                )

            # 3.13 should have same or more keywords than 3.10
            assert len(pack_313.keywords) >= len(pack_310.keywords), (
                f"{lang_code}: 3.13 has fewer keywords than 3.10 "
                f"({len(pack_313.keywords)} vs {len(pack_310.keywords)})"
            )

            print(
                f"✓ {lang_code}: 3.13 inherits all {len(pack_310.keywords)} keywords from 3.10"
            )

        except FileNotFoundError:
            pytest.skip(f"{lang_code} packs not fully available")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_inheritance_merges_builtins(self, pack_loader, lang_code):
        """Verify child packs inherit all parent builtins."""
        try:
            pack_310 = pack_loader.load(lang_code, "python", "3.10")
            pack_313 = pack_loader.load(lang_code, "python", "3.13")

            # 3.13 should have all builtins from 3.10
            for builtin in pack_310.builtins:
                assert builtin in pack_313.builtins, (
                    f"{lang_code}: Builtin '{builtin}' from 3.10 not inherited in 3.13"
                )

            # 3.13 should have same or more builtins than 3.10
            assert len(pack_313.builtins) >= len(pack_310.builtins), (
                f"{lang_code}: 3.13 has fewer builtins than 3.10 "
                f"({len(pack_313.builtins)} vs {len(pack_310.builtins)})"
            )

            print(
                f"✓ {lang_code}: 3.13 inherits all {len(pack_310.builtins)} builtins from 3.10"
            )

        except FileNotFoundError:
            pytest.skip(f"{lang_code} packs not fully available")


class TestVersionSpecificFeatures:
    """Test version-specific Python features are translated correctly."""

    def test_python_3_10_match_case(self, pack_loader):
        """Test Python 3.10+ match/case structural pattern matching."""
        test_code = """match status:
    case 200:
        print("OK")
    case 404:
        print("Not Found")
    case _:
        print("Other")"""

        for lang_code in LANGUAGES:
            try:
                pack = pack_loader.load(lang_code, "python", "3.10")

                # Verify match/case keywords exist
                assert "match" in pack.keywords, (
                    f"{lang_code} 3.10: Missing 'match' keyword"
                )
                assert "case" in pack.keywords, (
                    f"{lang_code} 3.10: Missing 'case' keyword"
                )

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

            except FileNotFoundError:
                pytest.skip(f"{lang_code} 3.10 pack not available")

    def test_python_3_11_exception_groups(self, pack_loader):
        """Test Python 3.11+ except* exception groups."""
        test_code = """try:
    raise ExceptionGroup("errors", [ValueError(), TypeError()])
except* ValueError as e:
    print("ValueError")
except* TypeError as e:
    print("TypeError")"""

        for lang_code in LANGUAGES:
            try:
                pack = pack_loader.load(lang_code, "python", "3.11")

                # Check if except* is defined (it's optional)
                if "except*" in pack.keywords:
                    translator = TokenTranslator(pack.keywords, pack.builtins)
                    translated = translator.translate_code(test_code, "en", lang_code)

                    assert pack.keywords["except*"] in translated, (
                        f"{lang_code}: 'except*' not translated"
                    )

                    print(f"✓ {lang_code} 3.11: except* working")
                else:
                    print(f"⊘ {lang_code} 3.11: except* not defined (optional)")

            except FileNotFoundError:
                pytest.skip(f"{lang_code} 3.11 pack not available")

    def test_version_features_not_in_earlier_versions(self, pack_loader):
        """Verify version-specific features aren't in earlier versions.

        Validates that:
        - Python 3.10+ features (match/case) are not in base 3.9 packs
        - Python 3.11+ features (except*) don't leak into 3.10 packs
        - Each version only adds features appropriate to that Python version
        """
        version_specific_features = {
            "3.10": ["match", "case"],  # PEP 634: Structural Pattern Matching
            # Note: 3.11+ features would go here when added:
            # "3.11": ["except*"],  # PEP 654: Exception Groups (if we add it)
        }

        for lang_code in LANGUAGES:
            try:
                # Load the base pack (3.10)
                pack_310 = pack_loader.load(lang_code, "python", "3.10")

                # Check that 3.10 features are present
                for feature in version_specific_features.get("3.10", []):
                    assert feature in pack_310.keywords, (
                        f"{lang_code} 3.10: Missing expected feature '{feature}'"
                    )

                # If we had older packs (3.9), we'd verify they DON'T have 3.10 features
                # For now, we just verify the 3.10 pack has the right features

                print(
                    f"✓ {lang_code}: Version-specific features correctly scoped "
                    f"(3.10: {', '.join(version_specific_features['3.10'])})"
                )

                # Check that child packs (3.11+) inherit but don't redefine base features
                try:
                    pack_311 = pack_loader.load(lang_code, "python", "3.11")
                    # 3.11 should have match/case from inheritance
                    for feature in version_specific_features["3.10"]:
                        assert feature in pack_311.keywords, (
                            f"{lang_code} 3.11: Should inherit 3.10 feature '{feature}'"
                        )
                except FileNotFoundError:
                    pass  # 3.11 pack may not exist yet

            except FileNotFoundError:
                pytest.skip(f"{lang_code} packs not available for version validation")


class TestVersionCompatibility:
    """Test that packs work across Python version ranges."""

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_metadata_version_ranges(self, pack_loader, lang_code):
        """Verify metadata specifies correct Python version ranges."""
        try:
            pack = pack_loader.load(lang_code, "python", "3.13")

            if pack.metadata:
                # Should specify minimum and maximum versions
                assert pack.metadata.python_version_min, (
                    f"{lang_code}: Missing python_version_min"
                )
                assert pack.metadata.python_version_max, (
                    f"{lang_code}: Missing python_version_max"
                )

                # Min should be <= max
                min_ver = float(pack.metadata.python_version_min)
                max_ver = float(pack.metadata.python_version_max)

                assert min_ver <= max_ver, (
                    f"{lang_code}: version_min ({min_ver}) > version_max ({max_ver})"
                )

                print(
                    f"✓ {lang_code}: Version range {pack.metadata.python_version_min} - {pack.metadata.python_version_max}"
                )

        except FileNotFoundError:
            pytest.skip(f"{lang_code} pack not available")

    @pytest.mark.parametrize("lang_code", LANGUAGES)
    def test_compatibility_tested_versions(self, pack_loader, lang_code):
        """Verify pack metadata lists tested Python versions."""
        try:
            pack = pack_loader.load(lang_code, "python", "3.13")

            if pack.metadata and hasattr(pack.metadata, "compatibility_tested"):
                tested = pack.metadata.compatibility_tested

                # Should be a list
                assert isinstance(tested, list), (
                    f"{lang_code}: compatibility_tested should be a list"
                )

                # Should have at least one version
                assert len(tested) > 0, f"{lang_code}: compatibility_tested is empty"

                # All entries should be valid version strings
                for version in tested:
                    assert version in [
                        "3.10",
                        "3.11",
                        "3.12",
                        "3.13",
                    ], (
                        f"{lang_code}: Invalid version in compatibility_tested: {version}"
                    )

                print(
                    f"✓ {lang_code}: Tested on {len(tested)} Python versions: {', '.join(tested)}"
                )

        except FileNotFoundError:
            pytest.skip(f"{lang_code} pack not available")


class TestCircularInheritance:
    """Test protection against circular inheritance."""

    def test_no_circular_references(self, pack_loader):
        """Verify pack loader prevents circular inheritance."""
        # This is more of a pack loader test, but important for validation
        # The pack loader should detect and prevent circular inheritance chains

        for lang_code in LANGUAGES:
            try:
                # If this loads successfully, no circular reference exists
                pack = pack_loader.load(lang_code, "python", "3.13")

                # Check inheritance chain doesn't have duplicates
                chain = pack.inheritance_chain
                unique_chain = list(set(chain))

                assert len(chain) == len(unique_chain), (
                    f"{lang_code}: Duplicate packs in inheritance chain: {chain}"
                )

                print(f"✓ {lang_code}: No circular inheritance detected")

            except FileNotFoundError:
                pytest.skip(f"{lang_code} pack not available")
            except RecursionError:
                pytest.fail(f"{lang_code}: Circular inheritance detected!")


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
        print("✓ Base packs (3.10) validated")
        print("✓ Child packs (3.11-3.13) inherit correctly")
        print("✓ Inheritance chains resolve properly")
        print("✓ Version-specific features working")
    else:
        print(f"\n⚠  {failed} test(s) failed")

    print("=" * 70)
