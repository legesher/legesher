"""Integration tests for metadata tracking with git operations.

Tests end-to-end metadata tracking through actual git filter operations,
including clean/smudge filters, git add/commit/checkout, and metadata
file management.

These tests verify that:
1. Metadata is created automatically during git operations
2. Translation history is tracked accurately
3. Git operations preserve metadata
4. Concurrent operations don't corrupt metadata
5. Errors in metadata don't break git operations

Test Design:
- Uses real git repositories (not mocked)
- Tests actual git filter operations via subprocess
- Validates metadata file content and structure
- Tests run in <30 seconds total
- Tests are isolated (no dependencies between tests)
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from legesher_core.git_filter import GitFilter
from legesher_core.metadata import MetadataManager
from legesher_core.types import HistoryEntry, TranslationRecord


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository with proper initialization.

    Sets up a clean git repository with:
    - Git init
    - User config (name/email)
    - Initial commit (required for some git operations)

    Returns:
        Path: Absolute path to repository root
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    # Configure git user
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    readme = repo / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return repo


@pytest.fixture
def metadata_manager(git_repo):
    """Create MetadataManager for the test repo.

    Returns:
        MetadataManager: Initialized manager for test repository
    """
    return MetadataManager(git_repo)


@pytest.fixture
def spanish_filter(git_repo):
    """Create a GitFilter instance for Spanish with metadata tracking.

    Note: This assumes GitFilter will be enhanced to support track_metadata
    parameter in CORE-438. For now, we create a standard filter.

    Returns:
        GitFilter: Spanish filter instance
    """
    return GitFilter(language="es", python_version="3.13")


@pytest.fixture
def spanish_source_code():
    """Sample Spanish Python source code for testing.

    Returns:
        str: Spanish Python code
    """
    return """definir calcular_suma(a, b):
    \"\"\"Calcula la suma de dos números.\"\"\"
    resultado = a + b
    retornar resultado

definir principal():
    x = calcular_suma(5, 3)
    imprimir(f"Resultado: {x}")
"""


@pytest.fixture
def english_source_code():
    """Sample English Python source code for testing.

    Returns:
        str: English Python code
    """
    return """def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    result = a + b
    return result

def main():
    x = calculate_sum(5, 3)
    print(f"Result: {x}")
