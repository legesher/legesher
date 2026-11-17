"""Native punctuation in code position, read as the mark the author meant.

An Arabic, Persian or Urdu keyboard layout puts ``،`` and ``؛`` on the comma
and semicolon keys. A Chinese, Japanese or Korean input method in fullwidth
mode types ``，`` ``；`` ``：`` ``（`` ``）``. Python accepts none of them outside
a string or a comment, so a program typed the natural way does not compile.
Both translator backends therefore read their input through
:func:`fold_code_punctuation`.

The contract:

- **Input side only.** A mark in :data:`NATIVE_PUNCTUATION` that stands in
  code position is read as its ASCII equivalent. The engine never writes a
  native mark: a translation for display, and the return leg of a round
  trip, carry ASCII punctuation. Source that uses a native mark in code
  position therefore runs, and does not come back byte-identical;
  ``round_trip`` reports that as ``Layer.PUNCTUATION``.
- **Code position only.** A mark inside a string, a comment or the text of
  an f-string is the author's prose and is returned byte for byte.
- **Offsets never move.** One character is replaced by one character, so
  every line and column of the result indexes the original text.
- **The stored file is not touched.** This runs when the engine reads
  source. The git clean filter does not call it, so git stores what the
  author typed.

How code position is found. The whole text is folded first, one character
for one, and that folded text is tokenized. A fold is then kept only where
the tokenizer reports an operator token; everywhere else the original
character stays. No target of the table can open or close a string or a
comment, so folding inside prose cannot change where prose ends, and the
tokenizer's own answer is used instead of a second, hand-written reading of
Python's string syntax. Text the tokenizer cannot read is returned as it
was given.

From CPython 3.12 the replacement fields of an f-string are tokens, so a
mark inside ``{...}`` is in code position there. On 3.10 and 3.11 an
f-string is a single string token and all of it is prose.

The table is one table for every language. None of its marks is valid in
Python code, so reading them cannot change the meaning of a program that
already compiles. It is deliberately short: each fullwidth mark is one that
Unicode itself equates with its ASCII form (NFKC), and the two Arabic marks
are the ones the keyboard layouts put on the comma and semicolon keys. A
mark that only resembles an operator (``؟``, ``、``, ``。``, curly quotes) is
not read as one.
"""

from __future__ import annotations

import io
import re
import tokenize
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from .stored_form import tokenizer_view

__all__ = ["NATIVE_PUNCTUATION", "fold_code_punctuation"]

#: Native mark to the ASCII mark it is read as, in code position only.
NATIVE_PUNCTUATION: Final[Mapping[str, str]] = MappingProxyType(
    {
        "\u060c": ",",  # ARABIC COMMA
        "\u061b": ";",  # ARABIC SEMICOLON
        "\uff0c": ",",  # FULLWIDTH COMMA
        "\uff1b": ";",  # FULLWIDTH SEMICOLON
        "\uff1a": ":",  # FULLWIDTH COLON
        "\uff08": "(",  # FULLWIDTH LEFT PARENTHESIS
        "\uff09": ")",  # FULLWIDTH RIGHT PARENTHESIS
    }
)

_FOLD = str.maketrans(dict(NATIVE_PUNCTUATION))
_ANY_MARK = re.compile("[" + "".join(NATIVE_PUNCTUATION) + "]")

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


def fold_code_punctuation(source: str) -> str:
    """Return ``source`` with native punctuation in code position as ASCII.

    The result has the same length as ``source``. Strings, comments and
    f-string text are returned byte for byte. ``source`` itself is returned
    when it holds no mark from :data:`NATIVE_PUNCTUATION`, when none of its
    marks is in code position, or when it cannot be tokenized.
    """
    if _ANY_MARK.search(source) is None:
        return source

    # A lone CR is a line break to Python but not to tokenize over StringIO;
    # the view replaces it one for one, so offsets hold for ``source``.
    folded = tokenizer_view(source).translate(_FOLD)
    line_starts = [0]
    index = folded.find("\n")
    while index != -1:
        line_starts.append(index + 1)
        index = folded.find("\n", index + 1)

    kept: list[int] = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(folded).readline):
            if token.type != tokenize.OP:
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
            kept.extend(
                offset
                for offset in range(start, end)
                if source[offset] in NATIVE_PUNCTUATION
            )
    except _TOKENIZE_FAILURES:
        return source

    if not kept:
        return source
    chars = list(source)
    for offset in kept:
        chars[offset] = NATIVE_PUNCTUATION[chars[offset]]
    return "".join(chars)
