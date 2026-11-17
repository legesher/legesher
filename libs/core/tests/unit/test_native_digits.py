"""Numeric literals typed in a language's own digits (``native_digits``).

The languages come from the registry: every language whose
``numeral_system`` is a decimal-digit block other than ASCII. The literal
forms come from one fixture, ``tests/fixtures/native_digits/literals.py``,
an English program whose prose carries digits from six scripts and whose
identifiers include vocalised Arabic, pointed Hebrew, Devanagari, Thai and
CJK. Each language's native file is built from it: translated by the pack,
then every decimal literal written in the language's digits.
"""

from __future__ import annotations

import io
import sys
import tokenize
from pathlib import Path

import pytest

from legesher_core.native_digits import fold_code_digits, read_native_code
from legesher_core.round_trip import FOLD_LAYERS, Layer, verify_round_trip
from legesher_core.transformer import TokenTranslator
from legesher_core.tree_sitter.translator import TreeSitterTranslator
from legesher_i18n import LanguagePackLoader
from legesher_i18n.language_registry import (
    get_active_language_codes,
    get_decimal_separator,
    get_native_digits,
)
from tests.interpreter_gaps import (
    skip_if_return_hop_is_inert,
    xfail_if_return_hop_is_inert,
)

FIXTURE = Path(__file__).parent.parent / "fixtures" / "native_digits" / "literals.py"
ENGLISH = FIXTURE.read_text(encoding="utf-8")

#: Every published language that writes a native digit block, from the registry.
NATIVE = [code for code in get_active_language_codes() if get_native_digits(code)]
#: Those whose decimal separator is not the ASCII full stop.
OWN_SEPARATOR = [code for code in NATIVE if get_decimal_separator(code) != "."]
#: Published languages that write ASCII digits.
LATIN = [code for code in get_active_language_codes() if not get_native_digits(code)]

BACKENDS = [TokenTranslator, TreeSitterTranslator]
_PREFIXED = ("0x", "0b", "0o")
#: The byte-identity test that pins the token backend's 3.10/3.11 gap.
_PIN = "test_native_file_reads_back_to_the_english_bytes[TokenTranslator]"


def native(language: str, text: str) -> str:
    """``text`` with ``language``'s digits written for ASCII ones."""
    digits = get_native_digits(language)
    assert digits is not None
    return text.translate(str.maketrans("0123456789", digits))


def write_literals(source: str, language: str) -> str:
    """Write every decimal literal in ``source`` in ``language``'s digits.

    ``source`` is valid ASCII-digit Python, so its number tokens are exact.
    The decimal point becomes the language's separator; prefixed literals
    stay ASCII, as a person writing them would leave them.
    """
    separator = get_decimal_separator(language)
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    chars = list(source)
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.NUMBER or token.string[:2].lower() in _PREFIXED:
            continue
        start = starts[token.start[0] - 1] + token.start[1]
        written = native(language, token.string).replace(".", separator)
        chars[start : start + len(written)] = written
    return "".join(chars)


def native_file(language: str) -> tuple[str, str]:
    """The fixture in ``language`` with ASCII literals, and with native ones."""
    ascii_digits = TokenTranslator.from_language_pack(language).translate_code(ENGLISH)
    return ascii_digits, write_literals(ascii_digits, language)


def test_registry_names_native_languages() -> None:
    # The parametrization below is only as good as this set.
    assert {"ar", "fa", "ur", "hi", "bn", "th", "my"} <= set(NATIVE)
    assert set(OWN_SEPARATOR) == {"ar", "fa", "ur"}


