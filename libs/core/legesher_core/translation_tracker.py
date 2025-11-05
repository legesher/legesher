"""Translation tracker for recording git filter operations.

This module provides a high-level API for tracking code translation operations
during git clean/smudge filters. It uses MetadataManager to persist metadata
about translation history and maintains an audit trail of all operations.

Example:
    >>> from legesher_core.metadata import MetadataManager
    >>> from legesher_core.translation_tracker import TranslationTracker
    >>>
    >>> manager = MetadataManager("/path/to/repo/.legesher/metadata")
    >>> tracker = TranslationTracker(manager)
    >>>
    >>> # Track a clean filter operation (es → en)
    >>> tracker.track_clean(
    ...     file_path=Path("src/main.py"),
    ...     from_language="es",
    ...     to_language="en"
    ... )
    >>>
    >>> # Get translation history
    >>> history = tracker.get_translation_history(Path("src/main.py"))
"""

from pathlib import Path
from datetime import datetime, timezone
import subprocess
import sys
import logging

from .types import TranslationRecord, HistoryEntry
from .metadata import MetadataManager

# Configure logger
logger = logging.getLogger(__name__)


class TranslationTracker:
    """Tracks code translation operations and records metadata.

    This class provides a high-level API for recording translation operations
    during git clean/smudge filters. It automatically gathers execution context
    (git commit SHA, Python version, translator version) and maintains both
    translation records and history logs.

    Translation records track cumulative state (which languages a file has been
    translated to), while history entries provide a chronological audit trail
    of git filter operations.

    Attributes:
        metadata_manager: MetadataManager instance for persistence

    Example:
        >>> manager = MetadataManager(Path(".legesher/metadata"))
        >>> tracker = TranslationTracker(manager)
        >>>
        >>> # Track clean filter (local → canonical)
        >>> tracker.track_clean(
        ...     file_path=Path("src/main.py"),
        ...     from_language="es",
        ...     to_language="en"
        ... )
        >>>
        >>> # Track smudge filter (canonical → local)
        >>> tracker.track_smudge(
        ...     file_path=Path("src/main.py"),
        ...     from_language="en",
        ...     to_language="es"
        ... )
        >>>
        >>> # Get history
        >>> history = tracker.get_translation_history(Path("src/main.py"))
        >>> print(f"File has {len(history)} operations")
    """

    def __init__(self, metadata_manager: MetadataManager):
        """Initialize with MetadataManager instance.

        Args:
            metadata_manager: MetadataManager for storing metadata
        """
        self.metadata_manager = metadata_manager

    def track_clean(
        self,
        file_path: Path,
        from_language: str,
        to_language: str,
        method: str = "token_transformer",
    ) -> None:
        """Track a git clean filter operation (local → canonical).

        Records a history entry for the clean operation and updates the
        translation record for the target language. This is called during
        git add/commit when translating from working directory language
        to canonical git storage language.

        Args:
            file_path: Path to file being translated (relative to repo root)
            from_language: Source language code (e.g., "es")
            to_language: Target language code (usually "en" for canonical)
            method: Translation method used (default: "token_transformer")

        Example:
            >>> # User commits Spanish code, git translates to English
            >>> tracker.track_clean(
            ...     file_path=Path("src/calculator.py"),
            ...     from_language="es",
            ...     to_language="en",
            ...     method="token_transformer"
            ... )

        Note:
            This method never raises exceptions. All errors are logged as
            warnings for graceful degradation.
        """
        try:
            self._track_operation(
                file_path=file_path,
                action="clean",
                from_language=from_language,
                to_language=to_language,
                method=method,
            )
        except Exception as e:
            logger.warning(
                f"Failed to track clean operation for {file_path}: {e}", exc_info=True
            )

    def track_smudge(
        self,
        file_path: Path,
        from_language: str,
        to_language: str,
        method: str = "token_transformer",
    ) -> None:
        """Track a git smudge filter operation (canonical → local).

        Records a history entry for the smudge operation and updates the
        translation record for the target language. This is called during
        git checkout/pull when translating from canonical git storage
        language to working directory language.

        Args:
            file_path: Path to file being translated (relative to repo root)
            from_language: Source language code (usually "en" for canonical)
            to_language: Target language code (e.g., "es")
            method: Translation method used (default: "token_transformer")

        Example:
            >>> # User checks out repo, git translates English to Spanish
            >>> tracker.track_smudge(
            ...     file_path=Path("src/calculator.py"),
            ...     from_language="en",
            ...     to_language="es",
            ...     method="token_transformer"
            ... )

        Note:
            This method never raises exceptions. All errors are logged as
            warnings for graceful degradation.
        """
        try:
            self._track_operation(
                file_path=file_path,
                action="smudge",
                from_language=from_language,
                to_language=to_language,
                method=method,
            )
        except Exception as e:
            logger.warning(
                f"Failed to track smudge operation for {file_path}: {e}", exc_info=True
            )

    def get_translation_history(self, file_path: Path) -> list[HistoryEntry]:
        """Get full translation history for a file.

        Returns chronological list of all git filter operations (clean/smudge)
        that have been performed on this file. Useful for debugging translation
        issues and understanding how a file has moved between languages.

        Args:
            file_path: Path to file (relative to repo root)

        Returns:
            List of history entries in chronological order (oldest first).
            Returns empty list if file has no metadata or on error.

        Example:
            >>> history = tracker.get_translation_history(Path("src/main.py"))
            >>> for entry in history:
            ...     print(f"{entry['action']}: {entry['from_language']} → {entry['to_language']}")
            clean: es → en
            smudge: en → es
            clean: es → en
        """
        try:
            metadata = self.metadata_manager.get_metadata(file_path)
            if metadata is None:
                return []
            return metadata.get("history", [])
        except Exception as e:
            logger.warning(
                f"Failed to get translation history for {file_path}: {e}", exc_info=True
            )
            return []

    def get_latest_translation(self, file_path: Path) -> TranslationRecord | None:
        """Get most recent translation record for a file.

        Returns the newest translation record based on timestamp. This shows
        the most recent translation operation performed, which is useful for
        understanding current file state.

        Args:
            file_path: Path to file (relative to repo root)

        Returns:
            Most recent TranslationRecord or None if no translations exist
            or on error.

        Example:
            >>> latest = tracker.get_latest_translation(Path("src/main.py"))
            >>> if latest:
            ...     print(f"Last translated to {latest['language']} at {latest['timestamp']}")
            Last translated to en at 2025-11-06T10:30:00Z
        """
        try:
            metadata = self.metadata_manager.get_metadata(file_path)
            if metadata is None or not metadata.get("translations"):
                return None

            # Get translation with most recent timestamp
            translations = metadata["translations"]
            latest = max(translations, key=lambda t: t["timestamp"])
            return latest
        except Exception as e:
            logger.warning(
                f"Failed to get latest translation for {file_path}: {e}", exc_info=True
            )
            return None

    def _track_operation(
        self,
        file_path: Path,
        action: str,
        from_language: str,
        to_language: str,
        method: str,
    ) -> None:
        """Internal method to track a translation operation.

        This method:
        1. Gets or creates metadata for the file
        2. Gathers current execution context
        3. Adds history entry (with deduplication)
        4. Updates/adds translation record (with deduplication)

        Args:
            file_path: Path to file being translated
            action: Git filter action ("clean" or "smudge")
            from_language: Source language code
            to_language: Target language code
            method: Translation method used

        Raises:
            Exception: Any error during tracking (caught by public methods)
        """
        # Get or create metadata
        metadata = self.metadata_manager.get_metadata(file_path)
        if metadata is None:
            # Create new metadata (assuming canonical language is English)
            # In production, this should be configurable
            metadata = self.metadata_manager.create_metadata(
                file_path=file_path,
                original_language=from_language,
                python_version=self._get_python_version(),
            )

        # Gather current execution context
        context = self._get_current_context()

        # Add history entry (with deduplication)
        history_entry: HistoryEntry = {
            "action": action,
            "from_language": from_language,
            "to_language": to_language,
            "timestamp": context["timestamp"],
            "commit_sha": context["commit_sha"],
        }

        if not self._is_duplicate_history_entry(metadata["history"], history_entry):
            self.metadata_manager.add_history_entry(file_path, history_entry)

        # Update or add translation record (with deduplication)
        translation_record: TranslationRecord = {
            "language": to_language,
            "method": method,
            "timestamp": context["timestamp"],
            "commit_sha": context["commit_sha"],
            "translator_version": context["translator_version"],
            "python_version": context["python_version"],
        }

        # Check if translation record needs to be added/updated
        existing_metadata = self.metadata_manager.get_metadata(file_path)
        if existing_metadata:
            # Check if we need to add this translation record
            should_update = True
            for existing_record in existing_metadata["translations"]:
                if existing_record["language"] == to_language:
                    # Language already exists, check if it needs updating
                    if existing_record["timestamp"] >= translation_record["timestamp"]:
                        should_update = False
                    break

            if should_update:
                self.metadata_manager.record_translation(file_path, translation_record)

    def _is_duplicate_history_entry(
        self, history: list[HistoryEntry], new_entry: HistoryEntry
    ) -> bool:
        """Check if history entry is a duplicate.

        A history entry is considered duplicate if there's an existing entry
        with the same action, languages, and timestamp within 1 minute.

        Args:
            history: Existing history entries
            new_entry: New entry to check

        Returns:
            True if duplicate exists, False otherwise
        """
        if not history:
            return False

        # Get the last entry
        last_entry = history[-1]

        # Check if action and languages match
        if (
            last_entry["action"] != new_entry["action"]
            or last_entry["from_language"] != new_entry["from_language"]
            or last_entry["to_language"] != new_entry["to_language"]
        ):
            return False

        # Check if timestamps are within 1 minute
        try:
            last_time = datetime.fromisoformat(
                last_entry["timestamp"].replace("Z", "+00:00")
            )
            new_time = datetime.fromisoformat(
                new_entry["timestamp"].replace("Z", "+00:00")
            )
            time_diff = abs((new_time - last_time).total_seconds())
            return time_diff < 60
        except (ValueError, KeyError):
            # If we can't parse timestamps, consider it not duplicate
            return False

    def _update_translation_record(
        self, translations: list[TranslationRecord], new_record: TranslationRecord
    ) -> None:
        """Update or add a translation record.

        If a record for the target language already exists, updates it.
        Otherwise, adds a new record. This ensures we only have one record
        per language, with the most recent information.

        Args:
            translations: List of existing translation records (modified in place)
            new_record: New record to add or update with
        """
        # Find existing record for this language
        for i, record in enumerate(translations):
            if record["language"] == new_record["language"]:
                # Update existing record
                translations[i] = new_record
                return

        # No existing record, add new one
        translations.append(new_record)

    def _get_current_context(self) -> dict:
        """Gather current execution context.

        Collects information about the current environment including:
        - Timestamp (ISO 8601 format with timezone)
        - Git commit SHA (if in a git repository)
        - Translator version (legesher-core version)
        - Python version (e.g., "3.13")

        Returns:
            Dictionary with context information. All fields guaranteed to exist,
            but commit_sha may be None if not in git repository or on error.

        Example:
            >>> context = tracker._get_current_context()
            >>> print(context)
            {
                'timestamp': '2025-11-06T10:30:00+00:00',
                'commit_sha': 'a91228a',
                'translator_version': '0.0.1',
                'python_version': '3.13'
            }
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "commit_sha": self._get_git_commit_sha(),
            "translator_version": self._get_translator_version(),
            "python_version": self._get_python_version(),
        }

    def _get_git_commit_sha(self) -> str | None:
        """Get current git commit SHA if in a git repo.

        Runs `git rev-parse HEAD` to get the current commit SHA.
        Returns short SHA (7 characters) for consistency with git conventions.

        Returns:
            Short git commit SHA (7 chars) or None if not in git repo or on error.

        Example:
            >>> sha = tracker._get_git_commit_sha()
            >>> print(sha)
            a91228a
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            full_sha = result.stdout.strip()
            # Return short SHA (first 7 characters)
            return full_sha[:7] if full_sha else None
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
        ):
            # Not in a git repo or git not available
            return None
        except Exception as e:
            logger.debug(f"Failed to get git commit SHA: {e}")
            return None

    def _get_translator_version(self) -> str:
        """Get legesher-core version.

        Attempts to get version from package metadata. Falls back to "unknown"
        if version cannot be determined.

        Returns:
            Version string (e.g., "0.0.1") or "unknown" if unavailable.

        Example:
            >>> version = tracker._get_translator_version()
            >>> print(version)
            0.0.1
        """
        try:
            # Try to import version from package
            from legesher_core import __version__

            return __version__
        except ImportError:
            pass

        try:
            # Try using importlib.metadata (Python 3.8+)
            from importlib.metadata import version

            return version("legesher-core")
        except Exception:
            pass

        # Fallback if version unavailable
        return "unknown"

    def _get_python_version(self) -> str:
        """Get Python version (e.g., '3.13').

        Returns the major.minor version of the Python interpreter currently
        running. This is used to track which Python version was used for
        translation, which is important for version-aware language packs.

        Returns:
            Python version string in format "major.minor" (e.g., "3.13")

        Example:
            >>> version = tracker._get_python_version()
            >>> print(version)
            3.13
        """
        return f"{sys.version_info.major}.{sys.version_info.minor}"
