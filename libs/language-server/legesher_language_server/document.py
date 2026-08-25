"""Document management for Language Server.

This module handles tracking open documents, their content, versions,
and cached translations.
"""

# Known gap — non-BMP offsets. The proportional interior mapping in
# source_map.py (SourceMap._map_to_translated / _map_to_original) measures
# positions in Python str characters, while LSP Position.character has no
# defined unit and clients commonly count UTF-16 code units. For non-BMP
# characters (emoji, astral CJK) the two disagree and offsets drift. The
# failing case is pinned by the xfail regression test
# tests/test_source_map_offset_gap.py, so the gap stays visible rather than
# being silently shipped; closing it means reworking the offset model.

from dataclasses import dataclass, field
from datetime import datetime


def split_lines_lsp(text: str) -> list[str]:
    r"""Split text into lines the way an LSP client counts them.

    The LSP spec (and every mainstream editor) treats only ``\n``, ``\r\n``,
    and a lone ``\r`` as line terminators. Python's ``str.splitlines()``
    additionally splits on Unicode line/paragraph separators (U+2028, U+2029),
    NEL (U+0085), vertical tab, form feed, and the file/group/record/unit
    separators (U+001C-U+001F). A single editor line containing a U+2028 would
    therefore become TWO Python lines, desyncing every line number the server
    returns. This splitter matches the editor.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized:
        return []
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


@dataclass
class DocumentState:
    """Tracks state of an open document.

    Attributes:
        uri: Document URI (e.g., 'file:///path/to/file.py')
        text: Current document content
        version: Document version number (incremented on each change)
        language_id: Language identifier (e.g., 'python')
        is_dirty: Whether document has unsaved changes
        translated_text: Cached translated content (None if not translated)
        last_modified: Timestamp of last modification
    """

    uri: str
    text: str
    version: int
    language_id: str
    is_dirty: bool = False
    translated_text: str | None = None
    last_modified: datetime = field(default_factory=datetime.now)

    def update(self, text: str, version: int) -> None:
        """Update document content and invalidate cache.

        Args:
            text: New document content
            version: New version number
        """
        self.text = text
        self.version = version
        self.is_dirty = True
        self.translated_text = None  # Invalidate translation cache
        self.last_modified = datetime.now()

    def set_translation(self, translated: str) -> None:
        """Cache translated content.

        Args:
            translated: Translated document content
        """
        self.translated_text = translated
        self.is_dirty = False

    def get_line_count(self) -> int:
        """Get number of lines in document.

        Returns:
            Number of lines
        """
        return len(split_lines_lsp(self.text))

    def get_line(self, line_number: int) -> str | None:
        """Get specific line from document.

        Args:
            line_number: Line number (0-indexed)

        Returns:
            Line content or None if line doesn't exist
        """
        lines = split_lines_lsp(self.text)
        if 0 <= line_number < len(lines):
            return lines[line_number]
        return None


class DocumentManager:
    """Manages open documents and their state.

    This class tracks all documents currently open in the editor,
    manages their versions, and handles caching of translations.
    """

    def __init__(self) -> None:
        """Initialize document manager."""
        self._documents: dict[str, DocumentState] = {}

    def open_document(self, uri: str, text: str, version: int, language_id: str) -> DocumentState:
        """Register a newly opened document.

        Args:
            uri: Document URI
            text: Initial document content
            version: Initial version number
            language_id: Language identifier

        Returns:
            Created DocumentState
        """
        doc = DocumentState(uri=uri, text=text, version=version, language_id=language_id)
        self._documents[uri] = doc
        return doc

    def update_document(self, uri: str, text: str, version: int) -> DocumentState | None:
        """Update an existing document.

        Args:
            uri: Document URI
            text: New document content
            version: New version number

        Returns:
            Updated DocumentState or None if document not found
        """
        if uri not in self._documents:
            return None

        self._documents[uri].update(text, version)
        return self._documents[uri]

    def close_document(self, uri: str) -> None:
        """Remove a document from tracking.

        Args:
            uri: Document URI to close
        """
        self._documents.pop(uri, None)

    def get_document(self, uri: str) -> DocumentState | None:
        """Retrieve document by URI.

        Args:
            uri: Document URI

        Returns:
            DocumentState or None if not found
        """
        return self._documents.get(uri)

    def get_all_documents(self) -> list[DocumentState]:
        """Get all open documents.

        Returns:
            List of all DocumentState objects
        """
        return list(self._documents.values())

    def get_document_count(self) -> int:
        """Get number of open documents.

        Returns:
            Count of open documents
        """
        return len(self._documents)

    def has_document(self, uri: str) -> bool:
        """Check if document is tracked.

        Args:
            uri: Document URI

        Returns:
            True if document exists
        """
        return uri in self._documents
