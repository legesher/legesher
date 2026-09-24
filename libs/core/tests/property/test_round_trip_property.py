"""Property-based round-trip tests for the translation engine (CORE-2129).

``tests/unit/test_round_trip.py`` fixes a handful of programs and asserts that
EN -> native -> EN is byte-identical. Here Hypothesis composes the programs:
identifiers are drawn from a multi-script alphabet, statements from a small
grammar, and every example is checked against six packs for four properties.

Properties, per pack in :data:`PACKS`:

1. translate then reverse is byte-identical to the source;
2. the native rendering is NFC;
3. every generated identifier survives byte-identical in the native rendering
   (the same number of NAME tokens as in the source; a substring count would
   miscount ``a`` inside ``pass``);
4. the reversed English compiles.

What the generator deliberately leaves out, and why:

* identifiers that collide with the target pack. The mapper compares NFKC
  forms, and exception names case-insensitively (``ArithmeticError`` is keyed
  ``arithmeticerror``), so an identifier whose NFKC-casefolded form equals any
  English key or native value in the pack is excluded. Those collisions are
  real and tracked on their own (CORE-1840); they are not round-trip defects.
* non-NFC identifiers. Identifiers pass through the engine verbatim, so a
  decomposed sequence in the source would set property 2 against property 1.
  Every drawn identifier is NFC.
* Python keywords (the source would not compile) and CRLF line endings (the
  tokenizer path normalises them to LF; a formatting question, not a
  vocabulary one).
"""

from __future__ import annotations

import io
import keyword
import sys
import tokenize
import unicodedata
from collections import Counter
from collections.abc import Callable
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from legesher_core import create_translator_from_language_pack
from legesher_core.round_trip import first_divergence
from legesher_i18n import LanguagePackLoader

PACKS = ("es", "ar", "hi", "zh", "th", "si")

#: Deepest block the grammar nests (top-level statements sit at depth 0).
MAX_DEPTH = 3


# ---------------------------------------------------------------------------
# Identifier alphabet
#
# Every non-ASCII character is produced with chr() from a code point range, so
# no combining mark or right-to-left letter sits literally in this file where
# a reviewer could not see it (and where Bandit would flag a bidi character).
# Ranges skip code points whose NFC form is a different sequence (Devanagari
# nukta composites, for instance); anything that still slips through is
# dropped by the NFC filter below rather than reported as a finding.
# ---------------------------------------------------------------------------


def _span(first: int, last: int) -> str:
    """Every code point from ``first`` to ``last`` inclusive."""
    return "".join(chr(point) for point in range(first, last + 1))


LATIN_START = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
LATIN_CONTINUE = "0123456789"

ARABIC_LETTERS = _span(0x0627, 0x064A)  # alef .. yeh
ARABIC_MARKS = chr(0x064E)  # fatha: a harakat (combining) mark

DEVANAGARI_LETTERS = (
    _span(0x0905, 0x0914)  # independent vowels
    + _span(0x0915, 0x0928)
    + _span(0x092A, 0x0930)
    + _span(0x0932, 0x0933)
    + _span(0x0935, 0x0939)
)
DEVANAGARI_MARKS = _span(0x093E, 0x094C) + chr(0x094D)  # vowel signs + virama

SINHALA_LETTERS = (
    _span(0x0D85, 0x0D96)
    + _span(0x0D9A, 0x0DB1)
    + _span(0x0DB3, 0x0DBB)
    + chr(0x0DBD)
    + _span(0x0DC0, 0x0DC6)
)
SINHALA_MARKS = (
    chr(0x0DCA)  # al-lakuna (virama)
    + _span(0x0DCF, 0x0DD4)
    + chr(0x0DD6)
    + _span(0x0DD8, 0x0DDF)
)

BENGALI_LETTERS = (
    _span(0x0985, 0x098C)
    + _span(0x098F, 0x0990)
    + _span(0x0993, 0x09A8)
    + _span(0x09AA, 0x09B0)
    + chr(0x09B2)
    + _span(0x09B6, 0x09B9)
)
BENGALI_MARKS = (
    _span(0x09BE, 0x09C4) + _span(0x09C7, 0x09C8) + _span(0x09CB, 0x09CC) + chr(0x09CD)
)

TAMIL_LETTERS = (
    _span(0x0B85, 0x0B8A)
    + _span(0x0B8E, 0x0B90)
    + _span(0x0B92, 0x0B95)
    + _span(0x0B99, 0x0B9A)
    + chr(0x0B9C)
    + _span(0x0B9E, 0x0B9F)
    + _span(0x0BA3, 0x0BA4)
    + _span(0x0BA8, 0x0BAA)
    + _span(0x0BAE, 0x0BB9)
)
TAMIL_MARKS = (
    _span(0x0BBE, 0x0BC2) + _span(0x0BC6, 0x0BC8) + _span(0x0BCA, 0x0BCC) + chr(0x0BCD)
)

