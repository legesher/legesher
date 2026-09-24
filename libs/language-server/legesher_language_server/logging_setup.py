"""Where everything this server logs actually goes (CORE-1979).

Under stdio transport, stdout *is* the JSON-RPC channel: a log line written
there corrupts the protocol stream. That leaves two destinations, and they are
not equivalent. An editor renders the server's stderr undifferentiated as
``[error]``, so a healthy startup arrives as forty red lines and a genuine
crash is camouflaged among them, which is exactly what happened the day this
was filed. The LSP's own ``window/logMessage`` notification carries a level the
client renders correctly, so that is the channel.

The routing rule is one sentence: forward through ``window/logMessage`` once a
connection exists, and fall back to stderr before one does. Records that can
wait are held, so they arrive with a real level instead of red; the ones that
cannot are written out immediately.

Verbosity is the client's to set. ``trace`` arrives in the initialization
options and again in ``$/setTrace``; ``verbose`` is what turns pygls's own
payload logging back on. Nothing dumps a JSON-RPC payload by default, because
those payloads carry text out of the user's file. ``off`` is the only setting
that keeps that text out of the log altogether: ``messages`` raises this
package to DEBUG, and its debug lines name the identifier under the cursor,
the hover text rendered for it, and the path of every document opened, changed
or closed.
"""

import logging
import sys
import threading
from collections import deque
from typing import Protocol, TextIO

from lsprotocol.types import LogMessageParams, MessageType, TraceValue

#: pygls logs whole JSON-RPC payloads through its own logger at INFO: the
#: 8KB ``InitializeParams`` dump, every response, every semantic-token array.
#: Its level is therefore set separately from ours.
PYGLS_LOGGER_NAME = "pygls"

#: This package's own logger, raised as a whole when the client asks for trace.
PACKAGE_LOGGER_NAME = "legesher_language_server"

#: Records logged before the connection exists are held until it does. Bounded
#: because a server started outside an editor never gets one.
MAX_BUFFERED_RECORDS = 200

_LEVEL_MESSAGE_TYPES = (
    (logging.ERROR, MessageType.Error),
    (logging.WARNING, MessageType.Warning),
    (logging.INFO, MessageType.Info),
)


def message_type_for_level(levelno: int) -> MessageType:
    """Map a Python logging level onto the LSP message type that matches it.

    Anything below INFO goes out as ``MessageType.Log`` rather than the more
    literal ``MessageType.Debug``. ``Debug`` is routed by the client into a
    level-gated logger and disappears unless the user has *also* raised their
    output channel's own level, which would make verbose mode look like it had
    done nothing. ``Log`` is appended verbatim.

    Args:
        levelno: A ``logging`` level number.

    Returns:
        The LSP message type a client should render this record as.
    """
    for threshold, message_type in _LEVEL_MESSAGE_TYPES:
        if levelno >= threshold:
            return message_type
    return MessageType.Log


class LogMessageSink(Protocol):
    """The part of a pygls server this handler needs: send a log notification."""

    def window_log_message(self, params: LogMessageParams) -> None:
        """Send a ``window/logMessage`` notification to the client."""
        ...


