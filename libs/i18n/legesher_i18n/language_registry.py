"""Language metadata registry for Legesher i18n.

This module provides centralized metadata about supported languages.
The canonical source of truth is languages.json in this directory.

To add or modify languages, edit languages.json and run:
    uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py
"""

import json
from pathlib import Path
from typing import Dict, Literal, TypedDict

# Path to the canonical language data
_LANGUAGES_JSON = Path(__file__).parent / "languages.json"


class LanguageMetadata(TypedDict):
    """Metadata about a language."""

    name: str  # English name
    native: str  # Native name
    iso639_2: str  # ISO 639-2 three-letter code
    bcp47: str  # BCP 47 language tag (e.g., 'en', 'zh-Hans', 'pt-BR')
    rtl: bool  # Right-to-left script
    status: Literal["available", "experimental", "deprecated"]


def _load_languages() -> tuple[Dict[str, LanguageMetadata], str]:
    """Load language metadata from JSON file.

    Returns:
        Tuple of (language_metadata dict, canonical_language code)
    """
    with open(_LANGUAGES_JSON, encoding="utf-8") as f:
        data = json.load(f)

    languages: Dict[str, LanguageMetadata] = {}
    for code, meta in data["languages"].items():
        languages[code] = {
            "name": meta["name"],
            "native": meta["native"],
            "iso639_2": meta["iso639_2"],
            "bcp47": meta["bcp47"],
            "rtl": meta["rtl"],
            "status": meta["status"],
        }

    return languages, data["canonical_language"]


# Load language data from JSON (single source of truth)
LANGUAGE_METADATA, CANONICAL_LANGUAGE = _load_languages()


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


def get_available_language_codes() -> list[str]:
    """Get list of available (non-experimental, non-deprecated) language codes.

    Returns:
        List of language codes with status 'available'
    """
    return [
        code
        for code, meta in LANGUAGE_METADATA.items()
        if meta["status"] == "available"
    ]


def get_rtl_language_codes() -> list[str]:
    """Get list of RTL (right-to-left) language codes.

    Returns:
        List of language codes that use RTL script
    """
    return [code for code, meta in LANGUAGE_METADATA.items() if meta["rtl"]]


def get_active_language_codes() -> list[str]:
    """Get list of active (non-deprecated) language codes.

    Returns both 'available' and 'experimental' status languages,
    excluding only 'deprecated' ones.

    Returns:
        List of language codes with status 'available' or 'experimental'
    """
    return [
        code
        for code, meta in LANGUAGE_METADATA.items()
        if meta["status"] in ("available", "experimental")
    ]


__all__ = [
    "LANGUAGE_METADATA",
    "CANONICAL_LANGUAGE",
    "LanguageMetadata",
    "get_language_name",
    "get_native_name",
    "is_rtl_language",
    "is_supported_language",
    "get_available_language_codes",
    "get_rtl_language_codes",
    "get_active_language_codes",
]
