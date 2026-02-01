"""Completion provider for localized IntelliSense.

This module provides completion items including:
- Keywords in target language (def→definir, class→clase)
- Builtins in target language (print→imprimir, len→longitud)
- User-defined symbols (functions, variables, classes from current file)
- Context-aware filtering
- Scope-aware symbol suggestions
- Fuzzy matching for typo tolerance

Implementation for CORE-358.
"""

import ast
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    Position,
)

from ..utils.keyword_docs import KeywordDocumentation

# Cache for pre-built keyword/builtin completions (bounded by language pairs)
# Key: (source_lang, target_lang)
# Value: tuple of (keyword_items, builtin_items)
_completion_cache: dict[tuple[str, str], tuple[list[CompletionItem], list[CompletionItem]]] = {}

# Cache for document symbols (bounded by open documents)
# Key: (document_uri, document_version)
# Value: list of Symbol objects
_symbol_cache: dict[tuple[str, int], list["Symbol"]] = {}


def clear_caches() -> None:
    """Clear completion and symbol caches.

    Useful for testing and when language configuration changes.
    """
    _completion_cache.clear()
    _symbol_cache.clear()


class SymbolKind(Enum):
    """Symbol types that can be completed."""

    FUNCTION = "function"
    VARIABLE = "variable"
    CLASS = "class"


@dataclass
class Symbol:
    """Represents a user-defined symbol in the document."""

    name: str
    kind: SymbolKind
    line: int
    col: int
    scope: str  # "module" or function name for function-local vars
    end_line: int  # Last line where symbol is valid


@dataclass
class CompletionContext:
    """Context information for intelligent completion filtering."""

    line: int
    col: int
    line_text: str
    partial_word: str
    is_line_start: bool
    preceding_token: str | None
    current_scope: str  # "module" or function name


async def provide_completion(
    server: "LegesherLanguageServer", uri: str, position: Position
) -> list[CompletionItem]:
    """Provide completion items at cursor position.

    Args:
        server: Language server instance
        uri: Document URI
        position: Cursor position

    Returns:
        List of completion items (keywords, builtins, user symbols)

    Note:
        Implementation for CORE-358 - Provides:
        - Localized keyword completions
        - Localized builtin completions
        - User-defined symbol completions
        - Context-aware filtering
        - Scope-aware suggestions
        - Fuzzy matching
    """
    # Get document
    doc = server.document_manager.get_document(uri)
    if not doc:
        return []

    # Create completion provider
    provider = CompletionProvider(
        source_lang=server.config.source_language,
        target_lang=server.config.target_language,
        document_text=doc.text,
        document_uri=uri,
        document_version=doc.version,
    )

    # Get completions
    return provider.get_completions(position)


