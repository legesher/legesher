"""Language-name resolution from ``languages.json`` — the single source.

CORE-1804 consolidates the language-name maps that had drifted across the
model-provider layer (``prompt_builder._FALLBACK_LANGUAGE_NAMES``,
``claude_model.LANGUAGE_NAMES``, ``hf_profiles.DEFAULT_LANGUAGE_NAMES``)
into one derivation from the DB-generated ``languages.json`` (CORE-611).

The exported mapping carries both the ISO 639-1 key (``"es"``) and the
``iso639_2`` alias (``"spa"``) for every language, so callers that address
models with three-letter codes (Aya-101) resolve through the same source.

A code absent from ``languages.json`` resolves to ``code.upper()`` — loud
in prompt output, and exactly the behavior every deleted copy had for its
own unknown codes.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_LANGUAGES_JSON = Path(__file__).parent / "languages.json"


@lru_cache(maxsize=1)
def language_names() -> dict[str, str]:
    """Return the ``code -> English name`` mapping derived from languages.json.

    Includes ISO 639-1 keys plus ``iso639_2`` aliases. Returns an empty dict
    (with a warning) when the file is missing or malformed — callers then
    render bare codes, which is visible rather than silently wrong.
    """
    try:
        with open(_LANGUAGES_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load languages.json: %s", exc)
        return {}

    names: dict[str, str] = {}
    for code, meta in data.get("languages", {}).items():
        name = meta.get("name")
        if not isinstance(name, str) or not name:
            continue
        names[code] = name
        alias = meta.get("iso639_2")
        if isinstance(alias, str) and alias and alias not in names:
            names[alias] = name
    return names


def language_name(code: str, default: str | None = None) -> str:
    """Resolve *code* to its English name, falling back to ``code.upper()``."""
    resolved = language_names().get(code)
    if resolved is not None:
        return resolved
    return default if default is not None else code.upper()


@lru_cache(maxsize=1)
def supported_language_codes() -> frozenset[str]:
    """ISO 639-1 codes present in ``languages.json``."""
    try:
        with open(_LANGUAGES_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to load languages.json: %s", exc)
        return frozenset()
    return frozenset(data.get("languages", {}).keys())