class TestWholeFile:
    @pytest.mark.parametrize("language", NATIVE)
    def test_fixture_reaches_every_literal_form(self, language: str) -> None:
        ascii_digits, typed = native_file(language)
        digits = set(get_native_digits(language) or "")
        # Prose already holds the language's digits; literals add many more.
        assert (
            sum(c in digits for c in typed)
            > sum(c in digits for c in ascii_digits) + 50
        )
        assert "0x1F" in typed and "0b101" in typed and "0o17" in typed

    @pytest.mark.parametrize("backend", BACKENDS, ids=lambda b: b.__name__)
    @pytest.mark.parametrize("language", NATIVE)
    def test_native_file_reads_back_to_the_english_bytes(
        self, language: str, backend: type, request: pytest.FixtureRequest
    ) -> None:
        ascii_digits, typed = native_file(language)
        if backend is TokenTranslator:
            # The token backend's return hop cannot read a pack rendering
            # with vowel signs on CPython 3.10 and 3.11, digits or none.
            xfail_if_return_hop_is_inert(request, ENGLISH, ascii_digits)
        english = backend.from_language_pack(language).reverse().translate_code(typed)
        # Keywords, builtins and every literal come back; prose, identifiers
        # and prefixed literals were never touched.
        assert english == ENGLISH

    @pytest.mark.parametrize("backend", BACKENDS, ids=lambda b: b.__name__)
    @pytest.mark.parametrize("language", NATIVE)
    def test_english_form_runs_to_the_same_values(
        self, language: str, backend: type
    ) -> None:
        ascii_digits, typed = native_file(language)
        if backend is TokenTranslator:
            skip_if_return_hop_is_inert(ENGLISH, ascii_digits, pinned_by=_PIN)
        english = backend.from_language_pack(language).reverse().translate_code(typed)
        ran: dict = {}
        exec(compile(english, f"<{language}>", "exec"), ran)  # noqa: S102
        expected: dict = {}
        exec(compile(ENGLISH, "<en>", "exec"), expected)  # noqa: S102
        assert ran["RESULT"] == expected["RESULT"]

    @pytest.mark.parametrize("backend", BACKENDS, ids=lambda b: b.__name__)
    @pytest.mark.parametrize("language", NATIVE)
    def test_without_the_source_language_nothing_is_read(
        self, language: str, backend: type
    ) -> None:
        # A translator that does not know its source language (built from
        # maps, not a pack) reads ASCII digits only: the literals stay native
        # and Python rejects them, as it did before.
        reverse = backend.from_language_pack(language).reverse()
        blind = backend(
            reverse.mapper.keyword_map,
            reverse.mapper.builtin_map,
            reverse.python_version,
            reverse.mapper.implicit_param_map,
        )
        _, typed = native_file(language)
        english = blind.translate_code(typed)
        assert english != ENGLISH
        with pytest.raises(SyntaxError, match="invalid character"):
            compile(english, f"<{language}>", "exec")

    @pytest.mark.parametrize("backend", BACKENDS, ids=lambda b: b.__name__)
    @pytest.mark.parametrize("language", NATIVE)
    def test_engine_never_writes_native_digits(
        self, language: str, backend: type
    ) -> None:
        # Display (English into the language) keeps the digits as given.
        rendered = backend.from_language_pack(language).translate_code(ENGLISH)
        for line_in, line_out in zip(
            ENGLISH.splitlines(), rendered.splitlines(), strict=True
        ):
            assert [c for c in line_in if c.isdecimal()] == [
                c for c in line_out if c.isdecimal()
            ]


class TestTranslatorLanguages:
    @pytest.mark.parametrize("backend", BACKENDS, ids=lambda b: b.__name__)
    def test_pack_translator_knows_both_languages(self, backend: type) -> None:
        forward = backend.from_language_pack("ar")
        assert (forward.source_language, forward.target_language) == ("en", "ar")
        reverse = forward.reverse()
        assert (reverse.source_language, reverse.target_language) == ("ar", "en")
        assert reverse.reverse().source_language == "en"


def line(text: str) -> str:
    return f"x = {text}\n"


