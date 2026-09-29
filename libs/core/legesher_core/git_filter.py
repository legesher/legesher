"""Git clean filter that keeps each block's keywords in its stored form.

The stored form of a file is its author's language, not English (CORE-1841).
``legesher git setup`` configures the clean filter only:

    Clean (git add, and git status / git diff on a changed file): a stray
    keyword is rewritten to the language its block is stored in. Nothing else
    changes, and the filter never fails.

Smudge is off by default, because rendered views are never files. The
keyword-only smudge is an opt-in for terminal editors: it renders an English
block's hard keywords in the reader's language from open pack terms, never
builtins or library vocabulary, and only when cleaning the rendering gives
back exactly what git stores.

The filter never refuses. Git treats a filter that fails as a passthrough and
stores the file unchanged, so refusal lives in ``legesher guard``
(:mod:`legesher_core.guard`), run by the pre-commit hook. The pull-request
check (CORE-1323) is to run the same checks on every commit.
"""

import logging
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TextIO

from .stored_form import clean_text, keyword_table, smudge_text
from .types import HistoryEntry

if TYPE_CHECKING:
    from .metadata import MetadataManager

logger = logging.getLogger(__name__)

#: Seconds a stored-version lookup may take before the filter gives up on it.
_GIT_TIMEOUT = 5


def read_stored_blob(
    path: str, cwd: str | os.PathLike[str] | None = None
) -> str | None:
    """Return the version git stores for ``path``, or ``None``.

    The committed version (``HEAD``) first, then the index entry (stage 0)
    for a path that was never committed. A staged blob can be a half-edited,
    mixed version, so it never outranks the commit: the language a block is
    stored in stays the same between ``git add`` and ``git status``. Git runs
    a filter from the top of the work tree and names ``path`` relative to it,
    so ``cwd`` defaults to the current directory. ``None`` for an untracked
    path, content that is not UTF-8, or any failure to run git: the caller
    then decides from the text itself.
    """
    for revision in (f"HEAD:{path}", f":0:{path}"):
        try:
            result = subprocess.run(
                ["git", "cat-file", "blob", revision],
                cwd=cwd,
                capture_output=True,
                timeout=_GIT_TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.debug(f"stored version of {path}: git unavailable: {exc}")
            return None
        if result.returncode == 0:
            try:
                return result.stdout.decode("utf-8")
            except UnicodeDecodeError:
                return None
    return None


class GitFilter:
    """The Legesher git filter for one machine's language.

    Attributes:
        language: The language this machine writes in (e.g. ``"es"``).
        python_version: The pack version keywords are read from.
        stored_reader: ``path -> stored text or None``; defaults to
            :func:`read_stored_blob`.
        metadata_manager: Optional manager that records filter history.
        file_path: The file being filtered, for metadata.

    Example:
        >>> git_filter = GitFilter(language="es")
        >>> git_filter.clean_text("definir f():\\n    return 1\\n")
        'definir f():\\n    devolver 1\\n'
    """

    def __init__(
        self,
        language: str,
        python_version: str | None = None,
        *,
        stored_reader: Callable[[str], str | None] | None = None,
        metadata_manager: Optional["MetadataManager"] = None,
        file_path: str | None = None,
    ) -> None:
        """Load the language's keywords.

        Raises:
            ValueError: If the language pack cannot be loaded.
        """
        self.language = language
        self.python_version = python_version or self._detect_python_version()
        self.stored_reader = stored_reader or read_stored_blob
        self.metadata_manager = metadata_manager
        self.file_path = file_path
        try:
            self.keywords = keyword_table(language, self.python_version)
        except Exception as e:
            logger.error(f"Failed to initialize GitFilter: {e}")
            raise ValueError(f"Could not load language pack for '{language}': {e}")

    def _stored(self, path: str | None) -> str | None:
        if path is None:
            return None
        try:
            return self.stored_reader(path)
        except Exception as exc:
            logger.warning(f"Clean filter: no stored version for {path}: {exc}")
            return None

    def clean_text(self, text: str, path: str | None = None) -> str:
        """Normalize stray keywords; return ``text`` unchanged on any error."""
        try:
            return clean_text(text, local=self.keywords, stored=self._stored(path))
        except Exception as exc:
            logger.error(f"Clean filter: passing through: {exc}", exc_info=True)
            return text

    def smudge_text(self, text: str) -> str:
        """Render an English block's keywords; ``text`` unchanged on any error."""
        try:
            return smudge_text(text, reader=self.keywords)
        except Exception as exc:
            logger.error(f"Smudge filter: passing through: {exc}", exc_info=True)
            return text

    def clean(
        self,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
        path: str | None = None,
    ) -> int:
        """Clean one file from ``input_stream`` to ``output_stream``.

        Returns:
            0, always. A non-zero status would make git store the file
            unchanged, which is no different from a passthrough.
        """
        text = input_stream.read()
        output_stream.write(self.clean_text(text, path))
        self._record_metadata_history("clean", self.language, self.language)
        return 0

    def smudge(
        self,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
        path: str | None = None,
    ) -> int:
        """Keyword-only smudge of one file. Returns 0, always."""
        text = input_stream.read()
        output_stream.write(self.smudge_text(text))
        self._record_metadata_history("smudge", "en", self.language)
        return 0

    def _record_metadata_history(
        self, action: str, from_language: str, to_language: str
    ) -> None:
        """Record a filter run in metadata history; never raises."""
        if not self.metadata_manager or not self.file_path:
            logger.debug("Skipping metadata recording: manager or file_path not set")
            return

        try:
            entry: HistoryEntry = {
                "action": action,
                "from_language": from_language,
                "to_language": to_language,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "commit_sha": self._get_current_commit_sha(),
            }
            self.metadata_manager.add_history_entry(Path(self.file_path), entry)
        except Exception as e:
            logger.warning(
                f"Failed to record metadata history for {self.file_path}: {e}",
                exc_info=True,
            )

    def _get_current_commit_sha(self) -> str | None:
        """Current commit SHA, or ``None`` when unavailable."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception as e:
            logger.debug(f"Error getting git commit SHA: {e}")
            return None

    def _detect_python_version(self) -> str:
        return f"{sys.version_info.major}.{sys.version_info.minor}"


def clean_filter(language: str, python_version: str | None = None) -> int:
    """Run the clean filter on stdin to stdout. Returns 0."""
    git_filter = GitFilter(language=language, python_version=python_version)
    return git_filter.clean()


def smudge_filter(language: str, python_version: str | None = None) -> int:
    """Run the keyword-only smudge on stdin to stdout. Returns 0."""
    git_filter = GitFilter(language=language, python_version=python_version)
    return git_filter.smudge()