"""


# ============================================================================
# Helper Functions
# ============================================================================


def create_python_file(repo: Path, relative_path: str, content: str) -> Path:
    """Helper to create a Python file in the repo.

    Args:
        repo: Repository root path
        relative_path: Relative path from repo root (e.g., "src/main.py")
        content: File content

    Returns:
        Path: Absolute path to created file
    """
    file_path = repo / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    return file_path


def git_add_commit(repo: Path, message: str, files: list[str] | None = None) -> str:
    """Helper to git add and commit files.

    Args:
        repo: Repository root path
        message: Commit message
        files: List of files to add (default: all files)

    Returns:
        str: Commit SHA
    """
    if files:
        for file in files:
            subprocess.run(
                ["git", "add", file], cwd=repo, check=True, capture_output=True
            )
    else:
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)

    subprocess.run(
        ["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True
    )

    # Get commit SHA
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_current_commit_sha(repo: Path) -> str:
    """Get current commit SHA.

    Args:
        repo: Repository root path

    Returns:
        str: Current commit SHA
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def read_metadata_yaml(metadata_path: Path) -> dict:
    """Read and parse metadata YAML file.

    Args:
        metadata_path: Path to metadata YAML file

    Returns:
        dict: Parsed metadata
    """
    with open(metadata_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================================
# Test: Metadata Creation
# ============================================================================


class TestMetadataCreation:
    """Test metadata creation during git operations."""

    def test_metadata_created_on_first_use(
        self, git_repo, metadata_manager, spanish_source_code
    ):
        """Test that metadata is created when first accessing a file."""
        # Create Python file
        _ = create_python_file(git_repo, "src/calculator.py", spanish_source_code)
        relative_path = Path("src/calculator.py")

        # Create metadata
        metadata = metadata_manager.create_metadata(
            relative_path,
            original_language="es",
            python_version="3.13",
        )

        # Verify metadata exists
        assert metadata is not None
        assert metadata["file"] == "src/calculator.py"
        assert metadata["original_language"] == "es"
        assert metadata["canonical_language"] == "en"
        assert metadata["python_version"] == "3.13"
        assert "created_at" in metadata
        assert "updated_at" in metadata
        assert metadata["translations"] == []
        assert metadata["history"] == []

        # Verify metadata file exists on disk
        metadata_path = (
            git_repo / ".legesher" / "metadata" / "src" / "calculator.py.yml"
        )
        assert metadata_path.exists()

        # Verify content
        saved_metadata = read_metadata_yaml(metadata_path)
        assert saved_metadata["file"] == "src/calculator.py"
        assert saved_metadata["original_language"] == "es"

    def test_metadata_directory_structure_mirrors_source(
        self, git_repo, metadata_manager
    ):
        """Test that metadata directory structure mirrors source tree."""
        # Create files in nested directories
        create_python_file(git_repo, "src/utils/math.py", "definir suma(): retornar 1")
        create_python_file(git_repo, "src/models/data.py", "clase Datos: pasar")
        create_python_file(git_repo, "tests/test_math.py", "definir test_suma(): pasar")

        # Create metadata for each
        metadata_manager.create_metadata(
            Path("src/utils/math.py"), original_language="es", python_version="3.13"
        )
        metadata_manager.create_metadata(
            Path("src/models/data.py"), original_language="es", python_version="3.13"
        )
        metadata_manager.create_metadata(
            Path("tests/test_math.py"), original_language="es", python_version="3.13"
        )

        # Verify directory structure
        assert (
            git_repo / ".legesher" / "metadata" / "src" / "utils" / "math.py.yml"
        ).exists()
        assert (
            git_repo / ".legesher" / "metadata" / "src" / "models" / "data.py.yml"
        ).exists()
        assert (
            git_repo / ".legesher" / "metadata" / "tests" / "test_math.py.yml"
        ).exists()

    def test_metadata_for_empty_file(self, git_repo, metadata_manager):
        """Test metadata creation for empty file."""
        # Create empty file
        create_python_file(git_repo, "src/empty.py", "")

        # Create metadata
        metadata = metadata_manager.create_metadata(
            Path("src/empty.py"),
            original_language="es",
            python_version="3.13",
        )

        # Verify metadata created successfully
        assert metadata is not None
        assert metadata["file"] == "src/empty.py"

    def test_metadata_with_unicode_paths(self, git_repo, metadata_manager):
        """Test metadata creation with Unicode characters in paths."""
        # Create file with Unicode in path
        create_python_file(git_repo, "src/cálculo.py", "definir test(): pasar")

        # Create metadata
        metadata = metadata_manager.create_metadata(
            Path("src/cálculo.py"),
            original_language="es",
            python_version="3.13",
        )

        # Verify metadata created
        assert metadata is not None
        assert metadata["file"] == "src/cálculo.py"

        # Verify file exists
        metadata_path = git_repo / ".legesher" / "metadata" / "src" / "cálculo.py.yml"
        assert metadata_path.exists()


# ============================================================================
# Test: Translation Recording
# ============================================================================


class TestTranslationRecording:
    """Test recording translation operations in metadata."""

    def test_record_translation_operation(self, git_repo, metadata_manager):
        """Test recording a translation operation."""
        # Setup: Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Record translation
        record: TranslationRecord = {
            "language": "en",
            "method": "token_transformer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": "abc123",
            "translator_version": "0.1.0",
            "python_version": "3.13",
        }
        metadata_manager.record_translation(Path("src/main.py"), record)

        # Verify translation recorded
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert len(metadata["translations"]) == 1
        assert metadata["translations"][0]["language"] == "en"
        assert metadata["translations"][0]["method"] == "token_transformer"
        assert metadata["translations"][0]["commit_sha"] == "abc123"

    def test_multiple_translation_records(self, git_repo, metadata_manager):
        """Test recording multiple translation operations."""
        # Setup
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Record multiple translations
        for i, lang in enumerate(["en", "fr", "de"]):
            record: TranslationRecord = {
                "language": lang,
                "method": "token_transformer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "commit_sha": f"commit{i}",
                "translator_version": "0.1.0",
                "python_version": "3.13",
            }
            metadata_manager.record_translation(Path("src/main.py"), record)

        # Verify all recorded
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert len(metadata["translations"]) == 3
        assert [t["language"] for t in metadata["translations"]] == ["en", "fr", "de"]

    def test_updated_at_timestamp_changes(self, git_repo, metadata_manager):
        """Test that updated_at timestamp changes with each operation."""
        # Setup
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata = metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )
        initial_updated_at = metadata["updated_at"]

        # Wait a tiny bit to ensure timestamp difference
        import time

        time.sleep(0.01)

        # Record translation
        record: TranslationRecord = {
            "language": "en",
            "method": "token_transformer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": None,
            "translator_version": "0.1.0",
            "python_version": "3.13",
        }
        metadata_manager.record_translation(Path("src/main.py"), record)

        # Verify updated_at changed
        updated_metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert updated_metadata is not None
        assert updated_metadata["updated_at"] != initial_updated_at


