"""Tests for surfacing enhanced-intelligence state (CORE-1886, scope items 4-5).

The transport fix makes the Pyright proxy *able* to run. These tests cover the
other half of the ticket: making it observable whether it actually is.

`enhanced_intelligence_enabled` defaults to True, so when the proxy cannot start the server
silently drops to Legesher-only features. Nothing tells the user, and every call
site simply guards on `is_running()`. A thinner experience arrives with no
indication that a richer one was meant to be there — the same failure class as
reporting a success you have not earned.

Two surfaces are needed, and they serve different readers:

* a one-time `window/showMessage` warning, which is what a *person* sees
* a `legesher/status` request, which is what a *client* polls to render a status
  indicator, and what answers "is enhanced intelligence actually on?"

`logger.warning` is neither. It lands in a server log the user never opens.

These tests avoid mocking the proxy. Failure is produced by cutting discovery
off from the machine, and success by pointing at the stub language server, so
what is asserted is real behaviour rather than a rehearsal of it.
"""

import asyncio

import pytest
from lsprotocol.types import InitializedParams, MessageType

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.server import LegesherLanguageServer


@pytest.fixture
def isolated_discovery(tmp_path, monkeypatch):
    """Cut discovery off from whatever this machine happens to have installed.

    Without this, a developer box with Homebrew's pyright-langserver satisfies
    the fallback search and the "no server available" tests pass or fail for
    reasons unrelated to the code under test.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setenv("PATH", str(bindir))
    monkeypatch.setattr("legesher_language_server.enhanced_intelligence.FALLBACK_BIN_DIRS", [])
    return bindir


@pytest.fixture
def config():
    return LanguageServerConfig(
        source_language="en",
        target_language="es",
        python_version="3.10",
        enhanced_intelligence_enabled=True,
    )


@pytest.fixture
def shown_messages(monkeypatch):
    """Capture outbound window/showMessage notifications.

    This is the protocol boundary, not an internal collaborator: capturing what
    the server actually puts on the wire is the only way to assert the user is
    told anything, short of driving a real client.
    """
    captured = []

    def record(self, params):
        captured.append(params)

    monkeypatch.setattr(LegesherLanguageServer, "window_show_message", record)
    return captured


@pytest.fixture
def server(config):
    return LegesherLanguageServer(config)


class TestStatusReporting:
    """`legesher/status` must answer the question honestly."""

    def test_reports_unavailable_before_anything_starts(self, server):
        """A server that has not started the proxy does not claim it is running."""
        status = server.enhanced_intelligence_status()

        assert status.enabled is True
        assert status.running is False
        assert status.server_path is None

    def test_reports_disabled_when_turned_off_in_config(self, config):
        """Disabled by choice is distinct from broken, and must read that way."""
        config.enhanced_intelligence_enabled = False
        status = LegesherLanguageServer(config).enhanced_intelligence_status()

        assert status.enabled is False
        assert status.running is False
        assert "disabled" in status.detail.lower(), (
            f"a deliberately disabled feature reads as a failure: {status.detail!r}"
        )

    async def test_reports_unavailable_with_install_guidance_after_a_failed_start(
        self, server, isolated_discovery
    ):
        """When no server is installed, the status says so and says what to do."""
        await server.on_initialized(InitializedParams())

        status = server.enhanced_intelligence_status()

        assert status.enabled is True
        assert status.running is False
        assert "pyright-langserver" in status.detail, (
            f"status does not name the binary the user needs: {status.detail!r}"
        )

    async def test_reports_running_after_a_successful_start(
        self, server, config, monkeypatch, stub_launcher
    ):
        """A working proxy is reported as running, with the path in use.

        Driven inside a single event loop: the subprocess transport is bound to
        the loop that created it, so tearing it down from a second loop is not a
        thing production ever does, and not a thing the test should do either.
        """
        monkeypatch.setenv("STUB_MODE", "normal")
        config.language_server_path = stub_launcher

        try:
            await server.on_initialized(InitializedParams())

            status = server.enhanced_intelligence_status()

            assert status.running is True, f"proxy started but status says otherwise: {status}"
            assert status.server_path == stub_launcher
        finally:
            await server.on_shutdown(None)

    def test_status_serialises_for_the_wire(self, server):
        """The client receives a plain, camelCased payload it can render."""
        payload = server.enhanced_intelligence_status().to_dict()

        assert isinstance(payload, dict)
        assert payload["enabled"] is True
        assert payload["running"] is False
        assert "detail" in payload
        assert "serverPath" in payload, f"expected camelCase keys for LSP: {sorted(payload)}"


class TestStatusRequestRegistration:
    """The status surface is only real if a client can actually reach it."""

    async def test_status_request_is_registered_under_its_wire_name(self, server):
        """`legesher/status` is dispatchable and returns the payload.

        The literal string is asserted rather than the module constant: the
        method name is the contract with the client, and a test that imports the
        same constant the code uses would pass happily if that constant were
        wrong.
        """
        handler = server.protocol._get_handler("legesher/status")

        payload = await handler(None)

        assert payload["enabled"] is True
        assert payload["running"] is False
        assert "serverPath" in payload

    def test_unregistered_methods_still_raise(self, server):
        """Guards the test above: dispatch must actually discriminate.

        If `_get_handler` returned something for any name, the registration test
        would prove nothing at all.
        """
        from pygls.exceptions import JsonRpcMethodNotFound

        with pytest.raises(JsonRpcMethodNotFound):
            server.protocol._get_handler("legesher/definitelyNotRegistered")


class TestUserVisibleWarning:
    """A degraded server must tell the person using it, not just the log."""

    async def test_failed_start_shows_a_warning_to_the_user(
        self, server, isolated_discovery, shown_messages
    ):
        """The failure reaches the client as a window/showMessage warning."""
        await server.on_initialized(InitializedParams())

        assert shown_messages, (
            "enhanced intelligence failed to start and the user was never told — "
            "a log line is not a user-visible surface"
        )

        message = shown_messages[0]
        assert message.type == MessageType.Warning
        assert "pyright-langserver" in message.message, (
            f"the warning does not say what to install: {message.message!r}"
        )

    async def test_successful_start_says_nothing(
        self, server, config, monkeypatch, shown_messages, stub_launcher
    ):
        """Working software is quiet. A popup on every launch trains people to dismiss them."""
        monkeypatch.setenv("STUB_MODE", "normal")
        config.language_server_path = stub_launcher

        try:
            await server.on_initialized(InitializedParams())

            assert not shown_messages, f"nagged the user about a success: {shown_messages}"
        finally:
            await server.on_shutdown(None)

    async def test_the_user_is_warned_only_once(self, server, isolated_discovery, shown_messages):
        """Re-initialising does not re-nag.

        Clients reconnect, and `initialized` can arrive more than once per
        session. One notice is information; a repeated one is noise.
        """
        await server.on_initialized(InitializedParams())
        await server.on_initialized(InitializedParams())

        assert len(shown_messages) == 1, (
            f"warned {len(shown_messages)} times across two initialisations"
        )

    async def test_disabled_by_config_is_not_warned_about(self, config, shown_messages):
        """Turning the feature off is not a malfunction and must not warn."""
        config.enhanced_intelligence_enabled = False
        server = LegesherLanguageServer(config)

        await server.on_initialized(InitializedParams())

        assert not shown_messages, (
            f"warned about a feature the user deliberately disabled: {shown_messages}"
        )


class TestProxyLifecycle:
    """Re-initialisation must not leak language server processes."""

    async def test_concurrent_initialize_spawns_only_one_server(
        self, server, config, monkeypatch, stub_launcher
    ):
        """Two `initialized` notifications in flight at once start one server.

        The sequential test below is satisfied by a plain `is_running()` check.
        This one is not: the check and the spawn are separated by an await, and
        `process` stays None until the spawn returns, so both callers can pass
        the check and the first child is orphaned for the editor's lifetime.

        Counts real spawns rather than inspecting the proxy, because the whole
        symptom is a child nobody holds a handle to any more.
        """
        monkeypatch.setenv("STUB_MODE", "normal")
        config.language_server_path = stub_launcher

        spawns = []
        real_exec = asyncio.create_subprocess_exec

        async def counting_exec(*args, **kwargs):
            spawns.append(args)
            return await real_exec(*args, **kwargs)

        monkeypatch.setattr(asyncio, "create_subprocess_exec", counting_exec)

        try:
            await asyncio.gather(
                server.on_initialized(InitializedParams()),
                server.on_initialized(InitializedParams()),
            )

            assert len(spawns) == 1, (
                f"{len(spawns)} language servers spawned concurrently; "
                f"{len(spawns) - 1} orphaned with no handle to stop them"
            )
        finally:
            await server.on_shutdown(None)

    async def test_repeated_initialize_does_not_spawn_a_second_server(
        self, server, config, monkeypatch, stub_launcher
    ):
        """A second `initialized` reuses the running proxy.

        Without a guard, the second call starts another child and drops the
        handle to the first, orphaning it for the lifetime of the editor.
        """
        monkeypatch.setenv("STUB_MODE", "normal")
        config.language_server_path = stub_launcher

        try:
            await server.on_initialized(InitializedParams())
            first_pid = server.intelligence_proxy.process.pid

            await server.on_initialized(InitializedParams())
            second_pid = server.intelligence_proxy.process.pid

            assert first_pid == second_pid, (
                f"second initialize spawned pid {second_pid}, orphaning pid {first_pid}"
            )
        finally:
            await server.on_shutdown(None)
