"""Translation database for storing and managing translations with community reviews.

This module provides the TranslationDatabase class for managing translation data,
including translations, reviews, deep contexts, and linguistic standards.
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
    - Core translations with metadata and confidence scores
    - Community reviews and feedback on translations
    - Deep contexts and etymology for programming terms
    - Linguistic standards and guidelines per language

    Features:
    - Thread-safe operations with connection pooling
    - WAL mode for better concurrent access
    - Automatic schema initialization
    - Foreign key support with cascading deletes

    Default storage location: .legesher/translations.db
    """

    def __init__(self, db_path: str = ".legesher/translations.db"):
        """
        Initialize Translation Database.

        Args:
            db_path: Path to SQLite database file (default: .legesher/translations.db)
        """
        self.db_path = db_path

        # Ensure directory exists
        db_dir = Path(db_path).parent
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
        - translations: Core translation data
        - reviews: Community feedback
        - deep_contexts: Etymology and explanations
        - linguistic_standards: Language-specific guidelines

        Indexes are created for optimized lookups.
        """
        conn = sqlite3.connect(self.db_path)

        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys=ON")

        # Get all schema statements
        schema_statements = get_schema()

        # Execute each statement
        for statement in schema_statements:
            conn.execute(statement)

        conn.commit()
        conn.close()

        logger.debug(f"Translation database initialized at {self.db_path}")

    # ===========================
    # Deep Context CRUD Operations
    # ===========================

    def add_deep_context(
        self,
        term: str,
        term_type: str,
        etymology: str | None = None,
        explanation_simple: str | None = None,
        explanation_beginner: str | None = None,
        explanation_intermediate: str | None = None,
        explanation_expert: str | None = None,
        concept_agnostic: str | None = None,
        translation_guidance: str | None = None,
    ) -> int:
        """Add deep context for a term.

        Args:
            term: The programming term (e.g., "class", "def")
            term_type: Type of term (keyword, builtin, etc.)
            etymology: Origin and history of the term
            explanation_simple: Simple explanation for non-programmers
            explanation_beginner: Explanation for beginner programmers
            explanation_intermediate: Explanation for intermediate programmers
            explanation_expert: Explanation for expert programmers
            concept_agnostic: Language-agnostic concept description
            translation_guidance: Guidelines for translating this term

        Returns:
            The context ID of the newly added deep context

        Raises:
            sqlite3.IntegrityError: If term already exists (UNIQUE constraint)
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            INSERT INTO deep_contexts (
                term, term_type, etymology, explanation_simple,
                explanation_beginner, explanation_intermediate,
                explanation_expert, concept_agnostic, translation_guidance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                term,
                term_type,
                etymology,
                explanation_simple,
                explanation_beginner,
                explanation_intermediate,
                explanation_expert,
                concept_agnostic,
                translation_guidance,
            ),
        )

        conn.commit()
        context_id = cursor.lastrowid
        logger.debug(f"Added deep context for term '{term}' with ID {context_id}")
        return context_id

    def get_deep_context(self, term: str) -> dict | None:
        """Get deep context for a term.

        Args:
            term: The programming term to look up

        Returns:
            Dictionary with all context fields or None if not found.
            Keys include: id, term, term_type, etymology, explanation_simple,
            explanation_beginner, explanation_intermediate, explanation_expert,
            concept_agnostic, translation_guidance, created_at, updated_at
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT * FROM deep_contexts WHERE term = ?
            """,
            (term,),
        )

        row = cursor.fetchone()
        if row is None:
            logger.debug(f"No deep context found for term '{term}'")
            return None

        return dict(row)

    def update_deep_context(self, term: str, **fields) -> bool:
        """Update deep context for a term.

        Args:
            term: The programming term to update
            **fields: Fields to update (etymology, explanation_simple, etc.)

        Returns:
            True if updated, False if not found

        Note:
            Also updates the updated_at timestamp automatically
        """
        if not fields:
            logger.warning("No fields provided for update")
            return False

        # Build SET clause dynamically
        valid_fields = {
            "term_type",
            "etymology",
            "explanation_simple",
            "explanation_beginner",
            "explanation_intermediate",
            "explanation_expert",
            "concept_agnostic",
            "translation_guidance",
        }

        # Filter to valid fields only
        update_fields = {k: v for k, v in fields.items() if k in valid_fields}

        if not update_fields:
            logger.warning(f"No valid fields provided for update: {fields.keys()}")
            return False

        set_clause = ", ".join([f"{field} = ?" for field in update_fields])
        values = list(update_fields.values())

        conn = self._get_connection()
        cursor = conn.execute(
            f"""
            UPDATE deep_contexts
            SET {set_clause}, updated_at = datetime('now')
            WHERE term = ?
            """,
            values + [term],
        )

        conn.commit()
        updated = cursor.rowcount > 0

        if updated:
            logger.debug(f"Updated deep context for term '{term}'")
        else:
            logger.debug(f"No deep context found to update for term '{term}'")

        return updated

    # ===========================
    # Linguistic Standards CRUD Operations
    # ===========================

    def add_linguistic_standard(
        self,
        language_code: str,
        language_family: str | None = None,
        action_keyword_form: str | None = None,
        state_keyword_form: str | None = None,
        constant_form: str | None = None,
        guidelines: str | None = None,
    ) -> int:
        """Add linguistic standards for a language.

        Args:
            language_code: ISO 639-1 language code (e.g., "es", "zh")
            language_family: Language family (e.g., "Romance", "Sino-Tibetan")
            action_keyword_form: Guidelines for action keywords (verbs)
            state_keyword_form: Guidelines for state keywords (conditions)
            constant_form: Guidelines for constant naming
            guidelines: General translation guidelines for the language

        Returns:
            The standard ID of the newly added linguistic standard

        Raises:
            sqlite3.IntegrityError: If language_code already exists (UNIQUE constraint)
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            INSERT INTO linguistic_standards (
                language_code, language_family, action_keyword_form,
                state_keyword_form, constant_form, guidelines
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                language_code,
                language_family,
                action_keyword_form,
                state_keyword_form,
                constant_form,
                guidelines,
            ),
        )

        conn.commit()
        standard_id = cursor.lastrowid
        logger.debug(
            f"Added linguistic standard for language '{language_code}' with ID {standard_id}"
        )
        return standard_id

    def get_linguistic_standard(self, language_code: str) -> dict | None:
        """Get linguistic standards for a language.

        Args:
            language_code: ISO 639-1 language code (e.g., "es", "zh")

        Returns:
            Dictionary with all standard fields or None if not found.
            Keys include: id, language_code, language_family, action_keyword_form,
            state_keyword_form, constant_form, guidelines, created_at, updated_at
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT * FROM linguistic_standards WHERE language_code = ?
            """,
            (language_code,),
        )

        row = cursor.fetchone()
        if row is None:
            logger.debug(f"No linguistic standard found for language '{language_code}'")
            return None

        return dict(row)

    def update_linguistic_standard(self, language_code: str, **fields) -> bool:
        """Update linguistic standards for a language.

        Args:
            language_code: ISO 639-1 language code to update
            **fields: Fields to update (language_family, action_keyword_form, etc.)

        Returns:
            True if updated, False if not found

        Note:
            Also updates the updated_at timestamp automatically
        """
        if not fields:
            logger.warning("No fields provided for update")
            return False

        # Build SET clause dynamically
        valid_fields = {
            "language_family",
            "action_keyword_form",
            "state_keyword_form",
            "constant_form",
            "guidelines",
        }

        # Filter to valid fields only
        update_fields = {k: v for k, v in fields.items() if k in valid_fields}

        if not update_fields:
            logger.warning(f"No valid fields provided for update: {fields.keys()}")
            return False

        set_clause = ", ".join([f"{field} = ?" for field in update_fields])
        values = list(update_fields.values())

        conn = self._get_connection()
        cursor = conn.execute(
            f"""
            UPDATE linguistic_standards
            SET {set_clause}, updated_at = datetime('now')
            WHERE language_code = ?
            """,
            values + [language_code],
        )

        conn.commit()
        updated = cursor.rowcount > 0

        if updated:
            logger.debug(f"Updated linguistic standard for language '{language_code}'")
        else:
            logger.debug(
                f"No linguistic standard found to update for language '{language_code}'"
            )

        return updated

    # ===========================
    # Review CRUD Operations
    # ===========================

    def add_review(
        self,
        translation_id: int,
        reviewer_github: str | None = None,
        reviewer_proficiency: str | None = None,
        regional_variant: str | None = None,
        vote: str | None = None,
        emoji: str | None = None,
        comment: str | None = None,
        suggested_translation: str | None = None,
        alternatives_suggested: str | None = None,
        review_source: str | None = None,
        github_issue_url: str | None = None,
    ) -> int:
        """Add a review for a translation.

        Args:
            translation_id: ID of the translation being reviewed
            reviewer_github: GitHub username of the reviewer
            reviewer_proficiency: Proficiency level in the language (e.g., 'native', 'fluent', 'intermediate')
            regional_variant: Regional variant of the language (e.g., 'mx', 'es', 'ar')
            vote: Review vote (e.g., 'approve', 'request_changes', 'comment')
            emoji: Emoji reaction to the translation
            comment: Text comment on the translation
            suggested_translation: Alternative translation suggested by reviewer
            alternatives_suggested: Other alternative translations considered
            review_source: Source of the review (e.g., 'github', 'web_ui', 'cli')
            github_issue_url: URL to GitHub issue for this review

        Returns:
            The review ID of the newly created review

        Raises:
            sqlite3.IntegrityError: If translation_id doesn't exist (foreign key constraint violation)
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.execute(
                """
                INSERT INTO reviews (
                    translation_id,
                    reviewer_github,
                    reviewer_proficiency,
                    regional_variant,
                    vote,
                    emoji,
                    comment,
                    suggested_translation,
                    alternatives_suggested,
                    review_source,
                    github_issue_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    translation_id,
                    reviewer_github,
                    reviewer_proficiency,
                    regional_variant,
                    vote,
                    emoji,
                    comment,
                    suggested_translation,
                    alternatives_suggested,
                    review_source,
                    github_issue_url,
                ),
            )
            conn.commit()
            review_id = cursor.lastrowid
            logger.debug(f"Added review {review_id} for translation {translation_id}")
            return review_id
        except sqlite3.IntegrityError as e:
            conn.rollback()
            logger.error(f"Failed to add review for translation {translation_id}: {e}")
            raise

    def get_reviews(self, translation_id: int) -> list[dict]:
        """Get all reviews for a specific translation.

        Args:
            translation_id: ID of the translation

        Returns:
            List of review dictionaries. Returns empty list if no reviews found.
            Each review dict contains all review fields including:
            - id, translation_id, reviewer_github, reviewer_proficiency,
            - regional_variant, vote, emoji, comment, suggested_translation,
            - alternatives_suggested, review_source, github_issue_url, created_at
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT * FROM reviews
            WHERE translation_id = ?
            ORDER BY created_at DESC
            """,
            (translation_id,),
        )

        rows = cursor.fetchall()
        reviews = [dict(row) for row in rows]

        logger.debug(
            f"Retrieved {len(reviews)} reviews for translation {translation_id}"
        )
        return reviews

    def get_reviews_by_reviewer(self, reviewer_github: str) -> list[dict]:
        """Get all reviews by a specific reviewer.

        Args:
            reviewer_github: GitHub username of the reviewer

        Returns:
            List of review dictionaries. Returns empty list if no reviews found.
            Each review dict contains all review fields including:
            - id, translation_id, reviewer_github, reviewer_proficiency,
            - regional_variant, vote, emoji, comment, suggested_translation,
            - alternatives_suggested, review_source, github_issue_url, created_at
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT * FROM reviews
            WHERE reviewer_github = ?
            ORDER BY created_at DESC
            """,
            (reviewer_github,),
        )

        rows = cursor.fetchall()
        reviews = [dict(row) for row in rows]

        logger.debug(f"Retrieved {len(reviews)} reviews by reviewer {reviewer_github}")
        return reviews

    def delete_review(self, review_id: int) -> bool:
        """Delete a review by ID.

        Args:
            review_id: ID of the review to delete

        Returns:
            True if the review was deleted, False if review_id was not found
        """
        conn = self._get_connection()

        cursor = conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.debug(f"Deleted review {review_id}")
        else:
            logger.debug(f"Review {review_id} not found for deletion")

        return deleted

    # ===========================
    # Translation CRUD Operations
    # ===========================

    def add_translation(
        self,
        language_code: str,
        term: str,
        term_type: str,
        translation: str,
        source: str,
        word_type: str | None = None,
        word_form: str | None = None,
        model_rationale: str | None = None,
        alternatives_considered: str | None = None,
        confidence: str | None = None,
        created_by: str | None = None,
    ) -> int:
        """Add a new translation to the database.

        Args:
            language_code: Target language code (e.g., 'es', 'ar', 'zh')
            term: The English term being translated
            term_type: Type of term (keyword, builtin, operator, etc.)
            translation: The translated term
            source: Source of translation (community, aya23, claude, etc.)
            word_type: Optional grammatical word type
            word_form: Optional word form variation
            model_rationale: Optional AI model reasoning for translation
            alternatives_considered: Optional alternative translations considered
            confidence: Optional confidence level (high, medium, low)
            created_by: Optional creator identifier

        Returns:
            The translation ID (primary key)

        Raises:
            sqlite3.IntegrityError: If duplicate (language_code, term, term_type, source)
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            INSERT INTO translations (
                language_code, term, term_type, translation, source,
                word_type, word_form, model_rationale, alternatives_considered,
                confidence, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                language_code,
                term,
                term_type,
                translation,
                source,
                word_type,
                word_form,
                model_rationale,
                alternatives_considered,
                confidence,
                created_by,
            ),
        )
        conn.commit()

        translation_id = cursor.lastrowid
        logger.debug(
            f"Added translation: {term} -> {translation} "
            f"({language_code}, {term_type}, source: {source}, id: {translation_id})"
        )

        return translation_id

    def upsert_translation(
        self,
        language_code: str,
        term: str,
        term_type: str,
        translation: str,
        source: str,
        word_type: str | None = None,
        word_form: str | None = None,
        model_rationale: str | None = None,
        alternatives_considered: str | None = None,
        confidence: str | None = None,
        created_by: str | None = None,
    ) -> int:
        """Add or update a translation in the database.

        If a translation with the same (language_code, term, term_type, source)
        already exists, it will be updated. Otherwise, a new translation is inserted.

        Args:
            language_code: Target language code (e.g., 'es', 'ar', 'zh')
            term: The English term being translated
            term_type: Type of term (keyword, builtin, operator, etc.)
            translation: The translated term
            source: Source of translation (community, aya23, claude, etc.)
            word_type: Optional grammatical word type
            word_form: Optional word form variation
            model_rationale: Optional AI model reasoning for translation
            alternatives_considered: Optional alternative translations considered
            confidence: Optional confidence level (high, medium, low)
            created_by: Optional creator identifier

        Returns:
            The translation ID (primary key)
        """
        conn = self._get_connection()

        # Check if translation exists
        existing = self.get_translation(language_code, term, term_type, source)

        if existing:
            # Update existing translation
            conn.execute(
                """
                UPDATE translations SET
                    translation = ?,
                    word_type = ?,
                    word_form = ?,
                    model_rationale = ?,
                    alternatives_considered = ?,
                    confidence = ?,
                    created_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE language_code = ? AND term = ? AND term_type = ? AND source = ?
            """,
                (
                    translation,
                    word_type,
                    word_form,
                    model_rationale,
                    alternatives_considered,
                    confidence,
                    created_by,
                    language_code,
                    term,
                    term_type,
                    source,
                ),
            )
            conn.commit()
            translation_id = existing["id"]
            logger.debug(
                f"Updated translation: {term} -> {translation} "
                f"({language_code}, {term_type}, source: {source}, id: {translation_id})"
            )
        else:
            # Insert new translation
            translation_id = self.add_translation(
                language_code=language_code,
                term=term,
                term_type=term_type,
                translation=translation,
                source=source,
                word_type=word_type,
                word_form=word_form,
                model_rationale=model_rationale,
                alternatives_considered=alternatives_considered,
                confidence=confidence,
                created_by=created_by,
            )

        return translation_id

    def get_translation(
        self,
        language_code: str,
        term: str,
        term_type: str,
        source: str,
    ) -> dict | None:
        """Get a specific translation.

        Args:
            language_code: Target language code
            term: The English term
            term_type: Type of term
            source: Source of translation

        Returns:
            Dictionary with all translation fields, or None if not found
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT * FROM translations
            WHERE language_code = ? AND term = ? AND term_type = ? AND source = ?
        """,
            (language_code, term, term_type, source),
        )

        row = cursor.fetchone()
        conn.row_factory = None  # Reset row factory

        if row:
            return dict(row)
        return None

    def get_all_translations(
        self,
        language_code: str | None = None,
        term: str | None = None,
        term_type: str | None = None,
        source: str | None = None,
    ) -> list[dict]:
        """Query translations with optional filters.

        All parameters are optional. Provide any combination to filter results.

        Args:
            language_code: Filter by target language code
            term: Filter by English term
            term_type: Filter by term type
            source: Filter by translation source

        Returns:
            List of translation dictionaries matching filters
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        # Build dynamic query based on provided filters
        query = "SELECT * FROM translations WHERE 1=1"
        params = []

        if language_code is not None:
            query += " AND language_code = ?"
            params.append(language_code)

        if term is not None:
            query += " AND term = ?"
            params.append(term)

        if term_type is not None:
            query += " AND term_type = ?"
            params.append(term_type)

        if source is not None:
            query += " AND source = ?"
            params.append(source)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.row_factory = None  # Reset row factory

        return [dict(row) for row in rows]

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

        Example:
            db.update_translation(
                translation_id=123,
                translation="nueva_traducción",
                confidence="high"
            )
        """
        if not fields:
            logger.warning("No fields provided to update_translation")
            return False

        # Valid fields that can be updated (exclude id, created_at)
        valid_fields = {
            "language_code",
            "term",
            "term_type",
            "translation",
            "source",
            "word_type",
            "word_form",
            "model_rationale",
            "alternatives_considered",
            "confidence",
            "created_by",
        }

        # Filter out invalid fields
        update_fields = {k: v for k, v in fields.items() if k in valid_fields}

        if not update_fields:
            logger.warning("No valid fields provided to update_translation")
            return False

        # Build UPDATE query dynamically
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

    def delete_translation(
        self,
        translation_id: int,
    ) -> bool:
        """Delete a translation by ID.

        Cascade deletes associated reviews due to foreign key constraint.

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
            logger.debug(
                f"Deleted translation {translation_id} (and cascade-deleted reviews)"
            )
            return True
        else:
            logger.debug(f"Translation {translation_id} not found for deletion")
            return False

    # Additional methods to be implemented in future phases:
    # - search_translations()
    # - get_stats()