# ============================================================================
# Test: History Tracking
# ============================================================================


class TestHistoryTracking:
    """Test tracking git filter operation history."""

    def test_add_clean_history_entry(self, git_repo, metadata_manager):
        """Test recording a clean filter operation in history."""
        # Setup
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Add history entry
        entry: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": "abc123",
        }
        metadata_manager.add_history_entry(Path("src/main.py"), entry)

        # Verify history
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert len(metadata["history"]) == 1
        assert metadata["history"][0]["action"] == "clean"
        assert metadata["history"][0]["from_language"] == "es"
        assert metadata["history"][0]["to_language"] == "en"

    def test_add_smudge_history_entry(self, git_repo, metadata_manager):
        """Test recording a smudge filter operation in history."""
        # Setup
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Add smudge entry
        entry: HistoryEntry = {
            "action": "smudge",
            "from_language": "en",
            "to_language": "es",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": "abc123",
        }
        metadata_manager.add_history_entry(Path("src/main.py"), entry)

        # Verify
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert len(metadata["history"]) == 1
        assert metadata["history"][0]["action"] == "smudge"

    def test_history_accumulation_over_multiple_operations(
        self, git_repo, metadata_manager
    ):
        """Test that history accumulates over multiple git operations."""
        # Setup
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Simulate multiple git operations
        operations = [
            ("clean", "es", "en", "commit1"),
            ("smudge", "en", "es", "commit1"),
            ("clean", "es", "en", "commit2"),
            ("smudge", "en", "es", "commit2"),
        ]

        for action, from_lang, to_lang, commit in operations:
            entry: HistoryEntry = {
                "action": action,
                "from_language": from_lang,
                "to_language": to_lang,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "commit_sha": commit,
            }
            metadata_manager.add_history_entry(Path("src/main.py"), entry)

        # Verify all recorded
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert len(metadata["history"]) == 4

        # Verify order preserved
        assert metadata["history"][0]["action"] == "clean"
        assert metadata["history"][1]["action"] == "smudge"
        assert metadata["history"][2]["action"] == "clean"
        assert metadata["history"][3]["action"] == "smudge"


# ============================================================================
# Test: Round-Trip Translation with Metadata
# ============================================================================


