"""Tests for log routing, level mapping and trace gating (CORE-1979).

What is actually testable here is the contract the output channel depends on:
which LSP message type a record goes out as, where a record goes when no
connection exists yet, and which loggers each trace value turns up. How VS Code
paints the result is not.
"""

import io
import logging
import sys

import pytest
from lsprotocol.types import (
    ClientCapabilities,
    DidOpenTextDocumentParams,
    InitializeParams,
    LogMessageParams,
    MessageType,
    Position,
    SetTraceParams,
    TextDocumentItem,
    TraceValue,
)

from legesher_language_server import logging_setup
from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.logging_setup import (
    MAX_BUFFERED_RECORDS,
    PACKAGE_LOGGER_NAME,
    PYGLS_LOGGER_NAME,
    LspLogHandler,
    apply_trace_value,
    configure_logging,
    message_type_for_level,
)
from legesher_language_server.providers import (
    provide_completion,
    provide_hover,
    provide_semantic_tokens,
)
from legesher_language_server.server import LegesherLanguageServer


class FakeProtocol:
    """Stands in for pygls's protocol object: has a writer once connected."""

    def __init__(self, connected: bool = True) -> None:
        self.writer = object() if connected else None


class FakeServer:
    """Records what would have gone out over ``window/logMessage``."""

    def __init__(self, connected: bool = True) -> None:
        self.protocol = FakeProtocol(connected)
        self.sent: list[LogMessageParams] = []

    def connect(self) -> None:
        self.protocol.writer = object()

    def window_log_message(self, params: LogMessageParams) -> None:
        self.sent.append(params)


class ChattyServer(FakeServer):
    """A server that logs while sending, the way pygls does."""

    def window_log_message(self, params: LogMessageParams) -> None:
        logging.getLogger("pygls.protocol.json_rpc").error("Sending data: %s", params.message)
        super().window_log_message(params)


class BrokenServer(FakeServer):
    """A server whose connection fails mid-send."""

    def window_log_message(self, params: LogMessageParams) -> None:
        raise BrokenPipeError("connection went away")


@pytest.fixture
def restore_logging():
    """Put global logging state back however the test leaves it.

    ``configure_logging`` reaches into the root logger and into module state,
    both of which outlive a test. Restoring them is what stops a test that asks
    for verbose logging from quietly deciding what a later test can see.
    """
    root = logging.getLogger()
    saved_handlers = list(root.handlers)
    saved_root_level = root.level
    saved_levels = {
        name: logging.getLogger(name).level for name in (PACKAGE_LOGGER_NAME, PYGLS_LOGGER_NAME)
    }
    saved_handler = logging_setup._handler
    saved_configured_level = logging_setup._configured_level

    yield

    for handler in list(root.handlers):
        if handler not in saved_handlers:
            root.removeHandler(handler)
    for handler in saved_handlers:
        if handler not in root.handlers:
            root.addHandler(handler)
    root.setLevel(saved_root_level)
    for name, level in saved_levels.items():
        logging.getLogger(name).setLevel(level)
    logging_setup._handler = saved_handler
    logging_setup._configured_level = saved_configured_level


