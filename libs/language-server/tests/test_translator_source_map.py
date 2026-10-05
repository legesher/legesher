"""Every source-map mapping covers its word in both texts (CORE-2343).

The enhanced-intelligence proxy sends the backend the English text that
``IncrementalTranslator`` builds, and moves every hover request and every
range the backend returns through the translator's source map. The map used
to track the English position with running counters, which skipped the gaps
between tokens and the newlines inside a multi-line string, and counted an
indent only on the line that opened its block. A keyword mapped correctly
only at the start of an unindented line or of a block's first line, with no
multi-line string or backslash continuation above it, and that was the only
shape the package's fixtures had.

These assert the characters each mapping covers, not its numbers: the
original span is a localized word, and the English span is exactly that
word's translation.
"""

import sys

import pytest

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy


@pytest.fixture(scope="module")
def translator():
    """The translator the proxy builds for Spanish documents."""
    config = LanguageServerConfig(
        source_language="en",
        target_language="es",
        enhanced_intelligence_enabled=False,  # never spawn a real backend
    )
    return EnhancedIntelligenceProxy(config).translator_for("es")


def _covered(text, start, end):
    """The characters a one-line span covers.

    Rows are split on ``\\n`` only, as ``tokenize`` reads them.
    """
    assert start.line == end.line, f"a word's span crosses lines: {start} to {end}"
    return text.split("\n")[start.line][start.character : end.character]


# Each case: the Spanish source, and the translated words in order.
CASES = {
    "a keyword after other code on its line": (
        "x = verdadero y falso\nsi a y b:\n    pasar\n",
        ["verdadero", "y", "falso", "si", "y", "pasar"],
    ),
    "below a multi-line string": (
        'definir saludo(nombre):\n    """Saluda.\n\n    Dos.\n    """\n'
        "    devolver nombre si nombre sino nulo\n",
        ["definir", "devolver", "si", "sino", "nulo"],
    ),
    "on the line a multi-line string closes": (
        'x = a y """uno\ndos""" si verdadero sino nulo\n',
        ["y", "si", "verdadero", "sino", "nulo"],
    ),
    "at the start of a block's later lines": (
        "definir f(a):\n    b = a\n    verdadero\n    no b\n",
        ["definir", "verdadero", "no"],
    ),
    # A row starts again from no shift even inside one logical line.
    "on both sides of a backslash continuation": (
        "x = verdadero y \\\n    no a\n",
        ["verdadero", "y", "no"],
    ),
    "after a backslash continuation": (
        "x = 1 + \\\n    2 si verdadero sino nulo\n",
        ["si", "verdadero", "sino", "nulo"],
    ),
    "inside brackets over several lines": (
        "x = [\n    a si verdadero sino b,\n        nulo]\n",
        ["si", "verdadero", "sino", "nulo"],
    ),
    "localized builtins, exceptions and implicit parameters (CORE-2342)": (
        "x = longitud(mismo) si verdadero sino errordevalor\n",
        ["longitud", "mismo", "si", "verdadero", "sino", "errordevalor"],
    ),
    "after a tab indent": (
        "si a:\n\tdevolver a y verdadero\n",
        ["si", "devolver", "y", "verdadero"],
    ),
    "with CRLF line endings": (
        "si a:\r\n    devolver a y verdadero\r\n",
        ["si", "devolver", "y", "verdadero"],
    ),
}


class TestEveryMappingCoversItsWord:
    """The English span of every mapping is the translated word, in the English text."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("source,words", list(CASES.values()), ids=list(CASES))
    async def test_mapping_spans(self, translator, source, words):
        await self._assert_every_mapping_covers_its_word(translator, source, words)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        sys.version_info < (3, 12),
        reason="f-string replacement fields are separate tokens from Python 3.12",
    )
    async def test_mapping_spans_in_an_f_string_replacement_field(self, translator):
        await self._assert_every_mapping_covers_its_word(
            translator,
            'x = f"{a si verdadero sino b}" + f"{{y}}" si c sino nulo\n',
            ["si", "verdadero", "sino", "si", "sino", "nulo"],
        )

    @staticmethod
    async def _assert_every_mapping_covers_its_word(translator, source, words):
        result = await translator.translate_to_english(source)
        vocabulary = {**translator.builtin_map, **translator.keyword_map}

        mappings = result.source_map.mappings
        assert [_covered(source, m.original_start, m.original_end) for m in mappings] == words

        english = [
            (
                _covered(source, m.original_start, m.original_end),
                _covered(result.translated_code, m.translated_start, m.translated_end),
            )
            for m in mappings
        ]
        assert english == [(word, vocabulary[word]) for word in words], result.translated_code
