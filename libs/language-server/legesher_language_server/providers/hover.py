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
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position

from ..utils.keyword_docs import (
    BuiltinDocumentation,
    KeywordDocumentation,
    ParameterTranslation,
)

logger = logging.getLogger(__name__)

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
    logger.info(f"Hover request at {position.line}:{position.character}, extracted word: '{word}'")
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
        logger.info(f"Returning hover content: {hover_content[:100]}...")
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
        self.builtin_docs = BuiltinDocumentation()
        self.param_translator = ParameterTranslation()

        # Load keyword translation map for target language
        self._keyword_translation_map = self._load_keyword_translations()

        # Load builtin translation map for target language
        self._builtin_translation_map = self._load_builtin_translations()

    def _load_keyword_translations(self) -> dict[str, str]:
        """Load keyword translation map (target language -> English).

        Returns:
            Dictionary mapping translated keywords to English keywords
            Example: {"definir": "def"}, {"تعريف": "def"}, {"定义": "def"}
        """
        from legesher_i18n import LanguagePackLoader

        keyword_map = {}

        try:
            loader = LanguagePackLoader()
            pack = loader.load(language=self.target_lang, target="python", version="3.10")

            # Build reverse map: target language -> English
            for english, translated in pack.keywords.items():
                keyword_map[translated] = english

            logger.info(
                f"Loaded {len(keyword_map)} keyword translations for hover provider "
                f"(lang={self.target_lang})"
            )
            logger.debug(f"Sample translations: {list(keyword_map.items())[:5]}")

        except Exception as e:
            # If loading fails, return empty dict (will fall back to English-only keywords)
            logger.warning(f"Failed to load keyword translations for hover: {e}")
            pass

        return keyword_map

    def _load_builtin_translations(self) -> dict[str, str]:
        """Load builtin translation map (target language -> English).

        Returns:
            Dictionary mapping translated builtins to English builtins
            Example: {"imprimir": "print"}, {"طباعة": "print"}
        """
        from legesher_i18n import LanguagePackLoader

        builtin_map = {}

        try:
            loader = LanguagePackLoader()
            pack = loader.load(language=self.target_lang, target="python", version="3.10")

            # Build reverse map: target language -> English
            for english, translated in pack.builtins.items():
                builtin_map[translated] = english

            logger.info(
                f"Loaded {len(builtin_map)} builtin translations for hover provider "
                f"(lang={self.target_lang})"
            )
            logger.debug(f"Sample builtin translations: {list(builtin_map.items())[:5]}")

        except Exception as e:
            # If loading fails, return empty dict (will fall back to English-only builtins)
            logger.warning(f"Failed to load builtin translations for hover: {e}")
            pass

        return builtin_map

    async def get_hover_content(self, word: str, position: Position) -> str | None:
        """Get hover content for word at position.

        Args:
            word: Word under cursor
            position: Cursor position

        Returns:
            Markdown-formatted hover content or None
        """
        logger.debug(
            f"get_hover_content called: word='{word}', "
            f"translation_map_size={len(self._keyword_translation_map)}"
        )

        # Check if English keyword
        if self.keyword_docs.has_keyword(word):
            logger.debug(f"'{word}' is an English keyword")
            return self._hover_keyword(word)

        # Check if translated keyword (e.g., Spanish "definir", Arabic "تعريف", Chinese "定义")
        english_keyword = self._keyword_translation_map.get(word)
        logger.debug(f"Translation lookup: '{word}' -> {english_keyword}")
        if english_keyword:
            # Show documentation for the English equivalent
            logger.debug(
                f"Calling _hover_keyword with keyword='{english_keyword}', original='{word}'"
            )
            return self._hover_keyword(english_keyword, original_keyword=word)

        # Check if English builtin
        if self._is_builtin(word):
            return await self._hover_builtin(word)

        # Check if translated builtin (e.g., Spanish "imprimir" -> "print")
        english_builtin = self._builtin_translation_map.get(word)
        if english_builtin and self._is_builtin(english_builtin):
            logger.debug(f"Translated builtin: '{word}' -> '{english_builtin}'")
            return await self._hover_builtin(english_builtin, original_name=word)

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

        logger.debug(
            f"Hover keyword: keyword={keyword}, original={original_keyword}, "
            f"display={display_keyword}"
        )

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

    async def _hover_builtin(self, name: str, original_name: str | None = None) -> str | None:
        """Get hover content for builtin function/class.

        Args:
            name: Builtin name in English (e.g., 'print', 'len', 'list')
            original_name: Original translated name if different (e.g., 'imprimir')

        Returns:
            Markdown-formatted docstring or None
        """
        # Use original name for cache key if provided
        display_name = original_name if original_name else name
        cache_key = (display_name, self.source_lang, self.target_lang)
        if cache_key in _docstring_cache:
            return _docstring_cache[cache_key]

        try:
            builtin_obj = getattr(builtins, name)

            # Try to get translated documentation first
            docstring = self.builtin_docs.get(name, self.target_lang)
            if not docstring:
                # Fallback to English translated doc
                docstring = self.builtin_docs.get(name, "en")
            if not docstring:
                # Fallback to Python's builtin docstring
                docstring = inspect.getdoc(builtin_obj)

            if not docstring:
                return None

            # Get signature if available
            try:
                sig = inspect.signature(builtin_obj)
                sig_str = str(sig)
                # Translate parameter names in signature
                translated_sig = self.param_translator.translate_signature(
                    sig_str, self.target_lang
                )
                # Build signature with translated function name and parameters
                signature_str = f"{display_name}{translated_sig}"
            except (ValueError, TypeError):
                signature_str = f"{display_name}(...)"

            # Format as markdown with improved layout
            if original_name and original_name != name:
                # Show: translated name (english name) - for translated builtins
                # Format:
                # **`imprimir`** (`print`)
                #
                # ```
                # imprimir(*argumentos, separador=' ', fin='\n', archivo=None, vaciar=False)
                # ```
                #
                # Description in target language
                content = (
                    f"**`{display_name}`** (`{name}`)\n\n```\n{signature_str}\n```\n\n{docstring}"
                )
            else:
                content = f"**`{display_name}`**\n\n```\n{signature_str}\n```\n\n{docstring}"

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
