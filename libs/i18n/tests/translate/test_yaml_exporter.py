"""Tests for YAML exporter merge functionality."""

import tempfile
from pathlib import Path
import yaml
import pytest

from legesher_i18n.db import TranslationDatabase
from scripts.translate.yaml_exporter import YAMLExporter


def _add_language(db, code):
    """Helper to ensure a language exists in the database."""
    names = {
        "es": ("Spanish", "Español"),
        "fr": ("French", "Français"),
        "de": ("German", "Deutsch"),
        "ja": ("Japanese", "日本語"),
        "ko": ("Korean", "한국어"),
        "tr": ("Turkish", "Türkçe"),
    }
    name, native_name = names.get(code, (code.upper(), code.upper()))
    conn = db._get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO languages (code, name, native_name) VALUES (?, ?, ?)",
        (code, name, native_name),
    )
    conn.commit()


def _add_translation(db, language_code, term, term_type, translation, source):
    """Helper that wraps the new schema API to mirror old add_translation interface.

    Creates the language (if needed), gets or creates the term, and adds the translation.
    """
    _add_language(db, language_code)
    term_id = db.get_or_create_term(
        name=term, programming_language="python", category=term_type
    )
    return db.add_translation(
        term_id=term_id,
        language_code=language_code,
        translation=translation,
        source=source,
    )


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = TranslationDatabase(db_path=db_path)
    yield db

    # Close DB before cleanup to avoid Windows file-locking errors
    db.close()
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
                "license": "Apache-2.0",
            },
        }

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(existing_data, f, allow_unicode=True, sort_keys=False)

        # Add new translations to database (only 2 new terms)
        _add_translation(temp_db, "es", "if", "keyword", "si", "aya")
        _add_translation(temp_db, "es", "abs", "builtin_func", "absoluto", "aya")

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
            ("es", "print", "builtin_func", "imprimir", "aya"),
            ("es", "ValueError", "exception", "ErrorDeValor", "aya"),
        ]

        for lang, term, term_type, translation, source in translations:
            _add_translation(temp_db, lang, term, term_type, translation, source)

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
        _add_translation(temp_db, "es", "if", "keyword", "si", "aya")

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

    def test_turkish_duplicate_bug_fix(self, exporter, temp_output_dir):
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


