"""Tests for version_detector module."""

import sys
import pytest
from pathlib import Path

from legesher_i18n.version_detector import PythonVersionDetector
from legesher_i18n.exceptions import VersionDetectionError


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "projects"


class TestVersionDetector:
    """Test Python version detection."""

    def test_detect_from_runtime(self):
        """Test detection from sys.version_info."""
        detector = PythonVersionDetector()
        version = detector.detect_from_runtime()

        # Should match current Python version
        expected = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert version == expected

    def test_detect_from_pyproject(self):
        """Test detection from pyproject.toml."""
        detector = PythonVersionDetector()
        project_path = FIXTURES_DIR / "with_pyproject"

        version = detector.detect_from_pyproject(project_path)

        assert version is not None
        assert version == "3.11"  # From requires-python = ">=3.11,<4.0"

    def test_detect_from_python_version_file(self):
        """Test detection from .python-version file."""
        detector = PythonVersionDetector()
        project_path = FIXTURES_DIR / "with_python_version"

        version = detector.detect_from_file(project_path)

        assert version == "3.12"

    def test_detect_priority(self):
        """Test that detect() follows correct priority order."""
        detector = PythonVersionDetector()

        # With valid pyproject.toml
        version = detector.detect(FIXTURES_DIR / "with_pyproject")
        assert version == "3.11"  # From pyproject.toml

        # With .python-version file
        version = detector.detect(FIXTURES_DIR / "with_python_version")
        assert version == "3.12"  # From .python-version

        # With neither, should fall back to runtime
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            version = detector.detect(Path(tmpdir))
            # Should match runtime version
            expected = f"{sys.version_info.major}.{sys.version_info.minor}"
            assert version == expected

    def test_detect_nonexistent_project(self):
        """Test detection on nonexistent project path."""
        detector = PythonVersionDetector()

        # Should fall back to runtime version
        version = detector.detect(Path("/nonexistent/project"))
        expected = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert version == expected

    def test_normalize_version(self):
        """Test version string normalization."""
        detector = PythonVersionDetector()

        # Test various formats
        assert detector._normalize_version("3.10.5") == "3.10"
        assert detector._normalize_version("3.10") == "3.10"
        assert detector._normalize_version("python3.10") == "3.10"
        assert detector._normalize_version("  3.11  ") == "3.11"

    def test_normalize_invalid_version(self):
        """Test normalization with invalid version."""
        detector = PythonVersionDetector()

        with pytest.raises(VersionDetectionError):
            detector._normalize_version("invalid")

        with pytest.raises(VersionDetectionError):
            detector._normalize_version("")

    def test_parse_requires_python_formats(self):
        """Test parsing various requires-python formats."""
        detector = PythonVersionDetector()

        assert detector._parse_requires_python(">=3.10") == "3.10"
        assert detector._parse_requires_python(">=3.10,<4.0") == "3.10"
        assert detector._parse_requires_python(">3.9") == "3.9"
        assert detector._parse_requires_python("==3.11") == "3.11"

    def test_is_version_compatible(self):
        """Test version compatibility checking."""
        detector = PythonVersionDetector()

        assert detector.is_version_compatible(">=3.10", "3.11")
        assert detector.is_version_compatible(">=3.10,<4.0", "3.12")
        assert not detector.is_version_compatible(">=3.11", "3.10")
        assert not detector.is_version_compatible("<3.11", "3.12")

    def test_repr(self):
        """Test __repr__ method."""
        detector = PythonVersionDetector()
        repr_str = repr(detector)

        assert "PythonVersionDetector" in repr_str
        assert "3.13" in repr_str  # Default version