class TestLiteralRules:
    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize(
        "ascii_literal",
        [
            "7",
            "123",
            "1_000",
            "00",
            "0.5",
            "000.125",
            "10.",
            ".25",
            "1e5",
            "1.5e-3",
            "2E10",
            "7j",
            "2.5j",
        ],
    )
    def test_each_form_reads_as_its_ascii_spelling(
        self, language: str, ascii_literal: str
    ) -> None:
        typed = line(native(language, ascii_literal))
        assert fold_code_digits(typed, language) == line(ascii_literal)

    @pytest.mark.parametrize("language", OWN_SEPARATOR)
    def test_both_decimal_marks_read_as_the_point(self, language: str) -> None:
        separator = get_decimal_separator(language)
        typed = line(native(language, "1") + separator + native(language, "5"))
        assert fold_code_digits(typed, language) == line("1.5")
        typed = line(native(language, "1") + "." + native(language, "5"))
        assert fold_code_digits(typed, language) == line("1.5")

    def test_a_comma_separator_is_never_read_as_the_point(self, monkeypatch) -> None:
        # The registry refuses a comma, but the fold must not depend on that:
        # read as the point, a comma would turn two arguments into one float.
        import legesher_core.native_digits as nd

        monkeypatch.setattr(nd, "get_decimal_separator", lambda _code: ",")
        nd._reading.cache_clear()
        try:
            typed = f"f({native('ar', '1')},{native('ar', '2')})\n"
            assert fold_code_digits(typed, "ar") == "f(1,2)\n"
        finally:
            nd._reading.cache_clear()

    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize("prefix", ["0x", "0X", "0b", "0o"])
    def test_prefixed_literal_is_left_as_typed(
        self, language: str, prefix: str
    ) -> None:
        # With an ASCII zero the literal mixes digit systems; with the
        # language's own zero (``٠x١١``) only the prefix rule refuses it.
        for written_prefix in (prefix, native(language, "0") + prefix[1]):
            typed = line(written_prefix + native(language, "11"))
            assert fold_code_digits(typed, language) == typed, written_prefix

    @pytest.mark.parametrize("language", NATIVE)
    def test_ascii_and_native_literals_mix_in_one_line(self, language: str) -> None:
        typed = line(native(language, "123") + " + 456")
        assert fold_code_digits(typed, language) == line("123 + 456")

    @pytest.mark.parametrize("language", NATIVE)
    def test_literal_mixing_ascii_and_native_digits_is_left_as_typed(
        self, language: str
    ) -> None:
        typed = line(native(language, "1") + "2" + native(language, "3"))
        assert fold_code_digits(typed, language) == typed

    @pytest.mark.parametrize("language", NATIVE)
    def test_another_languages_digits_are_left_as_typed(self, language: str) -> None:
        own = set(get_native_digits(language) or "")
        for other in NATIVE:
            if set(get_native_digits(other) or "") == own:
                continue
            typed = line(native(other, "123"))
            assert fold_code_digits(typed, language) == typed, other
            glued = line(native(language, "12") + native(other, "3"))
            assert fold_code_digits(glued, language) == glued, other

    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize("suffix", ["abc", "_", "ب"])
    def test_literal_glued_to_a_name_is_left_as_typed(
        self, language: str, suffix: str
    ) -> None:
        typed = line(native(language, "12") + suffix)
        assert fold_code_digits(typed, language) == typed

    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize(
        "stem",
        [
            "\u0938\u0902\u0916\u094d\u092f\u093e",  # संख्या, ends in a vowel sign
            "\u0642\u064a\u0645\u0629\u064b",  # قيمةً, ends in a haraka
            "\u0e17\u0e35\u0e48",  # ที่, ends in a tone mark
            "\u09b8\u0982\u0996\u09cd\u09af\u09be",  # সংখ্যা
            "\u1000\u102d\u1014\u103a\u1038",  # ကိန်း
            "a\u00b7",  # middle dot, Other_ID_Continue
            "a\u203f",  # undertie, connector punctuation
        ],
    )
    def test_digit_after_a_mark_stays_in_the_identifier(
        self, language: str, stem: str
    ) -> None:
        # On CPython 3.10 and 3.11 the tokenizer splits these names at the
        # mark and reports the trailing digit as a number; it is part of the
        # identifier, which compiles as typed.
        typed = f"{stem}{native(language, '1')} = 5\n"
        compile(typed, "<id>", "exec")
        assert fold_code_digits(typed, language) == typed

    @pytest.mark.parametrize("language", NATIVE)
    def test_identifier_digits_stay(self, language: str) -> None:
        typed = f"var{native(language, '3')} = 1\nمَبْلَغ{native(language, '2')} = 2\n"
        assert fold_code_digits(typed, language) == typed

    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize(
        "template",
        [
            's = "{n}"\n',
            "s = '{n}'\n",
            's = r"\\d {n}"\n',
            's = b"x"  # {n} שָׁלוֹם\n',
            's = """\n{n}\n"""\n',
            "s = 'مَرْحَبًا {n}'\n",
        ],
    )
    def test_prose_keeps_its_digits(self, language: str, template: str) -> None:
        typed = template.format(n=native(language, "123"))
        assert fold_code_digits(typed, language) == typed

    @pytest.mark.parametrize("language", NATIVE)
    def test_fstring_field_follows_the_interpreter(self, language: str) -> None:
        typed = f"s = f'{{{native(language, '12')}}} {native(language, '34')}'\n"
        folded = fold_code_digits(typed, language)
        if sys.version_info >= (3, 12):
            # The replacement field is code; the f-string text is prose.
            assert folded == f"s = f'{{12}} {native(language, '34')}'\n"
        else:
            assert folded == typed

    @pytest.mark.parametrize("language", LATIN)
    def test_ascii_language_reads_nothing(self, language: str) -> None:
        typed = line(native("ar", "123"))
        assert fold_code_digits(typed, language) is typed

    def test_no_language_reads_nothing(self) -> None:
        typed = line(native("ar", "123"))
        assert fold_code_digits(typed, None) is typed

    @pytest.mark.parametrize("language", NATIVE)
    def test_incomplete_code_reads_up_to_where_tokenizing_stops(
        self, language: str
    ) -> None:
        typed = f"x = ({native(language, '12')}\n"
        assert fold_code_digits(typed, language) == "x = (12\n"
        typed = f"x = '{native(language, '1')}\ny = {native(language, '2')}\n"
        assert fold_code_digits(typed, language) == typed

    @pytest.mark.parametrize("language", NATIVE)
    def test_lone_carriage_return_keeps_offsets(self, language: str) -> None:
        typed = f"x = {native(language, '1')}\ry = {native(language, '2')}\n"
        assert fold_code_digits(typed, language) == "x = 1\ry = 2\n"

    @pytest.mark.parametrize("language", NATIVE)
    def test_same_length_always(self, language: str) -> None:
        _, typed = native_file(language)
        assert len(fold_code_digits(typed, language)) == len(typed)


