"""Legesher i18n: Internationalization and Language Pack Management.

This package provides version-aware language pack loading with inheritance,
Python version detection, and schema validation for multilingual programming.
"""

from .exceptions import (
    CircularInheritanceError,
    InheritanceError,
    LanguagePackError,
    MaxInheritanceDepthError,
    PackNotFoundError,
    PackValidationError,
    PathTraversalError,
    UnsupportedVersionError,
    VersionDetectionError,
    VersionIndexError,
)
from .language_registry import (
    CANONICAL_LANGUAGE,
    LANGUAGE_METADATA,
    get_active_language_codes,
    get_available_language_codes,
    get_language_name,
    get_native_name,
    get_rtl_language_codes,
    is_rtl_language,
    is_supported_language,
)
from .pack_loader import LanguagePack, LanguagePackLoader
from .schema_validator import (
    LanguagePackMetadata,
    LanguagePackSchema,
    SchemaValidator,
)
from .version_detector import PythonVersionDetector
from .version_index import PythonVersionInfo, VersionIndex

__version__ = "0.7.2"

__all__ = [
    # Main classes
    "LanguagePack",
    "LanguagePackLoader",
    "PythonVersionDetector",
    "VersionIndex",
    # Schema classes
    "LanguagePackSchema",
    "LanguagePackMetadata",
    "SchemaValidator",
    "PythonVersionInfo",
    # Language registry (single source of truth)
    "LANGUAGE_METADATA",
    "CANONICAL_LANGUAGE",
    "get_active_language_codes",
    "get_available_language_codes",
    "get_rtl_language_codes",
    "get_language_name",
    "get_native_name",
    "is_rtl_language",
    "is_supported_language",
    # Exceptions
    "LanguagePackError",
    "PackNotFoundError",
    "PackValidationError",
    "InheritanceError",
    "CircularInheritanceError",
    "MaxInheritanceDepthError",
    "PathTraversalError",
    "VersionDetectionError",
    "VersionIndexError",
    "UnsupportedVersionError",
    # Convenience functions
    "load_language_pack",
]


def load_language_pack(
    language: str,
    target: str = "python",
    version: str | None = None,
    project_path: str | None = None,
) -> LanguagePack:
    """Convenience function to load a language pack with automatic version detection.

    Args:
        language: Language code (e.g., 'es', 'ar', 'zh')
        target: Target programming language (default: 'python')
        version: Python version (e.g., '3.10', '3.13')
                If None, auto-detects from project
        project_path: Path to project root for version detection
                     If None, uses current directory

    Returns:
        Loaded LanguagePack with all translations

    Raises:
        PackNotFoundError: If pack doesn't exist
        VersionDetectionError: If version cannot be detected

    Example:
        >>> # Auto-detect version
        >>> pack = load_language_pack('es')
        >>> print(pack.get_keyword_translation('def'))
        'definir'

        >>> # Explicit version
        >>> pack = load_language_pack('es', version='3.11')
        >>> print(pack.get_keyword_translation('except*'))
        'excepto*'
    """
    from pathlib import Path

    if version is None:
        detector = PythonVersionDetector()
        project_root = Path(project_path) if project_path else None
        version = detector.detect(project_root)

    loader = LanguagePackLoader()
    return loader.load(language, target, version)
