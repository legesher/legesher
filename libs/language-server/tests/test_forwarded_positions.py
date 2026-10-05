"""Forwarded hover and diagnostics map positions through the real source map (CORE-2227).

``SourceMap`` finds the mapping that contains a position with ``<=`` and ``<``.
Its own ``Position`` is a NamedTuple, so it orders. ``lsprotocol.types.Position``
is an attrs class with no ordering, so handing one to ``to_english`` or
``to_original`` raises ``TypeError`` as soon as the map holds a mapping. The
proxy used to build lsprotocol positions for those calls, so every hover and
diagnostic forward on a document with a translated keyword logged
"'<=' not supported between instances of 'Position' and 'Position'" at ERROR
and returned nothing.

The existing forwarded-diagnostic tests replace the source map with an
identity stub, which cannot see the type of what it is given, and no other test
reaches a real map through a forward. These keep the real translator, so the
map is the one production builds, and the hover request carries the real
``lsprotocol`` position that pygls hands the server. Only the backend's replies
are stubbed.
"""

import logging

import pytest
from lsprotocol.types import HoverParams, Position, TextDocumentIdentifier
from pygls.protocol import default_converter

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy

URI = "file:///demo_es.py"

# Two keywords change length: `definir` (7) -> `def` (3) on line 0 and
# `devolver` (8) -> `return` (6) on line 1. Every column after them shifts.
SPANISH = "definir saludo(nombre):\n    devolver nombre\n"
ENGLISH = "def saludo(nombre):\n    return nombre\n"


def _range(start_line, start_char, end_line, end_char):
    return {
        "start": {"line": start_line, "character": start_char},
        "end": {"line": end_line, "character": end_char},
    }


def _span(lsp_range):
    """A Range as plain numbers, for readable assertion failures."""
    return (
        (lsp_range.start.line, lsp_range.start.character),
        (lsp_range.end.line, lsp_range.end.character),
    )


@pytest.fixture
def proxy(monkeypatch):
    """A proxy with the real translator and a backend stubbed to canned replies."""
    config = LanguageServerConfig(
        source_language="en",
        target_language="es",
        enhanced_intelligence_enabled=False,  # never spawn a real backend
    )
    proxy = EnhancedIntelligenceProxy(config)
    proxy._initialized = True
    proxy._transport_alive = True
    monkeypatch.setattr(proxy, "is_running", lambda: True)

    async def send_notification(method, params):
        return None

    monkeypatch.setattr(proxy, "_send_notification", send_notification)
    return proxy


def _backend(proxy, monkeypatch, replies):
    """Answer each backend request from ``replies`` and record what was asked."""
    sent = []

    async def send_request(method, params):
        sent.append((method, params))
        return replies[method]

    monkeypatch.setattr(proxy, "_send_request", send_request)
    return sent


async def _cache_translation(proxy):
    """Translate the document the way didOpen does, and check the map is not empty.

    With no mappings the range checks never run, so a test of them would pass
    without exercising them.
    """
    translated = await proxy.translate_document_for_server(URI, SPANISH, "es")
    assert translated == ENGLISH, f"the es pack no longer translates the fixture: {translated!r}"
    assert len(proxy._document_cache[URI]["source_map"].mappings) == 2


def _forward_errors(caplog):
    return [
        r.getMessage()
        for r in caplog.records
        if r.name.startswith("legesher_language_server") and r.levelno >= logging.ERROR
    ]


class TestForwardedHover:
    """A hover request in Spanish coordinates reaches the backend in English ones."""

    @pytest.mark.asyncio
    async def test_hover_maps_the_request_and_the_reply_through_the_source_map(
        self, proxy, monkeypatch, caplog
    ):
        await _cache_translation(proxy)
        sent = _backend(
            proxy,
            monkeypatch,
            {
                "textDocument/hover": {
                    "result": {
                        "contents": {"kind": "markdown", "value": "(function) def saludo"},
                        # `saludo` in the English text the backend saw.
                        "range": _range(0, 4, 0, 10),
                    }
                }
            },
        )

        # The cursor on the `a` of `saludo`, as the editor sends it.
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri=URI),
            position=Position(line=0, character=9),
        )
        with caplog.at_level(logging.DEBUG):
            hover = await proxy.forward_hover(params)

        assert _forward_errors(caplog) == []
        assert hover is not None, "the forward returned nothing, which is also what a crash returns"
        assert sent == [
            (
                "textDocument/hover",
                {"textDocument": {"uri": URI}, "position": {"line": 0, "character": 5}},
            )
        ]
        assert _span(hover.range) == ((0, 8), (0, 14)), "the reply must land on `saludo`"
        default_converter().unstructure(hover)  # what pygls does before sending; must not raise

    @pytest.mark.asyncio
    async def test_hover_inside_a_translated_keyword(self, proxy, monkeypatch, caplog):
        # A position inside a mapping takes the containment branch, not the
        # cumulative-offset one: `definir` columns 0-6 scale onto `def` 0-2.
        await _cache_translation(proxy)
        sent = _backend(
            proxy,
            monkeypatch,
            {"textDocument/hover": {"result": {"contents": "def", "range": _range(0, 0, 0, 3)}}},
        )

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri=URI),
            position=Position(line=0, character=6),
        )
        with caplog.at_level(logging.DEBUG):
            hover = await proxy.forward_hover(params)

        assert _forward_errors(caplog) == []
        assert hover is not None
        assert sent[0][1]["position"] == {"line": 0, "character": 2}
        assert _span(hover.range) == ((0, 0), (0, 7)), "the reply must cover all of `definir`"


