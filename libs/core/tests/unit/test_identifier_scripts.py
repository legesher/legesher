"""Identifiers in every script the packs write survive translation untouched.

Why a Latin control proves nothing: Latin letters are all category L,
which every tokenizer and every ``\\w`` reads as word characters. The
scripts the packs actually write carry vowel signs, viramas, harakat and
joiners: categories Mn, Mc and Cf (``\\p{M}`` and format characters), which
``\\w`` excludes and which NFC/NFKC can reorder. ``latin_control`` passing
says nothing about ``हिन्दी``; each script has to be asserted on its own,
and the control is here only to show the harness itself works.

Identifiers are the writer's layer and are never translated, so the
property is strict: EN -> X leaves every occurrence of every identifier
byte-identical (the multiset of NAME tokens equal to the identifier is the
same in both renderings, so a lost or duplicated occurrence is caught, not
just a changed spelling), X -> EN returns the source byte-identical, and
the result compiles. Each identifier is used as a parameter, an operand
and an assignment target so every position the tokenizer sees it in is
covered.

The compare-NFC contract (``legesher_core.text_identity``): a canonically
equivalent spelling of a native keyword, here the NFD decomposition, still
reverse-translates to the English keyword because table lookups normalize
to NFC before matching.

Interpreter-dependent cases are strict xfails with the mechanism named:

* ZWJ (U+200D) joined ``Other_ID_Continue`` in Unicode 15.1, first shipped
  by CPython 3.13. Older interpreters reject it in an identifier, so the
  Sinhala conjunct cannot compile there (and on 3.12 the C tokenizer
  refuses the source outright, so nothing is translated).
* CPython 3.10 and 3.11 fragment marked names in ``tokenize``; the return
  hop is then inert for packs whose keywords carry marks. See
  ``tests/interpreter_gaps.py``.
"""

from __future__ import annotations

import io
import tokenize
import unicodedata
from collections import Counter

import pytest

from legesher_core import create_translator_from_language_pack
from legesher_core.round_trip import first_divergence
from legesher_i18n.pack_loader import LanguagePackLoader
from tests.interpreter_gaps import xfail_if_return_hop_is_inert

# Format and combining characters are built from code points, never
# written literally (Trojan-Source linters, and the reader's eyes).
ZWJ = chr(0x200D)  # ZERO WIDTH JOINER: Sinhala conjuncts
FATHATAN = chr(0x064B)  # ARABIC FATHATAN: a haraka, category Mn

#: One identifier per script, each a valid Python identifier on CPython
#: 3.13 (asserted below, so the harness never tests a broken fixture).
IDENTIFIERS: dict[str, str] = {
    "latin_control": "latin_control",
    # Vowel signs (Mc) and a virama (Mn).
    "devanagari": "हिन्दी",
    # Virama + ZWJ + consonant: the conjunct the si policy licenses ZWJ for.
    "sinhala_zwj": "ශ්" + ZWJ + "රී",
    "tamil": "தமிழ்",
    "bengali": "বাংলা",
    "thai": "ไทย",
    # Qamats, shin dot and holam: pointed, already in canonical order.
    "hebrew_pointed": "שָׁלוֹם",
    # Damma, sukun and fathatan on the letters.
    "arabic_harakat": "شُكْر" + FATHATAN + "ا",
    "ethiopic": "አማርኛ",
    # Medial ra (Mc), asat (Mn) and a vowel sign (Mc).
    "myanmar": "မြန်မာ",
    "cjk": "变量",
    "hangul": "변수",
}

#: Packs across the script families: Latin, Arabic, Devanagari, Sinhala,
#: Thai, Ethiopic and Han.
PACKS = ("es", "ar", "hi", "si", "th", "am", "zh")

#: One identifier in four positions: parameter, operand, iteration bound
#: and module-level assignment target.
SINGLE_IDENTIFIER_PROGRAM = """\
def compute({name}):
    total = 0
    for item in range({name}):
        total += item
    return total + {name}


{name} = compute(3)
"""

