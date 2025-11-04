"""CLI entry point for legesher-filter command.

This module provides the legesher-filter command that git calls during
clean and smudge filter operations. This is a separate entry point from
the main 'legesher' CLI to keep git filter operations lightweight.

Git calls this command like:
    cat file.py | legesher-filter --clean > .git/objects/...
    cat .git/objects/... | legesher-filter --smudge > file.py

The filter reads from stdin and writes to stdout, following git's filter protocol.
"""

import logging
import sys

import click

from legesher_core.git_filter import GitFilter

# Configure logger
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors by default
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # Log to .legesher/filter.log if it exists, otherwise stderr
        logging.StreamHandler(sys.stderr)
    ],
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--clean",
    "mode",
    flag_value="clean",
    help="Clean filter: translate local language → canonical English (for git add)",
)
@click.option(
    "--smudge",
    "mode",
    flag_value="smudge",
    help="Smudge filter: translate canonical English → local language (for git checkout)",
)
@click.option(
    "--language",
    "-l",
    help="Language code (default: read from config)",
)
@click.option(
    "--python-version",
    help="Python version (default: auto-detect)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    mode: str,
    language: str | None,
    python_version: str | None,
    verbose: bool,
):
    """Legesher git filter for multilingual code translation.

    This command is called by git during clean (add) and smudge (checkout)
    operations to transparently translate code between languages.

    \b
    Git configuration:
        [filter "legesher"]
            clean = legesher-filter --clean
            smudge = legesher-filter --smudge

    \b
    Examples:
        # Clean filter (called by git add)
        $ cat file.py | legesher-filter --clean

        # Smudge filter (called by git checkout)
        $ cat file.py | legesher-filter --smudge

        # Override language
        $ cat file.py | legesher-filter --clean --language es
    """
    # Enable verbose logging if requested
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate mode is specified
    if not mode:
        click.echo(
            "Error: Must specify either --clean or --smudge mode",
            err=True,
        )
        sys.exit(1)

    try:
        # Get language from config if not specified
        if language is None:
            language = _get_language_from_config()

        logger.debug(f"Filter mode: {mode}, language: {language}")

        # Create git filter
        git_filter = GitFilter(
            language=language,
            python_version=python_version,
        )

        # Run appropriate filter
        if mode == "clean":
            exit_code = git_filter.clean(sys.stdin, sys.stdout)
        elif mode == "smudge":
            exit_code = git_filter.smudge(sys.stdin, sys.stdout)
        else:
            click.echo(f"Error: Unknown mode '{mode}'", err=True)
            sys.exit(1)

        sys.exit(exit_code)

    except Exception as e:
        # Log error but don't break git - pass through unchanged
        logger.error(f"Filter error: {e}", exc_info=True)

        # Pass through input unchanged
        try:
            content = sys.stdin.read()
            sys.stdout.write(content)
        except Exception:
            pass

        # Always return success to not break git
        sys.exit(0)


def _get_language_from_config() -> str:
    """Get language setting from configuration.

    Returns:
        Language code from config

    Raises:
        ValueError: If no configuration found
    """
    try:
        # Import here to avoid circular dependency
        from legesher.config import LegesherConfig

        config = LegesherConfig.load()
        return config.language

    except Exception as e:
        logger.error(f"Could not load config: {e}")
        # Default to English if no config found
        logger.warning("Defaulting to English (en)")
        return "en"


if __name__ == "__main__":
    main()
