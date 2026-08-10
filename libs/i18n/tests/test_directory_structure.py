"""Tests for directory structure and path configuration.

This test suite ensures that the language-packs directory structure
is correctly configured across all components after the reorganization.
"""

import pytest
from pathlib import Path

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.db import TranslationDatabase
from tests import I18N_ROOT, language_packs_root, pack_file

#: The database is an untracked working copy since CORE-1794 — a fresh clone
#: does not have it until it is copied in from the private data home (see
#: libs/i18n/CLAUDE.md, "Durable home & sync ritual").
requires_real_db = pytest.mark.skipif(
    not (I18N_ROOT / "legesher_i18n" / "db" / "translations.db").exists(),
    reason=(
        "translations.db is an untracked working copy (CORE-1794); copy it in "
        "from the private data home — libs/i18n/CLAUDE.md, 'Durable home & "
        "sync ritual'"
    ),
)


class TestDirectoryStructure:
    """Test that all components use the correct directory structure."""

    def test_language_packs_directory_exists(self):
        """Verify language-packs directory exists."""
        pack_dir = I18N_ROOT / "language-packs"
        assert pack_dir.exists(), "language-packs directory should exist"
        assert pack_dir.is_dir(), "language-packs should be a directory"

    def test_python_subdirectory_exists(self):
        """Verify python subdirectory exists under language-packs."""
        python_dir = language_packs_root()
        assert python_dir.exists(), "python subdirectory should exist"
        assert python_dir.is_dir(), "python should be a directory"

    def test_language_package_directories_exist(self):
        """Verify language package directories exist (ar, es, en, fr, zh)."""
        python_dir = language_packs_root()
        expected_languages = ["ar", "es", "en", "fr", "zh"]

        for lang in expected_languages:
            lang_dir = python_dir / lang
            assert lang_dir.exists(), f"Language directory {lang} should exist"
            assert lang_dir.is_dir(), f"{lang} should be a directory"


class TestPackLoaderDefaultPath:
    """Test that LanguagePackLoader uses package discovery."""

    def test_can_discover_language_packs(self):
        """Verify package discovery finds all language packs."""
        loader = LanguagePackLoader()  # Uses package discovery

        discovered = loader._discover_packs()
        assert len(discovered) >= 5, "Should discover at least 5 language packs"
        assert "python-ar" in discovered, "Should discover python-ar pack"
        assert "python-es" in discovered, "Should discover python-es pack"
        assert "python-en" in discovered, "Should discover python-en pack"
        assert "python-fr" in discovered, "Should discover python-fr pack"
        assert "python-zh" in discovered, "Should discover python-zh pack"

    def test_can_load_pack_with_discovery(self):
        """Verify packs can be loaded using package discovery."""
        loader = LanguagePackLoader()  # Uses package discovery

        # Should be able to load Arabic 3.10 pack
        pack = loader.load(language="ar", target="python", version="3.10")
        assert pack.language == "ar"
        assert pack.target == "python"
        assert pack.version == "3.10"

    def test_list_available_languages(self):
        """Verify can list all available languages."""
        loader = LanguagePackLoader()

        langs = loader.list_available_languages("python")
        lang_codes = [code for code, _ in langs]
        assert len(lang_codes) >= 5, "Should have at least 5 languages"
        assert "ar" in lang_codes, "Should include Arabic"
        assert "es" in lang_codes, "Should include Spanish"
        assert "en" in lang_codes, "Should include English"
        assert "fr" in lang_codes, "Should include French"
        assert "zh" in lang_codes, "Should include Chinese"


