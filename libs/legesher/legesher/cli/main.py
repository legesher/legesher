"""Main CLI entry point for Legesher.

This module defines the main Click group and registers all CLI commands.

Example:
    $ legesher --help
    $ legesher translate input.py --from es --to en
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

import click

from legesher_i18n.console_encoding import ensure_utf8_stdio

from legesher.cli import config_cmd
from legesher.cli import git as git_module
from legesher.cli import guard as guard_module
from legesher.cli import init as init_module
from legesher.cli import metadata as metadata_module
from legesher.cli import run as run_module
from legesher.cli import translate


# Every subcommand of this group prints through `rich`, and several use box
# and status glyphs (`━`, `✗`) that a Windows ANSI code page cannot encode.
# Done once here rather than per-module so a new subcommand inherits it —
# and a tool whose entire subject is non-English text should never be the
# thing that cannot print non-English text (CORE-1927).
ensure_utf8_stdio()


def _get_legesher_version() -> str:
    """Get the installed legesher package version with fallback."""
    try:
        return get_version("legesher")
    except PackageNotFoundError:
        return "0.0.0-dev"


@click.group()
@click.version_option(version=_get_legesher_version(), prog_name="legesher")
def cli():
    """Legesher - Code in your native language.

    Legesher enables developers to write code in their native language
    by translating Python keywords and built-ins while preserving the
    semantic meaning of the code.

    \b
    Examples:
        # Translate a single file (keywords/builtins only)
        $ legesher translate input.py --from es --to en --output output.py

        # Translate from stdin to stdout
        $ cat input.py | legesher translate --from es --to en

        # Translate an entire directory
        $ legesher translate src/ --from es --to en --output translated/

        # Full LLM translation (identifiers, comments, strings)
        $ legesher translate src/ --to es --full --llm-backend anthropic

    For more information, visit: https://legesher.io
    """
    pass


# Register commands
cli.add_command(init_module.init)
cli.add_command(translate.translate)
cli.add_command(run_module.run)
cli.add_command(git_module.git)
cli.add_command(guard_module.guard)
cli.add_command(metadata_module.metadata)
cli.add_command(config_cmd.config)


if __name__ == "__main__":
    cli()
