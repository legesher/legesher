"""Native punctuation in code position reads as the mark the author meant.

An Arabic, Persian or Urdu keyboard puts ``،`` and ``؛`` on the comma and
semicolon keys, and a Chinese, Japanese or Korean input method in fullwidth
mode types ``，`` ``；`` ``：`` ``（`` ``）``. Python refuses all seven outside a
string or comment, so a program typed the natural way did not run.

What the engine promises, and what this suite holds it to:

* **Input side only.** A native mark in code position is read as its ASCII
  equivalent, in both backends and in every pack. The engine never writes a
  native mark: display and the return trip carry ASCII.
* **Code position only.** A mark inside a string, a comment or the text of an
  f-string is the author's prose and survives byte for byte.
* **Offsets never move.** One character is replaced by one character.
* **The stored file is the author's.** The git clean filter does not touch
  punctuation, so git stores what was typed.
* **The round-trip check stays strict.** Source that uses a native mark in
  code position comes back with the ASCII one, which is not byte-identical,
  and the report names punctuation as the cause.

"Code position" is defined here the way Python defines it, independently of
the implementation: wherever ``tokenize`` reports an operator token in the
same program typed with ASCII punctuation.
"""

from __future__ import annotations

import functools
import io
import sys
import tokenize

import pytest

from legesher_core import create_translator_from_language_pack, verify_round_trip
from legesher_core.git_filter import GitFilter
from legesher_core.native_punctuation import (
    NATIVE_PUNCTUATION,
    fold_code_punctuation,
)
from legesher_core.round_trip import Layer
from legesher_i18n import get_active_language_codes
from legesher_i18n.pack_loader import LanguagePackLoader
from tests.corpus import CorpusFile, corpus_for

RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

LANGUAGES: tuple[str, ...] = tuple(
    sorted(code for code in get_active_language_codes() if code != "en")
)

ENTRIES: tuple[CorpusFile, ...] = corpus_for(RUNNING_VERSION)

BACKENDS: tuple[str, ...] = ("token", "tree-sitter")

#: What each family of keyboard types in place of the ASCII mark.
FAMILIES: dict[str, dict[str, str]] = {
    "arabic": {",": "\u060c", ";": "\u061b"},
    "fullwidth": {
        ",": "\uff0c",
        ";": "\uff1b",
        ":": "\uff1a",
        "(": "\uff08",
        ")": "\uff09",
    },
}

_FSTRING_TEXT = tuple(
    getattr(tokenize, name)
    for name in ("FSTRING_MIDDLE", "TSTRING_MIDDLE")
    if hasattr(tokenize, name)
)
_PROSE = (tokenize.STRING, tokenize.COMMENT, *_FSTRING_TEXT)


def _offsets(source: str) -> list[int]:
    starts = [0]
    index = source.find("\n")
    while index != -1:
        starts.append(index + 1)
        index = source.find("\n", index + 1)
    return starts


def _spans(source: str, types: tuple[int, ...]) -> list[tuple[int, int, str]]:
    """``(start, end, text)`` of every token of the given types."""
    starts = _offsets(source)
    found = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in types:
            start = starts[token.start[0] - 1] + token.start[1]
            end = starts[token.end[0] - 1] + token.end[1]
            found.append((start, end, source[start:end]))
    return found


def typed_in_code(source: str, marks: dict[str, str]) -> tuple[str, int]:
    """``source`` with its operator-token marks typed natively, and how many.

    An operator token that is one of the marks is retyped, and so is the
    colon of ``:=``; every other operator (``->``, ``::``) is left alone.
    """
    chars = list(source)
    count = 0
    for start, _, text in _spans(source, (tokenize.OP,)):
        native = marks.get(":" if text == ":=" else text)
        if native is not None:
            chars[start] = native
            count += 1
    return "".join(chars), count


def typed_in_prose(source: str, marks: dict[str, str]) -> tuple[str, int]:
    """``source`` with native marks typed inside strings and comments."""
    chars = list(source)
    count = 0
    for start, end, _ in _spans(source, _PROSE):
        for offset in range(start, end):
            native = marks.get(chars[offset])
            if native is not None:
                chars[offset] = native
                count += 1
    return "".join(chars), count


def prose(source: str) -> list[str]:
    return [text for _, _, text in _spans(source, _PROSE)]


@functools.cache
def _translators(language: str, backend: str):
    forward = create_translator_from_language_pack(
        "python", language, use_tree_sitter=backend == "tree-sitter"
    )
    return forward, forward.reverse()


@functools.cache
def _native(language: str, name: str) -> str:
    entry = next(entry for entry in ENTRIES if entry.name == name)
    forward, _ = _translators(language, "token")
    return forward.translate_code(entry.source, "en", language)


