"""Universal import hook for native language Python execution.

This module implements Python's import protocol (PEP 302) to enable
seamless execution of Python code written in any natural language.

The key insight: Instead of "translating" to English, we compile
native language code directly to Python bytecode, making all languages
first-class citizens.

Features:
- LRU cache for translated code (default: 128 entries)
- Automatic cache invalidation on file modification
- Thread-safe cache operations
- Configurable cache size via API, environment, or config file

Configuration:
    # Via API parameter
    install_import_hook(language="es", cache_size=256)

    # Via environment variable
    export LEGESHER_CACHE_SIZE=256

    # Via config file (.legesher/config.yml)
    runtime:
      cache_size: 256

Cache Statistics:
    >>> stats = get_cache_stats()
    >>> print(stats)
    {'hits': 42, 'misses': 10, 'evictions': 5, 'size': 47, 'max_size': 128}

Example:
    >>> from legesher.runtime import install_import_hook
    >>> install_import_hook(language="es")
    >>> import mi_modulo  # Works seamlessly with Spanish code!
"""

import os
import ast
import sys
import logging
import threading
import importlib.abc
import importlib.machinery
from pathlib import Path
from typing import Any
from collections import OrderedDict

from legesher_core import TokenTranslator
from legesher.config import LegesherConfig
from legesher.runtime.source_mapper import get_source_mapper

# Configure logger
logger = logging.getLogger(__name__)


