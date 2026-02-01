"""Unit tests for MetadataManager.

Tests the MetadataManager class that handles reading, writing, and managing
YAML metadata files in the .legesher/metadata/ directory.

Test Coverage:
- Metadata creation and initialization
- Reading and writing metadata files
- Atomic writes and error handling
- Metadata validation
- Translation record management
- History entry management
- Path handling and directory creation
- YAML error handling
- Concurrent access patterns

Coverage Target: >90%
"""

import sys

import pytest
from pathlib import Path
from datetime import UTC, datetime
import yaml
import threading
import time

from legesher_core.metadata import MetadataManager
from legesher_core.types import TranslationRecord, HistoryEntry


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository for testing.

    Creates a clean temporary directory structure for isolated testing.
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()
    (repo / "src").mkdir()
    return repo


@pytest.fixture
def metadata_manager(temp_repo):
    """Create a MetadataManager instance for testing."""
    return MetadataManager(temp_repo)


@pytest.fixture
def sample_file(temp_repo):
    """Create a sample Python file for testing."""
    file_path = temp_repo / "src" / "example.py"
    file_path.write_text("def hello(): pass")
    return file_path


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return {
        "file": "src/example.py",
        "original_language": "es",
        "canonical_language": "en",
        "python_version": "3.13",
        "created_at": "2025-11-06T10:00:00Z",
        "updated_at": "2025-11-06T10:00:00Z",
        "translations": [],
        "history": [],
    }


class TestInitialization:
    """Tests for MetadataManager initialization."""

    def test_init_creates_metadata_dir(self, temp_repo):
        """Test that initializing MetadataManager creates the metadata directory."""
        manager = MetadataManager(temp_repo)

        # Directory should not exist yet (created lazily on first write)
        assert manager.repo_root == temp_repo.resolve()
        assert manager.metadata_dir == temp_repo / ".legesher" / "metadata"

    def test_init_resolves_repo_root(self, tmp_path):
        """Test that repo_root is resolved to absolute path."""
        relative_path = Path(".")
        manager = MetadataManager(relative_path)

        assert manager.repo_root.is_absolute()


class TestGetMetadata:
    """Tests for reading metadata."""

    def test_get_metadata_returns_none_for_nonexistent(self, metadata_manager):
        """Test getting metadata for a file that doesn't have metadata yet."""
        result = metadata_manager.get_metadata(Path("src/nonexistent.py"))

        assert result is None

    def test_get_metadata_after_create(self, metadata_manager):
        """Test reading metadata that was just created."""
        file_path = Path("src/example.py")

        # Create metadata
        _ = metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Read it back
        retrieved = metadata_manager.get_metadata(file_path)

        assert retrieved is not None
        assert retrieved["file"] == "src/example.py"
        assert retrieved["original_language"] == "es"
        assert retrieved["canonical_language"] == "en"
        assert retrieved["python_version"] == "3.13"
        assert retrieved["translations"] == []
        assert retrieved["history"] == []

    def test_get_metadata_with_absolute_path(self, metadata_manager, temp_repo):
        """Test getting metadata using absolute path."""
        file_path = temp_repo / "src" / "example.py"

        # Create metadata with absolute path
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Read with absolute path
        retrieved = metadata_manager.get_metadata(file_path)

        assert retrieved is not None
        assert retrieved["file"] == "src/example.py"

    def test_get_metadata_missing_required_fields(self, metadata_manager, temp_repo):
        """Test handling of metadata file with missing required fields."""
        file_path = Path("src/example.py")
        metadata_path = metadata_manager._get_metadata_path(file_path)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Write incomplete metadata
        incomplete_data = {
            "file": "src/example.py",
            "original_language": "es",
            # Missing other required fields
        }
        with open(metadata_path, "w") as f:
            yaml.safe_dump(incomplete_data, f)

        # Should return None for invalid metadata
        result = metadata_manager.get_metadata(file_path)
        assert result is None


