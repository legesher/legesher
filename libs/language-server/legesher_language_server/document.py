"""Document management for Language Server.

This module handles tracking open documents, their content, versions,
and cached translations.
"""

from dataclasses import dataclass, field
from datetime import datetime


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
        return len(self.text.splitlines())

    def get_line(self, line_number: int) -> str | None:
        """Get specific line from document.

        Args:
            line_number: Line number (0-indexed)

        Returns:
            Line content or None if line doesn't exist
        """
        lines = self.text.splitlines()
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
