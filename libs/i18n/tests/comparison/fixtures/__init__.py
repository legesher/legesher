"""Test fixtures for comparison module."""

from .mock_translations import (
    MOCK_SPANISH_TRANSLATIONS,
    MOCK_ARABIC_TRANSLATIONS,
    MOCK_CHINESE_TRANSLATIONS,
    get_all_mock_translations,
    get_mock_translations_for_term,
    get_mock_terms_for_language,
    get_available_languages,
    get_statistics,
)

__all__ = [
    "MOCK_SPANISH_TRANSLATIONS",
    "MOCK_ARABIC_TRANSLATIONS",
    "MOCK_CHINESE_TRANSLATIONS",
    "get_all_mock_translations",
    "get_mock_translations_for_term",
    "get_mock_terms_for_language",
    "get_available_languages",
    "get_statistics",
]