def make_record(level: int, message: str = "hello") -> logging.LogRecord:
    """Build a record without going through a logger."""
    return logging.LogRecord(
        name="legesher_language_server.test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def make_handler(server: FakeServer | None, stream: io.StringIO) -> LspLogHandler:
    """A handler wired the way ``configure_logging`` wires one."""
    handler = LspLogHandler(stream=stream)
    handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    if server is not None:
        handler.bind(server)
    return handler


class TestLevelMapping:
    """A record's level has to survive the trip to the client."""

    @pytest.mark.parametrize(
        ("levelno", "expected"),
        [
            (logging.CRITICAL, MessageType.Error),
            (logging.ERROR, MessageType.Error),
            (logging.WARNING, MessageType.Warning),
            (logging.INFO, MessageType.Info),
            (logging.DEBUG, MessageType.Log),
            (logging.NOTSET, MessageType.Log),
        ],
    )
    def test_level_maps_to_message_type(self, levelno, expected):
        """Each logging level maps to the message type a client renders it as."""
        assert message_type_for_level(levelno) == expected

    def test_info_is_not_an_error(self):
        """The whole defect in one assertion: INFO must not present as an error."""
        assert message_type_for_level(logging.INFO) != MessageType.Error

    def test_levels_between_the_named_ones_round_down(self):
        """A custom level sits with the named level below it, not above."""
        assert message_type_for_level(logging.INFO + 1) == MessageType.Info
        assert message_type_for_level(logging.WARNING - 1) == MessageType.Info


class TestRouting:
    """Where a record goes depends on whether a connection can carry it."""

    def test_connected_records_go_to_the_client(self):
        """With a live transport, records are forwarded, not written to stderr."""
        server = FakeServer()
        stream = io.StringIO()
        handler = make_handler(server, stream)

        handler.emit(make_record(logging.INFO, "started"))

        assert [params.type for params in server.sent] == [MessageType.Info]
        assert "started" in server.sent[0].message
        assert stream.getvalue() == ""

    def test_records_before_the_connection_are_replayed_in_order(self):
        """Startup happens before the transport exists; those lines still count."""
        server = FakeServer(connected=False)
        stream = io.StringIO()
        handler = make_handler(server, stream)

        handler.emit(make_record(logging.INFO, "first"))
        handler.emit(make_record(logging.WARNING, "second"))
        assert server.sent == []
        assert stream.getvalue() == ""

        server.connect()
        handler.emit(make_record(logging.INFO, "third"))

        assert [params.message.split(": ")[-1] for params in server.sent] == [
            "first",
            "second",
            "third",
        ]
        assert [params.type for params in server.sent] == [
            MessageType.Info,
            MessageType.Warning,
            MessageType.Info,
        ]

    def test_flush_replays_without_a_new_record(self):
        """A connection that comes up quietly still gets what was held."""
        server = FakeServer(connected=False)
        handler = make_handler(server, io.StringIO())
        handler.emit(make_record(logging.INFO, "held"))

        server.connect()
        handler.flush()

        assert len(server.sent) == 1

    def test_errors_before_the_connection_go_to_the_stream(self):
        """A crash during startup has only stderr, and must not wait for a client."""
        server = FakeServer(connected=False)
        stream = io.StringIO()
        handler = make_handler(server, stream)

        handler.emit(make_record(logging.ERROR, "it broke"))

        assert "it broke" in stream.getvalue()
        assert "[ERROR]" in stream.getvalue()

        # And it is not replayed once the client turns up: it was delivered.
        server.connect()
        handler.flush()
        assert server.sent == []

    def test_an_error_takes_the_held_lines_with_it(self):
        """The warning in front of a fatal failure is the one that explains it."""
        server = FakeServer(connected=False)
        stream = io.StringIO()
        handler = make_handler(server, stream)

        handler.emit(make_record(logging.INFO, "loading pack es"))
        handler.emit(make_record(logging.WARNING, "pack es failed to load"))
        handler.emit(make_record(logging.ERROR, "server error: no pack"))

        written = stream.getvalue()
        assert "loading pack es" in written
        assert "pack es failed to load" in written
        # In order, and ahead of the error, so the log reads as a sequence.
        assert (
            written.index("loading pack es")
            < written.index("pack es failed to load")
            < written.index("server error: no pack")
        )

    def test_closing_without_a_connection_writes_the_buffer_out(self):
        """`logging.shutdown` closes every handler; the buffer must not die there."""
        server = FakeServer(connected=False)
        stream = io.StringIO()
        handler = make_handler(server, stream)

        handler.emit(make_record(logging.INFO, "startup line"))
        handler.emit(make_record(logging.WARNING, "something looked wrong"))
        assert stream.getvalue() == ""

        handler.close()

        written = stream.getvalue()
        assert "[INFO] " in written
        assert "startup line" in written
        assert "[WARNING] " in written
        assert "something looked wrong" in written

    def test_closing_after_a_connection_replays_nothing_twice(self):
        """What the client already received must not reappear on stderr."""
        server = FakeServer(connected=False)
        stream = io.StringIO()
        handler = make_handler(server, stream)
        handler.emit(make_record(logging.INFO, "held"))

        server.connect()
        handler.flush()
        handler.close()

        assert len(server.sent) == 1
        assert stream.getvalue() == ""

    def test_a_replayed_record_keeps_its_own_level_label(self):
        """A replayed DEBUG falling back to the stream is `[DEBUG]`, not `[LOG]`."""
        server = BrokenServer(connected=False)
        stream = io.StringIO()
        handler = make_handler(server, stream)

        handler.emit(make_record(logging.DEBUG, "replayed detail"))
        server.connect()
        handler.flush()

        assert "[DEBUG] " in stream.getvalue()
        assert "[LOG]" not in stream.getvalue()

    def test_a_closed_record_keeps_its_own_level_label(self):
        """The same label on the close path: the buffer carries the levelname."""
        stream = io.StringIO()
        handler = make_handler(FakeServer(connected=False), stream)

        handler.emit(make_record(logging.DEBUG, "never delivered"))
        handler.close()

        assert "[DEBUG] " in stream.getvalue()
        assert "[LOG]" not in stream.getvalue()

    def test_unbound_handler_writes_to_the_stream(self):
        """Before a server exists at all, everything falls back to the stream."""
        handler = make_handler(None, io.StringIO())
        handler.emit(make_record(logging.ERROR, "no server yet"))

        assert "no server yet" in handler.stream.getvalue()

    def test_a_failed_send_falls_back_to_the_stream(self):
        """A half-open connection must not swallow the record."""
        stream = io.StringIO()
        handler = make_handler(BrokenServer(), stream)

        handler.emit(make_record(logging.WARNING, "still important"))

        assert "still important" in stream.getvalue()

    def test_logging_about_the_send_does_not_recurse(self, restore_logging):
        """pygls logs while sending; forwarding that would send again, forever."""
        server = ChattyServer()
        handler = make_handler(server, io.StringIO())
        logging.getLogger(PYGLS_LOGGER_NAME).setLevel(logging.DEBUG)
        logging.getLogger().addHandler(handler)

        logging.getLogger("legesher_language_server.test").error("real problem")

        assert len(server.sent) == 1
        assert "real problem" in server.sent[0].message

    def test_the_buffer_is_bounded(self):
        """A server nobody connects to cannot grow its backlog without limit."""
        server = FakeServer(connected=False)
        handler = make_handler(server, io.StringIO())
        for index in range(MAX_BUFFERED_RECORDS * 2):
            handler.emit(make_record(logging.INFO, f"line {index}"))

        server.connect()
        handler.flush()

        assert len(server.sent) == MAX_BUFFERED_RECORDS
        # The oldest go, not the newest: what happened most recently is what
        # someone reading a log after a failure needs.
        assert server.sent[-1].message.endswith(f"line {MAX_BUFFERED_RECORDS * 2 - 1}")


class TestConfigureLogging:
    """Installing the handler has to quiet pygls at the same time."""

    def test_pygls_payload_logging_is_off_by_default(self, restore_logging):
        """The 8KB InitializeParams dump is a pygls INFO record. Not by default."""
        configure_logging("INFO", stream=io.StringIO())

        assert not logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.INFO)
        assert logging.getLogger("pygls.feature_manager").isEnabledFor(logging.WARNING)

    def test_our_own_info_still_reaches_the_handler(self, restore_logging):
        """Quieting pygls must not quiet us."""
        configure_logging("INFO", stream=io.StringIO())

        assert logging.getLogger(PACKAGE_LOGGER_NAME).isEnabledFor(logging.INFO)

    def test_the_handler_replaces_a_stream_handler(self, restore_logging):
        """A leftover stderr handler would keep printing the wall of red."""
        stderr_handler = logging.StreamHandler(sys.stderr)
        logging.getLogger().addHandler(stderr_handler)

        configure_logging("INFO", stream=io.StringIO())

        handlers = logging.getLogger().handlers
        assert stderr_handler not in handlers
        assert sum(isinstance(h, LspLogHandler) for h in handlers) == 1

    def test_a_leftover_stdout_handler_is_removed(self, restore_logging):
        """The dangerous one: under stdio transport stdout is the JSON-RPC stream.

        A stderr handler only makes the output channel ugly. A handler writing
        to stdout writes log text into the protocol itself, and the client
        drops the connection over the framing error.
        """
        stdout_handler = logging.StreamHandler(sys.stdout)
        logging.getLogger().addHandler(stdout_handler)

        configure_logging("INFO", stream=io.StringIO())

        handlers = logging.getLogger().handlers
        assert stdout_handler not in handlers
        assert not [h for h in handlers if getattr(h, "stream", None) is sys.stdout]

    def test_nothing_the_server_logs_reaches_stdout(self, restore_logging, capsys):
        """End to end on the invariant: a configured server writes no stdout."""
        stderr_fallback = io.StringIO()
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        configure_logging("DEBUG", stream=stderr_fallback)

        logger = logging.getLogger(f"{PACKAGE_LOGGER_NAME}.test")
        logger.info("startup line")
        logger.error("and a failure")

        assert capsys.readouterr().out == ""
        assert "and a failure" in stderr_fallback.getvalue()

    def test_a_second_call_does_not_double_every_line(self, restore_logging):
        """Configuring twice must not leave two of us on the root logger."""
        configure_logging("INFO", stream=io.StringIO())
        configure_logging("INFO", stream=io.StringIO())

        handlers = logging.getLogger().handlers
        assert sum(isinstance(h, LspLogHandler) for h in handlers) == 1

    def test_an_unknown_level_name_does_not_crash_the_server(self, restore_logging):
        """A bad logging setting is not a reason to fail to start."""
        configure_logging("SHOUTING", stream=io.StringIO())

        assert logging.getLogger().level == logging.INFO


