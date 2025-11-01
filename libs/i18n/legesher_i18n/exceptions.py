"""Custom exceptions for the Legesher i18n package.

This module defines exception classes for language pack loading, validation,
version detection, and inheritance resolution.
"""

from typing import Optional


class LanguagePackError(Exception):
    """Base exception for all language pack-related errors."""

    pass


class PackNotFoundError(LanguagePackError):
    """Raised when a requested language pack cannot be found."""

    def __init__(
        self,
        language: str,
        target: str,
        version: str,
        pack_path: str,
        available_languages: Optional[list[tuple[str, str]]] = None,
    ):
        self.language = language
        self.target = target
        self.version = version
        self.pack_path = pack_path
        self.available_languages = available_languages

        # Build error message with available languages if provided
        msg = f"Language pack not found: '{language}' for {target} {version}\n"
        msg += f"Searched: {pack_path}\n"

        if available_languages:
            msg += "\nAvailable languages:\n"
            for code, name in available_languages:
                msg += f"  - {code} ({name})\n"
            msg += "\nTo add a new language pack, see: https://docs.legesher.io/guides/creating-packs"

        super().__init__(msg)


class PackValidationError(LanguagePackError):
    """Raised when a language pack fails schema validation."""

    def __init__(self, pack_path: str, errors: list[str]):
        self.pack_path = pack_path
        self.errors = errors
        error_msg = "\n  - ".join(errors)
        super().__init__(
            f"Language pack validation failed: {pack_path}\n  - {error_msg}"
        )


class InheritanceError(LanguagePackError):
    """Raised when there's a problem with language pack inheritance."""

    pass


class CircularInheritanceError(InheritanceError):
    """Raised when circular inheritance is detected."""

    def __init__(self, pack_path: str, visited: set[str]):
        self.pack_path = pack_path
        self.visited = visited
        chain = " -> ".join(visited)
        super().__init__(f"Circular inheritance detected: {chain} -> {pack_path}")


class MaxInheritanceDepthError(InheritanceError):
    """Raised when inheritance depth exceeds maximum allowed."""

    def __init__(self, pack_path: str, max_depth: int):
        self.pack_path = pack_path
        self.max_depth = max_depth
        super().__init__(
            f"Maximum inheritance depth ({max_depth}) exceeded for pack: {pack_path}"
        )


class PathTraversalError(LanguagePackError):
    """Raised when a path traversal attack is detected."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Path traversal detected (security violation): {path}")


class VersionDetectionError(LanguagePackError):
    """Raised when Python version cannot be detected."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Failed to detect Python version: {reason}")


class VersionIndexError(LanguagePackError):
    """Raised when there's a problem with the version index."""

    def __init__(self, index_path: str, reason: str):
        self.index_path = index_path
        self.reason = reason
        super().__init__(f"Version index error ({index_path}): {reason}")


class UnsupportedVersionError(LanguagePackError):
    """Raised when a Python version is not supported."""

    def __init__(self, version: str, supported_versions: list[str]):
        self.version = version
        self.supported_versions = supported_versions
        supported = ", ".join(supported_versions)
        super().__init__(
            f"Python version {version} is not supported. "
            f"Supported versions: {supported}"
        )
