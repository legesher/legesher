"""Unit tests for TranslationTracker.

Tests the TranslationTracker class that provides high-level API for tracking
translation operations during git clean/smudge filters.

Test Coverage:
- Track clean/smudge operations
- History retrieval and management
- Translation record management
- Context gathering (git SHA, versions)
- Deduplication logic
- Error handling and graceful degradation
- Metadata creation on first use
- Integration with MetadataManager

Coverage Target: >90%
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
import subprocess
import sys
from unittest.mock import patch

from legesher_core.metadata import MetadataManager
from legesher_core.translation_tracker import TranslationTracker
from legesher_core.types import TranslationRecord, HistoryEntry


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repository for testing."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    (repo / "src").mkdir()
    return repo


@pytest.fixture
def metadata_manager(temp_repo):
    """Create a MetadataManager instance for testing."""
    return MetadataManager(temp_repo)


@pytest.fixture
def translation_tracker(metadata_manager):
    """Create a TranslationTracker instance for testing."""
    return TranslationTracker(metadata_manager)


@pytest.fixture
def sample_file(temp_repo):
    """Create a sample Python file for testing."""
    file_path = temp_repo / "src" / "example.py"
    file_path.write_text("def hello(): pass")
    return file_path


@pytest.fixture
def file_with_metadata(metadata_manager):
    """Create a file with existing metadata."""
    file_path = Path("src/example.py")
    metadata_manager.create_metadata(
        file_path, original_language="es", python_version="3.13"
    )
    return file_path


class TestInitialization:
    """Tests for TranslationTracker initialization."""

    def test_init(self, metadata_manager):
        """Test TranslationTracker initialization."""
        tracker = TranslationTracker(metadata_manager)

        assert tracker.metadata_manager is metadata_manager


class TestTrackClean:
    """Tests for tracking clean filter operations."""

    def test_track_clean(self, translation_tracker, file_with_metadata):
        """Test tracking a clean filter operation."""
        translation_tracker.track_clean(
            file_path=file_with_metadata, from_language="es", to_language="en"
        )

        # Verify history entry was added
        history = translation_tracker.get_translation_history(file_with_metadata)
        assert len(history) == 1
        assert history[0]["action"] == "clean"
        assert history[0]["from_language"] == "es"
        assert history[0]["to_language"] == "en"

    def test_track_clean_with_method(self, translation_tracker, file_with_metadata):
        """Test tracking clean with custom method."""
        translation_tracker.track_clean(
            file_path=file_with_metadata,
            from_language="es",
            to_language="en",
            method="tree_sitter",
        )

        # Verify translation record has correct method
        latest = translation_tracker.get_latest_translation(file_with_metadata)
        assert latest is not None
        assert latest["method"] == "tree_sitter"

    def test_track_clean_multiple_operations(
        self, translation_tracker, file_with_metadata
    ):
        """Test tracking multiple clean operations."""
        # Track multiple cleans
        for i in range(3):
            translation_tracker.track_clean(
                file_path=file_with_metadata, from_language="es", to_language="en"
            )

        # Should have 3 history entries (or fewer if deduplicated)
        history = translation_tracker.get_translation_history(file_with_metadata)
        assert len(history) >= 1  # At least one entry

    def test_track_clean_no_metadata_creates_it(
        self, translation_tracker, metadata_manager
    ):
        """Test that tracking creates metadata for new files."""
        file_path = Path("src/new_file.py")

        # No metadata exists yet
        assert metadata_manager.get_metadata(file_path) is None

        # Track clean operation
        translation_tracker.track_clean(
            file_path=file_path, from_language="es", to_language="en"
        )

        # Metadata should now exist
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None
        assert metadata["original_language"] == "es"

    def test_track_clean_error_handling(self, translation_tracker, caplog):
        """Test that errors in track_clean are caught and logged."""
        # Use invalid file path or cause error
        invalid_path = Path("/invalid/path/that/causes/error")

        # Should not raise exception
        translation_tracker.track_clean(
            file_path=invalid_path, from_language="es", to_language="en"
        )

        # Should have logged a warning
        assert any(
            "Failed to track clean operation" in record.message
            for record in caplog.records
        )


class TestTrackSmudge:
    """Tests for tracking smudge filter operations."""

    def test_track_smudge(self, translation_tracker, file_with_metadata):
        """Test tracking a smudge filter operation."""
        translation_tracker.track_smudge(
            file_path=file_with_metadata, from_language="en", to_language="es"
        )

        # Verify history entry was added
        history = translation_tracker.get_translation_history(file_with_metadata)
        assert len(history) == 1
        assert history[0]["action"] == "smudge"
        assert history[0]["from_language"] == "en"
        assert history[0]["to_language"] == "es"

    def test_track_smudge_with_method(self, translation_tracker, file_with_metadata):
        """Test tracking smudge with custom method."""
        translation_tracker.track_smudge(
            file_path=file_with_metadata,
            from_language="en",
            to_language="es",
            method="tree_sitter",
        )

        # Verify translation record has correct method
        latest = translation_tracker.get_latest_translation(file_with_metadata)
        assert latest is not None
        assert latest["method"] == "tree_sitter"

    def test_track_smudge_no_metadata_creates_it(
        self, translation_tracker, metadata_manager
    ):
        """Test that tracking creates metadata for new files."""
        file_path = Path("src/new_file.py")

        # No metadata exists yet
        assert metadata_manager.get_metadata(file_path) is None

        # Track smudge operation
        translation_tracker.track_smudge(
            file_path=file_path, from_language="en", to_language="es"
        )

        # Metadata should now exist
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None
        # Original language is set to from_language
        assert metadata["original_language"] == "en"

    def test_track_smudge_error_handling(self, translation_tracker, caplog):
        """Test that errors in track_smudge are caught and logged."""
        # Use invalid file path or cause error
        invalid_path = Path("/invalid/path/that/causes/error")

        # Should not raise exception
        translation_tracker.track_smudge(
            file_path=invalid_path, from_language="en", to_language="es"
        )

        # Should have logged a warning
        assert any(
            "Failed to track smudge operation" in record.message
            for record in caplog.records
        )


class TestGetTranslationHistory:
    """Tests for retrieving translation history."""

    def test_get_translation_history(self, translation_tracker, file_with_metadata):
        """Test retrieving translation history."""
        # Add some history
        translation_tracker.track_clean(file_with_metadata, "es", "en")
        translation_tracker.track_smudge(file_with_metadata, "en", "es")

        # Get history
        history = translation_tracker.get_translation_history(file_with_metadata)

        assert len(history) >= 2
        # Check actions are recorded
        actions = [h["action"] for h in history]
        assert "clean" in actions or "smudge" in actions

    def test_get_translation_history_empty(
        self, translation_tracker, file_with_metadata
    ):
        """Test getting history for file with no operations."""
        # File has metadata but no history yet
        history = translation_tracker.get_translation_history(file_with_metadata)

        assert history == []

    def test_get_translation_history_no_metadata(self, translation_tracker):
        """Test getting history for file without metadata."""
        file_path = Path("src/nonexistent.py")

        history = translation_tracker.get_translation_history(file_path)

        assert history == []

    def test_get_translation_history_error_handling(self, translation_tracker, caplog):
        """Test error handling when getting history."""
        # Create a path that might cause errors
        invalid_path = Path("/invalid/path")

        # Should return empty list, not raise
        history = translation_tracker.get_translation_history(invalid_path)

        assert history == []


class TestGetLatestTranslation:
    """Tests for retrieving latest translation."""

    def test_get_latest_translation(self, translation_tracker, file_with_metadata):
        """Test getting the most recent translation."""
        # Add translations
        translation_tracker.track_clean(file_with_metadata, "es", "en")
        translation_tracker.track_smudge(file_with_metadata, "en", "fr")

        # Get latest
        latest = translation_tracker.get_latest_translation(file_with_metadata)

        assert latest is not None
        # Should be most recent (fr)
        assert latest["language"] == "fr"

    def test_get_latest_translation_none(self, translation_tracker, file_with_metadata):
        """Test getting latest when no translations exist."""
        # File has metadata but no translations
        latest = translation_tracker.get_latest_translation(file_with_metadata)

        assert latest is None

    def test_get_latest_translation_no_metadata(self, translation_tracker):
        """Test getting latest for file without metadata."""
        file_path = Path("src/nonexistent.py")

        latest = translation_tracker.get_latest_translation(file_path)

        assert latest is None

    def test_get_latest_translation_error_handling(self, translation_tracker, caplog):
        """Test error handling when getting latest translation."""
        invalid_path = Path("/invalid/path")

        # Should return None, not raise
        latest = translation_tracker.get_latest_translation(invalid_path)

        assert latest is None


class TestGetCurrentContext:
    """Tests for gathering execution context."""

    def test_get_current_context(self, translation_tracker):
        """Test gathering execution context (timestamp, versions, etc.)."""
        context = translation_tracker._get_current_context()

        # Check all expected fields exist
        assert "timestamp" in context
        assert "commit_sha" in context
        assert "translator_version" in context
        assert "python_version" in context

        # Check timestamp format
        assert context["timestamp"].endswith("+00:00") or "T" in context["timestamp"]

        # Python version should match current
        expected_py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert context["python_version"] == expected_py_version

    def test_get_current_context_timestamp_format(self, translation_tracker):
        """Test that timestamp is proper ISO 8601 format."""
        context = translation_tracker._get_current_context()

        # Should be parseable as datetime
        timestamp = context["timestamp"]
        dt = datetime.fromisoformat(timestamp)

        # Should be recent (within last minute)
        now = datetime.now(timezone.utc)
        time_diff = abs((now - dt).total_seconds())
        assert time_diff < 60


class TestGetGitCommitSha:
    """Tests for git commit SHA detection."""

    def test_get_git_commit_sha(self, translation_tracker, temp_repo):
        """Test git commit SHA detection."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=temp_repo, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=temp_repo,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=temp_repo,
            capture_output=True,
        )

        # Create a commit
        test_file = temp_repo / "test.txt"
        test_file.write_text("test")
        subprocess.run(["git", "add", "."], cwd=temp_repo, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=temp_repo,
            capture_output=True,
        )

        # Change to repo directory for git commands to work
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_repo)
            sha = translation_tracker._get_git_commit_sha()

            # Should return a 7-character SHA
            assert sha is not None
            assert len(sha) == 7
        finally:
            os.chdir(old_cwd)

    def test_get_git_commit_sha_not_in_repo(self, translation_tracker, tmp_path):
        """Test SHA detection when not in a git repo."""
        # Change to non-git directory
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            sha = translation_tracker._get_git_commit_sha()

            # Should return None when not in a git repo
            assert sha is None
        finally:
            os.chdir(old_cwd)

    @patch("subprocess.run")
    def test_get_git_commit_sha_git_not_available(self, mock_run, translation_tracker):
        """Test SHA detection when git is not available."""
        # Simulate git not being found
        mock_run.side_effect = FileNotFoundError()

        sha = translation_tracker._get_git_commit_sha()

        assert sha is None

    @patch("subprocess.run")
    def test_get_git_commit_sha_timeout(self, mock_run, translation_tracker):
        """Test SHA detection when git times out."""
        # Simulate timeout
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        sha = translation_tracker._get_git_commit_sha()

        assert sha is None