class TestTraceGating:
    """Verbose costs privacy and readability, so it has to be asked for."""

    def test_off_keeps_payloads_out_of_the_log(self, restore_logging):
        configure_logging("INFO", stream=io.StringIO())
        apply_trace_value(TraceValue.Off)

        assert not logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.INFO)
        assert not logging.getLogger(PACKAGE_LOGGER_NAME).isEnabledFor(logging.DEBUG)

    def test_messages_raises_our_logger_but_not_payloads(self, restore_logging):
        configure_logging("INFO", stream=io.StringIO())
        apply_trace_value("messages")

        assert logging.getLogger(PACKAGE_LOGGER_NAME).isEnabledFor(logging.DEBUG)
        assert not logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.INFO)

    def test_verbose_turns_payload_logging_on(self, restore_logging):
        configure_logging("INFO", stream=io.StringIO())
        apply_trace_value("verbose")

        assert logging.getLogger(PACKAGE_LOGGER_NAME).isEnabledFor(logging.DEBUG)
        assert logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.DEBUG)

    def test_verbose_is_reversible(self, restore_logging):
        """Turning trace back off has to actually cost nothing again."""
        configure_logging("INFO", stream=io.StringIO())
        apply_trace_value("verbose")
        apply_trace_value("off")

        assert not logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.INFO)
        assert not logging.getLogger(PACKAGE_LOGGER_NAME).isEnabledFor(logging.DEBUG)

    @pytest.mark.parametrize("value", [None, "", "VERBOSE!", 3, "true"])
    def test_anything_unrecognised_means_off(self, restore_logging, value):
        """A client's typo must not silently turn payload logging on."""
        configure_logging("INFO", stream=io.StringIO())

        assert apply_trace_value(value) == TraceValue.Off

    def test_case_is_not_a_trap(self, restore_logging):
        configure_logging("INFO", stream=io.StringIO())

        assert apply_trace_value("Verbose") == TraceValue.Verbose

    def test_a_configured_debug_level_survives_trace_off(self, restore_logging):
        """--log-level DEBUG is the operator's choice; trace off must not undo it."""
        configure_logging("DEBUG", stream=io.StringIO())
        apply_trace_value("verbose")
        apply_trace_value("off")

        assert logging.getLogger(PACKAGE_LOGGER_NAME).isEnabledFor(logging.DEBUG)


