"""Transport-level tests for EnhancedIntelligenceProxy (CORE-1886).

These cover the two defects that kept the Pyright proxy from ever completing an
LSP handshake, plus a latent framing bug found in the same code path:

1. Discovery searched for ``pyright`` — the command-line type checker — rather
   than ``pyright-langserver``. The CLI does not speak LSP over stdio; it closes
   the stream, so ``initialize`` never gets an answer.
2. The response reader was an ``async`` task performing *blocking* reads, which
   wedges the event loop thread. The handshake payload was always correct; the
   transport underneath it was not.
3. ``Content-Length`` counted characters rather than encoded bytes, which
   desynchronises the stream for any non-ASCII payload — i.e. for exactly the
   localized code and translated diagnostics this proxy exists to carry.

Most tests here drive a stub server (``fixtures/stub_langserver.py``) rather
than a real ``pyright-langserver``. That is deliberate: a real server gives one
happy path and cannot be asked to flood stderr, dribble a response out in
fragments, or go silent — the conditions that actually break a stdio transport.
The stub also gives the transport deterministic coverage on machines with no
Node toolchain. Two integration tests still run against the real binary, to
catch the case where the stub and reality have drifted apart.

A note on why several tests drive ``start()`` from a worker thread: when the
event loop is blocked by a synchronous read, ``asyncio.wait_for`` cannot fire,
because firing a timeout requires the very loop that is stuck. An in-loop
timeout would hang forever instead of failing. Imposing the deadline from
*outside* that thread is what turns a hang into an ordinary test failure.
"""

import asyncio
import concurrent.futures
import logging
import os
import shutil
import sys
import time
from pathlib import Path

import pytest
from lsprotocol.types import HoverParams, Position, TextDocumentIdentifier

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import (
    EnhancedIntelligenceProxy,
    default_fallback_bin_dirs,
)

STUB = Path(__file__).parent / "fixtures" / "stub_langserver.py"

# The real langserver is a developer-machine dependency, not a packaged one, so
# the one test that needs it skips when it is absent — but the skip is reported
# loudly by the terminal summary hook in conftest, because a drift check that
# silently does not run is indistinguishable from one that passed.
LANGSERVER = shutil.which("pyright-langserver")

# Set in the weekly drift workflow. There, a missing binary is the failure being
# looked for, not a reason to opt out of looking.
REQUIRE_LANGSERVER = os.environ.get("LEGESHER_REQUIRE_LANGSERVER") == "1"

requires_langserver = pytest.mark.skipif(
    LANGSERVER is None and not REQUIRE_LANGSERVER,
    reason="pyright-langserver not installed (npm install -g pyright)",
)

DEADLINE = 25.0

# The longest the event loop may go unserviced while a handshake is in flight.
# Generous enough to absorb process spawn and CI scheduling jitter, far below
# the multi-second stalls a blocking read produces.
MAX_LOOP_STALL = 1.0


def _force_kill(proxy: EnhancedIntelligenceProxy) -> None:
    """Kill the child so a wedged reader thread can unwind.

    A blocked ``readline()`` returns as soon as the pipe closes, so killing the
    subprocess is what releases the thread. Without this a failed run would leak
    a stuck thread for the rest of the session.
    """
    process = getattr(proxy, "process", None)
    if process is not None:
        try:
            process.kill()
        except (ProcessLookupError, OSError, ValueError):
            pass


def _run_off_loop(coro, proxy: EnhancedIntelligenceProxy, timeout: float = DEADLINE):
    """Run ``coro`` in its own thread and event loop, under an external deadline.

    The deadline has to be imposed from outside the loop under test: a blocked
    loop cannot fire its own timeout.
    """
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(asyncio.run, coro)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        _force_kill(proxy)
        pytest.fail(
            f"did not return within {timeout}s — the event loop is blocked by "
            "synchronous reads in the response reader, so neither a resolved "
            "future nor a request timeout can ever be scheduled."
        )
    finally:
        # Never wait: if the thread is still wedged, joining it would hang the run.
        executor.shutdown(wait=False)


