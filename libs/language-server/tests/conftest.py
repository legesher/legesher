"""Shared pytest fixtures for language server tests."""

import logging
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from tests.fixtures.mock_output_channel import MockOutputChannel

# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture
def fixtures_dir() -> Path:
    """Get path to test fixtures directory.

    Returns:
        Path to tests/fixtures directory
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def language_packs_dir(fixtures_dir: Path) -> Path:
    """Get path to language packs fixtures directory.

    Returns:
        Path to fixtures/language_packs directory
    """
    return fixtures_dir / "language_packs"


@pytest.fixture
def valid_packs_dir(language_packs_dir: Path) -> Path:
    """Get path to valid language packs fixtures.

    Returns:
        Path to language_packs/valid directory
    """
    return language_packs_dir / "valid"


@pytest.fixture
def invalid_packs_dir(language_packs_dir: Path) -> Path:
    """Get path to invalid language packs fixtures.

    Returns:
        Path to language_packs/invalid directory
    """
    return language_packs_dir / "invalid"


@pytest.fixture
def mixed_packs_dir(language_packs_dir: Path) -> Path:
    """Get path to mixed language packs fixtures.

    Returns:
        Path to language_packs/mixed directory
    """
    return language_packs_dir / "mixed"


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================


@pytest.fixture
def temp_pack_dir() -> Generator[Path, None, None]:
    """Create temporary directory for pack files.

    Yields:
        Temporary directory path (auto-cleaned up)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ============================================================================
# Mock Object Fixtures
# ============================================================================


@pytest.fixture
def mock_output_channel() -> MockOutputChannel:
    """Mock VS Code output channel for logging.

    Returns:
        MockOutputChannel instance with append_line() and other methods
    """
    return MockOutputChannel(name="Test Channel")


# ============================================================================
# Logging Fixtures
# ============================================================================


@pytest.fixture
def caplog_for_yaml_errors(caplog):
    """Fixture to capture logging output for YAML errors.

    Args:
        caplog: pytest's caplog fixture

    Returns:
        caplog with log level set to capture all messages
    """
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def clean_logs(caplog):
    """Fixture that clears logs between tests.

    Args:
        caplog: pytest's caplog fixture

    Yields:
        caplog instance
    """
    caplog.clear()
    yield caplog
    caplog.clear()


# ============================================================================
# Test Markers
# ============================================================================


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "keyword_docs: tests for KeywordDocumentation module")
    config.addinivalue_line("markers", "pack_discovery: tests for pack file discovery")
    config.addinivalue_line("markers", "yaml_parsing: tests for YAML parsing errors")
    config.addinivalue_line("markers", "schema_validation: tests for pack schema validation")
    config.addinivalue_line("markers", "data_validation: tests for pack data validation")
    config.addinivalue_line("markers", "version_fallback: tests for Python version fallback")
    config.addinivalue_line("markers", "language_fallback: tests for language fallback")
    config.addinivalue_line("markers", "output_channel: tests for output channel logging")
    config.addinivalue_line("markers", "integration: integration tests for end-to-end workflows")