class _TranslationCache:
    """Thread-safe LRU cache for translated source code.

    This cache uses OrderedDict for LRU behavior and threading.Lock for
    thread-safety. The cache automatically evicts least-recently-used
    entries when full.

    Each cache instance has its own lock to avoid contention between
    different import hook instances.

    Based on the pattern from the language server hover provider
    (hover.py:46-140).

    Args:
        max_size: Maximum number of cache entries (default: 128)

    Attributes:
        _cache: OrderedDict storing cached translations
        _max_size: Maximum cache size
        _lock: Instance-specific threading lock
        _stats: Dictionary tracking hits, misses, and evictions

    Note:
        Statistics (hits, misses, evictions, size, hit_rate) are accessible
        via the get_stats() method.
    """

    def __init__(self, max_size: int = 128):
        """Initialize the cache with a size limit.

        Args:
            max_size: Maximum number of cache entries
        """
        self._cache: OrderedDict[tuple[str, int], bytes] = OrderedDict()
        self._max_size = max(0, max_size)  # Validate non-negative
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
        self._lock = threading.Lock()  # Instance-specific lock

    def get(self, key: tuple[str, int]) -> bytes | None:
        """Get value from cache (thread-safe, LRU update).

        Args:
            key: Cache key (file_path, mtime_ns)

        Returns:
            Cached bytes if found, None otherwise
        """
        with self._lock:
            if key in self._cache:
                # Move to end (mark as recently used)
                self._cache.move_to_end(key)
                self._stats["hits"] += 1
                return self._cache[key]

            self._stats["misses"] += 1
            return None

    def set(self, key: tuple[str, int], value: bytes) -> None:
        """Store value in cache with LRU eviction (thread-safe).

        Args:
            key: Cache key (file_path, mtime_ns)
            value: Translated source code as bytes
        """
        with self._lock:
            # Add or update entry
            self._cache[key] = value
            self._cache.move_to_end(key)

            # Evict oldest if cache exceeds max size
            # When max_size=0, immediately evict to maintain empty cache
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)  # Remove oldest (first) item
                self._stats["evictions"] += 1

    def clear(self) -> None:
        """Clear the cache and reset statistics (thread-safe)."""
        with self._lock:
            self._cache.clear()
            self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics (thread-safe).

        Returns:
            Dictionary with hits, misses, evictions, size, max_size, and hit_rate
        """
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0.0

            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "size": len(self._cache),
                "max_size": self._max_size,
                "hit_rate": hit_rate,
            }


class LegesherMetaPathFinder(importlib.abc.MetaPathFinder):
    """Universal import hook for native language Python files.

    This finder intercepts imports and checks if the source file
    is written in a native language. If so, it translates on-the-fly.

    The cache uses LRU eviction to keep memory usage bounded.
    """

    def __init__(self, language: str, cache_size: int = 128):
        """Initialize the finder with a target language and cache size.

        Args:
            language: Language code (e.g., 'es', 'ar', 'zh')
            cache_size: Maximum number of cache entries (default: 128)
        """
        self.language = language
        # EN->native translator (for future use)
        self.translator = TokenTranslator.from_language_pack(language)
        # native->EN translator (for executing native code)
        self.reverse_translator = self.translator.reverse()
        # LRU cache with configurable size
        self.cache = _TranslationCache(max_size=cache_size)

    def find_spec(self, fullname, path, target=None):
        """Find module spec for native language files.

        Args:
            fullname: Fully qualified module name
            path: Search path (None means sys.path)
            target: Module object (unused)

        Returns:
            ModuleSpec if found, None otherwise
        """
        # Validate module name to prevent path traversal
        if not all(part.isidentifier() for part in fullname.split(".")):
            return None  # Invalid module name

        # The normal import machinery always passes the parent package's
        # __path__ for a submodule, so a dotted fullname with path=None
        # never comes from it. Resolving the tail against all of sys.path
        # here would claim an unrelated top-level module (e.g. a stray
        # client.py as `http.client`), so decline instead.
        if path is None and "." in fullname:
            return None

        # Search for .py files in the import path
        if path is None:
            path = sys.path

        # For a submodule import (dotted name), the import machinery hands us
        # the parent package's __path__ entries, which already point INSIDE
        # the parent package. Only the final name component is resolved
        # against them — joining the full dotted path would look for
        # e.g. <stdlib>/http/http/client.py and never match, so dotted
        # imports either broke or silently bypassed translation.
        tail = fullname.rpartition(".")[2]

        for search_path in path:
            search_path = Path(search_path)
            module_path = search_path / tail

            # Security: Ensure resolved path is within search_path (prevent path traversal)
            try:
                module_path.resolve().relative_to(search_path.resolve())
            except ValueError:
                # Path traversal attempt detected
                continue

            # Check for package (__init__.py)
            init_file = module_path / "__init__.py"
            if init_file.exists():
                return self._create_spec(fullname, init_file, is_package=True)

            # Check for module (.py)
            module_file = module_path.with_suffix(".py")
            if module_file.exists():
                return self._create_spec(fullname, module_file, is_package=False)

        return None  # Not found - let other finders try

    def _create_spec(self, fullname, origin, is_package):
        """Create module spec with LegesherLoader.

        Args:
            fullname: Fully qualified module name
            origin: Path to source file
            is_package: Whether this is a package

        Returns:
            ModuleSpec configured with LegesherLoader
        """
        spec = importlib.machinery.ModuleSpec(
            name=fullname,
            loader=LegesherLoader(fullname, str(origin), self),
            origin=str(origin),
            is_package=is_package,
        )
        # A bare ModuleSpec defaults has_location to False, and the import
        # system only sets __file__ (and __cached__) for specs that have a
        # location, so every module this finder loaded had no __file__,
        # breaking code that locates resources relative to its own file.
        spec.has_location = True
        if is_package:
            # ModuleSpec(is_package=True) initializes submodule_search_locations
            # to an EMPTY list, so submodules of any package this finder claims
            # (including stdlib packages like `http`) became unimportable:
            # every finder searched an empty path and raised ModuleNotFoundError.
            # Point it at the package directory so submodule imports resolve
            # through us or delegate to the normal import machinery.
            spec.submodule_search_locations = [str(Path(origin).parent)]
        return spec

    def invalidate_caches(self):
        """Clear the translation cache.

        This is called by importlib when caches should be invalidated.
        """
        self.cache.clear()


class LegesherLoader(importlib.abc.SourceLoader):
    """Loader that translates native language source to Python bytecode."""

    def __init__(self, fullname: str, path: str, finder: LegesherMetaPathFinder):
        """Initialize the loader.

        Args:
            fullname: Fully qualified module name
            path: Path to source file
            finder: The finder that created this loader
        """
        self.fullname = fullname
        self.path = path
        self.finder = finder

    def get_filename(self, fullname):
        """Return the path to the source file.

        Args:
            fullname: Fully qualified module name

        Returns:
            String path to source file
        """
        return self.path

    def get_data(self, path):
        """Return the source code (translated to English if needed).

        Args:
            path: Path to source file

        Returns:
            Source code as bytes (translated to English)

        Raises:
            FileNotFoundError: If the source file doesn't exist
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"No such file: {path}")

        # Check cache first (use nanosecond precision for reliable invalidation)
        cache_key = (str(file_path), file_path.stat().st_mtime_ns)
        cached_result = self.finder.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Read native language source. read_text(encoding="utf-8") keeps a
        # leading BOM as U+FEFF, and UTF-8-with-BOM is a common editor default,
        # so strip it once here, ahead of both the parse probe and the
        # translator. Left in place it fuses onto the first token, so the
        # translator does not recognise the module's opening keyword and leaves
        # it native while translating the rest. The import machinery's own
        # decode step (utf-8-sig) drops the BOM anyway, so removing it costs
        # nothing for modules that pass through untranslated.
        native_source = file_path.read_text(encoding="utf-8")
        if native_source.startswith("\ufeff"):
            native_source = native_source[1:]

        # Detect if file needs translation
        if self._needs_translation(native_source):
            # Translate to English for Python runtime
            # Use reverse_translator (native->EN) to convert native code to English
            english_source = self.finder.reverse_translator.translate_code(
                native_source
            )

            # A failed probe only says the source is not valid Python: it is
            # either native-language or genuinely broken English. Translating
            # broken English rewrites unrelated identifiers and usually plants
            # an EARLIER error, so the compiler would blame a line the user
            # wrote correctly (under the es pack a valid `con = 5` becomes
            # `with = 5`). If the translation does not parse either it was not
            # helping, so discard it and hand back the original, letting the
            # compiler report the user's own error on the user's own line.
            try:
                ast.parse(english_source)
            except (SyntaxError, ValueError):
                english_source = native_source
            else:
                # Register source mapping for error reporting
                source_mapper = get_source_mapper()
                source_mapper.register_mapping(
                    filename=str(file_path),
                    native_source=native_source,
                    english_source=english_source,
                )
        else:
            # Already English - pass through
            english_source = native_source

        # Cache result
        translated_bytes = english_source.encode("utf-8")
        self.finder.cache.set(cache_key, translated_bytes)
        return translated_bytes

    def _needs_translation(self, source):
        """Detect whether the source must be translated to run as Python.

        Parse-first rule: source that already parses as valid Python is
        imported as-is. Native-language modules use native keywords in
        keyword position, which makes ``ast.parse`` fail, and that failure
        is the translation signal. A word-scan heuristic is not safe
        here: the finder claims every ``.py`` file on the search path, so
        flagging any module that merely shares a word with the pack's
        native vocabulary would corrupt plain-English modules (under the
        es pack, ``con = ...`` would become a ``SyntaxError`` because
        ``con`` renders ``with``, and an ``ErrorDeOS`` attribute would be
        silently renamed to ``OSError``).

        Accepted limitation: a native-language module that happens to
        parse as valid Python (e.g. it uses only translated builtins and
        no native keywords) is not translated. That matches the pre-fix
        behavior, where detection was permanently False: the old body
        guarded on a translator attribute that never existed, so the
        word-scan branch it guarded never ran. The durable fix is
        header-driven language detection.

        Args:
            source: Source code string, decoded and BOM-stripped by get_data

        Returns:
            True if translation needed, False otherwise
        """
        # CORE-1539 tracks header-driven language detection, the durable fix.
        try:
            ast.parse(source)
        except (SyntaxError, ValueError):
            # ValueError covers null bytes on older interpreters.
            return True
        return False


