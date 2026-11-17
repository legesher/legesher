"""A pack word typed in another Unicode form still translates, in every pack.

Text identity here is store-NFC, compare-NFKC: a pack stores each word in
one form, and the same word reaches the engine in others. macOS hands back
decomposed text (NFD), a PDF paste carries ligatures and Arabic presentation
forms, an input method left in fullwidth mode types fullwidth letters. Python
reads all of them as one identifier (PEP 3131), so the engine must read all
of them as the one pack word. ``TokenMapper`` implements that as an exact
lookup with an NFKC fallback; this suite holds both backends to it for every
word of every shipped pack, in every section.

The invariant is stated against the stored spelling, not against a list:
whatever a spelling the pack stores translates to, every spelling that is
NFKC-equal to it translates to the same thing.

Three kinds of spelling are generated from the Unicode tables, never from a
hand-kept list, so a new pack or a new word is covered the day it ships:

* ``decomposed``: the NFD form (Arabic hamza carriers, Vietnamese and Latin
  diacritics, Hangul syllables as jamo).
* ``compatibility``: each character replaced by a single code point that
  NFKC folds to it (fullwidth Latin, Arabic and Hebrew presentation forms,
  halfwidth katakana).
* ``ligature``: one run of characters replaced by a single code point that
  NFKC expands to it (Latin ``fi``, Arabic lam-alef, the precomposed
  Devanagari nukta letters that NFC itself keeps decomposed).

On CPython 3.10 and 3.11 the pure-Python tokenizer cannot read a name with
a combining mark whole, so the token backend never sees such a spelling as
one name (``tests/interpreter_gaps.py``, gap 1). Those spellings are held in
their own strict expected failure there and stay in the assertion everywhere
else.
"""

from __future__ import annotations

import functools
import logging
import sys
import unicodedata

import pytest

from legesher_core import create_translator_from_language_pack
from legesher_core.script_lookup import get_script
from legesher_core.utils import is_rtl_language
from legesher_i18n import get_active_language_codes
from tests.interpreter_gaps import (
    PURE_PYTHON_TOKENIZER,
    error_tokens,
    unloadable_here,
    xfail_if_unloadable_here,
)

RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

#: Every active pack except the pivot itself.
LANGUAGES: tuple[str, ...] = tuple(
    sorted(code for code in get_active_language_codes() if code != "en")
)

BACKENDS: tuple[str, ...] = ("token", "tree-sitter")

#: The mapper's three tables. Exceptions are merged into the builtin table
#: when a translator is built from a pack, so that row covers both.
SECTIONS: tuple[str, ...] = ("keyword_map", "builtin_map", "implicit_param_map")

KINDS: tuple[str, ...] = ("decomposed", "compatibility", "ligature")

#: Compatibility tags in the order a typist meets them: an input method's
#: width setting first, then the shaped forms a paste carries.
_TAG_ORDER = (
    "<wide>",
    "<narrow>",
    "<isolated>",
    "<final>",
    "<initial>",
    "<medial>",
    "<font>",
    "<compat>",
    "",
)


def _tag(char: str) -> str:
    decomposition = unicodedata.decomposition(char)
    return decomposition.split(" ", 1)[0] if decomposition.startswith("<") else ""


@functools.cache
def _folds() -> tuple[dict[str, str], dict[str, str]]:
    """``(single, runs)``: code points NFKC folds to one character, and to a run.

    Only code points that may continue an identifier are kept, since a
    spelling Python would refuse is not a spelling of the word. Where several
    code points fold to the same text, the first by ``_TAG_ORDER`` and then
    by code point wins, so the choice is the same on every run.
    """
    single: dict[str, tuple[int, int, str]] = {}
    runs: dict[str, tuple[int, int, str]] = {}
    for code_point in range(0x80, 0x30000):
        char = chr(code_point)
        folded = unicodedata.normalize("NFKC", char)
        if folded == char or not folded or not ("a" + char).isidentifier():
            continue
        tag = _tag(char)
        if tag not in _TAG_ORDER:
            continue
        rank = (_TAG_ORDER.index(tag), code_point, char)
        table = single if len(folded) == 1 else runs
        if folded not in table or rank < table[folded]:
            table[folded] = rank
    return (
        {text: rank[2] for text, rank in single.items()},
        {text: rank[2] for text, rank in runs.items()},
    )


