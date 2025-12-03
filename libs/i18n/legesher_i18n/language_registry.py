"""Language metadata registry for Legesher i18n.

This module provides centralized metadata about supported languages.
Language availability is discovered dynamically from filesystem/database.
"""

from typing import Dict, TypedDict


class LanguageMetadata(TypedDict):
    """Metadata about a language."""

    name: str  # English name
    native: str  # Native name
    rtl: bool  # Right-to-left script


# Language metadata registry - immutable facts about languages
# This is the only place where language names should be defined
LANGUAGE_METADATA: Dict[str, LanguageMetadata] = {
    "ar": {"name": "Arabic", "native": "العربية", "rtl": True},
    "da": {"name": "Danish", "native": "Dansk", "rtl": False},
    "de": {"name": "German", "native": "Deutsch", "rtl": False},
    "el": {"name": "Greek", "native": "Ελληνικά", "rtl": False},
    "en": {"name": "English", "native": "English", "rtl": False},
    "es": {"name": "Spanish", "native": "Español", "rtl": False},
    "fi": {"name": "Finnish", "native": "Suomi", "rtl": False},
    "fr": {"name": "French", "native": "Français", "rtl": False},
    "he": {"name": "Hebrew", "native": "עברית", "rtl": True},
    "hi": {"name": "Hindi", "native": "हिन्दी", "rtl": False},
    "hu": {"name": "Hungarian", "native": "Magyar", "rtl": False},
    "id": {"name": "Indonesian", "native": "Bahasa Indonesia", "rtl": False},
    "it": {"name": "Italian", "native": "Italiano", "rtl": False},
    "ja": {"name": "Japanese", "native": "日本語", "rtl": False},
    "ko": {"name": "Korean", "native": "한국어", "rtl": False},
    "ms": {"name": "Malay", "native": "Bahasa Melayu", "rtl": False},
    "nl": {"name": "Dutch", "native": "Nederlands", "rtl": False},
    "no": {"name": "Norwegian", "native": "Norsk", "rtl": False},
    "pl": {"name": "Polish", "native": "Polski", "rtl": False},
    "pt": {"name": "Portuguese", "native": "Português", "rtl": False},
    "ru": {"name": "Russian", "native": "Русский", "rtl": False},
    "sv": {"name": "Swedish", "native": "Svenska", "rtl": False},
    "th": {"name": "Thai", "native": "ไทย", "rtl": False},
    "tr": {"name": "Turkish", "native": "Türkçe", "rtl": False},
    "vi": {"name": "Vietnamese", "native": "Tiếng Việt", "rtl": False},
    "zh": {"name": "Chinese", "native": "中文", "rtl": False},
}

# Canonical language (used as reference for all translations)
CANONICAL_LANGUAGE = "en"


def get_language_name(language_code: str) -> str:
    """Get English name for a language code.

    Args:
        language_code: ISO 639-1 language code (e.g., 'en', 'es', 'ar')

    Returns:
        English name of the language, or uppercase code if unknown
    """
    return LANGUAGE_METADATA.get(language_code, {}).get("name", language_code.upper())


def get_native_name(language_code: str) -> str:
    """Get native name for a language code.

    Args:
        language_code: ISO 639-1 language code (e.g., 'en', 'es', 'ar')

    Returns:
        Native name of the language, or uppercase code if unknown
    """
    return LANGUAGE_METADATA.get(language_code, {}).get("native", language_code.upper())


def is_rtl_language(language_code: str) -> bool:
    """Check if a language uses right-to-left script.

    Args:
        language_code: ISO 639-1 language code (e.g., 'en', 'es', 'ar')

    Returns:
        True if language uses RTL script (e.g., Arabic, Hebrew)
    """
    return LANGUAGE_METADATA.get(language_code, {}).get("rtl", False)


def is_supported_language(language_code: str) -> bool:
    """Check if a language code is in the registry.

    Args:
        language_code: ISO 639-1 language code (e.g., 'en', 'es', 'ar')

    Returns:
        True if language is in the metadata registry
    """
    return language_code in LANGUAGE_METADATA


__all__ = [
    "LANGUAGE_METADATA",
    "CANONICAL_LANGUAGE",
    "get_language_name",
    "get_native_name",
    "is_rtl_language",
    "is_supported_language",
]
