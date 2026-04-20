"""IDE integration support for cultural comments.

This module provides high-level API specifically designed for Language Server Protocol
(LSP) integration, offering convenient methods for displaying cultural comments as
hover tooltips, decorations, and diagnostics in IDEs.

Example:
    >>> code = '''
    ... #@culture[es]: "rango" puede significar "rank" o "range"
    ... def foo(): pass
    ... '''
    >>> provider = CulturalCommentProvider(code)
    >>> hover_text = provider.get_hover_text(2)
    >>> print(hover_text)
    💬 [ES] "rango" puede significar "rank" o "range"
"""

from .cultural_comments import CulturalCommentParser
from .types import CulturalComment


# Diagnostic error messages for cultural comment validation
class DiagnosticMessages:
    """Standardized diagnostic messages for cultural comment errors.

    These constants ensure consistent error messaging across the IDE integration
    and can be easily internationalized in the future.
    """

    MISSING_PREFIX = "Malformed cultural comment: missing '@culture[' prefix"
    MISSING_CLOSING_BRACKET = "Malformed cultural comment: missing closing bracket ']'"
    MISSING_COLON = "Malformed cultural comment: missing ':' after language code"
    INVALID_CASE = (
        "Invalid language code '{lang_code}': must be lowercase (try '{suggestion}')"
    )
    INVALID_LENGTH = (
        "Invalid language code '{lang_code}': must be exactly 2 characters (ISO 639-1)"
    )
    UNSUPPORTED_CODE = (
        "Unsupported language code '{lang_code}'. Valid codes: {valid_codes}"
    )
    MALFORMED_SYNTAX = (
        "Malformed cultural comment: check syntax '@culture[lang]: content'"
    )


