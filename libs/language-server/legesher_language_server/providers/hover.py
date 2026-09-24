"""Hover provider for translated docstrings and tooltips.

This module provides hover information showing:
- Translated keyword documentation
- Translated builtin function docstrings
- The user's own function and class docstrings, shown verbatim
- Cultural context comments

The keyword and builtin documentation is written out in this package and
currently covers English, Spanish, and Arabic. Hovering a keyword in any
other language returns nothing rather than an English fallback.
"""

import ast
import builtins
import inspect
import logging
import re
import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position

from ..utils.keyword_docs import (
    BuiltinDocumentation,
    KeywordDocumentation,
    ParameterTranslation,
    get_param_translator,
)

logger = logging.getLogger(__name__)

# Thread-safe cache lock for builtin documentation (CORE-446 security)
_cache_lock = threading.Lock()

# Cache version - increment when translation logic changes to invalidate old entries
# Version 1: Initial implementation with parameter name translation only
# Version 2: Added default value translation (None, True, False, types, exceptions)
_HOVER_CACHE_VERSION = 2

# LRU cache for builtin docstrings (CORE-442/CORE-443/CORE-446)
# Replaced simple dict with proper LRU cache with automatic eviction
# Size: 128 entries allows ~35 builtins × 3 languages with room for growth
# Note: We use OrderedDict for LRU behavior since BuiltinDocumentation/ParameterTranslation
# instances are not hashable for @lru_cache decorator


