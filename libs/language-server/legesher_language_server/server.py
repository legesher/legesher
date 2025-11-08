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
    Diagnostic,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentDiagnosticParams,
    DocumentDiagnosticReport,
    FullDocumentDiagnosticReport,
    Hover,
    HoverParams,
    InitializedParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.lsp.server import LanguageServer

from .config import LanguageServerConfig
from .document import DocumentManager
from .providers import provide_completion, provide_diagnostics, provide_hover
from .pylance_proxy import PylanceProxy

logger = logging.getLogger(__name__)


def _deduplicate_diagnostics(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    """Remove duplicate diagnostics by range and message.

    Args:
        diagnostics: List of diagnostics potentially containing duplicates

    Returns:
        List of unique diagnostics
    """
    seen: set[tuple[int, int, str]] = set()
    unique: list[Diagnostic] = []
    for diag in diagnostics:
        key = (diag.range.start.line, diag.range.start.character, diag.message)
        if key not in seen:
            seen.add(key)
            unique.append(diag)
    return unique


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

        # Pylance proxy for advanced Python intelligence (CORE-360)
        self.pylance_proxy: PylanceProxy | None = None
        if config.pylance_enabled:
            self.pylance_proxy = PylanceProxy(config)
            logger.info("Pylance proxy initialized")

        # Register all LSP handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all LSP method handlers using decorators."""
        # Create wrapper functions that pygls can decorate properly
        # This is necessary because pygls tries to set attributes on the function
        # and bound methods don't allow that

        async def initialize_wrapper(params: InitializeParams) -> InitializeResult:
            return await self.on_initialize(params)

        async def initialized_wrapper(params: InitializedParams) -> None:
            await self.on_initialized(params)

        async def shutdown_wrapper(*args, **kwargs) -> None:
            # pygls v2.0 may pass ls instance as first arg
            params = args[0] if args else kwargs.get("params", None)
            await self.on_shutdown(params)

        async def did_open_wrapper(params: DidOpenTextDocumentParams) -> None:
            await self.on_did_open(params)

        async def did_change_wrapper(params: DidChangeTextDocumentParams) -> None:
            await self.on_did_change(params)

        async def did_close_wrapper(params: DidCloseTextDocumentParams) -> None:
            await self.on_did_close(params)

        async def hover_wrapper(params: HoverParams) -> Hover | None:
            return await self.on_hover(params)

        async def completion_wrapper(params: CompletionParams) -> CompletionList:
            return await self.on_completion(params)

        async def diagnostic_wrapper(params: DocumentDiagnosticParams) -> DocumentDiagnosticReport:
            return await self.on_diagnostic(params)

        # Register the wrappers
        self.feature(INITIALIZE)(initialize_wrapper)
        self.feature(INITIALIZED)(initialized_wrapper)
        self.feature(SHUTDOWN)(shutdown_wrapper)
        self.feature(TEXT_DOCUMENT_DID_OPEN)(did_open_wrapper)
        self.feature(TEXT_DOCUMENT_DID_CHANGE)(did_change_wrapper)
        self.feature(TEXT_DOCUMENT_DID_CLOSE)(did_close_wrapper)
        self.feature(TEXT_DOCUMENT_HOVER)(hover_wrapper)
        self.feature(TEXT_DOCUMENT_COMPLETION)(completion_wrapper)
        self.feature(TEXT_DOCUMENT_DIAGNOSTIC)(diagnostic_wrapper)

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

        # Start Pylance proxy if enabled (CORE-360)
        if self.pylance_proxy:
            started = await self.pylance_proxy.start()
            if started:
                logger.info("Pylance proxy started successfully")
            else:
                logger.warning("Pylance proxy failed to start, using basic providers only")

    async def on_shutdown(self, params: object) -> None:
        """Handle shutdown request from client.

        Args:
            params: Shutdown parameters (unused)
        """
        logger.info("Server shutting down")

        # Stop Pylance proxy if running (CORE-360)
        if self.pylance_proxy:
            await self.pylance_proxy.stop()
            logger.info("Pylance proxy stopped")

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

        # Translate document for Pylance if enabled (CORE-360)
        if self.pylance_proxy and self.pylance_proxy.is_running():
            try:
                await self.pylance_proxy.translate_document_for_pylance(doc.uri, doc.text)
            except (TimeoutError, RuntimeError, ValueError) as e:
                logger.warning(f"Failed to translate document for Pylance: {e!r}")
            except Exception as e:
                logger.error(
                    f"Unexpected error translating document for Pylance: {e!r}", exc_info=True
                )

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

            # Update translation for Pylance if enabled (CORE-360)
            if self.pylance_proxy and self.pylance_proxy.is_running():
                try:
                    await self.pylance_proxy.translate_document_for_pylance(
                        params.text_document.uri, params.content_changes[0].text
                    )
                except (TimeoutError, RuntimeError, ValueError) as e:
                    logger.warning(f"Failed to update translation for Pylance: {e!r}")
                except Exception as e:
                    logger.error(
                        f"Unexpected error updating translation for Pylance: {e!r}", exc_info=True
                    )

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
            Implementation in CORE-357 with Pylance enhancement in CORE-360
        """
        # Try Pylance first for advanced type information (CORE-360)
        if self.pylance_proxy and self.pylance_proxy.is_running():
            try:
                pylance_hover = await self.pylance_proxy.forward_hover(params)
                if pylance_hover:
                    return pylance_hover
            except (TimeoutError, RuntimeError, ValueError) as e:
                logger.warning(f"Pylance hover request failed: {e!r}")
            except Exception as e:
                logger.error(f"Unexpected error in Pylance hover: {e!r}", exc_info=True)

        # Fallback to basic hover provider
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
        # Get basic diagnostics
        basic_diagnostics = await provide_diagnostics(self, params.text_document.uri)

        # Try to get Pylance diagnostics if available (CORE-360)
        pylance_diagnostics: list[Diagnostic] = []
        if self.pylance_proxy and self.pylance_proxy.is_running():
            doc = self.document_manager.get_document(params.text_document.uri)
            if doc:
                try:
                    pylance_diagnostics = await self.pylance_proxy.forward_diagnostic(
                        params.text_document.uri, doc.text
                    )
                except (TimeoutError, RuntimeError, ValueError) as e:
                    logger.warning(f"Pylance diagnostic request failed: {e!r}")
                except Exception as e:
                    logger.error(f"Unexpected error in Pylance diagnostics: {e!r}", exc_info=True)

        # Merge and deduplicate diagnostics
        all_diagnostics = _deduplicate_diagnostics(list(pylance_diagnostics) + basic_diagnostics)

        return FullDocumentDiagnosticReport(
            kind="full",
            items=all_diagnostics,
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