class TestForwardedDiagnostics:
    """Backend diagnostics in English coordinates come back in Spanish ones."""

    @pytest.mark.asyncio
    async def test_diagnostic_ranges_map_back_through_the_source_map(
        self, proxy, monkeypatch, caplog
    ):
        _backend(
            proxy,
            monkeypatch,
            {
                "textDocument/diagnostic": {
                    "result": {
                        "items": [
                            # `nombre` after `return `: past a mapping on its line.
                            {"range": _range(1, 11, 1, 17), "message": "after", "severity": 2},
                            # `return` itself: starts inside a mapping, ends on its edge.
                            {"range": _range(1, 4, 1, 10), "message": "keyword", "severity": 1},
                        ]
                    }
                }
            },
        )

        with caplog.at_level(logging.DEBUG):
            diagnostics = await proxy.forward_diagnostic(URI, SPANISH, "es")

        assert _forward_errors(caplog) == []
        assert len(proxy._document_cache[URI]["source_map"].mappings) == 2
        assert [(d.message, _span(d.range)) for d in diagnostics] == [
            ("after", ((1, 13), (1, 19))),
            ("keyword", ((1, 4), (1, 12))),
        ]
        converter = default_converter()
        for diagnostic in diagnostics:
            converter.unstructure(diagnostic)  # must not raise


# A docstring above, and keywords after other code on the last line (CORE-2343).
# The map used to record these mappings three lines too high and too far left,
# so a range below the docstring, or after `si` on its line, came back on the
# wrong characters.
DOCUMENTED_URI = "file:///documentado_es.py"
DOCUMENTED_SPANISH = (
    "definir saludo(nombre):\n"
    '    """Saluda.\n'
    "\n"
    "    Devuelve el nombre.\n"
    '    """\n'
    "    devolver nombre si nombre sino indefinido\n"
)
DOCUMENTED_ENGLISH = (
    "def saludo(nombre):\n"
    '    """Saluda.\n'
    "\n"
    "    Devuelve el nombre.\n"
    '    """\n'
    "    return nombre if nombre else indefinido\n"
)
LAST_LINE = 5


def _word_range(text, line, word):
    """The wire range of the only ``word`` on ``line`` of ``text``."""
    row = text.split("\n")[line]
    assert row.count(word) == 1, f"{word!r} is not unique on line {line}: {row!r}"
    start = row.index(word)
    return _range(line, start, line, start + len(word))


def _covered(text, lsp_range):
    """The characters of ``text`` a one-line Range covers."""
    assert lsp_range.start.line == lsp_range.end.line
    row = text.split("\n")[lsp_range.start.line]
    return row[lsp_range.start.character : lsp_range.end.character]


class TestBelowADocstringAfterAMidLineKeyword:
    """Positions below a multi-line string, after a keyword on their line, map exactly."""

    @pytest.mark.asyncio
    async def test_diagnostic_after_a_mid_line_keyword_lands_on_its_name(
        self, proxy, monkeypatch, caplog
    ):
        _backend(
            proxy,
            monkeypatch,
            {
                "textDocument/diagnostic": {
                    "result": {
                        "items": [
                            {
                                # Where the backend reports the name, in the
                                # English text it was sent.
                                "range": _word_range(DOCUMENTED_ENGLISH, LAST_LINE, "indefinido"),
                                "message": '"indefinido" is not defined',
                                "severity": 1,
                            }
                        ]
                    }
                }
            },
        )

        with caplog.at_level(logging.DEBUG):
            diagnostics = await proxy.forward_diagnostic(DOCUMENTED_URI, DOCUMENTED_SPANISH, "es")

        assert _forward_errors(caplog) == []
        assert proxy._document_cache[DOCUMENTED_URI]["translated"] == DOCUMENTED_ENGLISH
        assert len(diagnostics) == 1
        assert diagnostics[0].range.start.line == LAST_LINE
        assert _covered(DOCUMENTED_SPANISH, diagnostics[0].range) == "indefinido"

    @pytest.mark.asyncio
    async def test_hover_after_a_mid_line_keyword_asks_about_its_name(
        self, proxy, monkeypatch, caplog
    ):
        await proxy.translate_document_for_server(DOCUMENTED_URI, DOCUMENTED_SPANISH, "es")
        sent = _backend(
            proxy,
            monkeypatch,
            {
                "textDocument/hover": {
                    "result": {
                        "contents": {"kind": "markdown", "value": "(variable) indefinido"},
                        "range": _word_range(DOCUMENTED_ENGLISH, LAST_LINE, "indefinido"),
                    }
                }
            },
        )

        # The cursor on the last letter of `indefinido`, as the editor sends it.
        spanish = _word_range(DOCUMENTED_SPANISH, LAST_LINE, "indefinido")
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri=DOCUMENTED_URI),
            position=Position(line=LAST_LINE, character=spanish["end"]["character"] - 1),
        )
        with caplog.at_level(logging.DEBUG):
            hover = await proxy.forward_hover(params)

        assert _forward_errors(caplog) == []
        asked = sent[0][1]["position"]
        english = _word_range(DOCUMENTED_ENGLISH, LAST_LINE, "indefinido")
        assert asked == {"line": LAST_LINE, "character": english["end"]["character"] - 1}
        assert hover is not None
        assert _covered(DOCUMENTED_SPANISH, hover.range) == "indefinido"
