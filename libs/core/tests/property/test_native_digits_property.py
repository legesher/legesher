"""Property: a numeric literal written in native digits reads as its ASCII form.

Hypothesis draws an ASCII literal (integer, grouped integer, decimal,
exponent, imaginary) and a language from the registry, writes the literal in
that language's digits (with either decimal mark, where the language has its
own), and checks that ``fold_code_digits``:

1. reads the literal back to exactly the ASCII spelling, digit for digit;
2. leaves the same digits untouched in a string and in a comment on the line;
3. gives a literal Python evaluates to the value of the ASCII one.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from legesher_core.native_digits import fold_code_digits
from legesher_i18n.language_registry import (
    get_active_language_codes,
    get_decimal_separator,
    get_native_digits,
)

NATIVE = sorted(code for code in get_active_language_codes() if get_native_digits(code))

_digits = st.text(alphabet="0123456789", min_size=1, max_size=6)
_whole = st.integers(min_value=0, max_value=10**15)
_mantissa = st.builds(lambda a, b: f"{a}.{b}", _whole, _digits)

LITERALS = st.one_of(
    _whole.map(str),
    _whole.map(lambda n: f"{n:_}"),
    _mantissa,
    st.builds(
        lambda m, sign, e: f"{m}e{sign}{e}",
        _mantissa,
        st.sampled_from(["", "+", "-"]),
        st.integers(min_value=0, max_value=300),
    ),
    st.builds(lambda m: f"{m}j", st.one_of(_whole.map(str), _mantissa)),
)


@settings(max_examples=200, deadline=None, print_blob=True)
@given(
    literal=LITERALS,
    language=st.sampled_from(NATIVE),
    own_mark=st.booleans(),
)
def test_native_literal_reads_as_ascii(
    literal: str, language: str, own_mark: bool
) -> None:
    digits = get_native_digits(language)
    assert digits is not None
    mark = get_decimal_separator(language) if own_mark else "."
    written = literal.translate(str.maketrans("0123456789", digits)).replace(".", mark)

    source = f'x = {written}  # {written}\ns = "{written}"\n'
    read = fold_code_digits(source, language)

    assert read == f'x = {literal}  # {written}\ns = "{written}"\n'
    assert eval(read.split("\n", 1)[0][4:].split("  #")[0]) == eval(literal)  # noqa: S307