def _get_builtin_doc_cached(
    name: str,
    display_name: str,
    source_lang: str,
    target_lang: str,
    builtin_docs: BuiltinDocumentation,
    param_translator: ParameterTranslation,
) -> str | None:
    """Get cached builtin documentation with LRU eviction.

    Args:
        name: Builtin name in English (e.g., 'print', 'len')
        display_name: Display name (translated name if different)
        source_lang: Source language code
        target_lang: Target language code
        builtin_docs: BuiltinDocumentation instance for fetching docs
        param_translator: ParameterTranslation instance for signature translation

    Returns:
        Markdown-formatted docstring or None

    Note:
        This function uses a manual LRU cache. The cache is bounded
        at 128 entries and automatically evicts least-recently-used items.
        We use a manual cache because BuiltinDocumentation/ParameterTranslation
        instances are not hashable for @lru_cache decorator.

        Thread-safe: Uses threading.Lock to prevent race conditions during
        concurrent async task execution (CORE-446 security).
    """
    # Create cache key from hashable values only
    # Include cache version to invalidate old entries when translation logic changes
    cache_key = (_HOVER_CACHE_VERSION, name, display_name, source_lang, target_lang)

    # Create module-level cache if it doesn't exist
    if not hasattr(_get_builtin_doc_cached, "_cache"):
        _get_builtin_doc_cached._cache = OrderedDict()

    cache = _get_builtin_doc_cached._cache

    # Thread-safe cache access
    with _cache_lock:
        # Check cache
        if cache_key in cache:
            # Move to end (mark as recently used)
            cache.move_to_end(cache_key)
            return cache[cache_key]

    # Not in cache - compute result
    try:
        builtin_obj = getattr(builtins, name)

        # Try to get translated documentation first
        docstring = builtin_docs.get(name, target_lang)
        if not docstring:
            # Fallback to English translated doc
            docstring = builtin_docs.get(name, "en")
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
            translated_sig = param_translator.translate_signature(sig_str, target_lang)
            # Build signature with translated function name and parameters
            signature_str = f"{display_name}{translated_sig}"
        except (ValueError, TypeError):
            signature_str = f"{display_name}(...)"

        # Format as markdown with improved layout
        # Use 'python' language for syntax highlighting in code fence
        if display_name != name:
            # Show: translated name (english name) - for translated builtins
            content = (
                f"**`{display_name}`** (`{name}`)\n\n```python\n{signature_str}\n```\n\n{docstring}"
            )
        else:
            content = f"**`{display_name}`**\n\n```python\n{signature_str}\n```\n\n{docstring}"

        # Add to cache with LRU eviction (thread-safe)
        with _cache_lock:
            cache[cache_key] = content
            # Evict oldest if cache is full
            if len(cache) > 128:
                cache.popitem(last=False)  # Remove oldest (first) item

        return content

    except (AttributeError, TypeError):
        return None


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

    Resolves the word under the cursor through the target language pack, then
    returns whichever of keyword documentation, builtin documentation, the
    user's own docstring, or a cultural comment that word matches. Returns
    None when the document is not open, when the word matches nothing, or
    when no documentation exists for the target language — see the module
    docstring for which languages carry it.
    """
    # Get document
    doc = server.document_manager.get_document(uri)
    if not doc:
        return None

    # Extract word at position
    word = _extract_word_at_position(doc.text, position)
    # Debug, not info: the word under the cursor is text out of the user's
    # file, and a default-level log is not a place to put it (CORE-1979).
    logger.debug(f"Hover request at {position.line}:{position.character}, extracted word: '{word}'")
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
        logger.debug(f"Returning hover content: {hover_content[:100]}...")
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

    # Default Python version for language pack loading
    # This should match the minimum supported Python version in i18n packs
    DEFAULT_PYTHON_VERSION = "3.10"

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
        # Use cached singleton to avoid reloading 174+ translations on every hover
        self.param_translator = get_param_translator()

        # Load all translation maps in one pass (avoids redundant pack loading)
        translations = self._load_all_translations()
        self._keyword_translation_map = translations["keyword_reverse"]
        self._keyword_forward_map = translations["keyword_forward"]
        self._builtin_translation_map = translations["builtin_reverse"]
        self._builtin_forward_map = translations["builtin_forward"]

    def _load_all_translations(self) -> dict[str, dict[str, str]]:
        """Load all translation maps in a single language pack load.

        This consolidates what was previously 4 separate LanguagePackLoader.load()
        calls into a single call, improving initialization performance.

        Returns:
            Dictionary with keys:
                - "keyword_reverse": translated keywords -> English
                - "keyword_forward": English -> translated keywords
                - "builtin_reverse": translated builtins -> English
                - "builtin_forward": English -> translated builtins
        """
        from legesher_i18n import LanguagePackLoader

        result = {
            "keyword_reverse": {},
            "keyword_forward": {},
            "builtin_reverse": {},
            "builtin_forward": {},
        }

        try:
            loader = LanguagePackLoader()
            pack = loader.load(
                language=self.target_lang,
                target="python",
                version=self.DEFAULT_PYTHON_VERSION,
            )

            # Build keyword maps (forward and reverse) from single pack load
            for english, translated in pack.keywords.items():
                result["keyword_forward"][english] = translated
                result["keyword_reverse"][translated] = english

            # Build builtin maps (forward and reverse) from single pack load
            for english, translated in pack.builtins.items():
                result["builtin_forward"][english] = translated
                result["builtin_reverse"][translated] = english

            logger.info(
                f"Loaded {len(result['keyword_forward'])} keywords and "
                f"{len(result['builtin_forward'])} builtins for hover provider "
                f"(lang={self.target_lang})"
            )

        except Exception as e:
            # If loading fails, return empty dicts (will fall back to English-only)
            logger.warning(f"Failed to load translations for hover: {e}")

        return result

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
            pack = loader.load(
                language=self.target_lang,
                target="python",
                version=self.DEFAULT_PYTHON_VERSION,
            )

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

    def _load_keyword_forward_translations(self) -> dict[str, str]:
        """Load forward keyword translation map (English -> target language).

        Returns:
            Dictionary mapping English keywords to translated keywords
            Example: {"def": "definir"}, {"def": "تعريف"}, {"def": "定义"}
        """
        from legesher_i18n import LanguagePackLoader

        keyword_map = {}

        try:
            loader = LanguagePackLoader()
            pack = loader.load(
                language=self.target_lang,
                target="python",
                version=self.DEFAULT_PYTHON_VERSION,
            )

            # Build forward map: English -> target language
            for english, translated in pack.keywords.items():
                keyword_map[english] = translated

            logger.debug(f"Loaded {len(keyword_map)} forward keyword translations")

        except Exception as e:
            logger.warning(f"Failed to load forward keyword translations: {e}")

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
            pack = loader.load(
                language=self.target_lang,
                target="python",
                version=self.DEFAULT_PYTHON_VERSION,
            )

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

    def _load_builtin_forward_translations(self) -> dict[str, str]:
        """Load forward builtin translation map (English -> target language).

        Returns:
            Dictionary mapping English builtins to translated builtins
            Example: {"print": "imprimir"}, {"print": "طباعة"}
        """
        from legesher_i18n import LanguagePackLoader

        builtin_map = {}

        try:
            loader = LanguagePackLoader()
            pack = loader.load(
                language=self.target_lang,
                target="python",
                version=self.DEFAULT_PYTHON_VERSION,
            )

            # Build forward map: English -> target language
            for english, translated in pack.builtins.items():
                builtin_map[english] = translated

            logger.debug(f"Loaded {len(builtin_map)} forward builtin translations")

        except Exception as e:
            logger.warning(f"Failed to load forward builtin translations: {e}")

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

        Shows English documentation first, then target language translation if available.

        Args:
            keyword: Python keyword in English (e.g., 'def', 'class')
            original_keyword: Original translated keyword if hovering over translated code

        Returns:
            Markdown-formatted keyword documentation with translation
        """
        # Always get English documentation first
        english_doc = self.keyword_docs.get(keyword, "en") or "Python keyword"

        # Build the hover content - English info on top
        if original_keyword:
            # Hovering over translated keyword (e.g., परिभाषितकरना)
            # Show: translated keyword (english equivalent)
            content = f"**`{original_keyword}`** (`{keyword}`) — Python keyword\n\n{english_doc}"
        else:
            # Hovering over English keyword
            content = f"**`{keyword}`** — Python keyword\n\n{english_doc}"

        # Add target language translation section if available and different from English
        if self.target_lang != "en" and self.target_lang != self.source_lang:
            translated_keyword = self._keyword_forward_map.get(keyword)
            if translated_keyword and translated_keyword != keyword:
                # Get target language documentation if available
                target_doc = self.keyword_docs.get(keyword, self.target_lang)

                # Add dividing line and translation
                content += "\n\n---\n\n"
                content += f"**Legesher ({self.target_lang}):** `{translated_keyword}`"

                # Add target language documentation if different from English
                if target_doc and target_doc != english_doc:
                    content += f"\n\n{target_doc}"

        logger.debug(
            f"Hover keyword: keyword={keyword}, original={original_keyword}, "
            f"target_lang={self.target_lang}"
        )

        return content

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

        Shows English documentation first, then target language translation if available.

        Args:
            name: Builtin name in English (e.g., 'print', 'len', 'list')
            original_name: Original translated name if hovering over translated code

        Returns:
            Markdown-formatted docstring with translation or None

        Note:
            Uses LRU cached function for performance (CORE-442/CORE-443).
        """
        # Use original name for display if provided
        display_name = original_name if original_name else name

        # Call cached function for base content (CORE-442/CORE-443)
        content = _get_builtin_doc_cached(
            name=name,
            display_name=display_name,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            builtin_docs=self.builtin_docs,
            param_translator=self.param_translator,
        )

        if not content:
            return None

        # Add target language translation section if available and different from English
        if self.target_lang != "en" and self.target_lang != self.source_lang:
            translated_name = self._builtin_forward_map.get(name)
            if translated_name and translated_name != name and not original_name:
                # Only add translation section when hovering over English builtin
                # (not when already hovering over translated builtin)
                content += f"\n\n---\n\n**Legesher ({self.target_lang}):** `{translated_name}`"

        return content

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

                        # The user's own docstring is shown verbatim. Unlike
                        # keyword and builtin documentation, it has no entry in
                        # the language pack to translate against, and running
                        # it through a model would make hover a network call.
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
