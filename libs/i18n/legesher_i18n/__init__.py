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
    Finding,
    LanguagePackMetadata,
    LanguagePackSchema,
    SchemaValidator,
)
from .script_policy import ScriptPolicy, policy_for, scripts_of
from .prompt_builder import PromptBuilder
from .style_guides import StyleGuideLoader
from .version_detector import PythonVersionDetector
from .version_index import PythonVersionInfo, VersionIndex

__version__ = "0.21.2"

__all__ = [
    # Core pack loading
    "LanguagePack",
    "LanguagePackLoader",
    # Prompt building
    "PromptBuilder",
    "StyleGuideLoader",
    # Language registry
    "CANONICAL_LANGUAGE",
    "LANGUAGE_METADATA",
    "get_active_language_codes",
    "get_available_language_codes",
    "get_language_name",
    "get_native_name",
    "get_rtl_language_codes",
    "is_rtl_language",
    "is_supported_language",
    # Schema & validation
    "Finding",
    "LanguagePackMetadata",
    "LanguagePackSchema",
    "SchemaValidator",
    # Script policy (Unicode safety)
    "ScriptPolicy",
    "policy_for",
    "scripts_of",
    # Version detection
    "PythonVersionDetector",
    "PythonVersionInfo",
    "VersionIndex",
    # Exceptions
    "CircularInheritanceError",
    "InheritanceError",
    "LanguagePackError",
    "MaxInheritanceDepthError",
    "PackNotFoundError",
    "PackValidationError",
    "PathTraversalError",
    "UnsupportedVersionError",
    "VersionDetectionError",
    "VersionIndexError",
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
