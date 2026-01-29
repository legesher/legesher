"""Language pack loading with inheritance support.

This module implements the core functionality for loading language packs,
resolving inheritance chains, merging keyword translations, and caching results.
"""

import importlib.metadata
import importlib.util
import logging
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

logger = logging.getLogger(__name__)


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
        exceptions: Merged exception type translations
        metadata: Optional metadata about the pack
        extends: Optional path to parent pack (for reference)
        inheritance_chain: List of pack paths in inheritance order
    """

    language: str
    target: str
    version: str
    keywords: dict[str, str] = field(default_factory=dict)
    builtins: dict[str, str] = field(default_factory=dict)
    exceptions: dict[str, str] = field(default_factory=dict)
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

    def get_exception_translation(self, exception: str) -> Optional[str]:
        """Get translation for a specific exception type.

        Args:
            exception: English exception name to translate (e.g., 'ValueError')

        Returns:
            Translated exception name, or None if not found
        """
        # Try lowercase first (our internal convention), then original case
        return self.exceptions.get(exception.lower()) or self.exceptions.get(exception)

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
            f"builtins={len(self.builtins)}, exceptions={len(self.exceptions)})"
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
        self._discovered_packs: dict[str, Path] | None = None

    @staticmethod
    def _scan_pack_root(root: Path, discovered: dict[str, Path], label: str) -> None:
        """Scan a pack root directory and add discovered packs.

        Iterates over {root}/{target}/{lang}/legesher_i18n_{target}_{lang}/packs/
        and registers each valid pack in *discovered* (skipping duplicates).

        Args:
            root: Directory containing target/lang subdirectories.
            discovered: Accumulator dict; new packs are added in-place.
            label: Human-readable source label for debug logging.
        """
        for target_dir in root.iterdir():
            if target_dir.is_dir():
                target = target_dir.name
                for lang_dir in target_dir.iterdir():
                    if lang_dir.is_dir():
                        module_name = f"legesher_i18n_{target}_{lang_dir.name}"
                        module_dir = lang_dir / module_name
                        if module_dir.exists() and (module_dir / "packs").exists():
                            pack_key = f"{target}-{lang_dir.name}"
                            if pack_key not in discovered:
                                discovered[pack_key] = module_dir
                                logger.debug(
                                    f"Discovered {label} pack: {pack_key} at {module_dir}"
                                )

    def _discover_packs(self) -> dict[str, Path]:
        """Discover all available language packs from monorepo and installed packages.

        Checks two locations:
        1. Development monorepo: libs/i18n/language-packs/{target}/{lang}/
        2. Installed packages: legesher-i18n-{target}-{lang}

        Returns:
            Dictionary mapping pack keys to their base paths.
            Keys are formatted as "{target}-{lang}" (e.g., "python-ar").
            Values are Path objects to the package directory containing packs/.

        Example:
            {
                "python-ar": Path("/path/to/legesher_i18n_python_ar"),
                "python-es": Path("/path/to/legesher_i18n_python_es"),
            }
        """
        if self._discovered_packs is not None:
            return self._discovered_packs

        discovered: dict[str, Path] = {}

        # 1. Check development monorepo structure
        # Path: libs/i18n/language-packs/{target}/{lang}/legesher_i18n_{target}_{lang}/
        monorepo_root = Path(__file__).parent.parent / "language-packs"
        if monorepo_root.exists():
            self._scan_pack_root(monorepo_root, discovered, "monorepo")

        # 2. Check bundled packs inside legesher_i18n package
        bundled_root = Path(__file__).parent / "bundled_packs"
        if bundled_root.exists() and bundled_root.resolve() != monorepo_root.resolve():
            self._scan_pack_root(bundled_root, discovered, "bundled")

        # 3. Check installed packages using importlib
        # Package naming: legesher-i18n-{target}-{lang} -> legesher_i18n_{target}_{lang}
        try:
            for dist in importlib.metadata.distributions():
                package_name = dist.name
                if package_name.startswith("legesher-i18n-"):
                    # Extract target and language from package name
                    # e.g., "legesher-i18n-python-ar" -> ["python", "ar"]
                    parts = package_name[len("legesher-i18n-") :].split("-")
                    if len(parts) >= 2:
                        target = parts[0]
                        lang = "-".join(parts[1:])  # Support multi-part language codes
                        pack_key = f"{target}-{lang}"

                        # Convert package name to module name
                        # "legesher-i18n-python-ar" -> "legesher_i18n_python_ar"
                        module_name = package_name.replace("-", "_")

                        # Try to find the package location using importlib
                        spec = importlib.util.find_spec(module_name)
                        if spec and spec.origin:
                            # Get the package directory (parent of __init__.py)
                            package_path = Path(spec.origin).parent
                            if (package_path / "packs").exists():
                                discovered[pack_key] = package_path
                                logger.debug(
                                    f"Discovered installed pack: {pack_key} at {package_path}"
                                )
        except Exception as e:
            logger.warning(f"Error discovering installed packages: {e}")

        self._discovered_packs = discovered
        return discovered

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
            exceptions=dict(pack_schema.exceptions),
            metadata=pack_schema.metadata,
            extends=pack_schema.extends,
            inheritance_chain=inheritance_chain,
        )

        return pack

    def _get_pack_path(
        self, language: str, target: str, version: Optional[str]
    ) -> Path:
        """Build path to language pack file.

        First checks discovered packs (monorepo or installed packages).
        Falls back to legacy pack_root structure for backward compatibility.

        Args:
            language: Language code
            target: Target programming language
            version: Version string (or None for default)

        Returns:
            Path to pack file
        """
        # Try discovered packs first (new structure)
        discovered = self._discover_packs()
        pack_key = f"{target}-{language}"

        if pack_key in discovered:
            pack_dir = discovered[pack_key]
            if version:
                # New structure: {pack_dir}/packs/{version}.yml
                pack_path = pack_dir / "packs" / f"{version}.yml"
            else:
                # New structure: {pack_dir}/packs/default.yml
                pack_path = pack_dir / "packs" / "default.yml"

            # Check if pack exists in new structure
            if pack_path.exists():
                return pack_path

        # Fallback to legacy structure for backward compatibility
        if version:
            # Legacy: programming_languages/python/3.10/es.yml
            return self.pack_root / target / version / f"{language}.yml"
        else:
            # Legacy: programming_languages/python/es.yml
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

        # Merge exceptions (override takes precedence)
        if "exceptions" in base or "exceptions" in override:
            base_exceptions = base.get("exceptions", {})
            override_exceptions = override.get("exceptions", {})
            merged["exceptions"] = {**base_exceptions, **override_exceptions}

        # Override scalar fields
        for key in ["language", "target", "version", "extends", "metadata"]:
            if key in override:
                merged[key] = override[key]

        return merged

    def clear_cache(self):
        """Clear the pack cache and discovered packs.

        Thread-safe cache clearing using lru_cache.cache_clear().
        Also resets the discovered packs cache to force re-discovery.
        """
        self.load.cache_clear()
        self._discovered_packs = None

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

        First checks discovered packs (monorepo or installed packages).
        Falls back to legacy pack_root structure for backward compatibility.

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
        seen_codes: set[str] = set()

        # 1. Check discovered packs (new structure)
        discovered = self._discover_packs()
        for pack_key, pack_dir in discovered.items():
            # Extract target and language from pack_key (e.g., "python-ar")
            if pack_key.startswith(f"{target}-"):
                lang_code = pack_key[len(target) + 1 :]

                # Try to read metadata from default.yml or any version file
                metadata_path = pack_dir / "packs" / "default.yml"
                if not metadata_path.exists():
                    # Try to find any version file for metadata
                    packs_dir = pack_dir / "packs"
                    if packs_dir.exists():
                        for pack_file in packs_dir.glob("*.yml"):
                            metadata_path = pack_file
                            break

                # Load language name from metadata
                lang_name = lang_code.upper()
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                            lang_name = data.get("metadata", {}).get("name", lang_name)
                    except (
                        OSError,
                        yaml.YAMLError,
                        KeyError,
                        TypeError,
                        AttributeError,
                    ):
                        # Silently fall back to default language name if metadata is missing or invalid
                        pass

                languages.append((lang_code, lang_name))
                seen_codes.add(lang_code)

        # 2. Fallback to legacy structure (for backward compatibility)
        target_dir = self.pack_root / target

        if target_dir.exists():
            # Scan for .yml files in target directory
            for pack_file in target_dir.glob("*.yml"):
                if pack_file.is_file():
                    lang_code = pack_file.stem

                    # Skip version-index file (not a language pack)
                    if lang_code == "version-index":
                        continue

                    # Skip if already discovered in new structure
                    if lang_code in seen_codes:
                        continue

                    # Try to load metadata to get full language name
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
                    seen_codes.add(lang_code)

            # Also check versioned packs in legacy structure
            for version_dir in target_dir.iterdir():
                if version_dir.is_dir():
                    for pack_file in version_dir.glob("*.yml"):
                        if pack_file.is_file():
                            lang_code = pack_file.stem

                            # Skip version-index file
                            if lang_code == "version-index":
                                continue

                            # Skip if already found
                            if lang_code in seen_codes:
                                continue

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
                            seen_codes.add(lang_code)

        return sorted(languages, key=lambda x: x[0])

    def __repr__(self) -> str:
        """String representation of loader."""
        info = self.load.cache_info()
        discovered_count = (
            len(self._discovered_packs) if self._discovered_packs is not None else 0
        )
        return (
            f"LanguagePackLoader(pack_root={self.pack_root}, "
            f"discovered_packs={discovered_count}, "
            f"cache_size={info.currsize}/{info.maxsize})"
        )
