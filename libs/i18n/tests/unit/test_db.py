"""Unit tests for translation database (consolidated schema).

Tests the 4-table schema: terms, languages, translations, selected_translations.
See CORE-594 for migration details. Deferred tables (reviews, deep_contexts,
linguistic_standards) tracked in CORE-595.
"""

import sqlite3
import tempfile
import threading
from pathlib import Path

import pytest

import legesher_i18n.db.database as database_module
from legesher_i18n.db.database import (
    TranslationDatabase,
    _running_from_source_checkout,
    default_db_path,
)


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

    def test_context_manager_closes_connections(self):
        """CORE-610: leaving a ``with`` block closes the database connections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            with TranslationDatabase(db_path=db_path) as db:
                conn = db._get_connection()
                conn.execute("SELECT 1")

            with pytest.raises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")

    def test_close_closes_other_threads_connections(self):
        """CORE-610: close() releases connections opened by other threads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            db = TranslationDatabase(db_path=db_path)

            worker_connections: list[sqlite3.Connection] = []

            def open_connection():
                worker_connections.append(db._get_connection())

            thread = threading.Thread(target=open_connection)
            thread.start()
            thread.join()

            main_conn = db._get_connection()
            assert len(worker_connections) == 1
            assert worker_connections[0] is not main_conn

            db.close()

            for conn in (*worker_connections, main_conn):
                with pytest.raises(sqlite3.ProgrammingError):
                    conn.execute("SELECT 1")

    def test_close_is_idempotent(self):
        """CORE-610: calling close() twice is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            db = TranslationDatabase(db_path=db_path)
            db._get_connection()
            db.close()
            db.close()  # must not raise

    def test_get_connection_after_close_raises(self):
        """CORE-610: a closed database refuses to open new connections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            db = TranslationDatabase(db_path=db_path)
            db._get_connection()
            db.close()

            with pytest.raises(RuntimeError, match="closed"):
                db._get_connection()

    def test_concurrent_close_and_connect_does_not_leak(self):
        """CORE-610: close() racing _get_connection() never leaks a connection.

        Every connection a worker obtains must end up closed: either it was
        registered before close() swapped the tracking list (so close()
        sweeps it), or _get_connection() saw the closed flag, closed the
        fresh connection itself, and raised. Bounded iteration count — this
        is a race-shape check, not a stress test.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            for _ in range(10):
                db = TranslationDatabase(db_path=db_path)
                obtained: list[sqlite3.Connection] = []
                barrier = threading.Barrier(3)

                def open_connection():
                    barrier.wait()
                    try:
                        obtained.append(db._get_connection())
                    except RuntimeError:
                        pass  # lost the race to close() — expected

                def close_db():
                    barrier.wait()
                    db.close()

                threads = [
                    threading.Thread(target=open_connection),
                    threading.Thread(target=open_connection),
                    threading.Thread(target=close_db),
                ]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

                # No connection may remain registered or usable.
                assert db._connections == []
                for conn in obtained:
                    with pytest.raises(sqlite3.ProgrammingError):
                        conn.execute("SELECT 1")

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

    # ===========================
    # Collision Detection Tests (CORE-605)
    # ===========================

    def _setup_collision_fixture(self, db):
        """Helper: create two terms with the same selected translation in 'es'."""
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        id1 = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )
        id2 = db.get_or_create_term(
            name="elif", programming_language="python", category="keyword"
        )
        return id1, id2

    def test_find_collisions_empty(self, db):
        """Test that a clean database has no collisions."""
        collisions = db.find_collisions()
        assert collisions == []

    def test_find_collisions_detects_collision(self, db):
        """Test that two terms with the same selected translation are detected."""
        id1, id2 = self._setup_collision_fixture(db)

        # Both terms select the same translation "si"
        db.set_selected(
            term_id=id1, language_code="es", translation="si", allow_collision=True
        )
        db.set_selected(
            term_id=id2, language_code="es", translation="si", allow_collision=True
        )

        collisions = db.find_collisions()
        assert len(collisions) == 1
        assert collisions[0]["translation"] == "si"
        assert collisions[0]["language_code"] == "es"
        assert len(collisions[0]["terms"]) == 2
        term_names = {t["term_name"] for t in collisions[0]["terms"]}
        assert term_names == {"if", "elif"}

    def test_find_collisions_three_way(self, db):
        """Test detection of a three-way collision."""
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("hi", "Hindi", "हिन्दी"),
        )
        conn.commit()

        id1 = db.get_or_create_term(
            name="assert", programming_language="python", category="keyword"
        )
        id2 = db.get_or_create_term(
            name="def", programming_language="python", category="keyword"
        )
        id3 = db.get_or_create_term(
            name="vars", programming_language="python", category="builtin_func"
        )

        for tid in (id1, id2, id3):
            db.set_selected(
                term_id=tid,
                language_code="hi",
                translation="same",
                allow_collision=True,
            )

        collisions = db.find_collisions()
        assert len(collisions) == 1
        assert len(collisions[0]["terms"]) == 3

    def test_find_collisions_filter_by_language(self, db):
        """Test that language filter returns only collisions for that language."""
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("fi", "Finnish", "Suomi"),
        )
        conn.commit()

        id1 = db.get_or_create_term(
            name="and", programming_language="python", category="keyword"
        )
        id2 = db.get_or_create_term(
            name="or", programming_language="python", category="keyword"
        )
        id3 = db.get_or_create_term(
            name="if", programming_language="python", category="keyword"
        )
        id4 = db.get_or_create_term(
            name="elif", programming_language="python", category="keyword"
        )

        # Finnish collision: "ja" for and + or
        db.set_selected(
            term_id=id1, language_code="fi", translation="ja", allow_collision=True
        )
        db.set_selected(
            term_id=id2, language_code="fi", translation="ja", allow_collision=True
        )
        # Spanish collision: "si" for if + elif
        db.set_selected(
            term_id=id3, language_code="es", translation="si", allow_collision=True
        )
        db.set_selected(
            term_id=id4, language_code="es", translation="si", allow_collision=True
        )

        # Filter by Finnish
        fi_collisions = db.find_collisions(language_code="fi")
        assert len(fi_collisions) == 1
        assert fi_collisions[0]["language_code"] == "fi"

        # Filter by Spanish
        es_collisions = db.find_collisions(language_code="es")
        assert len(es_collisions) == 1
        assert es_collisions[0]["language_code"] == "es"

        # All collisions
        all_collisions = db.find_collisions()
        assert len(all_collisions) == 2

    def test_find_collisions_scoped_by_programming_language(self, db):
        """Test that Python and TypeScript terms sharing a translation don't collide."""
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

        py_id = db.get_or_create_term(
            name="def", programming_language="python", category="keyword"
        )
        ts_id = db.get_or_create_term(
            name="function", programming_language="typescript", category="keyword"
        )

        # Same translation for different programming languages
        db.set_selected(
            term_id=py_id,
            language_code="es",
            translation="definir",
            allow_collision=True,
        )
        db.set_selected(
            term_id=ts_id,
            language_code="es",
            translation="definir",
            allow_collision=True,
        )

        # Should NOT be a collision within Python scope
        py_collisions = db.find_collisions(programming_language="python")
        assert len(py_collisions) == 0

        # Should NOT be a collision within TypeScript scope
        ts_collisions = db.find_collisions(programming_language="typescript")
        assert len(ts_collisions) == 0

    def test_set_selected_rejects_collision(self, db):
        """Test that set_selected raises ValueError on collision by default."""
        id1, id2 = self._setup_collision_fixture(db)

        db.set_selected(term_id=id1, language_code="es", translation="si")

        with pytest.raises(ValueError, match="Collision"):
            db.set_selected(term_id=id2, language_code="es", translation="si")

    def test_set_selected_allows_collision_flag(self, db):
        """Test that allow_collision=True bypasses the collision check."""
        id1, id2 = self._setup_collision_fixture(db)

        db.set_selected(term_id=id1, language_code="es", translation="si")

        # Should NOT raise
        result_id = db.set_selected(
            term_id=id2, language_code="es", translation="si", allow_collision=True
        )
        assert result_id > 0

    def test_set_selected_replacing_own_translation_no_false_positive(self, db):
        """Test that updating a term's own translation doesn't trigger collision."""
        id1, _ = self._setup_collision_fixture(db)

        db.set_selected(term_id=id1, language_code="es", translation="si")

        # Updating the same term to the same translation should NOT raise
        result_id = db.set_selected(term_id=id1, language_code="es", translation="si")
        assert result_id > 0


