"""Numeral systems: which digits a language writes, derived from one identifier.

The language registry records two facts per language, both generated from the
``languages`` table of ``translations.db`` into ``languages.json``:

- ``numeral_system``: the CLDR numbering-system identifier of the digits the
  language writes natively: CLDR's ``native`` system for the locale when that
  is a Unicode decimal-digit block (``arab`` for Arabic, ``deva`` for Hindi),
  and ``latn`` (ASCII ``0``-``9``) otherwise, which includes Chinese, whose
  CLDR native system ``hanidec`` (``〇一二三``) is not one.
- ``decimal_separator``: the decimal mark written with those digits, CLDR's
  decimal symbol for the locale's native system (U+066B ``٫`` with
  Arabic-Indic and Extended Arabic-Indic digits). A language that writes
  ASCII digits records ``.``, the mark a numeric literal in code uses,
  whatever its prose convention (German writes ``3,5`` in text, ``3.5`` in
  code). It is stored per language, like every registry fact, and checked
  against the mark CLDR writes with the system in every locale that uses it
  (:func:`decimal_separator_for`). Khmer is the one CLDR system whose mark is
  a comma; a comma is a tuple in code, so it has no entry here.

Every decimal numbering system Unicode encodes is a block of ten consecutive
code points with the zero first, and ``unicodedata.digit`` already reads each
of them. So this module stores one code point per system, its zero, and
computes the ten digits from it. A stored digit string would be a hand-typed
copy of the Unicode character database.

Reading a native digit needs nothing from here: ``int("١٢٣") == 123`` for every
Unicode decimal digit. What a consumer needs is the other direction (which
digits does this language write?) and the identity of the block (is this
character one of the language's own digits?).

A language whose native numerals are not a decimal-digit block (Chinese
``一二三``, Japanese, Amharic ``፩፪፫``) records ``latn``: the digits its programs
are written with. Those numerals are a different problem from digit
substitution and are not modelled here.

The table holds the systems the registry names. A language that needs another
system adds its identifier and zero here, and the test that checks every zero
against the Unicode character database covers it.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

__all__ = [
    "DECIMAL_SEPARATORS",
    "LATIN",
    "NUMERAL_SYSTEM_ZEROS",
    "decimal_separator_for",
    "is_known_numeral_system",
    "numeral_system_digits",
]

#: The identifier of ASCII ``0``-``9``.
LATIN: Final = "latn"

#: The decimal marks a language may record: the ASCII full stop, and U+066B
#: ARABIC DECIMAL SEPARATOR. Not the comma (a tuple in code) and not U+066C,
#: the Arabic thousands separator that looks like U+066B.
DECIMAL_SEPARATORS: Final[frozenset[str]] = frozenset({".", "\u066b"})

#: CLDR numbering-system identifier to the code point of its digit zero.
NUMERAL_SYSTEM_ZEROS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "latn": 0x0030,  # DIGIT ZERO
        "arab": 0x0660,  # ARABIC-INDIC DIGIT ZERO
        "arabext": 0x06F0,  # EXTENDED ARABIC-INDIC DIGIT ZERO (Persian, Urdu)
        "beng": 0x09E6,  # BENGALI DIGIT ZERO
        "deva": 0x0966,  # DEVANAGARI DIGIT ZERO
        "gujr": 0x0AE6,  # GUJARATI DIGIT ZERO
        "knda": 0x0CE6,  # KANNADA DIGIT ZERO
        "mlym": 0x0D66,  # MALAYALAM DIGIT ZERO
        "mymr": 0x1040,  # MYANMAR DIGIT ZERO
        "telu": 0x0C66,  # TELUGU DIGIT ZERO
        "thai": 0x0E50,  # THAI DIGIT ZERO
    }
)


#: Systems CLDR writes with U+066B in every locale; every other system here
#: is written with ".".
_ARABIC_DECIMAL = frozenset({"arab", "arabext"})


def decimal_separator_for(system: str) -> str:
    """The decimal mark CLDR writes with ``system`` (U+066B or ``.``).

    Raises:
        ValueError: If ``system`` is not a known identifier.
    """
    if not is_known_numeral_system(system):
        raise ValueError(f"unknown numeral system {system!r}")
    return "\u066b" if system in _ARABIC_DECIMAL else "."


def is_known_numeral_system(system: str) -> bool:
    """Whether ``system`` is a numbering-system identifier this module knows."""
    return system in NUMERAL_SYSTEM_ZEROS


def numeral_system_digits(system: str) -> str:
    """The ten digits of ``system``, zero first.

    Raises:
        ValueError: If ``system`` is not a known identifier. An unknown value
            is a data error, so it fails instead of reading as ASCII.

    Example:
        >>> numeral_system_digits("arab")
        '٠١٢٣٤٥٦٧٨٩'
    """
    try:
        zero = NUMERAL_SYSTEM_ZEROS[system]
    except KeyError:
        raise ValueError(
            f"unknown numeral system {system!r}; known: "
            f"{', '.join(sorted(NUMERAL_SYSTEM_ZEROS))}"
        ) from None
    return "".join(chr(zero + d) for d in range(10))