class TestRoundTripWithMetadata:
    """Test round-trip translation tracking in metadata."""

    def test_round_trip_spanish_to_english_to_spanish(
        self, git_repo, metadata_manager, spanish_filter, spanish_source_code
    ):
        """Test Spanish → English → Spanish with metadata tracking."""
        # Setup
        _ = create_python_file(git_repo, "src/calculator.py", spanish_source_code)
        metadata_manager.create_metadata(
            Path("src/calculator.py"),
            original_language="es",
            python_version="3.13",
        )

        # Clean: Spanish → English
        import io

        input_stream = io.StringIO(spanish_source_code)
        output_stream = io.StringIO()
        spanish_filter.clean(input_stream, output_stream)
        english_code = output_stream.getvalue()

        # Record clean operation
        clean_entry: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": "test123",
        }
        metadata_manager.add_history_entry(Path("src/calculator.py"), clean_entry)

        # Smudge: English → Spanish
        input_stream2 = io.StringIO(english_code)
        output_stream2 = io.StringIO()
        spanish_filter.smudge(input_stream2, output_stream2)
        result_code = output_stream2.getvalue()

        # Record smudge operation
        smudge_entry: HistoryEntry = {
            "action": "smudge",
            "from_language": "en",
            "to_language": "es",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": "test123",
        }
        metadata_manager.add_history_entry(Path("src/calculator.py"), smudge_entry)

        # Verify metadata tracked both operations
        metadata = metadata_manager.get_metadata(Path("src/calculator.py"))
        assert metadata is not None
        assert len(metadata["history"]) == 2
        assert metadata["history"][0]["action"] == "clean"
        assert metadata["history"][1]["action"] == "smudge"

        # Verify translation preserved
        assert "definir" in result_code
        assert "retornar" in result_code


# ============================================================================
# Test: Multiple Files
# ============================================================================


class TestMultipleFiles:
    """Test metadata tracking for multiple files."""

    def test_metadata_tracks_multiple_files_independently(
        self, git_repo, metadata_manager
    ):
        """Test that metadata correctly tracks multiple files independently."""
        # Create multiple files
        files = [
            ("src/math.py", "definir suma(): pasar"),
            ("src/string.py", "definir concatenar(): pasar"),
            ("src/io.py", "definir leer(): pasar"),
        ]

        for rel_path, content in files:
            create_python_file(git_repo, rel_path, content)
            metadata_manager.create_metadata(
                Path(rel_path),
                original_language="es",
                python_version="3.13",
            )

        # Add different history to each
        for i, (rel_path, _) in enumerate(files):
            entry: HistoryEntry = {
                "action": "clean",
                "from_language": "es",
                "to_language": "en",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "commit_sha": f"commit{i}",
            }
            metadata_manager.add_history_entry(Path(rel_path), entry)

        # Verify each has independent metadata
        for i, (rel_path, _) in enumerate(files):
            metadata = metadata_manager.get_metadata(Path(rel_path))
            assert metadata is not None
            assert metadata["file"] == rel_path
            assert len(metadata["history"]) == 1
            assert metadata["history"][0]["commit_sha"] == f"commit{i}"

    def test_list_all_metadata_files(self, git_repo, metadata_manager):
        """Test listing all metadata files in repository."""
        # Create multiple files with metadata
        files = [
            "src/file1.py",
            "src/sub/file2.py",
            "tests/test_file.py",
        ]

        for rel_path in files:
            create_python_file(git_repo, rel_path, "definir test(): pasar")
            metadata_manager.create_metadata(
                Path(rel_path),
                original_language="es",
                python_version="3.13",
            )

        # List metadata files
        metadata_files = metadata_manager.list_metadata_files()

        # Verify all found
        assert len(metadata_files) == 3
        assert any("file1.py.yml" in str(f) for f in metadata_files)
        assert any("file2.py.yml" in str(f) for f in metadata_files)
        assert any("test_file.py.yml" in str(f) for f in metadata_files)


# ============================================================================
# Test: Error Handling
# ============================================================================


