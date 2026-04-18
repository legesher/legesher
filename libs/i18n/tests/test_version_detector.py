"""Tests for version_detector module."""

import re
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


class TestVersionDetectorErrorPaths:
    """CORE-1112: coverage for error-handling branches in PythonVersionDetector.

    Exercises the fallthrough behavior between detection strategies and
    every except branch in the individual detectors so a future rewrite
    can't silently swallow a different class of error.
    """

    def test_detect_falls_through_pyproject_error_to_file(self, tmp_path):
        """If pyproject.toml parsing raises, detect() moves to the
        .python-version strategy."""
        # Malformed pyproject.toml raises VersionDetectionError
        (tmp_path / "pyproject.toml").write_text(
            "this is not [ valid toml", encoding="utf-8"
        )
        # Valid .python-version file is the fallback
        (tmp_path / ".python-version").write_text("3.11\n", encoding="utf-8")

        detector = PythonVersionDetector()
        assert detector.detect(tmp_path) == "3.11"

    def test_detect_falls_through_file_error_to_runtime(self, tmp_path):
        """If both pyproject and .python-version fail, detect() uses
        the runtime version."""
        # Malformed pyproject and malformed .python-version
        (tmp_path / "pyproject.toml").write_text(":not:valid:", encoding="utf-8")
        # An unreadable .python-version: write bogus bytes that cause
        # _normalize_version to raise VersionDetectionError
        (tmp_path / ".python-version").write_text("no-digits-here", encoding="utf-8")
        detector = PythonVersionDetector()
        result = detector.detect(tmp_path)
        # Should have fallen through to runtime version
        assert re.match(r"^3\.\d+$", result)

    def test_detect_returns_default_when_nothing_exists(self, tmp_path):
        """An empty directory with no config files returns runtime version
        (strategy 3) — strategy 4 (DEFAULT_VERSION) only fires if even
        runtime detection somehow fails, which is essentially impossible.
        This test pins the happy no-config path that exits at strategy 3."""
        detector = PythonVersionDetector()
        result = detector.detect(tmp_path)
        assert re.match(r"^3\.\d+$", result)

    def test_detect_from_pyproject_missing_requires_python_returns_none(self, tmp_path):
        """pyproject.toml without a requires-python field returns None
        so the caller can try the next strategy."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\n', encoding="utf-8"
        )
        detector = PythonVersionDetector()
        assert detector.detect_from_pyproject(tmp_path) is None

    def test_detect_from_pyproject_malformed_raises(self, tmp_path):
        """Malformed TOML raises VersionDetectionError with a helpful message."""
        (tmp_path / "pyproject.toml").write_text(
            "this is not valid toml {{ [[", encoding="utf-8"
        )
        detector = PythonVersionDetector()
        with pytest.raises(VersionDetectionError, match="Malformed pyproject.toml"):
            detector.detect_from_pyproject(tmp_path)

    def test_parse_requires_python_regex_fallback(self):
        """When packaging.SpecifierSet fails, the regex fallback should
        still extract a version from a well-formed string."""
        detector = PythonVersionDetector()
        # A specifier packaging can't parse, but regex can
        # (e.g., Poetry's caret ranges aren't PEP 440)
        assert detector._parse_requires_python("^3.10") == "3.10"

    def test_parse_requires_python_returns_none_when_unparseable(self):
        """Completely unparseable input returns None."""
        detector = PythonVersionDetector()
        assert detector._parse_requires_python("not a version") is None

    def test_parse_requires_python_returns_none_on_unusable_operator(self):
        """A specifier with only `<` or `!=` operators has no extractable
        minimum — returns None."""
        detector = PythonVersionDetector()
        # `<` alone has no minimum; packaging parses it, but no usable op
        assert detector._parse_requires_python("<3.10") is None

    def test_detect_from_file_empty_returns_none(self, tmp_path):
        """An empty .python-version file returns None so the caller can
        try the next strategy."""
        (tmp_path / ".python-version").write_text("", encoding="utf-8")
        detector = PythonVersionDetector()
        assert detector.detect_from_file(tmp_path) is None

    def test_detect_from_file_unreadable_raises(self, tmp_path):
        """If reading the file fails, raise VersionDetectionError."""
        # _normalize_version will raise on content without digits, and
        # detect_from_file wraps that in VersionDetectionError
        (tmp_path / ".python-version").write_text(
            "no digits anywhere", encoding="utf-8"
        )
        detector = PythonVersionDetector()
        with pytest.raises(VersionDetectionError):
            detector.detect_from_file(tmp_path)

    def test_is_version_compatible_invalid_input_returns_false(self):
        """Garbage input doesn't raise — it returns False. Keeps callers
        from needing try/except around every compatibility probe."""
        detector = PythonVersionDetector()
        assert detector.is_version_compatible("not-a-specifier", "3.10") is False
        assert detector.is_version_compatible(">=3.10", "not-a-version") is False
