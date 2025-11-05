"""Metadata management for translation tracking.

This module provides the MetadataManager class for reading, writing, and
managing YAML metadata files in the .legesher/metadata/ directory. Each
source file gets a corresponding metadata file that tracks translation
history, git operations, and file configuration.

The metadata system enables:
- Audit trail for all translations and git operations
- Tracking original language and Python version
- Debugging translation issues
- Understanding file evolution over time

Example:
    >>> from pathlib import Path
    >>> from legesher_core.metadata import MetadataManager
    >>> manager = MetadataManager(Path("/path/to/repo"))
    >>>
    >>> # Create metadata for new file
    >>> metadata = manager.create_metadata(
    ...     Path("src/calculator.py"),
    ...     original_language="es",
    ...     python_version="3.13"
    ... )
    >>>
    >>> # Read existing metadata
    >>> metadata = manager.get_metadata(Path("src/calculator.py"))
    >>> if metadata:
    ...     print(f"Original language: {metadata['original_language']}")
    >>>
    >>> # Record translation operation
    >>> from legesher_core.types import TranslationRecord
    >>> record: TranslationRecord = {
    ...     "language": "en",
    ...     "method": "token_transformer",
    ...     "timestamp": "2025-11-06T10:30:00Z",
    ...     "commit_sha": "a91228a",
    ...     "translator_version": "0.1.0",
    ...     "python_version": "3.13"
    ... }
    >>> manager.record_translation(Path("src/calculator.py"), record)
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .types import FileMetadata, HistoryEntry, TranslationRecord

# Configure module logger
logger = logging.getLogger(__name__)


class MetadataManager:
    """Manages translation metadata files in .legesher/metadata/ directory.

    Provides CRUD operations for file metadata stored as YAML files. Each
    source file gets a corresponding metadata file that tracks translations,
    git operations, and configuration.

    The metadata directory structure mirrors the source tree:
        .legesher/metadata/
        └── src/
            └── calculator.py.yml  # Metadata for src/calculator.py

    All file operations are atomic (write to temp file, then rename) to
    prevent corruption during git operations or crashes.

    Attributes:
        repo_root: Absolute path to repository root
        metadata_dir: Path to .legesher/metadata directory

    Example:
        >>> manager = MetadataManager(Path("/path/to/repo"))
        >>> manager.create_metadata(
        ...     Path("src/main.py"),
        ...     original_language="es",
        ...     python_version="3.13"
        ... )
    """

    def __init__(self, repo_root: Path):
        """Initialize MetadataManager with repository root.

        Args:
            repo_root: Absolute path to repository root directory

        Example:
            >>> manager = MetadataManager(Path.cwd())
        """
        self.repo_root = repo_root.resolve()
        self.metadata_dir = self.repo_root / ".legesher" / "metadata"
        logger.debug(
            f"Initialized MetadataManager: repo_root={self.repo_root}, "
            f"metadata_dir={self.metadata_dir}"
        )

    def get_metadata(self, file_path: Path) -> FileMetadata | None:
        """Read metadata for a file.

        Args:
            file_path: Path to source file (absolute or relative to repo_root)

        Returns:
            FileMetadata dict if file exists, None if not found or on error

        Example:
            >>> metadata = manager.get_metadata(Path("src/calculator.py"))
            >>> if metadata:
            ...     print(f"Created: {metadata['created_at']}")
        """
        metadata_path = self._get_metadata_path(file_path)

        if not metadata_path.exists():
            logger.debug(f"Metadata file not found: {metadata_path}")
            return None

        data = self._read_yaml(metadata_path)
        if data is None:
            return None

        try:
            # Validate required fields
            metadata: FileMetadata = {
                "file": data["file"],
                "original_language": data["original_language"],
                "canonical_language": data["canonical_language"],
                "python_version": data["python_version"],
                "created_at": data["created_at"],
                "updated_at": data["updated_at"],
                "translations": data.get("translations", []),
                "history": data.get("history", []),
            }
            logger.debug(f"Successfully read metadata from {metadata_path}")
            return metadata
        except KeyError as e:
            logger.warning(
                f"Invalid metadata file {metadata_path}: missing field {e}",
                exc_info=True,
            )
            return None

    def create_metadata(
        self, file_path: Path, original_language: str, python_version: str
    ) -> FileMetadata:
        """Create new metadata for a file.

        Creates a new metadata file with initial values. The canonical
        language is always set to "en" (English) as that's what's stored
        in git.

        Args:
            file_path: Path to source file (absolute or relative to repo_root)
            original_language: Language file was originally written in
            python_version: Python version for this file (e.g., "3.13")

        Returns:
            Newly created FileMetadata dict

        Raises:
            OSError: If metadata directory cannot be created or file cannot be written

        Example:
            >>> metadata = manager.create_metadata(
            ...     Path("src/taxes.py"),
            ...     original_language="es",
            ...     python_version="3.13"
            ... )
            >>> print(metadata["file"])
            src/taxes.py
        """
        metadata_path = self._get_metadata_path(file_path)
        relative_path = self._get_relative_path(file_path)
        timestamp = datetime.now(UTC).isoformat()

        metadata: FileMetadata = {
            "file": str(relative_path),
            "original_language": original_language,
            "canonical_language": "en",  # Always English in git
            "python_version": python_version,
            "created_at": timestamp,
            "updated_at": timestamp,
            "translations": [],
            "history": [],
        }

        # Create parent directories if needed
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        self._write_yaml(metadata_path, metadata)
        logger.info(
            f"Created metadata for {relative_path}: "
            f"original_language={original_language}, "
            f"python_version={python_version}"
        )

        return metadata

    def update_metadata(self, file_path: Path, updates: dict) -> None:
        """Update existing metadata with partial updates.

        Reads existing metadata, applies updates, and writes back atomically.
        Automatically updates the 'updated_at' timestamp.

        Args:
            file_path: Path to source file
            updates: Dictionary of fields to update (partial update supported)

        Example:
            >>> manager.update_metadata(
            ...     Path("src/main.py"),
            ...     {"python_version": "3.12"}
            ... )
        """
        metadata = self.get_metadata(file_path)
        if metadata is None:
            logger.warning(
                f"Cannot update metadata for {file_path}: metadata not found"
            )
            return

        # Apply updates
        for key, value in updates.items():
            if key in metadata:
                metadata[key] = value  # type: ignore
            else:
                logger.warning(
                    f"Ignoring unknown metadata field '{key}' for {file_path}"
                )

        # Update timestamp
        metadata["updated_at"] = datetime.now(UTC).isoformat()

        metadata_path = self._get_metadata_path(file_path)
        self._write_yaml(metadata_path, metadata)
        logger.debug(f"Updated metadata for {file_path}: {updates.keys()}")

    def record_translation(self, file_path: Path, record: TranslationRecord) -> None:
        """Add a translation record to metadata.

        Appends a new translation record to the file's metadata and updates
        the timestamp. Creates metadata if it doesn't exist.

        Args:
            file_path: Path to source file
            record: Translation record to append

        Example:
            >>> record: TranslationRecord = {
            ...     "language": "en",
            ...     "method": "token_transformer",
            ...     "timestamp": "2025-11-06T10:30:00Z",
            ...     "commit_sha": "a91228a",
            ...     "translator_version": "0.1.0",
            ...     "python_version": "3.13"
            ... }
            >>> manager.record_translation(Path("src/main.py"), record)
        """
        metadata = self.get_metadata(file_path)
        if metadata is None:
            logger.warning(
                f"Cannot record translation for {file_path}: metadata not found. "
                "Create metadata first with create_metadata()."
            )
            return

        metadata["translations"].append(record)
        metadata["updated_at"] = datetime.now(UTC).isoformat()

        metadata_path = self._get_metadata_path(file_path)
        self._write_yaml(metadata_path, metadata)
        logger.info(
            f"Recorded translation for {file_path}: "
            f"language={record['language']}, method={record['method']}"
        )

    def add_history_entry(self, file_path: Path, entry: HistoryEntry) -> None:
        """Append history entry to metadata.

        Records a git filter operation (clean/smudge) in the file's history.
        Creates metadata if it doesn't exist.

        Args:
            file_path: Path to source file
            entry: History entry to append

        Example:
            >>> entry: HistoryEntry = {
            ...     "action": "clean",
            ...     "from_language": "es",
            ...     "to_language": "en",
            ...     "timestamp": "2025-11-06T10:30:00Z",
            ...     "commit_sha": "a91228a"
            ... }
            >>> manager.add_history_entry(Path("src/main.py"), entry)
        """
        metadata = self.get_metadata(file_path)
        if metadata is None:
            logger.warning(
                f"Cannot add history entry for {file_path}: metadata not found. "
                "Create metadata first with create_metadata()."
            )
            return

        metadata["history"].append(entry)
        metadata["updated_at"] = datetime.now(UTC).isoformat()

        metadata_path = self._get_metadata_path(file_path)
        self._write_yaml(metadata_path, metadata)
        logger.debug(
            f"Added history entry for {file_path}: "
            f"action={entry['action']}, {entry['from_language']}->{entry['to_language']}"
        )

    def list_metadata_files(self) -> list[Path]:
        """List all metadata files in the repository.

        Returns:
            List of paths to all .yml metadata files

        Example:
            >>> files = manager.list_metadata_files()
            >>> for f in files:
            ...     print(f)
            .legesher/metadata/src/main.py.yml
            .legesher/metadata/src/calculator.py.yml
        """
        if not self.metadata_dir.exists():
            logger.debug(f"Metadata directory does not exist: {self.metadata_dir}")
            return []

        metadata_files = list(self.metadata_dir.rglob("*.yml"))
        logger.debug(f"Found {len(metadata_files)} metadata files")
        return metadata_files

    def validate_metadata(self, file_path: Path) -> bool:
        """Validate metadata file integrity.

        Checks that the metadata file exists, is valid YAML, and contains
        all required fields.

        Args:
            file_path: Path to source file

        Returns:
            True if metadata is valid, False otherwise

        Example:
            >>> if manager.validate_metadata(Path("src/main.py")):
            ...     print("Metadata is valid")
        """
        metadata = self.get_metadata(file_path)
        if metadata is None:
            return False

        # Check required fields
        required_fields = [
            "file",
            "original_language",
            "canonical_language",
            "python_version",
            "created_at",
            "updated_at",
            "translations",
            "history",
        ]

        for field in required_fields:
            if field not in metadata:
                logger.warning(
                    f"Metadata for {file_path} missing required field: {field}"
                )
                return False

        logger.debug(f"Metadata for {file_path} is valid")
        return True

    # Private helper methods

    def _get_metadata_path(self, file_path: Path) -> Path:
        """Convert source file path to metadata file path.

        Args:
            file_path: Path to source file

        Returns:
            Path to corresponding metadata file

        Example:
            >>> manager._get_metadata_path(Path("src/main.py"))
            PosixPath('/repo/.legesher/metadata/src/main.py.yml')
        """
        relative_path = self._get_relative_path(file_path)
        metadata_path = self.metadata_dir / f"{relative_path}.yml"
        return metadata_path

    def _get_relative_path(self, file_path: Path) -> Path:
        """Get path relative to repository root.

        Args:
            file_path: Absolute or relative path

        Returns:
            Path relative to repo_root

        Example:
            >>> manager._get_relative_path(Path("/repo/src/main.py"))
            PosixPath('src/main.py')
        """
        try:
            # If absolute path, make it relative to repo_root
            if file_path.is_absolute():
                # Resolve both paths to handle symlinks (e.g., /var vs /private/var on macOS)
                resolved_file = file_path.resolve()
                resolved_root = self.repo_root.resolve()
                return resolved_file.relative_to(resolved_root)
            else:
                return file_path
        except ValueError:
            # Path is not under repo_root, return as-is
            logger.warning(
                f"Path {file_path} is not under repo_root {self.repo_root}, using as-is"
            )
            return file_path

    def _read_yaml(self, path: Path) -> dict | None:
        """Read and parse YAML file safely.

        Uses safe_load to prevent arbitrary code execution. Returns None
        on any error to enable graceful degradation.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML data as dict, or None on error

        Example:
            >>> data = manager._read_yaml(Path(".legesher/metadata/src/main.py.yml"))
            >>> if data:
            ...     print(data["file"])
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    logger.warning(f"YAML file {path} did not contain a dict")
                    return None
                return data
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML file {path}: {e}", exc_info=True)
            return None
        except OSError as e:
            logger.warning(f"Failed to read file {path}: {e}", exc_info=True)
            return None

    def _write_yaml(self, path: Path, data: FileMetadata | dict[str, Any]) -> None:
        """Write YAML file atomically.

        Writes to a temporary file first, then renames atomically to prevent
        corruption during git operations or crashes. This ensures metadata
        files are never partially written.

        Args:
            path: Path to YAML file
            data: FileMetadata or dictionary to serialize as YAML

        Raises:
            OSError: If file cannot be written

        Example:
            >>> manager._write_yaml(
            ...     Path(".legesher/metadata/src/main.py.yml"),
            ...     {"file": "src/main.py", ...}
            ... )
        """
        # Write to temporary file first
        temp_path = path.parent / f".{path.name}.tmp"

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            # Atomic rename
            temp_path.rename(path)
            logger.debug(f"Wrote YAML file atomically: {path}")

        except OSError as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass  # Best effort cleanup

            logger.error(f"Failed to write YAML file {path}: {e}", exc_info=True)
            raise
