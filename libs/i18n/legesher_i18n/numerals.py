"""Numeral systems: which digits a language writes, derived from one identifier.

The language registry records two facts per language, both generated from the
``languages`` table of ``translations.db`` into ``languages.json``:

- ``numeral_system``: the CLDR numbering-system identifier of the digits the
  language writes natively, CLDR's ``native`` system for the locale (``arab``
  for Arabic, ``deva`` for Hindi, ``latn`` for ASCII ``0``-``9``).
- ``decimal_separator``: the decimal mark written with those digits (U+066B
  ``٫`` with Arabic-Indic digits). No rule computes it from the digits, so it
  is stored.

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
    "LATIN",
    "NUMERAL_SYSTEM_ZEROS",
    "is_known_numeral_system",
    "numeral_system_digits",
]

#: The identifier of ASCII ``0``-``9``.
LATIN: Final = "latn"

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
