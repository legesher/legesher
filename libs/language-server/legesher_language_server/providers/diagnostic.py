"""Diagnostic provider for translated error messages.

The document is parsed with ``ast.parse``, so what this reports is what a
parse can detect: SyntaxError, IndentationError, TabError, and decoding
failures. Nothing here executes the code, so runtime errors (NameError,
TypeError) never reach it; those come from the external type-aware server
when one is configured.

Message text is drawn from templates written for English, Spanish, and
Arabic. For other languages the message is left in English.
"""

import ast
import io
import re
import tokenize
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import LegesherLanguageServer

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)

from ..utils.error_templates import ErrorMessageTemplates

# Module-level cache for translated error messages
# Key: (error_type, message, target_lang)
# Value: translated message string
_error_message_cache: dict[tuple[str, str, str], str] = {}

# Error templates constant for inline templates (used before ErrorMessageTemplates)
ERROR_TEMPLATES = {
    "SyntaxError": {
        "en": {"invalid_syntax": "invalid syntax", "expected_colon": "expected ':'"},
        "es": {"invalid_syntax": "sintaxis inválida", "expected_colon": "se esperaba ':'"},
        "ar": {"invalid_syntax": "بناء جملة غير صالح", "expected_colon": "متوقع ':'"},
    },
    "IndentationError": {
        "en": {
            "unexpected_indent": "unexpected indent",
            "expected_indent": "expected an indented block",
        },
        "es": {
            "unexpected_indent": "indentación inesperada",
            "expected_indent": "se esperaba un bloque indentado",
        },
        "ar": {
            "unexpected_indent": "مسافة بادئة غير متوقعة",
            "expected_indent": "متوقع كتلة ذات مسافة بادئة",
        },
    },
    "NameError": {
        "en": {"not_defined": "name '{var}' is not defined"},
        "es": {"not_defined": "el nombre '{var}' no está definido"},
        "ar": {"not_defined": "الاسم '{var}' غير معرف"},
    },
    "TypeError": {
        "en": {"not_callable": "'{var}' object is not callable"},
        "es": {"not_callable": "el objeto '{var}' no es invocable"},
        "ar": {"not_callable": "الكائن '{var}' غير قابل للاستدعاء"},
    },
}


async def provide_diagnostics(server: "LegesherLanguageServer", uri: str) -> list[Diagnostic]:
    """Provide diagnostics for document.

    Args:
        server: Language server instance
        uri: Document URI

    Returns:
        List of translated diagnostics

    Reports what parsing the document detects — SyntaxError and its kin — with
    the message rendered from a template in the configured target language
    where one exists, and left in English otherwise. Variable names and code
    structure are never rewritten. Returns an empty list when the document is
    not open or parses cleanly.
    """
    # Get document
    doc = server.document_manager.get_document(uri)
    if not doc:
        return []

    # Create provider instance
    provider = DiagnosticProvider(
        source_lang=server.config.source_language,
        target_lang=server.config.target_language,
        document_text=doc.text,
        document_uri=uri,
    )

    # Get diagnostics
    return await provider.get_diagnostics()


