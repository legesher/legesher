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
    SET_TRACE,
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
    SetTraceParams,
    ShowMessageParams,
    TextDocumentSyncKind,
    TraceValue,
)
from pygls.lsp.server import LanguageServer  # pygls 2.0 import path

from . import __version__
from .config import LanguageServerConfig
from .document import DocumentManager
from .enhanced_intelligence import INSTALL_HINT, EnhancedIntelligenceProxy, _get_pack_loader
from .logging_setup import apply_trace_value
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
# or with another extension's additions to the same session. Answers whether
# enhanced intelligence is running, and which language each document is being
# served in (CORE-1976).
LEGESHER_STATUS = "legesher/status"

# Custom LSP notification, client to server: `{uri, language}`, the language one
# document is written in (CORE-1976). The client resolves it (settings and
# content detection live there) and sends it as the document opens, normally
# just ahead of its didOpen, and whenever the answer changes. The server does
# no detection of its own.
LEGESHER_DOCUMENT_LANGUAGE = "legesher/documentLanguage"

# The pack version every provider loads, so a pack that loads here is one the
# providers can use.
_PROVIDER_PACK_VERSION = "3.10"


def _param(params: object, name: str) -> object:
    """Read one field of a custom message's params, in whatever shape pygls gave them.

    For a method it has no type for, pygls turns the params object into a
    namedtuple as it decodes the message, so a client's notification arrives
    with attributes, not keys. A direct call, or a pygls that stops doing
    that, hands over the plain dict instead, so both are read.
    """
    if isinstance(params, dict):
        return params.get(name)
    return getattr(params, name, None)