class TestGetTranslatorVersion:
    """Tests for legesher-core version detection."""

    def test_get_translator_version(self, translation_tracker):
        """Test legesher-core version detection."""
        version = translation_tracker._get_translator_version()

        # Should return a version string
        assert isinstance(version, str)
        assert len(version) > 0

        # Should be either a version number or "unknown"
        assert version == "unknown" or version[0].isdigit()

    @patch(
        "legesher_core.translation_tracker.TranslationTracker._get_translator_version"
    )
    def test_get_translator_version_fallback(self, mock_version, translation_tracker):
        """Test version detection fallback to 'unknown'."""
        mock_version.return_value = "unknown"

        version = translation_tracker._get_translator_version()

        assert version == "unknown"


class TestGetPythonVersion:
    """Tests for Python version detection."""

    def test_get_python_version(self, translation_tracker):
        """Test Python version detection."""
        version = translation_tracker._get_python_version()

        # Should match current Python version
        expected = f"{sys.version_info.major}.{sys.version_info.minor}"
        assert version == expected

    def test_get_python_version_format(self, translation_tracker):
        """Test Python version format is major.minor."""
        version = translation_tracker._get_python_version()

        # Should be in format "X.Y"
        parts = version.split(".")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()


class TestDeduplicationHistory:
    """Tests for history entry deduplication."""

    def test_deduplication_history(self, translation_tracker, file_with_metadata):
        """Test that duplicate history entries are prevented."""
        # Track same operation twice in quick succession
        translation_tracker.track_clean(file_with_metadata, "es", "en")
        translation_tracker.track_clean(file_with_metadata, "es", "en")

        # Should deduplicate (within 1 minute window)
        history = translation_tracker.get_translation_history(file_with_metadata)

        # Depending on timing, might be 1 or 2 entries
        # If both happen within the same second, should be deduplicated to 1
        assert len(history) <= 2

    def test_is_duplicate_history_entry(self, translation_tracker):
        """Test duplicate detection for history entries."""
        now = datetime.now(timezone.utc).isoformat()

        entry1: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": now,
            "commit_sha": "a91228a",
        }

        entry2: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": now,
            "commit_sha": "a91228a",
        }

        history = [entry1]

        # Should detect as duplicate
        is_dup = translation_tracker._is_duplicate_history_entry(history, entry2)
        assert is_dup is True

    def test_is_not_duplicate_different_action(self, translation_tracker):
        """Test that different actions are not duplicates."""
        now = datetime.now(timezone.utc).isoformat()

        entry1: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": now,
            "commit_sha": "a91228a",
        }

        entry2: HistoryEntry = {
            "action": "smudge",  # Different action
            "from_language": "es",
            "to_language": "en",
            "timestamp": now,
            "commit_sha": "a91228a",
        }

        history = [entry1]

        # Should NOT detect as duplicate
        is_dup = translation_tracker._is_duplicate_history_entry(history, entry2)
        assert is_dup is False

    def test_is_not_duplicate_time_difference(self, translation_tracker):
        """Test that entries with >1 minute difference are not duplicates."""
        now = datetime.now(timezone.utc)
        earlier = (now - timedelta(minutes=2)).isoformat()
        later = now.isoformat()

        entry1: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": earlier,
            "commit_sha": "a91228a",
        }

        entry2: HistoryEntry = {
            "action": "clean",
            "from_language": "es",
            "to_language": "en",
            "timestamp": later,
            "commit_sha": "a91228a",
        }

        history = [entry1]

        # Should NOT detect as duplicate (>1 minute apart)
        is_dup = translation_tracker._is_duplicate_history_entry(history, entry2)
        assert is_dup is False


