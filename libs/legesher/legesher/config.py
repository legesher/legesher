"""Configuration management for Legesher.

This module handles reading and writing Legesher configuration files,
which store user preferences for language, Python version, and git settings.

Configuration files are stored in YAML format at:
    - Project config: .legesher/config.yml (see ``find_project_config``)
    - User global config: ~/.legesher/config.yml (user home directory)

Configuration precedence (highest to lowest):
    1. Project config (.legesher/config.yml)
    2. User global config (~/.legesher/config.yml)
    3. Default values

Precedence is per top-level key (``merge_config_data``): a setting the
project file does not name comes from the user file, and a section such as
``git`` is taken whole from the file that names it.

Inside a git repository the project config is the one at the repository's
root, where ``legesher init`` and ``legesher git setup`` write it and where
git runs the filter and the guard hook. Outside one it is the nearest
``.legesher/config.yml`` at or above the working directory: a project does
not have to be a git repository. A home directory kept in git is not a
project's repository, because its root holds the user config.

A file that cannot be used (unparsable YAML, YAML nested too deeply to read,
not a mapping, or a value that fails validation) is found by
``parse_config_text`` (``read_config_file`` for a file on disk). The runtime
(``LegesherConfig.load()``, so ``legesher run``, the git filter and
``legesher guard --staged``) leaves it out whole, warns, and carries on
without it; ``legesher config`` and ``legesher git setup`` refuse until it
is fixed.

``legesher guard --diff`` is stricter on purpose (``language_named_in``): it
judges a pull request by the language its base's file names whenever that
file can be parsed, even if another value in it fails validation, so an
unrelated bad value merged earlier cannot switch the check off. Only a base
file that cannot be parsed at all is judged as English, with a notice.

One schema, written by ``legesher init`` and ``legesher git setup`` alike.
``legesher init`` once wrote a different one (``languages`` as a list and no
``language``, ``git.enabled`` and no ``git.filter_enabled``); a file in that
shape is still read (``normalize_config_data``) and is never rewritten for
being old.

The ``telemetry`` section is the exception: it is consent, so it is read
from the user config only and a project config cannot change it. A
committed project file must not be able to opt every collaborator in, or
switch a user's telemetry back on.
"""

import copy
import logging
from pathlib import Path
from typing import Optional, TypeGuard

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

#: Where a config file lives under its project (or home) directory.
CONFIG_RELATIVE_PATH = Path(".legesher") / "config.yml"


def user_config_path() -> Path:
    """The user-level config file, ``~/.legesher/config.yml``."""
    return Path.home() / CONFIG_RELATIVE_PATH


def language_list(value: object) -> list[str]:
    """The language codes in a ``languages`` value, in order, without repeats.

    Anything that is not a list is no list at all, and an entry that is not
    a non-empty string is dropped: a hand-edited file must not be able to
    name ``7`` or ``""`` as a language.
    """
    if not isinstance(value, list):
        return []
    codes: list[str] = []
    for entry in value:
        if isinstance(entry, str) and entry.strip() and entry not in codes:
            codes.append(entry)
    return codes