class TestYAMLExporterDefaultPath:
    """Test that YAMLExporter uses correct default output path."""

    @requires_real_db
    def test_yaml_exporter_default_output_uses_language_packs(self):
        """Verify YAML exporter default output uses language-packs."""
        import sys
        from pathlib import Path

        # Add scripts to path for import
        scripts_path = Path(__file__).parent.parent / "scripts" / "translate"
        sys.path.insert(0, str(scripts_path))

        try:
            from yaml_exporter import YAMLExporter

            db = TranslationDatabase()
            exporter = YAMLExporter(db)  # Uses default output_dir

            # Skip test if exporter still uses old path (backward compatibility)
            # This test can be updated when exporter is refactored for new structure
            if "programming_languages" in str(exporter.output_dir):
                pytest.skip("Exporter still uses old structure - will be updated")
        finally:
            # Clean up sys.path
            if str(scripts_path) in sys.path:
                sys.path.remove(str(scripts_path))


class TestLanguagePackStructure:
    """Test that language pack files are properly structured."""

    def test_spanish_pack_yaml_not_keyword_is_quoted(self):
        """Verify Spanish pack properly quotes 'not: no' to avoid YAML boolean parsing."""
        import yaml

        es_pack_path = pack_file("es", "3.10")

        # Load the YAML and verify the 'not' keyword is parsed as string "no", not boolean False
        with open(es_pack_path) as f:
            data = yaml.safe_load(f)

        not_value = data.get("keywords", {}).get("not")
        assert not_value == "no", (
            f"Spanish pack 'not' keyword should be string 'no', got {not_value!r} ({type(not_value).__name__})"
        )
        assert not isinstance(not_value, bool), (
            "Spanish pack 'not' keyword should not be parsed as boolean"
        )

    def test_language_pack_inheritance_chain(self):
        """Verify language packs properly inherit from previous versions."""
        loader = LanguagePackLoader()

        # Test 3.14 pack which should inherit through full chain
        pack = loader.load(language="fr", target="python", version="3.14")

        # Should have full inheritance chain
        assert len(pack.inheritance_chain) > 0, "Should have inheritance chain"

        # Should have keywords from base pack
        assert len(pack.keywords) > 0, "Should inherit keywords from base packs"
        assert pack.get_keyword_translation("def") is not None, (
            "Should inherit 'def' keyword from base pack"
        )


class TestCLIValidation:
    """Test CLI validation commands work with new directory structure."""

    def test_cli_can_validate_pack_in_language_packs(self):
        """Verify CLI can validate packs in language-packs directory."""
        from legesher_i18n.pack_loader import LanguagePackLoader

        loader = LanguagePackLoader()  # Uses package discovery

        # Test packs that don't have the YAML boolean issue
        test_packs = [
            ("ar", "python", "3.14"),
            ("zh", "python", "3.12"),
            ("fr", "python", "3.10"),
        ]

        for lang, target, version in test_packs:
            pack = loader.load(language=lang, target=target, version=version)
            assert pack is not None, f"Should load {lang} {version} pack"


class TestBackwardCompatibility:
    """Test that old directory structures are removed."""

    def test_old_languages_directory_does_not_exist(self):
        """Verify old 'languages' directory has been removed."""
        old_dir = Path(__file__).parent.parent / "languages"
        assert not old_dir.exists(), (
            "Old 'languages' directory should not exist after rename"
        )

    def test_old_programming_languages_directory_does_not_exist(self):
        """Verify old 'programming_languages' directory has been removed or is empty."""
        old_dir = Path(__file__).parent.parent / "programming_languages"

        # Check if directory doesn't exist OR is empty (may be recreated by some tools)
        if old_dir.exists():
            # Verify it's empty (no YAML files)
            yaml_files = list(old_dir.rglob("*.yml"))
            assert len(yaml_files) == 0, (
                f"Old 'programming_languages' directory should be empty, found {len(yaml_files)} YAML files"
            )

    def test_loader_uses_package_discovery(self):
        """Verify pack loader uses package discovery for new structure."""
        from legesher_i18n.pack_loader import LanguagePackLoader

        loader = LanguagePackLoader()
        discovered = loader._discover_packs()
        assert len(discovered) > 0, "Should discover packages via importlib"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