@pytest.mark.unit
class TestTermCategoryValidation:
    """get_or_create_term rejects unknown categories (CORE-710).

    SQLite accepts any string in the category column. Without runtime
    validation, a typo (`reserved_words`, `reservedword`) would silently
    insert a ghost row that no consumer can find via the documented
    categories. This pins the validation behavior.
    """

    def _make_db(self):
        """Build a fresh on-disk DB for isolation."""
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        return TranslationDatabase(db_path=Path(tmp.name)), Path(tmp.name)

    def test_canonical_categories_accepted(self):
        """All canonical TermCategory values are accepted."""
        db, path = self._make_db()
        try:
            for cat in (
                "keyword",
                "builtin_func",
                "builtin_type",
                "exception",
                "special_constant",
                "reserved_word",
                "helper",
                "unknown",
            ):
                tid = db.get_or_create_term(f"term_{cat}", "python", cat)
                assert tid > 0
        finally:
            path.unlink()

    def test_typo_reserved_words_plural_rejected(self):
        """The exact typo from review feedback (reserved_words plural)."""
        db, path = self._make_db()
        try:
            with pytest.raises(ValueError, match="Unknown term category"):
                db.get_or_create_term("test_term", "python", "reserved_words")
        finally:
            path.unlink()

    def test_typo_reservedword_no_underscore_rejected(self):
        """Plausible typo (no underscore)."""
        db, path = self._make_db()
        try:
            with pytest.raises(ValueError, match="Unknown term category"):
                db.get_or_create_term("test_term2", "python", "reservedword")
        finally:
            path.unlink()

    def test_completely_unknown_category_rejected(self):
        """Random unknown values are rejected, not silently stored."""
        db, path = self._make_db()
        try:
            with pytest.raises(ValueError, match="Unknown term category"):
                db.get_or_create_term("test_term3", "python", "totally_made_up")
        finally:
            path.unlink()

    def test_error_message_lists_valid_options(self):
        """Error message names the valid categories so callers can fix."""
        db, path = self._make_db()
        try:
            with pytest.raises(ValueError) as exc_info:
                db.get_or_create_term("test_term4", "python", "wrong")
            msg = str(exc_info.value)
            # Each canonical category name appears in the message
            for cat in ("keyword", "reserved_word", "exception", "unknown"):
                assert cat in msg
        finally:
            path.unlink()