def _get_cache_size(explicit_size: int | None = None) -> int:
    """Resolve cache size from configuration sources.

    Precedence (highest to lowest):
    1. Explicit API parameter
    2. Environment variable (LEGESHER_CACHE_SIZE)
    3. Config file (.legesher/config.yml)
    4. Default value (128)

    Args:
        explicit_size: Explicit cache size from API call

    Returns:
        Resolved cache size (non-negative integer)
    """
    # 1. Explicit API parameter
    if explicit_size is not None:
        return max(0, explicit_size)  # Validate non-negative

    # 2. Environment variable
    env_size = os.getenv("LEGESHER_CACHE_SIZE")
    if env_size is not None:
        try:
            return max(0, int(env_size))
        except ValueError:
            logger.warning(
                f"Invalid LEGESHER_CACHE_SIZE environment variable: {env_size!r}, "
                "using config file or default"
            )

    # 3. Config file
    try:
        config = LegesherConfig.load()
        if (
            hasattr(config, "runtime_cache_size")
            and config.runtime_cache_size is not None
        ):
            return max(0, config.runtime_cache_size)
    except Exception as e:
        logger.debug(f"Could not load config for cache size: {e}")

    # 4. Default
    return 128


def install_import_hook(language: str | None = None, cache_size: int | None = None):
    """Install the Legesher import hook for native language execution.

    Args:
        language: Target language code (default: auto-detect from config)
        cache_size: Maximum cache entries (default: 128, configurable via env/config)

    Returns:
        LegesherMetaPathFinder instance that was installed

    Raises:
        RuntimeError: If import hook is already installed

    Example:
        >>> install_import_hook("es")  # Spanish with default cache
        >>> install_import_hook("es", cache_size=256)  # Spanish with larger cache
        >>> import mi_modulo  # Imports mi_modulo.py which contains Spanish code
    """
    # Check if already installed
    if is_hook_installed():
        raise RuntimeError("Legesher import hook is already installed")

    if language is None:
        config = LegesherConfig.load()
        language = config.language

    # Resolve cache size from configuration sources
    resolved_cache_size = _get_cache_size(cache_size)

    # Create and install the finder
    finder = LegesherMetaPathFinder(language, cache_size=resolved_cache_size)
    sys.meta_path.insert(0, finder)  # Insert at front for priority

    return finder


