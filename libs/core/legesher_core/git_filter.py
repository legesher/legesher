"""Git clean/smudge filters for transparent multilingual code translation.

This module implements git filters that enable developers to work in their native
language while storing code in canonical English in the git repository.

Git Filter Flow:
    1. Clean filter (git add): Local language → English (stored in git)
    2. Smudge filter (git checkout): English → Local language (working directory)

The filters read from stdin and write to stdout, following git's filter protocol.
Error handling is designed to never break git operations - if translation fails,
the code passes through unchanged.
"""

import logging
import sys
from typing import Optional, TextIO

from .exceptions import InvalidCodeError
from .transformer import TokenTranslator

# Configure logger
logger = logging.getLogger(__name__)


class GitFilter:
    """Git clean/smudge filter for multilingual Python code.

    This class implements git filters that transparently translate Python code
    between natural languages during git operations:

    - Clean filter (git add): Translates from developer's language to English
    - Smudge filter (git checkout): Translates from English to developer's language

    The filters are designed with safety as the primary concern:
    - Never break git operations (always return success)
    - Pass through unchanged code on translation errors
    - Log errors for debugging without blocking operations

    Attributes:
        language: Target natural language code (e.g., "es", "ar")
        python_version: Target Python version (e.g., "3.13")
        translator_to_en: Translator for local language → English
        translator_from_en: Translator for English → local language

    Example:
        >>> # Create filter for Spanish
        >>> filter = GitFilter(language="es")
        >>>
        >>> # Clean: Spanish → English (for git storage)
        >>> exit_code = filter.clean(sys.stdin, sys.stdout)
        >>>
        >>> # Smudge: English → Spanish (for working directory)
        >>> exit_code = filter.smudge(sys.stdin, sys.stdout)
    """

    def __init__(
        self,
        language: str,
        python_version: Optional[str] = None,
        canonical_language: str = "en",
    ) -> None:
        """Initialize git filter for a specific language.

        Args:
            language: Target natural language code (e.g., "es" for Spanish)
            python_version: Python version (default: auto-detect from runtime)
            canonical_language: Git storage language (default: "en")

        Raises:
            ValueError: If language pack cannot be loaded

        Example:
            >>> filter = GitFilter(language="es")  # Auto-detect Python version
            >>> filter = GitFilter(language="ar", python_version="3.13")
        """
        self.language = language
        self.canonical_language = canonical_language
        self.python_version = python_version or self._detect_python_version()

        logger.info(
            f"Initializing GitFilter: {language} ↔ {canonical_language} "
            f"(Python {self.python_version})"
        )

        # Load language pack and create bidirectional translators
        try:
            # from_language_pack("es") creates EN→ES translator
            # We need ES→EN for clean filter, so reverse it
            en_to_local = TokenTranslator.from_language_pack(
                language=language,
                python_version=self.python_version,
            )

            # Translator for local language → English (clean filter)
            self.translator_to_en = en_to_local.reverse()

            # Translator for English → local language (smudge filter)
            self.translator_from_en = en_to_local

            logger.info(
                f"GitFilter initialized successfully for {language} "
                f"({en_to_local.get_pack_info()['keyword_count']} keywords, "
                f"{en_to_local.get_pack_info()['builtin_count']} builtins)"
            )

        except Exception as e:
            logger.error(f"Failed to initialize GitFilter: {e}")
            raise ValueError(f"Could not load language pack for '{language}': {e}")

    def clean(
        self,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
    ) -> int:
        """Clean filter: Translate from local language to canonical English.

        This filter runs during 'git add' and 'git commit', translating code from
        the developer's native language to English before storing in git.

        Git flow:
            Working directory (Spanish) → [clean filter] → Git storage (English)

        Args:
            input_stream: Input stream (default: stdin, provided by git)
            output_stream: Output stream (default: stdout, consumed by git)

        Returns:
            Exit code: 0 for success (always returns 0 to not break git)

        Example:
            >>> # Git calls this like:
            >>> # cat file.py | legesher-filter --clean > .git/objects/...
            >>> filter = GitFilter(language="es")
            >>> exit_code = filter.clean()  # Reads stdin, writes stdout
        """
        try:
            # Read source code from input stream
            source_code = input_stream.read()

            # If input is empty, pass through
            if not source_code.strip():
                output_stream.write(source_code)
                return 0

            logger.debug(
                f"Clean filter: Translating {len(source_code)} bytes "
                f"from {self.language} to {self.canonical_language}"
            )

            # Translate from local language to English
            # Note: If code is already in English, translation is a no-op
            translated_code = self.translator_to_en.translate_code(
                source_code=source_code,
                source_lang=self.language,
                target_lang=self.canonical_language,
            )

            # Write translated code to output stream
            output_stream.write(translated_code)
            logger.debug("Clean filter: Translation completed successfully")

            return 0

        except InvalidCodeError as e:
            # Code has syntax errors - pass through unchanged
            # This is common during editing (incomplete code)
            logger.warning(f"Clean filter: Invalid code, passing through: {e}")
            output_stream.write(source_code if "source_code" in locals() else "")
            return 0

        except Exception as e:
            # Unexpected error - pass through unchanged to not break git
            logger.error(
                f"Clean filter: Unexpected error, passing through: {e}", exc_info=True
            )
            output_stream.write(source_code if "source_code" in locals() else "")
            return 0

    def smudge(
        self,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
    ) -> int:
        """Smudge filter: Translate from canonical English to local language.

        This filter runs during 'git checkout' and 'git pull', translating code from
        English (stored in git) to the developer's native language (working directory).

        Git flow:
            Git storage (English) → [smudge filter] → Working directory (Spanish)

        Args:
            input_stream: Input stream (default: stdin, provided by git)
            output_stream: Output stream (default: stdout, consumed by git)

        Returns:
            Exit code: 0 for success (always returns 0 to not break git)

        Example:
            >>> # Git calls this like:
            >>> # cat .git/objects/... | legesher-filter --smudge > file.py
            >>> filter = GitFilter(language="es")
            >>> exit_code = filter.smudge()  # Reads stdin, writes stdout
        """
        try:
            # Read source code from input stream
            source_code = input_stream.read()

            # If input is empty, pass through
            if not source_code.strip():
                output_stream.write(source_code)
                return 0

            logger.debug(
                f"Smudge filter: Translating {len(source_code)} bytes "
                f"from {self.canonical_language} to {self.language}"
            )

            # Translate from English to local language
            # Note: If code is already in target language, translation is a no-op
            translated_code = self.translator_from_en.translate_code(
                source_code=source_code,
                source_lang=self.canonical_language,
                target_lang=self.language,
            )

            # Write translated code to output stream
            output_stream.write(translated_code)
            logger.debug("Smudge filter: Translation completed successfully")

            return 0

        except InvalidCodeError as e:
            # Code has syntax errors - pass through unchanged
            logger.warning(f"Smudge filter: Invalid code, passing through: {e}")
            output_stream.write(source_code if "source_code" in locals() else "")
            return 0

        except Exception as e:
            # Unexpected error - pass through unchanged to not break git
            logger.error(
                f"Smudge filter: Unexpected error, passing through: {e}", exc_info=True
            )
            output_stream.write(source_code if "source_code" in locals() else "")
            return 0

    def _is_canonical_language(self, code: str) -> bool:
        """Detect if code is in canonical language (English).

        This is a simple heuristic: if we can find English keywords in the code,
        it's likely English. Not perfect, but good enough for the filter's needs.

        Args:
            code: Python source code to check

        Returns:
            True if code appears to be in English, False otherwise
        """
        # Get English keywords from the EN→local translator
        # translator_from_en goes EN→local, so its keys are English keywords
        english_keywords = set(self.translator_from_en.mapper.keyword_map.keys())

        # Check if any English keywords are present
        # This is a simple heuristic - could be improved
        for keyword in english_keywords:
            if (
                f" {keyword} " in f" {code} "
                or f"\n{keyword} " in code
                or code.startswith(f"{keyword} ")
            ):
                return True

        return False

    def _detect_python_version(self) -> str:
        """Detect Python version from runtime.

        Returns:
            Python version string (e.g., "3.13")
        """
        version_info = sys.version_info
        return f"{version_info.major}.{version_info.minor}"


def clean_filter(language: str, python_version: Optional[str] = None) -> int:
    """Clean filter entry point for git (local → canonical).

    This is a convenience function for use as a git filter command:
        git config filter.legesher.clean "legesher-filter --clean --language es"

    Args:
        language: Target language code (e.g., "es", "ar")
        python_version: Python version (default: auto-detect)

    Returns:
        Exit code: 0 for success

    Example:
        >>> # Called by git during 'git add'
        >>> exit_code = clean_filter(language="es")
    """
    filter = GitFilter(language=language, python_version=python_version)
    return filter.clean()


def smudge_filter(language: str, python_version: Optional[str] = None) -> int:
    """Smudge filter entry point for git (canonical → local).

    This is a convenience function for use as a git filter command:
        git config filter.legesher.smudge "legesher-filter --smudge --language es"

    Args:
        language: Target language code (e.g., "es", "ar")
        python_version: Python version (default: auto-detect)

    Returns:
        Exit code: 0 for success

    Example:
        >>> # Called by git during 'git checkout'
        >>> exit_code = smudge_filter(language="es")
    """
    filter = GitFilter(language=language, python_version=python_version)
    return filter.smudge()
