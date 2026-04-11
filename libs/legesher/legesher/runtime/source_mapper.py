"""Source mapping engine for preserving line numbers and debugging context.

This module maintains bidirectional mappings between:
- Native language source code (Spanish, Arabic, etc.)
- English source code (for Python runtime)
- Python bytecode (executable form)

This enables:
- Accurate error line numbers in native language
- Debugger support showing native code
- Stack traces in user's language
"""

from dataclasses import dataclass


@dataclass
class SourceMapping:
    """Mapping between native and English source code.

    Attributes:
        native_file: Path to native language source file
        native_line: Line number in native source
        english_line: Line number in English source
        native_code: Native language code line
        english_code: English code line
    """

    native_file: str
    native_line: int
    english_line: int
    native_code: str
    english_code: str


class LegesherSourceMapper:
    """Manages source code mappings for error reporting.

    This class maintains bidirectional mappings between native language
    source code and English source code, enabling accurate error reporting
    with correct line numbers in the user's native language.
    """

    def __init__(self):
        """Initialize the source mapper with empty mappings."""
        # Map: (filename, english_line) -> native_line
        self._mappings: dict[tuple[str, int], int] = {}
        # Map: filename -> native_source
        self._native_sources: dict[str, str] = {}

    def register_mapping(self, filename: str, native_source: str, english_source: str):
        """Register a source mapping for a file.

        This creates a bidirectional mapping between native language source
        and English source, enabling accurate error reporting.

        Args:
            filename: Original file path
            native_source: Source code in native language
            english_source: Translated English source code
        """
        self._native_sources[filename] = native_source

        # Create line-by-line mapping
        # For MVP: Simple 1:1 mapping (line N in native = line N in English)
        # TODO: Future enhancement with AST-based structural matching
        native_lines = native_source.splitlines()
        english_lines = english_source.splitlines()

        for eng_line_no in range(1, len(english_lines) + 1):
            # Simple 1:1 mapping for MVP
            nat_line_no = eng_line_no
            if nat_line_no <= len(native_lines):
                self._mappings[(filename, eng_line_no)] = nat_line_no

    def get_native_line(self, filename: str, english_line: int) -> int | None:
        """Get native language line number from English line number.

        Args:
            filename: Source file path
            english_line: Line number in English source

        Returns:
            Line number in native source, or None if not found
        """
        return self._mappings.get((filename, english_line))

    def get_native_source_line(self, filename: str, line_no: int) -> str | None:
        """Get native source code line.

        Args:
            filename: Source file path
            line_no: Line number to retrieve

        Returns:
            Native source code line, or None if not found
        """
        if filename in self._native_sources:
            lines = self._native_sources[filename].splitlines()
            if 0 < line_no <= len(lines):
                return lines[line_no - 1]
        return None

    def has_mapping(self, filename: str) -> bool:
        """Check if a mapping exists for the given file.

        Args:
            filename: Source file path

        Returns:
            True if mapping exists, False otherwise
        """
        return filename in self._native_sources

    def clear(self):
        """Clear all mappings.

        This is useful for testing or when resetting the runtime state.
        """
        self._mappings.clear()
        self._native_sources.clear()

    def clear_all(self):
        """Clear all mappings (alias for clear()).

        This is useful for testing or when resetting the runtime state.
        """
        self.clear()

    def clear_mapping(self, filename: str):
        """Clear mapping for a specific file.

        Args:
            filename: Source file path to clear
        """
        if filename in self._native_sources:
            del self._native_sources[filename]
            # Remove all line mappings for this file
            keys_to_remove = [key for key in self._mappings if key[0] == filename]
            for key in keys_to_remove:
                del self._mappings[key]

    def get_mapped_files(self) -> list:
        """Get list of all files with registered mappings.

        Returns:
            List of file paths that have mappings
        """
        return list(self._native_sources.keys())

    def get_line_count(self, filename: str) -> int | None:
        """Get the number of lines in the native source file.

        Args:
            filename: Source file path

        Returns:
            Number of lines in native source, or None if not found
        """
        if filename in self._native_sources:
            return len(self._native_sources[filename].splitlines())
        return None


# Global mapper instance
_source_mapper = LegesherSourceMapper()


def get_source_mapper() -> LegesherSourceMapper:
    """Get global source mapper instance.

    Returns:
        Global LegesherSourceMapper instance
    """
    return _source_mapper


def reset_source_mapper():
    """Reset the global source mapper instance.

    This creates a new mapper instance, discarding all previous mappings.
    Primarily useful for testing.
    """
    global _source_mapper
    _source_mapper = LegesherSourceMapper()