def _shown_language(language: str) -> str:
    """Quote a reported language for a message, bounded, since it came off the wire."""
    if len(language) > 16:
        return f"{language[:16]!r}..."
    return repr(language)


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

    Every request is answered in the language of the document it is about,
    which the client names per document (CORE-1976), so one session serves
    files in any number of languages.
    """

    def __init__(self, config: LanguageServerConfig):
        """Initialize language server.

        Args:
            config: Server configuration
        """
        super().__init__("legesher-lsp", __version__)
        self.config = config
        self.document_manager = DocumentManager()

        # Debug, not info: the entry point has already said what the process
        # started with, and this repeats it a line later with no way for a
        # reader to tell which of the two won (CORE-1979).
        logger.debug(
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

        # One notice per problem is information; repeating it is noise the user
        # learns to dismiss (CORE-1886). Keyed, so two different problems, say
        # enhanced intelligence and a language with no pack, each get theirs.
        self._degradation_notified: set[str] = set()

        # The language each document is written in, as the client last named
        # it (CORE-1976). A document it has not named falls back to
        # `config.file_language`, which is what every document was served in
        # before the server could tell them apart.
        self._document_languages: dict[str, str] = {}

        # Why documents in a language cannot be served, or None when they can.
        # Decided once per language: it does not change mid-session, and every
        # request about such a document asks again.
        self._language_problems: dict[str, str | None] = {}

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

    def _notify_degraded_once(self, detail: str, key: str = "enhanced-intelligence") -> None:
        """Tell the user, once per problem, that something they expect is not running.

        `logger.warning` is not a user-visible surface — it lands in a log
        nobody opens. Silently serving a thinner experience than advertised is
        the failure this ticket exists to stop, so the notice goes to the client
        where a person will actually see it.

        ``key`` names the problem. A language that cannot be served passes its
        own, so its notice neither repeats per document nor is swallowed by an
        earlier notice about something else (CORE-1976).
        """
        if key in self._degradation_notified:
            return

        self._degradation_notified.add(key)
        self.window_show_message(ShowMessageParams(type=MessageType.Warning, message=detail))

    def document_language(self, uri: str) -> str:
        """The language the document at ``uri`` is written in, as far as the server knows.

        What the client last named for it, or the configured file language for
        a document it has not named. Read at call time, so the fallback follows
        whatever ``initialize`` settled on.
        """
        return self._document_languages.get(uri, self.config.file_language)

    def language_to_serve(self, uri: str) -> str | None:
        """The language to answer requests about ``uri`` in, or None if there is none.

        None means no pack can serve the document's language. The user is told
        once per language and `legesher/status` names every such document, so
        a provider answering nothing for it is never mistaken for a working
        file with nothing in it, which is how a file in the wrong language used
        to look (CORE-1976).
        """
        language = self.document_language(uri)
        problem = self._language_problem(language)
        if problem is None:
            return language

        self._notify_degraded_once(problem, key=f"language:{language}")
        return None

    def _language_problem(self, language: str) -> str | None:
        """Why documents in ``language`` cannot be served, or None when they can."""
        if language in self._language_problems:
            return self._language_problems[language]

        problem: str | None = None
        features = "Legesher highlighting, hover, completion or diagnostics"
        if not language:
            problem = f"A document's language arrived without a value, so it gets no {features}."
        else:
            shown = _shown_language(language)
            try:
                validate_language_code(language, "language")
            except ValueError:
                problem = (
                    f"Legesher has no language pack for {shown}, so documents in that "
                    f"language get no {features}."
                )
            else:
                try:
                    # The shared loader, whose cache (CORE-446) makes this cheap
                    # after the first document in each language.
                    _get_pack_loader().load(
                        language=language, target="python", version=_PROVIDER_PACK_VERSION
                    )
                except Exception as error:
                    problem = (
                        f"The Legesher language pack for {shown} could not be loaded "
                        f"({type(error).__name__}), so documents in that language get "
                        f"no {features}."
                    )

        if problem is not None:
            logger.warning(problem)
        self._language_problems[language] = problem
        return problem

    def _request_refresh(self) -> None:
        """Ask the client to re-request what it already holds for open documents.

        An editor keeps semantic tokens and pulled diagnostics until told they
        are stale; hover and completion are asked for fresh each time and need
        nothing. Sent only when the client declared it accepts the request.
        """
        capabilities = getattr(self.protocol, "client_capabilities", None)
        workspace = capabilities.workspace if capabilities else None
        if workspace is None:
            return
        if workspace.semantic_tokens and workspace.semantic_tokens.refresh_support:
            self.workspace_semantic_tokens_refresh(None)
        if workspace.diagnostics and workspace.diagnostics.refresh_support:
            self.workspace_diagnostic_refresh(None)

    def server_status(self) -> dict[str, object]:
        """The `legesher/status` payload.

        Whether enhanced intelligence is running, as before, plus one entry per
        document the server has open or has been told about: the language it
        is served in, whether that came from the client or the configuration,
        and, when it cannot be served, why (CORE-1976).
        """
        payload = self.enhanced_intelligence_status().to_dict()
        uris = set(self._document_languages) | {
            document.uri for document in self.document_manager.get_all_documents()
        }
        documents = []
        for uri in sorted(uris):
            language = self.document_language(uri)
            problem = self._language_problem(language)
            documents.append(
                {
                    "uri": uri,
                    "language": language,
                    "source": "client" if uri in self._document_languages else "configured",
                    "served": problem is None,
                    "detail": problem,
                }
            )
        payload["documents"] = documents
        return payload

    def _register_handlers(self) -> None:
        """Register all LSP method handlers using decorators."""
        # Create wrapper functions that pygls can decorate properly
        # This is necessary because pygls tries to set attributes on the function
        # and bound methods don't allow that

        async def initialize_wrapper(params: InitializeParams) -> InitializeResult:
            return await self.on_initialize(params)

        async def initialized_wrapper(params: InitializedParams) -> None:
            await self.on_initialized(params)

        async def set_trace_wrapper(params: SetTraceParams) -> None:
            await self.on_set_trace(params)

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
            return self.server_status()

        # Annotated with the wire shape on purpose: pygls passes the server in
        # as an extra first argument when that parameter's annotation is a
        # supertype of the server class, which `object` would be and a
        # parameterized `dict` is not.
        async def document_language_wrapper(params: dict[str, object] | None) -> None:
            await self.on_document_language(params)

        # Register the wrappers
        # CRITICAL: Must register initialize to process initialization_options
        # for language switching
        self.feature(INITIALIZE)(initialize_wrapper)
        self.feature(INITIALIZED)(initialized_wrapper)
        # pygls records the trace value itself and then calls this, which is
        # what turns the extra logging on and off (CORE-1979).
        self.feature(SET_TRACE)(set_trace_wrapper)
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

        # Custom notification naming each document's language (CORE-1976).
        self.feature(LEGESHER_DOCUMENT_LANGUAGE)(document_language_wrapper)

    def _apply_trace(self, params: InitializeParams) -> TraceValue:
        """Set logging verbosity from whichever trace setting the client sent.

        The setting arrives twice: `trace` on the initialize request itself,
        which is where the protocol puts it, and a `trace` key inside our
        initialization options, which is what the VS Code extension sends. The
        options win when both are present, because that one is ours and a user
        who sets it means it.

        Args:
            params: Initialize parameters from client

        Returns:
            The trace value that was applied.
        """
        trace: object = params.trace
        init_opts = params.initialization_options
        if isinstance(init_opts, dict) and init_opts.get("trace") is not None:
            trace = init_opts["trace"]

        value = apply_trace_value(trace)
        if value is not TraceValue.Off:
            logger.info(f"Trace level: {value.value}")
        return value

    async def on_set_trace(self, params: SetTraceParams) -> None:
        """Handle a `$/setTrace` notification.

        Trace is changeable mid-session, so a user who needs detail does not
        have to restart the server to get it, nor keep paying for it after.

        Args:
            params: The trace value the client is switching to
        """
        value = apply_trace_value(params.value)
        logger.info(f"Trace level changed to: {value.value}")

    async def on_initialize(self, params: InitializeParams) -> InitializeResult:
        """Handle initialize request from client.

        Args:
            params: Initialize parameters from client

        Returns:
            Server capabilities
        """
        logger.info(f"Client initializing from: {params.root_uri}")

        # The client's trace setting decides how much of the rest of this
        # session is logged, so it is read before anything else is (CORE-1979).
        self._apply_trace(params)

        # Update config from initialization options (CORE-362)
        # Security: Validate all client inputs to prevent injection attacks
        if params.initialization_options:
            init_opts = params.initialization_options
            logger.debug(f"Initialization options: {init_opts}")
            if isinstance(init_opts, dict):
                try:
                    # The deprecated single slot first, so the named roles can
                    # override it. A client that predates the role split sends
                    # only targetLanguage, and that one value was always three
                    # things at once — so it seeds all three (CORE-1760).
                    if "targetLanguage" in init_opts:
                        self.config.apply_legacy_target_language(
                            validate_language_code(init_opts["targetLanguage"], "targetLanguage")
                        )
                        logger.debug(
                            f"Updated target language from init options: "
                            f"{self.config.target_language}"
                        )
                    if "sourceLanguage" in init_opts:
                        self.config.source_language = validate_language_code(
                            init_opts["sourceLanguage"], "sourceLanguage"
                        )
                        logger.debug(
                            f"Updated source language from init options: "
                            f"{self.config.source_language}"
                        )
                    # The named roles (CORE-1760), carried as separate slots.
                    # target_language shadows file_language deliberately:
                    # every provider written against the old slot parses the
                    # file with it, and that is the file-language role.
                    if "fileLanguage" in init_opts:
                        self.config.file_language = validate_language_code(
                            init_opts["fileLanguage"], "fileLanguage"
                        )
                        self.config.target_language = self.config.file_language
                        logger.debug(
                            f"Updated file language from init options: {self.config.file_language}"
                        )
                    if "workingLanguage" in init_opts:
                        self.config.working_language = validate_language_code(
                            init_opts["workingLanguage"], "workingLanguage"
                        )
                        logger.debug(
                            f"Updated working language from init options: "
                            f"{self.config.working_language}"
                        )
                except ValueError as e:
                    logger.warning(
                        f"Invalid language configuration from client: {e}. Using defaults."
                    )
                    # Continue with default config - fail securely

        # One line, after the slots have settled, saying which languages are
        # actually in effect. A log that reports a language more than once
        # leaves the reader guessing which report won.
        logger.info(
            f"Languages resolved: source={self.config.source_language}, "
            f"file={self.config.file_language}, working={self.config.working_language}"
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
                "version": __version__,
            },
        )

    async def on_initialized(self, params: InitializedParams) -> None:
        """Handle initialized notification from client.

        Note: initialization_options are now processed in on_initialize() which runs first.
        This method just initializes EnhancedIntelligenceProxy after config has been updated.

        Args:
            params: Initialized parameters
        """
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

        # Translate document for the language server if enabled (CORE-360), with
        # its own language's keywords (CORE-1976). A document no pack can serve
        # is not sent: untranslated keywords read as undefined names to the
        # type checker, which answers with a screen of false errors.
        language = self.language_to_serve(doc.uri)
        if language and self.intelligence_proxy and self.intelligence_proxy.is_running():
            try:
                await self.intelligence_proxy.translate_document_for_server(
                    doc.uri, doc.text, language
                )
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
            uri = params.text_document.uri
            language = (
                self.language_to_serve(uri) if self.document_manager.has_document(uri) else None
            )
            if language and self.intelligence_proxy and self.intelligence_proxy.is_running():
                try:
                    await self.intelligence_proxy.translate_document_for_server(
                        params.text_document.uri, params.content_changes[0].text, language
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
        # Forget its language too. A reopened document is named again before
        # its didOpen; a stale entry would outrank the fallback for a client
        # that never names documents at all.
        self._document_languages.pop(params.text_document.uri, None)
        logger.debug(f"Document closed: {params.text_document.uri}")

    async def on_document_language(self, params: object) -> None:
        """Handle `legesher/documentLanguage`: the language one document is written in.

        The client sends it as the document opens, normally just ahead of its
        didOpen, and again whenever the language it resolves for that document
        changes; the server takes the client's word and does no detection of
        its own (CORE-1976). Arriving after the didOpen is handled like any
        other change: the client is asked to refresh what it already holds.

        A language no pack can serve is recorded anyway, and reported. Falling
        back to the configured language instead would answer for the document
        in a language it is not written in, which is the defect this replaces.

        Args:
            params: ``{"uri": str, "language": str}``
        """
        uri = _param(params, "uri")
        if not isinstance(uri, str) or not uri:
            logger.warning(f"Ignoring {LEGESHER_DOCUMENT_LANGUAGE} with no document URI")
            return
        reported = _param(params, "language")
        language = reported if isinstance(reported, str) else ""

        previous = self.document_language(uri)
        self._document_languages[uri] = language
        logger.debug(f"Document language: {uri} -> {_shown_language(language)}")

        document = self.document_manager.get_document(uri)
        if document is None:
            # Named ahead of its didOpen, which is the usual order: nothing has
            # been answered for it yet, so nothing is stale. If its language
            # cannot be served, the user is told when it opens.
            return

        # Tells the user now, once, if this language cannot be served.
        served = self.language_to_serve(uri)
        if language == previous:
            return

        if served and self.intelligence_proxy and self.intelligence_proxy.is_running():
            try:
                await self.intelligence_proxy.translate_document_for_server(
                    uri, document.text, served
                )
            except (TimeoutError, RuntimeError, ValueError) as e:
                logger.warning(f"Failed to retranslate document for the language server: {e!r}")
            except Exception as e:
                logger.error(
                    f"Unexpected error retranslating document for the language server: {e!r}",
                    exc_info=True,
                )

        self._request_refresh()

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
        # Try the language server first for advanced type information (CORE-360).
        # Not for a document no pack can serve (CORE-1976): whatever the proxy
        # holds for it was translated in a language it is not written in. Nor
        # for one that is not open, which has nothing to ask about.
        uri = params.text_document.uri
        language = self.language_to_serve(uri) if self.document_manager.has_document(uri) else None
        if language and self.intelligence_proxy and self.intelligence_proxy.is_running():
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

        # Try to get language-server diagnostics if available (CORE-360), for a
        # document translated with its own language's keywords (CORE-1976).
        enhanced_diagnostics: list[Diagnostic] = []
        if self.intelligence_proxy and self.intelligence_proxy.is_running():
            doc = self.document_manager.get_document(params.text_document.uri)
            language = self.language_to_serve(params.text_document.uri) if doc else None
            if doc and language:
                try:
                    enhanced_diagnostics = await self.intelligence_proxy.forward_diagnostic(
                        params.text_document.uri, doc.text, language
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
