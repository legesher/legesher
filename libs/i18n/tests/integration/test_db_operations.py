"""Integration tests for translation database operations (consolidated schema).

Tests end-to-end workflows using the 4-table schema:
terms, languages, translations, selected_translations.
"""

import tempfile
from pathlib import Path

import pytest

from legesher_i18n.db.database import TranslationDatabase


@pytest.mark.integration
class TestDatabaseOperations:
    """Integration tests for end-to-end database workflows."""

    @pytest.fixture
    def db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            db_instance = TranslationDatabase(db_path=db_path)
            yield db_instance
            db_instance.close()

    @pytest.fixture
    def populated_db(self, db):
        """Create a database populated with sample data."""
        conn = db._get_connection()

        # Add languages
        for code, name, native in [
            ("es", "Spanish", "Español"),
            ("ar", "Arabic", "العربية"),
            ("fr", "French", "Français"),
        ]:
            conn.execute(
                "INSERT INTO languages (code, name, native_name, has_yaml_pack) VALUES (?, ?, ?, 1)",
                (code, name, native),
            )
        conn.commit()

        # Add terms
        terms = [
            ("if", "keyword", "control_flow"),
            ("for", "keyword", "iteration"),
            ("def", "keyword", "structure"),
            ("print", "builtin_func", None),
            ("ValueError", "exception", "type_value"),
        ]
        for name, category, subcategory in terms:
            db.get_or_create_term(
                name=name,
                programming_language="python",
                category=category,
                subcategory=subcategory,
            )

        return db

    def test_full_translation_workflow(self, populated_db):
        """Test complete workflow: create terms, add translations, select best."""
        db = populated_db

        # Get term ID
        term = db.get_term_by_name("if")
        assert term is not None
        term_id = term["id"]

        # Add multiple translation suggestions from different sources
        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="si",
            source="community",
            confidence="high",
        )
        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="si",
            source="aya",
            confidence="medium",
        )
        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="cuando",
            source="claude",
            confidence="low",
        )

        # Check all suggestions exist
        translations = db.get_translations_for_term(term_name="if", language_code="es")
        assert len(translations) == 3

        # Select the best one
        db.set_selected(
            term_id=term_id,
            language_code="es",
            translation="si",
            selected_by="pipeline",
            selection_reason="Consensus across community and Aya",
        )

        # Verify selection
        selected = db.get_selected_by_name(term_name="if", language_code="es")
        assert selected["translation"] == "si"

    def test_multi_language_translations(self, populated_db):
        """Test adding translations across multiple languages for same term."""
        db = populated_db

        term = db.get_term_by_name("def")
        term_id = term["id"]

        # Add translations in 3 languages
        db.add_translation(
            term_id=term_id, language_code="es", translation="definir", source="aya"
        )
        db.add_translation(
            term_id=term_id, language_code="ar", translation="عرّف", source="aya"
        )
        db.add_translation(
            term_id=term_id, language_code="fr", translation="définir", source="aya"
        )

        # Select best for each language
        db.set_selected(term_id=term_id, language_code="es", translation="definir")
        db.set_selected(term_id=term_id, language_code="ar", translation="عرّف")
        db.set_selected(term_id=term_id, language_code="fr", translation="définir")

        # Get all selected for Spanish
        es_selected = db.get_all_selected(language_code="es")
        assert len(es_selected) == 1

        # Get all selected for Arabic
        ar_selected = db.get_all_selected(language_code="ar")
        assert len(ar_selected) == 1
        assert ar_selected[0]["translation"] == "عرّف"

    def test_change_selected_translation(self, populated_db):
        """Test changing the selected translation for a term+language pair."""
        db = populated_db

        term = db.get_term_by_name("print")
        term_id = term["id"]

        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="imprimir",
            source="community",
        )
        db.add_translation(
            term_id=term_id, language_code="es", translation="mostrar", source="aya"
        )

        # Select first option
        db.set_selected(term_id=term_id, language_code="es", translation="imprimir")
        assert (
            db.get_selected(term_id=term_id, language_code="es")["translation"]
            == "imprimir"
        )

        # Change selection
        db.set_selected(
            term_id=term_id,
            language_code="es",
            translation="mostrar",
            selection_reason="Community preferred",
        )
        assert (
            db.get_selected(term_id=term_id, language_code="es")["translation"]
            == "mostrar"
        )

    def test_stats_reflect_operations(self, populated_db):
        """Test that get_stats accurately reflects database state."""
        db = populated_db

        stats_before = db.get_stats()
        assert stats_before["terms_count"] == 5
        assert stats_before["languages_count"] == 3
        assert stats_before["translations_count"] == 0
        assert stats_before["selected_translations_count"] == 0

        # Add some translations
        term = db.get_term_by_name("for")
        db.add_translation(
            term_id=term["id"], language_code="es", translation="para", source="aya"
        )
        db.set_selected(term_id=term["id"], language_code="es", translation="para")

        stats_after = db.get_stats()
        assert stats_after["translations_count"] == 1
        assert stats_after["selected_translations_count"] == 1

    # Placeholder integration tests
    def test_bulk_insert_translations(self, populated_db):
        """Test inserting multiple translations in bulk."""
        pytest.skip("Will be implemented in Phase 2")

    def test_concurrent_read_write_operations(self, populated_db):
        """Test database handles concurrent read/write correctly."""
        pytest.skip("Will be implemented in Phase 2")

    def test_migration_from_yaml_to_db(self, populated_db):
        """Test migrating translations from YAML language packs to database."""
        pytest.skip("Will be implemented in Phase 2")

    def test_export_translations_to_yaml(self, populated_db):
        """Test exporting database translations to YAML format."""
        pytest.skip("Will be implemented in Phase 2")