class DiagnosticProvider:
    """Provides translated Python diagnostics."""

    def __init__(
        self,
        source_lang: str,
        target_lang: str,
        document_text: str,
        document_uri: str,
    ):
        """Initialize diagnostic provider.

        Args:
            source_lang: Source language code (e.g., "en")
            target_lang: Target language code (e.g., "es", "ar")
            document_text: Document content
            document_uri: Document URI
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.document_text = document_text
        self.document_uri = document_uri
        self.error_templates = ErrorMessageTemplates()

        # Load keyword translation map for translating code before parsing
        self._keyword_translation_map = self._load_keyword_translations()

    def _load_keyword_translations(self) -> dict[str, str]:
        """Load keyword translation map (target language -> English).

        Returns:
            Dictionary mapping translated keywords to English keywords
            Example: {"definir": "def", "devolver": "return", ...}
        """
        import logging

        logger = logging.getLogger(__name__)

        keyword_map = {}

        # Only load translations if target language is not English
        if self.target_lang == "en":
            return keyword_map

        try:
            from legesher_i18n import LanguagePackLoader

            loader = LanguagePackLoader()
            pack = loader.load(language=self.target_lang, target="python", version="3.10")

            # Build reverse map: Spanish/Arabic/etc -> English
            for english, translated in pack.keywords.items():
                keyword_map[translated] = english

            logger.debug(
                f"Loaded {len(keyword_map)} keyword translations for diagnostic provider "
                f"(lang={self.target_lang})"
            )

        except Exception as e:
            # If loading fails, return empty dict (diagnostics will fail for non-English code)
            logger.warning(f"Failed to load keyword translations for diagnostics: {e}")

        return keyword_map

    def _translate_code_to_english(self, code: str) -> str:
        """Translate code from target language to English for parsing.

        Uses Python's tokenizer to only replace NAME tokens, avoiding false
        positives on variable names, string contents, and comments.

        Args:
            code: Source code in target language

        Returns:
            Code translated to English
        """
        if not self._keyword_translation_map:
            return code

        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            # Incomplete/invalid code — fall back to regex for best-effort
            return self._translate_code_to_english_regex(code)

        # Collect replacements: (line, col_start, col_end, replacement)
        # Then apply in reverse order to preserve offsets
        lines = code.split("\n")
        replacements: list[tuple[int, int, int, str]] = []

        for tok in tokens:
            if tok.type == tokenize.NAME and tok.string in self._keyword_translation_map:
                row = tok.start[0] - 1  # Convert to 0-based
                col_start = tok.start[1]
                col_end = tok.end[1]
                replacements.append(
                    (row, col_start, col_end, self._keyword_translation_map[tok.string])
                )

        # Apply replacements in reverse order (right-to-left, bottom-to-top)
        for row, col_start, col_end, replacement in reversed(replacements):
            line = lines[row]
            lines[row] = line[:col_start] + replacement + line[col_end:]

        return "\n".join(lines)

    def _translate_code_to_english_regex(self, code: str) -> str:
        r"""Fallback regex-based translation for untokenizable code.

        Note: \b word boundaries only match ASCII word characters, so this
        fallback will silently skip non-Latin keywords (Arabic, Hebrew, etc.).
        The tokenizer-first approach in _translate_code_to_english handles
        all scripts correctly. This fallback is best-effort for broken code.
        """
        translated = code
        # Sort by length descending to avoid partial matches
        for target_keyword, english_keyword in sorted(
            self._keyword_translation_map.items(), key=lambda x: len(x[0]), reverse=True
        ):
            pattern = r"\b" + re.escape(target_keyword) + r"\b"
            translated = re.sub(pattern, english_keyword, translated)
        return translated

    async def get_diagnostics(self) -> list[Diagnostic]:
        """Get all diagnostics for document.

        Returns:
            List of diagnostics with translated messages
        """
        diagnostics = []

        # Parse for syntax errors
        syntax_errors = self._parse_syntax_errors()
        for error in syntax_errors:
            diag = await self._create_diagnostic(error)
            diagnostics.append(diag)

        return diagnostics

    def _parse_syntax_errors(self) -> list[dict]:
        """Parse document for syntax errors.

        Returns:
            List of error dictionaries with type, message, position, severity
        """
        errors = []

        # Translate code to English before parsing if needed
        code_to_parse = self._translate_code_to_english(self.document_text)

        try:
            ast.parse(code_to_parse)
        except SyntaxError as e:
            errors.append(
                {
                    "type": "SyntaxError",
                    "message": str(e.msg) if e.msg else "invalid syntax",
                    "line": (e.lineno or 1) - 1,  # LSP is 0-indexed
                    "column": e.offset or 0,
                    "severity": DiagnosticSeverity.Error,
                    "end_line": (e.end_lineno or e.lineno or 1) - 1,
                    "end_column": e.end_offset or (e.offset or 0) + 1,
                }
            )
        except IndentationError as e:
            errors.append(
                {
                    "type": "IndentationError",
                    "message": str(e.msg) if e.msg else "unexpected indent",
                    "line": (e.lineno or 1) - 1,
                    "column": e.offset or 0,
                    "severity": DiagnosticSeverity.Error,
                    "end_line": (e.end_lineno or e.lineno or 1) - 1,
                    "end_column": e.end_offset or (e.offset or 0) + 1,
                }
            )
        except TabError as e:
            errors.append(
                {
                    "type": "TabError",
                    "message": str(e.msg) if e.msg else "inconsistent use of tabs and spaces",
                    "line": (e.lineno or 1) - 1,
                    "column": e.offset or 0,
                    "severity": DiagnosticSeverity.Error,
                    "end_line": (e.end_lineno or e.lineno or 1) - 1,
                    "end_column": e.end_offset or (e.offset or 0) + 1,
                }
            )
        except UnicodeDecodeError as e:
            errors.append(
                {
                    "type": "UnicodeDecodeError",
                    "message": f"'{e.encoding}' codec can't decode byte {hex(e.start)}",
                    "line": 0,
                    "column": 0,
                    "severity": DiagnosticSeverity.Error,
                    "end_line": 0,
                    "end_column": 1,
                }
            )
        except Exception as e:
            # Catch-all for other parsing errors
            errors.append(
                {
                    "type": type(e).__name__,
                    "message": str(e),
                    "line": 0,
                    "column": 0,
                    "severity": DiagnosticSeverity.Error,
                    "end_line": 0,
                    "end_column": 1,
                }
            )

        return errors

    async def _create_diagnostic(self, error: dict) -> Diagnostic:
        """Create LSP Diagnostic from error dict.

        Args:
            error: Error dictionary with type, message, position

        Returns:
            LSP Diagnostic with translated message
        """
        # Translate the error message
        translated_message = await self._translate_error_message(error["type"], error["message"])

        # Ensure valid range (clamp negative values)
        start_line = max(0, error["line"])
        start_col = max(0, error["column"])
        end_line = max(start_line, error.get("end_line", error["line"]))
        end_col = max(start_col + 1, error.get("end_column", error["column"] + 1))

        return Diagnostic(
            range=Range(
                start=Position(line=start_line, character=start_col),
                end=Position(line=end_line, character=end_col),
            ),
            message=translated_message,
            severity=error["severity"],
            source="legesher-lsp",
        )

    async def _translate_error_message(self, error_type: str, message: str) -> str:
        """Translate error message with caching and variable preservation.

        Args:
            error_type: Type of error (e.g., "SyntaxError")
            message: Original error message

        Returns:
            Translated error message with preserved variables
        """
        # Check cache first
        cache_key = (error_type, message, self.target_lang)
        if cache_key in _error_message_cache:
            return _error_message_cache[cache_key]

        # Extract variables from message
        variables = self._extract_variables(message)

        # Get translation from templates
        translation = self._get_translation_template(error_type, variables)

        # Fallback to English if no translation
        if not translation:
            translation = message

        # Cache the result
        _error_message_cache[cache_key] = translation

        return translation

    def _get_translation_template(self, error_type: str, variables: dict[str, str]) -> str | None:
        """Get translation template and substitute variables.

        Args:
            error_type: Type of error
            variables: Variables to substitute

        Returns:
            Translated message or None if not found
        """
        # Try to get from ErrorMessageTemplates first
        if error_type in ["NameError", "TypeError", "AttributeError"]:
            # These need variable substitution
            template_key = self._match_template_key(error_type, variables.get("message", ""))
            if template_key:
                translation = self.error_templates.get_translation(
                    error_type, template_key, self.target_lang, **variables
                )
                if translation:
                    return translation

        # Fall back to inline ERROR_TEMPLATES
        if error_type in ERROR_TEMPLATES:
            # Try target language first
            lang_templates = ERROR_TEMPLATES[error_type].get(self.target_lang)

            # If target language not found, fall back to English
            if not lang_templates:
                lang_templates = ERROR_TEMPLATES[error_type].get("en", {})

            # Find matching template
            for template_key, template in lang_templates.items():
                try:
                    return template.format_map(variables)
                except (KeyError, ValueError):
                    # Template doesn't match or missing variables
                    continue

        return None

    def _match_template_key(self, error_type: str, message: str) -> str | None:
        """Match error message to template key.

        Args:
            error_type: Type of error
            message: Error message

        Returns:
            Template key or None
        """
        message_lower = message.lower()

        if error_type == "NameError":
            if "not defined" in message_lower:
                return "not_defined"
        elif error_type == "TypeError":
            if "not callable" in message_lower:
                return "not_callable"
        elif error_type == "AttributeError":
            if "has no attribute" in message_lower:
                return "no_attribute"

        return None

    def _extract_variables(self, message: str) -> dict[str, str]:
        """Extract variable names and values from error message.

        Args:
            message: Error message

        Returns:
            Dictionary of variable names to values
        """
        variables = {}

        # Always include the full message for fallback (truncate long messages)
        if len(message) > 100:
            variables["message"] = message[:97] + "..."
        else:
            variables["message"] = message

        # Pattern for quoted strings (variable names)
        # Matches 'varname' or "varname"
        pattern = r"['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, message)

        if matches:
            variables["var"] = matches[0]

            # Check for "No module named 'X'" pattern
            if "no module named" in message.lower():
                variables["module"] = matches[0]
            elif len(matches) > 1:
                # Check if it's "from 'module'" pattern (ImportError)
                if "from" in message.lower():
                    variables["module"] = matches[1]
                else:
                    variables["attr"] = matches[1]
            if len(matches) > 2:
                variables["module"] = matches[2]

        # Pattern for numbers (for argument counts, etc.)
        number_pattern = r"\b(\d+)\b"
        numbers = re.findall(number_pattern, message)
        if numbers:
            if "expected" not in variables and len(numbers) > 0:
                variables["expected"] = numbers[0]
            if "actual" not in variables and len(numbers) > 1:
                variables["actual"] = numbers[1]

        return variables

    def _get_error_position_context(self, line: int, column: int) -> str:
        """Get context around error position.

        Args:
            line: Line number (0-indexed)
            column: Column number

        Returns:
            Context string showing lines around error with marker
        """
        lines = self.document_text.split("\n")
        if line < 0 or line >= len(lines):
            return ""

        context_lines = []

        # Show 2 lines before and after
        start = max(0, line - 2)
        end = min(len(lines), line + 3)

        for i in range(start, end):
            context_lines.append(f"{i + 1:4d} | {lines[i]}")
            if i == line:
                # Add error marker
                marker = " " * (7 + column) + "^"
                context_lines.append(marker)

        return "\n".join(context_lines)