def uninstall_import_hook():
    """Remove Legesher import hooks from sys.meta_path.

    This removes all LegesherMetaPathFinder instances from the import system.
    """
    sys.meta_path = [
        finder
        for finder in sys.meta_path
        if not isinstance(finder, LegesherMetaPathFinder)
    ]


def is_hook_installed() -> bool:
    """Check if the Legesher import hook is installed.

    Returns:
        True if a LegesherMetaPathFinder is in sys.meta_path, False otherwise
    """
    return any(isinstance(finder, LegesherMetaPathFinder) for finder in sys.meta_path)


def get_installed_language() -> str | None:
    """Get the language of the installed import hook.

    Returns:
        Language code if hook is installed, None otherwise
    """
    for finder in sys.meta_path:
        if isinstance(finder, LegesherMetaPathFinder):
            return finder.language
    return None


def get_cache_stats() -> dict[str, Any] | None:
    """Get cache statistics from the installed import hook.

    Returns:
        Dictionary with cache statistics if hook is installed, None otherwise.
        Statistics include:
        - hits: Number of cache hits
        - misses: Number of cache misses
        - evictions: Number of evicted entries
        - size: Current cache size
        - max_size: Maximum cache size
        - hit_rate: Cache hit rate (hits / total lookups)

    Example:
        >>> stats = get_cache_stats()
        >>> print(f"Hit rate: {stats['hit_rate']:.1%}")
        Hit rate: 85.7%
    """
    for finder in sys.meta_path:
        if isinstance(finder, LegesherMetaPathFinder):
            return finder.cache.get_stats()
    return None


def clear_cache() -> None:
    """Clear the translation cache in the installed import hook.

    This clears all cached translations and resets statistics.
    If no import hook is installed, this is a no-op.

    Example:
        >>> clear_cache()  # Clear all cached translations
        >>> get_cache_stats()['size']
        0
    """
    for finder in sys.meta_path:
        if isinstance(finder, LegesherMetaPathFinder):
            finder.cache.clear()
