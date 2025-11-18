"""Smoke tests for language pack reorganization.

These tests verify that the reorganization is working correctly:
- All 5 language packs are discoverable
- Each pack has the correct number of keywords and builtins
- Version inheritance works properly
- Package discovery mechanism functions correctly
"""

import pytest
from legesher_i18n import load_language_pack, LanguagePackLoader


class TestPackageDiscovery:
    """Test that all language packs are discoverable."""

    def test_discovers_all_five_language_packs(self):
        """Verify that package discovery finds all 5 language packs."""
        loader = LanguagePackLoader()
        discovered = loader._discover_packs()

        assert len(discovered) >= 5, (
            f"Expected at least 5 packs, found {len(discovered)}"
        )

        expected_packs = [
            "python-ar",
            "python-es",
            "python-en",
            "python-fr",
            "python-zh",
        ]
        for pack_key in expected_packs:
            assert pack_key in discovered, f"Missing pack: {pack_key}"

    def test_list_available_languages_returns_all_five(self):
        """Verify that list_available_languages returns all 5 languages."""
        loader = LanguagePackLoader()
        langs = loader.list_available_languages("python")

        lang_codes = [code for code, _ in langs]
        assert len(lang_codes) >= 5, (
            f"Expected at least 5 languages, found {len(lang_codes)}"
        )

        expected_langs = ["ar", "es", "en", "fr", "zh"]
        for lang in expected_langs:
            assert lang in lang_codes, f"Missing language: {lang}"


class TestLanguagePackLoading:
    """Test that all language packs load correctly."""

    @pytest.mark.parametrize("lang", ["ar", "es", "en", "fr", "zh"])
    def test_load_python_3_13_for_all_languages(self, lang):
        """Verify each language pack loads for Python 3.13 with correct counts."""
        pack = load_language_pack(lang, version="3.13")

        assert pack.language == lang
        assert pack.target == "python"
        assert pack.version == "3.13"

        # Python 3.13 should have 39 keywords (37 base + except* + type)
        assert len(pack.keywords) == 39, (
            f"{lang} should have 39 keywords, got {len(pack.keywords)}"
        )

        # All packs should have 81 builtins (updated from 41)
        assert len(pack.builtins) == 81, (
            f"{lang} should have 81 builtins, got {len(pack.builtins)}"
        )


class TestVersionInheritance:
    """Test that version inheritance works correctly."""

    @pytest.mark.parametrize(
        "version,expected_keywords",
        [
            ("3.10", 37),  # Base: match, case
            ("3.11", 38),  # + except*
            ("3.12", 39),  # + type
            ("3.13", 39),  # No new keywords
            ("3.14", 39),  # No new keywords
        ],
    )
    def test_version_inheritance_keyword_counts(self, version, expected_keywords):
        """Verify that each version has the correct keyword count through inheritance."""
        pack = load_language_pack("es", version=version)

        assert len(pack.keywords) == expected_keywords, (
            f"Python {version} should have {expected_keywords} keywords, "
            f"got {len(pack.keywords)}"
        )

    def test_version_3_10_has_match_and_case(self):
        """Verify Python 3.10 has match/case keywords."""
        pack = load_language_pack("ar", version="3.10")

        assert "match" in pack.keywords, "3.10 should have 'match' keyword"
        assert "case" in pack.keywords, "3.10 should have 'case' keyword"

    def test_version_3_11_has_except_star(self):
        """Verify Python 3.11 has except* keyword."""
        pack = load_language_pack("ar", version="3.11")

        assert "except*" in pack.keywords, "3.11 should have 'except*' keyword"

    def test_version_3_12_has_type(self):
        """Verify Python 3.12 has type keyword."""
        pack = load_language_pack("ar", version="3.12")

        assert "type" in pack.keywords, "3.12 should have 'type' keyword"

    def test_inheritance_chain_is_present(self):
        """Verify that packs have inheritance chain information."""
        pack = load_language_pack("fr", version="3.14")

        # 3.14 should inherit through the full chain
        assert len(pack.inheritance_chain) > 0, "Should have inheritance chain"


class TestTranslationQuality:
    """Test that translations are present and correct."""

    def test_arabic_has_translations(self):
        """Verify Arabic pack has actual translations."""
        pack = load_language_pack("ar", version="3.10")

        # Check some key keywords have translations
        assert pack.get_keyword_translation("def") is not None
        assert pack.get_keyword_translation("class") is not None
        assert pack.get_builtin_translation("print") is not None

    def test_spanish_has_translations(self):
        """Verify Spanish pack has actual translations."""
        pack = load_language_pack("es", version="3.10")

        assert pack.get_keyword_translation("def") is not None
        assert pack.get_keyword_translation("class") is not None
        assert pack.get_builtin_translation("print") is not None

    def test_english_maps_to_itself(self):
        """Verify English pack maps keywords to themselves (canonical)."""
        pack = load_language_pack("en", version="3.10")

        # English should map to itself
        assert pack.get_keyword_translation("def") == "def"
        assert pack.get_keyword_translation("class") == "class"
        assert pack.get_builtin_translation("print") == "print"

    @pytest.mark.parametrize("lang", ["ar", "es", "en", "fr", "zh"])
    def test_all_languages_have_81_builtins(self, lang):
        """Verify all language packs have 81 builtins (updated count)."""
        pack = load_language_pack(lang, version="3.10")

        assert len(pack.builtins) == 81, (
            f"{lang} should have 81 builtins, got {len(pack.builtins)}"
        )


class TestPackageStructure:
    """Test that the package structure is correct."""

    def test_all_packs_are_in_language_packs_directory(self):
        """Verify all discovered packs are in the language-packs/ directory."""

        loader = LanguagePackLoader()
        discovered = loader._discover_packs()

        for pack_key, pack_path in discovered.items():
            # Should contain language-packs in the path
            assert "language-packs" in str(pack_path), (
                f"{pack_key} should be in language-packs/ directory, found at {pack_path}"
            )

    def test_no_old_programming_languages_structure_in_use(self):
        """Verify that packs are not loaded from old programming_languages/ structure."""

        loader = LanguagePackLoader()
        discovered = loader._discover_packs()

        for pack_key, pack_path in discovered.items():
            # Should NOT contain programming_languages in the path
            assert "programming_languages" not in str(pack_path), (
                f"{pack_key} should not use old programming_languages/ structure"
            )