def _is_language(value: object) -> TypeGuard[str]:
    """Whether a ``language`` value is a code: a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def normalize_config_data(data: object) -> dict:
    """A config file's YAML as the one schema every reader shares.

    Returns a copy; the input, and the file it came from, are left alone.
    Two keys are filled in when a file in the shape ``legesher init`` wrote
    before the schemas were unified lacks them:

    - ``language``, from the first entry of ``languages``. A ``language``
      the file names itself always wins.
    - ``git.filter_enabled``, from ``git.enabled``.

    A ``language`` that is not a code (a number, a list, an empty string)
    names none: it is treated as missing, filled from the list or dropped.

    Every reader of a config file goes through this (``read_config_file``,
    ``merge_config_data`` and ``legesher guard``), so they cannot disagree
    about what an old file says. Anything that is not a mapping reads as an
    empty config.
    This is the one place ``languages`` decides a language; a file with a
    ``language`` of its own never has its list consulted.
    """
    if not isinstance(data, dict):
        return {}
    result = copy.deepcopy(data)
    if not _is_language(result.get("language")):
        codes = language_list(result.get("languages"))
        if codes:
            result["language"] = codes[0]
        else:
            # A number, a list or an empty string there names no language.
            # Left in, it would hide the user config's language from one
            # reader and not from another.
            result.pop("language", None)
    git = result.get("git")
    if (
        isinstance(git, dict)
        and "filter_enabled" not in git
        and isinstance(git.get("enabled"), bool)
    ):
        git["filter_enabled"] = git["enabled"]
    return result


def merge_config_data(user_data: object, project_data: object) -> dict:
    """The user and project config files as one mapping, the project's first.

    Each file's YAML is read through ``normalize_config_data``. A top-level
    key the project file names replaces the user's, a section whole; a key
    it does not name is the user's. ``telemetry`` is the exception: it is
    the user's own section filled out with the defaults, whatever the
    project file says. No other default is filled in, so what comes back is
    what the files say.

    The loader and ``legesher config`` both merge through this, so the
    command reports what the runtime uses.
    """
    merged = normalize_config_data(user_data)
    merged.update(normalize_config_data(project_data))
    merged["telemetry"] = user_telemetry(user_data)
    return merged


def dump_config(data: dict) -> str:
    """Config data as the YAML every command writes.

    Keys in the order given, and text as itself: a value in Devanagari or
    Arabic is written in that script, not as escapes.
    """
    return yaml.safe_dump(
        data, default_flow_style=False, sort_keys=False, allow_unicode=True
    )


def is_user_config(path: Path) -> bool:
    """Whether ``path`` is the user-level config file, through any symlink."""
    try:
        return path.samefile(user_config_path())
    except (OSError, RuntimeError):
        return False


def home_directory() -> Path | None:
    """The user's home directory, resolved; None when it cannot be found."""
    try:
        return Path.home().resolve()
    except (OSError, RuntimeError):
        return None


def _repository_root(start: Path) -> Path | None:
    """The root of the git repository ``start`` is in, or None outside one.

    A home directory kept in git does not count: its root holds the user
    config, so it cannot hold a project's, and git there runs the filter
    with the user's language. ``start`` must be resolved.
    """
    home = home_directory()
    current = start
    while True:
        if (current / ".git").exists() and current != home:
            return current
        if current == current.parent:
            return None
        current = current.parent


def project_root(start: Path | None = None) -> Path:
    """The directory a project's ``.legesher/`` belongs in.

    The root of the git repository ``start`` (default: the working
    directory) is in, which is where git runs the filter and the guard
    hook; ``start`` itself outside a repository, or inside a home
    directory kept in git.
    """
    origin = (start or Path.cwd()).resolve()
    return _repository_root(origin) or origin


def home_is_the_repository(start: Path | None = None) -> bool:
    """Whether the git repository around ``start`` is the home directory's.

    Git runs the filter and the guard hook at that root, where
    ``.legesher/config.yml`` is the user config, so a project inside it
    cannot have a filter language of its own.
    """
    home = home_directory()
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".git").exists():
            return current == home
        if current == current.parent:
            return False
        current = current.parent


def find_project_config(start: Path | None = None) -> Path | None:
    """The project's ``.legesher/config.yml``, or ``None`` when it has none.

    Inside a git repository it is the file at the repository's root,
    whatever directory ``start`` (default: the working directory) is: that
    is where ``legesher init`` and ``legesher git setup`` write, and where
    git runs the filter and the guard hook, so every command reads one
    file. A repository with none at its root falls back to the nearest one
    between ``start`` and the root, which is where an earlier ``legesher
    init`` run in a subdirectory left it.

    Outside a repository, and inside a home directory kept in git, it is
    the nearest one at or above ``start``.

    It is never the user-level file, which sits at the same relative path
    under home, and the search never goes above a repository's root.
    """
    origin = (start or Path.cwd()).resolve()
    root = _repository_root(origin)
    nearest: Path | None = None
    current = origin
    while True:
        candidate = current / CONFIG_RELATIVE_PATH
        found = candidate.is_file() and not is_user_config(candidate)
        if current == root:
            return candidate if found else nearest
        if found and nearest is None:
            nearest = candidate
        if current == current.parent:
            return nearest
        current = current.parent


