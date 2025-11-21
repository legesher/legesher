"""Universal import hook for native language Python execution.

This module implements Python's import protocol (PEP 302) to enable
seamless execution of Python code written in any natural language.

The key insight: Instead of "translating" to English, we compile
native language code directly to Python bytecode, making all languages
first-class citizens.

Example:
    >>> from legesher.runtime import install_import_hook
    >>> install_import_hook(language="es")
    >>> import mi_modulo  # Works seamlessly with Spanish code!
"""

import sys
import importlib.abc
import importlib.machinery
from pathlib import Path
from typing import Optional

from legesher_core import TokenTranslator
from legesher.config import LegesherConfig
from legesher.runtime.source_mapper import get_source_mapper


class LegesherMetaPathFinder(importlib.abc.MetaPathFinder):
    """Universal import hook for native language Python files.

    This finder intercepts imports and checks if the source file
    is written in a native language. If so, it translates on-the-fly.
    """

    def __init__(self, language: str):
        """Initialize the finder with a target language.

        Args:
            language: Language code (e.g., 'es', 'ar', 'zh')
        """
        self.language = language
        self.translator = TokenTranslator.from_language_pack(language)
        self._cache = {}  # bytecode cache: (path, mtime) -> translated_bytes

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

        # Search for .py files in the import path
        if path is None:
            path = sys.path

        for search_path in path:
            search_path = Path(search_path)
            module_path = search_path / fullname.replace(".", "/")

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
        return importlib.machinery.ModuleSpec(
            name=fullname,
            loader=LegesherLoader(origin, self.translator, self._cache, self.language),
            origin=str(origin),
            is_package=is_package,
        )


class LegesherLoader(importlib.abc.SourceLoader):
    """Loader that translates native language source to Python bytecode."""

    def __init__(self, path, translator, cache, language):
        """Initialize the loader.

        Args:
            path: Path to source file
            translator: TokenTranslator instance
            cache: Shared cache dictionary
            language: Language code (e.g., 'es', 'ar', 'zh')
        """
        self.path = Path(path)
        self.translator = translator
        self.cache = cache
        self.language = language

    def get_filename(self, fullname):
        """Return the path to the source file.

        Args:
            fullname: Fully qualified module name

        Returns:
            String path to source file
        """
        return str(self.path)

    def get_data(self, path):
        """Return the source code (translated to English if needed).

        Args:
            path: Path to source file

        Returns:
            Source code as bytes (translated to English)
        """
        # Check cache first (use nanosecond precision for reliable invalidation)
        cache_key = (str(self.path), self.path.stat().st_mtime_ns)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Read native language source
        native_source = self.path.read_text(encoding="utf-8")

        # Detect if file needs translation
        if self._needs_translation(native_source):
            # Translate to English for Python runtime
            # The translator is configured for a target language
            # So we translate FROM target language TO English
            english_source = self.translator.translate_code(
                native_source,
                source_lang=self.language,
                target_lang="en",
            )

            # Register source mapping for error reporting
            source_mapper = get_source_mapper()
            source_mapper.register_mapping(
                filename=str(self.path),
                native_source=native_source,
                english_source=english_source,
            )
        else:
            # Already English - pass through
            english_source = native_source

        # Cache result
        translated_bytes = english_source.encode("utf-8")
        self.cache[cache_key] = translated_bytes
        return translated_bytes

    def _needs_translation(self, source):
        """Detect if source contains native language keywords.

        Args:
            source: Source code string

        Returns:
            True if translation needed, False otherwise
        """
        # Check for translated keywords (simple heuristic)
        # Get all translated keywords from the language pack
        if hasattr(self.translator, "translation_pack"):
            translated_keywords = []
            for version_data in self.translator.translation_pack.versions.values():
                if hasattr(version_data, "keywords"):
                    translated_keywords.extend(version_data.keywords.values())

            # Check if any translated keyword appears in source
            return any(keyword in source for keyword in translated_keywords if keyword)

        return False


def install_import_hook(language: Optional[str] = None):
    """Install the Legesher import hook for native language execution.

    Args:
        language: Target language code (default: auto-detect from config)

    Returns:
        LegesherMetaPathFinder instance that was installed

    Example:
        >>> install_import_hook("es")  # Spanish
        >>> import mi_modulo  # Imports mi_modulo.py which contains Spanish code
    """
    # Remove any existing Legesher hooks first to prevent duplicates
    uninstall_import_hook()

    if language is None:
        config = LegesherConfig.load()
        language = config.language

    # Create and install the finder
    finder = LegesherMetaPathFinder(language)
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
