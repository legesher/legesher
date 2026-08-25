"""Language Server Protocol server for Legesher.

This module provides the main LSP server implementation using pygls.
"""

import asyncio
import logging
from dataclasses import dataclass

from legesher_i18n import get_active_language_codes
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
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
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
    MessageType,
    SemanticTokens,
    SemanticTokensLegend,
    SemanticTokensOptions,
    SemanticTokensParams,
    ServerCapabilities,
    ShowMessageParams,
    TextDocumentSyncKind,
)
from pygls.lsp.server import LanguageServer  # pygls 2.0 import path

from .config import LanguageServerConfig
from .document import DocumentManager
from .enhanced_intelligence import INSTALL_HINT, EnhancedIntelligenceProxy
from .providers import (
    provide_completion,
    provide_diagnostics,
    provide_hover,
    provide_semantic_tokens,
)

logger = logging.getLogger(__name__)

# Allowed language codes for security validation
# Includes both 'available' and 'experimental' status languages
# Imported from legesher_i18n (single source of truth from languages.json)
ALLOWED_LANGUAGES = set(get_active_language_codes())


def validate_language_code(code: str, field_name: str) -> str:
    """Validate language code against whitelist.

    Security: Only accept whitelisted 2-letter ISO 639-1 codes
    to prevent injection attacks and path traversal.

    Args:
        code: Language code to validate
        field_name: Field name for error messages

    Returns:
        Validated language code

    Raises:
        ValueError: If code is invalid or not in whitelist
    """
    # Type validation
    if not isinstance(code, str):
        raise ValueError(f"{field_name} must be a string")

    # Format validation (2-letter lowercase)
    if not code.islower() or len(code) != 2:
        raise ValueError(f"{field_name} must be 2-letter lowercase code")

    # Whitelist validation
    if code not in ALLOWED_LANGUAGES:
        raise ValueError(
            f"{field_name} '{code}' not supported. Allowed: {', '.join(sorted(ALLOWED_LANGUAGES))}"
        )

    return code


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


# Custom LSP request. Namespaced so it cannot collide with a standard method
# or with another extension's additions to the same session.
LEGESHER_STATUS = "legesher/status"


@dataclass(frozen=True)
class EnhancedIntelligenceStatus:
    """Whether Pyright-backed intelligence is actually available right now.

    ``enabled`` and ``running`` are deliberately separate. A feature switched
    off on purpose and a feature that tried to start and failed look identical
    from the outside — both give you plain Legesher features — but they call for
    completely different responses from the user, so the status has to tell them
    apart (CORE-1886).
    """

    enabled: bool
    running: bool
    server_path: str | None
    detail: str

    def to_dict(self) -> dict[str, object]:
        """Render for the wire, in the camelCase LSP clients expect."""
        return {
            "enabled": self.enabled,
            "running": self.running,
            "serverPath": self.server_path,
            "detail": self.detail,
        }


