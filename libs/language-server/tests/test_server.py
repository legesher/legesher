"""Tests for LSP server implementation.

NOTE (CORE-356): Server integration tests are currently disabled due to Python 3.13
compatibility issues with pygls 1.3.1's feature registration mechanism. The foundation
is implemented and will be tested in CORE-357 when integrated with actual providers.

The error occurs because Python 3.13 removed __dict__ from bound methods, but pygls 1.3.1
tries to set attributes via setattr(). This will be resolved when:
1. pygls releases Python 3.13 compatible version, OR
2. We test server integration with VS Code client in Cycle 8 (CORE-360)

For now, config.py and document.py have 100% test coverage, which covers the core
foundation logic. Server wiring will be validated through integration testing.
"""

import pytest
from lsprotocol.types import (
    ClientCapabilities,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentDiagnosticParams,
    HoverParams,
    InitializeParams,
    Position,
    TextDocumentContentChangeWholeDocument,
    TextDocumentIdentifier,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
)

from legesher_language_server import __version__
from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.server import LegesherLanguageServer, create_server


@pytest.fixture
def config():
    """Create test configuration.

    Note: target_language="es" is required — completion and diagnostic tests
    assert Spanish translations (e.g., "definir" for "def").
    """
    return LanguageServerConfig(source_language="en", target_language="es", python_version="3.10")


@pytest.fixture
def server(config):
    """Create test server instance."""
    return LegesherLanguageServer(config)


@pytest.mark.asyncio
async def test_server_initialization(server):
    """Test server initialization."""
    params = InitializeParams(
        process_id=None, root_uri="file:///test", capabilities=ClientCapabilities()
    )

    result = await server.on_initialize(params)

    assert result.capabilities.hover_provider is True
    assert result.capabilities.completion_provider is not None
    assert result.capabilities.diagnostic_provider is not None
    assert result.server_info["name"] == "legesher-lsp"
    assert result.server_info["version"] == __version__


@pytest.mark.asyncio
async def test_document_open(server):
    """Test document open notification."""
    params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///test.py", language_id="python", version=1, text="def foo(): pass"
        )
    )

    await server.on_did_open(params)

    doc = server.document_manager.get_document("file:///test.py")
    assert doc is not None
    assert doc.text == "def foo(): pass"
    assert doc.version == 1
    assert doc.language_id == "python"


@pytest.mark.asyncio
async def test_document_change(server):
    """Test document change notification."""
    # Open document first
    open_params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///test.py", language_id="python", version=1, text="original"
        )
    )
    await server.on_did_open(open_params)

    # Change document
    change_params = DidChangeTextDocumentParams(
        text_document=VersionedTextDocumentIdentifier(uri="file:///test.py", version=2),
        content_changes=[TextDocumentContentChangeWholeDocument(text="updated")],
    )
    await server.on_did_change(change_params)

    doc = server.document_manager.get_document("file:///test.py")
    assert doc is not None
    assert doc.text == "updated"
    assert doc.version == 2


@pytest.mark.asyncio
async def test_document_close(server):
    """Test document close notification."""
    # Open document
    open_params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///test.py", language_id="python", version=1, text="test"
        )
    )
    await server.on_did_open(open_params)

    assert server.document_manager.has_document("file:///test.py")

    # Close document
    close_params = DidCloseTextDocumentParams(
        text_document=TextDocumentIdentifier(uri="file:///test.py")
    )
    await server.on_did_close(close_params)

    assert not server.document_manager.has_document("file:///test.py")


@pytest.mark.asyncio
async def test_hover_stub(server):
    """Test hover provider stub (returns None until CORE-357)."""
    # Open document
    open_params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///test.py", language_id="python", version=1, text="def foo(): pass"
        )
    )
    await server.on_did_open(open_params)

    # Request hover
    hover_params = HoverParams(
        text_document=TextDocumentIdentifier(uri="file:///test.py"),
        position=Position(line=0, character=4),
    )

    result = await server.on_hover(hover_params)

    # Should return None (stub implementation)
    assert result is None


@pytest.mark.asyncio
async def test_completion_returns_items(server):
    """Test completion provider returns keyword and builtin completions."""
    # Open document
    open_params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///test.py", language_id="python", version=1, text="def "
        )
    )
    await server.on_did_open(open_params)

    # Request completion
    completion_params = CompletionParams(
        text_document=TextDocumentIdentifier(uri="file:///test.py"),
        position=Position(line=0, character=4),
    )

    result = await server.on_completion(completion_params)

    # Should return keyword and builtin completions
    assert result.is_incomplete is False
    assert len(result.items) > 0
    labels = [item.label for item in result.items]
    assert "definir" in labels  # Spanish "def"


