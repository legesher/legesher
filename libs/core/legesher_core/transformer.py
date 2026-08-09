"""Token-based code transformer for multilingual Python translation.

This module implements the core translation engine using Python's tokenize module
to transform Python code between natural languages while preserving formatting,
whitespace, comments, and code structure.
"""

import io
import logging
import sys
import tokenize
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .register_map.model import RegisterMap

from .cultural_comments import CulturalCommentParser
from .exceptions import InvalidCodeError
from .token_mapper import TokenMapper
from .types import CulturalCommentMetadata
from .utils import validate_utf8_encoding, normalize_newlines

# Configure logger
logger = logging.getLogger(__name__)


class TokenTranslator:
    """Translate Python code between natural languages using token-based transformation.

    This class provides the main translation engine for Legesher, converting Python
    keywords and builtin function names between languages (e.g., English to Spanish)
    while perfectly preserving all formatting, whitespace, comments, and code structure.

    The translator uses Python's tokenize module for parsing, which:
    - Preserves exact formatting (whitespace, indentation, blank lines)
    - Handles incomplete code gracefully (for real-time editing)
    - Works line-by-line for fast performance
    - Doesn't require semantic understanding of code

    Attributes:
        mapper: TokenMapper instance for translation lookups
        python_version: Target Python version (e.g., "3.13")

    Example:
        >>> spanish_keywords = {"def": "definir", "return": "retornar"}
        >>> spanish_builtins = {"print": "imprimir", "len": "longitud"}
        >>> translator = TokenTranslator(
        ...     keyword_map=spanish_keywords,
        ...     builtin_map=spanish_builtins,
        ...     python_version="3.13"
        ... )
        >>> code = "def greet():\\n    print('Hello')"
        >>> spanish_code = translator.translate_code(code, "en", "es")
        >>> print(spanish_code)
        definir greet():
            imprimir('Hello')
    """

    def __init__(
        self,
        keyword_map: dict[str, str],
        builtin_map: dict[str, str],
        python_version: str = "3.13",
        reserved_word_map: dict[str, str] | None = None,
    ) -> None:
        """Initialize translator with language maps and Python version.

        Args:
            keyword_map: Dictionary mapping English keywords to target language
            builtin_map: Dictionary mapping English builtins to target language
            python_version: Python version string (default: "3.13")
            reserved_word_map: Optional mapping of Python conventions like
                ``self`` and ``cls`` to target language (CORE-710). Defaults
                to empty so existing callers don't need to change.

        Raises:
            ValueError: If keyword_map or builtin_map is empty or None.

        Example:
            >>> translator = TokenTranslator(
            ...     keyword_map={"def": "definir", "return": "retornar"},
            ...     builtin_map={"print": "imprimir"},
            ...     reserved_word_map={"self": "propio", "cls": "clase"},
            ...     python_version="3.13"
            ... )
        """
        self.mapper = TokenMapper(keyword_map, builtin_map, reserved_word_map)
        self.python_version = python_version

    def __repr__(self) -> str:
        """Return a developer-friendly string representation for debugging.

        Example:
            >>> translator = TokenTranslator({"def": "definir"}, {"print": "imprimir"})
            >>> repr(translator)
            "TokenTranslator(keywords=1, builtins=1, reserved_words=0, python_version='3.13')"
        """
        return (
            f"TokenTranslator("
            f"keywords={len(self.mapper.keyword_map)}, "
            f"builtins={len(self.mapper.builtin_map)}, "
            f"reserved_words={len(self.mapper.reserved_word_map)}, "
            f"python_version={self.python_version!r})"
        )

    def translate_code(
        self,
        source_code: str,
        source_lang: str = "en",
        target_lang: str = "es",
        return_metadata: bool = False,
    ) -> str | tuple[str, CulturalCommentMetadata]:
        """Translate Python source code from one language to another.

        This method translates Python keywords and builtin function names while
        preserving all formatting, whitespace, comments, and code structure.

        Translation process:
        1. Normalize line endings (\\r\\n → \\n)
        2. Tokenize source code using Python's tokenize module
        3. Optionally extract cultural comment metadata (for IDE integration)
        4. For each NAME token, check if it's a keyword or builtin
        5. Replace with translated version if found in maps
        6. Reconstruct code using untokenize, preserving formatting

        Args:
            source_code: Python source code to translate
            source_lang: Source language code (currently unused, for future)
            target_lang: Target language code (currently unused, for future)
            return_metadata: If True, return tuple of (code, cultural_metadata)

        Returns:
            If return_metadata=False: Translated source code (default)
            If return_metadata=True: Tuple of (translated code, cultural metadata)

        Raises:
            InvalidCodeError: If code has severe syntax errors

        Example:
            >>> code = "def calculate_tax(income, rate):\\n    return income * rate"
            >>> translated = translator.translate_code(code, "en", "es")
            >>> print(translated)
            definir calculate_tax(income, rate):
                retornar income * rate

            >>> # With metadata for IDE integration
            >>> code_with_cultural = '''
            ... #@culture[es]: explanation
            ... def foo(): pass
            ... '''
            >>> translated, metadata = translator.translate_code(
            ...     code_with_cultural, "en", "es", return_metadata=True
            ... )
            >>> metadata.has_comments()
            True

        Note:
            - Comments and docstrings are NOT translated (preserved as-is)
            - Cultural comments (#@culture[lang]: ...) are extracted when
              return_metadata=True for IDE tooltip/decoration support
            - Variable and function names are NOT translated (out of scope)
            - Incomplete code is handled gracefully (translates valid portion)
            - Syntax errors return original code unchanged
        """
        # Normalize line endings for consistent processing. Done BEFORE the
        # empty/whitespace-only early return so every rendering this method
        # hands back — including pass-throughs — is LF-normalized and can
        # never disagree with the register map's rendering (CORE-1160).
        source_code = normalize_newlines(source_code)

        # Handle empty input
        if not source_code or not source_code.strip():
            if return_metadata:
                return source_code, CulturalCommentMetadata()
            return source_code

        try:
            # Tokenize the source code
            tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))

            # Extract cultural comment metadata if requested (for IDE integration)
            cultural_metadata: CulturalCommentMetadata | None = None
            if return_metadata:
                parser = CulturalCommentParser()
                cultural_metadata = parser.parse_from_tokens(iter(tokens))
                logger.debug(
                    f"Extracted {len(cultural_metadata.comments)} "
                    f"cultural comment(s) from source"
                )

            # Translate tokens (index-based for compound keyword lookahead)
            translated_tokens = []
            i = 0
            while i < len(tokens):
                tok = tokens[i]

                # Check if this is a NAME token (keyword, builtin, or identifier)
                if tok.type == tokenize.NAME:
                    # Table lookups use the NFC form (compare-NFC contract,
                    # see unicode_guard): a canonically equivalent rendering
                    # of a keyword/builtin translates identically, and the
                    # emitted register map (entry text stored NFC) records
                    # exactly what this path does. ASCII fast path skips the
                    # normalization cost on the hot path.
                    lookup = (
                        tok.string
                        if tok.string.isascii()
                        else unicodedata.normalize("NFC", tok.string)
                    )
                    # Check for compound keyword: NAME + OP("*") → e.g., "except*"
                    compound_key = f"{lookup}*"
                    compound_val = self.mapper.get_keyword(compound_key)
                    if (
                        compound_val
                        and i + 1 < len(tokens)
                        and tokens[i + 1].type == tokenize.OP
                        and tokens[i + 1].string == "*"
                    ):
                        # Strip trailing * from translation (the * OP token is kept)
                        translated_val = (
                            compound_val[:-1]
                            if compound_val.endswith("*")
                            else compound_val
                        )
                        new_tok = tokenize.TokenInfo(
                            tok.type, translated_val, tok.start, tok.end, tok.line
                        )
                        translated_tokens.append(new_tok)
                        translated_tokens.append(tokens[i + 1])  # keep the * OP
                        i += 2
                        continue

                    # Try to translate as keyword first
                    translated = self.mapper.get_keyword(lookup)
                    if translated and translated != tok.string:
                        # Create new token only when translation changes the string
                        new_tok = tokenize.TokenInfo(
                            tok.type, translated, tok.start, tok.end, tok.line
                        )
                        translated_tokens.append(new_tok)
                        i += 1
                        continue

                    # Try to translate as builtin
                    translated = self.mapper.get_builtin(lookup)
                    if translated and translated != tok.string:
                        # Create new token only when translation changes the string
                        new_tok = tokenize.TokenInfo(
                            tok.type, translated, tok.start, tok.end, tok.line
                        )
                        translated_tokens.append(new_tok)
                        i += 1
                        continue

                    # Try to translate as reserved word (CORE-710: self, cls).
                    # Short-circuit when the map is empty — most callers (and
                    # all pre-CORE-710 ones) don't pass reserved_word_map, and
                    # the extra dict.get() costs ~6% on the hot path otherwise.
                    if reserved_word_map := self.mapper.reserved_word_map:
                        translated = reserved_word_map.get(lookup)
                        if translated and translated != tok.string:
                            new_tok = tokenize.TokenInfo(
                                tok.type,
                                translated,
                                tok.start,
                                tok.end,
                                tok.line,
                            )
                            translated_tokens.append(new_tok)
                            i += 1
                            continue

                # Keep token unchanged (identifiers, operators, etc.)
                translated_tokens.append(tok)
                i += 1

            # Reconstruct code from translated tokens
            result = tokenize.untokenize(translated_tokens)

            # untokenize returns bytes in some cases, decode to string
            if isinstance(result, bytes):
                result = result.decode("utf-8")

            # Return with or without metadata based on request
            if return_metadata:
                # When return_metadata is True, cultural_metadata was
                # populated above by parse_from_tokens (which returns a
                # non-None CulturalCommentMetadata). Narrow explicitly to
                # satisfy the tuple return contract.
                assert cultural_metadata is not None
                return result, cultural_metadata
            return result

        except tokenize.TokenError as e:
            # Handle incomplete code gracefully (expected during real-time editing)
            logger.info(f"Incomplete code handled gracefully: {e}")
            if return_metadata:
                return source_code, CulturalCommentMetadata()
            return source_code

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Translation failed unexpectedly: {e}")
            raise InvalidCodeError(f"Failed to translate code: {e}") from e

    def translate_code_with_map(
        self,
        source_code: str,
        source_lang: str = "en",
        target_lang: str = "es",
        register_map: "RegisterMap | None" = None,
        file: str | None = None,
    ) -> tuple[str, "RegisterMap"]:
        """Translate code AND emit the node-keyed register map (CORE-1662 f).

        Opt-in companion to :meth:`translate_code` for CLI/git-filter runs
        that want to persist classification. The deterministic token path
        is unchanged; the register map is produced by running the existing
        tree-sitter classification (``register_map.builder``) alongside it
        on the same source — reusing the extractor's node identity rather
        than re-teaching the tokenizer. The emitted map satisfies the same
        completeness invariant as a directly built one.

        The map describes the SOURCE rendering the translator saw (after
        CRLF normalization, per CORE-1160): entry text is source-language,
        NFC-normalized. Deterministic translations are recorded from the
        same tables ``translate_code`` uses, keyed by each entry's element
        class: ``keyword``/``builtin`` entries and reserved-word
        identifiers get ``translations[target_lang]``. The record is
        refreshed on every call as a function of the entry's CURRENT
        ``original_text`` — a stale value left behind by a re-anchor (the
        entry's text changed while its ID survived) is cleared, never
        kept. (Compound forms such as ``except*`` record the base token's
        translation; the trailing ``*`` is a separate ``other`` entry.)

        Warning:
            For names that shadow a keyword or builtin at a binding site
            (``print = 5``, ``def match(case)``) the two layers of the
            returned pair disagree by design: the context-free token path
            still rewrites the name in the translated OUTPUT (CORE-704
            family — the deterministic translator mistranslates shadowed
            names), while the map's context-aware classification correctly
            records the entry as an ``identifier`` with NO deterministic
            translation. The map's classification is authoritative; the
            divergence classes are pinned in
            ``tests/register_map/test_conformance.py``.

        Requires the ``treesitter`` extra (imported lazily, so plain
        :meth:`translate_code` keeps working on minimal installs; without
        the extra this method raises the ImportError naming it).

        Args:
            source_code: Python source code to translate.
            source_lang: Language of ``source_code`` (recorded on a newly
                built map).
            target_lang: Target language for the deterministic translation.
            register_map: Existing map to reconcile against (node IDs are
                preserved per the stability contract). When ``None``, a
                fresh map is built and IDs are minted.
            file: Optional file path recorded on a newly built map.

        Returns:
            ``(translated_code, register_map)``. ``translated_code`` is
            byte-identical to what :meth:`translate_code` returns; the map
            is reconciled in place when one was passed in.
        """
        # Lazy import via the package's PEP 562 re-exports (NOT the builder
        # module directly) so a missing tree-sitter extra surfaces as the
        # friendly ImportError naming `legesher-core[treesitter]` instead
        # of a raw ModuleNotFoundError. The default translate path stays
        # importable without the extra.
        from .register_map import build_register_map, update_register_map

        translated = cast(
            str,
            self.translate_code(source_code, source_lang, target_lang),
        )
        # The map describes what the translator saw: the LF-normalized
        # rendering (normalize_newlines is also translate_code's first step).
        normalized = normalize_newlines(source_code)
        if register_map is None:
            register_map = build_register_map(
                normalized, self.mapper, source_lang=source_lang, file=file
            )
        else:
            update_register_map(register_map, normalized, self.mapper)

        # Record what the deterministic path translates, per its tables.
        # Entry text is stored NFC and translate_code also looks tables up
        # via NFC (compare-NFC contract), so the two layers agree on every
        # lookup. The record must be a function of the CURRENT
        # original_text: on a table miss, a previously recorded value is a
        # stale leftover from a re-anchor (reconcile keeps translations
        # while refreshing the text) and is cleared.
        reserved_word_map = self.mapper.reserved_word_map
        reserved_values = frozenset(reserved_word_map.values())
        for entry in register_map.entries.values():
            translation: str | None = None
            deterministic_owned = False
            if entry.element_class == "keyword":
                translation = self.mapper.get_keyword(entry.original_text)
                deterministic_owned = True
            elif entry.element_class == "builtin":
                translation = self.mapper.get_builtin(entry.original_text)
                deterministic_owned = True
            elif entry.element_class == "identifier" and reserved_word_map:
                translation = reserved_word_map.get(entry.original_text)
                # Reserved-word records are the ONLY identifier translations
                # this layer owns — identifier-layer translations (LLM /
                # IdentifierMap) must survive re-emission. A stale reserved
                # record is recognizable by its value: IdentifierMap.add
                # validates against the pack, so an identifier-layer
                # translation can never equal a reserved-word value.
                # (Entry-level provenance arrives with the map-correction
                # workflow; this value check is the interim discriminator.)
                deterministic_owned = (
                    translation is not None
                    or entry.translations.get(target_lang) in reserved_values
                )
            if translation:
                entry.translations[target_lang] = translation
            elif deterministic_owned:
                entry.translations.pop(target_lang, None)
        return translated, register_map

    def translate_file(self, file_path: Path, target_lang: str) -> str:
        """Translate a Python file to target language.

        Reads a Python file from disk, detects encoding, and translates
        the code to the target language.

        Args:
            file_path: Path to Python source file
            target_lang: Target language code (e.g., "es", "ar")

        Returns:
            Translated Python source code

        Raises:
            EncodingError: If file is not UTF-8 encoded
            FileNotFoundError: If file doesn't exist

        Example:
            >>> result = translator.translate_file(
            ...     Path("my_code.py"),
            ...     target_lang="es"
            ... )
        """
        # Verify encoding is UTF-8
        encoding = validate_utf8_encoding(file_path)

        # Read file contents
        with open(file_path, encoding=encoding) as f:
            source_code = f.read()

        # Translate code with default return_metadata=False; always returns
        # str in that branch. mypy cannot narrow the union return of
        # translate_code without @overload, so use typing.cast — honest about
        # intent (no runtime check) and not stripped under python -O.
        return cast(
            str,
            self.translate_code(source_code, source_lang="en", target_lang=target_lang),
        )

    def reverse(self) -> "TokenTranslator":
        """Create a reversed translator (target → source language).

        Returns a new TokenTranslator with reversed translation maps, enabling
        bidirectional translation (e.g., Spanish → English).

        Returns:
            New TokenTranslator with reversed maps

        Example:
            >>> en_to_es = TokenTranslator.from_language_pack("es")
            >>> es_to_en = en_to_es.reverse()
            >>> spanish = "definir greet(): retornar 42"
            >>> english = es_to_en.translate_code(spanish)
            >>> "def greet(): return 42" in english
            True

        Note:
            If multiple English keywords map to the same target keyword,
            only one will be preserved in the reversed map (dict behavior).
        """
        reversed_mapper = self.mapper.reverse()
        return TokenTranslator(
            keyword_map=reversed_mapper.keyword_map,
            builtin_map=reversed_mapper.builtin_map,
            reserved_word_map=reversed_mapper.reserved_word_map,
            python_version=self.python_version,
        )

    @classmethod
    def from_language_pack(
        cls,
        language: str,
        python_version: str | None = None,
    ) -> "TokenTranslator":
        """Create translator from language pack with version awareness.

        Loads the appropriate language pack for the specified language and
        Python version, with automatic version detection if not specified.

        The language pack system supports inheritance, so newer Python
        versions automatically inherit translations from earlier versions.

        Args:
            language: ISO 639-1 language code (e.g., 'es', 'ar', 'hi')
            python_version: Python version string (e.g., '3.10', '3.13')
                           If None, auto-detects from runtime (sys.version_info)

        Returns:
            Configured TokenTranslator ready for code translation

        Raises:
            PackNotFoundError: If language pack doesn't exist for this version
                              (includes list of available languages)
            PackValidationError: If pack file is corrupted or invalid

        Example:
            >>> # Auto-detect version from runtime
            >>> translator = TokenTranslator.from_language_pack("es")
            >>> code = "def greet(): print('Hello')"
            >>> spanish = translator.translate_code(code)
            >>> print(spanish)
            definir greet(): imprimir('Hello')

            >>> # Pin to specific version
            >>> translator = TokenTranslator.from_language_pack("es", "3.10")

            >>> # Round-trip translation
            >>> en_to_es = TokenTranslator.from_language_pack("es")
            >>> es_to_en = en_to_es.reverse()

        See Also:
            - reverse(): Create bidirectional translator
            - list_available_languages(): Get available language packs

        Note:
            Language packs are cached after first load for performance.
            Concurrent calls are thread-safe.
        """
        # Import here to avoid circular dependency
        from legesher_i18n import LanguagePackLoader

        # Auto-detect Python version if not provided
        if python_version is None:
            version_info = sys.version_info
            python_version = f"{version_info.major}.{version_info.minor}"
            logger.debug(f"Auto-detected Python version: {python_version}")

        # Load language pack
        loader = LanguagePackLoader()
        pack = loader.load(language, target="python", version=python_version)

        logger.info(
            f"Loaded language pack: {pack.language} ({len(pack.keywords)} keywords, "
            f"{len(pack.builtins)} builtins) for Python {pack.version}"
        )

        # Merge exceptions into builtin_map (PascalCase remapping)
        from .utils import merge_exception_translations

        builtin_map = pack.builtins
        if hasattr(pack, "exceptions") and pack.exceptions:
            builtin_map = merge_exception_translations(pack.builtins, pack.exceptions)
            logger.debug(
                f"Merged {len(pack.exceptions)} exception translations into builtin map"
            )

        # CORE-710: pull reserved_words from the pack if present (defaults to {})
        reserved_word_map = getattr(pack, "reserved_words", {}) or {}

        return cls(
            keyword_map=pack.keywords,
            builtin_map=builtin_map,
            reserved_word_map=reserved_word_map,
            python_version=python_version,
        )

    @classmethod
    def list_available_languages(cls) -> list[tuple[str, str]]:
        """Get list of available language packs.

        Returns:
            List of (language_code, language_name) tuples

        Example:
            >>> TokenTranslator.list_available_languages()
            [('ar', 'Arabic'), ('es', 'Spanish'), ('hi', 'Hindi')]

        Note:
            This scans the language pack directory to find all available
            languages for Python.
        """
        # Import here to avoid circular dependency
        from legesher_i18n import LanguagePackLoader

        loader = LanguagePackLoader()
        result: list[tuple[str, str]] = loader.list_available_languages(target="python")
        return result

    def get_pack_info(self) -> dict[str, str | int]:
        """Get information about the translator's language maps.

        Returns:
            Dictionary with translation map metadata

        Example:
            >>> translator = TokenTranslator.from_language_pack("es")
            >>> info = translator.get_pack_info()
            >>> info
            {'python_version': '3.13', 'keyword_count': 35, 'builtin_count': 69}
        """
        return {
            "python_version": self.python_version,
            "keyword_count": len(self.mapper.keyword_map),
            "builtin_count": len(self.mapper.builtin_map),
        }