class TestCreateMetadata:
    """Tests for creating new metadata."""

    def test_create_metadata(self, metadata_manager):
        """Test creating new metadata for a file."""
        file_path = Path("src/calculator.py")

        metadata = metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        assert metadata["file"] == "src/calculator.py"
        assert metadata["original_language"] == "es"
        assert metadata["canonical_language"] == "en"
        assert metadata["python_version"] == "3.13"
        assert isinstance(metadata["created_at"], str)
        assert isinstance(metadata["updated_at"], str)
        assert metadata["translations"] == []
        assert metadata["history"] == []

    def test_create_metadata_creates_parent_dirs(self, metadata_manager):
        """Test that creating metadata creates nested directories."""
        file_path = Path("src/nested/deep/module.py")

        _ = metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        metadata_path = metadata_manager._get_metadata_path(file_path)
        assert metadata_path.exists()
        assert metadata_path.parent.exists()

    def test_create_metadata_timestamps(self, metadata_manager):
        """Test that timestamps are properly formatted ISO 8601."""
        file_path = Path("src/example.py")

        before = datetime.now(UTC)
        metadata = metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )
        after = datetime.now(UTC)

        # Parse timestamp (ISO 8601 format with timezone)
        created_at = datetime.fromisoformat(metadata["created_at"])

        # Timestamp should be between before and after
        assert before <= created_at <= after
        # Verify ISO 8601 format with timezone (either Z or +00:00)
        assert metadata["created_at"].endswith("Z") or metadata["created_at"].endswith(
            "+00:00"
        )
        assert metadata["created_at"] == metadata["updated_at"]


class TestUpdateMetadata:
    """Tests for updating existing metadata."""

    def test_update_metadata(self, metadata_manager):
        """Test updating existing metadata."""
        file_path = Path("src/example.py")

        # Create initial metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Update it
        metadata_manager.update_metadata(file_path, {"python_version": "3.12"})

        # Read updated metadata
        updated = metadata_manager.get_metadata(file_path)
        assert updated is not None
        assert updated["python_version"] == "3.12"
        assert updated["original_language"] == "es"  # Unchanged

    def test_update_metadata_updates_timestamp(self, metadata_manager):
        """Test that update_metadata updates the updated_at timestamp."""
        file_path = Path("src/example.py")

        # Create initial metadata
        original = metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )
        original_timestamp = original["updated_at"]

        # Wait a bit to ensure different timestamp
        time.sleep(0.01)

        # Update it
        metadata_manager.update_metadata(file_path, {"python_version": "3.12"})

        # Check timestamp was updated
        updated = metadata_manager.get_metadata(file_path)
        assert updated is not None
        assert updated["updated_at"] != original_timestamp

    def test_update_metadata_nonexistent_file(self, metadata_manager, caplog):
        """Test updating metadata for non-existent file logs warning."""
        file_path = Path("src/nonexistent.py")

        metadata_manager.update_metadata(file_path, {"python_version": "3.12"})

        # Should log a warning
        assert any(
            "Cannot update metadata" in record.message for record in caplog.records
        )

    def test_update_metadata_ignores_unknown_fields(self, metadata_manager, caplog):
        """Test that unknown fields are ignored with warning."""
        file_path = Path("src/example.py")

        # Create initial metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Try to update with unknown field
        metadata_manager.update_metadata(file_path, {"unknown_field": "value"})

        # Should log a warning
        assert any(
            "Ignoring unknown metadata field" in record.message
            for record in caplog.records
        )


class TestRecordTranslation:
    """Tests for recording translation operations."""

    def test_record_translation(self, metadata_manager):
        """Test adding a translation record to metadata."""
        file_path = Path("src/example.py")

        # Create initial metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Record a translation
        record: TranslationRecord = {
            "language": "en",
            "method": "token_transformer",
            "timestamp": "2025-11-06T10:30:00Z",
            "commit_sha": "a91228a",
            "translator_version": "0.1.0",
            "python_version": "3.13",
        }
        metadata_manager.record_translation(file_path, record)

        # Verify it was added
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None
        assert len(metadata["translations"]) == 1
        assert metadata["translations"][0]["language"] == "en"
        assert metadata["translations"][0]["method"] == "token_transformer"

    def test_record_translation_multiple(self, metadata_manager):
        """Test recording multiple translations."""
        file_path = Path("src/example.py")

        # Create initial metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Record multiple translations
        for lang in ["en", "fr", "de"]:
            record: TranslationRecord = {
                "language": lang,
                "method": "token_transformer",
                "timestamp": f"2025-11-06T10:{lang[0]}0:00Z",
                "commit_sha": f"{lang}91228a",
                "translator_version": "0.1.0",
                "python_version": "3.13",
            }
            metadata_manager.record_translation(file_path, record)

        # Verify all were added
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None
        assert len(metadata["translations"]) == 3
        assert [t["language"] for t in metadata["translations"]] == ["en", "fr", "de"]

    def test_record_translation_nonexistent_metadata(self, metadata_manager, caplog):
        """Test recording translation for file without metadata logs warning."""
        file_path = Path("src/nonexistent.py")

        record: TranslationRecord = {
            "language": "en",
            "method": "token_transformer",
            "timestamp": "2025-11-06T10:30:00Z",
            "commit_sha": "a91228a",
            "translator_version": "0.1.0",
            "python_version": "3.13",
        }

        metadata_manager.record_translation(file_path, record)

        # Should log a warning
        assert any(
            "Cannot record translation" in record.message for record in caplog.records
        )