def shadowed_project_configs(start: Path | None = None) -> list[Path]:
    """Config files between ``start`` and its repository's root that no
    command reads, because the root has one."""
    origin = (start or Path.cwd()).resolve()
    root = _repository_root(origin)
    if root is None or not (root / CONFIG_RELATIVE_PATH).is_file():
        return []
    shadowed: list[Path] = []
    current = origin
    while current != root:
        candidate = current / CONFIG_RELATIVE_PATH
        if candidate.is_file():
            shadowed.append(candidate)
        current = current.parent
    return shadowed


def parse_config_text(text: str) -> tuple[dict | None, str | None]:
    """A config file's text as every reader uses it.

    Returns ``(data, None)`` for a usable file, read through
    ``normalize_config_data`` (an empty file is an empty mapping), or
    ``(None, problem)`` for one that is left out whole: unparsable, nested
    too deeply to read, not a mapping, or holding a value that fails
    validation. A file left out neither sets nor hides anything.
    """
    try:
        raw = yaml.safe_load(text)
    except (ValueError, yaml.YAMLError, RecursionError) as e:
        reason = " ".join(str(e).split())
        return None, f"it cannot be read as YAML ({reason})"
    if raw is None:
        return {}, None
    if not isinstance(raw, dict):
        return None, f"it is not a YAML mapping (found {type(raw).__name__})"
    try:
        data = normalize_config_data(raw)
        LegesherConfig.from_dict(data)
    except RecursionError:
        return None, "it is nested too deeply to read"
    except (TypeError, ValueError, AttributeError) as e:
        return None, str(e)
    return data, None


def language_named_in(text: str) -> tuple[str | None, str | None]:
    """The language a config file's text names, for ``legesher guard --diff``.

    Returns ``(language, None)``, read as every other reader reads it (so
    the shape an earlier ``legesher init`` wrote names the first of its
    ``languages``), or ``(None, None)`` when the file names none. Unlike
    ``parse_config_text`` this does not validate the rest of the file: a
    pull request is judged by the language its base names, and a bad value
    elsewhere in that file must not change which language that is.
    ``(None, problem)`` only when the text cannot be read as a mapping.
    """
    try:
        raw = yaml.safe_load(text)
    except (ValueError, yaml.YAMLError, RecursionError) as e:
        reason = " ".join(str(e).split())
        return None, f"it cannot be read as YAML ({reason})"
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        return None, f"it is not a YAML mapping (found {type(raw).__name__})"
    try:
        language = normalize_config_data(raw).get("language")
    except RecursionError:
        return None, "it is nested too deeply to read"
    return (language if _is_language(language) else None), None


def read_config_file(config_path: Path | None) -> tuple[dict | None, str | None]:
    """A config file on disk as every reader uses it (``parse_config_text``).

    ``(None, None)`` when there is no file.
    """
    if config_path is None or not config_path.is_file():
        return None, None
    try:
        text = config_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        reason = " ".join(str(e).split())
        return None, f"it cannot be read ({reason})"
    return parse_config_text(text)


#: Files already reported as left out in this process, so a command that
#: loads the config twice warns once.
_REPORTED: set[tuple[str, str]] = set()


def _report_left_out(config_path: Path, problem: str) -> None:
    key = (str(config_path), problem)
    if key not in _REPORTED:
        _REPORTED.add(key)
        logger.warning(f"Ignoring {config_path}: {problem}")