def _decomposed(word: str) -> str:
    return unicodedata.normalize("NFD", word)


def _compatibility(word: str) -> str:
    single, _ = _folds()
    return "".join(single.get(char, char) for char in word)


def _ligature(word: str) -> str:
    _, runs = _folds()
    for length in (3, 2):
        for start in range(len(word) - length + 1):
            replacement = runs.get(word[start : start + length])
            if replacement is not None:
                return word[:start] + replacement + word[start + length :]
    return word


_GENERATORS = {
    "decomposed": _decomposed,
    "compatibility": _compatibility,
    "ligature": _ligature,
}


def spellings(word: str) -> dict[str, str]:
    """Other spellings of ``word`` that Python reads as the same identifier.

    Keyed by kind. A candidate is kept only when it differs from ``word``,
    is NFKC-equal to it, and is an identifier on the running interpreter.
    """
    target = unicodedata.normalize("NFKC", word)
    found: dict[str, str] = {}
    for kind, generate in _GENERATORS.items():
        candidate = generate(word)
        if (
            candidate != word
            and candidate not in found.values()
            and candidate.isidentifier()
            and unicodedata.normalize("NFKC", candidate) == target
        ):
            found[kind] = candidate
    return found


def _code_points(text: str) -> str:
    return " ".join(f"U+{ord(char):04X}" for char in text)


@functools.cache
def _reverse(language: str, backend: str):
    forward = create_translator_from_language_pack(
        "python", language, use_tree_sitter=backend == "tree-sitter"
    )
    return forward.reverse()


@functools.cache
def _stored(language: str, section: str) -> tuple[str, ...]:
    """The native words of one table, compound entries left out.

    ``except*`` is keyed with its star and matched across two tokens; its
    word is the ``except`` word, which the keyword table carries by itself.
    """
    table = getattr(_reverse(language, "token").mapper, section)
    return tuple(sorted(word for word in table if word.isidentifier()))


def _reads_whole(spelling: str) -> bool:
    """Whether the running ``tokenize`` reads ``spelling`` as one name."""
    return not error_tokens(spelling + "\n")


def _mismatches(
    language: str, backend: str, section: str, *, whole: bool
) -> tuple[list[str], int]:
    """``(failures, checked)`` over one table's spellings.

    ``whole`` picks the pairs the running tokenizer reads as one name each
    (``True``) or the pairs where it fragments the stored word or the
    spelling (``False``); the tree-sitter backend does not read names
    through ``tokenize``, so every pair is whole for it.
    """
    reverse = _reverse(language, backend)
    failures: list[str] = []
    checked = 0
    for word in _stored(language, section):
        expected = reverse.translate_code(word + "\n")
        word_reads_whole = backend == "tree-sitter" or _reads_whole(word)
        for kind, spelling in spellings(word).items():
            reads_whole = word_reads_whole and (
                backend == "tree-sitter" or _reads_whole(spelling)
            )
            if reads_whole is not whole:
                continue
            checked += 1
            actual = reverse.translate_code(spelling + "\n")
            if actual != expected:
                failures.append(
                    f"{language} {section} {kind}: {word!r} gives "
                    f"{expected.strip()!r}, but its spelling "
                    f"[{_code_points(spelling)}] gives {actual.strip()!r}"
                )
    return failures, checked


@pytest.mark.parametrize("section", SECTIONS)
@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("language", LANGUAGES)
def test_every_spelling_translates_as_the_stored_word(
    request: pytest.FixtureRequest, language: str, backend: str, section: str
) -> None:
    xfail_if_unloadable_here(request, language, RUNNING_VERSION)
    failures, _ = _mismatches(language, backend, section, whole=True)
    assert not failures, "\n".join(failures)


