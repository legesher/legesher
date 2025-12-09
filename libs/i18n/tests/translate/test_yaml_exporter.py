"""Tests for YAML exporter merge functionality."""

import tempfile
from pathlib import Path
import yaml
import pytest

from legesher_i18n.db import TranslationDatabase
from scripts.translate.yaml_exporter import YAMLExporter


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = TranslationDatabase(db_path=db_path)
    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for YAML files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def exporter(temp_db):
    """Create YAML exporter instance."""
    return YAMLExporter(db=temp_db)


class TestYAMLExporterMerge:
    """Test YAML exporter merge functionality."""

    def test_merge_preserves_existing_translations(
        self, exporter, temp_output_dir, temp_db
    ):
        """Test that merge preserves existing translations when adding new ones."""
        # Create an existing YAML file with some translations
        yaml_file = temp_output_dir / "test_pack.yml"
        existing_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {
                "def": "definir",
                "return": "retornar",
                "class": "clase",
            },
            "builtins": {
                "print": "imprimir",
                "len": "longitud",
            },
            "exceptions": {
                "ValueError": "ErrorDeValor",
            },
            "metadata": {
                "python_version_min": "3.10",
                "python_version_max": "3.14",
                "compatibility_tested": ["3.10"],
                "last_updated": "2024-01-01",
                "community_reviewed": True,
                "author": "Original Author",
                "license": "MIT",
            },
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False)

        # Add new translations to database (only 2 new terms)
        temp_db.add_translation(
            language_code="es",
            term="if",
            term_type="keyword",
            translation="si",
            source="aya",
        )
        temp_db.add_translation(
            language_code="es",
            term="abs",
            term_type="builtin",
            translation="absoluto",
            source="aya",
        )

        # Write using _write_yaml_pack to trigger merge
        exporter._write_yaml_pack(
            filepath=yaml_file,
            language_code="es",
            version="3.10",
            extends=None,
            keywords={"if": "si"},
            builtins={"abs": "absoluto"},
            exceptions={},
            header="# Test header",
        )

        # Read the merged file
        with open(yaml_file, "r", encoding="utf-8") as f:
            merged_data = yaml.safe_load(f)

        # Verify all original translations are preserved
        assert merged_data["keywords"]["def"] == "definir"
        assert merged_data["keywords"]["return"] == "retornar"
        assert merged_data["keywords"]["class"] == "clase"
        assert merged_data["builtins"]["print"] == "imprimir"
        assert merged_data["builtins"]["len"] == "longitud"
        assert merged_data["exceptions"]["ValueError"] == "ErrorDeValor"

        # Verify new translations were added
        assert merged_data["keywords"]["if"] == "si"
        assert merged_data["builtins"]["abs"] == "absoluto"

        # Verify metadata was preserved
        assert merged_data["metadata"]["author"] == "Original Author"
        assert merged_data["metadata"]["community_reviewed"] is True

    def test_merge_overrides_existing_translations(self, exporter, temp_output_dir):
        """Test that new translations override existing ones for same keys."""
        yaml_file = temp_output_dir / "test_pack.yml"

        # Create existing file with old translation
        existing_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {
                "def": "old_translation",  # Old translation
            },
            "builtins": {},
            "exceptions": {},
            "metadata": {"last_updated": "2024-01-01"},
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False)

        # Write with new translation for same key
        exporter._write_yaml_pack(
            filepath=yaml_file,
            language_code="es",
            version="3.10",
            extends=None,
            keywords={"def": "definir"},  # New translation
            builtins={},
            exceptions={},
            header="# Test",
        )

        # Verify new translation replaced old one
        with open(yaml_file, "r", encoding="utf-8") as f:
            merged_data = yaml.safe_load(f)

        assert merged_data["keywords"]["def"] == "definir"  # New translation
        assert merged_data["keywords"]["def"] != "old_translation"

    def test_merge_creates_file_if_not_exists(self, exporter, temp_output_dir):
        """Test that merge creates new file if it doesn't exist."""
        yaml_file = temp_output_dir / "new_pack.yml"

        # File doesn't exist yet
        assert not yaml_file.exists()

        # Write to non-existent file
        exporter._write_yaml_pack(
            filepath=yaml_file,
            language_code="fr",
            version="3.10",
            extends=None,
            keywords={"def": "définir"},
            builtins={"print": "afficher"},
            exceptions={},
            header="# New file",
        )

        # Verify file was created
        assert yaml_file.exists()

        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["keywords"]["def"] == "définir"
        assert data["builtins"]["print"] == "afficher"

    def test_merge_handles_corrupted_yaml(self, exporter, temp_output_dir):
        """Test that merge handles corrupted YAML gracefully."""
        yaml_file = temp_output_dir / "corrupted.yml"

        # Create corrupted YAML file
        with open(yaml_file, "w", encoding="utf-8") as f:
            f.write("this is: not: valid: yaml: {{{\n")

        # Write should succeed by treating it as empty
        exporter._write_yaml_pack(
            filepath=yaml_file,
            language_code="de",
            version="3.10",
            extends=None,
            keywords={"def": "definieren"},
            builtins={},
            exceptions={},
            header="# Test",
        )

        # Verify valid YAML was written
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["keywords"]["def"] == "definieren"

    def test_merge_preserves_metadata_fields(self, exporter, temp_output_dir):
        """Test that specific metadata fields are preserved during merge."""
        yaml_file = temp_output_dir / "metadata_test.yml"

        # Create file with custom metadata
        existing_data = {
            "language": "ja",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "定義"},
            "builtins": {},
            "exceptions": {},
            "metadata": {
                "python_version_min": "3.8",  # Should be preserved
                "python_version_max": "3.12",  # Should be preserved
                "compatibility_tested": ["3.8", "3.9", "3.10"],  # Should be preserved
                "community_reviewed": True,  # Should be preserved
                "author": "Community Contributor",  # Should be preserved
                "license": "Apache-2.0",  # Should be preserved
                "last_updated": "2023-06-15",  # Should be updated
            },
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False)

        # Merge with new data
        exporter._write_yaml_pack(
            filepath=yaml_file,
            language_code="ja",
            version="3.10",
            extends=None,
            keywords={"return": "戻る"},
            builtins={},
            exceptions={},
            header="# Test",
        )

        with open(yaml_file, "r", encoding="utf-8") as f:
            merged_data = yaml.safe_load(f)

        # Verify preserved fields
        assert merged_data["metadata"]["python_version_min"] == "3.8"
        assert merged_data["metadata"]["python_version_max"] == "3.12"
        assert merged_data["metadata"]["compatibility_tested"] == ["3.8", "3.9", "3.10"]
        assert merged_data["metadata"]["community_reviewed"] is True
        assert merged_data["metadata"]["author"] == "Community Contributor"
        assert merged_data["metadata"]["license"] == "Apache-2.0"

        # Verify updated field
        assert merged_data["metadata"]["last_updated"] != "2023-06-15"

    def test_merge_empty_sections(self, exporter, temp_output_dir):
        """Test merge when existing file has empty sections."""
        yaml_file = temp_output_dir / "empty_sections.yml"

        existing_data = {
            "language": "ko",
            "target": "python",
            "version": "3.10",
            "keywords": {},  # Empty
            "builtins": {},  # Empty
            "exceptions": {},  # Empty
            "metadata": {},
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False)

        exporter._write_yaml_pack(
            filepath=yaml_file,
            language_code="ko",
            version="3.10",
            extends=None,
            keywords={"def": "정의"},
            builtins={"print": "출력"},
            exceptions={"ValueError": "값오류"},
            header="# Test",
        )

        with open(yaml_file, "r", encoding="utf-8") as f:
            merged_data = yaml.safe_load(f)

        # Verify sections were populated
        assert merged_data["keywords"]["def"] == "정의"
        assert merged_data["builtins"]["print"] == "출력"
        assert merged_data["exceptions"]["ValueError"] == "값오류"

    def test_integration_export_multiple_versions(
        self, exporter, temp_output_dir, temp_db
    ):
        """Test full integration: export multiple versions with inheritance."""
        # Add translations for a complete language pack
        translations = [
            ("es", "def", "keyword", "definir", "aya"),
            ("es", "return", "keyword", "retornar", "aya"),
            ("es", "print", "builtin", "imprimir", "aya"),
            ("es", "ValueError", "exception", "ErrorDeValor", "aya"),
        ]

        for lang, term, term_type, translation, source in translations:
            temp_db.add_translation(
                language_code=lang,
                term=term,
                term_type=term_type,
                translation=translation,
                source=source,
            )

        # Export (this creates all version files)
        pack_dir = (
            temp_output_dir / "python" / "es" / "legesher_i18n_python_es" / "packs"
        )
        pack_dir.mkdir(parents=True, exist_ok=True)

        # Simulate export by manually writing base version
        exporter._write_yaml_pack(
            filepath=pack_dir / "3.10.yml",
            language_code="es",
            version="3.10",
            extends=None,
            keywords={"def": "definir", "return": "retornar"},
            builtins={"print": "imprimir"},
            exceptions={"ValueError": "ErrorDeValor"},
            header="# Spanish Python 3.10",
        )

        # Now add more translations and re-export (should merge)
        temp_db.add_translation(
            language_code="es",
            term="if",
            term_type="keyword",
            translation="si",
            source="aya",
        )

        exporter._write_yaml_pack(
            filepath=pack_dir / "3.10.yml",
            language_code="es",
            version="3.10",
            extends=None,
            keywords={"if": "si"},  # Only new term
            builtins={},
            exceptions={},
            header="# Spanish Python 3.10",
        )

        # Verify merge worked
        with open(pack_dir / "3.10.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # All translations should be present
        assert data["keywords"]["def"] == "definir"
        assert data["keywords"]["return"] == "retornar"
        assert data["keywords"]["if"] == "si"
        assert data["builtins"]["print"] == "imprimir"
        assert data["exceptions"]["ValueError"] == "ErrorDeValor"


class TestYAMLExporterRegressions:
    """Test regressions and bug fixes."""

    def test_turkish_duplicate_bug_fix(self, exporter, temp_output_dir, temp_db):
        """Regression test for Turkish duplicate bug that replaced entire file.

        This bug occurred when re-translating 3 duplicate terms - the entire
        Turkish pack (100+ translations) was replaced with only those 3 terms.
        """
        # Create Turkish pack with many translations (simulate existing pack)
        yaml_file = temp_output_dir / "tr_3.10.yml"

        existing_data = {
            "language": "tr",
            "target": "python",
            "version": "3.10",
            "keywords": {
                "def": "tanımla",
                "return": "dön",
                "class": "sınıf",
                "import": "içeaktar",
                "from": "kaynak",
                "as": "olarak",
                "if": "eğer",  # Duplicate issue
                "else": "değilse",
                "elif": "değilseeğer",
                # ... 30+ more keywords
            },
            "builtins": {
                "print": "yazdır",
                "len": "uzunluk",
                "str": "yazı",
                "int": "tamsayı",
                # ... 70+ more builtins
            },
            "exceptions": {
                "ValueError": "DeğerHatası",
                "TypeError": "TipHatası",
                # ... more exceptions
            },
            "metadata": {
                "author": "Legesher Team (Aya AI Model)",
                "last_updated": "2024-11-20",
            },
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False)

        # Count existing translations
        existing_keyword_count = len(existing_data["keywords"])
        existing_builtin_count = len(existing_data["builtins"])

        # Now simulate re-translating ONLY 3 duplicate terms
        exporter._write_yaml_pack(
            filepath=yaml_file,
            language_code="tr",
            version="3.10",
            extends=None,
            keywords={"not": "değil", "if": "eğer", "ord": "karakter"},  # Only 3 terms
            builtins={},
            exceptions={},
            header="# Turkish Python 3.10",
        )

        # Read merged file
        with open(yaml_file, "r", encoding="utf-8") as f:
            merged_data = yaml.safe_load(f)

        # BUG REGRESSION TEST: All original translations should be preserved
        assert "def" in merged_data["keywords"], "Original 'def' translation was lost!"
        assert "return" in merged_data["keywords"], (
            "Original 'return' translation was lost!"
        )
        assert "print" in merged_data["builtins"], (
            "Original 'print' translation was lost!"
        )

        # Count should be original + new (if new keys)
        assert len(merged_data["keywords"]) >= existing_keyword_count, (
            f"Keywords reduced from {existing_keyword_count} to {len(merged_data['keywords'])}"
        )
        assert len(merged_data["builtins"]) >= existing_builtin_count, (
            f"Builtins reduced from {existing_builtin_count} to {len(merged_data['builtins'])}"
        )

        # Verify the 3 new/updated translations are present
        assert merged_data["keywords"]["not"] == "değil"
        assert merged_data["keywords"]["if"] == "eğer"
        assert merged_data["keywords"]["ord"] == "karakter"

        # Verify metadata preserved
        assert merged_data["metadata"]["author"] == "Legesher Team (Aya AI Model)"
