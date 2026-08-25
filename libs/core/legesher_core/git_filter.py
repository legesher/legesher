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
import subprocess
import unicodedata
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TextIO
from collections.abc import Callable

from .exceptions import InvalidCodeError
from . import unicode_guard
from .language_interface import create_translator_from_language_pack
from .types import HistoryEntry, Translator

if TYPE_CHECKING:
    from .metadata import MetadataManager

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
        metadata_manager: Optional metadata manager for tracking translations
        file_path: Optional path to the file being filtered (for metadata)

    Example:
        >>> # Create filter for Spanish
        >>> filter = GitFilter(language="es")
        >>>
        >>> # Clean: Spanish → English (for git storage)
        >>> exit_code = filter.clean(sys.stdin, sys.stdout)
        >>>
        >>> # Smudge: English → Spanish (for working directory)
        >>> exit_code = filter.smudge(sys.stdin, sys.stdout)
        >>>
        >>> # With metadata tracking
        >>> from legesher_core.metadata import MetadataManager
        >>> manager = MetadataManager(Path("/repo"))
        >>> filter = GitFilter(language="es", metadata_manager=manager, file_path="src/main.py")
    """

    def __init__(
        self,
        language: str,
        python_version: str | None = None,
        canonical_language: str = "en",
        use_tree_sitter: bool | None = None,
        translator_factory: Callable[[str, str], Translator] | None = None,
        metadata_manager: Optional["MetadataManager"] = None,
        file_path: str | None = None,
    ) -> None:
        """Initialize git filter for a specific language.

        Args:
            language: Target natural language code (e.g., "es" for Spanish)
            python_version: Python version (default: auto-detect from runtime)
            canonical_language: Git storage language (default: "en")
            use_tree_sitter: Translator backend selection:
                - True: Use TreeSitterTranslator (4x faster, AST-based)
                - False: Use TokenTranslator (simpler, token-based)
                - None: Check LEGESHER_USE_TREE_SITTER environment variable
            translator_factory: Optional custom factory function for advanced usage.
                Should take (source_lang, target_lang) and return a Translator.
                If provided, use_tree_sitter is ignored.
            metadata_manager: Optional metadata manager for tracking translations
            file_path: Optional path to the file being filtered (for metadata tracking)

        Environment Variables:
            LEGESHER_USE_TREE_SITTER: Set to "true" to use tree-sitter backend by default

        Raises:
            ValueError: If language pack cannot be loaded

        Example:
            >>> # Default (token-based, or from environment)
            >>> filter = GitFilter(language="es")

            >>> # Explicit tree-sitter backend
            >>> filter = GitFilter(language="es", use_tree_sitter=True)

            >>> # With specific Python version
            >>> filter = GitFilter(language="ar", python_version="3.13", use_tree_sitter=True)

            >>> # With metadata tracking
            >>> from legesher_core.metadata import MetadataManager
            >>> manager = MetadataManager(Path("/repo"))
            >>> filter = GitFilter(language="es", metadata_manager=manager, file_path="src/main.py")

            >>> # Advanced: custom translator factory
            >>> def custom_factory(source_lang, target_lang):
            ...     return create_translator_from_language_pack("python", target_lang)
            >>> filter = GitFilter(language="es", translator_factory=custom_factory)
        """
        self.language = language
        self.canonical_language = canonical_language
        self.python_version = python_version or self._detect_python_version()
        self.metadata_manager = metadata_manager
        self.file_path = file_path

        backend_desc = (
            "custom factory"
            if translator_factory
            else (
                "tree-sitter"
                if use_tree_sitter
                else "token-based"
                if use_tree_sitter is False
                else "environment-configured"
            )
        )
        logger.info(
            f"Initializing GitFilter: {language} ↔ {canonical_language} "
            f"(Python {self.python_version}, backend: {backend_desc})"
        )

        # Load language pack and create bidirectional translators
        try:
            if translator_factory:
                # Custom factory provided (advanced usage)
                self.translator_from_en = translator_factory(
                    canonical_language, language
                )
                self.translator_to_en = translator_factory(language, canonical_language)
                logger.info("GitFilter initialized with custom translator factory")
            else:
                # Standard factory: load from language pack
                # from_language_pack("es") creates EN→ES translator
                # We need ES→EN for clean filter, so reverse it
                en_to_local = create_translator_from_language_pack(
                    programming_language="python",
                    natural_language=language,
                    programming_language_version=self.python_version,
                    use_tree_sitter=use_tree_sitter,  # Respects environment if None
                )

                # Translator for local language → English (clean filter)
                self.translator_to_en = en_to_local.reverse()

                # Translator for English → local language (smudge filter)
                self.translator_from_en = en_to_local

                pack_info = en_to_local.get_pack_info()
                logger.info(
                    f"GitFilter initialized successfully for {language} "
                    f"({pack_info['keyword_count']} keywords, "
                    f"{pack_info['builtin_count']} builtins)"
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

            # Strip a leading BOM before processing (canonical storage is
            # UTF-8 without BOM).
            source_code = unicode_guard.strip_bom(source_code)

            # FAIL CLOSED on Trojan Source (CVE-2021-42574). Bidi reordering
            # controls and disallowed invisibles in code are rejected before we
            # translate — never write attacker bytes into git. Legitimate
            # ZWJ/ZWNJ inside string/comment content is allowlisted.
            # Two allowlists, because the two scans ask different questions.
            # The whole-text scan may meet an invisible anywhere, so it honors
            # both what strings/comments legitimately contain and what this
            # language's orthography needs inside a name — without the second
            # half, Sinhala `විද්‍යා` and Persian `می‌رود` are refused as
            # invisible even though their policies declare the joiner.
            allowed = (
                self._collect_string_comment_format_chars(source_code)
                | self._identifier_format_allowlist()
            )
            issues = unicode_guard.scan_text(source_code, allowed_format_chars=allowed)
            # The code-position scan (CORE-1558) then re-narrows: the script
            # allowlist applies there, and the only format characters licensed
            # are the language's own — so a U+FE0F inside a comment no longer
            # licenses a U+FE0F inside a name. Strings and comments carry prose
            # in any script and are exempt; code position is the only place a
            # character becomes a runtime binding. Isolated in its own try so a
            # defect in the newest layer can never take the Trojan Source check
            # down with it.
            try:
                issues = issues + self._scan_identifier_scripts(source_code)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Clean filter: identifier scan failed: {exc}")
            issues = sorted(issues, key=lambda i: i.offset)
            blocking = [
                i
                for i in issues
                if i.kind in ("bidi", "invisible", "tatweel", "script")
            ]
            if blocking:
                first = blocking[0]
                classification = {
                    "bidi": "Trojan Source bidi reordering attack (CVE-2021-42574)",
                    "invisible": "invisible/format-character attack",
                    "tatweel": "tatweel padding character",
                    "script": "identifier character outside every supported script",
                }.get(first.kind, "disallowed Unicode control")
                sys.stderr.write(
                    "legesher: refusing to stage source containing a "
                    "disallowed Unicode control "
                    f"({first.codepoint} {first.char_name} at offset "
                    f"{first.offset}): {first.message}. Rejected as "
                    f"{classification}.\n"
                )
                return 1

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

            # Record metadata (never fail git operations due to metadata errors)
            self._record_metadata_history(
                action="clean",
                from_language=self.language,
                to_language=self.canonical_language,
            )

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

            # Record metadata (never fail git operations due to metadata errors)
            self._record_metadata_history(
                action="smudge",
                from_language=self.canonical_language,
                to_language=self.language,
            )

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

    @staticmethod
    def _collect_string_comment_format_chars(source_code: str) -> set[str]:
        """Collect non-bidi invisible chars inside string/comment tokens.

        Covers both category-``Cf`` format chars and non-``Cf``
        Default_Ignorable marks (e.g. the U+FE0F emoji variation selector), so
        legitimate invisibles in literals/comments — ZWJ/ZWNJ in Indic text,
        emoji presentation selectors — are allowlisted rather than rejected once
        the guard nets the full Default_Ignorable set (CORE-1559).

        Bidi reordering controls are intentionally NOT collected: they are
        dangerous even inside literals for the Trojan Source attack, so
        ``unicode_guard.scan_text`` always flags them.
        """
        import io
        import tokenize

        allowed: set[str] = set()
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)
            for tok in tokens:
                is_str_or_comment = tok.type in (
                    tokenize.STRING,
                    tokenize.COMMENT,
                )
                is_fstring_mid = (
                    hasattr(tokenize, "FSTRING_MIDDLE")
                    and tok.type == tokenize.FSTRING_MIDDLE
                )
                if is_str_or_comment or is_fstring_mid:
                    for ch in tok.string:
                        if ch in unicode_guard.BIDI_CONTROLS:
                            continue
                        is_invisible = unicodedata.category(
                            ch
                        ) == "Cf" or unicode_guard.is_default_ignorable(ch)
                        if is_invisible:
                            allowed.add(ch)
        except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
            return set()
        return allowed

    def _identifier_format_allowlist(self) -> frozenset[str]:
        """Return the format characters this language's identifiers may contain.

        Read from the language's :class:`~legesher_i18n.script_policy.ScriptPolicy`
        — today the Sinhala ZWJ (U+200D, virama+ZWJ conjuncts) and the
        Persian/Urdu ZWNJ (U+200C). Empty for every other language, and empty
        for a language with no registered policy: default-deny.

        Deliberately *not* the string/comment allowlist
        (:meth:`_collect_string_comment_format_chars`) — a ZWJ appearing in a
        comment must never license one inside an identifier.
        """
        try:
            from legesher_i18n.script_policy import policy_for

            return frozenset(policy_for(self.language).allowed_format_chars)
        except (ImportError, KeyError):
            return frozenset()

    @staticmethod
    def _literal_spans(source_code: str) -> list[tuple[int, int]] | None:
        """Return the character spans of every string/comment token.

        The complement is code position. Returns ``None`` when the source
        cannot be tokenized, which the caller treats as "scan nothing" — the
        clean filter passes incomplete code through rather than breaking a
        ``git add`` mid-edit.
        """
        import io
        import tokenize

        # tokenize reports (row, column) and its line model is its own: it
        # breaks lines only at \n, \r\n and \r, while ``str.splitlines`` also
        # breaks at U+000B, U+000C, U+0085, U+2028 and U+2029. Using splitlines
        # here shifts every later offset by one per such character (trivially
        # reachable inside a string literal), so build the line table from the
        # tokenizer's own line breaks.
        line_starts = [0]
        index = 0
        length = len(source_code)
        while index < length:
            char = source_code[index]
            if char == "\r":
                index += 2 if source_code[index + 1 : index + 2] == "\n" else 1
                line_starts.append(index)
            elif char == "\n":
                index += 1
                line_starts.append(index)
            else:
                index += 1

        def offset_of(position: tuple[int, int]) -> int | None:
            row, column = position
            if not 0 < row <= len(line_starts):
                return None
            return line_starts[row - 1] + column

        spans: list[tuple[int, int]] = []
        try:
            for tok in tokenize.generate_tokens(io.StringIO(source_code).readline):
                is_literal = tok.type in (tokenize.STRING, tokenize.COMMENT) or (
                    hasattr(tokenize, "FSTRING_MIDDLE")
                    and tok.type == tokenize.FSTRING_MIDDLE
                )
                if not is_literal:
                    continue
                start, end = offset_of(tok.start), offset_of(tok.end)
                if start is None or end is None:
                    continue
                spans.append((start, end))
        except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
            return None
        return spans

    def _scan_identifier_scripts(self, source_code: str) -> list["unicode_guard.Issue"]:
        """Apply the identifier allowlist to every character in code position.

        Deliberately NOT driven by ``NAME`` tokens. On CPython 3.10 and 3.11
        ``tokenize`` is the pure-Python implementation whose name pattern is
        ``\\w+``, which does not match a nonspacing mark — ``to<U+2D7F>tal``
        lexes as ``NAME`` / ``ERRORTOKEN`` / ``NAME`` and the mark is in no
        NAME token at all. A NAME-driven scan is therefore silently inert on
        two of the four interpreters this package supports, for exactly the
        character class the check exists to catch.

        Scanning the complement of the string/comment spans has no such
        version dependence, and is a superset: a character in code position
        that no token claims is still caught. ASCII outside ``[A-Za-z0-9_]`` is
        skipped because it is Python's own syntax, never an identifier
        character.

        Both the ``"script"`` and the ``"invisible"`` findings are returned.
        The whole-text scan above runs with the string/comment allowlist, so an
        invisible that appears in a comment is licensed everywhere — including
        inside an identifier, which is the one place it must never be. Here the
        allowlist is the language's own :class:`ScriptPolicy` list, so a U+FE0F
        in a comment no longer licenses a U+FE0F in a name.
        """
        spans = self._literal_spans(source_code)
        if spans is None:
            return []

        allowed = self._identifier_format_allowlist()
        issues: list[unicode_guard.Issue] = []
        cursor = 0
        for start, end in [*spans, (len(source_code), len(source_code))]:
            if start > cursor:
                issues.extend(
                    self._scan_code_region(source_code, cursor, start, allowed)
                )
            cursor = max(cursor, end)
        return issues

    @staticmethod
    def _scan_code_region(
        source_code: str, start: int, end: int, allowed: frozenset[str]
    ) -> list["unicode_guard.Issue"]:
        """Scan one code-position slice, skipping Python's own ASCII syntax."""
        issues: list[unicode_guard.Issue] = []
        for offset in range(start, end):
            ch = source_code[offset]
            if ch.isascii() and not (ch.isalnum() or ch == "_"):
                continue
            issues.extend(
                issue
                for issue in unicode_guard.scan_identifier(ch, allowed, start=offset)
                if issue.kind in ("script", "invisible")
            )
        return issues

    def _record_metadata_history(
        self, action: str, from_language: str, to_language: str
    ) -> None:
        """Record git filter operation in metadata history.

        This method is designed to never fail - if metadata recording fails,
        it logs the error but does not raise an exception. This ensures git
        operations are never interrupted by metadata issues.

        Args:
            action: Git filter action ("clean" or "smudge")
            from_language: Source language code
            to_language: Target language code
        """
        # Skip if no metadata manager or file path configured
        if not self.metadata_manager or not self.file_path:
            logger.debug("Skipping metadata recording: manager or file_path not set")
            return

        try:
            # Get current git commit SHA (if available)
            commit_sha = self._get_current_commit_sha()

            # Create history entry
            entry: HistoryEntry = {
                "action": action,
                "from_language": from_language,
                "to_language": to_language,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "commit_sha": commit_sha,
            }

            # Add to metadata
            file_path = Path(self.file_path)
            self.metadata_manager.add_history_entry(file_path, entry)

            logger.debug(
                f"Recorded metadata history: {action} {from_language}->{to_language} "
                f"for {self.file_path}"
            )

        except Exception as e:
            # Never fail git operations due to metadata errors
            logger.warning(
                f"Failed to record metadata history for {self.file_path}: {e}",
                exc_info=True,
            )

    def _get_current_commit_sha(self) -> str | None:
        """Get current git commit SHA.

        Returns:
            Current commit SHA or None if not available or on error
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=2,  # Don't hang git operations
                check=False,  # Don't raise on error
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.debug(f"Could not get git commit SHA: {result.stderr}")
                return None

        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug(f"Error getting git commit SHA: {e}")
            return None

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


def clean_filter(language: str, python_version: str | None = None) -> int:
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


def smudge_filter(language: str, python_version: str | None = None) -> int:
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
