"""Shared pytest fixtures for legesher-i18n tests."""

import json
import tempfile
from pathlib import Path

import pytest

from legesher_i18n.db import TranslationDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing.

    Yields a TranslationDatabase instance with a temporary file.
    Automatically cleans up after the test.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db = TranslationDatabase(db_path=db_path)

    yield db

    # Cleanup
    db.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_translations_data():
    """Load sample translations from fixtures.

    Returns the parsed JSON data from sample_translations.json.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "sample_translations.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def populated_db(temp_db, sample_translations_data):
    """Create a database pre-populated with sample data.

    Uses temp_db and sample_translations_data to create a realistic
    test database with terms, languages, and translations.
    """
    conn = temp_db._get_connection()

    # Add languages
    for lang in sample_translations_data.get("languages", []):
        conn.execute(
            """INSERT OR IGNORE INTO languages
               (code, name, native_name, direction, status, has_yaml_pack)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                lang["code"],
                lang["name"],
                lang["native_name"],
                lang.get("direction", "ltr"),
                lang.get("status", "experimental"),
                1 if lang.get("has_yaml_pack") else 0,
            ),
        )
    conn.commit()

    # Add terms and build name->id lookup
    term_ids = {}
    for term in sample_translations_data.get("terms", []):
        term_id = temp_db.get_or_create_term(
            name=term["name"],
            programming_language=term.get("programming_language", "python"),
            category=term.get("category", "unknown"),
            subcategory=term.get("subcategory"),
        )
        term_ids[term["name"]] = term_id

    # Add translations
    translation_ids = []
    for trans in sample_translations_data.get("translations", []):
        term_name = trans["term_name"]
        term_id = term_ids.get(term_name)
        if term_id is None:
            # Auto-create term if not in terms list
            term_id = temp_db.get_or_create_term(
                name=term_name, programming_language="python", category="unknown"
            )
            term_ids[term_name] = term_id

        trans_id = temp_db.add_translation(
            term_id=term_id,
            language_code=trans["language_code"],
            translation=trans["translation"],
            source=trans.get("source", "test"),
            confidence=trans.get("confidence"),
            created_by=trans.get("created_by"),
        )
        translation_ids.append(trans_id)

    # Store IDs for reference in tests
    temp_db.translation_ids = translation_ids
    temp_db.term_ids = term_ids

    return temp_db