async def _start_and_snapshot(proxy: EnhancedIntelligenceProxy) -> dict:
    """Start the proxy, record its state while alive, then stop it.

    All of it inside one event loop. An asyncio subprocess transport belongs to
    the loop that created it, so inspecting or tearing it down from a different
    loop afterwards is something production never does — and it makes asyncio
    complain about a closed loop during cleanup.
    """
    started = await proxy.start()
    snapshot = {
        "started": started,
        "running": proxy.is_running(),
        "initialized": proxy.initialized,
        "server_path": proxy.server_path,
    }
    await proxy.stop()
    return snapshot


def _make_executable(directory: Path, name: str) -> Path:
    """Drop a real (trivial) executable on disk so discovery can find it.

    Real files on a real PATH beat monkeypatching ``shutil.which``: the test
    then asserts on what discovery *chose*, not on how it went looking.

    Windows resolves executables through PATHEXT rather than a shebang, so the
    file needs the extension there. Callers compare stems, not full names, so
    the difference stays inside this helper.
    """
    if sys.platform == "win32":
        path = directory / f"{name}.cmd"
        path.write_text("@echo off\r\nexit /b 0\r\n")
    else:
        path = directory / name
        path.write_text("#!/bin/sh\nexit 0\n")
        path.chmod(0o755)
    return path


@pytest.fixture
def config():
    """Config with the proxy enabled and no path pinned."""
    return LanguageServerConfig(
        source_language="en",
        target_language="es",
        enhanced_intelligence_enabled=True,
    )