@pytest.fixture
def server():
    """A server configured the way a Spanish session would be."""
    return LegesherLanguageServer(
        LanguageServerConfig(source_language="en", target_language="es", python_version="3.10")
    )


class TestServerTraceHandling:
    """The trace setting arrives from the client and has to be acted on."""

    @pytest.mark.asyncio
    async def test_initialize_applies_the_trace_option(self, restore_logging, server):
        """`trace: verbose` in the init options is what the extension sends."""
        configure_logging("INFO", stream=io.StringIO())
        await server.on_initialize(
            InitializeParams(
                process_id=None,
                root_uri="file:///test",
                capabilities=ClientCapabilities(),
                initialization_options={"targetLanguage": "es", "trace": "verbose"},
            )
        )

        assert logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.DEBUG)

    @pytest.mark.asyncio
    async def test_initialize_without_trace_stays_quiet(self, restore_logging, server):
        """The default session logs no payloads."""
        configure_logging("INFO", stream=io.StringIO())
        await server.on_initialize(
            InitializeParams(
                process_id=None,
                root_uri="file:///test",
                capabilities=ClientCapabilities(),
                initialization_options={"targetLanguage": "es"},
            )
        )

        assert not logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.INFO)

    @pytest.mark.asyncio
    async def test_the_protocol_trace_field_is_honoured(self, restore_logging, server):
        """A client that sets trace where the protocol puts it is heard too."""
        configure_logging("INFO", stream=io.StringIO())
        await server.on_initialize(
            InitializeParams(
                process_id=None,
                root_uri="file:///test",
                capabilities=ClientCapabilities(),
                trace=TraceValue.Verbose,
            )
        )

        assert logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.DEBUG)

    @pytest.mark.asyncio
    async def test_set_trace_changes_it_mid_session(self, restore_logging, server):
        """No restart to get detail, and no restart to stop paying for it."""
        configure_logging("INFO", stream=io.StringIO())

        await server.on_set_trace(SetTraceParams(value=TraceValue.Verbose))
        assert logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.DEBUG)

        await server.on_set_trace(SetTraceParams(value=TraceValue.Off))
        assert not logging.getLogger("pygls.protocol.json_rpc").isEnabledFor(logging.INFO)

    @pytest.mark.asyncio
    async def test_initialize_logs_no_debug_scaffolding(self, restore_logging, server, caplog):
        """The `DEBUG:` lines were a developer talking to themselves."""
        with caplog.at_level(logging.INFO, logger=PACKAGE_LOGGER_NAME):
            await server.on_initialize(
                InitializeParams(
                    process_id=None,
                    root_uri="file:///test",
                    capabilities=ClientCapabilities(),
                    initialization_options={"targetLanguage": "es"},
                )
            )

        assert not [record for record in caplog.records if "DEBUG:" in record.getMessage()]

    @pytest.mark.asyncio
    async def test_initialize_reports_the_languages_once(self, restore_logging, server, caplog):
        """A log that answers "which language" twice answers it not at all."""
        with caplog.at_level(logging.INFO, logger=PACKAGE_LOGGER_NAME):
            await server.on_initialize(
                InitializeParams(
                    process_id=None,
                    root_uri="file:///test",
                    capabilities=ClientCapabilities(),
                    initialization_options={"targetLanguage": "es"},
                )
            )

        resolved = [r for r in caplog.records if "Languages resolved" in r.getMessage()]
        assert len(resolved) == 1
        assert "file=es" in resolved[0].getMessage()