def _section(value: object) -> dict:
    """A config section as a mapping; anything else reads as empty."""
    return value if isinstance(value, dict) else {}


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
        languages: Every language chosen for the project, as a record (a
            list of codes, or None when the config keeps no list).
            ``language`` is the one in use; the list stands in for it only
            in a file that has no ``language`` (``normalize_config_data``).
        language_source: The config file ``load()`` took ``language`` from,
            or None when no file names one and it is the default.
        left_out: The config files ``load()`` could not use, each with the
            reason, as ``(path, problem)`` pairs.
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
        languages: list[str] | None = None,
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
            telemetry_enabled: Telemetry switch, read from the user config only
            telemetry_repo_attribution: Repository attribution opt-in, user only
            languages: Every language chosen for the project, as a record
        """
        self.language = language
        self.languages = list(languages) if languages else None
        self.language_source: Path | None = None  # set by load()
        self.left_out: list[tuple[Path, str]] = []  # set by load()
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
        data = normalize_config_data(data)
        git_config = _section(data.get("git"))
        runtime_config = _section(data.get("runtime"))
        metadata_config = _section(data.get("metadata"))
        telemetry_config = telemetry_section(data.get("telemetry"))

        # A language is a code. Anything else a file holds there (a
        # number, a list) names none, and the default stands.
        language = data.get("language")
        if not _is_language(language):
            language = "en"

        config = cls(
            language=language,
            languages=language_list(data.get("languages")),
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
        result: dict = {"language": self.language}
        # The record of every language chosen sits beside the one in use.
        if self.languages:
            result["languages"] = list(self.languages)
        result.update(
            {
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
        )

        # Add runtime config if cache_size is set
        if hasattr(self, "runtime_cache_size") and self.runtime_cache_size is not None:
            result["runtime"] = {"cache_size": self.runtime_cache_size}

        return result

    def file_dict(self) -> dict:
        """``to_dict()`` as it is written to a file: no per-user section.

        Telemetry is consent, so no command writes it out from here; a user
        sets it with ``legesher config set --global``.
        """
        data = self.to_dict()
        for section in USER_ONLY_SECTIONS:
            data.pop(section, None)
        return data

    @classmethod
    def load_project_config(
        cls, repo_root: Path | None = None
    ) -> tuple[Optional["LegesherConfig"], bool]:
        """Load project-level configuration from .legesher/config.yml.

        Args:
            repo_root: The directory that holds ``.legesher/`` (default: the
                project's own file, found by ``find_project_config``)

        Returns:
            Tuple of (LegesherConfig instance or None, file_exists bool)
            If file doesn't exist, returns (None, False)

        Example:
            >>> config, exists = LegesherConfig.load_project_config()
            >>> if exists:
            ...     print(config.language)
        """
        if repo_root is None:
            config_path = find_project_config()
            if config_path is None:
                logger.debug("No project config found from the cwd")
                return (None, False)
        else:
            config_path = repo_root / CONFIG_RELATIVE_PATH

        data, problem = read_config_file(config_path)
        if problem is not None:
            _report_left_out(config_path, problem)
        if data is None:
            logger.debug(f"No usable project config at {config_path}")
            return (None, False)
        logger.info(f"Loaded project config from {config_path}")
        return (cls.from_dict(data), True)

    @classmethod
    def load_user_config(cls) -> tuple[Optional["LegesherConfig"], bool]:
        """Load user-level configuration from ~/.legesher/config.yml.

        Returns:
            Tuple of (LegesherConfig instance or None, file_exists bool)
            If file doesn't exist, returns (None, False)

        Example:
            >>> config, exists = LegesherConfig.load_user_config()
        """
        config_path = user_config_path()
        data, problem = read_config_file(config_path)
        if problem is not None:
            _report_left_out(config_path, problem)
        if data is None:
            logger.debug(f"No usable user config at {config_path}")
            return (None, False)
        logger.info(f"Loaded user config from {config_path}")
        return (cls.from_dict(data), True)

    @classmethod
    def load(cls, repo_root: Path | None = None) -> "LegesherConfig":
        """Load configuration with precedence: project > user > defaults.

        This method loads configuration from both project and user config files,
        with project config taking precedence over user config, except for
        the ``telemetry`` section, which comes from the user config only.
        Precedence is per top-level key (``merge_config_data``), the rule
        ``legesher config`` reports by. ``language_source`` on the result is
        the file the language came from.

        Args:
            repo_root: The directory that holds the project's ``.legesher/``
                (default: found from the working directory)

        Returns:
            LegesherConfig instance with merged configuration

        Example:
            >>> config = LegesherConfig.load()  # Load with precedence
        """
        user_path = user_config_path()
        try:
            if repo_root is None:
                project_path = find_project_config()
            else:
                project_path = repo_root / CONFIG_RELATIVE_PATH
        except (OSError, RuntimeError) as e:
            logger.debug(f"Could not look for a project config: {e}")
            project_path = None

        user_data, user_problem = read_config_file(user_path)
        project_data, project_problem = read_config_file(project_path)
        left_out = [
            (path, problem)
            for path, problem in (
                (project_path, project_problem),
                (user_path, user_problem),
            )
            if path is not None and problem is not None
        ]
        for left_path, problem in left_out:
            _report_left_out(left_path, problem)

        # Defaults, then what the files say, the project's settings first.
        merged_data = copy.deepcopy(DEFAULT_CONFIG)
        merged_data.update(merge_config_data(user_data, project_data))

        # Telemetry is consent: the user's own section, never the project's,
        # and read from the user file as written, so a user file that is
        # unusable for another reason still carries the user's choice.
        merged_data["telemetry"] = user_telemetry(cls._read_user_yaml())

        config = cls.from_dict(merged_data)
        config.left_out = left_out
        sources = ((project_path, project_data), (user_path, user_data))
        for source, data in sources:
            if (
                source is not None
                and data is not None
                and _is_language(data.get("language"))
            ):
                config.language_source = source
                break
        return config

    @staticmethod
    def _read_yaml(config_path: Path) -> object:
        """A config file's raw YAML, or ``None`` if it cannot be read."""
        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (OSError, ValueError, yaml.YAMLError, RecursionError) as e:
            logger.debug(f"Could not read {config_path}: {e}")
            return None

    @classmethod
    def _read_user_yaml(cls) -> object:
        """The user config file's raw YAML, or ``None`` if it cannot be read."""
        return cls._read_yaml(user_config_path())

    @classmethod
    def _write_config(cls, config_path: Path, data: dict) -> None:
        """Write ``data`` to ``config_path``, keeping what else the file holds.

        Saving sets the keys this class owns and leaves every other key as
        it was: a section someone added by hand, or the ones an older
        ``legesher init`` wrote, are theirs. A mapping is merged key by key,
        so ``git.enabled`` in an old file survives ``git.filter_enabled``
        being written beside it.
        """
        existing = cls._read_yaml(config_path)
        merged = existing if isinstance(existing, dict) else {}
        for key, value in data.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        # LF on every platform, so the file is the same bytes everywhere.
        with open(config_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dump_config(merged))

    def save_project_config(self, repo_root: Path | None = None) -> Path:
        """Save configuration to project .legesher/config.yml.

        Keys the file already holds that this class does not own are kept.

        Args:
            repo_root: The directory to write ``.legesher/`` in (default:
                the git repository root)

        Returns:
            Path to saved config file

        Raises:
            ValueError: If not in a git repository, or if the file would be
                the user config (a home directory kept in git)

        Example:
            >>> config = LegesherConfig(language="es")
            >>> config_path = config.save_project_config()
        """
        if repo_root is None:
            repo_root = self._find_repo_root()

        config_path = repo_root / CONFIG_RELATIVE_PATH
        if is_user_config(config_path) or repo_root.resolve() == home_directory():
            raise ValueError(
                f"{config_path} is the user config, not a project's; "
                "save it with save_user_config()"
            )

        # Create .legesher directory if it doesn't exist
        config_path.parent.mkdir(exist_ok=True)

        self._write_config(config_path, self.file_dict())

        logger.info(f"Saved project config to {config_path}")
        return config_path

    def save_user_config(self) -> Path:
        """Save configuration to user ~/.legesher/config.yml.

        Keys the file already holds that this class does not own are kept,
        and so is its ``telemetry`` section: this method rewrites settings
        such as the language, and must not reset a consent choice made with
        ``legesher config set --global``.

        Returns:
            Path to saved config file

        Example:
            >>> config = LegesherConfig(language="es")
            >>> config_path = config.save_user_config()
        """
        # Create ~/.legesher directory if it doesn't exist
        config_path = user_config_path()
        config_path.parent.mkdir(exist_ok=True)

        # The file's own telemetry section is one of the keys left as it is.
        self._write_config(config_path, self.file_dict())

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