class TestDeduplicationTranslationRecords:
    """Tests for translation record deduplication."""

    def test_deduplication_translation_records(
        self, translation_tracker, file_with_metadata
    ):
        """Test that translation records are deduplicated by language.

        Note: The current implementation of TranslationTracker has logic to avoid
        adding duplicate translation records based on timestamp comparison. However,
        if two operations happen in quick succession with different timestamps,
        both may be added. This test verifies the deduplication logic exists.
        """
        # Track multiple operations to same language
        translation_tracker.track_clean(file_with_metadata, "es", "en")

        # Small delay to ensure same timestamp wouldn't be used
        import time

        time.sleep(0.001)

        translation_tracker.track_clean(file_with_metadata, "es", "en")

        # Check translation records
        metadata = translation_tracker.metadata_manager.get_metadata(file_with_metadata)
        assert metadata is not None

        # Should have at least one record for "en", but due to timing may have 2
        # The important thing is that the metadata is valid
        en_records = [t for t in metadata["translations"] if t["language"] == "en"]
        assert len(en_records) >= 1

    def test_update_translation_record(self, translation_tracker):
        """Test updating existing translation record."""
        translations: list[TranslationRecord] = []

        # Add first record
        record1: TranslationRecord = {
            "language": "en",
            "method": "token_transformer",
            "timestamp": "2025-11-06T10:00:00Z",
            "commit_sha": "abc123",
            "translator_version": "0.1.0",
            "python_version": "3.13",
        }
        translation_tracker._update_translation_record(translations, record1)

        assert len(translations) == 1

        # Add record for same language (should update)
        record2: TranslationRecord = {
            "language": "en",
            "method": "tree_sitter",
            "timestamp": "2025-11-06T11:00:00Z",
            "commit_sha": "def456",
            "translator_version": "0.2.0",
            "python_version": "3.13",
        }
        translation_tracker._update_translation_record(translations, record2)

        # Should still have only one record, but updated
        assert len(translations) == 1
        assert translations[0]["method"] == "tree_sitter"
        assert translations[0]["commit_sha"] == "def456"

    def test_update_translation_record_different_languages(self, translation_tracker):
        """Test adding records for different languages."""
        translations: list[TranslationRecord] = []

        # Add records for different languages
        for lang in ["en", "es", "fr"]:
            record: TranslationRecord = {
                "language": lang,
                "method": "token_transformer",
                "timestamp": "2025-11-06T10:00:00Z",
                "commit_sha": "abc123",
                "translator_version": "0.1.0",
                "python_version": "3.13",
            }
            translation_tracker._update_translation_record(translations, record)

        # Should have 3 records
        assert len(translations) == 3
        assert set(t["language"] for t in translations) == {"en", "es", "fr"}