class LspLogHandler(logging.Handler):
    """Send log records to the client with their real severity.

    Falls back to a stream (stderr by default) whenever the LSP connection
    cannot carry the record: before the transport exists, and if a send fails.
    """

    def __init__(self, stream: TextIO | None = None) -> None:
        """Create the handler.

        Args:
            stream: Fallback destination. Defaults to ``sys.stderr``, which is
                the only channel available before a client connects.
        """
        super().__init__()
        self._server: LogMessageSink | None = None
        self._stream = stream
        # The level name travels with the message: a replayed record has to
        # print the same ``[WARNING]`` the direct path would have, and the
        # message type it maps to cannot be turned back into one (DEBUG and
        # NOTSET both become ``Log``).
        self._pending: deque[tuple[MessageType, str, str]] = deque(maxlen=MAX_BUFFERED_RECORDS)
        self._local = threading.local()

    def bind(self, server: LogMessageSink) -> None:
        """Attach the server whose connection carries forwarded records.

        Args:
            server: The pygls server. Records are forwarded only once its
                transport is up, so binding early is safe.
        """
        self._server = server

    @property
    def stream(self) -> TextIO:
        """The fallback stream, resolved late so a redirected stderr is honoured."""
        return sys.stderr if self._stream is None else self._stream

    def is_connected(self) -> bool:
        """Whether a forwarded record would actually reach the client."""
        protocol = getattr(self._server, "protocol", None)
        return getattr(protocol, "writer", None) is not None

    def emit(self, record: logging.LogRecord) -> None:
        """Route one record to the client, to the buffer, or to the stream."""
        if getattr(self._local, "emitting", False):
            # Sending a log message makes pygls log about sending it, and
            # forwarding *that* record would send another. The record describes
            # our own send and tells the user nothing, so it is dropped.
            return

        self._local.emitting = True
        try:
            message = self.format(record)
            if self.is_connected():
                self._drain()
                self._send(message_type_for_level(record.levelno), message, record.levelname)
            elif record.levelno >= logging.ERROR:
                # An error cannot wait for a connection that may never arrive:
                # a server that dies during startup has only stderr. What is
                # held goes out ahead of it, in order, because the lines in
                # front of a failure are the ones that explain it.
                self._drain_to_stream()
                self._write(record.levelname, message)
            else:
                self._pending.append(
                    (message_type_for_level(record.levelno), message, record.levelname)
                )
        except Exception:
            # A logging call site must never be the thing that fails.
            self.handleError(record)
        finally:
            self._local.emitting = False

    def flush(self) -> None:
        """Send anything held from before the connection existed."""
        if getattr(self._local, "emitting", False) or not self.is_connected():
            return

        self.acquire()
        self._local.emitting = True
        try:
            self._drain()
        finally:
            self._local.emitting = False
            self.release()

    def close(self) -> None:
        """Write out anything still held, then shut the handler down.

        ``logging.shutdown`` flushes and closes every handler at interpreter
        exit, but :meth:`flush` can only replay over a connection, so without
        this a server that died before one existed would drop its buffer in
        silence. That buffer is the interesting part: the WARNING in front of a
        fatal failure, and the startup lines that say what it was doing. stderr
        is a poor channel, but it is the one that is left.
        """
        try:
            self._drain_to_stream()
        finally:
            super().close()

    def _drain(self) -> None:
        """Replay the held records to the client, oldest first."""
        while self._pending:
            message_type, message, level_name = self._pending.popleft()
            self._send(message_type, message, level_name)

    def _drain_to_stream(self) -> None:
        """Write the held records to the fallback stream, oldest first."""
        self.acquire()
        try:
            while self._pending:
                _, message, level_name = self._pending.popleft()
                self._write(level_name, message)
        finally:
            self.release()

    def _send(self, message_type: MessageType, message: str, level_name: str) -> None:
        """Forward one record, falling back to the stream if the send fails."""
        server = self._server
        if server is None:
            self._write(level_name, message)
            return

        try:
            server.window_log_message(LogMessageParams(type=message_type, message=message))
        except Exception:
            # A dead or half-open connection must not swallow the record.
            self._write(level_name, message)

    def _write(self, level_name: str, message: str) -> None:
        """Write to the fallback stream, carrying the level the client would have rendered."""
        stream = self.stream
        stream.write(f"[{level_name}] {message}\n")
        stream.flush()


_handler: LspLogHandler | None = None
_configured_level: int = logging.INFO

