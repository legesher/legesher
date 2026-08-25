"""Database module for translation storage and management."""

from .database import TranslationDatabase, default_db_path
from .schema import (
    INDEXES,
    LANGUAGES_TABLE,
    SELECTED_TRANSLATIONS_TABLE,
    SELECTED_VOCABULARY_TABLE,
    TERMS_TABLE,
    TRANSLATIONS_TABLE,
    VOCABULARY_ENTRIES_TABLE,
    VOCABULARY_TRANSLATIONS_TABLE,
    get_schema,
)

__all__ = [
    "TranslationDatabase",
    "default_db_path",
    "TERMS_TABLE",
    "LANGUAGES_TABLE",
    "TRANSLATIONS_TABLE",
    "SELECTED_TRANSLATIONS_TABLE",
    "VOCABULARY_ENTRIES_TABLE",
    "VOCABULARY_TRANSLATIONS_TABLE",
    "SELECTED_VOCABULARY_TABLE",
    "INDEXES",
    "get_schema",
]