class TestErrorPositions:
    @pytest.mark.parametrize("language", NATIVE)
    def test_syntax_error_column_indexes_the_typed_line(self, language: str) -> None:
        # One character for one: the column Python reports in the read text
        # is the column of the same character in what the person typed.
        typed = f"total = {native(language, '120')} + {native(language, '35')} $ 1\n"
        with pytest.raises(SyntaxError) as raised:
            compile(fold_code_digits(typed, language), "<t>", "exec")
        assert raised.value.offset is not None
        assert typed[raised.value.offset - 1] == "$"


class TestWithNativePunctuation:
    """Both folds on one line: punctuation is read first, then digits."""

    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize("mark", ["\u060c", "\uff0c", "\u061b", "\uff1b"])
    def test_read_native_code_reads_a_mark_glued_to_a_digit(
        self, language: str, mark: str
    ) -> None:
        typed = f"f({native(language, '1')}{mark}{native(language, '2')})\n"
        ascii_mark = "," if mark in "\u060c\uff0c" else ";"
        assert read_native_code(typed, language) == f"f(1{ascii_mark}2)\n"

    @pytest.mark.parametrize("backend", BACKENDS, ids=lambda b: b.__name__)
    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize(
        ("template", "english"),
        [
            ("x = ({a}\u060c {b})\n", "x = (1, 2)\n"),  # Arabic comma
            # Unspaced: from CPython 3.12 the tokenizer reads a mark and the
            # digit after it as one name, so only this order reads both.
            ("x = f({a}\u060c{b})\n", "x = f(1,2)\n"),
            ("x = [{a}\uff0c{b}]\n", "x = [1,2]\n"),  # fullwidth comma
            ("y = {a}\u061b z = {b}\n", "y = 1; z = 2\n"),  # Arabic semicolon
        ],
    )
    def test_marks_and_digits_read_together(
        self, language: str, backend: type, template: str, english: str
    ) -> None:
        typed = template.format(a=native(language, "1"), b=native(language, "2"))
        reverse = backend.from_language_pack(language).reverse()
        assert reverse.translate_code(typed) == english


