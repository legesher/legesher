"""Native language error handling and traceback translation.

This module intercepts Python exceptions and translates them to
the user's native language, providing a truly localized debugging experience.

Example:
    Instead of:
        NameError: name 'x' is not defined

    Spanish users see:
        NameError: name 'x' is not defined
        (with native source code lines in the traceback)
"""

import sys
import traceback

from legesher.config import LegesherConfig
from legesher.runtime.source_mapper import get_source_mapper
from legesher_core import TokenTranslator


class LegesherErrorHandler:
    """Translates Python exceptions to native language.

    This handler intercepts Python exceptions and formats them with
    native language source code lines and (future) translated error messages.
    """

    def __init__(self, language: str):
        """Initialize the error handler.

        Args:
            language: Target language code (e.g., 'es', 'ar', 'zh')
        """
        self.language = language
        self.translator = TokenTranslator.from_language_pack(language)
        self.source_mapper = get_source_mapper()

        # Load translations (for future enhancement)
        self.exception_names = self._load_exception_translations()
        self.message_templates = self._load_message_templates()

    def _load_exception_translations(self) -> dict[str, str]:
        """Load exception type name translations.

        TODO: Add exception names to language packs in future
        For MVP: Return empty dict (use English names)

        Returns:
            Dictionary mapping English exception names to native names
        """
        return {}

    def _load_message_templates(self) -> dict[str, str]:
        """Load error message templates for common errors.

        TODO: Add message templates to language packs
        For MVP: Return empty dict (use English messages)

        Examples:
            "name '{name}' is not defined" -> "el nombre '{name}' no está definido"

        Returns:
            Dictionary mapping English message patterns to native templates
        """
        return {}

    def format_exception(self, exc_type, exc_value, exc_traceback):
        """Format exception with native language messages and source lines.

        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_traceback: Traceback object

        Returns:
            Formatted exception string with native source lines
        """
        # Translate exception type name (future enhancement)
        type_name = self.exception_names.get(exc_type.__name__, exc_type.__name__)

        # Translate error message (future enhancement)
        message = self._translate_message(str(exc_value))

        # Format traceback with native source lines
        tb_lines = []
        tb_lines.append("Traceback (most recent call last):\n")

        for frame_summary in traceback.extract_tb(exc_traceback):
            filename = frame_summary.filename
            lineno = frame_summary.lineno
            name = frame_summary.name
            line = frame_summary.line

            # Try to get native source line if available
            if self.source_mapper.has_mapping(filename):
                native_line_no = self.source_mapper.get_native_line(filename, lineno)
                native_line = self.source_mapper.get_native_source_line(
                    filename, native_line_no or lineno
                )

                # Use native line number and source if available
                display_lineno = native_line_no or lineno
                display_line = native_line or line
            else:
                # No mapping - use original
                display_lineno = lineno
                display_line = line

            # Format frame
            tb_lines.append(f'  File "{filename}", line {display_lineno}, in {name}\n')
            if display_line:
                tb_lines.append(f"    {display_line.strip()}\n")

        # Add exception message
        tb_lines.append(f"{type_name}: {message}\n")

        return "".join(tb_lines)

    def _translate_message(self, message: str) -> str:
        """Translate error message to native language.

        TODO: Use message templates and NLP for better translation
        For MVP: Keep English message

        Args:
            message: Error message in English

        Returns:
            Translated error message (currently returns English)
        """
        return message


def install_error_handler(language: str | None = None):
    """Install native language exception handler.

    This replaces sys.excepthook with a custom handler that shows
    native language source code in tracebacks.

    Args:
        language: Target language code (default: auto-detect from config)

    Returns:
        LegesherErrorHandler instance that was installed

    Example:
        >>> install_error_handler("es")
        >>> 1 / 0  # Error shown with Spanish source lines!
    """
    if language is None:
        config = LegesherConfig.load()
        language = config.language

    handler = LegesherErrorHandler(language)

    def excepthook(exc_type, exc_value, exc_traceback):
        """Custom exception hook showing native language errors."""
        formatted = handler.format_exception(exc_type, exc_value, exc_traceback)
        sys.stderr.write(formatted)

    sys.excepthook = excepthook
    return handler