#: Every identifier at once, across function, parameter, local, loop
#: variable and module-level names.
ALL_IDENTIFIERS_PROGRAM = """\
def {devanagari}({tamil}, {bengali}):
    {thai} = {tamil} + {bengali}
    if {thai} > 0:
        return {thai}
    return 0


def {hebrew_pointed}({arabic_harakat}):
    {ethiopic} = [{myanmar} for {myanmar} in range({arabic_harakat})]
    {cjk} = len({ethiopic})
    {hangul} = {cjk} * 2
    {sinhala_zwj} = {hangul} - {cjk}
    {latin_control} = {sinhala_zwj}
    return {latin_control}
"""

#: Whether this interpreter accepts ZWJ inside an identifier (Unicode 15.1+).
ZWJ_IS_IDENTIFIER_CHARACTER = ("a" + ZWJ + "b").isidentifier()

ZWJ_REASON = (
    "ZWJ (U+200D) is an identifier character only from Unicode 15.1 "
    "(CPython 3.13); this interpreter rejects it, so the Sinhala conjunct "
    "cannot compile here"
)


@pytest.fixture(scope="module")
def loader() -> LanguagePackLoader:
    return LanguagePackLoader()


@pytest.fixture(scope="module")
def translators():
    """Forward and reverse translators for every pack under test."""
    pairs = {}
    for code in PACKS:
        forward = create_translator_from_language_pack(
            "python", code, use_tree_sitter=False
        )
        pairs[code] = (forward, forward.reverse())
    return pairs


def _xfail_if_zwj_unsupported(request: pytest.FixtureRequest, name: str) -> None:
    if ZWJ in name and not ZWJ_IS_IDENTIFIER_CHARACTER:
        request.applymarker(pytest.mark.xfail(strict=True, reason=ZWJ_REASON))


def _name_occurrences(text: str) -> Counter[str]:
    """Multiset of NAME tokens in ``text``, one entry per occurrence.

    On CPython 3.10 and 3.11 ``tokenize`` spells NAME as ``\\w+`` and lexes
    a marked name as NAME / ERRORTOKEN / NAME fragments (gap 1 in
    ``tests/interpreter_gaps.py``). Adjacent fragments are glued back into
    the one name they came from, so the count is per occurrence on every
    supported interpreter; where the C tokenizer reads the name whole the
    gluing is a no-op.
    """
    names: Counter[str] = Counter()
    pending = ""
    pending_end: tuple[int, int] | None = None
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        is_fragment = (
            token.type in (tokenize.NAME, tokenize.ERRORTOKEN)
            and token.string.strip() != ""
        )
        if is_fragment and pending and token.start == pending_end:
            pending += token.string
            pending_end = token.end
            continue
        if pending:
            names[pending] += 1
            pending = ""
        if is_fragment:
            pending, pending_end = token.string, token.end
    if pending:
        names[pending] += 1
    return names


def _assert_round_trip(
    code: str, source: str, identifiers: list[str], translators
) -> None:
    forward, reverse = translators[code]
    native = forward.translate_code(source, "en", code)
    assert native != source, f"[{code}] nothing translated"
    expected = _name_occurrences(source)
    actual = _name_occurrences(native)
    for identifier in identifiers:
        codepoints = " ".join(f"U+{ord(ch):04X}" for ch in identifier)
        # The harness itself: the identifier lexes as a name in the source.
        assert expected[identifier] > 0, (
            f"identifier {identifier!r} ({codepoints}) is not a NAME in the source"
        )
        assert actual[identifier] == expected[identifier], (
            f"[{code}] identifier {identifier!r} ({codepoints}) appears "
            f"{expected[identifier]} times in the source and "
            f"{actual[identifier]} times after EN->{code}:\n{native}"
        )
    back = reverse.translate_code(native, code, "en")
    assert back == source, (
        f"[{code}] EN->{code}->EN diverged at {first_divergence(source, back)}"
    )
    compile(back, f"<{code}>", "exec", dont_inherit=True)


