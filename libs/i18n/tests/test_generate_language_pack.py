"""Tests for generate_language_pack script."""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from generate_language_pack import LanguagePackGenerator  # noqa: E402


class TestLanguagePackGenerator:
    """Test language pack generation."""

    @pytest.fixture
    def sample_content(self):
        """Create sample extracted content."""
        return {
            "python_version": "3.14",
            "keywords": {
                "all": ["if", "def", "class", "async", "await"],
            },
            "builtins": {
                "print": {"name": "print", "docstring": "Print objects to stdout"},
                "len": {"name": "len", "docstring": "Return length of object"},
                "range": {"name": "range", "docstring": "Create range object"},
            },
            "types": {
                "int": {"name": "int", "docstring": "Integer type"},
                "str": {"name": "str", "docstring": "String type"},
                "ValueError": {
                    "name": "ValueError",
                    "docstring": "Value error",
                    "category": "exception",
                },
            },
        }

    @pytest.fixture
    def languages_dir(self, tmp_path):
        """Create temporary languages directory."""
        lang_dir = tmp_path / "languages"
        lang_dir.mkdir()
        return lang_dir

    @pytest.fixture
    def version_index(self, languages_dir):
        """Create version index with existing versions."""
        python_dir = languages_dir / "python"
        python_dir.mkdir()

        # Create 3.13 directory and pack
        v3_13_dir = python_dir / "3.13"
        v3_13_dir.mkdir()

        pack_3_13 = v3_13_dir / "en.yml"
        pack_data = {
            "language": "en",
            "python_version": "3.13",
            "keywords": {"if": "if", "def": "def", "class": "class", "async": "async"},
        }

        with open(pack_3_13, "w") as f:
            yaml.dump(pack_data, f)

        # Create version index
        index_file = python_dir / "version-index.yml"
        index_data = {
            "python_versions": {
                "3.13": {
                    "added_keywords": [],
                    "extends": "3.12",
                    "supported_languages": ["en", "es", "ar", "zh"],
                },
            },
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "latest_version": "3.13",
            },
        }

        with open(index_file, "w") as f:
            yaml.dump(index_data, f)

        return index_file

    def test_init(self, languages_dir):
        """Test generator initialization."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        assert generator.version == "3.14"
        assert generator.languages_dir == languages_dir
        assert generator.python_dir == languages_dir / "python"
        assert generator.version_dir == languages_dir / "python" / "3.14"

    def test_init_with_custom_languages(self, languages_dir):
        """Test initialization with custom supported languages."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
            supported_languages=["es", "fr", "de"],
        )

        assert generator.supported_languages == ["es", "fr", "de"]

    def test_find_parent_version(self, version_index, languages_dir):
        """Test finding parent version for inheritance."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        parent = generator._find_parent_version()

        assert parent == "3.13"

    def test_find_parent_version_no_index(self, languages_dir):
        """Test finding parent when no index exists."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        parent = generator._find_parent_version()

        assert parent is None

    def test_generate_base_pack(self, sample_content, languages_dir, version_index):
        """Test generating base English pack."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        output_path = generator.generate_base_pack(sample_content)

        # Check file was created
        assert output_path.exists()
        assert output_path == languages_dir / "python" / "3.14" / "en.yml"

        # Load and verify content
        with open(output_path) as f:
            pack = yaml.safe_load(f)

        # Check metadata
        assert pack["language"] == "en"
        assert pack["language_name"] == "English"
        assert pack["target"] == "python"
        assert pack["python_version"] == "3.14"
        assert pack["mlcp_version"] == "1.0"

        # Should extend previous version
        assert pack["extends"] == "../3.13/en.yml"

        # Check keywords
        assert "keywords" in pack
        assert pack["keywords"]["if"] == "if"
        assert pack["keywords"]["def"] == "def"

        # Check builtins
        assert "builtins" in pack
        assert pack["builtins"]["print"]["name"] == "print"
        assert "docstring" in pack["builtins"]["print"]

        # Check types (should exclude exceptions)
        assert "types" in pack
        assert "int" in pack["types"]
        assert "ValueError" not in pack["types"]  # Exceptions filtered out

    def test_generate_base_pack_no_parent(self, sample_content, languages_dir):
        """Test generating base pack without parent version."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        output_path = generator.generate_base_pack(sample_content)

        with open(output_path) as f:
            pack = yaml.safe_load(f)

        # Should not have extends field
        assert "extends" not in pack

    def test_generate_base_pack_dry_run(self, sample_content, languages_dir):
        """Test dry run mode for base pack."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        output_path = generator.generate_base_pack(sample_content, dry_run=True)

        # File should NOT be created
        assert not output_path.exists()

    def test_generate_translated_pack(
        self, sample_content, languages_dir, version_index
    ):
        """Test generating translated language pack."""
        translations = {
            "keywords": {
                "if": {"translation": "si", "status": "new"},
                "def": {"translation": "definir", "status": "reused"},
                "class": {"translation": "clase", "status": "reused"},
                "async": {"translation": "asincrono", "status": "reused"},
                "await": {"translation": "esperar", "status": "new"},
            },
            "builtins": {
                "print": {"translation": "imprimir", "status": "reused"},
                "len": {"translation": "longitud", "status": "reused"},
                "range": {"translation": "rango", "status": "reused"},
            },
            "types": {
                "int": {"translation": "entero", "status": "reused"},
                "str": {"translation": "cadena", "status": "reused"},
            },
            "statistics": {
                "total_items": 10,
                "reused_items": 8,
                "new_items": 2,
                "reuse_rate": 0.8,
            },
        }

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        output_path = generator.generate_translated_pack(
            language_code="es",
            translations=translations,
            base_content=sample_content,
        )

        # Check file was created
        assert output_path.exists()
        assert output_path == languages_dir / "python" / "3.14" / "es.yml"

        # Load and verify content
        with open(output_path) as f:
            pack = yaml.safe_load(f)

        # Check metadata
        assert pack["language"] == "es"
        assert pack["language_name"] == "Spanish"
        assert pack["target"] == "python"
        assert pack["python_version"] == "3.14"

        # Should extend previous version
        assert pack["extends"] == "../3.13/es.yml"

        # Check translations
        assert pack["keywords"]["if"] == "si"
        assert pack["keywords"]["def"] == "definir"
        assert pack["builtins"]["print"] == "imprimir"
        assert pack["types"]["int"] == "entero"

        # Check metadata includes reuse stats
        assert pack["metadata"]["reuse_rate"] == 0.8
        assert pack["metadata"]["review_status"] == "needs-review"

    def test_generate_translated_pack_stable(self, sample_content, languages_dir):
        """Test generating pack with no new items (stable)."""
        translations = {
            "keywords": {
                "if": {"translation": "si", "status": "reused"},
            },
            "builtins": {},
            "types": {},
            "statistics": {
                "total_items": 1,
                "reused_items": 1,
                "new_items": 0,
                "reuse_rate": 1.0,
            },
        }

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        output_path = generator.generate_translated_pack(
            language_code="es",
            translations=translations,
            base_content=sample_content,
        )

        with open(output_path) as f:
            pack = yaml.safe_load(f)

        # Should be marked as stable (no new items)
        assert pack["metadata"]["review_status"] == "stable"

    def test_update_version_index(self, sample_content, languages_dir, version_index):
        """Test updating version index with new version."""
        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        generator.update_version_index(sample_content)

        # Load updated index
        with open(version_index) as f:
            index = yaml.safe_load(f)

        # Should have new version
        assert "3.14" in index["python_versions"]

        # Check version entry
        v3_14 = index["python_versions"]["3.14"]
        assert v3_14["extends"] == "3.13"
        assert v3_14["supported_languages"] == ["en", "es", "ar", "zh"]

        # Should detect new keywords
        assert "await" in v3_14["added_keywords"]

        # Metadata should be updated
        assert index["metadata"]["latest_version"] == "3.14"

    def test_update_version_index_no_previous(self, sample_content, languages_dir):
        """Test updating index when no previous versions exist."""
        python_dir = languages_dir / "python"
        python_dir.mkdir()

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        generator.update_version_index(sample_content)

        # Check index was created
        index_path = python_dir / "version-index.yml"
        assert index_path.exists()

        with open(index_path) as f:
            index = yaml.safe_load(f)

        # Should have 3.14
        assert "3.14" in index["python_versions"]
        assert index["python_versions"]["3.14"]["extends"] is None

    def test_update_version_index_dry_run(
        self, sample_content, languages_dir, version_index
    ):
        """Test dry run mode for version index update."""
        # Get original content
        with open(version_index) as f:
            original = yaml.safe_load(f)

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=languages_dir,
        )

        generator.update_version_index(sample_content, dry_run=True)

        # Load index again
        with open(version_index) as f:
            current = yaml.safe_load(f)

        # Should not have changed
        assert current == original
        assert "3.14" not in current["python_versions"]


class TestIntegration:
    """Integration tests for complete pack generation."""

    @pytest.fixture
    def complete_setup(self, tmp_path):
        """Create complete setup with content and translations."""
        # Content
        content = {
            "python_version": "3.14",
            "keywords": {"all": ["if", "def", "class", "await"]},
            "builtins": {
                "print": {"name": "print", "docstring": "Print objects"},
                "len": {"name": "len", "docstring": "Return length"},
            },
            "types": {
                "int": {"name": "int", "docstring": "Integer type"},
                "str": {"name": "str", "docstring": "String type"},
            },
        }

        # Translations
        translations = {
            "es": {
                "keywords": {
                    kw: {"translation": f"{kw}_es", "status": "new"}
                    for kw in content["keywords"]["all"]
                },
                "builtins": {
                    name: {"translation": f"{name}_es", "status": "new"}
                    for name in content["builtins"].keys()
                },
                "types": {
                    name: {"translation": f"{name}_es", "status": "new"}
                    for name in content["types"].keys()
                },
                "statistics": {
                    "total_items": 8,
                    "new_items": 8,
                    "reused_items": 0,
                    "reuse_rate": 0.0,
                },
            },
            "ar": {
                "keywords": {
                    kw: {"translation": f"{kw}_ar", "status": "new"}
                    for kw in content["keywords"]["all"]
                },
                "builtins": {
                    name: {"translation": f"{name}_ar", "status": "new"}
                    for name in content["builtins"].keys()
                },
                "types": {
                    name: {"translation": f"{name}_ar", "status": "new"}
                    for name in content["types"].keys()
                },
                "statistics": {
                    "total_items": 8,
                    "new_items": 8,
                    "reused_items": 0,
                    "reuse_rate": 0.0,
                },
            },
        }

        # Save translations to files
        trans_dir = tmp_path / "translations"
        trans_dir.mkdir()

        for lang, trans in translations.items():
            trans_file = trans_dir / f"python-3.14-{lang}.json"
            with open(trans_file, "w") as f:
                json.dump(trans, f)

        # Languages directory
        lang_dir = tmp_path / "languages"
        lang_dir.mkdir()

        return {
            "content": content,
            "translations_dir": trans_dir,
            "languages_dir": lang_dir,
        }

    def test_complete_workflow(self, complete_setup):
        """Test complete language pack generation workflow."""
        setup = complete_setup

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=setup["languages_dir"],
            supported_languages=["es", "ar"],
        )

        # Generate base pack
        base_path = generator.generate_base_pack(setup["content"])
        assert base_path.exists()

        # Generate translated packs
        for lang in ["es", "ar"]:
            trans_file = setup["translations_dir"] / f"python-3.14-{lang}.json"
            with open(trans_file) as f:
                translations = json.load(f)

            pack_path = generator.generate_translated_pack(
                language_code=lang,
                translations=translations,
                base_content=setup["content"],
            )
            assert pack_path.exists()

        # Update version index
        generator.update_version_index(setup["content"])

        # Verify all files created
        version_dir = setup["languages_dir"] / "python" / "3.14"
        assert (version_dir / "en.yml").exists()
        assert (version_dir / "es.yml").exists()
        assert (version_dir / "ar.yml").exists()

        # Verify index
        index_path = setup["languages_dir"] / "python" / "version-index.yml"
        assert index_path.exists()

        with open(index_path) as f:
            index = yaml.safe_load(f)

        assert "3.14" in index["python_versions"]
        assert set(index["python_versions"]["3.14"]["supported_languages"]) == {
            "en",
            "es",
            "ar",
        }


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_content(self, tmp_path):
        """Test handling of empty content."""
        content = {
            "python_version": "3.14",
            "keywords": {"all": []},
            "builtins": {},
            "types": {},
        }

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=tmp_path,
        )

        output_path = generator.generate_base_pack(content)

        # Should create pack even if empty
        assert output_path.exists()

        with open(output_path) as f:
            pack = yaml.safe_load(f)

        assert pack["keywords"] == {}
        assert pack["builtins"] == {}
        assert pack["types"] == {}

    def test_missing_sections(self, tmp_path):
        """Test handling content with missing sections."""
        content = {
            "python_version": "3.14",
            "keywords": {"all": ["if", "def"]},
            # Missing builtins and types
        }

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=tmp_path,
        )

        output_path = generator.generate_base_pack(content)

        with open(output_path) as f:
            pack = yaml.safe_load(f)

        # Should handle gracefully
        assert "keywords" in pack
        assert len(pack["keywords"]) == 2

    def test_unicode_content(self, tmp_path):
        """Test handling Unicode in translations."""
        content = {
            "python_version": "3.14",
            "keywords": {"all": ["if"]},
            "builtins": {},
            "types": {},
        }

        translations = {
            "keywords": {"if": {"translation": "如果", "status": "new"}},
            "builtins": {},
            "types": {},
            "statistics": {"total_items": 1, "new_items": 1},
        }

        generator = LanguagePackGenerator(
            version="3.14",
            languages_dir=tmp_path,
        )

        output_path = generator.generate_translated_pack(
            language_code="zh",
            translations=translations,
            base_content=content,
        )

        # Should handle Unicode properly
        with open(output_path, encoding="utf-8") as f:
            pack = yaml.safe_load(f)

        assert pack["keywords"]["if"] == "如果"
