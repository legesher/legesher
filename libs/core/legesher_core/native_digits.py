"""Numeric literals typed in a language's own digits, read as ASCII.

Python reads every Unicode decimal digit as a value (``int("١٢٣") == 123``),
but a numeric literal in source must be ASCII: ``x = ١٢٣`` is
``SyntaxError: invalid character '١' (U+0661)``. A person writing Arabic,
Hindi or Thai types numbers in the digits their keyboard gives them, so both
translator backends read their input through :func:`fold_code_digits`.

The contract:

- **Input side only.** A numeric literal written in the source language's
  native digits is read as the same literal in ASCII digits. The engine never
  writes native digits: a translation for display, and the return leg of a
  round trip, carry ASCII digits. Source with a native-digit literal therefore
  runs, and does not come back byte-identical; ``round_trip`` reports that as
  ``Layer.DIGITS``.
- **The language's own digits only.** Which digits are read comes from the
  language registry (``legesher_i18n.language_registry.get_native_digits``):
  Arabic-Indic for Arabic, Extended Arabic-Indic for Persian and Urdu,
  Devanagari for Hindi and Nepali, and so on. A language that writes ASCII
  digits reads nothing.
- **One literal at a time.** A literal is read when every digit in it is the
  language's own, so ``x = ١٢٣ + 456`` runs. A literal that mixes those digits
  with ASCII ones (``١2٣``) or with another script's, a literal followed
  directly by a letter or digit the tokenizer does not take into it, and a
  prefixed literal (``0x``, ``0b``, ``0o``: hexadecimal letters have no native
  form) are left as typed, so Python reports them as it always has. In a
  language whose decimal separator is not ``.`` (U+066B ``٫`` for Arabic,
  Persian and Urdu), that separator and ``.`` both read as the decimal point
  inside a native-digit literal.
- **Code position only.** Digits inside a string, a comment, the text of an
  f-string or an identifier (``var٣``) are returned byte for byte.
  Identifiers keep ASCII digits by policy, and the style-guide validator still
  warns on a native digit in one.
- **Offsets never move.** One character is replaced by one, so every line and
  column of the result indexes the original text, and an error position needs
  no mapping.
- **The stored file is not touched.** The git clean filter does not call this,
  so git stores what the author typed.

How code position is found. The whole text is folded first, one character for
one, and the folded text is tokenized. A fold is then kept only inside a
number token whose original spelling passes the rules above; everywhere else
the original character stays. A digit cannot open or close a string or a
comment, so folding inside prose cannot change where prose ends.

Folding stops where the tokenizer stops. Code being typed is often incomplete,
and the tokenizer reads such text up to the point it cannot read past; the
literals before that point are read and the rest is returned as given. The
spelling is kept digit for digit, leading zeros included (``٠٫٥`` reads as
``0.5``, ``٠٠`` as ``00``). A literal Python rejects in ASCII is still
rejected: ``٠١٢٣`` reads as ``0123`` from CPython 3.12, and is left as typed
on 3.10 and 3.11, whose tokenizer splits it in two. On CPython 3.10 and 3.11 the
tokenizer reads past an unterminated single-quoted string by lexing the
string's text as code, so folding also stops at the quote that opens it. From
CPython 3.12 the replacement fields of an f-string are tokens, so a literal
inside ``{...}`` is read there; on 3.10 and 3.11 an f-string is a single
string token and all of it is prose. A self-documenting field reads the
same way: ``f"{١٢=}"`` prints ``12=12``.

The language server keeps its own reading of the file for editor
diagnostics and does not call this yet, so the editor still marks a
native-digit literal as an error that ``legesher run`` does not raise.
"""

from __future__ import annotations

import io
import tokenize
from functools import lru_cache

from legesher_i18n.language_registry import get_decimal_separator, get_native_digits
from legesher_i18n.numerals import DECIMAL_SEPARATORS

from .native_punctuation import fold_code_punctuation
from .stored_form import tokenizer_view
from .utils import continues_identifier

__all__ = ["fold_code_digits", "read_native_code"]

_PREFIXES = ("0x", "0b", "0o")
_QUOTES = frozenset("'\"")

#: Tokenization failures are results, not exceptions (the catch list
#: ``round_trip`` uses): ValueError covers a lone surrogate, RecursionError
#: and MemoryError pathological nesting.
_TOKENIZE_FAILURES = (
    tokenize.TokenError,
    IndentationError,
    SyntaxError,
    ValueError,
    RecursionError,
    MemoryError,
)