@pytest.mark.unit
class TestAmbiguousTermResolution:
    """get_or_create_term resolves same-name terms by category (CORE-1400).

    'type' holds two pack slots — the builtin and the 3.12 soft keyword —
    and the two may carry different translations in a language. Before this
    fix, category-aware lookup was gated on ``allow_duplicate_name``, so an
    explicit ``category=`` was ignored and the lowest-id row (the builtin)
    came back for every caller. Translations for the soft keyword were then
    filed against the builtin, silently.
    """

    @pytest.fixture
    def db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_translations.db")
            db_instance = TranslationDatabase(db_path=db_path)
            yield db_instance
            db_instance.close()

    @pytest.fixture
    def spanish(self, db):
        """Register 'es' so translation rows satisfy the language FK."""
        conn = db._get_connection()
        conn.execute(
            "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
            ("es", "Spanish", "Español"),
        )
        conn.commit()

    @pytest.fixture
    def dual_type(self, db):
        """The two 'type' rows, as the real database holds them."""
        builtin_id = db.get_or_create_term("type", "python", "builtin_type")
        keyword_id = db.get_or_create_term(
            "type",
            "python",
            "keyword",
            subcategory="soft_keyword",
            allow_duplicate_name=True,
        )
        assert builtin_id != keyword_id
        return builtin_id, keyword_id

    def test_explicit_category_resolves_duplicated_name(self, db, dual_type):
        """The bug: category= must select the row, not be ignored."""
        builtin_id, keyword_id = dual_type

        assert db.get_or_create_term("type", "python", "keyword") == keyword_id
        assert db.get_or_create_term("type", "python", "builtin_type") == builtin_id

    def test_explicit_category_agrees_with_get_term_by_name(self, db, dual_type):
        """get_or_create_term and get_term_by_name must not disagree."""
        for category in ("keyword", "builtin_type"):
            by_name = db.get_term_by_name("type", "python", category=category)
            assert by_name is not None
            assert db.get_or_create_term("type", "python", category) == by_name["id"]

    def test_resolution_does_not_create_a_third_row(self, db, dual_type):
        """Resolving by category reuses a row; it never inserts one."""
        db.get_or_create_term("type", "python", "keyword")
        db.get_or_create_term("type", "python", "builtin_type")

        assert len(db.get_terms(programming_language="python")) == 2

    def test_ambiguous_name_without_category_raises(self, db, dual_type):
        """Silently returning the first row is the bug class, not a fallback."""
        with pytest.raises(ValueError, match="ambiguous"):
            db.get_or_create_term("type", "python")

    def test_ambiguous_error_names_the_candidate_rows(self, db, dual_type):
        """The error has to tell the caller which categories exist."""
        builtin_id, keyword_id = dual_type

        with pytest.raises(ValueError) as exc_info:
            db.get_or_create_term("type", "python")

        msg = str(exc_info.value)
        assert "builtin_type" in msg
        assert "keyword" in msg
        assert str(builtin_id) in msg
        assert str(keyword_id) in msg

    def test_ambiguous_name_with_category_matching_no_row_raises(self, db, dual_type):
        """A category matching no row cannot silently fall back to one.

        The category asked for here is one no pack section maps onto
        'type'. This test used to ask for 'builtin_func' — the literal
        call ``import_yaml_to_db`` made for every pack's ``builtins.type``
        slot — and so asserted that dropping 50 shipped pack values was
        the intended behavior. The importer now resolves a section
        against ``YAML_SECTION_CATEGORIES`` in order and lands on the
        ``builtin_type`` row; see
        ``tests/translate/test_import_yaml_to_db.py``.
        """
        with pytest.raises(ValueError, match="ambiguous"):
            db.get_or_create_term("type", "python", "exception")

    def test_allow_duplicate_name_still_creates_the_second_slot(self, db):
        """The flag's own behavior is unchanged."""
        builtin_id = db.get_or_create_term("type", "python", "builtin_type")
        keyword_id = db.get_or_create_term(
            "type", "python", "keyword", allow_duplicate_name=True
        )
        assert keyword_id != builtin_id
        # Re-running is idempotent, not a third row.
        assert (
            db.get_or_create_term(
                "type", "python", "keyword", allow_duplicate_name=True
            )
            == keyword_id
        )

    def test_unambiguous_name_unaffected(self, db):
        """The common case keeps returning the existing row."""
        term_id = db.get_or_create_term("def", "python", "keyword")

        assert db.get_or_create_term("def", "python", "keyword") == term_id
        assert db.get_or_create_term("def", "python") == term_id

    def test_unambiguous_name_with_mismatched_category_reuses_row(self, db):
        """Callers derive categories from lossy sources (YAML sections).

        A single-row name has no wrong row to return, so a mismatch must
        not raise and must not insert a duplicate.
        """
        term_id = db.get_or_create_term("str", "python", "builtin_type")

        assert db.get_or_create_term("str", "python", "builtin_func") == term_id
        assert len(db.get_terms(programming_language="python")) == 1

    def test_same_name_other_programming_language_is_not_ambiguous(self, db, dual_type):
        """Ambiguity is scoped to one programming language."""
        ts_id = db.get_or_create_term("type", "typescript", "keyword")

        assert db.get_or_create_term("type", "typescript") == ts_id

    def test_translations_resolve_per_category(self, db, spanish, dual_type):
        """End-to-end: the two slots keep separate translation pools."""
        builtin_id, keyword_id = dual_type
        db.add_translation(
            term_id=builtin_id,
            language_code="es",
            translation="tipo",
            source="test",
        )
        db.add_translation(
            term_id=keyword_id,
            language_code="es",
            translation="alias",
            source="test",
        )

        keyword_hits = db.get_translations_for_term(
            term_name="type", language_code="es", category="keyword"
        )
        builtin_hits = db.get_translations_for_term(
            term_name="type", language_code="es", category="builtin_type"
        )
        assert [t["translation"] for t in keyword_hits] == ["alias"]
        assert [t["translation"] for t in builtin_hits] == ["tipo"]

    def test_selected_resolves_per_category(self, db, spanish, dual_type):
        """get_selected_by_name honors the category passthrough."""
        builtin_id, keyword_id = dual_type
        db.set_selected(term_id=builtin_id, language_code="es", translation="tipo")
        db.set_selected(term_id=keyword_id, language_code="es", translation="alias")

        keyword_selected = db.get_selected_by_name(
            term_name="type", language_code="es", category="keyword"
        )
        builtin_selected = db.get_selected_by_name(
            term_name="type", language_code="es", category="builtin_type"
        )
        assert keyword_selected is not None
        assert builtin_selected is not None
        assert keyword_selected["translation"] == "alias"
        assert builtin_selected["translation"] == "tipo"

    def test_convenience_lookups_without_category_unchanged(self, db, spanish):
        """Omitting category keeps the documented lowest-id behavior."""
        term_id = db.get_or_create_term("while", "python", "keyword")
        db.add_translation(
            term_id=term_id,
            language_code="es",
            translation="mientras",
            source="test",
        )
        db.set_selected(term_id=term_id, language_code="es", translation="mientras")

        translations = db.get_translations_for_term(
            term_name="while", language_code="es"
        )
        selected = db.get_selected_by_name(term_name="while", language_code="es")
        assert [t["translation"] for t in translations] == ["mientras"]
        assert selected is not None
        assert selected["translation"] == "mientras"