THAI_LETTERS = _span(0x0E01, 0x0E2E) + _span(0x0E40, 0x0E44)
THAI_MARKS = chr(0x0E31) + _span(0x0E34, 0x0E3A) + _span(0x0E47, 0x0E4E)

ETHIOPIC_LETTERS = _span(0x1200, 0x1248)
CJK_LETTERS = _span(0x4E00, 0x4E4F)
HANGUL_SYLLABLES = _span(0xAC00, 0xAC4F)

START_CHARS = (
    LATIN_START
    + ARABIC_LETTERS
    + DEVANAGARI_LETTERS
    + SINHALA_LETTERS
    + BENGALI_LETTERS
    + TAMIL_LETTERS
    + THAI_LETTERS
    + ETHIOPIC_LETTERS
    + CJK_LETTERS
    + HANGUL_SYLLABLES
)
CONTINUE_CHARS = (
    START_CHARS
    + LATIN_CONTINUE
    + ARABIC_MARKS
    + DEVANAGARI_MARKS
    + SINHALA_MARKS
    + BENGALI_MARKS
    + TAMIL_MARKS
    + THAI_MARKS
)


def _fold(text: str) -> str:
    """The form the mapper compares on: NFKC, then casefold."""
    return unicodedata.normalize("NFKC", text).casefold()


def _is_nfc(text: str) -> bool:
    return unicodedata.normalize("NFC", text) == text


def _name_tokens(code: str) -> Counter[str]:
    """NAME tokens in ``code``; native keywords tokenize as NAMEs too."""
    tokens = tokenize.generate_tokens(io.StringIO(code).readline)
    return Counter(tok.string for tok in tokens if tok.type == tokenize.NAME)


def identifiers(forbidden: frozenset[str]) -> st.SearchStrategy[str]:
    """Identifiers over the multi-script alphabet that do not collide with a pack."""
    return (
        st.builds(
            "".join,
            st.tuples(
                st.sampled_from(START_CHARS),
                st.text(alphabet=CONTINUE_CHARS, max_size=11),
            ),
        )
        .filter(str.isidentifier)
        .filter(_is_nfc)
        .filter(lambda name: not keyword.iskeyword(name))
        .filter(lambda name: _fold(name) not in forbidden)
    )


# ---------------------------------------------------------------------------
# Statement grammar
# ---------------------------------------------------------------------------

Draw = Callable[[st.SearchStrategy], object]

INT_LITERALS = ("0", "1", "42")
#: String bodies carry English vocabulary on purpose: a translator that
#: rewrites inside a string literal breaks property 1.
STRING_LITERALS = ('"text"', '"def print return"', "'value'", '""')


def _expr(draw: Draw, names: list[str]) -> str:
    name = draw(st.sampled_from(names))
    other = draw(st.sampled_from(names))
    kind = draw(
        st.sampled_from(
            ("name", "int", "str", "fstring", "call", "binop", "compare", "comp")
        )
    )
    if kind == "name":
        return name
    if kind == "int":
        return draw(st.sampled_from(INT_LITERALS))
    if kind == "str":
        return draw(st.sampled_from(STRING_LITERALS))
    if kind == "fstring":
        return f'f"{{{name}}} def {{{other}}}"'
    if kind == "call":
        builtin = draw(st.sampled_from(("len", "int", "str", "range")))
        return f"{builtin}({name})"
    if kind == "binop":
        return f"{name} + {other}"
    if kind == "compare":
        return f"{name} == {other}"
    return f"[{name} for {name} in range(3) if {name}]"


def _simple(draw: Draw, names: list[str], in_loop: bool, in_def: bool) -> str:
    kinds = ["assign", "augassign", "call", "pass"]
    if in_def:
        kinds.append("return")
    if in_loop:
        kinds += ["break", "continue"]
    kind = draw(st.sampled_from(kinds))
    name = draw(st.sampled_from(names))
    if kind == "assign":
        return f"{name} = {_expr(draw, names)}"
    if kind == "augassign":
        return f"{name} += {draw(st.sampled_from(INT_LITERALS))}"
    if kind == "call":
        return f"print({_expr(draw, names)})"
    if kind == "return":
        return f"return {_expr(draw, names)}"
    return kind  # pass / break / continue


