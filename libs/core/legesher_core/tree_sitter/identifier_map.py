"""Identifier translation map for consistent cross-file, cross-language translations.

Maintains a mapping of source identifiers to their translations in each target
language. Supports compound identifier splitting (snake_case, camelCase, PascalCase),
multi-language storage, and JSON persistence.

Inspired by translation memory in CAT tools and symbol tables in compilers.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def split_identifier(text: str) -> list[str]:
    """Split a compound identifier into component words.

    Handles snake_case, camelCase, PascalCase, and SCREAMING_SNAKE_CASE.

    Examples:
        >>> split_identifier("calculate_tax")
        ["calculate", "tax"]
        >>> split_identifier("calculateTax")
        ["calculate", "Tax"]
        >>> split_identifier("UserProfile")
        ["User", "Profile"]
        >>> split_identifier("MAX_RETRY_COUNT")
        ["MAX", "RETRY", "COUNT"]
    """
    # First split on underscores
    if "_" in text:
        return [part for part in text.split("_") if part]

    # Then split on camelCase/PascalCase boundaries
    # Split before uppercase letters that follow lowercase letters
    parts = re.sub(r"([a-z])([A-Z])", r"\1_\2", text)
    # Split before uppercase letters that are followed by lowercase (for acronyms)
    parts = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", parts)
    return [part for part in parts.split("_") if part]


def reassemble_identifier(parts: list[str], convention: str) -> str:
    """Reassemble component words into an identifier using the given convention.

    Args:
        parts: List of word components
        convention: One of "snake_case", "camelCase", "PascalCase",
                   "SCREAMING_SNAKE_CASE", "lowercase"
    """
    if not parts:
        return ""

    if convention == "snake_case":
        return "_".join(p.lower() for p in parts)
    elif convention == "SCREAMING_SNAKE_CASE":
        return "_".join(p.upper() for p in parts)
    elif convention == "PascalCase":
        return "".join(p.capitalize() for p in parts)
    elif convention == "camelCase":
        first = parts[0].lower()
        rest = [p.capitalize() for p in parts[1:]]
        return first + "".join(rest)
    else:  # lowercase or unknown
        return "_".join(p.lower() for p in parts)


class IdentifierMap:
    """Maintains consistent identifier translations across files and languages.

    The map is keyed by source identifier and stores translations for
    multiple target languages. It is name-based (not scope-based) — the
    same identifier name always gets the same translation regardless of
    where it appears.

    Designed to be committed to git (.legesher/identifier_map.json) and
    shared across team members and translation runs.

    Example:
        >>> id_map = IdentifierMap(source_lang="en")
        >>> id_map.add("calculate_tax", "es", "calcular_impuesto")
        >>> id_map.get("calculate_tax", "es")
        'calcular_impuesto'
        >>> id_map.save(Path(".legesher/identifier_map.json"))
    """

    def __init__(self, source_lang: str = "en"):
        self.source_lang = source_lang
        self._map: dict[str, dict[str, str]] = {}
        # Maps: source_identifier -> {target_lang: translated_identifier}

    def get(self, identifier: str, target_lang: str) -> Optional[str]:
        """Get the translation for an identifier in a target language."""
        translations = self._map.get(identifier)
        if translations is None:
            return None
        return translations.get(target_lang)

    def add(self, identifier: str, target_lang: str, translation: str) -> None:
        """Add a translation for an identifier in a target language."""
        if identifier not in self._map:
            self._map[identifier] = {}
        self._map[identifier][target_lang] = translation

    def has(self, identifier: str, target_lang: str) -> bool:
        """Check if a translation exists for an identifier."""
        return self.get(identifier, target_lang) is not None

    def get_untranslated(self, identifiers: list[str], target_lang: str) -> list[str]:
        """Return identifiers that don't have a translation in target_lang."""
        return [i for i in identifiers if not self.has(i, target_lang)]

    def get_glossary(self, target_lang: str) -> dict[str, str]:
        """Get all translations for a target language as a flat dict.

        Useful for including as context in LLM prompts.
        """
        glossary = {}
        for identifier, translations in self._map.items():
            if target_lang in translations:
                glossary[identifier] = translations[target_lang]
        return glossary

    def get_all_identifiers(self) -> list[str]:
        """Get all source identifiers in the map."""
        return list(self._map.keys())

    def get_languages(self) -> set[str]:
        """Get all target languages that have at least one translation."""
        languages: set[str] = set()
        for translations in self._map.values():
            languages.update(translations.keys())
        return languages

    def merge(self, other: "IdentifierMap") -> None:
        """Merge another IdentifierMap into this one.

        Existing translations are NOT overwritten. Only new translations
        are added. This supports merging maps from different translation runs.
        """
        for identifier, translations in other._map.items():
            if identifier not in self._map:
                self._map[identifier] = {}
            for lang, translation in translations.items():
                if lang not in self._map[identifier]:
                    self._map[identifier][lang] = translation

    def __len__(self) -> int:
        return len(self._map)

    def __contains__(self, identifier: str) -> bool:
        return identifier in self._map

    def save(self, path: Path) -> None:
        """Save the identifier map to a JSON file.

        Creates parent directories if needed. The JSON format is
        designed to be human-readable and git-friendly.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "source_lang": self.source_lang,
            "identifier_count": len(self._map),
            "identifiers": dict(sorted(self._map.items())),
        }
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("Saved identifier map: %d identifiers to %s", len(self._map), path)

    @classmethod
    def load(cls, path: Path) -> "IdentifierMap":
        """Load an identifier map from a JSON file.

        Args:
            path: Path to the JSON file

        Returns:
            Loaded IdentifierMap instance

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)

        identifiers = data.get("identifiers", {})
        if not isinstance(identifiers, dict):
            raise ValueError("Invalid identifier map: 'identifiers' must be a dict")
        for key, translations in identifiers.items():
            if not isinstance(key, str) or not isinstance(translations, dict):
                raise ValueError(f"Invalid entry in identifier map: {key!r}")

        source_lang = data.get("source_lang", "en")
        instance = cls(source_lang=source_lang)
        instance._map = identifiers

        logger.info(
            "Loaded identifier map: %d identifiers from %s",
            len(instance._map),
            path,
        )
        return instance

    @classmethod
    def load_or_create(cls, path: Path, source_lang: str = "en") -> "IdentifierMap":
        """Load from file if it exists, otherwise create empty."""
        if path.exists():
            return cls.load(path)
        return cls(source_lang=source_lang)
