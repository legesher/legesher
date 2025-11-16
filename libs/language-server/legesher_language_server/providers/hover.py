"""Hover provider for translated docstrings and tooltips.

This module provides hover information showing:
- Translated keyword documentation
- Translated builtin function docstrings
- User function docstrings with translation
- Cultural context comments

Implementation for CORE-357.
"""

import ast
import builtins
import inspect
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position

from ..utils.keyword_docs import KeywordDocumentation

# Simple cache for builtin docstrings (bounded by ~35 builtins × 3 languages ≈ 105 entries max)
# Note: Not a true LRU cache - entries never expire. See CORE-XXX for proper LRU implementation.
_docstring_cache: dict[tuple[str, str, str], str] = {}


async def provide_hover(
    server: "LegesherLanguageServer", uri: str, position: Position
) -> Hover | None:
    """Provide hover information at cursor position.

    Args:
        server: Language server instance
        uri: Document URI
        position: Cursor position

    Returns:
        Hover information with translated documentation or None

    Note:
        Implementation for CORE-357 - Full hover provider with:
        - Keyword documentation
        - Builtin function docstrings
        - User function docstrings
        - Cultural comment integration
    """
    # Get document
    doc = server.document_manager.get_document(uri)
    if not doc:
        return None

    # Extract word at position
    word = _extract_word_at_position(doc.text, position)
    if not word:
        return None

    # Create hover provider
    provider = HoverProvider(
        source_lang=server.config.source_language,
        target_lang=server.config.target_language,
        document_text=doc.text,
        document_uri=uri,
    )

    # Get hover content
    hover_content = await provider.get_hover_content(word, position)

    if hover_content:
        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=hover_content,
            )
        )

    return None