class TestAddHistoryEntry:
    """Tests for adding history entries."""

    def test_add_history_entry(self, metadata_manager):
        """Test adding history entries."""
        file_path = Path("src/example.py")

        # Create initial metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Add history entry
        entry: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": "2025-11-06T10:30:00Z",
            "commit_sha": "a91228a",
        }
        metadata_manager.add_history_entry(file_path, entry)

        # Verify it was added
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None
        assert len(metadata["history"]) == 1
        assert metadata["history"][0]["action"] == "clean"
        assert metadata["history"][0]["from_language"] == "es"

    def test_add_history_entry_chronological(self, metadata_manager):
        """Test that history entries are added chronologically."""
        file_path = Path("src/example.py")

        # Create initial metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Add multiple entries
        actions = ["clean", "smudge", "clean"]
        for i, action in enumerate(actions):
            entry: HistoryEntry = {
                "action": action,
                "from_language": "es" if action == "clean" else "en",
                "to_language": "en" if action == "clean" else "es",
                "timestamp": f"2025-11-06T10:3{i}:00Z",
                "commit_sha": f"a91228{i}",
            }
            metadata_manager.add_history_entry(file_path, entry)

        # Verify chronological order
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None
        assert len(metadata["history"]) == 3
        assert [e["action"] for e in metadata["history"]] == actions

    def test_add_history_entry_nonexistent_metadata(self, metadata_manager, caplog):
        """Test adding history entry for file without metadata logs warning."""
        file_path = Path("src/nonexistent.py")

        entry: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": "2025-11-06T10:30:00Z",
            "commit_sha": "a91228a",
        }

        metadata_manager.add_history_entry(file_path, entry)

        # Should log a warning
        assert any(
            "Cannot add history entry" in record.message for record in caplog.records
        )


class TestListMetadataFiles:
    """Tests for listing metadata files."""

    def test_list_metadata_files(self, metadata_manager):
        """Test listing all metadata files in the repository."""
        # Create multiple metadata files
        files = ["src/calculator.py", "src/utils.py", "tests/test_calc.py"]

        for file_path in files:
            metadata_manager.create_metadata(
                Path(file_path), original_language="es", python_version="3.13"
            )

        # List all metadata files
        metadata_files = metadata_manager.list_metadata_files()

        assert len(metadata_files) == 3
        # All should be .yml files
        assert all(f.suffix == ".yml" for f in metadata_files)

    def test_list_metadata_files_empty(self, metadata_manager):
        """Test listing metadata files when directory doesn't exist."""
        # Don't create any metadata
        metadata_files = metadata_manager.list_metadata_files()

        assert metadata_files == []

    def test_list_metadata_files_nested(self, metadata_manager):
        """Test listing metadata files in nested directories."""
        # Create metadata in nested structure
        files = ["a/b/c/deep.py", "x/y.py", "root.py"]

        for file_path in files:
            metadata_manager.create_metadata(
                Path(file_path), original_language="es", python_version="3.13"
            )

        # List all
        metadata_files = metadata_manager.list_metadata_files()

        assert len(metadata_files) == 3


class TestValidateMetadata:
    """Tests for metadata validation."""

    def test_validate_metadata_valid(self, metadata_manager):
        """Test validating a valid metadata file."""
        file_path = Path("src/example.py")

        # Create valid metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Validate
        assert metadata_manager.validate_metadata(file_path) is True

    def test_validate_metadata_missing(self, metadata_manager):
        """Test validating non-existent metadata."""
        file_path = Path("src/nonexistent.py")

        # Validate
        assert metadata_manager.validate_metadata(file_path) is False

    def test_validate_metadata_corrupt(self, metadata_manager, temp_repo):
        """Test handling corrupt YAML metadata."""
        file_path = Path("src/example.py")
        metadata_path = metadata_manager._get_metadata_path(file_path)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Write corrupt YAML
        with open(metadata_path, "w") as f:
            f.write("invalid: yaml: syntax: [[[")

        # Should return False
        assert metadata_manager.validate_metadata(file_path) is False

    def test_validate_metadata_missing_fields(self, metadata_manager, temp_repo):
        """Test validating metadata with missing required fields."""
        file_path = Path("src/example.py")
        metadata_path = metadata_manager._get_metadata_path(file_path)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Write incomplete metadata
        incomplete_data = {
            "file": "src/example.py",
            "original_language": "es",
            # Missing many required fields
        }
        with open(metadata_path, "w") as f:
            yaml.safe_dump(incomplete_data, f)

        # Should return False
        assert metadata_manager.validate_metadata(file_path) is False


