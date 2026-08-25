"""Semantic tokens provider for syntax highlighting translated code.

This module provides LSP semantic token highlighting for translated Python keywords,
builtins, exceptions, class names, function names, and first function parameters.
Uses Python's tokenize module with a lightweight state machine for context-aware
token classification.
"""

import builtins as builtins_module
import io
import logging
import tokenize
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import SemanticTokens

logger = logging.getLogger(__name__)

# Semantic token types (indices must match the legend order in server.py)
TOKEN_TYPE_KEYWORD = 0
TOKEN_TYPE_CLASS = 1
TOKEN_TYPE_FUNCTION = 2
TOKEN_TYPE_VARIABLE = 3
TOKEN_TYPE_PARAMETER = 4

# State machine states for context-aware token classification (CORE-895)
_STATE_NORMAL = 0
_STATE_AFTER_CLASS = 1  # Just saw 'class'/'clase' keyword
_STATE_AFTER_DEF = 2  # Just saw 'def'/'definir' keyword
_STATE_AFTER_FUNC_NAME = 3  # Just saw function name, waiting for '('
_STATE_EXPECT_FIRST_PARAM = 4  # Just saw '(' after function name

# Pre-compute lowercase→proper-case map for Python builtins.
# Used to resolve YAML lowercase keys (e.g., "valueerror") to Python names ("ValueError"),
# and to distinguish builtin types (int, str) from builtin functions (print, len).
_BUILTIN_CASE_MAP: dict[str, str] = {}
_BUILTIN_TYPE_NAMES_LOWER: set[str] = set()
for _name in dir(builtins_module):
    _obj = getattr(builtins_module, _name, None)
    _BUILTIN_CASE_MAP[_name.lower()] = _name
    if isinstance(_obj, type):
        _BUILTIN_TYPE_NAMES_LOWER.add(_name.lower())


def provide_semantic_tokens(server: "LegesherLanguageServer", uri: str) -> SemanticTokens | None:
    """Provide semantic tokens for entire document.

    Args:
        server: Language server instance
        uri: Document URI

    Returns:
        Semantic tokens encoded in LSP delta format, or None if document not found

    Classifies translated keywords, builtins, exceptions, class and function
    names, and first parameters, so an editor colors them the same way it
    colors their English counterparts.
    """
    # Get document
    doc = server.document_manager.get_document(uri)
    if not doc:
        return None

    # Create semantic tokens provider
    provider = SemanticTokensProvider(
        source_lang=server.config.source_language,
        target_lang=server.config.target_language,
        document_text=doc.text,
        document_uri=uri,
    )

    # Get tokens (synchronous)
    tokens = provider.get_semantic_tokens()

    # Encode in LSP delta format
    encoded_data = provider.encode_tokens(tokens)

    return SemanticTokens(data=encoded_data)