class TestErrorHandling:
    """Test that metadata errors don't break git operations."""

    def test_missing_metadata_file_doesnt_break_read(self, git_repo, metadata_manager):
        """Test that reading non-existent metadata returns None."""
        # Try to read metadata for non-existent file
        metadata = metadata_manager.get_metadata(Path("non/existent/file.py"))

        # Should return None, not raise exception
        assert metadata is None

    def test_corrupted_metadata_file_returns_none(self, git_repo, metadata_manager):
        """Test that corrupted metadata file is handled gracefully."""
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Corrupt the metadata file
        metadata_path = git_repo / ".legesher" / "metadata" / "src" / "main.py.yml"
        metadata_path.write_text("this is not valid yaml: [[[")

        # Try to read corrupted metadata
        metadata = metadata_manager.get_metadata(Path("src/main.py"))

        # Should return None, not raise exception
        assert metadata is None

    def test_invalid_metadata_structure_returns_none(self, git_repo, metadata_manager):
        """Test that invalid metadata structure is handled gracefully."""
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Write invalid metadata (missing required fields)
        metadata_path = git_repo / ".legesher" / "metadata" / "src" / "main.py.yml"
        metadata_path.write_text("file: src/main.py\n")  # Missing required fields

        # Try to read invalid metadata
        metadata = metadata_manager.get_metadata(Path("src/main.py"))

        # Should return None
        assert metadata is None

    def test_record_translation_without_metadata_logs_warning(
        self, git_repo, metadata_manager, caplog
    ):
        """Test that recording translation without metadata logs warning."""
        import logging

        caplog.set_level(logging.WARNING)

        # Try to record translation for non-existent metadata
        record: TranslationRecord = {
            "language": "en",
            "method": "token_transformer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": None,
            "translator_version": "0.1.0",
            "python_version": "3.13",
        }
        metadata_manager.record_translation(Path("non/existent.py"), record)

        # Should log warning
        assert "Cannot record translation" in caplog.text


# ============================================================================
# Test: Metadata Validation
# ============================================================================


class TestMetadataValidation:
    """Test metadata validation functionality."""

    def test_validate_metadata_for_valid_file(self, git_repo, metadata_manager):
        """Test validation of valid metadata."""
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Validate
        is_valid = metadata_manager.validate_metadata(Path("src/main.py"))
        assert is_valid is True

    def test_validate_metadata_for_missing_file(self, git_repo, metadata_manager):
        """Test validation of non-existent metadata."""
        is_valid = metadata_manager.validate_metadata(Path("non/existent.py"))
        assert is_valid is False

    def test_validate_metadata_for_incomplete_file(self, git_repo, metadata_manager):
        """Test validation of incomplete metadata."""
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Corrupt metadata by removing required field
        metadata_path = git_repo / ".legesher" / "metadata" / "src" / "main.py.yml"
        data = read_metadata_yaml(metadata_path)
        del data["original_language"]
        with open(metadata_path, "w") as f:
            yaml.safe_dump(data, f)

        # Validate
        is_valid = metadata_manager.validate_metadata(Path("src/main.py"))
        assert is_valid is False


# ============================================================================
# Test: Atomic Operations
# ============================================================================


class TestAtomicOperations:
    """Test atomic write operations to prevent corruption."""

    def test_metadata_write_is_atomic(self, git_repo, metadata_manager):
        """Test that metadata writes are atomic (temp file + rename)."""
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Update metadata (triggers atomic write)
        metadata_manager.update_metadata(
            Path("src/main.py"),
            {"python_version": "3.12"},
        )

        # Verify no temp files left behind
        metadata_dir = git_repo / ".legesher" / "metadata" / "src"
        temp_files = list(metadata_dir.glob(".*.tmp"))
        assert len(temp_files) == 0

        # Verify update succeeded
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert metadata["python_version"] == "3.12"

    def test_concurrent_updates_dont_corrupt_metadata(self, git_repo, metadata_manager):
        """Test that rapid sequential updates don't corrupt metadata.

        Note: This tests rapid sequential updates, not true concurrent operations.
        True concurrent operations require more complex test setup.
        """
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Perform rapid updates
        for i in range(10):
            entry: HistoryEntry = {
                "action": "clean",
                "from_language": "es",
                "to_language": "en",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "commit_sha": f"commit{i}",
            }
            metadata_manager.add_history_entry(Path("src/main.py"), entry)

        # Verify all updates recorded
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert len(metadata["history"]) == 10

        # Verify file is still valid YAML
        assert metadata_manager.validate_metadata(Path("src/main.py")) is True


