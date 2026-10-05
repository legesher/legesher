"""The backend is sent the program that runs, builtins included (CORE-2342).

The proxy used to translate keywords only, on the reasoning that the backend
just has to parse the text. Pyright type-checks it, so every localized builtin
(`imprimir`), exception (`errordevalor`) and localized type in an annotation
(`entero`) came back as "is not defined", and a localized `self` (`mismo`) as
"Instance methods should take a "self" parameter". ``legesher run`` renames
all of these before Python sees the code, so the proxy now does too, by the
same rule. It still differs from the run where a word is typed in another
Unicode form (CORE-2352) and for ``NotImplemented`` and ``Ellipsis``
(CORE-2219).

These keep the real translator and the real es pack; only the backend is
stubbed. A real ``pyright-langserver`` checks the same document in
``test_enhanced_intelligence_transport.py``.
"""

import logging

import pytest

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy

URI = "file:///media_es.py"

# The six lines from the ticket, with the pack's `sumar` for `sum`. The ticket
# wrote `suma`, which is no builtin in the es pack: `legesher run` raises
# NameError on it, so Pyright's "is not defined" for it is true.
SIX_LINES = (
    "definir media(numeros):\n"
    "    total = sumar(numeros)\n"
    "    devolver total / longitud(numeros)\n"
    "\n"
    "por i en rango(3):\n"
    "    imprimir(media([1, 2, i]))\n"
)
SIX_LINES_ENGLISH = (
    "def media(numeros):\n"
    "    total = sum(numeros)\n"
    "    return total / len(numeros)\n"
    "\n"
    "for i in range(3):\n"
    "    print(media([1, 2, i]))\n"
)

# An exception, implicit parameters, a localized type and a decorator, with a
# genuinely undefined name after two builtins on the last line.
READER = (
    "clase Lector:\n"
    "    definir leer(mismo, texto: cadena) -> entero:\n"
    "        probar:\n"
    "            devolver entero(texto)\n"
    "        excepto errordevalor:\n"
    "            imprimir(longitud(texto) + indefinido)\n"
    "            devolver 0\n"
    "\n"
    "    @métododeclase\n"
    "    definir crear(misma_clase):\n"
    "        devolver misma_clase()\n"
)
READER_ENGLISH = (
    "class Lector:\n"
    "    def leer(self, texto: str) -> int:\n"
    "        try:\n"
    "            return int(texto)\n"
    "        except ValueError:\n"
    "            print(len(texto) + indefinido)\n"
    "            return 0\n"
    "\n"
    "    @classmethod\n"
    "    def crear(cls):\n"
    "        return cls()\n"
)
UNDEFINED_LINE = 5


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
    return proxy


def _stub_backend(proxy, monkeypatch, diagnostic_items):
    """Answer the diagnostic request with ``diagnostic_items``; record each didOpen text."""
    opened = []

    async def send_notification(method, params):
        if method == "textDocument/didOpen":
            opened.append(params["textDocument"]["text"])

    async def send_request(method, params):
        assert method == "textDocument/diagnostic"
        return {"result": {"items": diagnostic_items}}

    monkeypatch.setattr(proxy, "_send_notification", send_notification)
    monkeypatch.setattr(proxy, "_send_request", send_request)
    return opened


def _word_range(text, line, word):
    """The wire range of the only ``word`` on ``line`` of ``text``."""
    row = text.split("\n")[line]
    assert row.count(word) == 1, f"{word!r} is not unique on line {line}: {row!r}"
    start = row.index(word)
    return {
        "start": {"line": line, "character": start},
        "end": {"line": line, "character": start + len(word)},
    }


def _covered(text, lsp_range):
    """The characters of ``text`` a one-line Range covers."""
    assert lsp_range.start.line == lsp_range.end.line
    row = text.split("\n")[lsp_range.start.line]
    return row[lsp_range.start.character : lsp_range.end.character]