class SemanticTokensProvider:
    """Provides semantic tokens for syntax highlighting.

    This provider identifies translated Python keywords and encodes them
    as semantic tokens for LSP-based syntax highlighting.
    """

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        document_text: str,
        document_uri: str,
    ):
        """Initialize semantic tokens provider.

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

        # Lazy-load token mappings (keywords, builtins, exceptions, reserved_words)
        self._translated_keywords: set[str] | None = None
        self._reverse_keyword_map: dict[str, str] | None = None
        self._translated_builtin_types: set[str] | None = None
        self._translated_builtin_funcs: set[str] | None = None
        self._translated_exceptions: set[str] | None = None
        # CORE-710: foundational data path for self/cls reserved words.
        # The set is populated for downstream highlighting work (CORE-1060)
        # but no semantic-token classification logic uses it here yet.
        self._translated_reserved_words: set[str] | None = None

    def _load_token_mappings(self) -> None:
        """Load keyword, builtin, and exception mappings from language pack.

        This loads the language pack on first use to avoid initialization overhead.
        Creates fast lookup sets for keywords, builtins, and exceptions.
        """
        if self._translated_keywords is not None:
            return  # Already loaded

        from legesher_i18n import LanguagePackLoader

        try:
            # Load language pack for target language
            # Use version 3.10 as base (compatible with all Python 3.x)
            loader = LanguagePackLoader()
            pack = loader.load(language=self.target_lang, target="python", version="3.10")

            # Build reverse keyword map: translated -> english
            self._reverse_keyword_map = {
                translated: english for english, translated in pack.keywords.items()
            }

            # Also include English keywords (for mixed-language code)
            for english in pack.keywords.keys():
                if english not in self._reverse_keyword_map:
                    self._reverse_keyword_map[english] = english

            # Create fast lookup set
            self._translated_keywords = set(self._reverse_keyword_map.keys())

            # Build builtin sets, splitting types (int, str) from functions (print, len)
            # so VS Code colors them differently (teal vs yellow)
            builtin_type_names: set[str] = set()
            builtin_func_names: set[str] = set()
            for english_lower, translated in pack.builtins.items():
                proper_name = _BUILTIN_CASE_MAP.get(english_lower)
                if english_lower in _BUILTIN_TYPE_NAMES_LOWER:
                    builtin_type_names.add(translated)
                    builtin_type_names.add(english_lower)  # English fallback (lowercase)
                    if proper_name is not None:
                        builtin_type_names.add(proper_name)  # Properly-cased (e.g., Ellipsis)
                else:
                    builtin_func_names.add(translated)
                    builtin_func_names.add(english_lower)  # English fallback (lowercase)
                    if proper_name is not None:
                        builtin_func_names.add(proper_name)  # Properly-cased (e.g., NotImplemented)
            self._translated_builtin_types = builtin_type_names
            self._translated_builtin_funcs = builtin_func_names

            # Build exceptions set: translated exception names + English exceptions
            exception_names = set(pack.exceptions.values())
            # Add properly-cased English exceptions for mixed-language code
            # YAML keys are lowercase (e.g., "valueerror") but Python uses "ValueError"
            for lowercase_key in pack.exceptions.keys():
                proper_name = _BUILTIN_CASE_MAP.get(lowercase_key)
                if proper_name is not None:
                    exception_names.add(proper_name)
            self._translated_exceptions = exception_names

            # CORE-710: load reserved_words (self, cls) for downstream
            # highlighting (CORE-1060). Falls back to empty when the pack
            # doesn't have the section. Includes both translated values and
            # the canonical English keys (self, cls) so mixed-language code
            # is highlighted consistently.
            reserved_word_names = set(pack.reserved_words.values())
            reserved_word_names.update(pack.reserved_words.keys())
            self._translated_reserved_words = reserved_word_names

            logger.debug(
                f"Loaded {len(self._translated_keywords)} keywords, "
                f"{len(self._translated_builtin_types)} builtin types, "
                f"{len(self._translated_builtin_funcs)} builtin funcs, "
                f"{len(self._translated_exceptions)} exceptions, "
                f"{len(self._translated_reserved_words)} reserved words "
                f"for language '{self.target_lang}'"
            )

        except Exception as e:
            logger.warning(f"Failed to load language pack for '{self.target_lang}': {e!r}")
            # Fallback to empty sets
            self._translated_keywords = set()
            self._reverse_keyword_map = {}
            self._translated_builtin_types = set()
            self._translated_builtin_funcs = set()
            self._translated_exceptions = set()
            self._translated_reserved_words = set()

    def get_semantic_tokens(self) -> list[tuple[int, int, int, int, int]]:
        """Parse document and extract semantic tokens.

        Uses a state machine to provide context-aware classification:
        - After 'class'/'clase': next NAME → class name (TOKEN_TYPE_CLASS)
        - After 'def'/'definir': next NAME → function name (TOKEN_TYPE_FUNCTION)
        - After function name + '(': first NAME → first param/self (TOKEN_TYPE_PARAMETER)

        Returns:
            List of tokens as tuples: (line, char, length, token_type, modifiers)
        """
        # Ensure keyword mappings are loaded
        self._load_token_mappings()

        if (
            not self._translated_keywords
            and not self._translated_builtin_types
            and not self._translated_builtin_funcs
            and not self._translated_exceptions
        ):
            return []

        # After _load_token_mappings(), all sets are guaranteed non-None
        assert self._translated_keywords is not None
        assert self._translated_builtin_types is not None
        assert self._translated_builtin_funcs is not None
        assert self._translated_exceptions is not None
        assert self._reverse_keyword_map is not None

        tokens: list[tuple[int, int, int, int, int]] = []
        state = _STATE_NORMAL
        prev_op_is_dot = False  # Track '.' to suppress class/def on member access

        try:
            readline = io.BytesIO(self.document_text.encode("utf-8")).readline

            for tok in tokenize.tokenize(readline):
                if tok.type == tokenize.NAME:
                    # Context-aware classification via state machine
                    if state == _STATE_AFTER_CLASS:
                        # Class name following 'class'/'clase'
                        token_type = TOKEN_TYPE_CLASS
                        state = _STATE_NORMAL
                    elif state == _STATE_AFTER_DEF:
                        # Function name following 'def'/'definir'
                        token_type = TOKEN_TYPE_FUNCTION
                        state = _STATE_AFTER_FUNC_NAME
                    elif state == _STATE_EXPECT_FIRST_PARAM:
                        # First parameter (self/cls/propio)
                        token_type = TOKEN_TYPE_PARAMETER
                        state = _STATE_NORMAL
                    elif tok.string in self._translated_keywords:
                        token_type = TOKEN_TYPE_KEYWORD
                        english = self._reverse_keyword_map.get(tok.string)
                        # Only trigger class/def state on statement keywords,
                        # not member access (obj.clase) or assignment (clase = 1)
                        if english == "class" and not prev_op_is_dot:
                            state = _STATE_AFTER_CLASS
                        elif english == "def" and not prev_op_is_dot:
                            state = _STATE_AFTER_DEF
                        else:
                            state = _STATE_NORMAL
                    elif tok.string in self._translated_exceptions:
                        token_type = TOKEN_TYPE_CLASS
                        state = _STATE_NORMAL
                    elif tok.string in self._translated_builtin_types:
                        token_type = TOKEN_TYPE_CLASS
                        state = _STATE_NORMAL
                    elif tok.string in self._translated_builtin_funcs:
                        token_type = TOKEN_TYPE_FUNCTION
                        state = _STATE_NORMAL
                    else:
                        # Unrecognized identifier — keep AFTER_FUNC_NAME
                        # (waiting for '(') but reset other transitional states
                        if state != _STATE_AFTER_FUNC_NAME:
                            state = _STATE_NORMAL
                        continue

                    # LSP uses 0-based line numbers, tokenize uses 1-based
                    line = tok.start[0] - 1
                    char = tok.start[1]
                    length = len(tok.string)
                    tokens.append((line, char, length, token_type, 0))
                    prev_op_is_dot = False

                elif tok.type == tokenize.OP:
                    # OP tokens drive state transitions but are never emitted
                    if state == _STATE_AFTER_FUNC_NAME and tok.string == "(":
                        state = _STATE_EXPECT_FIRST_PARAM
                    elif state in (
                        _STATE_AFTER_CLASS,
                        _STATE_AFTER_DEF,
                        _STATE_EXPECT_FIRST_PARAM,
                    ):
                        state = _STATE_NORMAL
                    prev_op_is_dot = tok.string == "."
                else:
                    # NEWLINE, COMMENT, etc. — reset transitional states
                    # Keep AFTER_FUNC_NAME across NL/INDENT for line continuations
                    # like `def foo \\\n    (self): ...`
                    if state in (_STATE_AFTER_CLASS, _STATE_AFTER_DEF):
                        state = _STATE_NORMAL
                    elif state == _STATE_AFTER_FUNC_NAME and tok.type not in (
                        tokenize.NL,
                        tokenize.INDENT,
                    ):
                        state = _STATE_NORMAL

        except tokenize.TokenError as e:
            # Document has syntax errors - tokenize fails
            logger.debug(f"Tokenize error for {self.document_uri}: {e!r}")
            # Return partial tokens collected so far
            return tokens

        except Exception as e:
            logger.error(
                f"Unexpected error tokenizing document {self.document_uri}: {e!r}",
                exc_info=True,
            )
            return []

        return tokens

    def encode_tokens(self, tokens: list[tuple[int, int, int, int, int]]) -> list[int]:
        """Encode tokens in LSP delta format.

        LSP semantic tokens are encoded as a flat array of integers using delta encoding:
        [deltaLine, deltaChar, length, tokenType, tokenModifiers]

        Delta encoding means:
        - First token: absolute position
        - Subsequent tokens on same line: deltaLine=0, deltaChar=relative to previous
        - Subsequent tokens on new line: deltaLine=difference, deltaChar=absolute column

        Args:
            tokens: List of (line, char, length, token_type, modifiers) tuples

        Returns:
            Encoded token data as flat integer array

        Example:
            Input:  [(0, 0, 3, 0, 0), (0, 10, 5, 0, 0), (2, 4, 6, 0, 0)]
            Output: [0, 0, 3, 0, 0,  0, 10, 5, 0, 0,  2, 4, 6, 0, 0]
                     ^  ^  ^  ^  ^   ^   ^  ^  ^  ^   ^  ^  ^  ^  ^
                     |  |  |  |  |   |   |  |  |  |   |  |  |  |  |
                     L  C  L  T  M   ΔL  ΔC L  T  M   ΔL C  L  T  M
        """
        if not tokens:
            return []

        # Sort tokens by line, then by character position
        sorted_tokens = sorted(tokens, key=lambda t: (t[0], t[1]))

        encoded: list[int] = []
        prev_line = 0
        prev_char = 0

        for line, char, length, token_type, modifiers in sorted_tokens:
            # Calculate deltas
            delta_line = line - prev_line
            delta_char = char - prev_char if delta_line == 0 else char

            # Append encoded token (5 integers per token)
            encoded.extend([delta_line, delta_char, length, token_type, modifiers])

            # Update previous position
            prev_line = line
            prev_char = char

        return encoded
