"""The proxy sends the backend the English that ``legesher run`` executes (CORE-2342).

The language server does not depend on legesher-core, so the proxy keeps its
own copy of the engine's renaming rule. These pin the two together with
shared inputs: the same localized source, translated by both, must give the
same English. If the engine's rule changes (CORE-2237 plans to stop renaming
attributes, keyword arguments, definitions, module paths and import-shadowed
names spelled like a builtin, and soft keywords used as names), they fail
until the proxy follows. Known differences are strict
xfails naming the ticket that removes them.

They need legesher-core, which the monorepo workspace installs; an install
of this package on its own skips them.
"""

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
}

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
    @pytest.mark.parametrize(
        "language,localized", list(KNOWN_DIFFERENCES.values()), ids=list(KNOWN_DIFFERENCES)
    )
    async def test_known_differences(self, proxy, language, localized):
        await _assert_same_english(proxy, language, localized)
