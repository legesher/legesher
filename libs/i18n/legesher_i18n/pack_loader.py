"""Language pack loading with inheritance support.

This module implements the core functionality for loading language packs,
resolving inheritance chains, merging keyword translations, and caching results.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml

from .exceptions import (
    CircularInheritanceError,
    MaxInheritanceDepthError,
    PackNotFoundError,
    PathTraversalError,
)
from .schema_validator import LanguagePackMetadata, SchemaValidator


MAX_INHERITANCE_DEPTH = 10


@dataclass(frozen=True)
class LanguagePack:
    """Immutable representation of a loaded language pack.

    Attributes:
        language: Language code (e.g., 'es', 'ar')
        target: Target programming language (e.g., 'python')
        version: Python version string (e.g., '3.10', '3.13')
        keywords: Merged keyword translations from pack + inheritance
        builtins: Merged builtin function translations
        metadata: Optional metadata about the pack
        extends: Optional path to parent pack (for reference)
        inheritance_chain: List of pack paths in inheritance order
    """

    language: str
    target: str
    version: str
    keywords: dict[str, str] = field(default_factory=dict)
    builtins: dict[str, str] = field(default_factory=dict)
    metadata: Optional[LanguagePackMetadata] = None
    extends: Optional[str] = None
    inheritance_chain: list[str] = field(default_factory=list)

    def get_keyword_translation(self, keyword: str) -> Optional[str]:
        """Get translation for a specific keyword.

        Args:
            keyword: English keyword to translate

        Returns:
            Translated keyword, or None if not found
        """
        return self.keywords.get(keyword)

    def get_builtin_translation(self, builtin: str) -> Optional[str]:
        """Get translation for a specific builtin function.

        Args:
            builtin: English builtin name to translate

        Returns:
            Translated builtin name, or None if not found
        """
        return self.builtins.get(builtin)

    def has_keyword(self, keyword: str) -> bool:
        """Check if pack contains a keyword translation.

        Args:
            keyword: Keyword to check

        Returns:
            True if keyword is in the pack
        """
        return keyword in self.keywords

    def __repr__(self) -> str:
        """String representation of language pack."""
        return (
            f"LanguagePack(language={self.language}, target={self.target}, "
            f"version={self.version}, keywords={len(self.keywords)}, "
            f"builtins={len(self.builtins)})"
        )


class LanguagePackLoader:
    """Loads language packs with inheritance resolution and caching.

    This loader is thread-safe and uses LRU caching for performance.
    """

    def __init__(self, pack_root: Optional[Path] = None):
        """Initialize the loader.

        Args:
            pack_root: Root directory for language packs
                      (defaults to libs/i18n/programming_languages/)
        """
        if pack_root is None:
            # Default to package's programming_languages directory
            pack_root = Path(__file__).parent.parent / "programming_languages"

        self.pack_root = pack_root

    @lru_cache(maxsize=32)
    def load(
        self,
        language: str,
        target: str = "python",
        version: Optional[str] = None,
    ) -> LanguagePack:
        """Load a language pack with full inheritance resolution.

        This method is thread-safe and caches results using lru_cache.

        Args:
            language: Language code (e.g., 'es', 'ar')
            target: Target programming language (default: 'python')
            version: Python version (e.g., '3.10', '3.13')
                    If None, attempts to load default pack

        Returns:
            Loaded LanguagePack with merged keywords from inheritance

        Raises:
            PackNotFoundError: If pack file doesn't exist (includes available languages)
            CircularInheritanceError: If circular inheritance detected
            MaxInheritanceDepthError: If inheritance too deep
        """
        # Build pack path
        pack_path = self._get_pack_path(language, target, version)

        if not pack_path.exists():
            # Get list of available languages for helpful error message
            available = self.list_available_languages(target)
            raise PackNotFoundError(
                language,
                target,
                version or "default",
                str(pack_path),
                available_languages=available,
            )

        # Load with inheritance
        pack_data, inheritance_chain = self._resolve_inheritance(pack_path, set())

        # Validate merged pack
        pack_schema = SchemaValidator.validate_pack(pack_data, pack_path)

        # Create immutable LanguagePack
        pack = LanguagePack(
            language=pack_schema.language,
            target=pack_schema.target,
            version=pack_schema.version,
            keywords=dict(pack_schema.keywords),  # Copy to ensure immutability
            builtins=dict(pack_schema.builtins),
            metadata=pack_schema.metadata,
            extends=pack_schema.extends,
            inheritance_chain=inheritance_chain,
        )

        return pack

    def _get_pack_path(
        self, language: str, target: str, version: Optional[str]
    ) -> Path:
        """Build path to language pack file.

        Args:
            language: Language code
            target: Target programming language
            version: Version string (or None for default)

        Returns:
            Path to pack file
        """
        if version:
            # Version-specific pack: programming_languages/python/3.10/es.yml
            return self.pack_root / target / version / f"{language}.yml"
        else:
            # Default pack: programming_languages/python/es.yml
            return self.pack_root / target / f"{language}.yml"

    def _resolve_inheritance(
        self,
        pack_path: Path,
        visited: set[str],
    ) -> tuple[dict[str, Any], list[str]]:
        """Recursively resolve inheritance chain and merge packs.

        Args:
            pack_path: Path to current pack file
            visited: Set of already visited pack paths (for cycle detection)

        Returns:
            Tuple of (merged_pack_data, inheritance_chain)

        Raises:
            CircularInheritanceError: If circular inheritance detected
            MaxInheritanceDepthError: If chain exceeds max depth
            PathTraversalError: If path traversal attempt detected
        """
        pack_path_str = str(pack_path)

        # Check for circular inheritance
        if pack_path_str in visited:
            raise CircularInheritanceError(pack_path_str, visited)

        # Check max depth
        if len(visited) >= MAX_INHERITANCE_DEPTH:
            raise MaxInheritanceDepthError(pack_path_str, MAX_INHERITANCE_DEPTH)

        visited_copy = visited.copy()
        visited_copy.add(pack_path_str)

        # Load current pack
        with open(pack_path, "r", encoding="utf-8") as f:
            current_data = yaml.safe_load(f)

        if not current_data:
            current_data = {}

        inheritance_chain = [pack_path_str]

        # Check if pack extends another
        extends = current_data.get("extends")

        if extends:
            # Security check: prevent path traversal
            if ".." in extends and not self._is_safe_parent_path(pack_path, extends):
                raise PathTraversalError(extends)

            # Resolve parent pack path
            parent_path = SchemaValidator.validate_inheritance_path(extends, pack_path)

            # Recursively load parent
            parent_data, parent_chain = self._resolve_inheritance(
                parent_path, visited_copy
            )

            # Merge parent into current (current overrides parent)
            merged = self._merge_packs(parent_data, current_data)

            # Combine inheritance chains
            inheritance_chain = parent_chain + inheritance_chain

            return merged, inheritance_chain

        return current_data, inheritance_chain

    def _is_safe_parent_path(self, current_path: Path, extends: str) -> bool:
        """Check if extends path is a safe relative parent path.

        Allows ../X.Y/lang.yml for going up to parent version, but not
        escaping the language packs directory entirely.

        Args:
            current_path: Current pack file path
            extends: Extends path from pack

        Returns:
            True if path is safe
        """
        # Allow one level up for version inheritance (e.g., ../3.10/es.yml)
        if extends.startswith("../") and extends.count("../") == 1:
            return True

        return False

    def _merge_packs(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge two pack dictionaries (override takes precedence).

        Merges keywords and builtins from base and override. Override values
        replace base values for duplicate keys.

        Args:
            base: Base pack data (parent)
            override: Override pack data (child)

        Returns:
            Merged pack dictionary
        """
        merged = base.copy()

        # Merge keywords (override takes precedence)
        if "keywords" in base or "keywords" in override:
            base_keywords = base.get("keywords", {})
            override_keywords = override.get("keywords", {})
            merged["keywords"] = {**base_keywords, **override_keywords}

        # Merge builtins (override takes precedence)
        if "builtins" in base or "builtins" in override:
            base_builtins = base.get("builtins", {})
            override_builtins = override.get("builtins", {})
            merged["builtins"] = {**base_builtins, **override_builtins}

        # Override scalar fields
        for key in ["language", "target", "version", "extends", "metadata"]:
            if key in override:
                merged[key] = override[key]

        return merged

    def clear_cache(self):
        """Clear the pack cache.

        Thread-safe cache clearing using lru_cache.cache_clear().
        """
        self.load.cache_clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache size and hit information from lru_cache
        """
        info = self.load.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "size": info.currsize,
            "maxsize": info.maxsize,
        }

    def list_available_languages(self, target: str = "python") -> list[tuple[str, str]]:
        """List all available language packs for a target language.

        Note: This method performs filesystem operations (globbing, file I/O, YAML parsing)
        which can be expensive. Results are computed fresh on each call since language
        packs may be added/removed at runtime. For better performance in production,
        consider calling this method once at startup and caching the results.

        Args:
            target: Target programming language (default: 'python')

        Returns:
            List of (language_code, language_name) tuples

        Example:
            >>> loader = LanguagePackLoader()
            >>> loader.list_available_languages()
            [('es', 'Spanish'), ('ar', 'Arabic'), ('hi', 'Hindi')]
        """
        languages: list[tuple[str, str]] = []
        target_dir = self.pack_root / target

        if not target_dir.exists():
            return languages

        # Scan for .yml files in target directory
        for pack_file in target_dir.glob("*.yml"):
            if pack_file.is_file():
                lang_code = pack_file.stem

                # Skip version-index file (not a language pack)
                if lang_code == "version-index":
                    continue

                # Try to load metadata to get full language name
                try:
                    with open(pack_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        lang_name = data.get("metadata", {}).get(
                            "name", lang_code.upper()
                        )
                except (OSError, yaml.YAMLError, KeyError, TypeError, AttributeError):
                    # Fall back to language code if file can't be read, parsed,
                    # or has unexpected structure
                    lang_name = lang_code.upper()

                languages.append((lang_code, lang_name))

        # Also check versioned packs
        for version_dir in target_dir.iterdir():
            if version_dir.is_dir():
                for pack_file in version_dir.glob("*.yml"):
                    if pack_file.is_file():
                        lang_code = pack_file.stem

                        # Skip version-index file
                        if lang_code == "version-index":
                            continue

                        if not any(code == lang_code for code, _ in languages):
                            try:
                                with open(pack_file, "r", encoding="utf-8") as f:
                                    data = yaml.safe_load(f)
                                    lang_name = data.get("metadata", {}).get(
                                        "name", lang_code.upper()
                                    )
                            except (
                                OSError,
                                yaml.YAMLError,
                                KeyError,
                                TypeError,
                                AttributeError,
                            ):
                                # Fall back to language code if file can't be read, parsed,
                                # or has unexpected structure
                                lang_name = lang_code.upper()

                            languages.append((lang_code, lang_name))

        return sorted(languages, key=lambda x: x[0])

    def __repr__(self) -> str:
        """String representation of loader."""
        info = self.load.cache_info()
        return f"LanguagePackLoader(pack_root={self.pack_root}, cache_size={info.currsize}/{info.maxsize})"
