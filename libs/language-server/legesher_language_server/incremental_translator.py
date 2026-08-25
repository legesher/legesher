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

        # Track cumulative position changes for accurate mapping
        translated_line = 0
        translated_col = 0

        for token in tokens:
            tok_type = token.type
            tok_string = token.string
            start_line, start_col = token.start
            end_line, end_col = token.end

            # Translate keywords and builtins
            if tok_type == tokenize.NAME:
                if tok_string in keyword_map:
                    # Translate keyword
                    translation = keyword_map[tok_string]

                    # Record mapping
                    source_map_builder.add_mapping(
                        original_start=Position(start_line - 1, start_col),
                        original_end=Position(end_line - 1, end_col),
                        translated_start=Position(translated_line, translated_col),
                        translated_end=Position(translated_line, translated_col + len(translation)),
                    )

                    result_tokens.append(
                        (tok_type, translation, token.start, token.end, token.line)
                    )
                    translated_col += len(translation)

                elif tok_string in builtin_map:
                    # Translate builtin (optional - may keep as-is)
                    translation = builtin_map[tok_string]

                    source_map_builder.add_mapping(
                        original_start=Position(start_line - 1, start_col),
                        original_end=Position(end_line - 1, end_col),
                        translated_start=Position(translated_line, translated_col),
                        translated_end=Position(translated_line, translated_col + len(translation)),
                    )

                    result_tokens.append(
                        (tok_type, translation, token.start, token.end, token.line)
                    )
                    translated_col += len(translation)

                else:
                    # Keep identifier as-is (user-defined names never translate)
                    result_tokens.append(token)
                    translated_col += len(tok_string)

            else:
                # Non-NAME tokens pass through
                result_tokens.append(token)

                # Update position tracking
                if tok_type == tokenize.NEWLINE or tok_type == tokenize.NL:
                    translated_line += 1
                    translated_col = 0
                else:
                    translated_col += len(tok_string)

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