class TestYAMLExporterTermTypeFromDB:
    """Test that YAML exporter uses stored term_type from database (CORE-460).

    This test class verifies that:
    1. Exporter uses the term_type stored in the database as single source of truth
    2. Fallback to classify_term() works for legacy data with missing/invalid term_type
    3. Special constants map correctly to builtins section
    4. Future term types would create new sections (extensible design)
    """

    def test_uses_term_type_from_database(self, temp_db, temp_output_dir):
        """Verify exporter uses stored term_type, not re-classification."""
        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        # Add translations with explicit term_types (category in new schema)
        _add_translation(temp_db, "es", "def", "keyword", "definir", "test")
        _add_translation(temp_db, "es", "print", "builtin_func", "imprimir", "test")
        _add_translation(
            temp_db, "es", "ValueError", "exception", "ErrorDeValor", "test"
        )

        # Build term map and classify
        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)
        classified = exporter._classify_terms(term_map)

        # Verify terms are in correct sections based on stored term_type
        assert "def" in classified["keywords"], "keyword term should be in keywords"
        assert "print" in classified["builtins"], "builtin_func should be in builtins"
        assert "ValueError" in classified["exceptions"], (
            "exception should be in exceptions"
        )

    def test_fallback_for_empty_term_type(self, temp_db, temp_output_dir, caplog):
        """Verify fallback classification when term_type is empty string.

        In the new schema, term_type comes from terms.category via JOIN.
        We insert a term with empty category to trigger the fallback.
        """
        import logging

        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        # Insert a term with empty category and a translation for it
        _add_language(temp_db, "es")
        conn = temp_db._get_connection()
        conn.execute(
            "INSERT INTO terms (name, programming_language, category) VALUES (?, ?, ?)",
            ("return", "python", ""),  # Empty string category
        )
        conn.commit()
        term_id = conn.execute(
            "SELECT id FROM terms WHERE name = ? AND programming_language = ?",
            ("return", "python"),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO translations (term_id, language_code, translation, source) VALUES (?, ?, ?, ?)",
            (term_id, "es", "retornar", "legacy"),
        )
        conn.commit()

        # Get translations and classify
        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)

        with caplog.at_level(logging.WARNING):
            classified = exporter._classify_terms(term_map)

        # Verify fallback worked - "return" should be classified as keyword
        assert "return" in classified["keywords"], (
            "fallback should classify 'return' as keyword"
        )

        # Verify warning was logged about invalid term_type
        assert any("Invalid term_type" in record.message for record in caplog.records)

    def test_fallback_for_invalid_term_type(self, temp_db, temp_output_dir, caplog):
        """Verify fallback classification when term_type is invalid."""
        import logging

        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        # Insert a term with invalid category and a translation for it
        _add_language(temp_db, "es")
        conn = temp_db._get_connection()
        conn.execute(
            "INSERT INTO terms (name, programming_language, category) VALUES (?, ?, ?)",
            ("for", "python", "invalid_type_xyz"),
        )
        conn.commit()
        term_id = conn.execute(
            "SELECT id FROM terms WHERE name = ? AND programming_language = ?",
            ("for", "python"),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO translations (term_id, language_code, translation, source) VALUES (?, ?, ?, ?)",
            (term_id, "es", "para", "bad_source"),
        )
        conn.commit()

        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)

        with caplog.at_level(logging.WARNING):
            classified = exporter._classify_terms(term_map)

        # Verify fallback worked - "for" should be classified as keyword
        assert "for" in classified["keywords"], (
            "fallback should classify 'for' as keyword"
        )

        # Verify warning was logged about invalid term_type
        assert any("Invalid term_type" in record.message for record in caplog.records)

    def test_special_constant_maps_to_builtins(self, temp_db, temp_output_dir):
        """Verify special_constant term_type maps to builtins section."""
        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        # Add special constant with explicit term_type
        _add_translation(
            temp_db, "es", "ellipsis", "special_constant", "puntos_suspensivos", "test"
        )

        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)
        classified = exporter._classify_terms(term_map)

        # Verify special_constant goes to builtins section
        assert "ellipsis" in classified["builtins"], (
            "special_constant should map to builtins section"
        )
        assert "ellipsis" not in classified.get("special_constants", {}), (
            "should not create separate special_constants section"
        )

    def test_builtin_type_maps_to_builtins(self, temp_db, temp_output_dir):
        """Verify builtin_type term_type maps to builtins section."""
        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        _add_translation(temp_db, "es", "str", "builtin_type", "cadena", "test")

        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)
        classified = exporter._classify_terms(term_map)

        assert "str" in classified["builtins"], (
            "builtin_type should map to builtins section"
        )

    def test_standard_sections_always_exist(self, temp_db, temp_output_dir):
        """Verify keywords, builtins, exceptions sections always exist."""
        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        # Add only a keyword - no builtins or exceptions
        _add_translation(temp_db, "es", "if", "keyword", "si", "test")

        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)
        classified = exporter._classify_terms(term_map)

        # All standard sections should exist (even if empty)
        assert "keywords" in classified
        assert "builtins" in classified
        assert "exceptions" in classified

    def test_helper_and_unknown_excluded_from_yaml(self, temp_db, temp_output_dir):
        """Verify helper and unknown term types are excluded from YAML export."""
        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        # Add translations with helper and unknown types
        _add_translation(temp_db, "es", "README", "helper", "LEEME", "test")

        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)
        classified = exporter._classify_terms(term_map)

        # Helper terms should not appear in any section
        assert "README" not in classified["keywords"]
        assert "README" not in classified["builtins"]
        assert "README" not in classified["exceptions"]

    def test_pipeline_to_yaml_term_type_consistency(self, temp_db, temp_output_dir):
        """Integration test: verify term_type consistency from storage to export."""
        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        # Simulate what pipeline.py does: store with classified term_type
        test_terms = [
            ("def", "keyword", "definir"),
            ("print", "builtin_func", "imprimir"),
            ("str", "builtin_type", "cadena"),
            ("ValueError", "exception", "ErrorDeValor"),
            ("ellipsis", "special_constant", "puntos_suspensivos"),
        ]

        for term, term_type, translation in test_terms:
            _add_translation(
                temp_db, "es", term, term_type, translation, "pipeline_test"
            )

        # Export and classify
        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)
        classified = exporter._classify_terms(term_map)

        # Verify correct section placement
        assert classified["keywords"]["def"] == "definir"
        assert classified["builtins"]["print"] == "imprimir"
        assert classified["builtins"]["str"] == "cadena"
        assert classified["exceptions"]["ValueError"] == "ErrorDeValor"
        assert classified["builtins"]["ellipsis"] == "puntos_suspensivos"

    def test_export_produces_idempotent_result(self, temp_db, temp_output_dir):
        """Verify re-exporting produces the same classification result."""
        exporter = YAMLExporter(db=temp_db, output_dir=temp_output_dir)

        _add_translation(temp_db, "es", "class", "keyword", "clase", "test")
        _add_translation(temp_db, "es", "len", "builtin_func", "longitud", "test")

        translations = temp_db.get_translations_joined(language_code="es")
        term_map = exporter._build_term_map(translations)

        # Classify twice
        classified_1 = exporter._classify_terms(term_map)
        classified_2 = exporter._classify_terms(term_map)

        # Results should be identical
        assert classified_1 == classified_2, "Classification should be idempotent"
