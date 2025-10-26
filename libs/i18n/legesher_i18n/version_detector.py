"""Python version detection for language pack selection.

This module implements version detection with multiple strategies:
1. pyproject.toml requires-python field
2. .python-version file
3. Runtime sys.version_info
4. Default to latest supported version

Priority is given in the order listed above.
"""

import re
import sys
from pathlib import Path

# tomllib is only available in Python 3.11+, use tomli for older versions
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]
from typing import Optional

from packaging.specifiers import SpecifierSet

from .exceptions import VersionDetectionError


class PythonVersionDetector:
    """Detects the Python version for a project using multiple strategies."""

    DEFAULT_VERSION = "3.13"  # Fallback if detection fails

    def detect(self, project_path: Optional[Path] = None) -> str:
        """Detect Python version using all available strategies.

        Detection priority:
        1. pyproject.toml requires-python field
        2. .python-version file
        3. Runtime sys.version_info
        4. Default version (3.13)

        Args:
            project_path: Path to project root (defaults to current directory)

        Returns:
            Python version string (e.g., '3.10', '3.11', '3.12', '3.13')
        """
        if project_path is None:
            project_path = Path.cwd()

        # Strategy 1: pyproject.toml
        try:
            version = self.detect_from_pyproject(project_path)
            if version:
                return version
        except Exception:
            pass  # Continue to next strategy

        # Strategy 2: .python-version file
        try:
            version = self.detect_from_file(project_path)
            if version:
                return version
        except Exception:
            pass  # Continue to next strategy

        # Strategy 3: Runtime version
        try:
            version = self.detect_from_runtime()
            if version:
                return version
        except Exception:
            pass  # Fall through to default

        # Strategy 4: Default
        return self.DEFAULT_VERSION

    def detect_from_pyproject(self, project_path: Path) -> Optional[str]:
        """Detect Python version from pyproject.toml requires-python field.

        Parses the requires-python field and extracts the minimum or target
        Python version. Handles various formats:
        - '>=3.10'
        - '>=3.10,<4.0'
        - '^3.10'

        Args:
            project_path: Path to project root

        Returns:
            Python version string, or None if not found/parseable

        Raises:
            VersionDetectionError: If pyproject.toml is malformed
        """
        pyproject_path = project_path / "pyproject.toml"

        if not pyproject_path.exists():
            return None

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            requires_python = data.get("project", {}).get("requires-python")
            if not requires_python:
                return None

            return self._parse_requires_python(requires_python)

        except tomllib.TOMLDecodeError as e:
            raise VersionDetectionError(f"Malformed pyproject.toml: {e}")
        except Exception as e:
            raise VersionDetectionError(f"Failed to read pyproject.toml: {e}")

    def _parse_requires_python(self, requires_python: str) -> Optional[str]:
        """Parse requires-python field to extract version.

        Args:
            requires_python: Value from requires-python field

        Returns:
            Python version string (e.g., '3.10'), or None if unparseable
        """
        try:
            # Use packaging.specifiers to parse
            specifier = SpecifierSet(requires_python)

            # Extract minimum version from specifier
            # Look for >= or > operators
            for spec in specifier:
                if spec.operator in (">=", ">", "~=", "=="):
                    version_str = spec.version
                    return self._normalize_version(version_str)

            return None

        except Exception:
            # If packaging fails, try regex as fallback
            match = re.search(r"(\d+)\.(\d+)", requires_python)
            if match:
                major, minor = match.groups()
                return f"{major}.{minor}"

            return None

    def detect_from_file(self, project_path: Path) -> Optional[str]:
        """Detect Python version from .python-version file.

        This file is commonly used by pyenv and other version managers.

        Args:
            project_path: Path to project root

        Returns:
            Python version string, or None if not found

        Raises:
            VersionDetectionError: If file is malformed
        """
        python_version_file = project_path / ".python-version"

        if not python_version_file.exists():
            return None

        try:
            content = python_version_file.read_text(encoding="utf-8").strip()

            if not content:
                return None

            return self._normalize_version(content)

        except Exception as e:
            raise VersionDetectionError(f"Failed to read .python-version: {e}")

    def detect_from_runtime(self) -> str:
        """Detect Python version from current runtime.

        Uses sys.version_info to get the currently running Python version.

        Returns:
            Python version string (e.g., '3.10', '3.11')
        """
        major = sys.version_info.major
        minor = sys.version_info.minor
        return f"{major}.{minor}"

    def _normalize_version(self, version_str: str) -> str:
        """Normalize version string to X.Y format.

        Handles various formats:
        - '3.10.5' -> '3.10'
        - '3.10' -> '3.10'
        - 'python3.10' -> '3.10'

        Args:
            version_str: Raw version string

        Returns:
            Normalized version string (X.Y format)

        Raises:
            VersionDetectionError: If version cannot be normalized
        """
        # Remove common prefixes
        version_str = version_str.lower().replace("python", "").strip()

        # Extract X.Y from version
        match = re.search(r"(\d+)\.(\d+)", version_str)
        if not match:
            raise VersionDetectionError(f"Invalid version format: {version_str}")

        major, minor = match.groups()
        return f"{major}.{minor}"

    def is_version_compatible(
        self,
        required: str,
        available: str,
    ) -> bool:
        """Check if an available version satisfies a requirement.

        Args:
            required: Required version string (e.g., '>=3.10')
            available: Available version string (e.g., '3.11')

        Returns:
            True if available satisfies required
        """
        try:
            specifier = SpecifierSet(required)
            # Convert '3.11' to '3.11.0' for comparison
            available_version = f"{available}.0"
            return available_version in specifier
        except Exception:
            return False

    def __repr__(self) -> str:
        """String representation of version detector."""
        return f"PythonVersionDetector(default={self.DEFAULT_VERSION})"
