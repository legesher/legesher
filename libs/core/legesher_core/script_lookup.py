"""Dependency-free Unicode script lookup.

The stdlib ``unicodedata`` module does not expose the Unicode ``Script``
property, and the previous engine implementation guessed a character's script
from substrings of its *name* (e.g. ``"ARABIC" in name``). That heuristic is
brittle and cannot see script-spoofing confusables.

This module provides :func:`get_script` backed by a compact range table
covering the scripts Legesher's language packs target plus common confusable
scripts. It returns ``"Common"`` for shared punctuation/digits and
``"Unknown"`` for anything unclassified. If the optional ``regex`` module is
installed, it is used for fuller coverage.

A future PR should consolidate this with the i18n ``script_policy`` helper.
"""

from __future__ import annotations

import bisect

try:  # pragma: no cover - exercised only when regex is installed
    import regex as _regex
except ImportError:  # pragma: no cover
    _regex = None


# (start, end_inclusive, script_name), sorted by start.
_SCRIPT_RANGES: list[tuple[int, int, str]] = [
    (0x0030, 0x0039, "Common"),  # ASCII digits
    (0x0041, 0x005A, "Latin"),
    (0x0061, 0x007A, "Latin"),
    (0x00C0, 0x024F, "Latin"),
    (0x0370, 0x03FF, "Greek"),
    (0x0400, 0x04FF, "Cyrillic"),
    (0x0500, 0x052F, "Cyrillic"),
    (0x0530, 0x058F, "Armenian"),
    (0x0590, 0x05FF, "Hebrew"),
    (0x0600, 0x06FF, "Arabic"),
    (0x0750, 0x077F, "Arabic"),
    (0x0900, 0x097F, "Devanagari"),
    (0x0980, 0x09FF, "Bengali"),
    (0x0A00, 0x0A7F, "Gurmukhi"),
    (0x0A80, 0x0AFF, "Gujarati"),
    (0x0B80, 0x0BFF, "Tamil"),
    (0x0C00, 0x0C7F, "Telugu"),
    (0x0C80, 0x0CFF, "Kannada"),
    (0x0D00, 0x0D7F, "Malayalam"),
    (0x0D80, 0x0DFF, "Sinhala"),
    (0x0E00, 0x0E7F, "Thai"),
    (0x1000, 0x109F, "Myanmar"),
    (0x10A0, 0x10FF, "Georgian"),
    (0x1100, 0x11FF, "Hangul"),
    (0x1800, 0x18AF, "Mongolian"),
    (0x3040, 0x309F, "Hiragana"),
    (0x30A0, 0x30FF, "Katakana"),
    (0x3400, 0x4DBF, "Han"),
    (0x4E00, 0x9FFF, "Han"),
    (0xA840, 0xA87F, "PhagsPa"),
    (0xAC00, 0xD7AF, "Hangul"),
    (0xF900, 0xFAFF, "Han"),
]

_STARTS = [r[0] for r in _SCRIPT_RANGES]


def get_script(char: str) -> str:
    """Return the Unicode script name of ``char``.

    Returns ``"Common"`` for shared characters (ASCII digits) and ``"Unknown"``
    for characters the table does not classify.
    """
    if not char:
        return "Unknown"
    cp = ord(char[0])

    if _regex is not None:  # pragma: no cover - depends on optional dep
        try:
            for name in (
                "Latin",
                "Greek",
                "Cyrillic",
                "Arabic",
                "Hebrew",
                "Han",
                "Hangul",
                "Hiragana",
                "Katakana",
                "Devanagari",
                "Thai",
            ):
                if _regex.match(rf"\p{{Script={name}}}", char):
                    return name
        except Exception:
            pass

    idx = bisect.bisect_right(_STARTS, cp) - 1
    if 0 <= idx < len(_SCRIPT_RANGES):
        start, end, name = _SCRIPT_RANGES[idx]
        if start <= cp <= end:
            return name
    return "Unknown"
