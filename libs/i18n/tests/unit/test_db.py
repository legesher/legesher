"""Unit tests for translation database."""

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
            # Explicitly close connections before temp directory cleanup (important on Windows)
            db_instance.close()

    def test_database_initialization(self, db):
        """Test that database and tables are created."""
        # Verify the database was initialized
        assert db is not None
        assert hasattr(db, "close")

        # Verify tables exist by attempting to query them
        # This will be expanded in Phase 2 to check specific schema
        conn = db._get_connection()
        cursor = conn.cursor()

        # Check if translations table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='translations'"
        )
        assert cursor.fetchone() is not None

        # Check if reviews table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'"
        )
        assert cursor.fetchone() is not None

    def test_database_path_creation(self, db):
        """Test that database file is created at specified path."""
        # The database should have a valid path
        assert hasattr(db, "db_path") or hasattr(db, "_db_path")
        # Path validation will be expanded in Phase 2

    # Placeholder tests for CRUD operations (to be filled in Phase 2)

    def test_add_translation(self, db):
        """Test adding a translation to the database."""
        # Add a translation with all fields
        translation_id = db.add_translation(
            language_code="es",
            term="class",
            term_type="keyword",
            translation="clase",
            source="community",
            word_type="noun",
            word_form="singular",
            model_rationale="Translates to 'class' in Spanish as a category/group",
            alternatives_considered="grupo, categoría",
            confidence="high",
            created_by="test_user",
        )

        # Verify it was added with a valid ID
        assert translation_id > 0

        # Verify we can retrieve it
        result = db.get_translation(
            language_code="es", term="class", term_type="keyword", source="community"
        )
        assert result is not None
        assert result["translation"] == "clase"
        assert result["word_type"] == "noun"
        assert result["word_form"] == "singular"
        assert result["confidence"] == "high"
        assert result["created_by"] == "test_user"

    def test_get_translation(self, db):
        """Test retrieving a translation by language and term."""
        # Add a translation first
        db.add_translation(
            language_code="es",
            term="lambda",
            term_type="keyword",
            translation="lambda",
            source="community",
            confidence="medium",
        )

        # Retrieve it
        result = db.get_translation(
            language_code="es", term="lambda", term_type="keyword", source="community"
        )

        assert result is not None
        assert result["language_code"] == "es"
        assert result["term"] == "lambda"
        assert result["term_type"] == "keyword"
        assert result["translation"] == "lambda"
        assert result["source"] == "community"
        assert result["confidence"] == "medium"
        assert "id" in result
        assert "created_at" in result
        assert "updated_at" in result

    def test_get_all_translations_for_term(self, db):
        """Test retrieving all translations for a specific term."""
        # Add multiple translations for the same term
        db.add_translation(
            language_code="es",
            term="if",
            term_type="keyword",
            translation="si",
            source="community",
        )
        db.add_translation(
            language_code="es",
            term="if",
            term_type="keyword",
            translation="si",
            source="aya23",
        )
        db.add_translation(
            language_code="ar",
            term="if",
            term_type="keyword",
            translation="إذا",
            source="community",
        )

        # Get all translations for "if"
        results = db.get_all_translations(term="if")
        assert len(results) == 3

        # Get Spanish translations for "if"
        results = db.get_all_translations(language_code="es", term="if")
        assert len(results) == 2
        assert all(r["language_code"] == "es" for r in results)

        # Get specific source
        results = db.get_all_translations(
            language_code="es", term="if", term_type="keyword", source="community"
        )
        assert len(results) == 1
        assert results[0]["source"] == "community"

    def test_update_translation(self, db):
        """Test updating an existing translation."""
        # Add a translation
        translation_id = db.add_translation(
            language_code="es",
            term="continue",
            term_type="keyword",
            translation="continuar",
            source="community",
            confidence="low",
        )

        # Update some fields
        updated = db.update_translation(
            translation_id,
            translation="seguir",
            confidence="high",
            word_type="verb",
            model_rationale="Updated based on community feedback",
        )

        assert updated is True

        # Verify updates
        result = db.get_translation(
            language_code="es", term="continue", term_type="keyword", source="community"
        )
        assert result["translation"] == "seguir"
        assert result["confidence"] == "high"
        assert result["word_type"] == "verb"
        assert result["model_rationale"] == "Updated based on community feedback"
        assert result["term"] == "continue"  # unchanged

    def test_delete_translation(self, db):
        """Test deleting a translation."""
        # Add a translation
        translation_id = db.add_translation(
            language_code="es",
            term="raise",
            term_type="keyword",
            translation="levantar",
            source="community",
        )

        # Delete it
        deleted = db.delete_translation(translation_id)
        assert deleted is True

        # Verify it's gone
        result = db.get_translation(
            language_code="es", term="raise", term_type="keyword", source="community"
        )
        assert result is None

    def test_add_review(self, db):
        """Test adding a review for a translation."""

        # First, add a translation using the proper method
        translation_id = db.add_translation(
            language_code="es",
            term="class",
            term_type="keyword",
            translation="clase",
            source="community",
        )

        # Add a review for this translation
        review_id = db.add_review(
            translation_id=translation_id,
            reviewer_github="testuser",
            reviewer_proficiency="native",
            regional_variant="mx",
            vote="approve",
            emoji="👍",
            comment="This is a great translation!",
            suggested_translation=None,
            alternatives_suggested=None,
            review_source="github",
            github_issue_url="https://github.com/legesher/legesher/issues/123",
        )

        # Verify the review was added
        assert review_id > 0

        # Retrieve the review to verify it was stored correctly
        reviews = db.get_reviews(translation_id)
        assert len(reviews) == 1
        assert reviews[0]["id"] == review_id
        assert reviews[0]["translation_id"] == translation_id
        assert reviews[0]["reviewer_github"] == "testuser"
        assert reviews[0]["reviewer_proficiency"] == "native"
        assert reviews[0]["regional_variant"] == "mx"
        assert reviews[0]["vote"] == "approve"
        assert reviews[0]["emoji"] == "👍"
        assert reviews[0]["comment"] == "This is a great translation!"
        assert reviews[0]["review_source"] == "github"
        assert (
            reviews[0]["github_issue_url"]
            == "https://github.com/legesher/legesher/issues/123"
        )

    def test_get_reviews_for_translation(self, db):
        """Test retrieving reviews for a translation."""

        # First, add a translation using the proper method
        translation_id = db.add_translation(
            language_code="es",
            term="def",
            term_type="keyword",
            translation="def",
            source="community",
        )

        # Add multiple reviews for this translation
        review_id_1 = db.add_review(
            translation_id=translation_id,
            reviewer_github="user1",
            comment="Good translation",
        )
        review_id_2 = db.add_review(
            translation_id=translation_id,
            reviewer_github="user2",
            comment="Could be better",
        )
        review_id_3 = db.add_review(
            translation_id=translation_id, reviewer_github="user3", comment="Perfect!"
        )

        # Retrieve all reviews for this translation
        reviews = db.get_reviews(translation_id)
        assert len(reviews) == 3

        # Verify reviews are returned in descending order by created_at (most recent first)
        # The IDs should be in reverse order if created sequentially
        review_ids = [r["id"] for r in reviews]
        assert review_id_3 in review_ids
        assert review_id_2 in review_ids
        assert review_id_1 in review_ids

        # Test getting reviews for non-existent translation
        empty_reviews = db.get_reviews(99999)
        assert len(empty_reviews) == 0

    def test_get_translation_with_best_score(self, db):
        """Test retrieving translation with highest review score."""
        pytest.skip("Will be implemented in Phase 2")

    def test_source_filtering(self, db):
        """Test filtering translations by source (community, aya23, etc)."""
        pytest.skip("Will be implemented in Phase 2")

    def test_concurrent_access(self, db):
        """Test database handles concurrent access correctly."""
        pytest.skip("Will be implemented in Phase 2")

    def test_transaction_rollback(self, db):
        """Test transaction rollback on error."""
        pytest.skip("Will be implemented in Phase 2")

    # ===========================
    # Deep Context CRUD Tests
    # ===========================

    def test_add_deep_context(self, db):
        """Test adding deep context for a programming term."""
        context_id = db.add_deep_context(
            term="class",
            term_type="keyword",
            etymology="From Latin 'classis' meaning group or division",
            explanation_simple="A blueprint for creating objects",
            explanation_beginner="Classes are templates that define attributes and methods",
            explanation_intermediate="Classes support OOP with inheritance and encapsulation",
            explanation_expert="Classes are first-class objects with metaclass customization",
            concept_agnostic="Object-oriented programming construct for encapsulation",
            translation_guidance="Translate based on 'group' or 'category' concepts",
        )

        assert context_id > 0

        # Verify it was added
        context = db.get_deep_context("class")
        assert context is not None
        assert context["term"] == "class"
        assert context["term_type"] == "keyword"
        assert context["etymology"] == "From Latin 'classis' meaning group or division"

    def test_add_deep_context_minimal_fields(self, db):
        """Test adding deep context with only required fields."""
        context_id = db.add_deep_context(term="def", term_type="keyword")

        assert context_id > 0

        # Verify it was added
        context = db.get_deep_context("def")
        assert context is not None
        assert context["term"] == "def"
        assert context["term_type"] == "keyword"
        assert context["etymology"] is None

    def test_add_deep_context_unique_constraint(self, db):
        """Test that adding duplicate term raises IntegrityError."""
        import sqlite3

        db.add_deep_context(term="class", term_type="keyword")

        # Attempting to add same term should raise IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            db.add_deep_context(term="class", term_type="keyword")

    def test_get_deep_context(self, db):
        """Test retrieving deep context by term."""
        # Add a context first
        db.add_deep_context(
            term="return",
            term_type="keyword",
            etymology="From re- (back) + turn",
            explanation_simple="Exit a function with a value",
            concept_agnostic="Control flow statement for function exit",
        )

        # Retrieve it
        context = db.get_deep_context("return")

        assert context is not None
        assert context["term"] == "return"
        assert context["term_type"] == "keyword"
        assert context["etymology"] == "From re- (back) + turn"
        assert context["explanation_simple"] == "Exit a function with a value"
        assert context["concept_agnostic"] == "Control flow statement for function exit"
        assert "id" in context
        assert "created_at" in context
        assert "updated_at" in context

    def test_get_deep_context_not_found(self, db):
        """Test retrieving non-existent deep context returns None."""
        context = db.get_deep_context("nonexistent")
        assert context is None

    def test_update_deep_context(self, db):
        """Test updating deep context fields."""
        # Add a context
        db.add_deep_context(
            term="lambda",
            term_type="keyword",
            etymology="From Greek letter λ (lambda)",
            explanation_simple="Anonymous function",
        )

        # Update some fields
        updated = db.update_deep_context(
            "lambda",
            etymology="From Greek letter λ (lambda) used in lambda calculus",
            explanation_beginner="A small anonymous function for simple operations",
            translation_guidance="Use mathematical function terminology",
        )

        assert updated is True

        # Verify updates
        context = db.get_deep_context("lambda")
        assert (
            context["etymology"]
            == "From Greek letter λ (lambda) used in lambda calculus"
        )
        assert (
            context["explanation_beginner"]
            == "A small anonymous function for simple operations"
        )
        assert (
            context["translation_guidance"] == "Use mathematical function terminology"
        )
        assert context["explanation_simple"] == "Anonymous function"  # unchanged

    def test_update_deep_context_not_found(self, db):
        """Test updating non-existent deep context returns False."""
        updated = db.update_deep_context("nonexistent", etymology="Some etymology")
        assert updated is False

    def test_update_deep_context_no_fields(self, db):
        """Test updating with no fields returns False."""
        db.add_deep_context(term="if", term_type="keyword")

        updated = db.update_deep_context("if")
        assert updated is False

    def test_update_deep_context_invalid_fields(self, db):
        """Test updating with invalid field names returns False."""
        db.add_deep_context(term="while", term_type="keyword")

        updated = db.update_deep_context(
            "while", invalid_field="value", another_invalid="value"
        )
        assert updated is False

    def test_update_deep_context_mixed_valid_invalid_fields(self, db):
        """Test updating with mix of valid and invalid fields."""
        db.add_deep_context(term="for", term_type="keyword")

        updated = db.update_deep_context(
            "for", etymology="Valid update", invalid_field="Should be ignored"
        )
        assert updated is True

        context = db.get_deep_context("for")
        assert context["etymology"] == "Valid update"

    # ===========================
    # Linguistic Standards CRUD Tests
    # ===========================

    def test_add_linguistic_standard(self, db):
        """Test adding linguistic standards for a language."""
        standard_id = db.add_linguistic_standard(
            language_code="es",
            language_family="Romance",
            action_keyword_form="infinitive",
            state_keyword_form="noun",
            constant_form="UPPERCASE",
            guidelines="Use infinitive forms for action keywords",
        )

        assert standard_id > 0

        # Verify it was added
        standard = db.get_linguistic_standard("es")
        assert standard is not None
        assert standard["language_code"] == "es"
        assert standard["language_family"] == "Romance"
        assert standard["action_keyword_form"] == "infinitive"

    def test_add_linguistic_standard_minimal_fields(self, db):
        """Test adding linguistic standard with only required field."""
        standard_id = db.add_linguistic_standard(language_code="fr")

        assert standard_id > 0

        # Verify it was added
        standard = db.get_linguistic_standard("fr")
        assert standard is not None
        assert standard["language_code"] == "fr"
        assert standard["language_family"] is None

    def test_add_linguistic_standard_unique_constraint(self, db):
        """Test that adding duplicate language_code raises IntegrityError."""
        import sqlite3

        db.add_linguistic_standard(language_code="es")

        # Attempting to add same language_code should raise IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            db.add_linguistic_standard(language_code="es")

    def test_get_linguistic_standard(self, db):
        """Test retrieving linguistic standards by language code."""
        # Add a standard first
        db.add_linguistic_standard(
            language_code="zh",
            language_family="Sino-Tibetan",
            action_keyword_form="verb",
            state_keyword_form="adjective",
            constant_form="UPPERCASE",
            guidelines="Use descriptive characters for keywords",
        )

        # Retrieve it
        standard = db.get_linguistic_standard("zh")

        assert standard is not None
        assert standard["language_code"] == "zh"
        assert standard["language_family"] == "Sino-Tibetan"
        assert standard["action_keyword_form"] == "verb"
        assert standard["state_keyword_form"] == "adjective"
        assert standard["constant_form"] == "UPPERCASE"
        assert standard["guidelines"] == "Use descriptive characters for keywords"
        assert "id" in standard
        assert "created_at" in standard
        assert "updated_at" in standard

    def test_get_linguistic_standard_not_found(self, db):
        """Test retrieving non-existent linguistic standard returns None."""
        standard = db.get_linguistic_standard("nonexistent")
        assert standard is None

    def test_update_linguistic_standard(self, db):
        """Test updating linguistic standard fields."""
        # Add a standard
        db.add_linguistic_standard(
            language_code="ar", language_family="Semitic", action_keyword_form="verb"
        )

        # Update some fields
        updated = db.update_linguistic_standard(
            "ar",
            language_family="Afro-Asiatic",
            state_keyword_form="noun",
            guidelines="Use Arabic script naturally with right-to-left flow",
        )

        assert updated is True

        # Verify updates
        standard = db.get_linguistic_standard("ar")
        assert standard["language_family"] == "Afro-Asiatic"
        assert standard["state_keyword_form"] == "noun"
        assert (
            standard["guidelines"]
            == "Use Arabic script naturally with right-to-left flow"
        )
        assert standard["action_keyword_form"] == "verb"  # unchanged

    def test_update_linguistic_standard_not_found(self, db):
        """Test updating non-existent linguistic standard returns False."""
        updated = db.update_linguistic_standard(
            "nonexistent", language_family="Some family"
        )
        assert updated is False

    def test_update_linguistic_standard_no_fields(self, db):
        """Test updating with no fields returns False."""
        db.add_linguistic_standard(language_code="ja")

        updated = db.update_linguistic_standard("ja")
        assert updated is False

    def test_update_linguistic_standard_invalid_fields(self, db):
        """Test updating with invalid field names returns False."""
        db.add_linguistic_standard(language_code="ko")

        updated = db.update_linguistic_standard(
            "ko", invalid_field="value", another_invalid="value"
        )
        assert updated is False

    def test_update_linguistic_standard_mixed_valid_invalid_fields(self, db):
        """Test updating with mix of valid and invalid fields."""
        db.add_linguistic_standard(language_code="pt")

        updated = db.update_linguistic_standard(
            "pt", language_family="Romance", invalid_field="Should be ignored"
        )
        assert updated is True

        standard = db.get_linguistic_standard("pt")
        assert standard["language_family"] == "Romance"

    # ===========================
    # Review CRUD Tests
    # ===========================

    def test_add_review_minimal_fields(self, db):
        """Test adding a review with only required field (translation_id)."""

        # Add a translation first using the proper method
        translation_id = db.add_translation(
            language_code="es",
            term="return",
            term_type="keyword",
            translation="retornar",
            source="community",
        )

        # Add a review with minimal fields
        review_id = db.add_review(translation_id=translation_id)

        assert review_id > 0

        # Verify the review was added with NULL values for optional fields
        reviews = db.get_reviews(translation_id)
        assert len(reviews) == 1
        assert reviews[0]["translation_id"] == translation_id
        assert reviews[0]["reviewer_github"] is None
        assert reviews[0]["comment"] is None

    def test_add_review_foreign_key_constraint(self, db):
        """Test that adding a review with non-existent translation_id raises IntegrityError."""
        import sqlite3

        # Attempt to add review for non-existent translation
        with pytest.raises(sqlite3.IntegrityError):
            db.add_review(translation_id=99999, comment="This should fail")

    def test_get_reviews_by_reviewer(self, db):
        """Test retrieving all reviews by a specific reviewer."""

        # Add two translations using the proper method
        translation_id_1 = db.add_translation(
            language_code="es",
            term="if",
            term_type="keyword",
            translation="si",
            source="community",
        )

        translation_id_2 = db.add_translation(
            language_code="es",
            term="else",
            term_type="keyword",
            translation="sino",
            source="community",
        )

        # Add reviews from different reviewers
        db.add_review(
            translation_id=translation_id_1,
            reviewer_github="alice",
            comment="Great work!",
        )
        db.add_review(
            translation_id=translation_id_2,
            reviewer_github="alice",
            comment="Looks good",
        )
        db.add_review(
            translation_id=translation_id_1,
            reviewer_github="bob",
            comment="Could be improved",
        )

        # Get all reviews by alice
        alice_reviews = db.get_reviews_by_reviewer("alice")
        assert len(alice_reviews) == 2
        assert all(r["reviewer_github"] == "alice" for r in alice_reviews)

        # Get all reviews by bob
        bob_reviews = db.get_reviews_by_reviewer("bob")
        assert len(bob_reviews) == 1
        assert bob_reviews[0]["reviewer_github"] == "bob"

        # Get reviews by non-existent reviewer
        no_reviews = db.get_reviews_by_reviewer("nonexistent")
        assert len(no_reviews) == 0

    def test_delete_review(self, db):
        """Test deleting a review by ID."""

        # Add a translation using the proper method
        translation_id = db.add_translation(
            language_code="es",
            term="while",
            term_type="keyword",
            translation="mientras",
            source="community",
        )

        # Add a review
        review_id = db.add_review(
            translation_id=translation_id,
            reviewer_github="testuser",
            comment="Test review",
        )

        # Verify the review exists
        reviews = db.get_reviews(translation_id)
        assert len(reviews) == 1

        # Delete the review
        deleted = db.delete_review(review_id)
        assert deleted is True

        # Verify the review was deleted
        reviews = db.get_reviews(translation_id)
        assert len(reviews) == 0

        # Try to delete again (should return False)
        deleted_again = db.delete_review(review_id)
        assert deleted_again is False

        # Try to delete non-existent review
        deleted_nonexistent = db.delete_review(99999)
        assert deleted_nonexistent is False

    def test_cascade_delete_reviews_on_translation_delete(self, db):
        """Test that deleting a translation cascades to delete its reviews."""

        # Add a translation using the proper method
        translation_id = db.add_translation(
            language_code="es",
            term="for",
            term_type="keyword",
            translation="para",
            source="community",
        )

        # Add multiple reviews for this translation
        review_id_1 = db.add_review(
            translation_id=translation_id, reviewer_github="user1", comment="Review 1"
        )
        review_id_2 = db.add_review(
            translation_id=translation_id, reviewer_github="user2", comment="Review 2"
        )
        review_id_3 = db.add_review(
            translation_id=translation_id, reviewer_github="user3", comment="Review 3"
        )

        # Verify reviews exist
        reviews = db.get_reviews(translation_id)
        assert len(reviews) == 3

        # Delete the translation using raw SQL to test CASCADE
        conn = db._get_connection()
        conn.execute("DELETE FROM translations WHERE id = ?", (translation_id,))
        conn.commit()

        # Verify reviews were cascade deleted
        reviews_after = db.get_reviews(translation_id)
        assert len(reviews_after) == 0

        # Verify reviews don't exist in the database at all
        result = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE id IN (?, ?, ?)",
            (review_id_1, review_id_2, review_id_3),
        )
        count = result.fetchone()[0]
        assert count == 0
