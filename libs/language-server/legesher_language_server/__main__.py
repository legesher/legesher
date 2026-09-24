"""CLI entry point for Legesher Language Server."""

import argparse
import logging
import sys

from .config import LanguageServerConfig
from .logging_setup import LspLogHandler, configure_logging
from .server import create_server


def setup_logging(log_level: str) -> LspLogHandler:
    """Configure logging for the language server.

    Logs go to the client through ``window/logMessage`` with the level they
    were written at, and to stderr only when no connection can carry them.
    Sending them to stdout is not an option, because under stdio transport
    that is the JSON-RPC channel itself, and sending them all to stderr is what
    made a healthy startup look like forty errors (CORE-1979).

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        The installed handler, which the server is bound to once it exists.
    """
    return configure_logging(log_level)


def main() -> None:
    """Main entry point for language server CLI."""
    parser = argparse.ArgumentParser(
        description="Legesher Language Server - LSP for multilingual Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with Spanish target language
  legesher-lsp --target-lang es

  # Start server with French, Python 3.11
  legesher-lsp --target-lang fr --python-version 3.11

  # Start server with debug logging
  legesher-lsp --target-lang es --log-level DEBUG

Environment Variables:
  LEGESHER_SOURCE_LANG      Source code language (default: en)
  LEGESHER_TARGET_LANG      Target display language (default: es)
  LEGESHER_PYTHON_VERSION   Python version (auto-detected if not set)
  LEGESHER_LOG_LEVEL        Logging level (default: INFO)
        """,
    )

    parser.add_argument(
        "--source-lang", default=None, help="Source code language (ISO 639-1 code, default: en)"
    )
    parser.add_argument(
        "--target-lang", default=None, help="Target display language (ISO 639-1 code, default: es)"
    )
    parser.add_argument(
        "--python-version",
        default=None,
        help="Python version (e.g., '3.10', '3.11'). Auto-detected if not specified.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio for LSP communication (default mode for IDE integration)",
    )
    parser.add_argument("--version", action="version", version="legesher-lsp 0.1.0")

    args = parser.parse_args()

    # Load config from environment first
    config = LanguageServerConfig.from_env()

    # Override with CLI arguments if provided
    if args.source_lang:
        config.source_language = args.source_lang
    if args.target_lang:
        # Seeds file_language and working_language too: the flag predates the
        # role split and stands for both (CORE-1760).
        config.apply_legacy_target_language(args.target_lang)
    if args.python_version:
        config.python_version = args.python_version
    if args.log_level:
        config.log_level = args.log_level

    # Validate language codes
    if not config.validate_languages():
        print(
            f"Error: Invalid language codes. "
            f"Source: '{config.source_language}', Target: '{config.target_language}'. "
            f"Must be 2-letter ISO 639-1 codes.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Setup logging
    handler = setup_logging(config.log_level)

    # Named rather than ``__name__``: launched as ``python -m`` this module is
    # ``__main__``, which sits outside the package logger the trace setting
    # raises and lands in the output channel under a name that says nothing.
    logger = logging.getLogger("legesher_language_server.__main__")
    logger.info("Starting Legesher Language Server v0.1.0")
    # Labelled "startup" on purpose. These are the languages the process was
    # launched with, and a client's initialize options can still replace them;
    # the server then reports what it resolved. Two unlabelled reports are what
    # left a log reader guessing which language was actually in effect.
    logger.info(
        f"Startup configuration: source={config.source_language}, "
        f"target={config.target_language}, python={config.detect_python_version()}"
    )

    # Create and start server
    try:
        server = create_server(config)
        # Nothing logged up to here could have reached the client: the
        # transport does not exist until start_io. Binding is what lets those
        # held records be replayed with their real level once it does.
        handler.bind(server)
        server.start_io()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