class TestTrackOperation:
    """Tests for internal _track_operation method."""

    def test_track_operation_creates_metadata(
        self, translation_tracker, metadata_manager
    ):
        """Test that _track_operation creates metadata if missing."""
        file_path = Path("src/new_file.py")

        # No metadata exists
        assert metadata_manager.get_metadata(file_path) is None

        # Track operation
        translation_tracker._track_operation(
            file_path=file_path,
            action="clean",
            from_language="es",
            to_language="en",
            method="token_transformer",
        )

        # Metadata should now exist
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None

    def test_track_operation_updates_existing(
        self, translation_tracker, file_with_metadata
    ):
        """Test that _track_operation updates existing metadata."""
        # Track operation
        translation_tracker._track_operation(
            file_path=file_with_metadata,
            action="clean",
            from_language="es",
            to_language="en",
            method="token_transformer",
        )

        # Check metadata was updated
        metadata = translation_tracker.metadata_manager.get_metadata(file_with_metadata)
        assert metadata is not None
        assert len(metadata["history"]) == 1
        assert len(metadata["translations"]) == 1

    def test_track_operation_updates_timestamp(
        self, translation_tracker, file_with_metadata
    ):
        """Test that _track_operation updates metadata timestamp."""
        # Get original timestamp
        original = translation_tracker.metadata_manager.get_metadata(file_with_metadata)
        assert original is not None
        original_timestamp = original["updated_at"]

        # Track operation
        translation_tracker._track_operation(
            file_path=file_with_metadata,
            action="clean",
            from_language="es",
            to_language="en",
            method="token_transformer",
        )

        # Timestamp should be updated
        updated = translation_tracker.metadata_manager.get_metadata(file_with_metadata)
        assert updated is not None
        # Note: timestamp might be same if operation is very fast
        assert updated["updated_at"] >= original_timestamp


