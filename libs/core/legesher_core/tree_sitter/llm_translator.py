"""Full LLM-powered code translator for Python.

Composes TreeSitterTranslator (keywords/builtins) with a pluggable
TextTranslationBackend (identifiers, comments, docstrings, strings)
to translate entire Python files between natural languages.

This is the main entry point for Condition 5 (full translation) and
implements the Translator protocol for polymorphic usage.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional, Union

from ..exceptions import InvalidCodeError
from ..token_mapper import TokenMapper
from ..types import (
    CulturalCommentMetadata,
    TextTranslationBackend,
    TranslatableElement,
    TranslationScope,
)
from .extractor import TranslatableExtractor
from .identifier_map import IdentifierMap
from .identifier_validator import IdentifierValidator
from .parser import PythonParser
from .translation_logger import TranslationLogger
from .translator import TreeSitterTranslator

logger = logging.getLogger(__name__)


class LLMTranslator:
    """Full-code translator using LLM backends for identifiers, comments, strings.

    Composes TreeSitterTranslator (keywords/builtins via language packs) with a
    TextTranslationBackend (LLM for everything else). Maintains identifier
    consistency via IdentifierMap and validates output for valid Python syntax.

    Implements the Translator protocol for polymorphic usage with
    create_translator() factory.

    Example:
        >>> from legesher_core.types import TextTranslationBackend
        >>> class MockBackend:
        ...     def translate_text(self, text, source_lang, target_lang, context=None):
        ...         return f"translated_{text}"
        ...     def translate_batch(self, items, source_lang, target_lang):
        ...         return [f"translated_{i['text']}" for i in items]
        >>> translator = LLMTranslator(
        ...     keyword_map={"def": "definir"},
        ...     builtin_map={"print": "imprimir"},
        ...     backend=MockBackend(),
        ... )
        >>> code = 'def greet():\\n    print("Hello")'
        >>> translated = translator.translate_code(code, "en", "es")
    """

    def __init__(
        self,
        keyword_map: dict[str, str],
        builtin_map: dict[str, str],
        backend: TextTranslationBackend,
        python_version: str = "3.13",
        identifier_map: Optional[IdentifierMap] = None,
        scope: Optional[TranslationScope] = None,
        translation_logger: Optional[TranslationLogger] = None,
    ) -> None:
        """Initialize the LLM translator.

        Args:
            keyword_map: Keyword translation mappings from language pack
            builtin_map: Builtin translation mappings from language pack
            backend: LLM backend for translating identifiers/comments/strings
            python_version: Python version for version-aware packs
            identifier_map: Optional pre-populated identifier map for consistency
            scope: Optional scope config to toggle what gets translated
            translation_logger: Optional logger for training data collection
        """
        self.keyword_translator = TreeSitterTranslator(
            keyword_map=keyword_map,
            builtin_map=builtin_map,
            python_version=python_version,
        )
        self.backend = backend
        self.mapper = TokenMapper(keyword_map, builtin_map)
        self.identifier_map = identifier_map or IdentifierMap()
        self.scope = scope or TranslationScope()
        self.validator = IdentifierValidator()
        self.extractor = TranslatableExtractor(self.mapper)
        self.parser = PythonParser()
        self.python_version = python_version
        self.translation_logger = translation_logger

    def translate_code(
        self,
        source_code: str,
        source_lang: str = "en",
        target_lang: str = "es",
        return_metadata: bool = False,
    ) -> Union[str, tuple[str, CulturalCommentMetadata]]:
        """Translate Python source code with full LLM translation.

        Pipeline:
        1. Parse with tree-sitter
        2. Extract all translatable elements
        3. Translate keywords/builtins via language packs
        4. Translate identifiers via LLM (with dedup + validation)
        5. Translate comments/docstrings/strings via LLM
        6. Apply all replacements
        7. Verify output parses

        Args:
            source_code: Python source code to translate
            source_lang: Source language code (default: "en")
            target_lang: Target language code (default: "es")
            return_metadata: If True, return tuple with cultural comment metadata

        Returns:
            Translated Python source code, or tuple if return_metadata=True
        """
        if not source_code or not source_code.strip():
            if return_metadata:
                return source_code, CulturalCommentMetadata()
            return source_code

        try:
            # Step 1: Parse and extract
            elements = self.extractor.extract(source_code)

            # Step 2: Get keyword/builtin replacements from existing translator
            tree = self.parser.parse(source_code)
            keyword_replacements: list[tuple[int, int, str]] = []
            self.keyword_translator._find_translations(
                tree.root_node, keyword_replacements
            )

            # Step 3: Translate identifiers via LLM
            identifier_replacements = self._translate_identifiers(
                elements, source_lang, target_lang
            )

            # Step 4: Translate comments, docstrings, strings via LLM
            text_replacements = self._translate_text_elements(
                elements, source_lang, target_lang
            )

            # Step 5: Merge all replacements (avoid overlaps)
            all_replacements = self._merge_replacements(
                keyword_replacements, identifier_replacements, text_replacements
            )

            # Step 6: Apply replacements
            byte_to_char = TreeSitterTranslator._build_byte_to_char_map(source_code)
            translated = self._apply_replacements(
                source_code, all_replacements, byte_to_char
            )

            # Step 7: Verify output parses
            self._verify_output(translated, source_code, len(keyword_replacements))

            if return_metadata:
                return translated, CulturalCommentMetadata()
            return translated

        except Exception as e:
            logger.error("LLM translation failed: %s", e)
            raise InvalidCodeError("Failed to translate code") from e

    def _translate_identifiers(
        self,
        elements: list[TranslatableElement],
        source_lang: str,
        target_lang: str,
    ) -> list[tuple[int, int, str]]:
        """Translate identifiers via LLM with dedup and validation."""
        if not self.scope.translate_identifiers:
            return []

        # Collect unique identifiers
        identifier_elements = [e for e in elements if e.kind == "identifier"]
        # Preserve first-seen order for deterministic batching
        unique_ids = list(dict.fromkeys(e.text for e in identifier_elements))

        # Filter out already-translated identifiers
        untranslated = self.identifier_map.get_untranslated(unique_ids, target_lang)

        if untranslated:
            # Build batch with context
            glossary = self.identifier_map.get_glossary(target_lang)
            items = []
            for text in untranslated:
                # Find the first element with this text for context
                elem = next((e for e in identifier_elements if e.text == text), None)
                context: dict[str, Any] = {}
                if elem:
                    context = {**elem.context, "glossary": glossary}
                    context["role"] = elem.role
                items.append({"text": text, "context": context})

            # Batch translate
            translations = self.backend.translate_batch(items, source_lang, target_lang)

            # Validate and store
            for text, translation in zip(untranslated, translations):
                valid = self.validator.is_valid(translation)
                if not valid:
                    raw_attempt = translation  # Preserve for logging
                    # Log failure for training data
                    if self.translation_logger:
                        self.translation_logger.log_validation_failure(
                            identifier=text,
                            first_attempt=raw_attempt,
                            failure_reason="invalid Python identifier",
                        )
                    # Try sanitizing
                    translation = self.validator.sanitize(translation)
                    if self.translation_logger:
                        self.translation_logger.log_validation_failure(
                            identifier=text,
                            first_attempt=raw_attempt,
                            failure_reason="sanitized",
                            retry_result=translation,
                            retry_valid=self.validator.is_valid(translation),
                        )

                self.identifier_map.add(text, target_lang, translation)

                # Log for training data
                if self.translation_logger:
                    elem = next(
                        (e for e in identifier_elements if e.text == text), None
                    )
                    self.translation_logger.log_identifier_pair(
                        source=text,
                        target=translation,
                        target_lang=target_lang,
                        role=elem.role if elem else "other",
                        naming_convention=(
                            elem.context.get("naming_convention", "unknown")
                            if elem
                            else "unknown"
                        ),
                        context=elem.context if elem else None,
                    )

        # Build replacement list
        replacements: list[tuple[int, int, str]] = []
        for elem in identifier_elements:
            translation = self.identifier_map.get(elem.text, target_lang)
            if translation and translation != elem.text:
                replacements.append((elem.start_byte, elem.end_byte, translation))

        return replacements

    def _translate_text_elements(
        self,
        elements: list[TranslatableElement],
        source_lang: str,
        target_lang: str,
    ) -> list[tuple[int, int, str]]:
        """Translate comments, docstrings, and strings via LLM."""
        replacements: list[tuple[int, int, str]] = []

        # Collect elements to translate based on scope
        to_translate = []
        for elem in elements:
            if elem.kind == "identifier":
                continue
            if elem.kind == "comment" and not self.scope.translate_comments:
                continue
            if elem.kind == "docstring" and not self.scope.translate_docstrings:
                continue
            if elem.kind == "string" and not self.scope.translate_strings:
                continue
            to_translate.append(elem)

        if not to_translate:
            return []

        # Batch translate — include identifier glossary so text elements
        # (comments, docstrings, strings) use the same terms as translated identifiers
        glossary = self.identifier_map.get_glossary(target_lang)
        items = [
            {
                "text": elem.text,
                "context": {**elem.context, "kind": elem.kind, "glossary": glossary},
            }
            for elem in to_translate
        ]
        translations = self.backend.translate_batch(items, source_lang, target_lang)

        for elem, translation in zip(to_translate, translations):
            if translation and translation != elem.text:
                if elem.kind == "comment":
                    # Reconstruct comment with # prefix from extractor context
                    # elem.text is content only (no #), hash_prefix is in context
                    hash_prefix = elem.context.get("hash_prefix", "# ")
                    # Handle multi-line LLM responses: prefix each line with #
                    if "\n" in translation:
                        lines = translation.split("\n")
                        translated_comment = "\n".join(
                            f"{hash_prefix}{line}" for line in lines
                        )
                    else:
                        translated_comment = f"{hash_prefix}{translation}"
                    replacements.append(
                        (elem.start_byte, elem.end_byte, translated_comment)
                    )
                elif elem.kind in ("docstring", "string"):
                    is_fstring_content = elem.context.get("is_fstring_content", False)
                    if is_fstring_content:
                        # F-string string_content: insert raw text, no quotes
                        safe_translation = translation
                        # Escape braces to avoid creating new interpolations
                        safe_translation = safe_translation.replace("{", "{{").replace(
                            "}", "}}"
                        )
                        # For non-triple-quoted f-strings, escape newlines
                        is_triple = elem.context.get("is_triple_quoted", False)
                        if not is_triple and "\n" in safe_translation:
                            safe_translation = safe_translation.replace("\n", "\\n")
                        reconstructed = safe_translation
                    else:
                        # Full string/docstring: reconstruct with quotes
                        prefix_str = elem.prefix or ""
                        quote = elem.quote_style or '"""'
                        safe_translation = translation.replace(
                            quote, "\\" + quote[0] + quote[1:]
                        )
                        # For non-triple-quoted strings, escape newlines
                        if quote in ("'", '"') and "\n" in safe_translation:
                            safe_translation = safe_translation.replace("\n", "\\n")
                        reconstructed = f"{prefix_str}{quote}{safe_translation}{quote}"
                    replacements.append((elem.start_byte, elem.end_byte, reconstructed))

                # Log for training data
                if self.translation_logger:
                    self.translation_logger.log_text_pair(
                        source=elem.text,
                        target=translation,
                        target_lang=target_lang,
                        kind=elem.kind,
                        context=elem.context,
                    )

        return replacements

    @staticmethod
    def _merge_replacements(
        *replacement_lists: list[tuple[int, int, str]],
    ) -> list[tuple[int, int, str]]:
        """Merge replacement lists, resolving overlaps by priority.

        Earlier lists have higher priority (keywords > identifiers > text).
        Overlapping replacements from lower-priority lists are dropped.
        """
        # Collect all with priority
        all_replacements: list[tuple[int, int, str, int]] = []
        for priority, rlist in enumerate(replacement_lists):
            for start, end, text in rlist:
                all_replacements.append((start, end, text, priority))

        # Sort by start position, then by priority (lower = higher priority)
        all_replacements.sort(key=lambda r: (r[0], r[3]))

        # Remove overlaps — keep higher priority
        merged: list[tuple[int, int, str]] = []
        last_end = -1
        for start, end, text, _priority in all_replacements:
            if start >= last_end:
                merged.append((start, end, text))
                last_end = end

        return merged

    @staticmethod
    def _apply_replacements(
        source_code: str,
        replacements: list[tuple[int, int, str]],
        byte_to_char: dict[int, int],
    ) -> str:
        """Apply replacements to source code in reverse byte order."""
        # Sort in reverse order to apply from end to start
        sorted_replacements = sorted(replacements, key=lambda r: r[0], reverse=True)

        result = source_code
        for start_byte, end_byte, replacement_text in sorted_replacements:
            start_char = byte_to_char.get(start_byte, start_byte)
            end_char = byte_to_char.get(end_byte, end_byte)
            result = result[:start_char] + replacement_text + result[end_char:]

        return result

    def _verify_output(
        self, translated: str, original: str, keyword_replacement_count: int = 0
    ) -> None:
        """Verify that translated output doesn't introduce structural damage.

        Note: Tree-sitter uses the English Python grammar, so translated
        keywords (e.g., 'definir' instead of 'def') always produce parse
        "errors" — these are expected and harmless. We log a warning if the
        translated output has significantly MORE errors than expected from
        keyword translation, which may indicate broken reconstruction.

        Args:
            translated: The translated source code
            original: The original source code
            keyword_replacement_count: Number of keyword replacements made
        """
        try:
            original_tree = self.parser.parse(original)
            original_errors = self._count_errors(original_tree.root_node)

            translated_tree = self.parser.parse(translated)
            translated_errors = self._count_errors(translated_tree.root_node)

            new_errors = translated_errors - original_errors
            # Each keyword replacement can cause ~1 parse error in the English grammar.
            # Allow that plus a small tolerance for identifier/string changes.
            allowed = keyword_replacement_count + 5
            if new_errors > allowed:
                logger.warning(
                    "Translation may have structural issues: %d new parse errors "
                    "(expected up to %d from %d keyword replacements, got %d total)",
                    new_errors,
                    allowed,
                    keyword_replacement_count,
                    translated_errors,
                )
        except Exception as e:
            logger.warning("Could not verify translated output: %s", e)

    def _count_errors(self, node) -> int:
        """Count ERROR nodes in a tree-sitter parse tree."""
        count = 1 if node.type == "ERROR" else 0
        for child in node.children:
            count += self._count_errors(child)
        return count

    def translate_file(self, file_path: Path, target_lang: str) -> str:
        """Translate a Python file to the target language.

        Args:
            file_path: Path to Python file
            target_lang: Target language code

        Returns:
            Translated Python source code
        """
        source_code = file_path.read_text(encoding="utf-8")
        result = self.translate_code(source_code, "en", target_lang)
        if isinstance(result, tuple):
            return result[0]
        return result

    def reverse(self) -> "LLMTranslator":
        """Create a reverse translator.

        Note: LLM translation is non-deterministic, so reverse translation
        uses the IdentifierMap for consistent round-trips. Comments and
        strings will be re-translated by the LLM.
        """
        reversed_keyword = {v: k for k, v in self.mapper.keyword_map.items()}
        reversed_builtin = {v: k for k, v in self.mapper.builtin_map.items()}
        return LLMTranslator(
            keyword_map=reversed_keyword,
            builtin_map=reversed_builtin,
            backend=self.backend,
            python_version=self.python_version,
            identifier_map=self.identifier_map,
            scope=self.scope,
        )

    @classmethod
    def from_language_pack(
        cls,
        language: str,
        python_version: Optional[str] = None,
        backend: Optional[TextTranslationBackend] = None,
    ) -> "LLMTranslator":
        """Create LLM translator from a language pack.

        Args:
            language: Natural language code (e.g., "es", "zh", "ur")
            python_version: Python version (auto-detects if None)
            backend: LLM backend (required for LLM translation)

        Returns:
            LLMTranslator instance

        Raises:
            ValueError: If no backend is provided
        """
        if backend is None:
            raise ValueError(
                "LLMTranslator requires a TextTranslationBackend. "
                "Use TreeSitterTranslator.from_language_pack() for "
                "keyword-only translation."
            )

        from legesher_i18n import LanguagePackLoader

        if python_version is None:
            version_info = sys.version_info
            python_version = f"{version_info.major}.{version_info.minor}"

        loader = LanguagePackLoader()
        pack = loader.load(language, target="python", version=python_version)

        return cls(
            keyword_map=pack.keywords,
            builtin_map=pack.builtins,
            backend=backend,
            python_version=python_version,
        )

    @classmethod
    def list_available_languages(cls) -> list[tuple[str, str]]:
        """List all available language packs."""
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()
        return loader.list_available_languages()

    def get_pack_info(self) -> dict[str, Union[str, int]]:
        """Get information about the loaded language pack."""
        return {
            "language": "unknown",
            "python_version": self.python_version,
            "keyword_count": len(self.mapper.keyword_map),
            "builtin_count": len(self.mapper.builtin_map),
            "backend": "llm",
        }
