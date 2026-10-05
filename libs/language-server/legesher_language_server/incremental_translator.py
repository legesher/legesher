"""Incremental code translation with caching and dirty tracking.

This module provides efficient incremental translation of Python code,
only retranslating changed portions when documents are edited. This
dramatically improves performance for real-time IDE features.

Part of the enhanced-intelligence path: it prepares the canonical English
text an external type-aware server is asked about, and keeps that text in
step with the editor buffer without retranslating the whole document.
"""

import hashlib
import io
import tokenize
from typing import NamedTuple

from .source_map import Position, SourceMap, SourceMapBuilder
from .type_alias_generator import TypeAliasGenerator


class TranslationResult(NamedTuple):
    """Result of code translation.

    Attributes:
        translated_code: The translated Python code
        source_map: Position mapping between original and translated
        content_hash: Hash of original content for cache invalidation
    """

    translated_code: str
    source_map: SourceMap
    content_hash: str


class IncrementalTranslator:
    """Performs incremental translation of Python code with caching.

    This translator minimizes redundant work by:
    1. Caching full translations by content hash
    2. Tracking which parts of documents have changed
    3. Reusing translations for unchanged regions

    Example:
        >>> translator = IncrementalTranslator(
        ...     source_lang='es',
        ...     target_lang='en',
        ...     keyword_map={'definir': 'def', 'retornar': 'return'}
        ... )
        >>> result = await translator.translate('definir foo():\n    retornar 42')
        >>> # Later, if content unchanged:
        >>> cached = await translator.translate('definir foo():\n    retornar 42')
        >>> assert cached.content_hash == result.content_hash
    """

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        keyword_map: dict[str, str],
        builtin_map: dict[str, str] | None = None,
    ):
        """Initialize incremental translator.

        Args:
            source_lang: Source language code (e.g., 'es')
            target_lang: Target language code (e.g., 'en')
            keyword_map: Mapping from source to target keywords
            builtin_map: Optional mapping for builtin function names
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.keyword_map = keyword_map
        self.builtin_map = builtin_map or {}

        # Reverse mappings for bidirectional translation
        self.reverse_keyword_map = {v: k for k, v in keyword_map.items()}
        self.reverse_builtin_map = {v: k for k, v in self.builtin_map.items()}

        # Translation cache: content_hash -> TranslationResult
        self._cache: dict[str, TranslationResult] = {}

        # Type alias generator for localized types (uses source_lang for localized language)
        self.type_alias_generator = TypeAliasGenerator(target_lang=source_lang)

    async def translate_to_english(self, code: str) -> TranslationResult:
        """Translate localized code to English.

        Args:
            code: Source code in localized language

        Returns:
            TranslationResult with translated code and source map
        """
        # Check cache first
        content_hash = self._hash_content(code)
        if content_hash in self._cache:
            return self._cache[content_hash]

        # Perform translation
        translated, source_map = self._translate_with_map(
            code=code,
            keyword_map=self.keyword_map,
            builtin_map=self.builtin_map,
        )

        # Add type aliases if needed
        translated_with_aliases = self.type_alias_generator.generate_with_aliases(translated)

        # Cache result
        result = TranslationResult(
            translated_code=translated_with_aliases,
            source_map=source_map,
            content_hash=content_hash,
        )
        self._cache[content_hash] = result

        return result

    async def translate_to_localized(self, code: str) -> TranslationResult:
        """Translate English code to localized language.

        Args:
            code: Source code in English

        Returns:
            TranslationResult with translated code and source map
        """
        # Check cache first
        content_hash = self._hash_content(code)
        cache_key = f"reverse_{content_hash}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Perform translation
        translated, source_map = self._translate_with_map(
            code=code,
            keyword_map=self.reverse_keyword_map,
            builtin_map=self.reverse_builtin_map,
        )

        # Cache result
        result = TranslationResult(
            translated_code=translated,
            source_map=source_map,
            content_hash=content_hash,
        )
        self._cache[cache_key] = result

        return result

    def _translate_with_map(
        self,
        code: str,
        keyword_map: dict[str, str],
        builtin_map: dict[str, str],
    ) -> tuple[str, SourceMap]:
        """Translate code and build source map.

        ``tokenize.untokenize`` rebuilds the text from each token's original
        start and end, so every token keeps its row, every gap before a token
        keeps its width, and a translated name changes only its own width. A
        translated name's English position is therefore its original line,
        and its original column plus the width change of the names
        translated before it on the same line. Running counters cannot get
        there: the gaps between tokens, an indent the line did not open, and
        the newlines inside a multi-line string are not tokens of their own
        (CORE-2343).

        Args:
            code: Source code to translate
            keyword_map: Keyword translation mapping
            builtin_map: Builtin function translation mapping

        Returns:
            Tuple of (translated_code, source_map)
        """
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
        except tokenize.TokenError:
            # Handle incomplete code gracefully
            return code, SourceMap([])

        source_map_builder = SourceMapBuilder()
        result_tokens = []

        # The width change so far on the row being translated. A NAME token
        # never spans rows, so a new row starts again from zero.
        shift_row = 0
        shift = 0

        for token in tokens:
            tok_string = token.string

            if token.type == tokenize.NAME:
                translation = keyword_map.get(tok_string, builtin_map.get(tok_string))
            else:
                translation = None

            if translation is None:
                # Everything else passes through, user-defined names included.
                result_tokens.append(token)
                continue

            row, col = token.start
            if row != shift_row:
                shift_row, shift = row, 0

            source_map_builder.add_mapping(
                original_start=Position(row - 1, col),
                original_end=Position(row - 1, col + len(tok_string)),
                translated_start=Position(row - 1, col + shift),
                translated_end=Position(row - 1, col + shift + len(translation)),
            )
            shift += len(translation) - len(tok_string)

            result_tokens.append(token._replace(string=translation))

        # Reconstruct code from tokens
        translated_code = tokenize.untokenize(result_tokens)

        return translated_code, source_map_builder.build()

    def _hash_content(self, content: str) -> str:
        """Generate content hash for cache key.

        Args:
            content: Code content

        Returns:
            SHA256 hash of content
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def clear_cache(self) -> None:
        """Clear translation cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get number of cached translations.

        Returns:
            Number of entries in cache
        """
        return len(self._cache)