def _block(
    draw: Draw,
    names: list[str],
    lines: list[str],
    depth: int,
    in_loop: bool,
    in_def: bool,
) -> None:
    """Append one block (1-3 statements) at ``depth`` to ``lines``."""
    indent = "    " * depth
    for _ in range(draw(st.integers(min_value=1, max_value=3))):
        if depth >= MAX_DEPTH or not draw(st.booleans()):
            lines.append(indent + _simple(draw, names, in_loop, in_def))
            continue

        kind = draw(st.sampled_from(("def", "if", "for", "while", "try", "class")))
        name = draw(st.sampled_from(names))
        inner = depth + 1
        if kind == "def":
            params = draw(
                st.lists(st.sampled_from(names), min_size=2, max_size=2, unique=True)
            )
            lines.append(f"{indent}def {name}({params[0]}, {params[1]}=None):")
            _block(draw, names, lines, inner, in_loop=False, in_def=True)
        elif kind == "if":
            lines.append(f"{indent}if {_expr(draw, names)}:")
            _block(draw, names, lines, inner, in_loop, in_def)
            if draw(st.booleans()):
                lines.append(f"{indent}elif {_expr(draw, names)}:")
                _block(draw, names, lines, inner, in_loop, in_def)
            if draw(st.booleans()):
                lines.append(f"{indent}else:")
                _block(draw, names, lines, inner, in_loop, in_def)
        elif kind == "for":
            bound = draw(st.sampled_from(INT_LITERALS))
            lines.append(f"{indent}for {name} in range({bound}):")
            _block(draw, names, lines, inner, in_loop=True, in_def=in_def)
        elif kind == "while":
            lines.append(f"{indent}while {_expr(draw, names)}:")
            _block(draw, names, lines, inner, in_loop=True, in_def=in_def)
        elif kind == "try":
            lines.append(f"{indent}try:")
            _block(draw, names, lines, inner, in_loop, in_def)
            lines.append(f"{indent}except ValueError as {name}:")
            _block(draw, names, lines, inner, in_loop, in_def)
            if draw(st.booleans()):
                lines.append(f"{indent}finally:")
                _block(draw, names, lines, inner, in_loop, in_def)
        else:
            lines.append(f"{indent}class {name}:")
            _block(draw, names, lines, inner, in_loop=False, in_def=False)

        if draw(st.booleans()):
            lines.append("")  # a blank line after a compound statement


@st.composite
def programs(draw: Draw, ident: st.SearchStrategy[str]) -> tuple[str, list[str]]:
    """A small program and the identifiers it was built from."""
    names = draw(st.lists(ident, min_size=3, max_size=6, unique=True))
    lines: list[str] = []
    _block(draw, names, lines, depth=0, in_loop=False, in_def=False)
    return "\n".join(lines) + "\n", names


# ---------------------------------------------------------------------------
# The properties
# ---------------------------------------------------------------------------


class Engines:
    """Per pack: (EN->native translator, native->EN translator, forbidden forms).

    A thin mapping with a one-line ``repr``. Hypothesis prints every argument
    of a failing test, fixtures included, and the raw dict of translators and
    six forbidden frozensets ran to about 2,300 lines, burying the shrunk
    program and the ``@reproduce_failure`` blob that matter.
    """

    def __init__(self, built: dict[str, tuple[Any, Any, frozenset[str]]]) -> None:
        self._built = built

    def __getitem__(self, code: str) -> tuple[Any, Any, frozenset[str]]:
        return self._built[code]

    def __repr__(self) -> str:
        return f"<Engines packs={sorted(self._built)}>"


@pytest.fixture(scope="session")
def engines() -> Engines:
    """Build :class:`Engines` for every pack under test.

    The forbidden set is every English key and native value the translator can
    match, folded the way the mapper folds (see :func:`_fold`): the mapper's
    own maps plus the pack's exception section, which the mapper matches by
    the real exception name.
    """
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    loader = LanguagePackLoader()
    built = {}
    for code in PACKS:
        forward = create_translator_from_language_pack("python", code, version)
        pack = loader.load(code, target="python", version=version)
        sections = (
            forward.mapper.keyword_map,
            forward.mapper.builtin_map,
            forward.mapper.implicit_param_map,
            pack.keywords,
            pack.builtins,
            pack.exceptions,
            pack.implicit_params,
        )
        forbidden: set[str] = set()
        for section in sections:
            forbidden.update(_fold(key) for key in section)
            forbidden.update(_fold(value) for value in section.values())
        built[code] = (forward, forward.reverse(), frozenset(forbidden))
    return Engines(built)


@pytest.mark.parametrize("code", PACKS)
# print_blob: a CI runner keeps no example database, so the failure output
# must carry everything needed to replay the example locally.
@settings(max_examples=60, deadline=None, print_blob=True)
@given(data=st.data())
def test_round_trip_properties(engines, code, data):
    """EN -> native -> EN is lossless, NFC, identifier-preserving, compilable."""
    forward, reverse, forbidden = engines[code]
    source, names = data.draw(programs(identifiers(forbidden)), label="program")
    compile(source, "<generated>", "exec")  # the generator must emit valid Python

    native = forward.translate_code(source, "en", code)
    back = reverse.translate_code(native, code, "en")

    divergence = first_divergence(source, back)
    assert divergence is None, f"EN -> {code} -> EN diverged: {divergence}"
    assert unicodedata.normalize("NFC", native) == native, (
        f"{code} rendering is not NFC: {native!r}"
    )
    source_names, native_names = _name_tokens(source), _name_tokens(native)
    for name in names:
        assert native_names[name] == source_names[name], (
            f"identifier {name!r} did not survive translation to {code}: {native!r}"
        )
    compile(back, "<reversed>", "exec")
