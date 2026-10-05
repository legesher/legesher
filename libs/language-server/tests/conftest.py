"""Shared pytest fixtures for language server tests."""

import logging
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from tests import timing
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


@pytest.fixture(scope="session")
def stub_launcher(tmp_path_factory) -> str:
    """An executable that starts the stub language server on any platform.

    The proxy spawns its language server as ``[path, "--stdio"]``, so ``path``
    must be something the OS can execute directly. A bare ``.py`` file satisfies
    that on POSIX via its shebang but not on Windows — where the CI matrix does
    run this suite on pushes to main. That gap would have been invisible on the
    pull request, since PRs are ubuntu-only.

    A shim that re-invokes the current interpreter keeps one code path for every
    platform.
    """
    stub = Path(__file__).parent / "fixtures" / "stub_langserver.py"
    directory = tmp_path_factory.mktemp("stub-launcher")

    if sys.platform == "win32":
        launcher = directory / "stub-langserver.cmd"
        launcher.write_text(f'@echo off\r\n"{sys.executable}" "{stub}" %*\r\n')
    else:
        launcher = directory / "stub-langserver"
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{stub}" "$@"\n')
        launcher.chmod(0o755)

    return str(launcher)


_DRIFT_ITEMS: set[str] = set()


def pytest_collection_modifyitems(items):
    """Record which tests guard the stub against drifting from a real server."""
    for item in items:
        if item.get_closest_marker("langserver_drift"):
            _DRIFT_ITEMS.add(item.nodeid)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Say plainly when the drift check did not run (CORE-1886).

    The transport is covered by a stub language server, which encodes our
    beliefs about how a real one behaves. If those beliefs are wrong, every stub
    test passes and the product is still broken — which is exactly what happened
    here: a passing test file sat beside this feature the entire time it was
    dead.

    A silently skipped drift check reports green having verified nothing. That
    is the same class of unearned success this ticket exists to stop, so the
    skip is stated rather than swallowed.
    """
    if not _DRIFT_ITEMS:
        return

    skipped = {report.nodeid for report in terminalreporter.stats.get("skipped", [])}
    missed = sorted(_DRIFT_ITEMS & skipped)
    if not missed:
        return

    terminalreporter.write_sep("=", "STUB DRIFT CHECK DID NOT RUN", yellow=True, bold=True)
    terminalreporter.write_line(
        "The language-server transport was exercised against the stub only. Nothing "
        "in this run verified that the stub still matches a real pyright-langserver."
    )
    terminalreporter.write_line("")
    for nodeid in missed:
        terminalreporter.write_line(f"  skipped: {nodeid}")
    terminalreporter.write_line("")
    terminalreporter.write_line(
        "To run it locally:  npm install -g pyright   (provides `pyright-langserver`)"
    )
    terminalreporter.write_line(
        "Otherwise it runs on the weekly Language Server Drift Check workflow."
    )


def pytest_addoption(parser):
    """``--timing`` turns on the wall-clock bounds in ``tests/timing.py``."""
    parser.addoption(
        "--timing",
        action="store_true",
        default=False,
        help="enforce wall-clock bounds (make bench passes this with -m timing)",
    )


def pytest_report_header(config):
    """Say whether this run enforces wall-clock bounds, so their absence is not silent."""
    if config.getoption("--timing"):
        return "timing: assert_within bounds enforced"
    return "timing: assert_within bounds not enforced (make bench enforces them)"


def pytest_configure(config):
    """Register custom pytest markers, and set the timing mode."""
    timing.ENFORCED = config.getoption("--timing")
    config.addinivalue_line(
        "markers",
        "langserver_drift: verifies the stub language server still matches a real one",
    )
    config.addinivalue_line("markers", "keyword_docs: tests for KeywordDocumentation module")
    config.addinivalue_line("markers", "pack_discovery: tests for pack file discovery")
    config.addinivalue_line("markers", "yaml_parsing: tests for YAML parsing errors")
    config.addinivalue_line("markers", "schema_validation: tests for pack schema validation")
    config.addinivalue_line("markers", "data_validation: tests for pack data validation")
    config.addinivalue_line("markers", "version_fallback: tests for Python version fallback")
    config.addinivalue_line("markers", "language_fallback: tests for language fallback")
    config.addinivalue_line("markers", "output_channel: tests for output channel logging")
    config.addinivalue_line("markers", "integration: integration tests for end-to-end workflows")
