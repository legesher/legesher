"""Version index management for Python language packs.

This module handles loading and querying the version-index.yml file,
which tracks keyword changes across Python versions and enables
version-aware language pack inheritance.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from .exceptions import (
    CircularInheritanceError,
    MaxInheritanceDepthError,
    VersionIndexError,
    UnsupportedVersionError,
)


# Maximum inheritance chain depth to prevent infinite loops
MAX_INHERITANCE_DEPTH = 10


class AutoUpdateConfig(BaseModel):
    """Configuration for automatic version index updates."""

    enabled: bool = False
    source: str
    check_interval: str = "monthly"


class PythonVersionInfo(BaseModel):
    """Metadata for a specific Python version."""

    version: str
    added_keywords: list[str] = Field(default_factory=list)
    removed_keywords: list[str] = Field(default_factory=list)
    base: Optional[str] = None

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version string format (e.g., '3.10', '3.11')."""
        if not v:
            raise ValueError("Version cannot be empty")

        parts = v.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid version format: {v} (expected X.Y)")

        try:
            int(parts[0])
            int(parts[1])
        except ValueError:
            raise ValueError(f"Invalid version format: {v} (parts must be numeric)")

        return v


class VersionIndexSchema(BaseModel):
    """Schema for version-index.yml file."""

    python_versions: dict[str, dict[str, Any]]
    auto_update: Optional[AutoUpdateConfig] = None

    def to_version_infos(self) -> dict[str, PythonVersionInfo]:
        """Convert raw dict to PythonVersionInfo objects."""
        result = {}
        for version, data in self.python_versions.items():
            result[version] = PythonVersionInfo(
                version=version,
                added_keywords=data.get("added_keywords", []),
                removed_keywords=data.get("removed_keywords", []),
                base=data.get("base"),
            )
        return result


@dataclass
class VersionIndex:
    """Manages the Python version index and inheritance chains."""

    versions: dict[str, PythonVersionInfo] = field(default_factory=dict)
    auto_update_config: Optional[AutoUpdateConfig] = None
    _index_path: Optional[Path] = None

    @classmethod
    def load(cls, index_path: Path) -> "VersionIndex":
        """Load version index from YAML file.

        Args:
            index_path: Path to version-index.yml file

        Returns:
            Loaded VersionIndex instance

        Raises:
            VersionIndexError: If file cannot be loaded or is invalid
        """
        if not index_path.exists():
            raise VersionIndexError(
                str(index_path), f"Version index file not found: {index_path}"
            )

        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise VersionIndexError(str(index_path), "Empty version index file")

            # Validate with Pydantic schema
            schema = VersionIndexSchema(**data)
            versions = schema.to_version_infos()

            return cls(
                versions=versions,
                auto_update_config=schema.auto_update,
                _index_path=index_path,
            )

        except yaml.YAMLError as e:
            raise VersionIndexError(str(index_path), f"Invalid YAML: {e}")
        except Exception as e:
            raise VersionIndexError(str(index_path), f"Failed to load: {e}")

    def get_version_info(self, version: str) -> PythonVersionInfo:
        """Get metadata for a specific Python version.

        Args:
            version: Python version string (e.g., '3.10', '3.11')

        Returns:
            PythonVersionInfo for the requested version

        Raises:
            UnsupportedVersionError: If version is not in the index
        """
        if version not in self.versions:
            supported = list(self.versions.keys())
            raise UnsupportedVersionError(version, supported)

        return self.versions[version]

    def get_supported_versions(self) -> list[str]:
        """Get list of all supported Python versions.

        Returns:
            Sorted list of version strings
        """
        return sorted(self.versions.keys())

    def get_inheritance_chain(self, version: str) -> list[str]:
        """Build the inheritance chain for a version.

        Returns versions in order from oldest to newest (base to specific).

        Example:
            For Python 3.13: ['3.10', '3.11', '3.12', '3.13']

        Args:
            version: Python version string

        Returns:
            List of version strings in inheritance order

        Raises:
            UnsupportedVersionError: If version is not supported
            CircularInheritanceError: If circular inheritance detected
            MaxInheritanceDepthError: If chain exceeds max depth
        """
        if version not in self.versions:
            raise UnsupportedVersionError(version, self.get_supported_versions())

        chain = []
        visited = set()
        current = version

        while current:
            # Check for circular inheritance
            if current in visited:
                raise CircularInheritanceError(current, visited)

            # Check max depth
            if len(chain) >= MAX_INHERITANCE_DEPTH:
                raise MaxInheritanceDepthError(current, MAX_INHERITANCE_DEPTH)

            visited.add(current)
            chain.append(current)

            # Get base version
            info = self.versions.get(current)
            if not info or not info.base:
                break

            current = info.base

        # Reverse to get base-to-specific order
        return list(reversed(chain))

    def get_all_keywords(self, version: str) -> set[str]:
        """Get all keywords available in a Python version (including inherited).

        Args:
            version: Python version string

        Returns:
            Set of all keyword names

        Raises:
            UnsupportedVersionError: If version is not supported
        """
        chain = self.get_inheritance_chain(version)
        keywords = set()

        for v in chain:
            info = self.versions[v]
            keywords.update(info.added_keywords)
            keywords.difference_update(info.removed_keywords)

        return keywords

    def get_added_since(self, base_version: str, target_version: str) -> list[str]:
        """Get keywords added between two versions.

        Args:
            base_version: Starting version
            target_version: Ending version

        Returns:
            List of keywords added between versions

        Raises:
            UnsupportedVersionError: If either version is not supported
        """
        base_keywords = self.get_all_keywords(base_version)
        target_keywords = self.get_all_keywords(target_version)
        return sorted(target_keywords - base_keywords)

    def is_keyword_available(self, keyword: str, version: str) -> bool:
        """Check if a keyword is available in a specific Python version.

        Args:
            keyword: Keyword name to check
            version: Python version string

        Returns:
            True if keyword is available in the version

        Raises:
            UnsupportedVersionError: If version is not supported
        """
        keywords = self.get_all_keywords(version)
        return keyword in keywords

    def __repr__(self) -> str:
        """String representation of VersionIndex."""
        versions_str = ", ".join(self.get_supported_versions())
        return f"VersionIndex(versions=[{versions_str}])"
