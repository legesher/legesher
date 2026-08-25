"""Language pack loading with inheritance support.

This module implements the core functionality for loading language packs,
resolving inheritance chains, merging keyword translations, and caching results.
"""

import importlib.metadata
import importlib.util
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .exceptions import (
    CircularInheritanceError,
    MaxInheritanceDepthError,
    PackNotFoundError,
    PackValidationError,
    PathTraversalError,
    UnsupportedInterpreterError,
)
from .data_contract import MAX_PACK_FILE_BYTES
from .schema_validator import LanguagePackMetadata, SchemaValidator

logger = logging.getLogger(__name__)


MAX_INHERITANCE_DEPTH = 10

# A pack version is either an ``X.Y`` Python version or the literal ``default``.
# ``_get_pack_path`` joins this directly into a filename (``{version}.yml``), so
# an unvalidated value like ``../../../../etc/passwd`` would be a path-traversal
# primitive. The loader validates ``version`` against this pattern before any
# filesystem join (closes the gap; the ``extends`` field has its own guard).
_VERSION_PATTERN = re.compile(r"^(\d+\.\d+|default)$")


def _parse_xy(version: str) -> tuple[int, int] | None:
    """Parse a leading ``X.Y`` from a version string, ignoring any suffix.

    Returns ``(major, minor)`` or ``None`` when there is no ``X.Y`` prefix (e.g.
    ``"default"``), so callers can skip a comparison they cannot make.
    """
    match = re.match(r"^(\d+)\.(\d+)", version)
    return (int(match.group(1)), int(match.group(2))) if match else None


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
        reserved_words: Merged translations for Python conventions like
            ``self`` and ``cls`` (CORE-710). Distinct from ``keywords``
            because they aren't Python reserved words; treated
            deterministically by the translator regardless.
        members: Merged member/property-name translations — labels bounded
            by their receiver, for member-bearing targets such as JavaScript
            (CORE-1582). Empty for Python packs.
        symbols: What each Python symbol is CALLED in this language, keyed
            by the slug from :mod:`legesher_i18n.vocabulary_definitions`
            (CORE-1396). Prose for teaching text and error messages — never
            substituted into code. Empty until a language's vocabulary is
            generated.
        variable_conventions: The idiomatic short name for each variable
            ROLE (``loop_index`` -> ``i``), CORE-1396. Advice for a human
            writing new code, not a substitution the engine performs.
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
    reserved_words: dict[str, str] = field(default_factory=dict)
    members: dict[str, str] = field(default_factory=dict)
    symbols: dict[str, str] = field(default_factory=dict)
    variable_conventions: dict[str, str] = field(default_factory=dict)
    metadata: LanguagePackMetadata | None = None
    extends: str | None = None
    inheritance_chain: list[str] = field(default_factory=list)

    def get_keyword_translation(self, keyword: str) -> str | None:
        """Get translation for a specific keyword.

        Looks up the term in ``keywords`` first, then falls back to
        ``reserved_words``. The keyword section always wins on conflict,
        so any term that is both a true Python keyword and a Legesher
        reserved word is resolved as the keyword.

        Args:
            keyword: English keyword to translate

        Returns:
            Translated keyword, or None if not found in either section
        """
        return self.keywords.get(keyword) or self.reserved_words.get(keyword)

    def get_builtin_translation(self, builtin: str) -> str | None:
        """Get translation for a specific builtin function.

        Args:
            builtin: English builtin name to translate

        Returns:
            Translated builtin name, or None if not found
        """
        return self.builtins.get(builtin)

    def get_exception_translation(self, exception: str) -> str | None:
        """Get translation for a specific exception type.

        Args:
            exception: English exception name to translate (e.g., 'ValueError')

        Returns:
            Translated exception name, or None if not found
        """
        # Try lowercase first (our internal convention), then original case
        return self.exceptions.get(exception.lower()) or self.exceptions.get(exception)

    def get_reserved_word_translation(self, reserved_word: str) -> str | None:
        """Get translation for a specific reserved word (CORE-710).

        Reserved words are Python conventions like ``self`` and ``cls`` that
        Legesher treats deterministically even though Python itself does not
        reserve them. This is the canonical accessor — prefer it over
        ``get_keyword_translation`` when callers know they're working with
        a reserved word.

        Args:
            reserved_word: English reserved word to translate (e.g., 'self')

        Returns:
            Translated reserved word, or None if not found
        """
        return self.reserved_words.get(reserved_word)

    def has_keyword(self, keyword: str) -> bool:
        """Check if pack contains a keyword translation.

        Args:
            keyword: Keyword to check

        Returns:
            True if keyword is in the pack
        """
        return keyword in self.keywords

    def has_reserved_word(self, reserved_word: str) -> bool:
        """Check if pack contains a reserved word translation (CORE-710).

        Args:
            reserved_word: Reserved word to check (e.g., 'self', 'cls')

        Returns:
            True if reserved_word is in the pack's reserved_words section
        """
        return reserved_word in self.reserved_words

    def get_symbol_name(self, slug: str) -> str | None:
        """What this language calls the symbol identified by *slug*.

        Args:
            slug: A slug from :data:`legesher_i18n.vocabulary_definitions.SYMBOLS`
                (e.g. ``"colon"``, ``"underscore"``, ``"indentation"``).

        Returns:
            The localized name, or None when this pack carries no symbol
            vocabulary. Callers rendering teaching text should fall back to
            the canonical English name from ``vocabulary_definitions`` and
            say so, rather than silently mixing languages.
        """
        return self.symbols.get(slug)

    def get_variable_convention(self, role: str) -> str | None:
        """The idiomatic short name this language uses for *role*.

        Args:
            role: A slug from
                :data:`legesher_i18n.vocabulary_definitions.VARIABLE_CONVENTIONS`
                (e.g. ``"loop_index"``, ``"throwaway"``).

        Returns:
            The recommended name, or None when this pack carries no
            variable conventions.
        """
        return self.variable_conventions.get(role)

    def __repr__(self) -> str:
        """String representation of language pack."""
        return (
            f"LanguagePack(language={self.language}, target={self.target}, "
            f"version={self.version}, keywords={len(self.keywords)}, "
            f"builtins={len(self.builtins)}, exceptions={len(self.exceptions)}, "
            f"reserved_words={len(self.reserved_words)}, members={len(self.members)}, "
            f"symbols={len(self.symbols)}, "
            f"variable_conventions={len(self.variable_conventions)})"
        )


