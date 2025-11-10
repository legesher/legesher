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
    test database with translations, deep contexts, and linguistic standards.
    """
    # Add translations
    translation_ids = []
    for trans in sample_translations_data["translations"]:
        trans_id = temp_db.add_translation(**trans)
        translation_ids.append(trans_id)

    # Add deep contexts
    for context in sample_translations_data["deep_contexts"]:
        temp_db.add_deep_context(**context)

    # Add linguistic standards
    for standard in sample_translations_data["linguistic_standards"]:
        temp_db.add_linguistic_standard(**standard)

    # Store IDs for reference in tests
    temp_db.translation_ids = translation_ids

    return temp_db