class HoverProvider:
    """Provides hover information for code elements.

    This class handles keyword documentation, builtin docstrings,
    user function docstrings, and cultural comments.
    """

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        document_text: str,
        document_uri: str,
    ):
        """Initialize hover provider.

        Args:
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es', 'ar')
            document_text: Full document text
            document_uri: Document URI for context
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.document_text = document_text
        self.document_uri = document_uri
        self.keyword_docs = KeywordDocumentation()

        # Load keyword translation map for target language
        self._keyword_translation_map = self._load_keyword_translations()

    def _load_keyword_translations(self) -> dict[str, str]:
        """Load keyword translation map (Spanish -> English).

        Returns:
            Dictionary mapping translated keywords to English keywords
            Example: {"definir": "def", "retornar": "return", ...}
        """
        from legesher_i18n import LanguagePackLoader

        keyword_map = {}

        try:
            loader = LanguagePackLoader()
            pack = loader.load(language=self.target_lang, target="python", version="3.10")

            # Build reverse map: Spanish -> English
            for english, translated in pack.keywords.items():
                keyword_map[translated] = english

        except Exception:
            # If loading fails, return empty dict (will fall back to English-only keywords)
            pass

        return keyword_map

    async def get_hover_content(self, word: str, position: Position) -> str | None:
        """Get hover content for word at position.

        Args:
            word: Word under cursor
            position: Cursor position

        Returns:
            Markdown-formatted hover content or None
        """
        # Check if English keyword
        if self.keyword_docs.has_keyword(word):
            return self._hover_keyword(word)

        # Check if translated keyword (e.g., Spanish "definir")
        english_keyword = self._keyword_translation_map.get(word)
        if english_keyword:
            # Show documentation for the English equivalent
            return self._hover_keyword(english_keyword, original_keyword=word)

        # Check if builtin
        if self._is_builtin(word):
            return await self._hover_builtin(word)

        # Check if user function/class
        hover_content = self._hover_user_defined(word)
        if hover_content:
            return hover_content

        # Check for cultural comments on this line
        cultural_content = self._get_cultural_comment(position.line)
        if cultural_content:
            return cultural_content

        return None

    def _hover_keyword(self, keyword: str, original_keyword: str | None = None) -> str:
        """Get hover content for Python keyword.

        Args:
            keyword: Python keyword (e.g., 'def', 'class')
            original_keyword: Original translated keyword if different (e.g., 'definir')

        Returns:
            Markdown-formatted keyword documentation
        """
        # Get documentation in target language
        doc = self.keyword_docs.get(keyword, self.target_lang)

        if not doc:
            # Fallback to English if translation not available
            doc = self.keyword_docs.get(keyword, "en") or "Python keyword"

        # Use original keyword in display if provided (e.g., show "definir" not "def")
        display_keyword = original_keyword if original_keyword else keyword

        # Format as markdown
        return f"**`{display_keyword}`** — Python keyword\n\n{doc}"

    def _is_builtin(self, name: str) -> bool:
        """Check if name is a Python builtin.

        Args:
            name: Name to check

        Returns:
            True if name is a builtin function/class
        """
        return hasattr(builtins, name)

    async def _hover_builtin(self, name: str) -> str | None:
        """Get hover content for builtin function/class.

        Args:
            name: Builtin name (e.g., 'print', 'len', 'list')

        Returns:
            Markdown-formatted docstring or None
        """
        # Check cache first
        cache_key = (name, self.source_lang, self.target_lang)
        if cache_key in _docstring_cache:
            return _docstring_cache[cache_key]

        try:
            builtin_obj = getattr(builtins, name)
            docstring = inspect.getdoc(builtin_obj)

            if not docstring:
                return None

            # For MVP, show English docstring
            # TODO: Integrate translation API for docstring translation
            # (Would require legesher-i18n Translation API integration)

            # Get signature if available
            try:
                sig = inspect.signature(builtin_obj)
                signature_str = f"{name}{sig}"
            except (ValueError, TypeError):
                signature_str = f"{name}(...)"

            # Format as markdown
            content = f"**`{signature_str}`** — Python builtin\n\n{docstring}"

            # Cache result
            _docstring_cache[cache_key] = content

            return content

        except (AttributeError, TypeError):
            return None

    def _hover_user_defined(self, name: str) -> str | None:
        """Get hover content for user-defined function/class.

        Args:
            name: Function or class name

        Returns:
            Markdown-formatted docstring or None
        """
        try:
            # Parse document to find definition
            tree = ast.parse(self.document_text)

            # Search for function or class definition
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    if node.name == name:
                        # Extract docstring
                        docstring = ast.get_docstring(node)

                        if not docstring:
                            return None

                        # Get function signature for functions
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            args = self._format_arguments(node.args)
                            kind = (
                                "async function"
                                if isinstance(node, ast.AsyncFunctionDef)
                                else "function"
                            )
                            signature = (
                                f"{'async ' if kind == 'async function' else ''}{name}({args})"
                            )
                        else:
                            signature = f"class {name}"
                            kind = "class"

                        # Format as markdown
                        # For MVP, show docstring as-is
                        # TODO: Integrate translation for user docstrings
                        return f"**`{signature}`** — User-defined {kind}\n\n{docstring}"

            return None

        except SyntaxError:
            # Document has syntax errors, can't parse
            return None

    def _format_arguments(self, args: ast.arguments) -> str:
        """Format function arguments for display.

        Args:
            args: AST arguments node

        Returns:
            Formatted argument list (e.g., 'x, y, *args, **kwargs')
        """
        arg_strs = []

        # Regular arguments
        for arg in args.args:
            arg_strs.append(arg.arg)

        # *args
        if args.vararg:
            arg_strs.append(f"*{args.vararg.arg}")

        # **kwargs
        if args.kwarg:
            arg_strs.append(f"**{args.kwarg.arg}")

        return ", ".join(arg_strs)

    def _get_cultural_comment(self, line_number: int) -> str | None:
        """Get cultural comment for line if present.

        Args:
            line_number: Line number (0-indexed in LSP)

        Returns:
            Formatted cultural comment or None
        """
        # Get line content
        lines = self.document_text.splitlines()
        if line_number >= len(lines):
            return None

        line = lines[line_number]

        # Check for cultural comment syntax: #@culture[lang]: explanation
        match = re.search(r"#@culture\[(\w+)\]:\s*(.+)", line)

        if match:
            lang = match.group(1)
            explanation = match.group(2)

            # Format with emoji icon
            return f"💬 **Cultural Context** [{lang.upper()}]\n\n{explanation}"

        return None


def _extract_word_at_position(text: str, position: Position) -> str | None:
    """Extract word at cursor position.

    Args:
        text: Document text
        position: Cursor position (line, character)

    Returns:
        Word at position or None
    """
    lines = text.splitlines()

    # Check if line exists
    if position.line >= len(lines):
        return None

    line = lines[position.line]

    # Check if character position is valid
    if position.character >= len(line):
        return None

    # Find word boundaries using regex
    # Support Unicode identifiers for all languages (Spanish, Arabic, Chinese, etc.)
    # Python identifiers can contain: letters (any Unicode), digits, underscore
    # But must start with a letter or underscore (not a digit)
    # Use negative lookahead/lookbehind to avoid matching parts of larger identifiers
    word_pattern = r"(?<![a-zA-Z0-9_\u0080-\uFFFF])[\w\u0080-\uFFFF]+(?![a-zA-Z0-9_\u0080-\uFFFF])"

    for match in re.finditer(word_pattern, line, re.UNICODE):
        start, end = match.span()
        if start <= position.character < end:
            word = match.group()
            # Ensure it starts with a letter or underscore (not a digit)
            if word and (word[0].isalpha() or word[0] == "_"):
                return word

    return None