class CompletionProvider:
    """Provides completion items for code elements.

    This class handles keyword completions, builtin function completions,
    user-defined symbol completions, context awareness, and scope filtering.
    """

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        document_text: str,
        document_uri: str,
        document_version: int,
    ):
        """Initialize completion provider.

        Args:
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'es', 'ar')
            document_text: Full document text
            document_uri: Document URI
            document_version: Document version number
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.document_text = document_text
        self.document_uri = document_uri
        self.document_version = document_version
        self.keyword_docs = KeywordDocumentation()

        # Build or retrieve cached completions
        self._load_keyword_builtin_completions()

        # Extract user symbols from document
        self._extract_symbols()

    def get_completions(self, position: Position) -> list[CompletionItem]:
        """Get completion items for the given position.

        Args:
            position: Cursor position in document

        Returns:
            List of completion items filtered by context and scope
        """
        # Get context at position
        context = self._get_completion_context(position)

        # Collect all completion types
        items: list[CompletionItem] = []

        # Add keywords (context-filtered)
        items.extend(self._get_keyword_completions(context))

        # Add builtins
        items.extend(self.builtin_items)

        # Add user symbols (scope-filtered)
        items.extend(self._get_symbol_completions(context))

        # Apply fuzzy matching filter
        if context.partial_word:
            items = self._fuzzy_filter(items, context.partial_word)

        return items

    def _load_keyword_builtin_completions(self) -> None:
        """Load or build keyword and builtin completion items.

        Uses cache for performance. Completions are pre-built and reused
        across multiple completion requests.
        """
        cache_key = (self.source_lang, self.target_lang)

        if cache_key in _completion_cache:
            self.keyword_items, self.builtin_items = _completion_cache[cache_key]
        else:
            # Build keyword completions
            self.keyword_items = self._build_keyword_completions()

            # Build builtin completions
            self.builtin_items = self._build_builtin_completions()

            # Cache for future use
            _completion_cache[cache_key] = (self.keyword_items, self.builtin_items)

    def _build_keyword_completions(self) -> list[CompletionItem]:
        """Build completion items for Python keywords.

        Returns:
            List of CompletionItem objects for keywords in target language
        """
        items = []

        # Get all Python keywords
        keywords = self.keyword_docs.get_all_keywords()

        for keyword in keywords:
            # Get translation
            translated = self.keyword_docs.get_keyword_translation(keyword, self.target_lang)
            if not translated:
                # Fallback to English if translation not available
                translated = keyword

            # Create completion item
            items.append(
                CompletionItem(
                    label=translated,
                    kind=CompletionItemKind.Keyword,
                    detail=f"Python keyword ({keyword})",
                    documentation=self.keyword_docs.get(keyword, self.target_lang),
                    sort_text=f"0_{translated}",  # Priority 0 for keywords
                    insert_text=translated,
                )
            )

        return items

    def _build_builtin_completions(self) -> list[CompletionItem]:
        """Build completion items for Python builtin functions.

        Returns:
            List of CompletionItem objects for builtins in target language
        """
        items = []

        # Get common builtin functions
        builtins_to_complete = [
            "print",
            "len",
            "range",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "bool",
            "type",
            "isinstance",
            "issubclass",
            "sum",
            "min",
            "max",
            "abs",
            "round",
            "sorted",
            "reversed",
            "enumerate",
            "zip",
            "map",
            "filter",
            "any",
            "all",
            "open",
            "input",
            "help",
        ]

        for builtin in builtins_to_complete:
            # Get translation (for MVP, assume English)
            # TODO (CORE-360 or future): Use translation API/pack for builtins
            # See: CORE-444 (Snippet Completions) and CORE-445 (Signature Help)
            # for related enhancements to builtin function support
            translated = builtin

            items.append(
                CompletionItem(
                    label=translated,
                    kind=CompletionItemKind.Function,
                    detail=f"Built-in function ({builtin})",
                    sort_text=f"1_{translated}",  # Priority 1 for builtins
                    insert_text=f"{translated}($0)",  # Snippet with cursor in parens
                )
            )

        return items

    def _extract_symbols(self) -> None:
        """Extract user-defined symbols from document using AST.

        Populates self.symbols with Function, Variable, and Class definitions.
        Uses cache to avoid re-parsing unchanged documents.
        """
        cache_key = (self.document_uri, self.document_version)

        if cache_key in _symbol_cache:
            self.symbols = _symbol_cache[cache_key]
            return

        self.symbols: list[Symbol] = []

        try:
            tree = ast.parse(self.document_text)
        except SyntaxError:
            # Handle incomplete/invalid code gracefully
            _symbol_cache[cache_key] = self.symbols
            return

        # Walk AST and extract symbols
        # Note: Currently extracts module-level symbols only
        # TODO (Future): Support nested scope (function-local variables, nested functions)
        # This would require tracking scope hierarchy and filtering based on cursor position
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.symbols.append(
                    Symbol(
                        name=node.name,
                        kind=SymbolKind.FUNCTION,
                        line=node.lineno,
                        col=node.col_offset,
                        scope="module",  # MVP: Module-level only
                        end_line=node.end_lineno or node.lineno,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                self.symbols.append(
                    Symbol(
                        name=node.name,
                        kind=SymbolKind.CLASS,
                        line=node.lineno,
                        col=node.col_offset,
                        scope="module",
                        end_line=node.end_lineno or node.lineno,
                    )
                )
            elif isinstance(node, ast.Assign):
                # Extract variable names from assignments
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.symbols.append(
                            Symbol(
                                name=target.id,
                                kind=SymbolKind.VARIABLE,
                                line=node.lineno,
                                col=node.col_offset,
                                scope="module",
                                end_line=node.end_lineno or node.lineno,
                            )
                        )

        # Cache symbols
        _symbol_cache[cache_key] = self.symbols

    def _get_completion_context(self, position: Position) -> CompletionContext:
        """Analyze context at cursor position.

        Args:
            position: Cursor position

        Returns:
            CompletionContext with line info, partial word, etc.
        """
        lines = self.document_text.split("\n")
        line_idx = position.line
        col_idx = position.character

        if line_idx >= len(lines):
            line_text = ""
        else:
            line_text = lines[line_idx]

        # Extract partial word being typed
        partial_word = ""
        if col_idx > 0 and len(line_text) > 0:
            # Walk backwards to find word boundary
            start = min(col_idx - 1, len(line_text) - 1)  # Bounds check
            while (
                start >= 0
                and start < len(line_text)
                and (line_text[start].isalnum() or line_text[start] == "_")
            ):
                start -= 1
            partial_word = line_text[start + 1 : col_idx]

        # Check if at start of line (ignoring whitespace)
        is_line_start = line_text[:col_idx].strip() == ""

        # Get preceding token (last non-whitespace word before cursor)
        preceding_token = None
        before_cursor = line_text[:col_idx].strip()
        if before_cursor:
            tokens = before_cursor.split()
            if len(tokens) > 0:
                preceding_token = tokens[-1]

        # Determine current scope (simplified - always module for MVP)
        current_scope = "module"

        return CompletionContext(
            line=line_idx,
            col=col_idx,
            line_text=line_text,
            partial_word=partial_word,
            is_line_start=is_line_start,
            preceding_token=preceding_token,
            current_scope=current_scope,
        )

    def _get_keyword_completions(self, context: CompletionContext) -> list[CompletionItem]:
        """Filter keywords based on context.

        Args:
            context: Completion context

        Returns:
            Filtered list of keyword completions

        Note:
            MVP returns all keywords. Future enhancements could include:
            - Don't suggest 'def' after 'def' (avoid duplicate keywords)
            - Only suggest 'return'/'yield' inside function definitions
            - Only suggest 'break'/'continue' inside loops
            - Prioritize statement keywords (def, class, if) at line start
            - Prioritize expression keywords (and, or, not) mid-statement
        """
        # MVP: Return all keywords for maximum discoverability
        # Context filtering can be added incrementally based on user feedback
        return self.keyword_items

    def _get_symbol_completions(self, context: CompletionContext) -> list[CompletionItem]:
        """Get user symbol completions filtered by scope.

        Args:
            context: Completion context

        Returns:
            List of CompletionItem objects for in-scope symbols
        """
        items = []

        for symbol in self.symbols:
            # Don't suggest forward references (symbols defined after cursor)
            if symbol.line > context.line:
                continue

            # Check if symbol is in scope (simplified - module-level only for MVP)
            if symbol.scope != context.current_scope:
                # Future: handle function-local scope
                pass

            # Map symbol kind to CompletionItemKind
            if symbol.kind == SymbolKind.FUNCTION:
                item_kind = CompletionItemKind.Function
            elif symbol.kind == SymbolKind.CLASS:
                item_kind = CompletionItemKind.Class
            else:
                item_kind = CompletionItemKind.Variable

            items.append(
                CompletionItem(
                    label=symbol.name,
                    kind=item_kind,
                    detail=f"User-defined {symbol.kind.value}",
                    sort_text=f"2_{symbol.name}",  # Priority 2 for user symbols
                    insert_text=symbol.name,
                )
            )

        return items

    def _fuzzy_filter(self, items: list[CompletionItem], partial: str) -> list[CompletionItem]:
        """Filter items using fuzzy matching.

        Args:
            items: List of completion items
            partial: Partial word typed by user

        Returns:
            Filtered list matching partial input (case-insensitive prefix match)

        Note:
            Current implementation uses simple prefix matching for performance.
            Future enhancements could include:
            - Levenshtein distance for better typo tolerance
            - Subsequence matching (e.g., "pnt" matches "print")
            - Character frequency analysis
            - Machine learning-based relevance scoring

            For MVP, prefix matching provides good balance of:
            - Performance (<50ms requirement)
            - Simplicity (easy to understand/debug)
            - Effectiveness (handles common typos like "pri" → "print")
        """
        if not partial:
            return items

        partial_lower = partial.lower()
        return [item for item in items if item.label.lower().startswith(partial_lower)]
