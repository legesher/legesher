"""Unit tests for translation database (consolidated schema).

Tests the 4-table schema: terms, languages, translations, selected_translations.
See CORE-594 for migration details. Deferred tables (reviews, deep_contexts,
linguistic_standards) tracked in CORE-595.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from legesher_i18n.db.database import TranslationDatabase


@pytest.mark.unit
class TestTranslationDatabase:
    """Test TranslationDatabase core functionality."""

    @pytest.fixture
    def db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            db_instance = TranslationDatabase(db_path=db_path)
            yield db_instance
            db_instance.close()

    # ===========================
    # Database Initialization
    # ===========================

    def test_database_initialization(self, db):
        """Test that database and all 4 tables are created."""
        assert db is not None
        conn = db._get_connection()
        cursor = conn.cursor()

        # Verify all 4 tables exist
        for table in ("terms", "languages", "translations", "selected_translations"):
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            assert cursor.fetchone() is not None, f"Table '{table}' should exist"

    def test_database_wal_mode(self, db):
        """Test that WAL mode is enabled for concurrent access."""
        conn = db._get_connection()
        result = conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"

    def test_database_foreign_keys_enabled(self, db):
        """Test that foreign keys are enforced."""
        conn = db._get_connection()
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1

    def test_database_path_creation(self, db):
        """Test that database file is created at specified path."""
        assert hasattr(db, "db_path")
        assert Path(db.db_path).exists()

    def test_database_default_path(self):
        """Test that default path resolves to translations.db inside the package db directory."""
        expected_dir = Path(__file__).parent.parent.parent / "legesher_i18n" / "db"
        db = TranslationDatabase()
        try:
            assert Path(db.db_path).parent == expected_dir
            assert Path(db.db_path).name == "translations.db"
        finally:
            db.close()

    # ===========================
    # Term CRUD Tests
    # ===========================

    def test_get_or_create_term_creates_new(self, db):
        """Test creating a new term via get_or_create_term."""
        term_id = db.get_or_create_term(
            name="class",
            programming_language="python",
            category="keyword",
            subcategory="structure",
        )
        assert term_id > 0

    def test_get_or_create_term_returns_existing(self, db):
        """Test that get_or_create_term returns existing ID for duplicate."""
        id1 = db.get_or_create_term(
            name="def", programming_language="python", category="keyword"
        )
        id2 = db.get_or_create_term(
            name="def", programming_language="python", category="keyword"
        )
        assert id1 == id2

    def test_get_or_create_term_different_languages(self, db):
        """Test that same term name in different programming languages creates separate entries."""
        id_python = db.get_or_create_term(
            name="class", programming_language="python", category="keyword"
        )
        id_ts = db.get_or_create_term(
            name="class", programming_language="typescript", category="keyword"
        )
        assert id_python != id_ts

    def test_get_term_by_name(self, db):
        """Test retrieving a term by name."""
        db.get_or_create_term(
            name="return", programming_language="python", category="keyword"
        )

        term = db.get_term_by_name("return")
        assert term is not None
        assert term["name"] == "return"
        assert term["programming_language"] == "python"
        assert term["category"] == "keyword"
        assert "id" in term
        assert "created_at" in term

    def test_get_term_by_name_not_found(self, db):
        """Test that non-existent term returns None."""
        term = db.get_term_by_name("nonexistent_term")
        assert term is None

    def test_get_terms_all(self, db):
        """Test retrieving all terms."""
        db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )
        db.get_or_create_term(
            name="print", programming_language="python", category="builtin_func"
        )
        db.get_or_create_term(
            name="ValueError", programming_language="python", category="exception"
        )

        terms = db.get_terms()
        assert len(terms) == 3

    def test_get_terms_by_category(self, db):
        """Test filtering terms by category."""
        db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )
        db.get_or_create_term(
            name="for", programming_language="python", category="keyword"
        )
        db.get_or_create_term(
            name="print", programming_language="python", category="builtin_func"
        )

        keywords = db.get_terms(category="keyword")
        assert len(keywords) == 2
        assert all(t["category"] == "keyword" for t in keywords)

    def test_get_terms_by_programming_language(self, db):
        """Test filtering terms by programming language."""
        db.get_or_create_term(
            name="def", programming_language="python", category="keyword"
        )
        db.get_or_create_term(
            name="function", programming_language="typescript", category="keyword"
        )

        python_terms = db.get_terms(programming_language="python")
        assert len(python_terms) == 1
        assert python_terms[0]["name"] == "def"

    def test_term_unique_constraint(self, db):
        """Test that UNIQUE(name, programming_language) is enforced."""
        db.get_or_create_term(
            name="class", programming_language="python", category="keyword"
        )

        # Direct insert should fail
        conn = db._get_connection()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO terms (name, programming_language, category) VALUES (?, ?, ?)",
                ("class", "python", "keyword"),
            )

    # ===========================
    # Language Operations Tests
    # ===========================

    def test_get_language(self, db):
        """Test retrieving a language by code."""
        # Insert a language directly
        conn = db._get_connection()
        conn.execute(
            """INSERT INTO languages (code, name, native_name, direction, status)
               VALUES (?, ?, ?, ?, ?)""",
            ("es", "Spanish", "Español", "ltr", "experimental"),
        )
        conn.commit()

        lang = db.get_language("es")
        assert lang is not None
        assert lang["code"] == "es"
        assert lang["name"] == "Spanish"
        assert lang["native_name"] == "Español"
        assert lang["direction"] == "ltr"
        assert lang["status"] == "experimental"

    def test_get_language_not_found(self, db):
        """Test that non-existent language returns None."""
        lang = db.get_language("xx")
        assert lang is None

    def test_get_languages(self, db):
        """Test retrieving all languages."""
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name, has_yaml_pack) VALUES (?, ?, ?, ?)",
            ("es", "Spanish", "Español", 1),
        )
        conn.execute(
            "INSERT INTO languages (code, name, native_name, has_yaml_pack) VALUES (?, ?, ?, ?)",
            ("ar", "Arabic", "العربية", 1),
        )
        conn.execute(
            "INSERT INTO languages (code, name, native_name, has_yaml_pack) VALUES (?, ?, ?, ?)",
            ("bn", "Bengali", "বাংলা", 0),
        )
        conn.commit()

        all_langs = db.get_languages()
        assert len(all_langs) == 3

        with_packs = db.get_languages(has_yaml_pack=True)
        assert len(with_packs) == 2

        without_packs = db.get_languages(has_yaml_pack=False)
        assert len(without_packs) == 1
        assert without_packs[0]["code"] == "bn"

    # ===========================
    # Translation CRUD Tests
    # ===========================

    def test_add_translation(self, db):
        """Test adding a translation suggestion."""
        term_id = db.get_or_create_term(
            name="class", programming_language="python", category="keyword"
        )

        # Ensure the language exists
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        translation_id = db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="clase",
            source="community",
            word_type="noun",
            word_form="singular",
            confidence="high",
            model_rationale="Direct translation of 'class' as category",
            created_by="test_user",
        )

        assert translation_id > 0

    def test_add_multiple_translations_same_term(self, db):
        """Test that each model suggestion gets its own row."""
        term_id = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        id1 = db.add_translation(
            term_id=term_id, language_code="es", translation="si", source="community"
        )
        id2 = db.add_translation(
            term_id=term_id, language_code="es", translation="si", source="aya"
        )
        id3 = db.add_translation(
            term_id=term_id, language_code="es", translation="cuando", source="claude"
        )

        assert len({id1, id2, id3}) == 3

    def test_get_translations_by_term_id(self, db):
        """Test querying translations by term_id."""
        term_id = db.get_or_create_term(
            name="def", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("ar", "Arabic", "العربية"),
        )
        conn.commit()

        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="definir",
            source="community",
        )
        db.add_translation(
            term_id=term_id, language_code="ar", translation="عرّف", source="community"
        )

        results = db.get_translations(term_id=term_id)
        assert len(results) == 2

    def test_get_translations_by_language(self, db):
        """Test querying translations by language code."""
        id1 = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )
        id2 = db.get_or_create_term(
            name="for", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.add_translation(
            term_id=id1, language_code="es", translation="si", source="community"
        )
        db.add_translation(
            term_id=id2, language_code="es", translation="para", source="community"
        )

        results = db.get_translations(language_code="es")
        assert len(results) == 2
        assert all(r["language_code"] == "es" for r in results)

    def test_get_translations_by_source(self, db):
        """Test querying translations by source."""
        term_id = db.get_or_create_term(
            name="print", programming_language="python", category="builtin_func"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="imprimir",
            source="community",
        )
        db.add_translation(
            term_id=term_id, language_code="es", translation="imprimir", source="aya"
        )

        community = db.get_translations(source="community")
        assert len(community) == 1
        assert community[0]["source"] == "community"

    def test_get_translations_for_term_by_name(self, db):
        """Test get_translations_for_term convenience method."""
        term_id = db.get_or_create_term(
            name="return", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="retornar",
            source="community",
        )
        db.add_translation(
            term_id=term_id, language_code="es", translation="devolver", source="aya"
        )

        results = db.get_translations_for_term(term_name="return", language_code="es")
        assert len(results) == 2

    def test_get_translations_for_term_not_found(self, db):
        """Test get_translations_for_term returns empty for unknown term."""
        results = db.get_translations_for_term(
            term_name="nonexistent", language_code="es"
        )
        assert results == []

    def test_update_translation(self, db):
        """Test updating an existing translation."""
        term_id = db.get_or_create_term(
            name="continue", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        translation_id = db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="continuar",
            source="community",
            confidence="low",
        )

        updated = db.update_translation(
            translation_id,
            translation="seguir",
            confidence="high",
            word_type="verb",
            model_rationale="Updated based on community feedback",
        )
        assert updated is True

        # Verify updates
        results = db.get_translations(term_id=term_id, language_code="es")
        assert len(results) >= 1
        result = [r for r in results if r["id"] == translation_id][0]
        assert result["translation"] == "seguir"
        assert result["confidence"] == "high"
        assert result["word_type"] == "verb"
        assert result["model_rationale"] == "Updated based on community feedback"

    def test_delete_translation(self, db):
        """Test deleting a translation."""
        term_id = db.get_or_create_term(
            name="raise", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        translation_id = db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="levantar",
            source="community",
        )

        deleted = db.delete_translation(translation_id)
        assert deleted is True

        # Verify it's gone
        results = db.get_translations(term_id=term_id, language_code="es")
        assert len(results) == 0

    def test_delete_translation_not_found(self, db):
        """Test deleting non-existent translation returns False."""
        deleted = db.delete_translation(99999)
        assert deleted is False

    def test_translation_foreign_key_term(self, db):
        """Test that translations require valid term_id."""
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            db.add_translation(
                term_id=99999,
                language_code="es",
                translation="test",
                source="test",
            )

    def test_translation_foreign_key_language(self, db):
        """Test that translations require valid language_code."""
        term_id = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.add_translation(
                term_id=term_id,
                language_code="xx",  # non-existent language
                translation="test",
                source="test",
            )

    # ===========================
    # Selected Translations Tests
    # ===========================

    def test_set_selected(self, db):
        """Test setting a selected translation for a term+language pair."""
        term_id = db.get_or_create_term(
            name="def", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        result_id = db.set_selected(
            term_id=term_id,
            language_code="es",
            translation="definir",
            selected_by="pipeline",
            selection_reason="Highest confidence from Aya model",
        )
        assert result_id > 0

    def test_set_selected_replaces_existing(self, db):
        """Test that set_selected replaces previous selection (UNIQUE constraint)."""
        term_id = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.set_selected(term_id=term_id, language_code="es", translation="si")
        db.set_selected(term_id=term_id, language_code="es", translation="cuando")

        selected = db.get_selected(term_id=term_id, language_code="es")
        assert selected is not None
        assert selected["translation"] == "cuando"

    def test_get_selected(self, db):
        """Test retrieving selected translation by term_id + language."""
        term_id = db.get_or_create_term(
            name="for", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.set_selected(term_id=term_id, language_code="es", translation="para")

        selected = db.get_selected(term_id=term_id, language_code="es")
        assert selected is not None
        assert selected["translation"] == "para"
        assert selected["term_id"] == term_id
        assert selected["language_code"] == "es"

    def test_get_selected_not_found(self, db):
        """Test get_selected returns None when no selection exists."""
        selected = db.get_selected(term_id=99999, language_code="es")
        assert selected is None

    def test_get_selected_by_name(self, db):
        """Test get_selected_by_name convenience method."""
        term_id = db.get_or_create_term(
            name="while", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.set_selected(term_id=term_id, language_code="es", translation="mientras")

        selected = db.get_selected_by_name(term_name="while", language_code="es")
        assert selected is not None
        assert selected["translation"] == "mientras"

    def test_get_selected_by_name_not_found(self, db):
        """Test get_selected_by_name returns None for unknown term."""
        selected = db.get_selected_by_name(term_name="nonexistent", language_code="es")
        assert selected is None

    def test_get_all_selected(self, db):
        """Test retrieving all selected translations for a language."""
        id1 = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )
        id2 = db.get_or_create_term(
            name="for", programming_language="python", category="keyword"
        )
        id3 = db.get_or_create_term(
            name="print", programming_language="python", category="builtin_func"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.set_selected(term_id=id1, language_code="es", translation="si")
        db.set_selected(term_id=id2, language_code="es", translation="para")
        db.set_selected(term_id=id3, language_code="es", translation="imprimir")

        all_selected = db.get_all_selected(language_code="es")
        assert len(all_selected) == 3

    def test_remove_selected(self, db):
        """Test removing a selected translation."""
        term_id = db.get_or_create_term(
            name="class", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.set_selected(term_id=term_id, language_code="es", translation="clase")

        removed = db.remove_selected(term_id=term_id, language_code="es")
        assert removed is True

        # Verify it's gone
        selected = db.get_selected(term_id=term_id, language_code="es")
        assert selected is None

    def test_remove_selected_not_found(self, db):
        """Test removing non-existent selected translation returns False."""
        removed = db.remove_selected(term_id=99999, language_code="es")
        assert removed is False

    # ===========================
    # Cascade Delete Tests
    # ===========================

    def test_cascade_delete_translations_on_term_delete(self, db):
        """Test that deleting a term cascades to delete its translations."""
        term_id = db.get_or_create_term(
            name="lambda", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="lambda",
            source="community",
        )
        db.add_translation(
            term_id=term_id, language_code="es", translation="lambda", source="aya"
        )

        # Verify translations exist
        translations = db.get_translations(term_id=term_id)
        assert len(translations) == 2

        # Delete the term directly
        conn.execute("DELETE FROM terms WHERE id = ?", (term_id,))
        conn.commit()

        # Verify translations were cascade deleted
        translations_after = db.get_translations(term_id=term_id)
        assert len(translations_after) == 0

    def test_cascade_delete_selected_on_term_delete(self, db):
        """Test that deleting a term cascades to delete selected translations."""
        term_id = db.get_or_create_term(
            name="break", programming_language="python", category="keyword"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        db.set_selected(term_id=term_id, language_code="es", translation="romper")

        # Delete term
        conn.execute("DELETE FROM terms WHERE id = ?", (term_id,))
        conn.commit()

        # Verify selected was cascade deleted
        selected = db.get_selected(term_id=term_id, language_code="es")
        assert selected is None

    # ===========================
    # Stats Tests
    # ===========================

    def test_get_stats_empty(self, db):
        """Test get_stats on empty database."""
        stats = db.get_stats()
        assert stats["terms_count"] == 0
        assert stats["languages_count"] == 0
        assert stats["translations_count"] == 0
        assert stats["selected_translations_count"] == 0

    def test_get_stats_with_data(self, db):
        """Test get_stats with populated data."""
        id1 = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )
        id2 = db.get_or_create_term(
            name="print", programming_language="python", category="builtin_func"
        )

        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name, has_yaml_pack) VALUES (?, ?, ?, ?)",
            ("es", "Spanish", "Español", 1),
        )
        conn.execute(
            "INSERT INTO languages (code, name, native_name, has_yaml_pack) VALUES (?, ?, ?, ?)",
            ("ar", "Arabic", "العربية", 0),
        )
        conn.commit()

        db.add_translation(
            term_id=id1, language_code="es", translation="si", source="community"
        )
        db.add_translation(
            term_id=id2, language_code="es", translation="imprimir", source="aya"
        )
        db.set_selected(term_id=id1, language_code="es", translation="si")

        stats = db.get_stats()
        assert stats["terms_count"] == 2
        assert stats["languages_count"] == 2
        assert stats["languages_with_packs"] == 1
        assert stats["translations_count"] == 2
        assert stats["selected_translations_count"] == 1
        assert "terms_by_category" in stats
        assert stats["terms_by_category"]["keyword"] == 1
        assert stats["terms_by_category"]["builtin_func"] == 1

    # ===========================
    # Placeholder Tests (Phase 2)
    # ===========================

    def test_concurrent_access(self, db):
        """Test database handles concurrent access correctly."""
        pytest.skip("Will be implemented in Phase 2")

    def test_transaction_rollback(self, db):
        """Test transaction rollback on error."""
        pytest.skip("Will be implemented in Phase 2")

    def test_source_filtering(self, db):
        """Test filtering translations by source (community, aya, claude, etc)."""
        pytest.skip("Will be implemented in Phase 2")