@pytest.mark.skipif(
    not PURE_PYTHON_TOKENIZER,
    reason="the C tokenizer (CPython 3.12+) reads every spelling as one name",
)
@pytest.mark.parametrize("section", SECTIONS)
@pytest.mark.parametrize("language", LANGUAGES)
def test_spellings_the_pure_python_tokenizer_fragments(
    request: pytest.FixtureRequest, language: str, section: str
) -> None:
    """Gap 1, pinned for spellings as it is for stored words.

    A name with a combining mark lexes as NAME / ERRORTOKEN fragments on
    CPython 3.10 and 3.11, so the token backend never matches it, whether the
    mark is in the stored word or in the spelling. Strict: a table whose
    fragmenting pairs all start to translate alike reports XPASS.
    """
    failures, checked = _mismatches(language, "token", section, whole=False)
    if not checked:
        pytest.skip("no spelling of this table fragments under this tokenizer")
    request.applymarker(
        pytest.mark.xfail(
            strict=True,
            reason=(
                f"pure-Python tokenize (CPython {RUNNING_VERSION}) reads a name "
                "with a combining mark as fragments, so the token backend "
                "cannot match the spelling (tests/interpreter_gaps.py, gap 1; "
                "CORE-2192)"
            ),
        )
    )
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_shipped_pack_holds_two_words_that_differ_only_in_form(
    request: pytest.FixtureRequest,
    language: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The fallback never has to choose between two entries of a shipped pack.

    ``TokenMapper`` warns when two keys of one table fold to the same NFKC
    form with different targets, and keeps the first. The pack validator's
    stability rule (``SchemaValidator.check_normalization``) is what makes
    that unreachable for shipped data; this holds the engine side of the
    same promise, in both directions, so a pack that slips past the
    validator fails here by name.
    """
    xfail_if_unloadable_here(request, language, RUNNING_VERSION)
    with caplog.at_level(logging.WARNING, logger="legesher_core.token_mapper"):
        forward = create_translator_from_language_pack(
            "python", language, use_tree_sitter=False
        )
        forward.reverse()
    collisions = sorted(
        {
            record.getMessage()
            for record in caplog.records
            if "NFKC normalization collision" in record.getMessage()
        }
    )
    assert not collisions, f"{language}: " + "; ".join(collisions)


# -- guards: the sweep must never pass by testing nothing --------------------


@functools.cache
def _scripts_by_kind() -> dict[str, dict[str, set[str]]]:
    """Per kind, the scripts with at least one spelling and the languages."""
    covered: dict[str, dict[str, set[str]]] = {kind: {} for kind in KINDS}
    for language in LANGUAGES:
        if language in _unloadable():
            continue
        for section in SECTIONS:
            for word in _stored(language, section):
                for kind in spellings(word):
                    script = next(
                        (
                            get_script(char)
                            for char in word
                            if get_script(char) not in ("Common", "Inherited")
                        ),
                        "Common",
                    )
                    covered[kind].setdefault(script, set()).add(language)
    return covered


@functools.cache
def _unloadable() -> frozenset[str]:
    return frozenset(
        language for language in LANGUAGES if unloadable_here(language, RUNNING_VERSION)
    )


@pytest.mark.parametrize("kind", ("decomposed", "compatibility"))
def test_each_kind_reaches_three_scripts_and_a_right_to_left_one(kind: str) -> None:
    covered = _scripts_by_kind()[kind]
    assert len(covered) >= 3, f"{kind} spellings exist only for {sorted(covered)}"
    right_to_left = sorted(
        script
        for script, languages in covered.items()
        if any(is_rtl_language(language) for language in languages)
        and script != "Latin"
    )
    assert right_to_left, f"no right-to-left script has a {kind} spelling"


def test_ligature_spellings_exist() -> None:
    assert _scripts_by_kind()["ligature"], "no pack word has a ligature spelling"


@pytest.mark.parametrize(
    ("word", "kind", "code_points"),
    [
        # Arabic alef with hamza above, as macOS decomposes it.
        ("أكد", "decomposed", "U+0627 U+0654 U+0643 U+062F"),
        # Vietnamese: base letter, then the tone mark.
        ("và", "decomposed", "U+0076 U+0061 U+0300"),
        # Hangul syllable as its jamo.
        ("만약", "decomposed", "U+1106 U+1161 U+11AB U+110B U+1163 U+11A8"),
        # Fullwidth Latin from an input method left in fullwidth mode.
        ("si", "compatibility", "U+FF53 U+FF49"),
        # Hebrew wide alef, a presentation form.
        ("אם", "compatibility", "U+FB21 U+FB26"),
        # Latin fi ligature from a PDF paste.
        ("definir", "ligature", "U+0064 U+0065 U+FB01 U+006E U+0069 U+0072"),
        # Devanagari qa: one code point that NFC itself decomposes.
        ("क़", "ligature", "U+0958"),
    ],
)
def test_the_generators_produce_the_forms_typists_meet(
    word: str, kind: str, code_points: str
) -> None:
    assert _code_points(spellings(word)[kind]) == code_points