class LegesherLanguageServer(LanguageServer):
    """LSP server for multilingual Python programming.

    This server provides translation-aware IDE features including:
    - Document synchronization
    - Hover tooltips
    - Code completion
    - Diagnostics
    - Semantic token highlighting
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

        # Semantic tokens legend (CORE-450)
        # These token types match the indices in semantic_tokens.py
        self.semantic_tokens_legend = SemanticTokensLegend(
            token_types=[
                "keyword",  # 0: Python keywords
                "class",  # 1: Class names (future)
                "function",  # 2: Function names (future)
                "variable",  # 3: Variables (future)
                "parameter",  # 4: Parameters (future)
            ],
            token_modifiers=[
                # No modifiers in Phase 1 (CORE-450)
                # Future: "declaration", "readonly", "async", etc.
            ],
        )

        # Note: Translation engine will be loaded on-demand in CORE-357
        # to avoid loading language packs during initialization
        self.translator: object | None = None

        # Enhanced-intelligence proxy for advanced Python information (CORE-360)
        # Note: Initialization deferred until on_initialized() to ensure
        # initialization_options are processed first (fixes language switching bug)
        self.intelligence_proxy: EnhancedIntelligenceProxy | None = None

        # One notice per session is information; repeating it is noise the user
        # learns to dismiss (CORE-1886).
        self._degradation_notified = False

        # Serialises proxy startup. Checking `is_running()` is not enough on its
        # own: the check and the spawn are separated by an await, and
        # `self.process` stays None until the spawn returns, so two concurrently
        # dispatched `initialized` notifications could both pass the check and
        # both start a server.
        self._proxy_start_lock = asyncio.Lock()

        # Register all LSP handlers
        self._register_handlers()

    def enhanced_intelligence_status(self) -> EnhancedIntelligenceStatus:
        """Report whether Pyright-backed intelligence is actually running.

        Answers the question the ticket poses directly — "is enhanced
        intelligence actually on?" — without the caller having to read a log.
        """
        enabled = self.config.enhanced_intelligence_enabled
        proxy = self.intelligence_proxy

        if not enabled:
            return EnhancedIntelligenceStatus(
                enabled=False,
                running=False,
                server_path=None,
                detail="Enhanced Python intelligence is disabled by configuration.",
            )

        running = proxy is not None and proxy.is_running() and proxy.initialized
        server_path = proxy.server_path if proxy else None

        if running:
            detail = f"Enhanced Python intelligence is active, using {server_path}."
        else:
            detail = (
                "Enhanced Python intelligence is enabled but not running: no Python "
                f"language server is available. Install one with {INSTALL_HINT}. "
                "Legesher features are unaffected."
            )

        return EnhancedIntelligenceStatus(
            enabled=True,
            running=running,
            server_path=server_path,
            detail=detail,
        )

    def _notify_degraded_once(self, detail: str) -> None:
        """Tell the user, once, that a defaulted-on feature is not running.

        `logger.warning` is not a user-visible surface — it lands in a log
        nobody opens. Silently serving a thinner experience than advertised is
        the failure this ticket exists to stop, so the notice goes to the client
        where a person will actually see it.
        """
        if self._degradation_notified:
            return

        self._degradation_notified = True
        self.window_show_message(ShowMessageParams(type=MessageType.Warning, message=detail))

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

        async def semantic_tokens_full_wrapper(
            params: SemanticTokensParams,
        ) -> SemanticTokens | None:
            return await self.on_semantic_tokens_full(params)

        async def status_wrapper(*args, **kwargs) -> dict[str, object]:
            # Takes no meaningful parameters; accepts whatever the client sends
            # so a stray argument cannot turn a status query into an error.
            return self.enhanced_intelligence_status().to_dict()

        # Register the wrappers
        # CRITICAL: Must register initialize to process initialization_options
        # for language switching
        self.feature(INITIALIZE)(initialize_wrapper)
        self.feature(INITIALIZED)(initialized_wrapper)
        self.feature(SHUTDOWN)(shutdown_wrapper)
        self.feature(TEXT_DOCUMENT_DID_OPEN)(did_open_wrapper)
        self.feature(TEXT_DOCUMENT_DID_CHANGE)(did_change_wrapper)
        self.feature(TEXT_DOCUMENT_DID_CLOSE)(did_close_wrapper)
        self.feature(TEXT_DOCUMENT_HOVER)(hover_wrapper)
        self.feature(TEXT_DOCUMENT_COMPLETION)(completion_wrapper)
        self.feature(TEXT_DOCUMENT_DIAGNOSTIC)(diagnostic_wrapper)

        # Register semantic tokens with legend
        self.feature(TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL, self.semantic_tokens_legend)(
            semantic_tokens_full_wrapper
        )

        # Custom request so a client can render an indicator answering "is
        # enhanced intelligence actually on?" without parsing server logs.
        self.feature(LEGESHER_STATUS)(status_wrapper)

    async def on_initialize(self, params: InitializeParams) -> InitializeResult:
        """Handle initialize request from client.

        Args:
            params: Initialize parameters from client

        Returns:
            Server capabilities
        """
        logger.info(f"Client initializing from: {params.root_uri}")
        logger.info(f"DEBUG: initialization_options = {params.initialization_options}")
        logger.info(
            f"DEBUG: config BEFORE - target: {self.config.target_language}, "
            f"source: {self.config.source_language}"
        )

        # Update config from initialization options (CORE-362)
        # Security: Validate all client inputs to prevent injection attacks
        if params.initialization_options:
            logger.info("DEBUG: initialization_options exists, processing...")
            init_opts = params.initialization_options
            logger.info(
                f"DEBUG: init_opts type = {type(init_opts)}, "
                f"isinstance dict = {isinstance(init_opts, dict)}"
            )
            if isinstance(init_opts, dict):
                logger.info(f"DEBUG: Keys in init_opts: {list(init_opts.keys())}")
                try:
                    # The deprecated single slot first, so the named roles can
                    # override it. A client that predates the role split sends
                    # only targetLanguage, and that one value was always three
                    # things at once — so it seeds all three (CORE-1760).
                    if "targetLanguage" in init_opts:
                        logger.info(f"DEBUG: Found targetLanguage = {init_opts['targetLanguage']}")
                        self.config.apply_legacy_target_language(
                            validate_language_code(init_opts["targetLanguage"], "targetLanguage")
                        )
                        logger.info(
                            f"Updated target language from init options: "
                            f"{self.config.target_language}"
                        )
                    if "sourceLanguage" in init_opts:
                        logger.info(f"DEBUG: Found sourceLanguage = {init_opts['sourceLanguage']}")
                        self.config.source_language = validate_language_code(
                            init_opts["sourceLanguage"], "sourceLanguage"
                        )
                        logger.info(
                            f"Updated source language from init options: "
                            f"{self.config.source_language}"
                        )
                    # The named roles (CORE-1760), carried as separate slots.
                    # target_language shadows file_language deliberately:
                    # every provider written against the old slot parses the
                    # file with it, and that is the file-language role.
                    if "fileLanguage" in init_opts:
                        logger.info(f"DEBUG: Found fileLanguage = {init_opts['fileLanguage']}")
                        self.config.file_language = validate_language_code(
                            init_opts["fileLanguage"], "fileLanguage"
                        )
                        self.config.target_language = self.config.file_language
                        logger.info(
                            f"Updated file language from init options: {self.config.file_language}"
                        )
                    if "workingLanguage" in init_opts:
                        logger.info(
                            f"DEBUG: Found workingLanguage = {init_opts['workingLanguage']}"
                        )
                        self.config.working_language = validate_language_code(
                            init_opts["workingLanguage"], "workingLanguage"
                        )
                        logger.info(
                            f"Updated working language from init options: "
                            f"{self.config.working_language}"
                        )
                except ValueError as e:
                    logger.warning(
                        f"Invalid language configuration from client: {e}. Using defaults."
                    )
                    # Continue with default config - fail securely

        logger.info(
            f"DEBUG: config AFTER - target: {self.config.target_language}, "
            f"source: {self.config.source_language}, "
            f"file: {self.config.file_language}, "
            f"working: {self.config.working_language}"
        )

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
                semantic_tokens_provider=SemanticTokensOptions(
                    legend=self.semantic_tokens_legend,
                    full=True,
                    # Phase 1 (CORE-450): Only full document tokens
                    # Future phases: range=True
                ),
            ),
            server_info={
                "name": "legesher-lsp",
                "version": "0.1.0",
            },
        )

    async def on_initialized(self, params: InitializedParams) -> None:
        """Handle initialized notification from client.

        Note: initialization_options are now processed in on_initialize() which runs first.
        This method just initializes EnhancedIntelligenceProxy after config has been updated.

        Args:
            params: Initialized parameters
        """
        logger.info(
            f"Server initialized: target={self.config.target_language}, "
            f"source={self.config.source_language}"
        )
        logger.info("Server initialized successfully")

        # Initialize the enhanced-intelligence proxy now that config is finalized (CORE-360)
        # This must happen AFTER processing initialization_options above
        if self.config.enhanced_intelligence_enabled and self.intelligence_proxy is None:
            self.intelligence_proxy = EnhancedIntelligenceProxy(self.config)
            logger.info("Enhanced-intelligence proxy initialized")

        # Start the enhanced-intelligence proxy if enabled (CORE-360)
        if self.intelligence_proxy:
            # `initialized` can arrive more than once — clients reconnect.
            # Starting again would spawn a second language server and drop the
            # handle to the first, orphaning it for the editor's lifetime. The
            # lock matters as much as the check: they are separated by an await.
            async with self._proxy_start_lock:
                if self.intelligence_proxy.is_running():
                    logger.debug("Enhanced-intelligence proxy already running; reusing it")
                    return

                started = await self.intelligence_proxy.start()

            if started:
                logger.info("Enhanced-intelligence proxy started successfully")
            else:
                # Say it where someone will see it. The proxy already logged the
                # specifics; this is the part that reaches the user (CORE-1886).
                status = self.enhanced_intelligence_status()
                logger.warning(
                    "Enhanced-intelligence proxy failed to start, using Legesher-only providers"
                )
                self._notify_degraded_once(status.detail)

    async def on_shutdown(self, params: object) -> None:
        """Handle shutdown request from client.

        Args:
            params: Shutdown parameters (unused)
        """
        logger.info("Server shutting down")

        # Stop the enhanced-intelligence proxy if running (CORE-360)
        if self.intelligence_proxy:
            await self.intelligence_proxy.stop()
            logger.info("Enhanced-intelligence proxy stopped")

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

        # Translate document for the language server if enabled (CORE-360)
        if self.intelligence_proxy and self.intelligence_proxy.is_running():
            try:
                await self.intelligence_proxy.translate_document_for_server(doc.uri, doc.text)
            except (TimeoutError, RuntimeError, ValueError) as e:
                logger.warning(f"Failed to translate document for the language server: {e!r}")
            except Exception as e:
                logger.error(
                    f"Unexpected error translating document for the language server: {e!r}",
                    exc_info=True,
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

            # Update translation for the language server if enabled (CORE-360)
            if self.intelligence_proxy and self.intelligence_proxy.is_running():
                try:
                    await self.intelligence_proxy.translate_document_for_server(
                        params.text_document.uri, params.content_changes[0].text
                    )
                except (TimeoutError, RuntimeError, ValueError) as e:
                    logger.warning(f"Failed to update translation for the language server: {e!r}")
                except Exception as e:
                    logger.error(
                        f"Unexpected error updating translation for the language server: {e!r}",
                        exc_info=True,
                    )

    async def on_did_close(self, params: DidCloseTextDocumentParams) -> None:
        """Handle document close notification.

        Args:
            params: Document close parameters
        """
        self.document_manager.close_document(params.text_document.uri)
        logger.debug(f"Document closed: {params.text_document.uri}")

    # LSP request handlers. Each delegates to the matching module in
    # `providers/`, and the two that an external type-aware server can improve
    # on — hover and diagnostics — try `enhanced_intelligence` first.

    async def on_hover(self, params: HoverParams) -> Hover | None:
        """Provide hover information at cursor position.

        Args:
            params: Hover request parameters

        Returns:
            Hover information or None

        Tries the external type-aware server first when one is running, and
        falls back to the built-in provider if it is absent, times out, or
        returns nothing.
        """
        # Try the language server first for advanced type information (CORE-360)
        if self.intelligence_proxy and self.intelligence_proxy.is_running():
            try:
                enhanced_hover = await self.intelligence_proxy.forward_hover(params)
                if enhanced_hover:
                    return enhanced_hover
            except (TimeoutError, RuntimeError, ValueError) as e:
                logger.warning(f"Enhanced-intelligence hover request failed: {e!r}")
            except Exception as e:
                logger.error(
                    f"Unexpected error in enhanced-intelligence hover: {e!r}", exc_info=True
                )

        # Fallback to basic hover provider
        return await provide_hover(self, params.text_document.uri, params.position)

    async def on_completion(self, params: CompletionParams) -> CompletionList:
        """Provide completion suggestions at cursor position.

        Args:
            params: Completion request parameters

        Returns:
            List of completion items

        The list is marked complete, so an editor may filter it client-side as
        typing continues instead of re-requesting.
        """
        items = await provide_completion(self, params.text_document.uri, params.position)
        return CompletionList(is_incomplete=False, items=items)

    async def on_diagnostic(self, params: DocumentDiagnosticParams) -> DocumentDiagnosticReport:
        """Provide diagnostics for document.

        Args:
            params: Diagnostic request parameters

        Returns:
            Document diagnostics

        Merges the built-in translated diagnostics with anything the external
        type-aware server reports, deduplicated. The built-in set is always
        produced, so diagnostics survive that server being unavailable.
        """
        # Get basic diagnostics
        basic_diagnostics = await provide_diagnostics(self, params.text_document.uri)

        # Try to get language-server diagnostics if available (CORE-360)
        enhanced_diagnostics: list[Diagnostic] = []
        if self.intelligence_proxy and self.intelligence_proxy.is_running():
            doc = self.document_manager.get_document(params.text_document.uri)
            if doc:
                try:
                    enhanced_diagnostics = await self.intelligence_proxy.forward_diagnostic(
                        params.text_document.uri, doc.text
                    )
                except (TimeoutError, RuntimeError, ValueError) as e:
                    logger.warning(f"Enhanced-intelligence diagnostic request failed: {e!r}")
                except Exception as e:
                    logger.error(
                        f"Unexpected error in enhanced-intelligence diagnostics: {e!r}",
                        exc_info=True,
                    )

        # Merge and deduplicate diagnostics
        all_diagnostics = _deduplicate_diagnostics(list(enhanced_diagnostics) + basic_diagnostics)

        return FullDocumentDiagnosticReport(
            kind="full",
            items=all_diagnostics,
        )

    async def on_semantic_tokens_full(self, params: SemanticTokensParams) -> SemanticTokens | None:
        """Provide semantic tokens for entire document.

        Args:
            params: Semantic tokens request parameters

        Returns:
            Semantic tokens for syntax highlighting

        Returns None when the document is not open.
        """
        return provide_semantic_tokens(self, params.text_document.uri)


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