class TestDocumentContentStaysOutOfTheLog:
    """Hover and diagnostics carry text from the user's file. Logs should not.

    "Should not" is level-dependent, and the docs have to say which level. Only
    `off` is content-free; `messages` raises this package to DEBUG and the
    debug lines do name identifiers out of the open file. Both halves are
    asserted here so the README and `logging_setup`'s trace table cannot drift
    back into claiming otherwise.
    """

    @pytest.mark.asyncio
    async def test_debug_records_do_carry_document_identifiers(
        self, restore_logging, server, caplog
    ):
        """The honest half of the claim: `messages` is not a private setting.

        If this ever stops being true, the documentation is the thing to
        change, not this test.
        """
        secret = "contrasena_del_banco"
        text = f"def {secret}():\n    return '{secret}_valor'\n"
        server.document_manager.open_document(
            uri="file:///secret.py", text=text, version=1, language_id="python"
        )

        with caplog.at_level(logging.DEBUG, logger=PACKAGE_LOGGER_NAME):
            await provide_hover(server, "file:///secret.py", Position(line=0, character=6))

        logged = "\n".join(record.getMessage() for record in caplog.records)
        assert secret in logged

    @pytest.mark.asyncio
    async def test_no_default_level_record_carries_document_text(self, server, caplog):
        """Exercise the providers over a document full of distinctive strings."""
        secret = "contrasena_del_banco"
        text = f"def {secret}():\n    return '{secret}_valor'\n"
        server.document_manager.open_document(
            uri="file:///secret.py", text=text, version=1, language_id="python"
        )

        with caplog.at_level(logging.INFO, logger=PACKAGE_LOGGER_NAME):
            await provide_hover(server, "file:///secret.py", Position(line=0, character=6))
            await provide_completion(server, "file:///secret.py", Position(line=0, character=6))
            provide_semantic_tokens(server, "file:///secret.py")

        logged = "\n".join(record.getMessage() for record in caplog.records)
        assert secret not in logged

    @pytest.mark.asyncio
    async def test_a_half_edited_document_does_not_log_its_source_line(self, server, caplog):
        """A bad dedent must not put the offending line in the log.

        IndentationError and TabError are SyntaxError subclasses rather than
        TokenError ones, and both carry the source line in their repr. Before
        the semantic-tokens provider caught SyntaxError they reached its
        catch-all and were logged at ERROR with a traceback, so the user's own
        line appeared at the default level, on every keystroke that left the
        file mid-edit. Any editor re-requests tokens while you type, so this is
        an ordinary state, not an exotic one.
        """
        secret = "contrasena_del_banco"
        text = f"def f():\n    {secret}_a = 1\n  {secret}_b = 2\n"
        server.document_manager.open_document(
            uri="file:///half_edited.py", text=text, version=1, language_id="python"
        )

        with caplog.at_level(logging.INFO, logger=PACKAGE_LOGGER_NAME):
            provide_semantic_tokens(server, "file:///half_edited.py")

        logged = "\n".join(record.getMessage() for record in caplog.records)
        assert secret not in logged

    @pytest.mark.asyncio
    async def test_a_tab_space_mix_does_not_log_its_source_line(self, server, caplog):
        """The TabError half of the same defect."""
        secret = "numero_de_tarjeta"
        text = f"def f():\n\t{secret}_a = 1\n        {secret}_b = 2\n"
        server.document_manager.open_document(
            uri="file:///tabs.py", text=text, version=1, language_id="python"
        )

        with caplog.at_level(logging.INFO, logger=PACKAGE_LOGGER_NAME):
            provide_semantic_tokens(server, "file:///tabs.py")

        logged = "\n".join(record.getMessage() for record in caplog.records)
        assert secret not in logged

    @pytest.mark.asyncio
    async def test_opening_a_document_does_not_log_its_text(self, server, caplog):
        """did_open carries the whole file; the log gets none of it."""
        secret = "numero_de_tarjeta"
        params_text = f"{secret} = 1234\n"

        with caplog.at_level(logging.INFO, logger=PACKAGE_LOGGER_NAME):
            await server.on_did_open(
                DidOpenTextDocumentParams(
                    text_document=TextDocumentItem(
                        uri="file:///card.py",
                        language_id="python",
                        version=1,
                        text=params_text,
                    )
                )
            )

        logged = "\n".join(record.getMessage() for record in caplog.records)
        assert secret not in logged
