"""Forwarded diagnostics must serialize — severity is an enum, not an int (CORE-1977).

The backend's LSP JSON carries ``severity`` as a plain integer. Constructing
``lsprotocol.types.Diagnostic`` with that raw int used to survive until
serialization time, where cattrs calls ``.value`` on the field, the whole
``textDocument/diagnostic`` response fails to send, and pygls surfaces the
failure as a ``window/showMessage`` of type Error — a red toast in VS Code.

The conversion boundary is ``wire_severity``; the end-to-end tests drive
``forward_diagnostic`` from a raw backend payload and push the result through
the same converter pygls uses on the wire, so a regression fails here rather
than on screen. The general convention (per CORE-1977): anywhere a wire
payload becomes an ``lsprotocol`` object, the enum conversion is a boundary
that needs asserting.
"""

import pytest
from lsprotocol.types import Diagnostic, DiagnosticSeverity
from pygls.protocol import default_converter

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import (
    EnhancedIntelligenceProxy,
    wire_severity,
)


class TestWireSeverity:
    """The int-to-enum boundary in isolation."""

    @pytest.mark.parametrize(
        ("wire_value", "expected"),
        [
            (1, DiagnosticSeverity.Error),
            (2, DiagnosticSeverity.Warning),
            (3, DiagnosticSeverity.Information),
            (4, DiagnosticSeverity.Hint),
        ],
    )
    def test_valid_wire_values_map_to_the_enum(self, wire_value, expected):
        assert wire_severity(wire_value) is expected

    def test_absent_severity_defaults_to_error(self):
        # Matches the previous hardcoded default of 1.
        assert wire_severity(None) is DiagnosticSeverity.Error

    @pytest.mark.parametrize("wire_value", [0, 5, -1, 99])
    def test_out_of_range_values_fall_back_to_error(self, wire_value, caplog):
        assert wire_severity(wire_value) is DiagnosticSeverity.Error
        assert "Unknown diagnostic severity" in caplog.text

    def test_non_numeric_junk_falls_back_to_error(self):
        assert wire_severity("2") is DiagnosticSeverity.Error


class _IdentitySourceMap:
    """Positions map to themselves; range math is not under test here."""

    def to_original(self, position):
        return position


class _StubTranslation:
    def __init__(self, content: str):
        self.translated_code = content
        self.source_map = _IdentitySourceMap()
        self.content_hash = "stub-hash"


class _StubTranslator:
    async def translate_to_english(self, content: str):
        return _StubTranslation(content)


def _backend_item(severity=..., line=0):
    """One diagnostic item as the backend's LSP JSON would carry it."""
    item = {
        "range": {
            "start": {"line": line, "character": 0},
            "end": {"line": line, "character": 5},
        },
        "message": "name is not defined",
    }
    if severity is not ...:
        item["severity"] = severity
    return item


@pytest.fixture
def proxy(monkeypatch):
    """A proxy whose transport is stubbed down to the payload under test."""
    config = LanguageServerConfig(
        source_language="en",
        target_language="es",
        enhanced_intelligence_enabled=False,  # never spawn a real backend
    )
    proxy = EnhancedIntelligenceProxy(config)
    proxy._initialized = True
    proxy._transport_alive = True
    monkeypatch.setattr(proxy, "is_running", lambda: True)
    proxy.translator = _StubTranslator()

    async def send_notification(method, params):
        return None

    monkeypatch.setattr(proxy, "_send_notification", send_notification)
    return proxy


def _respond_with(proxy, monkeypatch, items):
    async def send_request(method, params):
        assert method == "textDocument/diagnostic"
        return {"result": {"items": items}}

    monkeypatch.setattr(proxy, "_send_request", send_request)


class TestForwardedDiagnosticsSerialize:
    """End to end: raw backend payload in, wire-serializable response out."""

    @pytest.mark.asyncio
    async def test_integer_severity_payload_serializes(self, proxy, monkeypatch):
        # The exact shape that crashed on screen: backend int severity,
        # pushed through the converter pygls uses when sending the response.
        _respond_with(
            proxy,
            monkeypatch,
            [_backend_item(severity=s, line=i) for i, s in enumerate([1, 2, 3, 4])],
        )

        diagnostics = await proxy.forward_diagnostic("file:///demo.py", "x = y\n")

        assert [d.severity for d in diagnostics] == [
            DiagnosticSeverity.Error,
            DiagnosticSeverity.Warning,
            DiagnosticSeverity.Information,
            DiagnosticSeverity.Hint,
        ]
        converter = default_converter()
        for diagnostic in diagnostics:
            unstructured = converter.unstructure(diagnostic)
            assert isinstance(unstructured["severity"], int)

    @pytest.mark.asyncio
    async def test_absent_and_out_of_range_severity_still_serialize(self, proxy, monkeypatch):
        _respond_with(
            proxy,
            monkeypatch,
            [_backend_item(), _backend_item(severity=7, line=1)],
        )

        diagnostics = await proxy.forward_diagnostic("file:///demo.py", "x = y\n")

        assert len(diagnostics) == 2
        assert all(d.severity is DiagnosticSeverity.Error for d in diagnostics)
        converter = default_converter()
        for diagnostic in diagnostics:
            converter.unstructure(diagnostic)  # must not raise

    @pytest.mark.asyncio
    async def test_forwarded_diagnostics_are_not_silently_dropped(self, proxy, monkeypatch):
        # Guard against the failure mode hiding behind the broad except in
        # forward_diagnostic: an empty list is what a crash also produces.
        _respond_with(proxy, monkeypatch, [_backend_item(severity=1)])

        diagnostics = await proxy.forward_diagnostic("file:///demo.py", "x = y\n")

        assert len(diagnostics) == 1
        assert isinstance(diagnostics[0], Diagnostic)
        assert diagnostics[0].message == "name is not defined"
        assert diagnostics[0].source == "pyright"