class TestBuiltinMap:
    """What `_get_builtin_map` hands the translator, beside the keywords."""

    def test_spanish_builtins_exceptions_and_implicit_parameters(self, proxy):
        names = proxy._get_builtin_map("es")

        assert names["imprimir"] == "print"
        assert names["longitud"] == "len"
        assert names["entero"] == "int"
        assert names["métododeclase"] == "classmethod"
        # Pack keys are lowercase; Python's spelling is not.
        assert names["errordevalor"] == "ValueError"
        assert names["noimplementado"] == "NotImplemented"
        assert names["elipsis"] == "Ellipsis"
        # Implicit parameters (CORE-710).
        assert names["mismo"] == "self"
        assert names["misma_clase"] == "cls"

    def test_a_word_that_differs_from_english_only_in_case_is_renamed(self, proxy):
        # The de pack writes `float` as `Float`, which is not Python's name.
        # Only a word spelled exactly as in English is left out.
        assert proxy._get_builtin_map("de")["Float"] == "float"

    def test_every_language_s_translator_gets_its_own_builtins(self, proxy):
        # One translator per document language (CORE-1976), not only the
        # configured one.
        assert proxy.translator.builtin_map["imprimir"] == "print"
        assert proxy.translator_for("fr").builtin_map["imprimer"] == "print"

    def test_a_pack_spelled_in_english_adds_nothing(self, proxy):
        # The en pack maps `valueerror` to `valueerror`. Renaming a user's
        # `valueerror` to `ValueError` would change their program.
        assert proxy._get_builtin_map("en") == {}

    def test_a_missing_pack_falls_back_to_no_builtins(self, proxy, caplog):
        with caplog.at_level(logging.WARNING):
            assert proxy._get_builtin_map("nonexistent") == {}
        assert "Failed to load language pack for 'nonexistent'" in caplog.text


class TestTheBackendSeesTheProgramThatRuns:
    """The English text sent in didOpen has no localized names left in it."""

    @pytest.mark.asyncio
    async def test_the_six_line_program(self, proxy, monkeypatch):
        opened = _stub_backend(proxy, monkeypatch, [])

        assert await proxy.forward_diagnostic(URI, SIX_LINES, "es") == []
        assert opened == [SIX_LINES_ENGLISH]

    @pytest.mark.asyncio
    async def test_exceptions_implicit_parameters_and_localized_types(self, proxy, monkeypatch):
        opened = _stub_backend(proxy, monkeypatch, [])

        await proxy.forward_diagnostic(URI, READER, "es")

        assert opened == [READER_ENGLISH]

    @pytest.mark.asyncio
    async def test_a_variable_spelled_like_a_builtin_is_renamed_as_the_engine_renames_it(
        self, proxy, monkeypatch
    ):
        # `legesher run` renames every name spelled like a localized builtin,
        # whatever it names (CORE-1107). Pyright has to check that program: a
        # user's `sumar = 0` really does shadow `sum` when it runs.
        opened = _stub_backend(proxy, monkeypatch, [])

        await proxy.forward_diagnostic(URI, "entrada = 3\nimprimir(entrada)\n", "es")

        assert opened == ["input = 3\nprint(input)\n"]

    @pytest.mark.asyncio
    async def test_an_attribute_spelled_like_a_builtin_is_renamed_too(self, proxy, monkeypatch):
        # The engine writes `str.format` as `.formatear`, because it renames
        # every name, attributes included. Left in place, Pyright reports
        # `Cannot access attribute "formatear"`.
        opened = _stub_backend(proxy, monkeypatch, [])

        await proxy.forward_diagnostic(URI, 'imprimir("{}".formatear(1))\n', "es")

        assert opened == ['print("{}".format(1))\n']


class TestAGenuineUndefinedName:
    """A real error after translated builtins comes back on its own characters."""

    @pytest.mark.asyncio
    async def test_lands_on_the_name_in_the_localized_source(self, proxy, monkeypatch, caplog):
        _stub_backend(
            proxy,
            monkeypatch,
            [
                {
                    # Where the backend reports it, in the English text it was sent.
                    "range": _word_range(READER_ENGLISH, UNDEFINED_LINE, "indefinido"),
                    "message": '"indefinido" is not defined',
                    "severity": 1,
                }
            ],
        )

        with caplog.at_level(logging.DEBUG):
            diagnostics = await proxy.forward_diagnostic(URI, READER, "es")

        assert [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR] == []
        assert len(diagnostics) == 1
        assert diagnostics[0].range.start.line == UNDEFINED_LINE
        # `imprimir` and `longitud` are 3 and 5 longer than `print` and `len`.
        assert _covered(READER, diagnostics[0].range) == "indefinido"
