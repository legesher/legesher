"""CLI entry point for Legesher Language Server."""

import argparse
import logging
import sys

from .config import LanguageServerConfig
from .server import create_server


def setup_logging(log_level: str) -> None:
    """Configure logging for the language server.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr)  # Log to stderr, LSP uses stdio
        ],
    )


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
        config.target_language = args.target_lang
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
    setup_logging(config.log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting Legesher Language Server v0.1.0")
    logger.info(f"Source language: {config.source_language}")
    logger.info(f"Target language: {config.target_language}")
    logger.info(f"Python version: {config.detect_python_version()}")

    # Create and start server
    try:
        server = create_server(config)
        server.start_io()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