@lru_cache(maxsize=None)
def _reading(language: str) -> tuple[frozenset[str], dict[int, str]] | None:
    """The language's native digits and the table that folds them, or None."""
    digits = get_native_digits(language)
    if digits is None:
        return None
    table = {ord(digit): str(value) for value, digit in enumerate(digits)}
    separator = get_decimal_separator(language)
    # Only a mark the registry allows: a comma read as the point would turn
    # ``f(١,٢)`` into ``f(1.2)``.
    if separator != "." and separator in DECIMAL_SEPARATORS:
        table[ord(separator)] = "."
    return frozenset(digits), table


def _is_native_literal(original: str, ascii_form: str, digits: frozenset[str]) -> bool:
    """Whether a number token's original spelling is read as ``ascii_form``."""
    if ascii_form[:2].lower() in _PREFIXES:
        return False
    # Every digit the author typed is one of the language's own: no ASCII
    # digit and no other script's digit beside them.
    return all(char in digits for char in original if char.isdecimal())


def _glued(source: str, index: int) -> bool:
    """Whether ``source[index]`` joins the token beside it into one word.

    By Python's identifier rules, not the tokenizer's: on CPython 3.10 and
    3.11 the tokenizer splits ``संख्या१`` at the vowel sign and reports the
    trailing digit as a number, but the digit belongs to the identifier.
    """
    if not 0 <= index < len(source):
        return False
    return continues_identifier(source[index])


def fold_code_digits(source: str, language: str | None) -> str:
    """Return ``source`` with ``language``'s native-digit literals in ASCII.

    The result has the same length as ``source``. Strings, comments,
    f-string text and identifiers are returned byte for byte, and so is
    everything from the first point the tokenizer cannot read past.
    ``source`` itself is returned when ``language`` writes ASCII digits, when
    the text holds none of its native digits, or when none of them stands in
    a literal this module reads.
    """
    reading = _reading(language) if language else None
    if reading is None:
        return source
    digits, table = reading
    if digits.isdisjoint(source):
        return source

    # A lone CR is a line break to Python but not to tokenize over StringIO;
    # the view replaces it one for one, so offsets hold for ``source``.
    folded = tokenizer_view(source).translate(table)
    line_starts = [0]
    index = folded.find("\n")
    while index != -1:
        line_starts.append(index + 1)
        index = folded.find("\n", index + 1)

    kept: list[tuple[int, int]] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(folded).readline):
            if token.type == tokenize.ERRORTOKEN and _QUOTES & set(token.string):
                # CPython 3.10 and 3.11: an unterminated string. What follows
                # on the line is its text, which this tokenizer goes on to
                # lex as code; 3.12 and later raise here instead.
                break
            if token.type != tokenize.NUMBER:
                continue
            (start_row, start_col), (end_row, end_col) = token.start, token.end
            if not 0 < start_row <= end_row <= len(line_starts):
                return source
            start = line_starts[start_row - 1] + start_col
            end = line_starts[end_row - 1] + end_col
            if folded[start:end] != token.string:
                # The reported position does not land on the token's own
                # spelling, so there is no offset it is safe to rewrite at.
                return source
            original = source[start:end]
            if original == token.string:
                continue
            if _glued(source, start - 1) or _glued(source, end):
                # The number is part of a longer word: the tail of an
                # identifier the 3.10 and 3.11 tokenizer split at a mark
                # (``संख्या१``, ``قيمةً٣``), or a literal running into a name
                # or another script's digit (``١٢abc``, ``١٢२``, and
                # ``٠١٢٣``, which that tokenizer splits in two).
                continue
            if _is_native_literal(original, token.string, digits):
                kept.append((start, end))
    except _TOKENIZE_FAILURES:
        # Every token before the failure was read; the literals found there
        # stand, and the rest of the text is returned as given.
        pass

    if not kept:
        return source
    chars = list(source)
    for start, end in kept:
        chars[start:end] = folded[start:end]
    return "".join(chars)


def read_native_code(source: str, language: str | None) -> str:
    """``source`` as the engine reads it: native marks, then native digits.

    The one place the order of the two folds is decided; both translator
    backends and the round-trip check read through this. Punctuation comes
    first because the digit fold tokenizes: from CPython 3.12 the tokenizer
    reads a native mark as the start of a name and takes the digit after it
    into that name, so ``f(١،٢)`` read digits first would leave ``٢`` as
    typed. One character for one either way, so no offset moves.
    """
    return fold_code_digits(fold_code_punctuation(source), language)
