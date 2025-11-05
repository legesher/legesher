"""Tests for document management system."""

from datetime import datetime

from legesher_language_server.document import DocumentManager, DocumentState


def test_document_state_creation():
    """Test creating a DocumentState."""
    doc = DocumentState(
        uri="file:///test.py", text="def foo(): pass", version=1, language_id="python"
    )

    assert doc.uri == "file:///test.py"
    assert doc.text == "def foo(): pass"
    assert doc.version == 1
    assert doc.language_id == "python"
    assert doc.is_dirty is False
    assert doc.translated_text is None
    assert isinstance(doc.last_modified, datetime)


def test_document_state_update():
    """Test updating document content."""
    doc = DocumentState(uri="file:///test.py", text="original", version=1, language_id="python")

    # Set initial translation
    doc.set_translation("translated")
    assert doc.translated_text == "translated"
    assert doc.is_dirty is False

    # Update should invalidate cache
    old_time = doc.last_modified
    doc.update("updated", 2)

    assert doc.text == "updated"
    assert doc.version == 2
    assert doc.is_dirty is True
    assert doc.translated_text is None  # Cache invalidated
    assert doc.last_modified >= old_time


def test_document_state_get_line_count():
    """Test getting line count."""
    doc = DocumentState(
        uri="file:///test.py", text="line1\nline2\nline3", version=1, language_id="python"
    )

    assert doc.get_line_count() == 3


def test_document_state_get_line():
    """Test getting specific line."""
    doc = DocumentState(
        uri="file:///test.py", text="line1\nline2\nline3", version=1, language_id="python"
    )

    assert doc.get_line(0) == "line1"
    assert doc.get_line(1) == "line2"
    assert doc.get_line(2) == "line3"
    assert doc.get_line(3) is None  # Out of range
    assert doc.get_line(-1) is None  # Negative


def test_document_manager_open():
    """Test opening a document."""
    manager = DocumentManager()

    doc = manager.open_document(
        uri="file:///test.py", text="def foo(): pass", version=1, language_id="python"
    )

    assert doc.uri == "file:///test.py"
    assert manager.get_document_count() == 1
    assert manager.has_document("file:///test.py")


def test_document_manager_update():
    """Test updating a document."""
    manager = DocumentManager()

    # Open document
    manager.open_document(uri="file:///test.py", text="original", version=1, language_id="python")

    # Update document
    updated_doc = manager.update_document(uri="file:///test.py", text="updated", version=2)

    assert updated_doc is not None
    assert updated_doc.text == "updated"
    assert updated_doc.version == 2
    assert updated_doc.is_dirty is True

    # Update non-existent document
    result = manager.update_document(uri="file:///nonexistent.py", text="text", version=1)
    assert result is None


def test_document_manager_close():
    """Test closing a document."""
    manager = DocumentManager()

    # Open two documents
    manager.open_document("file:///test1.py", "text1", 1, "python")
    manager.open_document("file:///test2.py", "text2", 1, "python")

    assert manager.get_document_count() == 2

    # Close one
    manager.close_document("file:///test1.py")

    assert manager.get_document_count() == 1
    assert not manager.has_document("file:///test1.py")
    assert manager.has_document("file:///test2.py")

    # Close non-existent (should not error)
    manager.close_document("file:///nonexistent.py")
    assert manager.get_document_count() == 1


def test_document_manager_get_all():
    """Test getting all documents."""
    manager = DocumentManager()

    manager.open_document("file:///test1.py", "text1", 1, "python")
    manager.open_document("file:///test2.py", "text2", 1, "python")
    manager.open_document("file:///test3.py", "text3", 1, "python")

    all_docs = manager.get_all_documents()

    assert len(all_docs) == 3
    assert all(isinstance(doc, DocumentState) for doc in all_docs)

    uris = {doc.uri for doc in all_docs}
    assert uris == {"file:///test1.py", "file:///test2.py", "file:///test3.py"}


def test_document_manager_multiple_updates():
    """Test multiple updates to same document."""
    manager = DocumentManager()

    manager.open_document("file:///test.py", "v1", 1, "python")

    for i in range(2, 6):
        doc = manager.update_document("file:///test.py", f"v{i}", i)
        assert doc is not None
        assert doc.version == i
        assert doc.text == f"v{i}"

    final_doc = manager.get_document("file:///test.py")
    assert final_doc is not None
    assert final_doc.version == 5
    assert final_doc.text == "v5"


def test_translation_cache_invalidation():
    """Test that translation cache is properly invalidated."""
    manager = DocumentManager()

    doc = manager.open_document("file:///test.py", "original", 1, "python")

    # Set translation
    doc.set_translation("traducido")
    assert doc.translated_text == "traducido"
    assert doc.is_dirty is False

    # Update document - should invalidate cache
    manager.update_document("file:///test.py", "updated", 2)

    updated_doc = manager.get_document("file:///test.py")
    assert updated_doc is not None
    assert updated_doc.translated_text is None
    assert updated_doc.is_dirty is True
