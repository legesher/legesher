"""Configuration management for Legesher.

This module handles reading and writing Legesher configuration files,
which store user preferences for language, Python version, and git settings.

Configuration files are stored in YAML format at:
    - Project config: .legesher/config.yml (in git repo root)
    - User global config: ~/.legesher/config.yml (user home directory)

Configuration precedence (highest to lowest):
    1. Project config (.legesher/config.yml)
    2. User global config (~/.legesher/config.yml)
    3. Default values

The ``telemetry`` section is the exception: it is consent, so it is read
from the user config only and a project config cannot change it. A
committed project file must not be able to opt every collaborator in, or
switch a user's telemetry back on.
"""

import copy
import logging
from pathlib import Path
from typing import Optional

import yaml

# Configure logger
logger = logging.getLogger(__name__)

# Telemetry defaults: on (with a first-run notice), repo attribution off.
DEFAULT_TELEMETRY: dict[str, bool] = {
    "enabled": True,
    "repo_attribution": False,
}

# Default configuration values
DEFAULT_CONFIG = {
    "language": "en",
    "python_version": None,  # Auto-detect if not specified
    "git": {
        "canonical_language": "en",
        "filter_enabled": True,
    },
    "runtime": {
        "cache_size": 128,
    },
    "metadata": {
        "enabled": True,
        "directory": ".legesher/metadata",
        "track_in_git": True,
        "verbose_history": False,
        "max_history_entries": 100,
    },
    # Telemetry is opt-out with a first-run notice; repo attribution (the
    # X-Legesher-Repo label on hosted calls) is a separate opt-in. The
    # kill switches LEGESHER_TELEMETRY_DISABLED and DO_NOT_TRACK win over
    # both (legesher_core.repo_attribution). Read from the user config only.
    "telemetry": dict(DEFAULT_TELEMETRY),
}

#: Top-level config keys a project config may not set (see the module docstring).
USER_ONLY_SECTIONS = ("telemetry",)


def telemetry_section(value: object) -> dict:
    """A ``telemetry`` config value as a mapping.

    ``null`` (or a missing section) reads as an empty section. A scalar in
    place of the mapping (``telemetry: false``, ``telemetry: off``) is read
    as the ``enabled`` switch; ``legesher_core.repo_attribution`` decides
    which values mean off, so that rule lives in one place.
    """
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"enabled": value}


def user_telemetry(user_data: object) -> dict:
    """The effective telemetry section: the user's own, else the defaults.

    ``user_data`` is the user config file's raw YAML (``None`` when there is
    no file). Project config never contributes to this.
    """
    if isinstance(user_data, dict) and "telemetry" in user_data:
        return {
            **DEFAULT_TELEMETRY,
            **telemetry_section(user_data["telemetry"]),
        }
    return dict(DEFAULT_TELEMETRY)