class CulturalCommentProvider:
    """High-level API for IDE integration with cultural comments.

    Optimized for Language Server Protocol use cases such as:
    - Hover tooltips showing cultural context
    - Editor decorations (icons/highlights for cultural comments)
    - Diagnostics for malformed cultural comments

    The provider parses source code once and caches results for fast queries.

    Attributes:
        metadata: Parsed cultural comment metadata
        source_code: Original source code (stored for diagnostics)

    Example:
        >>> provider = CulturalCommentProvider(source_code)
        >>> # For hover provider
        >>> hover_text = provider.get_hover_text(line=5)
        >>> # For decoration provider
        >>> decorations = provider.get_decorations()
        >>> # For diagnostic provider
        >>> diagnostics = provider.get_diagnostics()
    """

    def __init__(self, source_code: str, language: str = "python"):
        """Initialize provider with source code.

        Args:
            source_code: Python source code to parse
            language: Programming language (default: "python")
        """
        self.source_code = source_code
        self.language = language

        # Parse cultural comments once and cache
        parser = CulturalCommentParser(language=language)
        self.metadata = parser.parse_from_source(source_code)

    def get_hover_text(
        self, line: int, language_preference: str | None = None
    ) -> str | None:
        """Get formatted hover text for a line.

        Formats cultural comments for display in IDE hover tooltips.
        If multiple cultural comments exist on the line, returns all of them
        formatted nicely. Optionally filters by language preference.

        Args:
            line: 1-indexed line number
            language_preference: Optional ISO 639-1 code to filter by language

        Returns:
            Formatted hover text with icon, or None if no cultural comments

        Example:
            >>> hover = provider.get_hover_text(5)
            '💬 [ES] Explanation text here'

            >>> # Multiple comments on same line
            >>> hover = provider.get_hover_text(10)
            '''💬 [ES] Spanish explanation
            💬 [EN] English explanation'''

            >>> # Filter by language
            >>> hover = provider.get_hover_text(10, language_preference='es')
            '💬 [ES] Spanish explanation'
        """
        comments = self.metadata.get_for_line(line)

        if not comments:
            return None

        # Filter by language preference if provided
        if language_preference:
            comments = [c for c in comments if c.language == language_preference]
            if not comments:
                return None

        # Format each comment
        formatted = []
        for comment in comments:
            formatted.append(self._format_comment(comment))

        return "\n".join(formatted)

    def get_decorations(self) -> list[tuple[int, str, str]]:
        """Get decoration info for all cultural comments.

        Returns line numbers and formatting information for IDE decorations
        (e.g., icons in the gutter, inline highlights).

        Returns:
            List of tuples: (line_number, icon, preview_text)
            - line_number: 1-indexed line number
            - icon: Emoji icon for decoration (💬)
            - preview_text: Short preview for inline display

        Example:
            >>> decorations = provider.get_decorations()
            >>> for line, icon, preview in decorations:
            ...     print(f"Line {line}: {icon} {preview}")
            Line 5: 💬 [ES] "rango" puede significar...
        """
        decorations = []

        for line_num, comments in self.metadata.comments.items():
            for comment in comments:
                # Create preview (truncate if too long)
                preview = comment.content
                if len(preview) > 50:
                    preview = preview[:47] + "..."

                decorations.append(
                    (
                        line_num,
                        "💬",  # Cultural comment icon
                        f"[{comment.language.upper()}] {preview}",
                    )
                )

        return decorations

    def get_diagnostics(self) -> list[tuple[int, int, str, str]]:
        """Get syntax errors in cultural comments for LSP diagnostics.

        Scans the source code for malformed cultural comments that don't
        match the proper syntax, helping developers fix formatting issues.

        Returns:
            List of tuples: (line_number, column, severity, message)
            - line_number: 1-indexed line number
            - column: 0-indexed column offset
            - severity: "warning" or "error"
            - message: Human-readable error message

        Example:
            >>> diagnostics = provider.get_diagnostics()
            >>> for line, col, severity, msg in diagnostics:
            ...     print(f"{severity.upper()} at {line}:{col}: {msg}")
            WARNING at 5:0: Invalid language code 'zz' in cultural comment
        """
        import io
        import tokenize

        diagnostics = []
        parser = CulturalCommentParser(language=self.language)

        try:
            tokens = tokenize.generate_tokens(io.StringIO(self.source_code).readline)

            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    # Check if it looks like a cultural comment but is malformed
                    if "@culture" in tok.string:
                        is_valid, result = parser.validate_syntax(tok.string)

                        if not is_valid:
                            # This is a malformed cultural comment
                            diagnostics.append(
                                (
                                    tok.start[0],  # line number
                                    tok.start[1],  # column offset
                                    "warning",
                                    self._get_diagnostic_message(tok.string, parser),
                                )
                            )

        except tokenize.TokenError:
            # Incomplete code - ignore diagnostics
            pass

        return diagnostics

    def has_cultural_comments(self) -> bool:
        """Quick check if source has any cultural comments.

        Returns:
            True if at least one cultural comment exists
        """
        return self.metadata.has_comments()

    def get_all_languages(self) -> set[str]:
        """Get set of all language codes used in cultural comments.

        Useful for IDE features like "show only comments in my language".

        Returns:
            Set of ISO 639-1 language codes

        Example:
            >>> provider.get_all_languages()
            {'es', 'en', 'ar'}
        """
        languages: set[str] = set()
        for comments_list in self.metadata.comments.values():
            languages.update(c.language for c in comments_list)
        return languages

    def _format_comment(self, comment: CulturalComment) -> str:
        """Format a single cultural comment for display.

        Args:
            comment: Cultural comment to format

        Returns:
            Formatted string with icon and language tag
        """
        lang_upper = comment.language.upper()
        if comment.content:
            return f"💬 [{lang_upper}] {comment.content}"
        else:
            return f"💬 [{lang_upper}] (no content)"

    def _get_diagnostic_message(
        self, comment_str: str, parser: CulturalCommentParser
    ) -> str:
        """Generate helpful diagnostic message for malformed comment.

        Args:
            comment_str: The malformed comment string
            parser: Parser instance for pattern matching

        Returns:
            Human-readable error message with helpful hints
        """
        # Try to figure out what's wrong
        if "@culture[" not in comment_str:
            return DiagnosticMessages.MISSING_PREFIX

        # Check for missing bracket
        if "]" not in comment_str:
            return DiagnosticMessages.MISSING_CLOSING_BRACKET

        # Check for missing colon
        if ":" not in comment_str.split("]", 1)[1]:
            return DiagnosticMessages.MISSING_COLON

        # Try to extract language code
        import re

        match = re.search(r"@culture\[([^\]]+)\]", comment_str)
        if match:
            lang_code = match.group(1)

            # Check if it's not lowercase
            if not lang_code.islower():
                return DiagnosticMessages.INVALID_CASE.format(
                    lang_code=lang_code, suggestion=lang_code.lower()
                )

            # Check if it's not 2 characters
            if len(lang_code) != 2:
                return DiagnosticMessages.INVALID_LENGTH.format(lang_code=lang_code)

            # Must be an unsupported language code
            return DiagnosticMessages.UNSUPPORTED_CODE.format(
                lang_code=lang_code, valid_codes=sorted(parser.VALID_LANG_CODES)
            )

        return DiagnosticMessages.MALFORMED_SYNTAX