#: What each trace value means here, as ``(this package's level, pygls's
#: level)``. ``off`` leaves our own logger at whatever was configured.
#: ``messages`` raises ours without unmuting pygls, because pygls has no level
#: that logs a method name without also logging its payload. Only ``verbose``
#: turns payload logging on, which is why it has to be asked for.
#:
#: ``verbose`` is the only value that logs whole JSON-RPC *payloads*. It is not
#: the only one that logs document-derived content: ``messages`` puts this
#: package at DEBUG, which unmutes the word under the cursor and the rendered
#: hover text in ``providers/hover.py``, the document paths logged by the
#: did-open/did-change/did-close handlers, and the backend's own stderr in
#: ``enhanced_intelligence``.
#:
#: Do not promise that ``off`` is content-free. An error logged at any level
#: can name the document's path, and an exception repr can embed a source line
#: (``IndentationError`` and ``TabError`` carry one, which is why
#: ``providers/semantic_tokens.py`` catches ``SyntaxError`` alongside
#: ``TokenError`` rather than letting it reach a catch-all at error level).
#: The safe user-facing claim is that no text out of the file is logged at
#: ``off``, while an error may still name the path and position that failed.
_TRACE_LEVELS: dict[TraceValue, tuple[int | None, int]] = {
    TraceValue.Off: (None, logging.WARNING),
    TraceValue.Messages: (logging.DEBUG, logging.WARNING),
    TraceValue.Verbose: (logging.DEBUG, logging.DEBUG),
}


def _coerce_trace(trace: object) -> TraceValue:
    """Read a client's trace setting, treating anything unrecognised as off."""
    if isinstance(trace, TraceValue):
        return trace
    try:
        return TraceValue(str(trace).lower())
    except ValueError:
        return TraceValue.Off


def configure_logging(log_level: str, stream: TextIO | None = None) -> LspLogHandler:
    """Install LSP-aware routing as the only destination for log records.

    Args:
        log_level: Level name (``DEBUG``/``INFO``/``WARNING``/``ERROR``).
            Unrecognised names fall back to ``INFO`` rather than crashing the
            server over a logging setting.
        stream: Fallback stream, for tests. Defaults to ``sys.stderr``.

    Returns:
        The installed handler, so the caller can bind the server to it.
    """
    global _handler, _configured_level

    level = getattr(logging, log_level.upper(), None)
    _configured_level = level if isinstance(level, int) else logging.INFO

    handler = LspLogHandler(stream=stream)
    # No timestamp and no level: the client stamps and colours each line
    # itself, so repeating either here only makes the channel harder to read.
    # The stream fallback re-adds the level, since nothing else would.
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))

    root = logging.getLogger()
    for existing in list(root.handlers):
        # Drop only the handlers that would undo this: another copy of
        # ourselves, and anything writing to the standard streams. A stderr
        # handler re-creates the wall of red; a stdout handler is worse, since
        # under stdio transport it writes into the JSON-RPC stream itself.
        if isinstance(existing, LspLogHandler) or getattr(existing, "stream", None) in (
            sys.stderr,
            sys.stdout,
        ):
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(_configured_level)

    _handler = handler
    apply_trace_value(TraceValue.Off)
    return handler


def apply_trace_value(trace: object) -> TraceValue:
    """Set verbosity from the client's ``trace`` setting.

    Does nothing to logger levels unless :func:`configure_logging` installed
    them. Embedding the server in a process with its own logging setup is a
    reasonable thing to do, and a client's trace setting is no reason to
    rearrange configuration we did not create.

    Args:
        trace: A ``TraceValue``, the string a client sent, or ``None``.

    Returns:
        The trace value that was applied.
    """
    value = _coerce_trace(trace)
    if _handler is None:
        return value

    package_level, pygls_level = _TRACE_LEVELS[value]

    logging.getLogger(PACKAGE_LOGGER_NAME).setLevel(
        _configured_level if package_level is None else package_level
    )
    logging.getLogger(PYGLS_LOGGER_NAME).setLevel(pygls_level)

    if _handler is not None:
        _handler.flush()

    return value


def get_handler() -> LspLogHandler | None:
    """The installed handler, or ``None`` when logging was never configured."""
    return _handler