class LanguagePackLoader:
    """Load language packs with inheritance resolution and caching.

    Discovers packs from two locations: the in-repo monorepo layout under
    ``libs/i18n/language-packs/`` and installed distributions named
    ``legesher-i18n-{target}-{lang}``. Resolves ``extends:`` chains at load
    time, merges parent keyword, builtin, and exception translations, and
    caches results via LRU for repeated lookups. Thread-safe.

    Example:
        >>> loader = LanguagePackLoader()
        >>> pack = loader.load("es", "python", "3.13")
        >>> pack.get_keyword_translation("def")
        'definir'
    """

    def __init__(self) -> None:
        """Initialize the loader.

        Packs are discovered from two locations (see :meth:`_discover_packs`):
        the in-repo monorepo layout under ``libs/i18n/language-packs/`` and
        installed distributions named ``legesher-i18n-{target}-{lang}``.
        """
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
        version: str | None = None,
        enforce_min_interpreter: bool = True,
        strict: bool = False,
    ) -> LanguagePack:
        """Load a language pack with full inheritance resolution.

        This method is thread-safe and caches results using lru_cache.

        Args:
            language: Language code (e.g., 'es', 'ar')
            target: Target programming language (default: 'python')
            version: Python version (e.g., '3.10', '3.13')
                    If None, attempts to load default pack
            enforce_min_interpreter: When True (the default) and ``version`` is
                an ``X.Y`` string, refuse a pack whose ``python_version_min``
                exceeds it — its identifiers would ``SyntaxError`` on that
                interpreter (e.g. Sinhala ZWJ conjuncts need 3.13+, CORE-1318).
                Tooling that inspects the raw pack without running translated
                code (the auditor, exporters) passes ``False``.
            strict: When True, warn on loading any pack whose
                ``metadata.review_status`` is not ``official`` (CORE-1453
                trust tiers). Default False — experimental packs load
                silently, matching the ship-experimental-packs policy.

        Returns:
            Loaded LanguagePack with merged keywords from inheritance

        Raises:
            PackNotFoundError: If pack file doesn't exist (includes available languages)
            CircularInheritanceError: If circular inheritance detected
            MaxInheritanceDepthError: If inheritance too deep
            UnsupportedInterpreterError: If the pack's ``python_version_min``
                exceeds ``version`` and ``enforce_min_interpreter`` is True
            ValueError: If ``version`` is not ``X.Y`` or ``"default"``
                (path-traversal guard, since version is joined into a filename)
        """
        # Path-traversal guard: ``version`` is joined directly into the pack
        # filename, so reject anything that isn't a bare ``X.Y`` version or the
        # literal ``default`` before touching the filesystem. ``None`` is fine
        # (loads ``default.yml``). This is intentionally placed *before* the
        # lru_cache-backed body runs so a malicious arg never reaches disk.
        if version is not None and not _VERSION_PATTERN.match(version):
            raise ValueError(
                f"Invalid pack version '{version}': must match X.Y (e.g. "
                "'3.13') or be 'default'. Refusing to join into a filename "
                "(path-traversal guard)."
            )

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

        # Interpreter-floor guard: a pack whose declared minimum exceeds the
        # version we are loading FOR contains identifiers that only parse on the
        # newer interpreter (the Sinhala ZWJ conjuncts, CORE-1318). Refuse loudly
        # here rather than letting a SyntaxError surface in the user's code.
        # Skipped when ``version`` is None (no target to compare) or on the
        # auditor/exporter bypass, which inspect the raw pack without running it.
        if enforce_min_interpreter and version is not None:
            self._enforce_min_interpreter(pack_schema, version, language)

        # Create immutable LanguagePack
        pack = LanguagePack(
            language=pack_schema.language,
            target=pack_schema.target,
            version=pack_schema.version,
            keywords=dict(pack_schema.keywords),  # Copy to ensure immutability
            builtins=dict(pack_schema.builtins),
            exceptions=dict(pack_schema.exceptions),
            reserved_words=dict(pack_schema.reserved_words),
            members=dict(pack_schema.members),
            symbols=dict(pack_schema.symbols),
            variable_conventions=dict(pack_schema.variable_conventions),
            metadata=pack_schema.metadata,
            extends=pack_schema.extends,
            inheritance_chain=inheritance_chain,
        )

        # Trust tiers (CORE-1453): in strict mode, anything below `official`
        # on the review ladder loads with a warning, never silently.
        if strict:
            review_status = (
                pack.metadata.review_status if pack.metadata else "experimental"
            )
            if review_status != "official":
                logger.warning(
                    f"Language pack {language}/{target} has review_status="
                    f"'{review_status}' — not 'official'. Strict mode loads "
                    "it with this warning (CORE-1453 trust tiers)."
                )

        return pack

    @staticmethod
    def _enforce_min_interpreter(
        pack_schema: Any, requested_version: str, language: str
    ) -> None:
        """Refuse a pack that requires a newer interpreter than requested.

        No-op when the pack declares no ``python_version_min`` or when either
        version string lacks a parseable ``X.Y`` prefix (nothing to compare).

        Raises:
            UnsupportedInterpreterError: If ``python_version_min`` > requested.
        """
        metadata = pack_schema.metadata
        if metadata is None or not metadata.python_version_min:
            return
        required = _parse_xy(metadata.python_version_min)
        requested = _parse_xy(requested_version)
        if required is None or requested is None:
            return
        if requested < required:
            raise UnsupportedInterpreterError(
                language, metadata.python_version_min, requested_version
            )

    def _get_pack_path(self, language: str, target: str, version: str | None) -> Path:
        """Build path to language pack file.

        Resolves against discovered packs (monorepo or installed packages).
        Returns the expected pack location even when the file does not exist
        so the caller can report a helpful ``PackNotFoundError``.

        Args:
            language: Language code
            target: Target programming language
            version: Version string (or None for default)

        Returns:
            Path to pack file (may not exist)
        """
        discovered = self._discover_packs()
        pack_key = f"{target}-{language}"

        if pack_key in discovered:
            pack_dir = discovered[pack_key]
            filename = f"{version}.yml" if version else "default.yml"
            return pack_dir / "packs" / filename

        # Pack wasn't discovered — return a synthetic path so the caller's
        # existence check fails with a ``PackNotFoundError`` that names the
        # target/lang/version the user asked for.
        filename = f"{version}.yml" if version else "default.yml"
        return Path(f"<not-discovered>/{target}-{language}/packs/{filename}")

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

        # Data-contract size cap (CORE-1453): the DoS guard must fire before
        # the YAML parser ever sees the file.
        file_size = pack_path.stat().st_size
        if file_size > MAX_PACK_FILE_BYTES:
            raise PackValidationError(
                pack_path_str,
                [
                    f"Pack file size {file_size} bytes exceeds the "
                    f"data-contract cap of {MAX_PACK_FILE_BYTES} bytes "
                    "(CORE-1453 DoS guard)"
                ],
            )

        # Load current pack
        with open(pack_path, encoding="utf-8") as f:
            current_data = yaml.safe_load(f)

        if not current_data:
            current_data = {}

        inheritance_chain = [pack_path_str]

        # Check if pack extends another
        extends = current_data.get("extends")

        if extends:
            # Security check: prevent path traversal. Normalize separators so
            # Windows-style `..\\foo.yml` is caught the same as posix-style
            # `../foo.yml`, then split into components. Using a component
            # check instead of a substring match avoids false positives on
            # benign filenames that happen to contain `..` (e.g. "foo..bar.yml").
            # Variants this layer does NOT catch — URL-encoded (`..%2Fpasswd`),
            # fullwidth (`\uff0e\uff0e\uff0fpasswd`), etc. — are intentionally
            # left to the authoritative layer-3 enforcement in
            # SchemaValidator.validate_inheritance_path, which resolves the
            # path and checks `relative_to(sandbox_root)`. Those variants
            # aren't interpreted as traversal by the filesystem, so they
            # resolve to benign (non-existent) filenames and fail safely.
            normalized = extends.replace("\\", "/")
            extends_parts = [p for p in normalized.split("/") if p]
            if ".." in extends_parts and not self._is_safe_parent_path(extends):
                raise PathTraversalError(extends)

            # Derive the sandbox root for layer-3 enforcement: the
            # ``packs/`` directory of the current pack. All packs live in
            # ``<module>/packs/<version>.yml`` layouts (monorepo or
            # installed) so the walk-up always finds a ``packs/`` parent.
            sandbox_root = pack_path
            while (
                sandbox_root.parent.name != "packs"
                and sandbox_root.parent != sandbox_root
            ):
                sandbox_root = sandbox_root.parent
            if sandbox_root.parent.name != "packs":
                # Unexpected layout — refuse to process rather than falling
                # back to a lax sandbox.
                raise PackValidationError(
                    str(pack_path),
                    [
                        f"Cannot derive sandbox root: pack is not inside a 'packs/' directory: {pack_path}"
                    ],
                )
            sandbox_root = sandbox_root.parent

            # Resolve parent pack path
            parent_path = SchemaValidator.validate_inheritance_path(
                extends, pack_path, sandbox_root
            )

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

    def _is_safe_parent_path(self, extends: str) -> bool:
        """Check if extends path is a safe relative parent path.

        Allows ``../X.Y/lang.yml`` for going up to parent version, but not
        escaping the language packs directory entirely. This is a heuristic
        prefix check; the authoritative sandbox enforcement is performed by
        :meth:`SchemaValidator.validate_inheritance_path`, which resolves
        the path and verifies it stays within the sandbox root passed by
        the caller.

        Args:
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

        # Merge reserved_words (override takes precedence)
        if "reserved_words" in base or "reserved_words" in override:
            base_reserved = base.get("reserved_words", {})
            override_reserved = override.get("reserved_words", {})
            merged["reserved_words"] = {**base_reserved, **override_reserved}

        # Merge members (override takes precedence) — CORE-1582
        if "members" in base or "members" in override:
            base_members = base.get("members", {})
            override_members = override.get("members", {})
            merged["members"] = {**base_members, **override_members}

        # Merge the vocabulary partition (override takes precedence) —
        # CORE-1396. Per-key override, exactly like every other section,
        # rather than whole-section replacement: that is the semantics the
        # pack chain has always had, and the ambiguity CORE-1782 is
        # settling for STYLE-GUIDE lists does not arise here because these
        # sections are mappings, not lists.
        #
        # In practice the vocabulary lives entirely in 3.10.yml — symbol
        # names and variable idiom do not change with the interpreter — so
        # the merge is a pass-through today. It is written out anyway so a
        # future version overlay inherits rather than silently drops.
        for section in ("symbols", "variable_conventions"):
            if section in base or section in override:
                merged[section] = {
                    **base.get(section, {}),
                    **override.get(section, {}),
                }

        # Override scalar fields
        for key in ["language", "target", "version", "extends", "metadata"]:
            if key in override:
                merged[key] = override[key]

        return merged

    def refresh_discovery(self) -> None:
        """Drop the pack-discovery cache, keeping already-loaded packs.

        Discovery is what goes stale when a pack is installed or removed
        mid-process; the packs already parsed into memory are still valid.
        Long-lived servers call this to pick up new packs without paying to
        re-parse the YAML for every pack already in use. Use
        :meth:`clear_cache` when pack *content* may have changed on disk.
        """
        self._discovered_packs = None

    def list_available_versions(self, target: str = "python") -> list[str]:
        """List the ``X.Y`` versions any discovered pack provides for *target*.

        The pack version index: the union of version-named pack files across
        every installed pack, so callers can derive the set of supported
        versions instead of hand-maintaining a parallel list. The generic
        ``default.yml`` is not a version and is excluded.

        Args:
            target: Target programming language (default: 'python')

        Returns:
            Version strings sorted numerically, e.g. ``['3.10', '3.13']``.

        Example:
            >>> loader = LanguagePackLoader()
            >>> loader.list_available_versions()
            ['3.10', '3.11', '3.12', '3.13', '3.14']
        """
        versions: set[str] = set()
        for pack_key, pack_dir in self._discover_packs().items():
            if not pack_key.startswith(f"{target}-"):
                continue
            packs_dir = pack_dir / "packs"
            if not packs_dir.exists():
                continue
            for pack_file in packs_dir.glob("*.yml"):
                stem = pack_file.stem
                # Reuse the loader's own version grammar so the index can
                # never admit a name ``load()`` would refuse.
                if stem != "default" and _VERSION_PATTERN.match(stem):
                    versions.add(stem)
        return sorted(versions, key=lambda v: _parse_xy(v) or (0, 0))

    def clear_cache(self) -> None:
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

        Iterates over discovered packs (monorepo or installed packages).

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
                if (
                    metadata_path.exists()
                    and metadata_path.stat().st_size <= MAX_PACK_FILE_BYTES
                ):
                    try:
                        with open(metadata_path, encoding="utf-8") as f:
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

        return sorted(languages, key=lambda x: x[0])

    def __repr__(self) -> str:
        """String representation of loader."""
        info = self.load.cache_info()
        discovered_count = (
            len(self._discovered_packs) if self._discovered_packs is not None else 0
        )
        return (
            f"LanguagePackLoader(discovered_packs={discovered_count}, "
            f"cache_size={info.currsize}/{info.maxsize})"
        )