@functools.cache
def _plain_english(language: str, backend: str, name: str) -> str:
    """What the engine reads from the pack's rendering typed with ASCII marks."""
    _, reverse = _translators(language, backend)
    return reverse.translate_code(_native(language, name), language, "en")


def _entry_id(entry: CorpusFile) -> str:
    return entry.name


# -- the table ----------------------------------------------------------------


def test_the_table_is_the_seven_marks() -> None:
    assert dict(NATIVE_PUNCTUATION) == {
        "\u060c": ",",  # ARABIC COMMA
        "\u061b": ";",  # ARABIC SEMICOLON
        "\uff0c": ",",  # FULLWIDTH COMMA
        "\uff1b": ";",  # FULLWIDTH SEMICOLON
        "\uff1a": ":",  # FULLWIDTH COLON
        "\uff08": "(",  # FULLWIDTH LEFT PARENTHESIS
        "\uff09": ")",  # FULLWIDTH RIGHT PARENTHESIS
    }


def test_every_family_mark_is_in_the_table() -> None:
    typed = {mark for marks in FAMILIES.values() for mark in marks.values()}
    assert typed == set(NATIVE_PUNCTUATION)


# -- every pack, the whole corpus, both backends ---------------------------------


@pytest.mark.parametrize("family", sorted(FAMILIES))
@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("language", LANGUAGES)
def test_code_typed_with_native_marks_reads_as_the_ascii_program(
    language: str, backend: str, entry: CorpusFile, family: str
) -> None:
    """Typing the marks natively changes nothing about what the engine reads.

    Stated against the same program with ASCII marks, so the known
    round-trip failures and the interpreter gaps, which this change does not
    touch, cancel out on both sides.
    """
    native = _native(language, entry.name)
    typed, count = typed_in_code(native, FAMILIES[family])
    if not count:
        pytest.skip(f"{entry.name} has no {family} mark in code position")
    _, reverse = _translators(language, backend)
    assert reverse.translate_code(typed, language, "en") == _plain_english(
        language, backend, entry.name
    )


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_the_code_sweep_types_every_mark_of_the_family(family: str) -> None:
    """Every mark of each family is typed somewhere in the corpus."""
    marks = FAMILIES[family]
    typed = "".join(typed_in_code(entry.source, marks)[0] for entry in ENTRIES)
    missing = sorted(
        ascii_mark for ascii_mark, mark in marks.items() if mark not in typed
    )
    assert not missing, f"no corpus file has {missing} in code position"


@pytest.mark.parametrize("family", sorted(FAMILIES))
@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("language", ("ar", "zh", "hi", "he", "th", "si", "ko"))
def test_native_marks_in_prose_survive_byte_for_byte(
    language: str, backend: str, entry: CorpusFile, family: str
) -> None:
    native = _native(language, entry.name)
    typed, count = typed_in_prose(native, FAMILIES[family])
    if not count:
        pytest.skip(f"{entry.name} has no {family} mark inside a string or comment")
    _, reverse = _translators(language, backend)
    back = reverse.translate_code(typed, language, "en")
    assert prose(back) == prose(typed)


def test_the_prose_sweep_is_not_empty() -> None:
    counts = {
        family: sum(typed_in_prose(entry.source, marks)[1] for entry in ENTRIES)
        for family, marks in FAMILIES.items()
    }
    assert all(counts.values()), counts


# -- the acceptance samples, spelled out -------------------------------------------

#: Vocalised Arabic in the string and the comment: combining marks beside the
#: Arabic comma, which must all survive.
ARABIC_ENGLISH = (
    "def join(first, second):\n"
    "    pair = [first, second]; total = len(pair)\n"
    "    return 'مَرْحَبًا، يَا عَالَم؛'  # تَعْلِيق، هُنَا؛\n"
)

#: Han in the string and the comment, with fullwidth marks that are prose.
CHINESE_ENGLISH = (
    "def join(first, second):\n"
    "    pair = (first, second); total = len(pair)\n"
    "    if total:\n"
    "        return '你好，世界：（一）'  # 注释，这里：（二）\n"
)


def _typed_sample(language: str, english: str, family: str) -> tuple[str, str]:
    forward, _ = _translators(language, "token")
    native = forward.translate_code(english, "en", language)
    typed, count = typed_in_code(native, FAMILIES[family])
    assert count
    return native, typed