@pytest.mark.unit
class TestDefaultDbPath:
    """CORE-601: default db_path resolution must never target site-packages."""

    def test_source_checkout_uses_packaged_path(self, monkeypatch):
        """Source checkouts / editable installs keep the in-repo database."""
        monkeypatch.setattr(
            database_module, "_running_from_source_checkout", lambda: True
        )
        packaged_dir = Path(database_module.__file__).parent
        assert default_db_path() == packaged_dir / "translations.db"

    def test_installed_environment_falls_back_to_user_dir(self, monkeypatch, tmp_path):
        """Installed environments resolve to ~/.legesher/translations.db."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr(
            database_module, "_running_from_source_checkout", lambda: False
        )
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        result = default_db_path()

        assert result == fake_home / ".legesher" / "translations.db"
        # Seeded once from the bundled database shipped with the package
        packaged = Path(database_module.__file__).parent / "translations.db"
        if packaged.exists():
            assert result.exists()
            assert result.stat().st_size == packaged.stat().st_size

    def test_installed_environment_does_not_reseed_existing_user_db(
        self, monkeypatch, tmp_path
    ):
        """An existing user database is never overwritten by the seed copy."""
        fake_home = tmp_path / "home"
        user_db = fake_home / ".legesher" / "translations.db"
        user_db.parent.mkdir(parents=True)
        user_db.write_bytes(b"sentinel")
        monkeypatch.setattr(
            database_module, "_running_from_source_checkout", lambda: False
        )
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        result = default_db_path()

        assert result == user_db
        assert user_db.read_bytes() == b"sentinel"


@pytest.mark.unit
class TestRunningFromSourceCheckout:
    """CORE-601: install-location detection uses exact path components."""

    def test_real_module_location_is_source_checkout(self):
        """The test suite itself runs from the repo checkout."""
        assert _running_from_source_checkout() is True

    def test_site_packages_is_not_source_checkout(self, tmp_path):
        module_path = (
            tmp_path
            / "venv"
            / "lib"
            / "python3.12"
            / "site-packages"
            / "legesher_i18n"
            / "db"
            / "database.py"
        )
        assert _running_from_source_checkout(module_path) is False

    def test_dist_packages_is_not_source_checkout(self, tmp_path):
        module_path = (
            tmp_path
            / "usr"
            / "lib"
            / "python3"
            / "dist-packages"
            / "legesher_i18n"
            / "db"
            / "database.py"
        )
        assert _running_from_source_checkout(module_path) is False

    def test_substring_match_does_not_false_positive(self, tmp_path):
        """A directory merely containing 'site-packages' in its name is fine."""
        checkout = tmp_path / "my-site-packages-fork"
        module_dir = checkout / "libs" / "i18n" / "legesher_i18n" / "db"
        module_dir.mkdir(parents=True)
        (checkout / "libs" / "i18n" / "pyproject.toml").write_text("[project]\n")
        module_path = module_dir / "database.py"
        assert _running_from_source_checkout(module_path) is True

    def test_no_repo_marker_is_not_source_checkout(self, tmp_path):
        """Without a pyproject.toml above the module, treat it as installed."""
        module_dir = tmp_path / "somewhere" / "legesher_i18n" / "db"
        module_dir.mkdir(parents=True)
        module_path = module_dir / "database.py"
        assert _running_from_source_checkout(module_path) is False
