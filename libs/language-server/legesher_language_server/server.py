"""Language Server Protocol server for Legesher.

This module provides the main LSP server implementation using pygls.
"""

import logging

from lsprotocol.types import (
    INITIALIZE,
    INITIALIZED,
    SHUTDOWN,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DIAGNOSTIC,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_HOVER,
    CompletionList,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentDiagnosticParams,
    DocumentDiagnosticReport,
    Hover,
    HoverParams,
    InitializedParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.server import LanguageServer

from .config import LanguageServerConfig
from .document import DocumentManager
from .providers import provide_completion, provide_diagnostics, provide_hover

logger = logging.getLogger(__name__)


class LegesherLanguageServer(LanguageServer):
    """LSP server for multilingual Python programming.

    This server provides translation-aware IDE features including:
    - Document synchronization
    - Hover tooltips (CORE-357)
    - Code completion (CORE-358)
    - Diagnostics (CORE-359)
    """

    def __init__(self, config: LanguageServerConfig):
        """Initialize language server.

        Args:
            config: Server configuration
        """
        super().__init__("legesher-lsp", "v0.1.0")
        self.config = config
        self.document_manager = DocumentManager()

        logger.info(
            f"Initializing Legesher Language Server "
            f"(source: {config.source_language}, target: {config.target_language})"
        )

        # Note: Translation engine will be loaded on-demand in CORE-357
        # to avoid loading language packs during initialization
        self.translator: object | None = None

        # Register all LSP handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all LSP method handlers."""
        self.feature(INITIALIZE)(self.on_initialize)
        self.feature(INITIALIZED)(self.on_initialized)
        self.feature(SHUTDOWN)(self.on_shutdown)
        self.feature(TEXT_DOCUMENT_DID_OPEN)(self.on_did_open)
        self.feature(TEXT_DOCUMENT_DID_CHANGE)(self.on_did_change)
        self.feature(TEXT_DOCUMENT_DID_CLOSE)(self.on_did_close)

        # Provider stubs (implemented in CORE-357, 358, 359)
        self.feature(TEXT_DOCUMENT_HOVER)(self.on_hover)
        self.feature(TEXT_DOCUMENT_COMPLETION)(self.on_completion)
        self.feature(TEXT_DOCUMENT_DIAGNOSTIC)(self.on_diagnostic)

    async def on_initialize(self, params: InitializeParams) -> InitializeResult:
        """Handle initialize request from client.

        Args:
            params: Initialize parameters from client

        Returns:
            Server capabilities
        """
        logger.info(f"Client initializing from: {params.root_uri}")

        return InitializeResult(
            capabilities=ServerCapabilities(
                text_document_sync=TextDocumentSyncKind.Full,
                hover_provider=True,
                completion_provider={
                    "trigger_characters": ["."],
                },
                diagnostic_provider={
                    "inter_file_dependencies": False,
                    "workspace_diagnostics": False,
                },
            ),
            server_info={
                "name": "legesher-lsp",
                "version": "0.1.0",
            },
        )

    async def on_initialized(self, params: InitializedParams) -> None:
        """Handle initialized notification from client.

        Args:
            params: Initialized parameters
        """
        logger.info("Server initialized successfully")

    async def on_shutdown(self, params: object) -> None:
        """Handle shutdown request from client.

        Args:
            params: Shutdown parameters (unused)
        """
        logger.info("Server shutting down")
        # Clean up resources if needed

    async def on_did_open(self, params: DidOpenTextDocumentParams) -> None:
        """Handle document open notification.

        Args:
            params: Document open parameters
        """
        doc = params.text_document
        self.document_manager.open_document(
            uri=doc.uri, text=doc.text, version=doc.version, language_id=doc.language_id
        )
        logger.debug(f"Document opened: {doc.uri}")

    async def on_did_change(self, params: DidChangeTextDocumentParams) -> None:
        """Handle document change notification.

        Args:
            params: Document change parameters
        """
        if params.content_changes:
            self.document_manager.update_document(
                uri=params.text_document.uri,
                text=params.content_changes[0].text,
                version=params.text_document.version,
            )
            logger.debug(f"Document changed: {params.text_document.uri}")

    async def on_did_close(self, params: DidCloseTextDocumentParams) -> None:
        """Handle document close notification.

        Args:
            params: Document close parameters
        """
        self.document_manager.close_document(params.text_document.uri)
        logger.debug(f"Document closed: {params.text_document.uri}")

    # Provider stubs - Implemented in CORE-357, 358, 359

    async def on_hover(self, params: HoverParams) -> Hover | None:
        """Provide hover information at cursor position.

        Args:
            params: Hover request parameters

        Returns:
            Hover information or None

        Note:
            STUB - Full implementation in CORE-357
        """
        return await provide_hover(self, params.text_document.uri, params.position)

    async def on_completion(self, params: CompletionParams) -> CompletionList:
        """Provide completion suggestions at cursor position.

        Args:
            params: Completion request parameters

        Returns:
            List of completion items

        Note:
            STUB - Full implementation in CORE-358
        """
        items = await provide_completion(self, params.text_document.uri, params.position)
        return CompletionList(is_incomplete=False, items=items)

    async def on_diagnostic(self, params: DocumentDiagnosticParams) -> DocumentDiagnosticReport:
        """Provide diagnostics for document.

        Args:
            params: Diagnostic request parameters

        Returns:
            Document diagnostics

        Note:
            STUB - Full implementation in CORE-359
        """
        diagnostics = await provide_diagnostics(self, params.text_document.uri)

        return DocumentDiagnosticReport(
            kind="full",
            items=diagnostics,
        )


def create_server(config: LanguageServerConfig | None = None) -> LegesherLanguageServer:
    """Create and configure language server instance.

    Args:
        config: Server configuration (loads from env if None)

    Returns:
        Configured LegesherLanguageServer instance
    """
    if config is None:
        config = LanguageServerConfig.from_env()

    return LegesherLanguageServer(config)