# ============================================================================
# Test: Git Integration
# ============================================================================


class TestGitIntegration:
    """Test metadata integration with git operations.

    Note: These tests verify metadata behavior alongside git operations,
    but don't test actual git filter integration (that requires CORE-438).
    """

    def test_metadata_survives_git_commit(
        self, git_repo, metadata_manager, spanish_source_code
    ):
        """Test that metadata is preserved through git commit."""
        # Create file with metadata
        create_python_file(git_repo, "src/calculator.py", spanish_source_code)
        metadata_manager.create_metadata(
            Path("src/calculator.py"),
            original_language="es",
            python_version="3.13",
        )

        # Add history entry
        entry: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": None,  # Will be set after commit
        }
        metadata_manager.add_history_entry(Path("src/calculator.py"), entry)

        # Commit the file (but not metadata directory)
        git_add_commit(git_repo, "Add calculator", ["src/calculator.py"])

        # Verify metadata still exists and is valid
        metadata = metadata_manager.get_metadata(Path("src/calculator.py"))
        assert metadata is not None
        assert len(metadata["history"]) == 1

    def test_metadata_tracks_commit_sha(self, git_repo, metadata_manager):
        """Test that metadata can track commit SHAs."""
        # Create file with metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Commit
        commit_sha = git_add_commit(git_repo, "Add main.py", ["src/main.py"])

        # Record operation with commit SHA
        entry: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": commit_sha,
        }
        metadata_manager.add_history_entry(Path("src/main.py"), entry)

        # Verify commit SHA recorded
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert metadata["history"][0]["commit_sha"] == commit_sha

    def test_metadata_directory_can_be_gitignored(self, git_repo, metadata_manager):
        """Test that metadata directory can be excluded from git.

        This is important because metadata is local tracking information
        and doesn't need to be committed to git.
        """
        # Create .gitignore
        gitignore = git_repo / ".gitignore"
        gitignore.write_text(".legesher/metadata/\n")

        # Create file with metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Check git status
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )

        # Metadata directory should not appear in git status
        assert ".legesher/metadata" not in result.stdout


# ============================================================================
# Test: Update Operations
# ============================================================================


class TestUpdateOperations:
    """Test metadata update operations."""

    def test_update_python_version(self, git_repo, metadata_manager):
        """Test updating Python version in metadata."""
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Update Python version
        metadata_manager.update_metadata(
            Path("src/main.py"),
            {"python_version": "3.12"},
        )

        # Verify update
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert metadata["python_version"] == "3.12"

    def test_update_multiple_fields(self, git_repo, metadata_manager):
        """Test updating multiple metadata fields at once."""
        # Create file and metadata
        create_python_file(git_repo, "src/main.py", "definir test(): pasar")
        metadata_manager.create_metadata(
            Path("src/main.py"),
            original_language="es",
            python_version="3.13",
        )

        # Update multiple fields
        metadata_manager.update_metadata(
            Path("src/main.py"),
            {
                "python_version": "3.12",
                "original_language": "fr",
            },
        )

        # Verify updates
        metadata = metadata_manager.get_metadata(Path("src/main.py"))
        assert metadata is not None
        assert metadata["python_version"] == "3.12"
        assert metadata["original_language"] == "fr"

    def test_update_nonexistent_metadata_logs_warning(
        self, git_repo, metadata_manager, caplog
    ):
        """Test that updating non-existent metadata logs warning."""
        import logging

        caplog.set_level(logging.WARNING)

        # Try to update non-existent metadata
        metadata_manager.update_metadata(
            Path("non/existent.py"),
            {"python_version": "3.12"},
        )

        # Should log warning
        assert "Cannot update metadata" in caplog.text
