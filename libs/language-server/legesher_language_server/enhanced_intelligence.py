"""Enhanced Python intelligence: proxying an external language server.

Legesher's own features work on localized source directly. This module adds the
things a type-aware server provides — type checking, richer hover, go-to-
definition — by running one alongside and translating in both directions:
localized code goes out as canonical English, and the answer comes back mapped
onto the reader's own positions.

The backend is ``pyright-langserver`` (Apache-2.0). It is deliberately **not**
Pylance, despite the history in CORE-360: Pylance's licence grants use only
with Microsoft products (§1(a)) and forbids standalone redistribution (§2(e)),
and its bundled server does not answer plain ``--stdio`` in any case.

Note ``pyright`` and ``pyright-langserver`` are different executables shipped in
the same npm package. The first is a command-line type checker that closes the
stream instead of speaking LSP, so pointing this module at it leaves the
feature silently dead; the second is the one that speaks the protocol.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from legesher_i18n import LanguagePackLoader
from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Hover,
    HoverParams,
    Position,
    Range,
)

from .config import LanguageServerConfig
from .incremental_translator import IncrementalTranslator

logger = logging.getLogger(__name__)

# The language server executable. Note this is NOT `pyright`: that is the
# command-line type checker, which exits instead of speaking LSP over stdio.
# Both ship in the same npm package, which is exactly why the wrong one is easy
# to pick up (CORE-1886).
LANGSERVER_BIN = "pyright-langserver"
CLI_BIN = "pyright"

INSTALL_HINT = f"npm install -g {CLI_BIN} (provides `{LANGSERVER_BIN}`)"


def default_fallback_bin_dirs(
    platform: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    """Directories to search when the language server is not on PATH.

    The platform and environment are injectable so each branch can be tested
    from any host. That is not fastidiousness: the POSIX list below can never
    match anything on Windows, which meant Windows had no fallback at all and
    nothing to reveal it short of a Windows runner.

    Args:
        platform: ``sys.platform`` value; defaults to the running platform
        environ: environment mapping; defaults to ``os.environ``

    Returns:
        Candidate directories, most likely first
    """
    platform = sys.platform if platform is None else platform
    environ = os.environ if environ is None else environ

    if platform == "win32":
        # `npm install -g` writes to %APPDATA%\npm; %LOCALAPPDATA% shows up in
        # some per-user installs. Absent either variable there is simply
        # nothing to offer, which is not an error.
        candidates = []
        for variable in ("APPDATA", "LOCALAPPDATA"):
            root = environ.get(variable)
            if root:
                candidates.append(os.path.join(root, "npm"))
        return candidates

    return [
        "/opt/homebrew/bin",  # Homebrew's default prefix on Apple Silicon
        "/usr/local/bin",
        "/usr/bin",
        str(Path.home() / ".local/bin"),
        str(Path.home() / ".npm-global/bin"),
    ]


# Resolved once at import; tests substitute this directly to isolate discovery
# from whatever the host machine happens to have installed.
FALLBACK_BIN_DIRS = default_fallback_bin_dirs()

# Generous ceiling for a single buffered LSP message. Hover results carrying
# rendered documentation comfortably exceed asyncio's 64 KiB default.
STREAM_LIMIT = 4 * 1024 * 1024


def frame_message(message: dict) -> bytes:
    """Encode a JSON-RPC message with an LSP ``Content-Length`` header.

    The header must count **bytes**, not characters. Deriving it from the
    encoded payload is the whole point: measuring the str instead under-declares
    the length for any non-ASCII content, so the server reads a truncated body
    and every message after it lands at the wrong offset.

    Args:
        message: JSON-RPC request or notification

    Returns:
        Framed bytes ready to write to the server's stdin
    """
    body = json.dumps(message).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


# Shared language pack loader with LRU cache (CORE-446)
# Uses lazy initialization to avoid import-time failures
_pack_loader: LanguagePackLoader | None = None


def _get_pack_loader() -> LanguagePackLoader:
    """Get or create the shared language pack loader with error handling.

    Uses lazy initialization to avoid module import failures if language
    pack directory is missing or permissions are incorrect (CORE-446 security).

    Returns:
        LanguagePackLoader instance

    Note:
        On initialization failure, returns a loader with empty pack root
        to allow graceful degradation rather than crashing.
    """
    global _pack_loader
    if _pack_loader is None:
        _pack_loader = LanguagePackLoader()
    return _pack_loader


def wire_severity(value: object) -> DiagnosticSeverity:
    """Convert a wire-format diagnostic severity into ``DiagnosticSeverity``.

    LSP JSON carries severity as a plain integer (1=Error, 2=Warning,
    3=Information, 4=Hint), but ``lsprotocol`` types want the enum: cattrs
    calls ``.value`` on the field at serialization time, so a raw int makes
    the whole ``textDocument/diagnostic`` response unserializable and puts a
    red error toast on screen (CORE-1977).

    Absent (``None``) and out-of-range values fall back to ``Error``,
    matching the previous default of ``1`` and erring loud rather than
    silently downgrading an unknown severity.
    """
    try:
        return DiagnosticSeverity(value)
    except (ValueError, TypeError):
        if value is not None:
            logger.warning(f"Unknown diagnostic severity {value!r}; treating as Error")
        return DiagnosticSeverity.Error


class EnhancedIntelligenceProxy:
    """Proxy to an external Python language server.

    Manages a ``pyright-langserver`` subprocess and translates LSP requests and
    responses between localized code and English, so type-aware features work
    on source written with non-English keywords.

    Architecture:
        User Code (Spanish) →  Translate to English  → Language server
                                                        ↓
        User IDE (Spanish)  ←  Translate to Spanish  ← Server response

    Example:
        >>> proxy = EnhancedIntelligenceProxy(config)
        >>> await proxy.start()
        >>> if proxy.is_running():
        ...     hover = await proxy.forward_hover(params)
    """

    def __init__(self, config: LanguageServerConfig):
        """Initialize the enhanced-intelligence proxy.

        Args:
            config: Language server configuration
        """
        self.config = config
        self.process: asyncio.subprocess.Process | None = None
        self.server_path: str | None = None

        # Translation engine for the configured file language. Documents in
        # other languages get their own, from `translator_for` (CORE-1976).
        self._default_language = config.file_language
        self.translator = self._build_translator(config.file_language)
        self._translators: dict[str, IncrementalTranslator] = {}

        # Document cache: uri -> (translated_content, source_map)
        self._document_cache: dict[str, Any] = {}

        # JSON-RPC request tracking
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._reader_task: asyncio.Task | None = None
        self._stderr_task: asyncio.Task | None = None
        self._initialized = False
        # Liveness of the read side, tracked apart from the handshake flag.
        # The reader can observe the stream die while `_initialize_server`
        # is still unwinding, and that coroutine would otherwise set
        # `_initialized = True` *after* the reader had cleared it.
        self._transport_alive = False

        # Performance tracking
        self._request_count = 0
        self._total_latency = 0.0

    def _build_translator(self, language: str) -> IncrementalTranslator:
        """A translator for documents written in ``language``.

        Keywords come from the language pack via `_get_keyword_map`; builtins
        are left untranslated because the proxy only needs the source to parse
        as canonical Python, and builtin names already do.
        """
        return IncrementalTranslator(
            source_lang=self.config.source_language,
            target_lang=language,
            keyword_map=self._get_keyword_map(language),
            builtin_map={},  # Optional: translate builtins
        )

    def translator_for(self, language: str | None) -> IncrementalTranslator:
        """The translator for documents written in ``language``.

        One per language, because each translator caches by content alone:
        shared across languages, the same text named as two languages would be
        answered from whichever was translated first. ``None`` is the
        configured file language (CORE-1976).
        """
        if language is None or language == self._default_language:
            return self.translator
        translator = self._translators.get(language)
        if translator is None:
            translator = self._build_translator(language)
            self._translators[language] = translator
        return translator

    def _get_keyword_map(self, lang: str) -> dict[str, str]:
        """Get keyword translation map for language.

        Uses cached LanguagePackLoader for performance (CORE-446).
        Creates reversed mapping (localized→English) for translation.

        Args:
            lang: Target language code (e.g., 'es', 'ar', 'zh')

        Returns:
            Dictionary mapping localized keywords to English, or empty dict on error

        Example:
            >>> proxy._get_keyword_map("es")
            {'definir': 'def', 'clase': 'class', ...}  # Reversed for translation
        """
        try:
            # Load language pack using cached loader (CORE-446)
            pack = _get_pack_loader().load(language=lang, target="python", version="3.10")

            # Build reverse map: localized → English
            reversed_map = {translated: english for english, translated in pack.keywords.items()}

            logger.debug(f"Loaded {len(reversed_map)} keyword translations for {lang}")

            return reversed_map

        except Exception as e:
            # Log warning and fall back to empty dict (pass-through mode)
            logger.warning(f"Failed to load language pack for '{lang}': {e}")
            return {}

    async def start(self) -> bool:
        """Start Pyright subprocess and initialize LSP connection.

        Returns:
            True if successfully started, False otherwise
        """
        if not self.config.enhanced_intelligence_enabled:
            logger.info("Enhanced Python intelligence disabled in config")
            return False

        # Find the language server
        self.server_path = self._find_language_server()
        if not self.server_path:
            # Loud on purpose. This feature defaults to enabled, so failing
            # quietly leaves the user with a thinner experience and no clue that
            # a richer one was meant to be there (CORE-1886).
            logger.warning(
                "Enhanced Python intelligence is enabled but no language server was found. "
                f"Install one with: {INSTALL_HINT}. "
                "Continuing with Legesher-only features."
            )
            return False

        try:
            # Start the language server. asyncio's subprocess gives us streams
            # we can await; the blocking equivalents would have to run on the
            # event loop thread, which is what deadlocked this proxy before.
            self.process = await asyncio.create_subprocess_exec(
                self.server_path,
                "--stdio",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=STREAM_LIMIT,
            )

            self._transport_alive = True

            # Start background reader and stderr drain
            self._reader_task = asyncio.create_task(self._read_responses())
            self._stderr_task = asyncio.create_task(self._drain_stderr())

            # Initialize LSP connection
            initialized = await self._initialize_server()
            if not initialized:
                logger.warning(
                    "Enhanced Python intelligence could not be started: the language "
                    f"server at {self.server_path} did not complete initialization. "
                    "Continuing with Legesher-only features."
                )
                await self.stop()
                return False

            logger.info(f"Language server started and initialized: {self.server_path}")
            return True

        except Exception as e:
            logger.warning(
                f"Enhanced Python intelligence could not be started: {e}. "
                "Continuing with Legesher-only features."
            )
            await self.stop()
            return False

    def _find_language_server(self) -> str | None:
        """Find an executable that can actually serve LSP.

        Checks, in order:
        1. Configured path (``config.language_server_path``)
        2. ``pyright-langserver`` on PATH
        3. ``pyright-langserver`` in the common install prefixes

        Finding only ``pyright`` counts as finding nothing: it is the CLI type
        checker, and spawning it produces a process that closes the stream
        instead of answering, which is indistinguishable from a hang until the
        request times out.

        Returns:
            Path to the language server executable, or None if unavailable
        """
        # Check configured path first — an explicit setting always wins.
        if self.config.language_server_path:
            if os.path.isfile(self.config.language_server_path):
                return self.config.language_server_path
            logger.warning(
                "Configured language server path does not exist: "
                f"{self.config.language_server_path}"
            )

        on_path = shutil.which(LANGSERVER_BIN)
        if on_path:
            return on_path

        for directory in FALLBACK_BIN_DIRS:
            candidate = os.path.join(directory, LANGSERVER_BIN)
            if os.path.isfile(candidate):
                return candidate

        # Distinguish "nothing installed" from "the wrong half installed": the
        # second is far more confusing to diagnose, and far more common, since
        # both binaries ship together.
        if shutil.which(CLI_BIN):
            logger.warning(
                f"Found `{CLI_BIN}` but not `{LANGSERVER_BIN}`. `{CLI_BIN}` is the "
                "command-line type checker and cannot serve LSP. Reinstall with: "
                f"{INSTALL_HINT}."
            )

        return None

    async def _initialize_server(self) -> bool:
        """Initialize Pyright with LSP initialize handshake.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Send initialize request
            init_params = {
                "processId": os.getpid(),
                "clientInfo": {"name": "legesher", "version": "0.1.0"},
                "rootUri": None,
                "capabilities": {
                    "textDocument": {
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "diagnostic": {"dynamicRegistration": False},
                    }
                },
            }

            response = await self._send_request("initialize", init_params, timeout=10.0)
            if not response or "error" in response:
                logger.error(f"Initialize request failed: {response}")
                return False

            # Send initialized notification
            await self._send_notification("initialized", {})

            self._initialized = True
            logger.debug("Pyright initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Pyright initialization failed: {e}")
            return False

    async def _send_request(self, method: str, params: dict, timeout: float = 5.0) -> dict | None:
        """Send JSON-RPC request to Pyright and wait for response.

        Args:
            method: LSP method name
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Response dictionary or None on error
        """
        if not self.process or not self.process.stdin:
            return None

        # Generate request ID
        self._request_id += 1
        request_id = self._request_id

        # Create JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Send request
            self.process.stdin.write(frame_message(request))
            await self.process.stdin.drain()

            logger.debug(f"Sent request {request_id}: {method}")

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            logger.warning(f"Request {request_id} timed out: {method}")
            self._pending_requests.pop(request_id, None)
            return None
        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            self._pending_requests.pop(request_id, None)
            return None

    async def _send_notification(self, method: str, params: dict) -> None:
        """Send JSON-RPC notification to Pyright (no response expected).

        Args:
            method: LSP method name
            params: Method parameters
        """
        if not self.process or not self.process.stdin:
            return

        # Create JSON-RPC notification (no id field)
        notification = {"jsonrpc": "2.0", "method": method, "params": params}

        try:
            self.process.stdin.write(frame_message(notification))
            await self.process.stdin.drain()

            logger.debug(f"Sent notification: {method}")

        except Exception as e:
            logger.error(f"Failed to send notification {method}: {e}")

    async def _read_responses(self) -> None:
        """Background task reading JSON-RPC messages from the server's stdout.

        Every read here awaits. That is the fix for CORE-1886: the previous
        version called the blocking ``readline()``/``read()`` from inside this
        task, which pinned the event loop thread inside a syscall. The response
        would arrive and resolve its future, then the reader would block again
        on the next read — leaving the loop unable to schedule the very
        coroutine that was waiting, or to fire the timeout meant to rescue it.
        """
        stdout = self.process.stdout if self.process else None
        if stdout is None:
            return

        try:
            while True:
                headers = await self._read_headers(stdout)
                if headers is None:
                    logger.debug("Language server closed its output stream")
                    break

                content_length = headers.get("content-length")
                if not content_length:
                    # Not a framed message we can act on; the stream is still
                    # positioned at a boundary, so keep going.
                    continue

                try:
                    length = int(content_length)
                except ValueError:
                    # A malformed header means we no longer know where the next
                    # message starts, so there is nothing safe to resynchronise
                    # to. Stop rather than read at a guessed offset.
                    logger.error(
                        f"Malformed Content-Length from language server: {content_length!r}"
                    )
                    break

                body = await stdout.readexactly(length)

                try:
                    message = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON message: {e}")
                    continue

                await self._handle_response(message)

        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError) as e:
            logger.debug(f"Language server stream ended: {e}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Response reader crashed: {e}")
        finally:
            # The reader is the only thing that can deliver a response, so once
            # it stops the transport is unusable even if the child is still
            # alive. Marking it uninitialized is what makes that visible: every
            # call site guards on `is_running() and initialized`, and
            # `legesher/status` reports the same pair. Without this a crashed
            # reader leaves the server claiming to be active while every request
            # burns its full timeout.
            self._transport_alive = False

            # Nothing further will arrive, so anyone still waiting would wait
            # forever. Wake them so they fail fast instead.
            self._fail_pending_requests()

    async def _read_headers(self, stdout: asyncio.StreamReader) -> dict[str, str] | None:
        """Read one LSP header block, or None at end of stream.

        Header lines are read individually rather than assumed to arrive
        together: nothing guarantees a write on the far end maps to one read on
        ours, and a server that fragments its output is entirely legal.
        """
        headers: dict[str, str] = {}

        while True:
            try:
                line = await stdout.readuntil(b"\r\n")
            except asyncio.IncompleteReadError:
                return None

            text = line.decode("utf-8").strip()
            if not text:
                return headers

            key, _, value = text.partition(":")
            headers[key.strip().lower()] = value.strip()

    async def _drain_stderr(self) -> None:
        """Continuously drain the server's stderr.

        stderr is a pipe with a finite OS buffer (~64 KiB). Left unread, a
        server that logs enough will block trying to write to it — and a blocked
        server never answers the request we are waiting on. Draining costs
        nothing and removes a whole class of stall.
        """
        stderr = self.process.stderr if self.process else None
        if stderr is None:
            return

        try:
            while True:
                line = await stderr.readline()
                if not line:
                    break
                logger.debug(f"[langserver] {line.decode('utf-8', errors='replace').rstrip()}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.debug(f"stderr drain ended: {e}")

    def _fail_pending_requests(self) -> None:
        """Resolve every in-flight request with None so no caller waits forever."""
        for request_id, future in list(self._pending_requests.items()):
            if not future.done():
                future.set_result(None)
            self._pending_requests.pop(request_id, None)

    async def _handle_response(self, response: dict) -> None:
        """Handle JSON-RPC response from Pyright.

        Args:
            response: Parsed JSON-RPC response
        """
        # An `id` alone does not mean "this answers us". In JSON-RPC the server
        # can send its own *requests* (workspace/configuration,
        # client/registerCapability), and those carry an id too — drawn from the
        # server's own counter, which overlaps ours. The discriminator is
        # `method`: requests have one, responses never do. Without this check an
        # id collision resolves the wrong future, so a hover silently returns
        # None while the real response is discarded.
        has_id = "id" in response
        has_method = "method" in response

        if has_id and not has_method:
            request_id = response["id"]
            future = self._pending_requests.pop(request_id, None)
            if future and not future.done():
                future.set_result(response)
                logger.debug(f"Received response for request {request_id}")
            else:
                logger.debug(f"Response for unknown or already-settled request {request_id}")
        elif has_id and has_method:
            # A request from the server. We do not implement any of these yet;
            # log it rather than mis-file it as a response.
            #
            # It goes unanswered, which JSON-RPC says it should not. That is
            # survivable only because our declared capabilities are minimal
            # enough that pyright asks for nothing — verified by probe. Declare
            # `workspace.configuration` or dynamic registration and it
            # immediately sends three requests that will wait forever. Tracked
            # in CORE-1898, which must land before those capabilities widen.
            logger.debug(f"Unhandled request from language server: {response.get('method')}")
        else:
            # This is a notification from server (e.g., diagnostics)
            logger.debug(f"Received notification: {response.get('method', 'unknown')}")

    async def stop(self) -> None:
        """Stop the language server subprocess gracefully.

        Safe to call repeatedly, and safe to call after a failed start: both
        happen in practice, and neither should raise.
        """
        process = self.process

        if process is not None:
            try:
                # Ask politely first, while the transport is still up.
                if self.initialized:
                    await self._send_request("shutdown", {}, timeout=2.0)
                    await self._send_notification("exit", {})

                if process.returncode is None:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                        logger.warning("Language server forcefully terminated")

                logger.info("Language server stopped")
            except (ProcessLookupError, OSError) as e:
                logger.debug(f"Language server already gone: {e}")
            finally:
                self.process = None
                self._initialized = False

        # Cancel background tasks only after the child is gone, so the reader
        # observes a clean end-of-stream rather than being cut off mid-message.
        for task in (self._reader_task, self._stderr_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._reader_task = None
        self._stderr_task = None
        self._fail_pending_requests()

    def is_running(self) -> bool:
        """Check if the language server subprocess is running.

        Returns:
            True if process is alive, False otherwise
        """
        return self.process is not None and self.process.returncode is None

    @property
    def initialized(self) -> bool:
        """Whether the LSP handshake completed.

        A live process is not the same as a usable one. It can be running and
        still not have answered ``initialize``, and it can have answered and
        since lost its read side — in both cases forwarding anything to it is
        pointless. Both conditions are folded in here so no caller has to
        remember to check the second one.
        """
        return self._initialized and self._transport_alive

    async def forward_hover(self, params: HoverParams) -> Hover | None:
        """Forward hover request to the language server with translation.

        Args:
            params: Hover request parameters

        Returns:
            Hover information or None if not available
        """
        if not self.is_running() or not self.initialized:
            return None

        start_time = time.time()

        try:
            uri = params.text_document.uri
            position = params.position

            # Get document content from cache or translate
            cache_entry = self._document_cache.get(uri)
            if not cache_entry:
                logger.debug(f"Document {uri} not in cache for hover")
                return None

            source_map = cache_entry["source_map"]

            # Translate position to English coordinates
            english_pos = source_map.to_english(
                Position(line=position.line, character=position.character)
            )

            # Send hover request to Pyright
            hover_params = {
                "textDocument": {"uri": uri},
                "position": {
                    "line": english_pos.line,
                    "character": english_pos.character,
                },
            }

            response = await self._send_request("textDocument/hover", hover_params)
            if not response or "error" in response:
                return None

            result = response.get("result")
            if not result:
                return None

            # Translate response position back to original
            if "range" in result:
                eng_range = result["range"]
                start_pos = source_map.to_original(
                    Position(
                        line=eng_range["start"]["line"],
                        character=eng_range["start"]["character"],
                    )
                )
                end_pos = source_map.to_original(
                    Position(
                        line=eng_range["end"]["line"],
                        character=eng_range["end"]["character"],
                    )
                )

                hover_range = Range(
                    start=Position(line=start_pos.line, character=start_pos.character),
                    end=Position(line=end_pos.line, character=end_pos.character),
                )
            else:
                hover_range = None

            # Create Hover object
            hover = Hover(contents=result.get("contents", ""), range=hover_range)

            # Track performance
            elapsed = time.time() - start_time
            self._request_count += 1
            self._total_latency += elapsed

            logger.debug(f"Hover completed in {elapsed * 1000:.1f}ms")
            return hover

        except Exception as e:
            logger.error(f"Hover forward failed: {e}")
            return None

    async def forward_diagnostic(
        self, uri: str, content: str, language: str | None = None
    ) -> list[Diagnostic]:
        """Forward diagnostic request to the language server with translation.

        Args:
            uri: Document URI
            content: Document content in localized language
            language: The language the document is written in; None for the
                configured file language

        Returns:
            List of diagnostics with translated messages
        """
        if not self.is_running() or not self.initialized:
            return []

        try:
            # Translate document to English
            result = await self.translator_for(language).translate_to_english(content)

            # Cache translation
            self._document_cache[uri] = {
                "translated": result.translated_code,
                "source_map": result.source_map,
                "hash": result.content_hash,
            }

            # Send didOpen to sync document with Pyright
            await self._send_notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": result.translated_code,
                    }
                },
            )

            # Request diagnostics
            diag_params = {"textDocument": {"uri": uri}}
            response = await self._send_request("textDocument/diagnostic", diag_params)

            if not response or "error" in response:
                return []

            result_data = response.get("result", {})
            items = result_data.get("items", [])

            # Translate diagnostics back to original positions
            diagnostics = []
            source_map = self._document_cache[uri]["source_map"]

            for item in items:
                # Translate range
                eng_range = item["range"]
                start_pos = source_map.to_original(
                    Position(
                        line=eng_range["start"]["line"],
                        character=eng_range["start"]["character"],
                    )
                )
                end_pos = source_map.to_original(
                    Position(
                        line=eng_range["end"]["line"],
                        character=eng_range["end"]["character"],
                    )
                )

                diag_range = Range(
                    start=Position(line=start_pos.line, character=start_pos.character),
                    end=Position(line=end_pos.line, character=end_pos.character),
                )

                # Create diagnostic. The message is the backend's own English
                # text, passed through untranslated: these are type-checker
                # findings, which the `diagnostic` provider's templates (built
                # for CPython's error messages) do not cover.
                diagnostic = Diagnostic(
                    range=diag_range,
                    message=item.get("message", ""),
                    severity=wire_severity(item.get("severity")),
                    source="pyright",
                )

                diagnostics.append(diagnostic)

            return diagnostics

        except Exception as e:
            logger.error(f"Diagnostic forward failed: {e}")
            return []

    async def translate_document_for_server(
        self, uri: str, content: str, language: str | None = None
    ) -> str | None:
        """Translate document content for the language server.

        Args:
            uri: Document URI
            content: Original content in localized language
            language: The language the document is written in; None for the
                configured file language

        Returns:
            Translated content in English or None on error
        """
        try:
            result = await self.translator_for(language).translate_to_english(content)

            # Cache for future position mappings
            self._document_cache[uri] = {
                "translated": result.translated_code,
                "source_map": result.source_map,
                "hash": result.content_hash,
            }

            return result.translated_code

        except Exception as e:
            logger.error(f"Translation failed for {uri}: {e}")
            return None

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        avg_latency = self._total_latency / self._request_count if self._request_count > 0 else 0

        return {
            "request_count": self._request_count,
            "total_latency_ms": self._total_latency * 1000,
            "average_latency_ms": avg_latency * 1000,
            "cache_size": len(self._document_cache),
            "translation_cache_size": sum(
                translator.get_cache_size() for translator in self._all_translators()
            ),
            "initialized": self.initialized,
        }

    def _all_translators(self) -> list[IncrementalTranslator]:
        """The configured language's translator and every per-language one built since."""
        return [self.translator, *self._translators.values()]

    def clear_caches(self) -> None:
        """Clear all caches."""
        self._document_cache.clear()
        for translator in self._all_translators():
            translator.clear_cache()
        logger.debug("Caches cleared")

    def __repr__(self) -> str:
        """String representation."""
        status = "running" if self.is_running() else "stopped"
        init_status = "initialized" if self.initialized else "not initialized"
        return f"EnhancedIntelligenceProxy(status={status}, {init_status}, path={self.server_path})"
