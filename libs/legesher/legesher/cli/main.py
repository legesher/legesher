"""Main CLI entry point for Legesher.

This module defines the main Click group and registers all CLI commands.

Example:
    $ legesher --help
    $ legesher translate input.py --from es --to en
"""

import click

from legesher.cli import translate


@click.group()
@click.version_option(version="0.0.1", prog_name="legesher")
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
cli.add_command(translate.translate)


if __name__ == "__main__":
    cli()