@pytest.mark.parametrize("backend", BACKENDS)
def test_arabic_comma_and_semicolon_translate_and_compile(backend: str) -> None:
    _, typed = _typed_sample("ar", ARABIC_ENGLISH, "arabic")
    assert "\u060c " in typed.splitlines()[0] and "\u061b " in typed.splitlines()[1]
    _, reverse = _translators("ar", backend)
    back = reverse.translate_code(typed, "ar", "en")
    assert back == ARABIC_ENGLISH
    compile(back, "<arabic>", "exec")


@pytest.mark.parametrize("backend", BACKENDS)
def test_fullwidth_marks_translate_and_compile(backend: str) -> None:
    _, typed = _typed_sample("zh", CHINESE_ENGLISH, "fullwidth")
    first = typed.splitlines()[0]
    assert "\uff08" in first and first.endswith("\uff09\uff1a")
    _, reverse = _translators("zh", backend)
    back = reverse.translate_code(typed, "zh", "en")
    assert back == CHINESE_ENGLISH
    compile(back, "<chinese>", "exec")


@pytest.mark.parametrize("backend", BACKENDS)
def test_native_and_ascii_marks_mix_in_one_program(backend: str) -> None:
    native, typed = _typed_sample("ar", ARABIC_ENGLISH, "arabic")
    lines, typed_lines = native.splitlines(True), typed.splitlines(True)
    mixed = typed_lines[0] + "".join(lines[1:])
    assert mixed not in (native, typed)
    _, reverse = _translators("ar", backend)
    assert reverse.translate_code(mixed, "ar", "en") == ARABIC_ENGLISH


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize(
    ("language", "english"),
    [
        pytest.param("ar", ARABIC_ENGLISH, id="ar"),
        pytest.param("zh", CHINESE_ENGLISH, id="zh"),
    ],
)
def test_the_engine_never_writes_a_native_mark(
    backend: str, language: str, english: str
) -> None:
    """Display keeps ASCII punctuation; only the prose carries native marks."""
    forward, _ = _translators(language, backend)
    native = forward.translate_code(english, "en", language)
    code_only = native
    for text in prose(native):
        code_only = code_only.replace(text, "")
    assert not set(code_only) & set(NATIVE_PUNCTUATION)


# -- the fold itself -----------------------------------------------------------------


class TestFold:
    def test_source_without_a_mark_is_returned_as_is(self) -> None:
        source = "def f(a, b):\n    return a; b\n"
        assert fold_code_punctuation(source) is source

    def test_length_never_changes(self) -> None:
        source = "x = f\uff08a\u060c b\uff09\u061b y = '\u060c'  # \uff1a\n"
        folded = fold_code_punctuation(source)
        assert folded == "x = f(a, b); y = '\u060c'  # \uff1a\n"
        assert len(folded) == len(source)

    def test_folding_twice_changes_nothing_more(self) -> None:
        source = "x = \uff08a\uff0c b\uff09\n"
        once = fold_code_punctuation(source)
        assert fold_code_punctuation(once) == once

    @pytest.mark.parametrize(
        ("typed", "expected"),
        [
            (
                "if \uff08n \uff1a= 3\uff09\uff1a\n    pass\n",
                "if (n := 3):\n    pass\n",
            ),
            (
                "def f\uff08a\uff1a int\uff09 -> int\uff1a\n    return a\n",
                "def f(a: int) -> int:\n    return a\n",
            ),
            ("d = {1\uff1a 2}\uff1b s = d[1\uff1a]\n", "d = {1: 2}; s = d[1:]\n"),
            ("g = lambda a\u060c b\uff1a a\n", "g = lambda a, b: a\n"),
            (
                "x = f\uff08\n    1\uff0c\n    2\uff0c\n\uff09\n",
                "x = f(\n    1,\n    2,\n)\n",
            ),
        ],
    )
    def test_marks_in_code_position(self, typed: str, expected: str) -> None:
        assert fold_code_punctuation(typed) == expected
        compile(expected, "<fold>", "exec")

    @pytest.mark.parametrize(
        "source",
        [
            "s = '\u0623\u064e\u060c \u0628\u064f\u061b'\n",
            's = """\uff08\u4e00\uff09\uff0c\n\uff08\u4e8c\uff09\uff1a"""\n',
            "# \u062a\u064e\u0639\u0652\u0644\u0650\u064a\u0642\u060c \uff08\u6ce8\uff09\n",
            "s = r'\\\uff08' + b'x'.decode()\n",
            "s = f'\u0623\u060c {1}\uff1b'\n",
        ],
    )
    def test_marks_in_prose_are_left_alone(self, source: str) -> None:
        assert fold_code_punctuation(source) is source

    @pytest.mark.parametrize(
        "mark",
        [
            "\u061f",  # ARABIC QUESTION MARK
            "\u066b",  # ARABIC DECIMAL SEPARATOR
            "\u066c",  # ARABIC THOUSANDS SEPARATOR
            "\u3001",  # IDEOGRAPHIC COMMA
            "\u3002",  # IDEOGRAPHIC FULL STOP
            "\uff0e",  # FULLWIDTH FULL STOP
            "\uff1d",  # FULLWIDTH EQUALS SIGN
            "\u201c",  # LEFT DOUBLE QUOTATION MARK
        ],
    )
    def test_a_mark_outside_the_table_is_left_alone(self, mark: str) -> None:
        source = f"x = f(a{mark} b)\n"
        assert fold_code_punctuation(source) is source

    def test_text_that_cannot_be_tokenized_is_returned_as_is(self) -> None:
        source = "x = f\uff08a\uff0c '''never closed\n"
        assert fold_code_punctuation(source) is source

    @pytest.mark.skipif(
        sys.version_info < (3, 12),
        reason="before CPython 3.12 an f-string is one string token, all prose",
    )
    def test_f_string_fields_are_code_and_their_text_is_prose(self) -> None:
        typed = "s = f'{a\uff0c b}\uff0c {c\uff1a>4}\uff1a {d\uff1a\uff1a>4}'\n"
        assert (
            fold_code_punctuation(typed)
            == "s = f'{a, b}\uff0c {c:>4}\uff1a {d:\uff1a>4}'\n"
        )

    @pytest.mark.skipif(
        sys.version_info >= (3, 12),
        reason="from CPython 3.12 the fields of an f-string are tokens",
    )
    def test_an_f_string_is_all_prose_before_3_12(self) -> None:
        source = "s = f'{a\uff0c b}\uff0c {c\uff1a>4}'\n"
        assert fold_code_punctuation(source) is source


