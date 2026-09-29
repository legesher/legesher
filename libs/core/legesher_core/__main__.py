"""CLI entry point for the ``legesher-filter`` command.

Git runs this command as the clean filter (and, when the keyword-only smudge
is opted into, as the smudge filter). A separate entry point from the main
``legesher`` CLI keeps filter start-up light.

``legesher git setup`` configures the long-running process, which git
prefers, and the single-file command as the fallback for git before 2.11:

    [filter "legesher"]
        process = sh <git dir>/legesher/filter-process
        clean = legesher-filter --clean --path %f
        required = false

The filter reads bytes on stdin and writes bytes on stdout. Content that is
not UTF-8 is passed through unchanged, and the exit status is always 0: git
treats a failing filter as a passthrough anyway, and refusal is the job of
``legesher guard``.
"""

import logging
import sys

import click

from legesher_core.git_filter import GitFilter

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--clean",
    "mode",
    flag_value="clean",
    help="Clean filter: normalize stray keywords to each block's stored form",
)
@click.option(
    "--smudge",
    "mode",
    flag_value="smudge",
    help="Keyword-only smudge: render an English block's keywords (opt-in)",
)
@click.option(
    "--process",
    "mode",
    flag_value="process",
    help="Serve git's long-running filter protocol for a whole git command",
)
@click.option(
    "--handshake-done",
    is_flag=True,
    hidden=True,
    help="With --process: the launcher has already answered git's handshake",
)
@click.option(
    "--keyword-smudge",
    is_flag=True,
    help="With --process: also offer the keyword-only smudge (the setup opt-in)",
)
@click.option(
    "--path",
    "path",
    default=None,
    help="Path of the file being filtered, relative to the repository (git's %f)",
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
    handshake_done: bool,
    keyword_smudge: bool,
    path: str | None,
    language: str | None,
    python_version: str | None,
    verbose: bool,
):
    """Legesher git filter: keep each block's keywords in its stored form.

    \b
    Examples:
        $ cat file.py | legesher-filter --clean --path file.py
        $ cat file.py | legesher-filter --clean --language es
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not mode:
        click.echo("Error: Must specify --clean, --smudge or --process", err=True)
        sys.exit(1)

    if mode == "process":
        sys.exit(
            _serve_process(language, python_version, keyword_smudge, not handshake_done)
        )

    data = sys.stdin.buffer.read()
    sys.stdout.buffer.write(_filter(data, mode, path, language, python_version))
    sys.stdout.buffer.flush()
    sys.exit(0)


def _filter(
    data: bytes,
    mode: str,
    path: str | None,
    language: str | None,
    python_version: str | None,
) -> bytes:
    """Filter one blob; any failure returns ``data`` unchanged."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    try:
        git_filter = GitFilter(
            language=language or _get_language_from_config(),
            python_version=python_version,
        )
    except Exception as e:
        logger.error(f"Filter error: {e}")
        return data
    if mode == "clean":
        result = git_filter.clean_text(text, path)
    else:
        result = git_filter.smudge_text(text)
    return result.encode("utf-8")


def _serve_process(
    language: str | None,
    python_version: str | None,
    keyword_smudge: bool,
    handshake: bool = True,
) -> int:
    """Serve git's long-running filter protocol until git closes stdin."""
    from legesher_core.filter_process import (
        BatchStoredReader,
        FilterProcess,
        ProtocolError,
    )

    reader = BatchStoredReader()
    git_filter = None
    try:
        git_filter = GitFilter(
            language=language or _get_language_from_config(),
            python_version=python_version,
            stored_reader=reader,
        )
    except Exception as e:
        # The process still answers git, with an abort, so git keeps every
        # file unchanged instead of failing the command.
        logger.error(f"Filter error: {e}")
    try:
        return FilterProcess(git_filter, smudge=keyword_smudge).serve(
            sys.stdin.buffer, sys.stdout.buffer, handshake=handshake
        )
    except ProtocolError as e:
        logger.error(f"Filter protocol error: {e}")
        return 1
    finally:
        reader.close()


def _get_language_from_config() -> str:
    """The configured language, or English when there is no configuration."""
    try:
        from legesher.config import LegesherConfig

        return LegesherConfig.load().language
    except Exception as e:
        logger.error(f"Could not load config: {e}")
        logger.warning("Defaulting to English (en)")
        return "en"


if __name__ == "__main__":
    main()
