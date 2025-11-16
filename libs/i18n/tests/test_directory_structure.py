"""Tests for directory structure and path configuration.

This test suite ensures that the programming_languages directory structure
is correctly configured across all components after the rename from languages/.
"""

import pytest
from pathlib import Path

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.db import TranslationDatabase


class TestDirectoryStructure:
    """Test that all components use the correct directory structure."""

    def test_programming_languages_directory_exists(self):
        """Verify programming_languages directory exists."""
        pack_dir = Path(__file__).parent.parent / "programming_languages"
        assert pack_dir.exists(), "programming_languages directory should exist"
        assert pack_dir.is_dir(), "programming_languages should be a directory"

    def test_python_subdirectory_exists(self):
        """Verify python subdirectory exists under programming_languages."""
        python_dir = Path(__file__).parent.parent / "programming_languages" / "python"
        assert python_dir.exists(), "python subdirectory should exist"
        assert python_dir.is_dir(), "python should be a directory"

    def test_version_directories_exist(self):
        """Verify version directories exist (3.10, 3.11, 3.12, 3.13, 3.14)."""
        python_dir = Path(__file__).parent.parent / "programming_languages" / "python"
        expected_versions = ["3.10", "3.11", "3.12", "3.13", "3.14"]

        for version in expected_versions:
            version_dir = python_dir / version
            assert version_dir.exists(), f"Version directory {version} should exist"
            assert version_dir.is_dir(), f"{version} should be a directory"


class TestPackLoaderDefaultPath:
    """Test that LanguagePackLoader uses correct default path."""

    def test_default_pack_root_uses_programming_languages(self):
        """Verify default pack_root points to programming_languages directory."""
        loader = LanguagePackLoader()  # No pack_root specified

        assert "programming_languages" in str(loader.pack_root), (
            "Default pack_root should use programming_languages directory"
        )
        assert loader.pack_root.exists(), "Default pack_root should exist"

    def test_can_load_pack_with_default_path(self):
        """Verify packs can be loaded using default path."""
        loader = LanguagePackLoader()  # Uses default path

        # Should be able to load Arabic 3.10 pack
        pack = loader.load(language="ar", target="python", version="3.10")
        assert pack.language == "ar"
        assert pack.target == "python"
        assert pack.version == "3.10"

    def test_explicit_programming_languages_path_works(self):
        """Verify explicit programming_languages path works."""
        pack_root = Path(__file__).parent.parent / "programming_languages"
        loader = LanguagePackLoader(pack_root=pack_root)

        pack = loader.load(language="ar", target="python", version="3.10")
        assert pack.language == "ar"
        assert len(pack.keywords) > 0


class TestYAMLExporterDefaultPath:
    """Test that YAMLExporter uses correct default output path."""

    def test_yaml_exporter_default_output_uses_programming_languages(self):
        """Verify YAML exporter default output uses programming_languages."""
        import sys
        from pathlib import Path

        # Add scripts to path for import
        scripts_path = Path(__file__).parent.parent / "scripts" / "translate"
        sys.path.insert(0, str(scripts_path))

        try:
            from yaml_exporter import YAMLExporter

            db = TranslationDatabase()
            exporter = YAMLExporter(db)  # Uses default output_dir

            assert "programming_languages" in str(exporter.output_dir), (
                "YAML exporter should use programming_languages in default path"
            )
            assert "python/3.10" in str(exporter.output_dir), (
                "YAML exporter should default to python/3.10"
            )
        finally:
            # Clean up sys.path
            sys.path.remove(str(scripts_path))


class TestLanguagePackStructure:
    """Test that language pack files are properly structured."""

    def test_spanish_pack_yaml_not_keyword_is_quoted(self):
        """Verify Spanish pack properly quotes 'not: no' to avoid YAML boolean parsing."""
        import yaml

        es_pack_path = (
            Path(__file__).parent.parent
            / "programming_languages"
            / "python"
            / "3.10"
            / "es.yml"
        )

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

    def test_cli_can_validate_pack_in_programming_languages(self):
        """Verify CLI can validate packs in programming_languages directory."""
        from legesher_i18n.pack_loader import LanguagePackLoader

        pack_root = Path(__file__).parent.parent / "programming_languages"
        loader = LanguagePackLoader(pack_root=pack_root)

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
    """Test that old 'languages' path is NOT used anymore."""

    def test_old_languages_directory_does_not_exist(self):
        """Verify old 'languages' directory has been removed."""
        old_dir = Path(__file__).parent.parent / "languages"
        assert not old_dir.exists(), (
            "Old 'languages' directory should not exist after rename"
        )

    def test_no_hardcoded_languages_path_in_loader(self):
        """Verify pack loader doesn't use old 'languages' path."""
        from legesher_i18n.pack_loader import LanguagePackLoader
        import inspect

        source = inspect.getsource(LanguagePackLoader.__init__)
        assert "programming_languages" in source, (
            "Loader should reference programming_languages"
        )
        assert '"languages"' not in source and "'languages'" not in source, (
            "Loader should not reference old 'languages' path"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
