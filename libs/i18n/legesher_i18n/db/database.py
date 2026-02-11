"""Translation database for storing and managing translations.

This module provides the TranslationDatabase class for managing translation data
with the consolidated schema: terms, languages, translations, selected_translations.
"""

import logging
import sqlite3
import threading
from pathlib import Path

from .schema import get_schema

logger = logging.getLogger(__name__)


class TranslationDatabase:
    """
    SQLite-based database for translation storage with connection pooling.

    This database stores:
    - Terms: canonical list of reserved words (extensible across programming languages)
    - Languages: language registry with ISO standards and script metadata
    - Translations: one row per translation suggestion (per term, per language, per source)
    - Selected translations: which translation is currently active for YAML packs

    Features:
    - Thread-safe operations with connection pooling
    - WAL mode for better concurrent access
    - Automatic schema initialization
    - Foreign key support with cascading deletes

    Default storage location: libs/i18n/legesher_i18n/db/translations.db
    """

    def __init__(self, db_path: str | Path | None = None):
        """
        Initialize Translation Database.

        Args:
            db_path: Path to SQLite database file. Defaults to
                     libs/i18n/legesher_i18n/db/translations.db
        """
        if db_path is None:
            db_path = str(Path(__file__).parent / "translations.db")
        self.db_path = str(db_path)

        # Ensure directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Connection pooling: maintain persistent connection per thread
        self._local = threading.local()

        # Initialize database schema
        self._init_db()

    def __del__(self):
        """Clean up connections on deletion."""
        self.close()

    def close(self):
        """
        Close all thread-local database connections.

        Important on Windows to prevent file locking issues.
        Should be called when the database is no longer needed.
        """
        if hasattr(self, "_local") and hasattr(self._local, "conn"):
            if self._local.conn is not None:
                try:
                    self._local.conn.close()
                    self._local.conn = None
                    logger.debug(
                        f"Closed SQLite connection for thread {threading.current_thread().name}"
                    )
                except Exception as e:
                    logger.warning(f"Error closing SQLite connection: {e}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection for the current thread.

        Uses thread-local storage to maintain one connection per thread,
        providing connection pooling for high-frequency operations.

        Returns:
            SQLite connection for the current thread
        """
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=10.0
            )
            # Enable WAL mode for better concurrent access
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            # Enable foreign key support
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            logger.debug(
                f"Created new SQLite connection for thread {threading.current_thread().name}"
            )
        return self._local.conn

    def _init_db(self):
        """
        Initialize translation database with complete schema.

        Creates all required tables and indexes:
        - terms: canonical list of reserved words
        - languages: language registry
        - translations: translation suggestions
        - selected_translations: active translations for YAML packs
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys=ON")

        for statement in get_schema():
            conn.execute(statement)

        conn.commit()
        conn.close()

        logger.debug(f"Translation database initialized at {self.db_path}")

    # ===========================
    # Term Operations
    # ===========================

    def get_term_by_name(
        self,
        name: str,
        programming_language: str = "python",
    ) -> dict | None:
        """Get a term by its name and programming language.

        Args:
            name: The term name (e.g., "def", "print", "ValueError")
            programming_language: Programming language (default: "python")

        Returns:
            Dictionary with term fields, or None if not found
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            "SELECT * FROM terms WHERE name = ? AND programming_language = ?",
            (name, programming_language),
        )

        row = cursor.fetchone()
        conn.row_factory = None
        if row:
            return dict(row)
        return None

    def get_or_create_term(
        self,
        name: str,
        programming_language: str = "python",
        category: str = "unknown",
        subcategory: str | None = None,
    ) -> int:
        """Get existing term ID or create a new term.

        Args:
            name: The term name
            programming_language: Programming language (default: "python")
            category: Term category (used only if creating)
            subcategory: Term subcategory (used only if creating)

        Returns:
            The term ID
        """
        existing = self.get_term_by_name(name, programming_language)
        if existing:
            return existing["id"]

        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO terms (name, programming_language, category, subcategory)
            VALUES (?, ?, ?, ?)
            """,
            (name, programming_language, category, subcategory),
        )
        conn.commit()
        term_id: int = cursor.lastrowid  # type: ignore[assignment]
        logger.debug(
            f"Created term '{name}' ({programming_language}) with ID {term_id}"
        )
        return term_id

    def get_terms(
        self,
        programming_language: str | None = None,
        category: str | None = None,
    ) -> list[dict]:
        """Get terms with optional filters.

        Args:
            programming_language: Filter by programming language
            category: Filter by category

        Returns:
            List of term dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM terms WHERE 1=1"
        params: list = []

        if programming_language is not None:
            query += " AND programming_language = ?"
            params.append(programming_language)

        if category is not None:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY name"
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.row_factory = None
        return [dict(row) for row in rows]

    # ===========================
    # Language Operations
    # ===========================

    def get_language(self, code: str) -> dict | None:
        """Get a language by its code.

        Args:
            code: ISO 639-1 language code (e.g., "es", "ar")

        Returns:
            Dictionary with language fields, or None if not found
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM languages WHERE code = ?", (code,))
        row = cursor.fetchone()
        conn.row_factory = None
        if row:
            return dict(row)
        return None

    def get_languages(self, has_yaml_pack: bool | None = None) -> list[dict]:
        """Get all languages with optional filter.

        Args:
            has_yaml_pack: If set, filter by whether language has a YAML pack

        Returns:
            List of language dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM languages WHERE 1=1"
        params: list = []

        if has_yaml_pack is not None:
            query += " AND has_yaml_pack = ?"
            params.append(1 if has_yaml_pack else 0)

        query += " ORDER BY code"
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.row_factory = None
        return [dict(row) for row in rows]

    # ===========================
    # Translation CRUD Operations
    # ===========================

    def add_translation(
        self,
        term_id: int,
        language_code: str,
        translation: str,
        source: str,
        model_version: str | None = None,
        word_type: str | None = None,
        word_form: str | None = None,
        confidence: str | None = None,
        model_rationale: str | None = None,
        created_by: str | None = None,
    ) -> int:
        """Add a translation suggestion to the database.

        Each distinct suggestion gets its own row. If a model returns 3
        different options for "True" in Russian, that's 3 rows. Duplicate
        suggestions (same term_id, language_code, source, translation) are
        silently ignored.

        Args:
            term_id: Foreign key to terms table
            language_code: Target language code (e.g., 'es', 'ar', 'zh')
            translation: The translated term
            source: Source of translation (e.g., 'aya', 'community', 'anthropic')
            model_version: Optional model version (e.g., 'aya-101', 'claude-3.5-sonnet')
            word_type: Optional grammatical word type
            word_form: Optional word form variation
            confidence: Optional confidence level (high, medium, low)
            model_rationale: Optional AI model reasoning for translation
            created_by: Optional creator identifier

        Returns:
            The translation ID, or 0 if the suggestion already existed
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO translations (
                term_id, language_code, translation, source,
                model_version, word_type, word_form, confidence,
                model_rationale, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                term_id,
                language_code,
                translation,
                source,
                model_version,
                word_type,
                word_form,
                confidence,
                model_rationale,
                created_by,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            logger.debug(
                f"Duplicate translation skipped: term_id={term_id} -> {translation} "
                f"({language_code}, source: {source})"
            )
            return 0

        translation_id: int = cursor.lastrowid  # type: ignore[assignment]
        logger.debug(
            f"Added translation: term_id={term_id} -> {translation} "
            f"({language_code}, source: {source}, id: {translation_id})"
        )
        return translation_id

    def get_translations(
        self,
        term_id: int | None = None,
        language_code: str | None = None,
        source: str | None = None,
    ) -> list[dict]:
        """Query translations with optional filters.

        All parameters are optional. Provide any combination to filter results.

        Args:
            term_id: Filter by term ID
            language_code: Filter by target language code
            source: Filter by translation source

        Returns:
            List of translation dictionaries matching filters
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM translations WHERE 1=1"
        params: list = []

        if term_id is not None:
            query += " AND term_id = ?"
            params.append(term_id)

        if language_code is not None:
            query += " AND language_code = ?"
            params.append(language_code)

        if source is not None:
            query += " AND source = ?"
            params.append(source)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.row_factory = None
        return [dict(row) for row in rows]

    def get_translations_joined(
        self,
        language_code: str | None = None,
        source: str | None = None,
    ) -> list[dict]:
        """Query translations joined with term info.

        Returns translation rows enriched with term name and category,
        useful for export workflows that need term metadata.

        Args:
            language_code: Filter by target language code
            source: Filter by translation source

        Returns:
            List of dicts with translation fields plus 'term' and 'term_type' keys
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        query = """
            SELECT t.*, terms.name AS term, terms.category AS term_type
            FROM translations t
            JOIN terms ON t.term_id = terms.id
            WHERE 1=1
        """
        params: list = []

        if language_code is not None:
            query += " AND t.language_code = ?"
            params.append(language_code)

        if source is not None:
            query += " AND t.source = ?"
            params.append(source)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.row_factory = None
        return [dict(row) for row in rows]

    def get_translations_for_term(
        self,
        term_name: str,
        language_code: str,
        programming_language: str = "python",
    ) -> list[dict]:
        """Get all translation suggestions for a term+language combination.

        Convenience method that looks up the term by name first.

        Args:
            term_name: The term name (e.g., "def", "print")
            language_code: Target language code
            programming_language: Programming language (default: "python")

        Returns:
            List of translation dictionaries (all suggestions from all sources)
        """
        term = self.get_term_by_name(term_name, programming_language)
        if term is None:
            return []
        return self.get_translations(term_id=term["id"], language_code=language_code)

    def update_translation(
        self,
        translation_id: int,
        **fields,
    ) -> bool:
        """Update a translation by ID.

        Accepts any valid translation field as a keyword argument.
        Automatically updates the updated_at timestamp.

        Args:
            translation_id: The translation ID to update
            **fields: Field names and values to update

        Returns:
            True if translation was updated, False if not found
        """
        if not fields:
            logger.warning("No fields provided to update_translation")
            return False

        valid_fields = {
            "term_id",
            "language_code",
            "translation",
            "source",
            "model_version",
            "word_type",
            "word_form",
            "confidence",
            "model_rationale",
            "created_by",
        }

        update_fields = {k: v for k, v in fields.items() if k in valid_fields}

        if not update_fields:
            logger.warning("No valid fields provided to update_translation")
            return False

        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        set_clause += ", updated_at = datetime('now')"

        query = f"UPDATE translations SET {set_clause} WHERE id = ?"
        params = list(update_fields.values()) + [translation_id]

        conn = self._get_connection()
        cursor = conn.execute(query, params)
        conn.commit()

        if cursor.rowcount > 0:
            logger.debug(
                f"Updated translation {translation_id}: {list(update_fields.keys())}"
            )
            return True
        else:
            logger.debug(f"Translation {translation_id} not found for update")
            return False

    def delete_translation(self, translation_id: int) -> bool:
        """Delete a translation by ID.

        Args:
            translation_id: The translation ID to delete

        Returns:
            True if translation was deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM translations WHERE id = ?", (translation_id,)
        )
        conn.commit()

        if cursor.rowcount > 0:
            logger.debug(f"Deleted translation {translation_id}")
            return True
        else:
            logger.debug(f"Translation {translation_id} not found for deletion")
            return False

    # ===========================
    # Selected Translation Operations
    # ===========================

    def get_selected(
        self,
        term_id: int,
        language_code: str,
    ) -> dict | None:
        """Get the selected (active) translation for a term+language.

        Args:
            term_id: The term ID
            language_code: Target language code

        Returns:
            Dictionary with selected translation fields, or None if not found
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT st.*, t.name as term_name, t.category as term_category
            FROM selected_translations st
            JOIN terms t ON t.id = st.term_id
            WHERE st.term_id = ? AND st.language_code = ?
            """,
            (term_id, language_code),
        )

        row = cursor.fetchone()
        conn.row_factory = None
        if row:
            return dict(row)
        return None

    def get_selected_by_name(
        self,
        term_name: str,
        language_code: str,
        programming_language: str = "python",
    ) -> dict | None:
        """Get the selected translation for a term by name.

        Convenience method that looks up the term by name first.

        Args:
            term_name: The term name (e.g., "def", "print")
            language_code: Target language code
            programming_language: Programming language (default: "python")

        Returns:
            Dictionary with selected translation fields, or None if not found
        """
        term = self.get_term_by_name(term_name, programming_language)
        if term is None:
            return None
        return self.get_selected(term["id"], language_code)

    def set_selected(
        self,
        term_id: int,
        language_code: str,
        translation: str,
        selected_by: str | None = None,
        selection_reason: str | None = None,
    ) -> int:
        """Set or update the selected translation for a term+language.

        Uses INSERT OR REPLACE to ensure exactly one selection per term+language.

        Args:
            term_id: The term ID
            language_code: Target language code
            translation: The chosen translation text
            selected_by: Who/what made the selection
            selection_reason: Why this translation was chosen

        Returns:
            The selected_translation ID
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT OR REPLACE INTO selected_translations (
                term_id, language_code, translation,
                selected_by, selection_reason
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (term_id, language_code, translation, selected_by, selection_reason),
        )
        conn.commit()

        row_id: int = cursor.lastrowid  # type: ignore[assignment]
        logger.debug(
            f"Set selected translation: term_id={term_id}, "
            f"lang={language_code} -> {translation}"
        )
        return row_id

    def get_all_selected(
        self,
        language_code: str | None = None,
        category: str | None = None,
    ) -> list[dict]:
        """Get all selected translations with optional filters.

        Args:
            language_code: Filter by target language code
            category: Filter by term category (e.g., "keyword", "builtin_func")

        Returns:
            List of selected translation dictionaries with joined term info
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        query = """
            SELECT st.*, t.name as term_name, t.category as term_category,
                   t.subcategory as term_subcategory,
                   t.programming_language
            FROM selected_translations st
            JOIN terms t ON t.id = st.term_id
            WHERE 1=1
        """
        params: list = []

        if language_code is not None:
            query += " AND st.language_code = ?"
            params.append(language_code)

        if category is not None:
            query += " AND t.category = ?"
            params.append(category)

        query += " ORDER BY t.name"
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.row_factory = None
        return [dict(row) for row in rows]

    def remove_selected(self, term_id: int, language_code: str) -> bool:
        """Remove the selected translation for a term+language.

        Args:
            term_id: The term ID
            language_code: Target language code

        Returns:
            True if removed, False if not found
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "DELETE FROM selected_translations WHERE term_id = ? AND language_code = ?",
            (term_id, language_code),
        )
        conn.commit()
        return cursor.rowcount > 0

    # ===========================
    # Statistics
    # ===========================

    def get_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dictionary with counts for each table and breakdowns
        """
        conn = self._get_connection()

        stats: dict = {}
        for table in ("terms", "languages", "translations", "selected_translations"):
            stats[f"{table}_count"] = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

        stats["languages_with_packs"] = conn.execute(
            "SELECT COUNT(*) FROM languages WHERE has_yaml_pack = 1"
        ).fetchone()[0]

        rows = conn.execute(
            "SELECT source, COUNT(*) FROM translations GROUP BY source"
        ).fetchall()
        stats["translations_by_source"] = {row[0]: row[1] for row in rows}

        rows = conn.execute(
            "SELECT category, COUNT(*) FROM terms GROUP BY category"
        ).fetchall()
        stats["terms_by_category"] = {row[0]: row[1] for row in rows}

        return stats