class TestRoundTrip:
    @staticmethod
    def _translate(source: str, source_lang: str, target_lang: str, version: str):
        if source_lang == "en":
            translator = TokenTranslator.from_language_pack(target_lang, version)
        else:
            translator = TokenTranslator.from_language_pack(
                source_lang, version
            ).reverse()
        return translator.translate_code(source), False

    @staticmethod
    def _translate_tree_sitter(
        source: str, source_lang: str, target_lang: str, version: str
    ):
        if source_lang == "en":
            translator = TreeSitterTranslator.from_language_pack(target_lang, version)
        else:
            translator = TreeSitterTranslator.from_language_pack(
                source_lang, version
            ).reverse()
        return translator.translate_code(source), False

    @staticmethod
    def _compiles(code: str) -> bool:
        try:
            compile(code, "<rt>", "exec")
        except SyntaxError:
            return False
        return True

    def _trip(self, source: str, language: str, *, tree_sitter: bool = False):
        pack = LanguagePackLoader().load(language, target="python", version="3.13")
        return verify_round_trip(
            source,
            language,
            "en",
            "3.13",
            translate=self._translate_tree_sitter if tree_sitter else self._translate,
            pack=pack,
            validate=self._compiles,
        )

    @pytest.mark.parametrize("language", NATIVE)
    def test_tree_sitter_trip_names_digits_on_every_interpreter(
        self, language: str
    ) -> None:
        # The tree-sitter backend reads vowel-sign renderings on 3.10 and 3.11
        # too, so this keeps the classification covered where the token
        # backend's trip is skipped.
        _, typed = native_file(language)
        report = self._trip(typed, language, tree_sitter=True)
        assert report.forward_valid is True
        assert report.divergences
        assert {d.layer for d in report.divergences} == {Layer.DIGITS}

    @pytest.mark.parametrize("language", NATIVE)
    @pytest.mark.parametrize(
        ("template", "layer"),
        [
            # The first differing character decides the name.
            ("x = ({a}\u060c {b})\n", Layer.DIGITS),
            ("x = (y\u060c {a})\n", Layer.PUNCTUATION),
            # Unspaced, where the order of the two folds decides the reading.
            ("x = f({a}\u060c{b})\n", Layer.DIGITS),
            ("x = [{a}\uff0c{b}]\n", Layer.DIGITS),
        ],
    )
    def test_line_with_both_folds_is_named_for_its_first_difference(
        self, language: str, template: str, layer: Layer
    ) -> None:
        typed = template.format(a=native(language, "1"), b=native(language, "2"))
        report = self._trip(typed, language, tree_sitter=True)
        assert [d.layer for d in report.divergences] == [layer]

    @pytest.mark.parametrize("language", NATIVE)
    def test_second_difference_is_reported_at_its_own_column(
        self, language: str
    ) -> None:
        # The literal is read by design; the English builtin after it comes
        # back in the language. The column points at the builtin, the cause
        # the layer names, not at the digit.
        typed = f"x = {native(language, '12')} + len(y)\n"
        report = self._trip(typed, language, tree_sitter=True)
        [divergence] = report.divergences
        assert divergence.layer not in FOLD_LAYERS
        assert divergence.layer is not None
        assert typed[divergence.offset - 1 :].startswith("len")

    @pytest.mark.parametrize("language", NATIVE)
    def test_native_literals_are_named_as_digits(self, language: str) -> None:
        ascii_digits, typed = native_file(language)
        skip_if_return_hop_is_inert(ENGLISH, ascii_digits, pinned_by=_PIN)
        report = self._trip(typed, language)
        assert report.forward_valid is True
        assert not report.round_trips
        assert report.divergences
        assert {d.layer for d in report.divergences} == {Layer.DIGITS}
        assert "layer digits" in report.verdict_line
        assert not report.findings

    @pytest.mark.parametrize("language", NATIVE)
    def test_ascii_literals_still_verify(self, language: str) -> None:
        ascii_digits, _ = native_file(language)
        skip_if_return_hop_is_inert(ENGLISH, ascii_digits, pinned_by=_PIN)
        report = self._trip(ascii_digits, language)
        assert report.round_trips
        assert report.forward_valid is True
        assert report.verdict_line.startswith("legesher: round-trip VERIFIED")
        assert "digits" not in report.verdict_line

    @pytest.mark.parametrize("language", NATIVE)
    def test_a_second_difference_on_the_line_is_not_credited_to_digits(
        self, language: str
    ) -> None:
        # An English builtin typed in a native file comes back in the
        # language, so this line differs by the name as well as the
        # literal. Digits are named only when they are the whole difference.
        typed = f"print({native(language, '12')})\n"
        skip_if_return_hop_is_inert("print(12)\n", typed, pinned_by=_PIN)
        report = self._trip(typed, language)
        assert report.divergences
        layers = {d.layer for d in report.divergences}
        # The line is classified by its other cause, never left unattributed
        # and never credited to digits.
        assert None not in layers
        assert Layer.DIGITS not in layers