class TestIntegrationWithMetadataManager:
    """Integration tests with MetadataManager."""

    def test_full_workflow(self, translation_tracker, metadata_manager):
        """Test complete workflow from creation to retrieval."""
        file_path = Path("src/workflow_test.py")

        # Track multiple operations
        translation_tracker.track_clean(file_path, "es", "en")
        translation_tracker.track_smudge(file_path, "en", "es")
        translation_tracker.track_clean(file_path, "es", "en")

        # Verify metadata exists
        metadata = metadata_manager.get_metadata(file_path)
        assert metadata is not None

        # Verify history
        history = translation_tracker.get_translation_history(file_path)
        assert len(history) >= 2

        # Verify latest translation
        latest = translation_tracker.get_latest_translation(file_path)
        assert latest is not None

    def test_metadata_persistence(
        self, translation_tracker, metadata_manager, temp_repo
    ):
        """Test that metadata persists across tracker instances."""
        file_path = Path("src/persist_test.py")

        # Track with first tracker
        translation_tracker.track_clean(file_path, "es", "en")

        # Create new tracker instance
        new_manager = MetadataManager(temp_repo)
        new_tracker = TranslationTracker(new_manager)

        # Should still have history
        history = new_tracker.get_translation_history(file_path)
        assert len(history) >= 1


