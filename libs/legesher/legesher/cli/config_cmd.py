"""Configuration management commands for Legesher.

This module provides CLI commands for viewing and modifying Legesher
configuration. Values live in the project config (.legesher/config.yml)
or the user-level config (~/.legesher/config.yml); project values take
precedence when both define a key.

Commands:
    legesher config list: Display all configuration values
    legesher config get <key>: Get a specific configuration value
    legesher config set <key> <value>: Set a configuration value
    legesher config set --global <key> <value>: Set a user-level value
"""

import sys
from pathlib import Path

import click
import yaml


def _find_config_path() -> Path:
    """Find .legesher/config.yml in the current or parent directories.

    Returns:
        Path to config.yml

    Raises:
        click.ClickException: If no config file found
    """
    current = Path.cwd().resolve()
    while True:
        config_path = current / ".legesher" / "config.yml"
        if config_path.exists():
            return config_path
        if current == current.parent:
            break
        current = current.parent

    raise click.ClickException(
        "No .legesher/config.yml found. Run 'legesher init' first."
    )


def _user_config_path() -> Path:
    """Return the user-level config path (~/.legesher/config.yml)."""
    return Path.home() / ".legesher" / "config.yml"


def _load_yaml_mapping(config_path: Path) -> dict:
    """Load a config file, requiring the YAML root to be a mapping.

    An empty file loads as an empty dict.

    Raises:
        click.ClickException: If the YAML root is not a mapping.
    """
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise click.ClickException(
            f"Config file {config_path} is not a YAML mapping "
            f"(found {type(data).__name__}). Fix or remove the file."
        )
    return data


def _load_config() -> tuple[dict, Path]:
    """Load config file and return data + path."""
    config_path = _find_config_path()
    return _load_yaml_mapping(config_path), config_path


def _load_merged_config() -> tuple[dict, list[Path]]:
    """Load user-level and project config merged (project takes precedence).

    Merging is a top-level update, matching LegesherConfig.load(): a
    project-level section replaces the user-level section of the same
    name entirely, so these commands report what the runtime actually
    uses.

    Returns:
        Tuple of (merged data, list of contributing config paths)

    Raises:
        click.ClickException: If neither config file exists
    """
    data: dict = {}
    paths: list[Path] = []

    user_path = _user_config_path()
    if user_path.exists():
        data = _load_yaml_mapping(user_path)
        paths.append(user_path)

    try:
        project_data, project_path = _load_config()
    except click.ClickException:
        if not paths:
            raise
    else:
        data = dict(data)
        data.update(project_data)
        paths.append(project_path)

    return data, paths


_MISSING = object()


def _get_nested(data: dict, dotted_key: str, default=_MISSING):
    """Get a value from a nested dict using dotted key notation.

    Returns _MISSING sentinel if key is not found (to distinguish from None values).
    """
    keys = dotted_key.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _validate_key(dotted_key: str) -> None:
    """Validate a dotted config key.

    Raises:
        click.ClickException: If the key is empty or contains invalid characters.
    """
    if not dotted_key or not dotted_key.strip():
        raise click.ClickException("Key cannot be empty.")
    for part in dotted_key.split("."):
        if not part:
            raise click.ClickException(
                f"Invalid key '{dotted_key}': contains empty segment."
            )


def _set_nested(data: dict, dotted_key: str, value: str) -> None:
    """Set a value in a nested dict using dotted key notation.

    Automatically coerces value strings to appropriate types.
    """
    _validate_key(dotted_key)
    keys = dotted_key.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    # Coerce value to appropriate type
    current[keys[-1]] = _coerce_value(value)


def _coerce_value(value: str):
    """Coerce a string value to its appropriate Python type.

    Only booleans, null/none, and pure integer strings are coerced.
    Float-like strings (e.g., "3.10") are kept as strings to avoid
    corruption of version numbers.
    """
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "none"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    return value


def _format_value(data, prefix: str = "") -> list[str]:
    """Flatten a nested dict into dotted key-value lines."""
    lines = []
    if isinstance(data, dict):
        for key, val in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            lines.extend(_format_value(val, full_key))
    elif isinstance(data, list):
        lines.append(f"{prefix} = {', '.join(str(v) for v in data)}")
    elif isinstance(data, bool):
        lines.append(f"{prefix} = {str(data).lower()}")
    elif data is None:
        lines.append(f"{prefix} = null")
    else:
        lines.append(f"{prefix} = {data}")
    return lines


@click.group(name="config")
def config():
    """View and modify Legesher project configuration.

    Configuration is stored in the project's .legesher/config.yml or
    the user-level ~/.legesher/config.yml and can be viewed or
    modified using these subcommands.

    \b
    Examples:
        $ legesher config list
        $ legesher config get git.enabled
        $ legesher config set translation.default_target ar
        $ legesher config set --global language es
    """
    pass


@config.command(name="list")
def config_list():
    """Display all configuration values (user-level merged with project)."""
    data, paths = _load_merged_config()
    sources = ", ".join(str(path) for path in paths)
    click.echo(click.style(f"Configuration ({sources}):\n", bold=True))
    for line in _format_value(data):
        click.echo(f"  {line}")


@config.command(name="get")
@click.argument("key")
def config_get(key: str):
    """Get a specific configuration value.

    KEY is a dotted path like 'git.enabled' or 'translation.default_target'.
    Values are read from the user-level config merged with the project
    config (project takes precedence).
    """
    data, _paths = _load_merged_config()
    value = _get_nested(data, key)
    if value is _MISSING:
        click.echo(click.style(f"Key '{key}' not found.", fg="yellow"))
        sys.exit(1)
    if value is None:
        click.echo("null")
        return
    if isinstance(value, dict):
        for line in _format_value(value, key):
            click.echo(line)
    elif isinstance(value, list):
        click.echo(f"{', '.join(str(v) for v in value)}")
    elif isinstance(value, bool):
        click.echo(str(value).lower())
    else:
        click.echo(value)


@config.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option(
    "--global",
    "use_global",
    is_flag=True,
    help="Set in user-level config (~/.legesher/config.yml)",
)
def config_set(key: str, value: str, use_global: bool):
    """Set a configuration value.

    KEY is a dotted path like 'git.enabled' or 'translation.default_target'.
    VALUE is the new value (booleans: true/false, numbers auto-detected).
    With --global, the value is written to the user-level config
    (~/.legesher/config.yml) instead of the project config.
    """
    _validate_key(key)
    if use_global:
        config_path = _user_config_path()
        data = _load_yaml_mapping(config_path) if config_path.exists() else {}
        config_path.parent.mkdir(exist_ok=True)
    else:
        data, config_path = _load_config()
    _set_nested(data, key, value)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    click.echo(f"Set {key} = {_coerce_value(value)} in {config_path}")


__all__ = ["config"]
