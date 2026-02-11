"""Database module for translation storage and management."""

from .database import TranslationDatabase
from .schema import (
    INDEXES,
    LANGUAGES_TABLE,
    SELECTED_TRANSLATIONS_TABLE,
    TERMS_TABLE,
    TRANSLATIONS_TABLE,
    get_schema,
)

__all__ = [
    "TranslationDatabase",
    "TERMS_TABLE",
    "LANGUAGES_TABLE",
    "TRANSLATIONS_TABLE",
    "SELECTED_TRANSLATIONS_TABLE",
    "INDEXES",
    "get_schema",
]