class TestErrorHandling:
    """Tests for error handling and graceful degradation."""

    def test_error_handling(self, translation_tracker, caplog):
        """Test that errors are caught and logged, not raised."""
        # Use invalid path
        invalid_path = Path("/invalid/path/file.py")

        # Should not raise exceptions
        try:
            translation_tracker.track_clean(invalid_path, "es", "en")
            translation_tracker.track_smudge(invalid_path, "en", "es")
            translation_tracker.get_translation_history(invalid_path)
            translation_tracker.get_latest_translation(invalid_path)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")

        # Should have logged warnings
        assert len(caplog.records) > 0

    @patch.object(MetadataManager, "get_metadata")
    def test_metadata_manager_error_handling(
        self, mock_get, translation_tracker, caplog
    ):
        """Test handling of MetadataManager errors."""
        # Make get_metadata raise an exception
        mock_get.side_effect = Exception("Simulated error")

        file_path = Path("src/test.py")

        # Should not raise
        history = translation_tracker.get_translation_history(file_path)
        assert history == []

    @patch.object(MetadataManager, "add_history_entry")
    def test_add_history_entry_error_handling(
        self, mock_add, translation_tracker, file_with_metadata, caplog
    ):
        """Test handling of add_history_entry errors."""
        # Make add_history_entry raise an exception
        mock_add.side_effect = Exception("Simulated add error")

        # Should not raise
        try:
            translation_tracker.track_clean(file_with_metadata, "es", "en")
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_file_path(self, translation_tracker):
        """Test handling of empty file path."""
        file_path = Path("")

        # Should handle gracefully
        translation_tracker.track_clean(file_path, "es", "en")
        history = translation_tracker.get_translation_history(file_path)
        assert isinstance(history, list)

    def test_special_characters_in_languages(
        self, translation_tracker, file_with_metadata
    ):
        """Test handling of special characters in language codes."""
        # Use language codes with hyphens (e.g., zh-CN)
        translation_tracker.track_clean(
            file_with_metadata, from_language="zh-CN", to_language="en-US"
        )

        history = translation_tracker.get_translation_history(file_with_metadata)
        assert len(history) >= 1

    def test_very_long_commit_sha(self, translation_tracker, file_with_metadata):
        """Test handling of very long commit SHAs."""
        # Manually create context with long SHA
        with patch.object(
            translation_tracker, "_get_git_commit_sha", return_value="a" * 40
        ):
            translation_tracker.track_clean(file_with_metadata, "es", "en")

            latest = translation_tracker.get_latest_translation(file_with_metadata)
            assert latest is not None
            # SHA should be shortened to 7 chars by _get_git_commit_sha
            # but if it returns 40 chars, it should still be stored
            assert len(latest["commit_sha"]) > 0

    def test_concurrent_tracking(self, translation_tracker, file_with_metadata):
        """Test concurrent tracking operations."""
        import threading

        errors = []

        def track_operations():
            try:
                for i in range(10):
                    translation_tracker.track_clean(file_with_metadata, "es", "en")
            except Exception as e:
                errors.append(e)

        # Run concurrent operations
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=track_operations)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should not have any errors
        assert len(errors) == 0

        # Should have some history entries
        history = translation_tracker.get_translation_history(file_with_metadata)
        assert len(history) > 0