# -- the fixtures themselves ---------------------------------------------------


@pytest.mark.parametrize("script", IDENTIFIERS, ids=str)
def test_fixture_is_a_canonical_identifier(script: str, request):
    """Stored NFC and accepted by the compiler, or the harness tests itself."""
    name = IDENTIFIERS[script]
    _xfail_if_zwj_unsupported(request, name)
    assert unicodedata.normalize("NFC", name) == name
    assert name.isidentifier(), f"{script}: {name!r} is not an identifier here"


def test_marked_scripts_are_not_plain_letters():
    """The point of the module: most fixtures carry M or Cf characters."""
    marked = {
        script
        for script, name in IDENTIFIERS.items()
        if any(unicodedata.category(ch)[0] == "M" or ch == ZWJ for ch in name)
    }
    assert "latin_control" not in marked
    assert marked >= {
        "devanagari",
        "sinhala_zwj",
        "tamil",
        "bengali",
        "hebrew_pointed",
        "arabic_harakat",
        "myanmar",
    }, marked


# -- identifiers through the packs ----------------------------------------------


@pytest.mark.parametrize("script", IDENTIFIERS, ids=str)
@pytest.mark.parametrize("code", PACKS)
def test_identifier_survives_the_round_trip(
    code: str, script: str, translators, request: pytest.FixtureRequest
):
    name = IDENTIFIERS[script]
    _xfail_if_zwj_unsupported(request, name)
    source = SINGLE_IDENTIFIER_PROGRAM.format(name=name)
    forward, _ = translators[code]
    xfail_if_return_hop_is_inert(
        request, source, forward.translate_code(source, "en", code)
    )
    _assert_round_trip(code, source, [name], translators)


@pytest.mark.parametrize("code", PACKS)
def test_all_identifiers_survive_together(
    code: str, translators, request: pytest.FixtureRequest
):
    _xfail_if_zwj_unsupported(request, IDENTIFIERS["sinhala_zwj"])
    source = ALL_IDENTIFIERS_PROGRAM.format(**IDENTIFIERS)
    forward, _ = translators[code]
    xfail_if_return_hop_is_inert(
        request, source, forward.translate_code(source, "en", code)
    )
    _assert_round_trip(code, source, list(IDENTIFIERS.values()), translators)


# -- the compare-NFC contract ---------------------------------------------------

#: (pack, English keyword, English snippet using it). Each pack's rendering
#: of the keyword must change under NFD, which the test asserts first.
NFD_CASES = (
    ("vi", "if", "if x:\n    pass\n"),
    ("fr", "def", "def f():\n    pass\n"),
    ("de", "for", "for i in x:\n    pass\n"),
    ("ar", "else", "if x:\n    pass\nelse:\n    pass\n"),
)


@pytest.mark.parametrize(
    "code,keyword,source", NFD_CASES, ids=[f"{c}-{k}" for c, k, _ in NFD_CASES]
)
def test_nfd_spelling_of_native_keyword_reverse_translates(
    code: str, keyword: str, source: str, loader, request: pytest.FixtureRequest
):
    forward = create_translator_from_language_pack(
        "python", code, use_tree_sitter=False
    )
    reverse = forward.reverse()
    rendering = loader.load(code, "python", forward.python_version).keywords[keyword]
    decomposed = unicodedata.normalize("NFD", rendering)
    assert decomposed != rendering, (
        f"{code} {keyword!r}: pick a keyword that decomposes"
    )
    assert unicodedata.normalize("NFC", decomposed) == rendering

    native = forward.translate_code(source, "en", code)
    assert native.count(rendering) == 1, native
    native_nfd = native.replace(rendering, decomposed)
    assert native_nfd != native
    xfail_if_return_hop_is_inert(request, source, native_nfd)

    assert reverse.translate_code(native, code, "en") == source
    assert reverse.translate_code(native_nfd, code, "en") == source, (
        f"[{code}] NFD spelling of {rendering!r} did not reverse to {keyword!r}"
    )