# -- what is stored, and what the round-trip check says ----------------------------


def test_the_clean_filter_stores_the_file_as_typed() -> None:
    _, typed = _typed_sample("ar", ARABIC_ENGLISH, "arabic")
    assert GitFilter("ar").clean_text(typed) == typed


class TestRoundTripReport:
    @staticmethod
    def _translate(source, source_lang, target_lang, python_version):
        language = target_lang if source_lang == "en" else source_lang
        forward, reverse = _translators(language, "token")
        translator = forward if source_lang == "en" else reverse
        return translator.translate_code(source, source_lang, target_lang), False

    @staticmethod
    def _compiles(source: str) -> bool:
        try:
            compile(source, "<forward>", "exec")
        except SyntaxError:
            return False
        return True

    def _report(self, language: str, source: str):
        pack = LanguagePackLoader().load(
            language, target="python", version=RUNNING_VERSION
        )
        return verify_round_trip(
            source,
            language,
            "en",
            RUNNING_VERSION,
            translate=self._translate,
            pack=pack,
            validate=self._compiles,
        )

    @pytest.mark.parametrize(
        ("language", "english", "family", "lines"),
        [
            pytest.param("ar", ARABIC_ENGLISH, "arabic", 2, id="ar"),
            pytest.param("zh", CHINESE_ENGLISH, "fullwidth", 3, id="zh"),
        ],
    )
    def test_native_marks_run_but_do_not_come_back(
        self, language: str, english: str, family: str, lines: int
    ) -> None:
        native, typed = _typed_sample(language, english, family)
        report = self._report(language, typed)
        assert report.forward == english
        assert report.forward_valid is True
        assert report.returned == native
        assert report.round_trips is False
        assert report.divergence_count == lines
        assert {d.layer for d in report.divergences} == {Layer.PUNCTUATION}
        assert "layer punctuation" in report.verdict_line

    def test_the_same_program_with_ascii_marks_still_verifies(self) -> None:
        native, _ = _typed_sample("ar", ARABIC_ENGLISH, "arabic")
        report = self._report("ar", native)
        assert report.round_trips is True
        assert "VERIFIED" in report.verdict_line

    def test_a_line_with_a_second_difference_is_not_blamed_on_punctuation(
        self,
    ) -> None:
        """Punctuation is named only when it is the whole difference.

        Otherwise the layers outside the reported set would be credited as
        clean while one of them sits behind the comma.
        """
        pack = LanguagePackLoader().load("es", target="python", version=RUNNING_VERSION)
        rendering = pack.builtins["print"]

        def lossy(source, source_lang, target_lang, python_version):
            if target_lang == "es":
                return f"x = [{rendering}X, 1]\n", False
            return source, False

        report = verify_round_trip(
            f"x = [{rendering}\u060c 1]\n",
            "es",
            "en",
            RUNNING_VERSION,
            translate=lossy,
            pack=pack,
        )
        assert [d.layer for d in report.divergences] == [Layer.BUILTINS]