class LegesherConfig:
    """Legesher configuration manager.

    Handles reading and writing configuration files for Legesher projects.
    Supports both project-level (.legesher/config.yml) and user-level
    (~/.legesher/config.yml) configuration files.

    Attributes:
        language: Default natural language code (e.g., "es", "ar")
        python_version: Python version (e.g., "3.13", None for auto-detect)
        git_canonical_language: Language used for git storage (default: "en")
        git_filter_enabled: Whether git filters are enabled (default: True)
        metadata_enabled: Whether metadata tracking is enabled (default: True)
        metadata_directory: Directory for storing metadata files (default: ".legesher/metadata")
        metadata_track_in_git: Whether to track metadata files in git (default: True)
        metadata_verbose_history: Include detailed history in metadata (default: False)
        metadata_max_history_entries: Maximum history entries per file (default: 100)

    Example:
        >>> # Load configuration
        >>> config = LegesherConfig.load_project_config()
        >>> print(config.language)  # "es"
        >>>
        >>> # Create new configuration
        >>> config = LegesherConfig(language="es", python_version="3.13")
        >>> config.save_project_config()
    """

    def __init__(
        self,
        language: str = "en",
        python_version: str | None = None,
        git_canonical_language: str = "en",
        git_filter_enabled: bool = True,
        metadata_enabled: bool = True,
        metadata_directory: str = ".legesher/metadata",
        metadata_track_in_git: bool = True,
        metadata_verbose_history: bool = False,
        metadata_max_history_entries: int = 100,
        telemetry_enabled: bool = True,
        telemetry_repo_attribution: bool = False,
    ) -> None:
        """Initialize configuration with values.

        Args:
            language: Default natural language code
            python_version: Python version (None for auto-detect)
            git_canonical_language: Language for git storage (default: "en")
            git_filter_enabled: Enable git filters (default: True)
            metadata_enabled: Whether to track translation metadata (default: True)
            metadata_directory: Directory for storing metadata files (default: ".legesher/metadata")
            metadata_track_in_git: Whether to track metadata files in git (default: True)
            metadata_verbose_history: Include detailed history in metadata (default: False)
            metadata_max_history_entries: Maximum history entries per file (default: 100)
        """
        self.language = language
        self.python_version = python_version
        self.git_canonical_language = git_canonical_language
        self.git_filter_enabled = git_filter_enabled
        self.runtime_cache_size = None  # Will be set from dict if provided
        self.metadata_enabled = metadata_enabled
        self.metadata_directory = metadata_directory
        self.metadata_track_in_git = metadata_track_in_git
        self.metadata_verbose_history = metadata_verbose_history
        self.metadata_max_history_entries = metadata_max_history_entries
        self.telemetry_enabled = telemetry_enabled
        self.telemetry_repo_attribution = telemetry_repo_attribution

        # Validate metadata configuration
        self._validate_metadata_config()

    @classmethod
    def from_dict(cls, data: dict) -> "LegesherConfig":
        """Create configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            LegesherConfig instance

        Example:
            >>> data = {"language": "es", "python_version": "3.13"}
            >>> config = LegesherConfig.from_dict(data)
        """
        git_config = data.get("git", {})
        runtime_config = data.get("runtime", {})
        metadata_config = data.get("metadata", {})
        telemetry_config = telemetry_section(data.get("telemetry"))

        config = cls(
            language=data.get("language", "en"),
            python_version=data.get("python_version"),
            git_canonical_language=git_config.get("canonical_language", "en"),
            git_filter_enabled=git_config.get("filter_enabled", True),
            metadata_enabled=metadata_config.get("enabled", True),
            metadata_directory=metadata_config.get("directory", ".legesher/metadata"),
            metadata_track_in_git=metadata_config.get("track_in_git", True),
            metadata_verbose_history=metadata_config.get("verbose_history", False),
            metadata_max_history_entries=metadata_config.get(
                "max_history_entries", 100
            ),
            telemetry_enabled=telemetry_config.get("enabled", True),
            telemetry_repo_attribution=telemetry_config.get("repo_attribution", False),
        )

        # Set runtime_cache_size from config (not in __init__ to keep it simple)
        config.runtime_cache_size = runtime_config.get("cache_size")

        return config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary

        Example:
            >>> config = LegesherConfig(language="es")
            >>> config.to_dict()
            {'language': 'es', 'python_version': None, 'git': {...}, 'runtime': {...}, 'metadata': {...}}
        """
        result = {
            "language": self.language,
            "python_version": self.python_version,
            "git": {
                "canonical_language": self.git_canonical_language,
                "filter_enabled": self.git_filter_enabled,
            },
            "metadata": {
                "enabled": self.metadata_enabled,
                "directory": self.metadata_directory,
                "track_in_git": self.metadata_track_in_git,
                "verbose_history": self.metadata_verbose_history,
                "max_history_entries": self.metadata_max_history_entries,
            },
            "telemetry": {
                "enabled": self.telemetry_enabled,
                "repo_attribution": self.telemetry_repo_attribution,
            },
        }

        # Add runtime config if cache_size is set
        if hasattr(self, "runtime_cache_size") and self.runtime_cache_size is not None:
            result["runtime"] = {"cache_size": self.runtime_cache_size}

        return result

    @classmethod
    def load_project_config(
        cls, repo_root: Path | None = None
    ) -> tuple[Optional["LegesherConfig"], bool]:
        """Load project-level configuration from .legesher/config.yml.

        Args:
            repo_root: Git repository root (default: auto-detect)

        Returns:
            Tuple of (LegesherConfig instance or None, file_exists bool)
            If file doesn't exist, returns (None, False)

        Raises:
            ValueError: If not in a git repository

        Example:
            >>> config, exists = LegesherConfig.load_project_config()
            >>> if exists:
            ...     print(config.language)
        """
        if repo_root is None:
            repo_root = cls._find_repo_root()

        config_path = repo_root / ".legesher" / "config.yml"

        if not config_path.exists():
            logger.debug(f"No project config found at {config_path}")
            return (None, False)

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            logger.info(f"Loaded project config from {config_path}")
            return (cls.from_dict(data), True)

        except Exception as e:
            logger.error(f"Error loading project config: {e}")
            return (None, False)

    @classmethod
    def load_user_config(cls) -> tuple[Optional["LegesherConfig"], bool]:
        """Load user-level configuration from ~/.legesher/config.yml.

        Returns:
            Tuple of (LegesherConfig instance or None, file_exists bool)
            If file doesn't exist, returns (None, False)

        Example:
            >>> config, exists = LegesherConfig.load_user_config()
        """
        config_path = Path.home() / ".legesher" / "config.yml"

        if not config_path.exists():
            logger.debug(f"No user config found at {config_path}")
            return (None, False)

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}

            logger.info(f"Loaded user config from {config_path}")
            return (cls.from_dict(data), True)

        except Exception as e:
            logger.error(f"Error loading user config: {e}")
            return (None, False)

    @classmethod
    def load(cls, repo_root: Path | None = None) -> "LegesherConfig":
        """Load configuration with precedence: project > user > defaults.

        This method loads configuration from both project and user config files,
        with project config taking precedence over user config, except for
        the ``telemetry`` section, which comes from the user config only.

        Args:
            repo_root: Git repository root (default: auto-detect)

        Returns:
            LegesherConfig instance with merged configuration

        Example:
            >>> config = LegesherConfig.load()  # Load with precedence
        """
        # Start with default config
        merged_data = copy.deepcopy(DEFAULT_CONFIG)

        # Merge user config (if exists)
        try:
            user_config, user_exists = cls.load_user_config()
            if user_exists and user_config:
                user_data = user_config.to_dict()
                merged_data.update(user_data)
        except Exception as e:
            logger.debug(f"Could not load user config: {e}")

        # Merge project config (if exists)
        try:
            project_config, project_exists = cls.load_project_config(repo_root)
            if project_exists and project_config:
                project_data = project_config.to_dict()
                merged_data.update(project_data)
        except Exception as e:
            logger.debug(f"Could not load project config: {e}")

        # Telemetry is consent: the user's own section, never the project's.
        # to_dict() always writes a full telemetry block, so without this a
        # project file holding only `language: es` would reset the user's
        # choice, and one holding `telemetry:` would make it for them.
        merged_data["telemetry"] = user_telemetry(cls._read_user_yaml())

        return cls.from_dict(merged_data)

    @staticmethod
    def _read_user_yaml() -> object:
        """The user config file's raw YAML, or ``None`` if it cannot be read."""
        config_path = Path.home() / ".legesher" / "config.yml"
        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (OSError, ValueError, yaml.YAMLError) as e:
            logger.debug(f"Could not read user config for telemetry: {e}")
            return None

    def save_project_config(self, repo_root: Path | None = None) -> Path:
        """Save configuration to project .legesher/config.yml.

        Args:
            repo_root: Git repository root (default: auto-detect)

        Returns:
            Path to saved config file

        Raises:
            ValueError: If not in a git repository

        Example:
            >>> config = LegesherConfig(language="es")
            >>> config_path = config.save_project_config()
        """
        if repo_root is None:
            repo_root = self._find_repo_root()

        # Create .legesher directory if it doesn't exist
        legesher_dir = repo_root / ".legesher"
        legesher_dir.mkdir(exist_ok=True)

        config_path = legesher_dir / "config.yml"

        # Telemetry is per user, so it never goes into a project file.
        data = self.to_dict()
        for section in USER_ONLY_SECTIONS:
            data.pop(section, None)

        # Write configuration
        with open(config_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved project config to {config_path}")
        return config_path

    def save_user_config(self) -> Path:
        """Save configuration to user ~/.legesher/config.yml.

        The file's existing ``telemetry`` section is kept as it is: this
        method rewrites settings such as the language, and must not reset
        a consent choice made with ``legesher config set --global``.

        Returns:
            Path to saved config file

        Example:
            >>> config = LegesherConfig(language="es")
            >>> config_path = config.save_user_config()
        """
        # Create ~/.legesher directory if it doesn't exist
        legesher_dir = Path.home() / ".legesher"
        legesher_dir.mkdir(exist_ok=True)

        config_path = legesher_dir / "config.yml"

        data = self.to_dict()
        for section in USER_ONLY_SECTIONS:
            data.pop(section, None)
        existing = self._read_user_yaml()
        if isinstance(existing, dict):
            for section in USER_ONLY_SECTIONS:
                if section in existing:
                    data[section] = existing[section]

        # Write configuration
        with open(config_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved user config to {config_path}")
        return config_path

    @staticmethod
    def _find_repo_root(start_path: Path | None = None) -> Path:
        """Find git repository root by searching for .git directory.

        Args:
            start_path: Starting path (default: current working directory)

        Returns:
            Path to git repository root

        Raises:
            ValueError: If no git repository found
        """
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()

        # Search upwards for .git directory
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        raise ValueError(f"Not in a git repository (starting from {start_path})")

    def _validate_metadata_config(self) -> None:
        """Validate metadata configuration values.

        Raises:
            ValueError: If configuration values are invalid
        """
        # Ensure directory is relative (not absolute)
        if Path(self.metadata_directory).is_absolute():
            raise ValueError(
                f"metadata_directory must be a relative path, got: {self.metadata_directory}"
            )

        # Ensure max_history_entries is non-negative
        if self.metadata_max_history_entries < 0:
            raise ValueError(
                f"metadata_max_history_entries must be >= 0, got: {self.metadata_max_history_entries}"
            )

    def is_metadata_enabled(self) -> bool:
        """Check if metadata tracking is enabled.

        Returns:
            True if metadata tracking is enabled

        Example:
            >>> config = LegesherConfig(metadata_enabled=True)
            >>> config.is_metadata_enabled()
            True
        """
        return self.metadata_enabled

    def get_metadata_dir(self, repo_root: Path) -> Path:
        """Get absolute path to metadata directory.

        Args:
            repo_root: Git repository root path

        Returns:
            Absolute path to metadata directory

        Example:
            >>> config = LegesherConfig()
            >>> repo_root = Path("/home/user/project")
            >>> config.get_metadata_dir(repo_root)
            PosixPath('/home/user/project/.legesher/metadata')
        """
        return repo_root / self.metadata_directory

    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"LegesherConfig(language={self.language!r}, "
            f"python_version={self.python_version!r}, "
            f"git_canonical_language={self.git_canonical_language!r}, "
            f"git_filter_enabled={self.git_filter_enabled}, "
            f"metadata_enabled={self.metadata_enabled})"
        )


def get_language_for_git_filter() -> str:
    """Get the language to use for git filters.

    This is a convenience function that loads configuration and returns
    the language setting. Used by git filter entry points.

    Returns:
        Language code (e.g., "es", "ar")

    Example:
        >>> lang = get_language_for_git_filter()
        >>> print(lang)  # "es"
    """
    config = LegesherConfig.load()
    return config.language


def get_python_version() -> str | None:
    """Get the Python version from configuration.

    Returns:
        Python version string or None (for auto-detect)

    Example:
        >>> version = get_python_version()
        >>> print(version)  # "3.13" or None
    """
    config = LegesherConfig.load()
    return config.python_version