@pytest.fixture
def isolated_discovery(tmp_path, monkeypatch):
    """Cut discovery off from whatever this machine happens to have installed.

    Without this, a developer box with Homebrew's pyright-langserver silently
    satisfies the fallback search, so tests about *not* finding a server pass or
    fail for reasons that have nothing to do with the code under test.

    Yields an empty directory that is the entirety of PATH, for tests that want
    to place specific binaries on it.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setenv("PATH", str(bindir))
    monkeypatch.setattr("legesher_language_server.enhanced_intelligence.FALLBACK_BIN_DIRS", [])
    return bindir


@pytest.fixture
def stub_config(config, monkeypatch, stub_launcher):
    """Config pinned to the stub server, in its default well-behaved mode."""
    monkeypatch.setenv("STUB_MODE", "normal")
    config.language_server_path = stub_launcher
    return config


class TestHandshake:
    """The proxy must complete an LSP handshake and stay usable afterwards."""

    def test_start_completes_handshake(self, stub_config):
        """start() reports success and the proxy is genuinely initialized."""
        proxy = EnhancedIntelligenceProxy(stub_config)

        try:
            snapshot = _run_off_loop(_start_and_snapshot(proxy), proxy)

            assert snapshot["started"] is True, "start() reported failure against a working server"
            assert snapshot["running"] is True, "subprocess is not alive after start()"
            assert snapshot["initialized"] is True, "initialize handshake did not complete"
        finally:
            _force_kill(proxy)

    def test_event_loop_stays_responsive_during_start(self, stub_config):
        """No single read may stall the loop.

        Asserting merely that *some* other coroutine ran would be satisfied by a
        loop that froze for ten seconds and then recovered. What matters is the
        longest interval the loop went unserviced, because during that interval
        every hover and every diagnostic in the language server is frozen too.
        """
        proxy = EnhancedIntelligenceProxy(stub_config)
        gaps = []

        async def scenario():
            async def heartbeat():
                last = time.perf_counter()
                while True:
                    await asyncio.sleep(0.01)
                    now = time.perf_counter()
                    gaps.append(now - last)
                    last = now

            beat = asyncio.create_task(heartbeat())
            try:
                started = await proxy.start()
                # Guarantee the heartbeat gets a window to record ticks even if
                # start() returns almost immediately, so an empty `gaps` always
                # means "the loop was blocked" and never "the test was too fast".
                await asyncio.sleep(0.1)
                await proxy.stop()
                return started
            finally:
                beat.cancel()

        try:
            started = _run_off_loop(scenario(), proxy)

            assert started is True
            assert gaps, "the event loop never ran another coroutine during start()"
            assert max(gaps) < MAX_LOOP_STALL, (
                f"event loop stalled for {max(gaps):.2f}s during start() — "
                "a synchronous read is running on the loop thread"
            )
        finally:
            _force_kill(proxy)

    def test_requests_still_work_after_initialize(self, stub_config):
        """The reader keeps correlating responses beyond the handshake.

        One successful round-trip proves very little. Every hover the user
        triggers is another request through the same reader, so the loop has to
        survive repeated use.
        """
        proxy = EnhancedIntelligenceProxy(stub_config)

        async def scenario():
            if not await proxy.start():
                return None
            first = await proxy._send_request("textDocument/hover", {"probe": "one"})
            second = await proxy._send_request("textDocument/hover", {"probe": "two"})
            return first, second

        try:
            result = _run_off_loop(scenario(), proxy)

            assert result is not None, "start() failed, so the follow-up requests never ran"
            first, second = result
            assert first is not None and second is not None, "a follow-up request got no response"
            assert first["result"]["contents"] == "one"
            assert second["result"]["contents"] == "two", (
                "responses were correlated to the wrong requests"
            )
        finally:
            _force_kill(proxy)

    def test_non_ascii_payload_survives_the_wire(self, stub_config):
        """A localized payload round-trips byte-for-byte.

        This is the framing bug observed end-to-end rather than in isolation: a
        character-counted Content-Length under-declares the body, so the server
        reads a truncated message and the stream desynchronises from there on.
        """
        proxy = EnhancedIntelligenceProxy(stub_config)
        probe = "definir función(): pasar  # 日本語 ✓ مرحبا"

        async def scenario():
            if not await proxy.start():
                return None
            return await proxy._send_request("textDocument/hover", {"probe": probe})

        try:
            response = _run_off_loop(scenario(), proxy)

            assert response is not None, "no response to a non-ASCII request"
            assert response["result"]["contents"] == probe, "payload was corrupted in transit"
        finally:
            _force_kill(proxy)


class TestHostileServers:
    """Conditions a real server will not reproduce on demand, but does produce."""

    def test_chunked_writes_are_reassembled(self, stub_config, monkeypatch):
        """A response arriving in fragments is still parsed.

        Nothing guarantees a header and its body land in one read. A transport
        that assumes they do works until the day the pipe splits them.
        """
        monkeypatch.setenv("STUB_MODE", "chunked")
        proxy = EnhancedIntelligenceProxy(stub_config)

        try:
            snapshot = _run_off_loop(_start_and_snapshot(proxy), proxy)
            assert snapshot["started"] is True, (
                "handshake failed when the response arrived in fragments"
            )
        finally:
            _force_kill(proxy)

    def test_stderr_flood_does_not_stall_the_handshake(self, stub_config, monkeypatch):
        """A chatty server cannot deadlock us by filling its stderr pipe.

        stderr is opened as a PIPE and never read. Once the OS buffer fills
        (~64 KB) the child blocks trying to write, so it never gets as far as
        answering us — and we wait forever for an answer it cannot send.
        """
        monkeypatch.setenv("STUB_MODE", "stderr_flood")
        proxy = EnhancedIntelligenceProxy(stub_config)

        try:
            snapshot = _run_off_loop(_start_and_snapshot(proxy), proxy)
            assert snapshot["started"] is True, "handshake stalled behind an undrained stderr pipe"
        finally:
            _force_kill(proxy)

    def test_unsolicited_notifications_do_not_break_correlation(self, stub_config, monkeypatch):
        """Server-initiated messages interleaved with responses are handled.

        Real servers push diagnostics and log messages unprompted. A client that
        assumes the next message is its answer will mis-correlate.
        """
        monkeypatch.setenv("STUB_MODE", "noisy")
        proxy = EnhancedIntelligenceProxy(stub_config)

        async def scenario():
            if not await proxy.start():
                return None
            return await proxy._send_request("textDocument/hover", {"probe": "after-noise"})

        try:
            response = _run_off_loop(scenario(), proxy)

            assert response is not None, "notifications swallowed the response"
            assert response["result"]["contents"] == "after-noise"
        finally:
            _force_kill(proxy)

    def test_silent_server_times_out_rather_than_hanging(self, stub_config, monkeypatch):
        """An unresponsive server produces a clean failure, not a wedged loop.

        This is the difference the whole ticket turns on. A correct transport
        lets the request timeout fire and returns False; the broken one cannot
        fire any timer at all, because the timer needs the loop it has blocked.
        """
        monkeypatch.setenv("STUB_MODE", "silent")
        proxy = EnhancedIntelligenceProxy(stub_config)

        try:
            snapshot = _run_off_loop(_start_and_snapshot(proxy), proxy)
            assert snapshot["started"] is False, (
                "a server that never answered was reported as started"
            )
        finally:
            _force_kill(proxy)


class TestMessageCorrelation:
    """An `id` does not by itself mean "this message answers us"."""

    def test_server_request_is_not_mistaken_for_a_response(self, stub_config, monkeypatch):
        """A server→client request sharing our id must not resolve our future.

        Both sides number their requests from independent counters, so overlap
        is ordinary rather than exotic. A client keying purely on `id` resolves
        the wrong message: the caller receives the server's request, and the
        real response is discarded when it finally arrives. `method` is the
        discriminator — requests carry one, responses never do.
        """
        monkeypatch.setenv("STUB_MODE", "collide")
        proxy = EnhancedIntelligenceProxy(stub_config)
        probe = "correlated"

        async def scenario():
            if not await proxy.start():
                return None
            response = await proxy._send_request("textDocument/hover", {"probe": probe})
            await proxy.stop()
            return response

        try:
            response = _run_off_loop(scenario(), proxy)

            assert response is not None, "no response survived the id collision"
            assert "method" not in response, (
                f"resolved with the server's own request rather than our response: {response}"
            )
            assert response["result"]["contents"] == probe
        finally:
            _force_kill(proxy)


class TestTransportDeath:
    """When the transport dies, the proxy must stop claiming to be usable."""

    def test_server_exit_marks_the_transport_unusable(self, stub_config, monkeypatch):
        """A server that quits after the handshake leaves the proxy not-initialized.

        This is the whole ticket's failure mode one layer up: if `initialized`
        stays True after the reader stops, every later request burns its full
        timeout and `legesher/status` reports "active" for a transport that
        cannot carry anything.
        """
        monkeypatch.setenv("STUB_MODE", "die_after_init")
        proxy = EnhancedIntelligenceProxy(stub_config)

        async def scenario():
            started = await proxy.start()
            # Let the reader observe end-of-stream and run its cleanup.
            await asyncio.sleep(0.3)
            state = {"started": started, "initialized": proxy.initialized}
            await proxy.stop()
            return state

        try:
            state = _run_off_loop(scenario(), proxy)

            assert state["started"] is True, "handshake should have completed before the exit"
            assert state["initialized"] is False, (
                "transport reports itself initialized after the server exited — "
                "requests will hang and the status surface will lie"
            )
        finally:
            _force_kill(proxy)

    def test_malformed_content_length_does_not_hang(self, stub_config, monkeypatch):
        """An unparseable length ends the reader instead of reading at a guess.

        Shares its observable outcome with the generic reader-crash path, so it
        pins behaviour rather than isolating the parse guard: what matters is
        that a corrupt stream cannot leave the proxy wedged or lying.
        """
        monkeypatch.setenv("STUB_MODE", "bad_header")
        proxy = EnhancedIntelligenceProxy(stub_config)

        async def scenario():
            started = await proxy.start()
            await asyncio.sleep(0.3)
            state = {"started": started, "initialized": proxy.initialized}
            await proxy.stop()
            return state

        try:
            state = _run_off_loop(scenario(), proxy)

            assert state["started"] is True
            assert state["initialized"] is False, (
                "transport still reports initialized after the stream desynchronised"
            )
        finally:
            _force_kill(proxy)


class TestLifecycle:
    """Starting and stopping must not leak processes."""

    def test_stop_terminates_the_child_and_is_idempotent(self, stub_config):
        """stop() leaves nothing running and tolerates being called twice."""
        proxy = EnhancedIntelligenceProxy(stub_config)

        async def scenario():
            if not await proxy.start():
                return None
            await proxy.stop()
            first = proxy.is_running()
            await proxy.stop()
            return first, proxy.is_running()

        try:
            result = _run_off_loop(scenario(), proxy)

            assert result is not None, "start() failed, so stop() was never exercised"
            after_first, after_second = result
            assert after_first is False, "child still running after stop()"
            assert after_second is False, "second stop() resurrected or errored on the child"
        finally:
            _force_kill(proxy)


class TestDiscovery:
    """Discovery must find a binary that can actually serve LSP."""

    def test_prefers_langserver_over_the_cli_type_checker(self, config, isolated_discovery):
        """`pyright-langserver` wins when both binaries are on PATH.

        `npm install -g pyright` installs both side by side, so "found something
        called pyright" is not evidence of having found a language server.
        """
        _make_executable(isolated_discovery, "pyright")
        _make_executable(isolated_discovery, "pyright-langserver")

        found = EnhancedIntelligenceProxy(config)._find_language_server()

        assert found is not None, "discovery found nothing with both binaries present"
        assert Path(found).stem == "pyright-langserver", (
            f"discovery chose {found!r}; `pyright` is the CLI type checker and "
            "returns EOF when spoken to over stdio"
        )

    def test_configured_path_outranks_path_lookup(self, config, tmp_path, isolated_discovery):
        """An explicit `language_server_path` is honoured even when PATH has a candidate."""
        _make_executable(isolated_discovery, "pyright-langserver")

        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        pinned = _make_executable(elsewhere, "my-langserver")
        config.language_server_path = str(pinned)

        found = EnhancedIntelligenceProxy(config)._find_language_server()

        assert found == str(pinned), f"configured path ignored; discovery chose {found!r}"

    def test_cli_only_installation_is_not_accepted(self, config, isolated_discovery, caplog):
        """Finding only the CLI is the same as finding nothing.

        Returning it would spawn a process that exits immediately, which is the
        original defect: a confident start() followed by a silent, permanent
        degradation. Better to report honestly that no language server is
        available and say which one to install.
        """
        _make_executable(isolated_discovery, "pyright")

        with caplog.at_level(logging.WARNING):
            found = EnhancedIntelligenceProxy(config)._find_language_server()

        assert found is None, (
            f"discovery returned {found!r} — the CLI type checker cannot serve LSP"
        )
        assert "pyright-langserver" in caplog.text, (
            "the user was not told which binary they are missing"
        )

    def test_homebrew_prefix_is_searched(self):
        """`/opt/homebrew/bin` is among the documented fallback locations.

        It is the default prefix on Apple Silicon and was absent from a list
        that named only Intel and npm locations.
        """
        from legesher_language_server.enhanced_intelligence import FALLBACK_BIN_DIRS

        assert "/opt/homebrew/bin" in FALLBACK_BIN_DIRS, (
            f"Homebrew prefix missing from fallback search: {FALLBACK_BIN_DIRS}"
        )


class TestFraming:
    """LSP framing must survive non-ASCII payloads."""

    def test_content_length_counts_bytes_not_characters(self):
        """The declared length matches the encoded body exactly.

        `len(str)` and `len(str.encode())` diverge the moment a payload carries
        anything outside ASCII. Every byte of that difference is a byte the
        server waits for and never receives.
        """
        from legesher_language_server.enhanced_intelligence import frame_message

        framed = frame_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "textDocument/didOpen",
                "params": {"text": "definir función(): pasar  # 日本語 ✓"},
            }
        )

        header, separator, body = framed.partition(b"\r\n\r\n")

        assert separator == b"\r\n\r\n", "framed message is missing its header separator"
        declared = int(header.split(b":")[1].strip())
        assert declared == len(body), (
            f"header declares {declared} bytes but body is {len(body)} bytes — "
            "Content-Length is counting characters"
        )


class TestDegradation:
    """A defaulted-on feature that turns itself off must say so."""

    def test_missing_langserver_warns_with_the_correct_install_command(
        self, config, isolated_discovery, caplog
    ):
        """The failure is visible and names something that actually helps.

        `enhanced_intelligence_enabled` defaults to True, so a silent False is the whole bug
        class: the server quietly degrades and the user never learns the richer
        experience was meant to be there. The old message named `pyright`, which
        is precisely the install that leaves you without a language server.
        """
        # isolated_discovery leaves PATH pointing at an empty directory and
        # empties the fallback search, so nothing installed on this machine can
        # accidentally satisfy discovery and mask the behaviour under test.
        proxy = EnhancedIntelligenceProxy(config)

        with caplog.at_level(logging.WARNING):
            started = asyncio.run(proxy.start())

        assert started is False

        warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert warnings, "a defaulted-on feature failed to start and said nothing"

        message = " ".join(r.getMessage() for r in warnings)
        assert "pyright-langserver" in message, (
            f"warning does not name the binary the user actually needs: {message!r}"
        )


class TestAgainstRealLangserver:
    """Tests against the real thing, in case the stub has drifted from it.

    The stub encodes our beliefs about how a language server behaves. Everything
    else in this file verifies the transport against those beliefs; only these
    verify the beliefs themselves. They are the tests a wrong mental model
    cannot satisfy.
    """

    @pytest.mark.langserver_drift
    @requires_langserver
    def test_handshake_against_real_pyright_langserver(self, config):
        """The transport works against the server we actually ship against."""
        if LANGSERVER is None:
            # Only reachable under LEGESHER_REQUIRE_LANGSERVER=1, i.e. in the
            # weekly drift workflow, where a missing binary means the check did
            # not happen — which is the thing that must not pass silently.
            pytest.fail(
                "LEGESHER_REQUIRE_LANGSERVER=1 but pyright-langserver is not installed, "
                "so the drift check did not run. Install it with: npm install -g pyright"
            )

        config.language_server_path = LANGSERVER
        proxy = EnhancedIntelligenceProxy(config)

        try:
            snapshot = _run_off_loop(_start_and_snapshot(proxy), proxy)

            assert snapshot["started"] is True, "handshake failed against a real pyright-langserver"
            assert snapshot["running"] is True
            assert snapshot["initialized"] is True
        finally:
            _force_kill(proxy)

    @pytest.mark.langserver_drift
    @requires_langserver
    def test_forwarding_against_real_pyright_langserver(self, config, tmp_path, caplog):
        """Hover and diagnostics on a translated document come back mapped (CORE-2227).

        Until CORE-2227 both forwards raised a Position comparison error on any
        document with a translated keyword, logged it at ERROR and returned
        nothing, so the handshake test above passed while forwarding never did.
        """
        if LANGSERVER is None:
            pytest.fail(
                "LEGESHER_REQUIRE_LANGSERVER=1 but pyright-langserver is not installed, "
                "so the drift check did not run. Install it with: npm install -g pyright"
            )

        config.language_server_path = LANGSERVER
        proxy = EnhancedIntelligenceProxy(config)
        uri = (tmp_path / "saludo.py").as_uri()

        try:
            with caplog.at_level(logging.DEBUG):
                result = _run_off_loop(_forward_a_spanish_document(proxy, uri), proxy)
        finally:
            _force_kill(proxy)

        errors = [
            r.getMessage()
            for r in caplog.records
            if r.name.startswith("legesher_language_server") and r.levelno >= logging.ERROR
        ]
        assert errors == []
        assert result["started"] is True, "handshake failed against a real pyright-langserver"

        # `indefinido` is column 20 of the English text Pyright saw, and column
        # 22 of the Spanish the reader sees: `devolver` is two longer than `return`.
        undefined = [d for d, _ in result["diagnostics"] if "indefinido" in d]
        assert undefined, f"Pyright's undefined-name diagnostic is missing: {result['diagnostics']}"
        assert dict(result["diagnostics"])[undefined[0]] == ((1, 22), (1, 32))

        assert result["hover"] is not None, "the hover forward returned nothing"
        contents, hover_range = result["hover"]
        assert "saludo" in contents
        # `saludo` is columns 4-10 in English and 8-14 in Spanish.
        assert hover_range == ((0, 8), (0, 14))


SPANISH_WITH_A_DEFECT = "definir saludo(nombre):\n    devolver nombre + indefinido\n"


async def _forward_a_spanish_document(proxy: EnhancedIntelligenceProxy, uri: str) -> dict:
    """Start the proxy, forward diagnostics then a hover for one document, stop.

    One event loop throughout, for the reason given on ``_start_and_snapshot``.
    The results are reduced to plain values before the loop closes.
    """
    started = await proxy.start()
    diagnostics = await proxy.forward_diagnostic(uri, SPANISH_WITH_A_DEFECT, "es")
    hover = await proxy.forward_hover(
        HoverParams(
            text_document=TextDocumentIdentifier(uri=uri),
            # The last letter of `saludo`, as an editor sends it. Unmapped,
            # column 13 of the English text is inside `nombre`, so a request
            # that skipped the source map would hover the wrong name.
            position=Position(line=0, character=13),
        )
    )
    await proxy.stop()

    def span(r):
        return ((r.start.line, r.start.character), (r.end.line, r.end.character))

    return {
        "started": started,
        "diagnostics": [(d.message, span(d.range)) for d in diagnostics],
        "hover": None
        if hover is None
        else (str(hover.contents), span(hover.range) if hover.range else None),
    }


class TestPlatformDiscoveryPaths:
    """Fallback locations must be right for the platform we are actually on.

    The platform is injected rather than inferred so Windows behaviour is
    covered from any host. Waiting for a Windows runner to find out whether
    Windows discovery works is how the gap in CORE-1886 survived: a code path
    nothing exercises is a code path nobody has checked.
    """

    def test_windows_searches_the_npm_install_location(self):
        """`%APPDATA%\\npm` is where `npm install -g` puts binaries on Windows.

        None of the POSIX prefixes can exist on Windows, so without this the
        fallback chain is dead weight there and discovery rests entirely on
        PATH.
        """
        dirs = default_fallback_bin_dirs(
            platform="win32",
            environ={
                "APPDATA": r"C:\Users\dev\AppData\Roaming",
                "LOCALAPPDATA": r"C:\Users\dev\AppData\Local",
            },
        )

        assert any("npm" in d for d in dirs), f"npm install location not searched: {dirs}"
        assert any(d.startswith(r"C:\Users\dev\AppData\Roaming") for d in dirs), (
            f"APPDATA npm directory missing: {dirs}"
        )

    def test_windows_does_not_search_posix_prefixes(self):
        """Unix paths on Windows are noise: they cost a stat and can never hit."""
        dirs = default_fallback_bin_dirs(platform="win32", environ={"APPDATA": r"C:\a"})

        assert not any(d.startswith("/") for d in dirs), f"POSIX paths offered on Windows: {dirs}"

    def test_windows_tolerates_a_missing_appdata(self):
        """A stripped environment yields no candidates rather than a crash."""
        assert default_fallback_bin_dirs(platform="win32", environ={}) == []

    def test_posix_searches_the_homebrew_and_npm_prefixes(self):
        """The Apple Silicon prefix and the npm global bin are both covered."""
        dirs = default_fallback_bin_dirs(platform="darwin", environ={})

        assert "/opt/homebrew/bin" in dirs
        assert any(d.endswith(".npm-global/bin") for d in dirs), dirs

    def test_posix_does_not_offer_windows_paths(self):
        """Guards the tests above: the two branches must actually differ."""
        dirs = default_fallback_bin_dirs(platform="linux", environ={"APPDATA": r"C:\a"})

        assert not any("AppData" in d for d in dirs), f"Windows paths offered on POSIX: {dirs}"
