"""Configuration management commands for Legesher.

This module provides CLI commands for viewing and modifying Legesher
project configuration stored in .legesher/config.yml.

Commands:
    legesher config list: Display all configuration values
    legesher config get <key>: Get a specific configuration value
    legesher config set <key> <value>: Set a configuration value
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


def _load_config() -> tuple[dict, Path]:
    """Load config file and return data + path."""
    config_path = _find_config_path()
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data, config_path


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

    Configuration is stored in .legesher/config.yml and can be
    viewed or modified using these subcommands.

    \b
    Examples:
        $ legesher config list
        $ legesher config get git.enabled
        $ legesher config set translation.default_target ar
    """
    pass


@config.command(name="list")
def config_list():
    """Display all configuration values."""
    data, config_path = _load_config()
    click.echo(click.style(f"Configuration ({config_path}):\n", bold=True))
    for line in _format_value(data):
        click.echo(f"  {line}")


@config.command(name="get")
@click.argument("key")
def config_get(key: str):
    """Get a specific configuration value.

    KEY is a dotted path like 'git.enabled' or 'translation.default_target'.
    """
    data, _path = _load_config()
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
def config_set(key: str, value: str):
    """Set a configuration value.

    KEY is a dotted path like 'git.enabled' or 'translation.default_target'.
    VALUE is the new value (booleans: true/false, numbers auto-detected).
    """
    data, config_path = _load_config()
    _set_nested(data, key, value)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    click.echo(f"Set {key} = {_coerce_value(value)}")


__all__ = ["config"]