@pytest.mark.asyncio
async def test_diagnostic_returns_errors(server):
    """Test diagnostic provider returns syntax errors."""
    # Open document with syntax error
    open_params = DidOpenTextDocumentParams(
        text_document=TextDocumentItem(
            uri="file:///test.py",
            language_id="python",
            version=1,
            text="def foo()\n  pass",  # Syntax error: missing colon
        )
    )
    await server.on_did_open(open_params)

    # Request diagnostics
    diagnostic_params = DocumentDiagnosticParams(
        text_document=TextDocumentIdentifier(uri="file:///test.py")
    )

    result = await server.on_diagnostic(diagnostic_params)

    # Should detect the syntax error
    assert result.kind == "full"
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_shutdown(server):
    """Test server shutdown."""
    # Should not raise any errors
    await server.on_shutdown(None)


def test_create_server_with_config():
    """Test creating server with explicit config."""
    config = LanguageServerConfig(source_language="fr", target_language="de")

    server = create_server(config)

    assert server.config.source_language == "fr"
    assert server.config.target_language == "de"


def test_create_server_from_env(monkeypatch):
    """Test creating server from environment variables."""
    monkeypatch.setenv("LEGESHER_SOURCE_LANG", "pt")
    monkeypatch.setenv("LEGESHER_TARGET_LANG", "ja")

    server = create_server()

    assert server.config.source_language == "pt"
    assert server.config.target_language == "ja"


@pytest.mark.asyncio
async def test_multiple_documents(server):
    """Test handling multiple open documents."""
    # Open three documents
    for i in range(1, 4):
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=f"file:///test{i}.py", language_id="python", version=1, text=f"# File {i}"
            )
        )
        await server.on_did_open(params)

    # Verify all tracked
    assert server.document_manager.get_document_count() == 3

    # Close one
    close_params = DidCloseTextDocumentParams(
        text_document=TextDocumentIdentifier(uri="file:///test2.py")
    )
    await server.on_did_close(close_params)

    assert server.document_manager.get_document_count() == 2
    assert server.document_manager.has_document("file:///test1.py")
    assert not server.document_manager.has_document("file:///test2.py")
    assert server.document_manager.has_document("file:///test3.py")


@pytest.mark.asyncio
async def test_initialize_carries_file_and_working_languages_separately(server):
    """The named roles arrive as separate slots and stay separate (CORE-1760).

    The client resolves the file language (detection) and the working language
    (settings) independently and must not collapse them before the server sees
    them — a Farsi file opened by a Portuguese speaker is exactly the case the
    two-slot model got wrong.
    """
    params = InitializeParams(
        process_id=None,
        root_uri="file:///test",
        capabilities=ClientCapabilities(),
        initialization_options={
            "sourceLanguage": "en",
            "fileLanguage": "fa",
            "workingLanguage": "pt",
            # The deprecated compat slot mirrors fileLanguage on the wire.
            "targetLanguage": "fa",
        },
    )

    await server.on_initialize(params)

    assert server.config.source_language == "en"
    assert server.config.file_language == "fa"
    assert server.config.working_language == "pt"
    # Providers written against the old slot parse the file with it, so it
    # tracks the file language — never the working language.
    assert server.config.target_language == "fa"


@pytest.mark.asyncio
async def test_initialize_legacy_target_language_seeds_all_roles(server):
    """A client that predates the role split keeps working (CORE-1760).

    Old clients send only targetLanguage, and that one value always meant the
    file and working languages at once — so it seeds both.
    """
    params = InitializeParams(
        process_id=None,
        root_uri="file:///test",
        capabilities=ClientCapabilities(),
        initialization_options={"sourceLanguage": "en", "targetLanguage": "de"},
    )

    await server.on_initialize(params)

    assert server.config.target_language == "de"
    assert server.config.file_language == "de"
    assert server.config.working_language == "de"


@pytest.mark.asyncio
async def test_initialize_role_slots_override_the_deprecated_slot(server):
    """When both protocols appear, the named roles win (CORE-1760)."""
    params = InitializeParams(
        process_id=None,
        root_uri="file:///test",
        capabilities=ClientCapabilities(),
        initialization_options={
            "targetLanguage": "de",
            "fileLanguage": "fa",
            "workingLanguage": "pt",
        },
    )

    await server.on_initialize(params)

    assert server.config.file_language == "fa"
    assert server.config.working_language == "pt"
    assert server.config.target_language == "fa"


@pytest.mark.asyncio
async def test_initialize_invalid_working_language_fails_secure(server):
    """An invalid role value is rejected without taking the server down.

    Same fail-secure contract the deprecated slot has (CORE-446): the value is
    dropped, the server keeps its previous configuration, and initialize still
    answers with capabilities.
    """
    params = InitializeParams(
        process_id=None,
        root_uri="file:///test",
        capabilities=ClientCapabilities(),
        initialization_options={"workingLanguage": "../etc/passwd"},
    )

    result = await server.on_initialize(params)

    assert server.config.working_language == "en"
    assert result.capabilities.hover_provider is True
