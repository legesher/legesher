"""Main CLI entry point for Legesher.

This module defines the main Click group and registers all CLI commands.

Example:
    $ legesher --help
    $ legesher translate input.py --from es --to en
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

import click

from legesher.cli import git as git_module
from legesher.cli import init as init_module
from legesher.cli import metadata as metadata_module
from legesher.cli import run as run_module
from legesher.cli import translate


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
        # Translate a single file
        $ legesher translate input.py --from es --to en --output output.py

        # Translate from stdin to stdout
        $ cat input.py | legesher translate --from es --to en

        # Translate an entire directory
        $ legesher translate src/ --from es --to en --output translated/

    For more information, visit: https://legesher.io
    """
    pass


# Register commands
cli.add_command(init_module.init)
cli.add_command(translate.translate)
cli.add_command(run_module.run)
cli.add_command(git_module.git)
cli.add_command(metadata_module.metadata)


if __name__ == "__main__":
    cli()