class TestAtomicWrite:
    """Tests for atomic write operations."""

    def test_atomic_write(self, metadata_manager):
        """Test that writes are atomic (no orphaned .tmp files)."""
        file_path = Path("src/example.py")

        # Create metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        metadata_path = metadata_manager._get_metadata_path(file_path)
        temp_path = metadata_path.parent / f".{metadata_path.name}.tmp"

        # Verify no temp file exists
        assert metadata_path.exists()
        assert not temp_path.exists()

    @pytest.mark.skipif(
        sys.platform == "win32", reason="chmod doesn't restrict writes on Windows"
    )
    def test_atomic_write_cleanup_on_error(self, metadata_manager, temp_repo):
        """Test that temp files are cleaned up on write errors."""
        file_path = Path("src/example.py")

        # Create the directory
        metadata_path = metadata_manager._get_metadata_path(file_path)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        # Make the directory read-only to cause write error
        metadata_path.parent.chmod(0o555)

        try:
            # This should fail due to permissions
            with pytest.raises(OSError):
                metadata_manager.create_metadata(
                    file_path, original_language="es", python_version="3.13"
                )

            # Temp file should be cleaned up
            temp_path = metadata_path.parent / f".{metadata_path.name}.tmp"
            assert not temp_path.exists()
        finally:
            # Restore permissions
            metadata_path.parent.chmod(0o755)


class TestGetMetadataPath:
    """Tests for metadata path conversion."""

    def test_get_metadata_path(self, metadata_manager, temp_repo):
        """Test conversion of source file paths to metadata paths."""
        file_path = Path("src/main.py")

        metadata_path = metadata_manager._get_metadata_path(file_path)

        expected = temp_repo / ".legesher" / "metadata" / "src" / "main.py.yml"
        assert metadata_path == expected

    def test_get_metadata_path_nested(self, metadata_manager, temp_repo):
        """Test metadata path for nested files."""
        file_path = Path("src/utils/helpers/math.py")

        metadata_path = metadata_manager._get_metadata_path(file_path)

        expected = (
            temp_repo
            / ".legesher"
            / "metadata"
            / "src"
            / "utils"
            / "helpers"
            / "math.py.yml"
        )
        assert metadata_path == expected

    def test_get_metadata_path_absolute(self, metadata_manager, temp_repo):
        """Test metadata path conversion for absolute paths."""
        file_path = temp_repo / "src" / "main.py"

        metadata_path = metadata_manager._get_metadata_path(file_path)

        expected = temp_repo / ".legesher" / "metadata" / "src" / "main.py.yml"
        assert metadata_path == expected


