"""The proxy sends the backend the English that ``legesher run`` executes (CORE-2342).

The language server does not depend on legesher-core, so the proxy keeps its
own copy of the engine's renaming rule. These pin the two together with
shared inputs: the same localized source, translated by both, must give the
same English. If the engine's rule changes, they fail until the proxy
follows. Known differences are strict xfails naming the ticket that removes
them.

CORE-2237 keeps a name after a dot, a keyword-argument name and a module path
as written. Both sides read that rule from ``name_positions.py``, which ships
byte-identical in each package (``scripts/tests/test_name_positions_copies.py``);
the cases here check that each side applies it the same way. CORE-2613 (soft
keywords used as names) and CORE-2614 (shadowed builtins) will change the
rule again.

They need legesher-core, which the monorepo workspace installs; an install
of this package on its own skips them.
"""

import sys
import unicodedata

import pytest

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy

transformer = pytest.importorskip("legesher_core.transformer")

# Both sides read the 3.10 pack tier, the one the language server loads
# (CORE-2345 moves the server to the running interpreter's tier).
PACK_TIER = "3.10"

# Hand-written Spanish, with names spelled like a builtin or a soft keyword
# in each position the engine renames them today, CORE-2237's included.
SPANISH = {
    "keywords, builtins, exceptions and implicit parameters": (
        "clase Lector:\n"
        "    definir leer(mismo, texto: cadena) -> entero:\n"
        "        probar:\n"
        "            devolver entero(texto)\n"
        "        excepto errordevalor:\n"
        "            imprimir(longitud(texto))\n"
        "            devolver 0\n"
        "\n"
        "    @métododeclase\n"
        "    definir crear(misma_clase):\n"
        "        devolver misma_clase()\n"
    ),
    "an attribute": "clase Punto:\n    definir __init__(mismo):\n        mismo.rango = 5\n",
    "a method": 'x = "{}".formatear(1)\n',
    "a keyword argument": "f(tipo=entero)\n",
    "a variable": "entrada = 3\nimprimir(entrada)\n",
    "a function that shadows a builtin": (
        "definir longitud(x):\n    devolver 0\nn = longitud([1])\n"
    ),
    "a module path": "importar cadena\n",
    "a soft keyword used as a name": "coincidir = patron.coincidir(texto)\n",
    "a builtin shadowed by an import": "desde os importar abrir\nfd = abrir('p', 0)\n",
    # CORE-2237: positions kept as written, and the bindings that keep their
    # old rendering so a definition and its uses agree.
    "a library function after a dot": "fd = os.open('p', 0)\nn = longitud(os.sep)\n",
    "a keyword argument into a library": "analizador.add_argument('--n', type=entero)\n",
    "a keyword argument in a class header": "clase C(Base, metaclass=tipo):\n    pasar\n",
    "a dotted module path and its module": (
        "importar entrada.lista como el\nimportar rango\nrango.x\n"
    ),
    "a relative import": "desde . importar uno\ndesde .. importar dos\n",
    "a class field read as an attribute": (
        "clase P:\n    tipo = 'x'\np = P(tipo='y')\nimprimir(p.tipo)\n"
    ),
    "a parameter passed by keyword": ("definir f(lista=nulo):\n    devolver lista\nf(lista=[1])\n"),
    "a method called as an attribute": (
        "clase Pila:\n    definir longitud(mismo):\n        devolver 3\nPila().longitud()\n"
    ),
}

# CPython 3.10 and 3.11 tokenize in pure Python, which splits a word at a
# combining mark (CORE-2192), so there the engine never sees an NFD-typed
# word whole and, like the proxy, leaves it alone.
ENGINE_READS_AN_NFD_WORD_WHOLE = sys.version_info >= (3, 12)

# Localized by the engine from English, for a spread of scripts and packs.
ENGLISH = (
    "class Reader:\n"
    "    def read(self, text: str) -> int:\n"
    "        try:\n"
    "            return int(text)\n"
    "        except ValueError:\n"
    "            print(len(text), sorted([3, 1]), float(2))\n"
    "            return 0\n"
)
OTHER_PACKS = ["fr", "de", "ar", "zh", "hi", "am"]

# Library names after a dot and as keyword arguments, and a module path:
# the engine keeps them in English when it localizes (CORE-2237).
ENGLISH_KEPT = (
    "import argparse\n"
    "fd = os.open(path, 0)\n"
    "argparse.ArgumentParser().add_argument('--n', type=int, default=len(path))\n"
    "self.input = input()\n"
)

KNOWN_DIFFERENCES = {
    "NotImplemented and Ellipsis": pytest.param(
        "es",
        "x = noimplementado\nz = elipsis\n",
        marks=pytest.mark.xfail(
            strict=True,
            reason="CORE-2219: the engine renders them as notimplemented and ellipsis",
        ),
    ),
    "a builtin typed in NFD": pytest.param(
        "es",
        unicodedata.normalize("NFD", "@métododeclase\ndefinir f(misma_clase):\n    pasar\n"),
        marks=pytest.mark.xfail(
            ENGINE_READS_AN_NFD_WORD_WHOLE,
            strict=True,
            reason="CORE-2352: the proxy matches words only as typed; the engine also NFC/NFKC",
        ),
    ),
}


@pytest.fixture(scope="module")
def proxy():
    config = LanguageServerConfig(
        source_language="en",
        target_language="es",
        enhanced_intelligence_enabled=False,  # never spawn a real backend
    )
    return EnhancedIntelligenceProxy(config)


def _engine(language):
    return transformer.TokenTranslator.from_language_pack(language, python_version=PACK_TIER)


async def _assert_same_english(proxy, language, localized):
    run = _engine(language).reverse().translate_code(localized)
    sent = (await proxy.translator_for(language).translate_to_english(localized)).translated_code
    assert sent == run, f"proxy sends {sent!r}, legesher run executes {run!r}"


class TestTheProxySendsWhatRuns:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("source", list(SPANISH.values()), ids=list(SPANISH))
    async def test_spanish_names_spelled_like_a_builtin(self, proxy, source):
        await _assert_same_english(proxy, "es", source)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", OTHER_PACKS)
    async def test_other_packs(self, proxy, language):
        localized = _engine(language).translate_code(ENGLISH)
        assert localized != ENGLISH, f"the {language} pack translated nothing"
        await _assert_same_english(proxy, language, localized)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("language", OTHER_PACKS)
    async def test_other_packs_keep_the_same_names(self, proxy, language):
        localized = _engine(language).translate_code(ENGLISH_KEPT)
        assert "os.open" in localized and "type=" in localized, localized
        await _assert_same_english(proxy, language, localized)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "language,localized", list(KNOWN_DIFFERENCES.values()), ids=list(KNOWN_DIFFERENCES)
    )
    async def test_known_differences(self, proxy, language, localized):
        await _assert_same_english(proxy, language, localized)