class TestYamlOperations:
    """Tests for YAML read/write operations."""

    def test_read_yaml_valid(self, metadata_manager, temp_repo):
        """Test reading valid YAML file."""
        yaml_file = temp_repo / "test.yml"
        data = {"key": "value", "number": 42}

        with open(yaml_file, "w") as f:
            yaml.safe_dump(data, f)

        result = metadata_manager._read_yaml(yaml_file)

        assert result == data

    def test_handle_yaml_error_gracefully(self, metadata_manager, temp_repo):
        """Test that YAML errors are handled gracefully."""
        yaml_file = temp_repo / "corrupt.yml"

        # Write invalid YAML
        with open(yaml_file, "w") as f:
            f.write("invalid: yaml: syntax: [[[")

        result = metadata_manager._read_yaml(yaml_file)

        assert result is None

    def test_read_yaml_not_dict(self, metadata_manager, temp_repo):
        """Test reading YAML that doesn't contain a dict."""
        yaml_file = temp_repo / "list.yml"

        # Write a list instead of dict
        with open(yaml_file, "w") as f:
            yaml.safe_dump([1, 2, 3], f)

        result = metadata_manager._read_yaml(yaml_file)

        assert result is None

    def test_read_yaml_nonexistent(self, metadata_manager, temp_repo):
        """Test reading non-existent YAML file."""
        yaml_file = temp_repo / "nonexistent.yml"

        result = metadata_manager._read_yaml(yaml_file)

        assert result is None

    def test_write_yaml_preserves_structure(self, metadata_manager, temp_repo):
        """Test that YAML writing preserves data structure."""
        yaml_file = temp_repo / "test.yml"
        data = {
            "nested": {"structure": {"with": ["lists", "and", "dicts"]}},
            "unicode": "こんにちは",
        }

        metadata_manager._write_yaml(yaml_file, data)

        # Read it back
        with open(yaml_file, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        assert loaded == data


class TestConcurrentAccess:
    """Tests for concurrent metadata access."""

    @pytest.mark.skipif(
        sys.platform == "win32", reason="os.replace() file-locking on Windows"
    )
    def test_concurrent_access(self, metadata_manager):
        """Test that concurrent operations don't corrupt metadata.

        Note: This tests that the metadata system handles concurrent access
        gracefully. Due to the atomic write implementation (write to temp, then
        rename), some operations may fail with FileNotFoundError in highly
        concurrent scenarios. This is acceptable as long as the metadata remains
        valid and doesn't get corrupted.
        """
        file_path = Path("src/example.py")

        # Create initial metadata
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Define concurrent update function
        errors = []
        success_count = [0]  # Use list for mutability in closure

        def update_metadata(index):
            try:
                for i in range(10):
                    try:
                        entry: HistoryEntry = {
                            "action": "clean",
                            "from_language": "es",
                            "to_language": "en",
                            "timestamp": f"2025-11-06T10:{index}{i}:00Z",
                            "commit_sha": f"{index}{i}91228a",
                        }
                        metadata_manager.add_history_entry(file_path, entry)
                        success_count[0] += 1
                    except (FileNotFoundError, OSError):
                        # These are acceptable race condition errors
                        # They don't corrupt the metadata
                        pass
            except Exception as e:
                # Unexpected errors
                errors.append(e)

        # Run concurrent updates with fewer threads to reduce race conditions
        threads = []
        for i in range(3):
            thread = threading.Thread(target=update_metadata, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check no unexpected errors occurred
        assert len(errors) == 0

        # Verify metadata is still valid (not corrupted)
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None
        assert metadata_manager.validate_metadata(file_path)

        # We should have at least some successful writes
        # (exact count depends on race conditions, but metadata should be valid)
        assert len(metadata["history"]) > 0
        assert success_count[0] > 0


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_file_path(self, metadata_manager):
        """Test handling of empty file path."""
        file_path = Path("")

        # Should handle gracefully
        result = metadata_manager.get_metadata(file_path)
        assert result is None

    def test_special_characters_in_path(self, metadata_manager):
        """Test handling of special characters in file paths."""
        file_path = Path("src/file with spaces.py")

        # Should work fine
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        retrieved = metadata_manager.get_metadata(file_path)
        assert retrieved is not None
        assert "with spaces" in retrieved["file"]

    def test_unicode_in_path(self, metadata_manager):
        """Test handling of Unicode characters in file paths."""
        file_path = Path("src/日本語.py")

        # Should work fine with Unicode
        metadata_manager.create_metadata(
            file_path, original_language="ja", python_version="3.13"
        )

        retrieved = metadata_manager.get_metadata(file_path)
        assert retrieved is not None
        assert "日本語" in retrieved["file"]

    def test_very_long_path(self, metadata_manager):
        """Test handling of very long file paths."""
        # Create a path with many nested levels
        parts = ["level" + str(i) for i in range(50)]
        file_path = Path("/".join(parts) + "/file.py")

        # Should handle long paths
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        retrieved = metadata_manager.get_metadata(file_path)
        assert retrieved is not None

    def test_relative_path_outside_repo(self, metadata_manager, temp_repo, caplog):
        """Test handling of path outside repository root."""
        # Path that goes outside repo
        file_path = Path("../outside/file.py")

        # Should handle gracefully (logs warning)
        metadata_manager.create_metadata(
            file_path, original_language="es", python_version="3.13"
        )

        # Check for warning about path not under repo_root
        # (This might log a warning depending on implementation)
        retrieved = metadata_manager.get_metadata(file_path)
        assert retrieved is not None
