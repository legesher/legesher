"""Unicode/script security guard for the Legesher transpiler engine.

This is a self-contained, dependency-free module that detects script-level
attacks against source code that flows through Legesher's translation
pipeline. It is the engine-side complement to the language-pack validation
layer.

Attack classes covered:
    * Trojan Source (CVE-2021-42574): bidirectional control characters that
      visually reorder code so the rendered text differs from the bytes the
      compiler sees.
    * Invisible / format characters (Unicode category ``Cf``) that can hide
      or smuggle content.
    * Default-ignorable characters that render as nothing but are valid,
      NFKC-stable identifier characters (U+034F, Hangul fillers, variation
      selectors, …). These sit outside category ``Cf`` yet let two visually
      identical identifiers differ in canonical output (parity with the JS
      guard's ``\\p{Default_Ignorable_Code_Point}`` net).
    * Arabic tatweel (U+0640) padding used to disguise identifiers.
    * Byte-order marks (BOM) that desync byte/character offsets and PEP 263
      encoding detection.

Note:
    A future PR should consolidate this module with the ``script_policy``
    helper in ``libs/i18n`` so the engine and the pack-validation layer share
    one allow/deny policy. They are intentionally kept separate here to keep
    this PR scoped to the engine.
"""

from __future__ import annotations

import bisect
import functools
import unicodedata
from dataclasses import dataclass
from typing import Any

# Bidirectional formatting / reordering controls. This is the exact set that
# the Trojan Source paper (CVE-2021-42574) identifies as dangerous in source
# code: the explicit embeddings/overrides, the isolates, and the Arabic
# letter mark. Built from code points via ``chr()`` so the dangerous
# characters never appear literally in this file (which also keeps the
# Trojan-Source linters from flagging the detector itself).
BIDI_CONTROLS: frozenset[str] = frozenset(
    chr(cp)
    for cp in (
        0x202A,  # LEFT-TO-RIGHT EMBEDDING (LRE)
        0x202B,  # RIGHT-TO-LEFT EMBEDDING (RLE)
        0x202C,  # POP DIRECTIONAL FORMATTING (PDF)
        0x202D,  # LEFT-TO-RIGHT OVERRIDE (LRO)
        0x202E,  # RIGHT-TO-LEFT OVERRIDE (RLO)
        0x2066,  # LEFT-TO-RIGHT ISOLATE (LRI)
        0x2067,  # RIGHT-TO-LEFT ISOLATE (RLI)
        0x2068,  # FIRST STRONG ISOLATE (FSI)
        0x2069,  # POP DIRECTIONAL ISOLATE (PDI)
        0x061C,  # ARABIC LETTER MARK (ALM)
    )
)

# Byte-order mark (U+FEFF, ZERO WIDTH NO-BREAK SPACE).
BOM: str = chr(0xFEFF)

# Arabic tatweel / kashida — a justification character with no semantic value
# that is frequently abused to pad or disguise identifiers.
TATWEEL: str = chr(0x0640)


# Default_Ignorable_Code_Point ranges (start, end_inclusive), sorted by start.
#
# These code points render as nothing yet many of them are valid identifier
# characters (ID_Continue, and the Hangul fillers are even ID_Start) AND
# NFKC-stable, so neither the category-``Cf`` invisible check nor a
# normalization pass rejects them. Left unchecked they let two visually
# identical identifiers differ in the runnable canonical output — the exact
# "what you see is what runs" bypass this guard exists to surface. The plain
# ``unicodedata.category(ch) == "Cf"`` test misses the non-``Cf`` members
# (U+034F COMBINING GRAPHEME JOINER, the U+115F/U+1160 HANGUL FILLERS, the
# U+FE00–U+FE0F VARIATION SELECTORS, …), which is the gap CORE-1559 closes —
# the parallel of the JS guard's ``\p{Default_Ignorable_Code_Point}`` net
# (CORE-1556).
#
# ``unicodedata`` does not expose the Default_Ignorable_Code_Point property, so
# this is a static table transcribed from the Unicode Character Database
# DerivedCoreProperties.txt (Unicode 15.1; the property set is unchanged in
# 16.0). This mirrors the range-table style already used by
# ``script_lookup.py`` and ``libs/i18n``'s ``script_policy.py``. Reserved (Cn)
# sub-ranges are included so the net stays complete as those code points are
# assigned in future Unicode versions.
_DEFAULT_IGNORABLE_RANGES: tuple[tuple[int, int], ...] = (
    (0x00AD, 0x00AD),  # SOFT HYPHEN (Cf)
    (0x034F, 0x034F),  # COMBINING GRAPHEME JOINER (Mn)
    (0x061C, 0x061C),  # ARABIC LETTER MARK (Cf)
    (0x115F, 0x1160),  # HANGUL CHOSEONG/JUNGSEONG FILLER (Lo)
    (0x17B4, 0x17B5),  # KHMER VOWEL INHERENT AQ..AA (Mn)
    (0x180B, 0x180D),  # MONGOLIAN FREE VARIATION SELECTOR ONE..THREE (Mn)
    (0x180E, 0x180E),  # MONGOLIAN VOWEL SEPARATOR (Cf)
    (0x180F, 0x180F),  # MONGOLIAN FREE VARIATION SELECTOR FOUR (Mn)
    (0x200B, 0x200F),  # ZERO WIDTH SPACE..RIGHT-TO-LEFT MARK (Cf)
    (0x202A, 0x202E),  # LEFT-TO-RIGHT EMBEDDING..RIGHT-TO-LEFT OVERRIDE (Cf)
    (0x2060, 0x2064),  # WORD JOINER..INVISIBLE PLUS (Cf)
    (0x2065, 0x2065),  # <reserved> (Cn)
    (0x2066, 0x206F),  # LEFT-TO-RIGHT ISOLATE..NOMINAL DIGIT SHAPES (Cf)
    (0x3164, 0x3164),  # HANGUL FILLER (Lo)
    (0xFE00, 0xFE0F),  # VARIATION SELECTOR-1..16 (Mn)
    (0xFEFF, 0xFEFF),  # ZERO WIDTH NO-BREAK SPACE / BOM (Cf)
    (0xFFA0, 0xFFA0),  # HALFWIDTH HANGUL FILLER (Lo)
    (0xFFF0, 0xFFF8),  # <reserved> (Cn)
    (0x1BCA0, 0x1BCA3),  # SHORTHAND FORMAT LETTER OVERLAP..UP STEP (Cf)
    (0x1D173, 0x1D17A),  # MUSICAL SYMBOL BEGIN BEAMED..END PHRASE (Cf)
    (0xE0000, 0xE0000),  # <reserved> (Cn)
    (0xE0001, 0xE0001),  # LANGUAGE TAG (Cf)
    (0xE0002, 0xE001F),  # <reserved> (Cn)
    (0xE0020, 0xE007F),  # TAG SPACE..CANCEL TAG (Cf)
    (0xE0080, 0xE00FF),  # <reserved> (Cn)
    (0xE0100, 0xE01EF),  # VARIATION SELECTOR-17..256 (Mn)
    (0xE01F0, 0xE0FFF),  # <reserved> (Cn)
)

_DEFAULT_IGNORABLE_STARTS: tuple[int, ...] = tuple(
    r[0] for r in _DEFAULT_IGNORABLE_RANGES
)


def is_default_ignorable(ch: str) -> bool:
    """Return True if ``ch`` is a Default_Ignorable_Code_Point.

    These characters render invisibly. Many are valid identifier characters and
    NFKC-stable, so they can silently distinguish two visually identical
    identifiers in canonical output. Backed by a static Unicode 15.1 range table
    because ``unicodedata`` does not expose the property.
    """
    if not ch:
        return False
    cp = ord(ch[0])
    idx = bisect.bisect_right(_DEFAULT_IGNORABLE_STARTS, cp) - 1
    if 0 <= idx < len(_DEFAULT_IGNORABLE_RANGES):
        start, end = _DEFAULT_IGNORABLE_RANGES[idx]
        return start <= cp <= end
    return False


@functools.lru_cache(maxsize=1)
def _compute_default_ignorable() -> frozenset[str]:
    return frozenset(
        chr(cp)
        for start, end in _DEFAULT_IGNORABLE_RANGES
        for cp in range(start, end + 1)
    )


@functools.lru_cache(maxsize=1)
def _compute_invisible_format() -> frozenset[str]:
    chars: set[str] = set()
    for cp in range(0x110000):
        ch = chr(cp)
        if unicodedata.category(ch) == "Cf":
            chars.add(ch)
    return frozenset(chars)


def __getattr__(name: str) -> Any:
    # ``INVISIBLE_FORMAT`` (the full set of category-Cf characters) and
    # ``DEFAULT_IGNORABLE`` (the full Default_Ignorable_Code_Point set) are
    # computed lazily on first access so importing this module stays cheap:
    # scan_text checks membership inline (``category`` / ``is_default_ignorable``)
    # and never materializes either set. Exposed for callers/tests that want to
    # test membership directly.
    if name == "INVISIBLE_FORMAT":
        return _compute_invisible_format()
    if name == "DEFAULT_IGNORABLE":
        return _compute_default_ignorable()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


@dataclass(frozen=True)
class Issue:
    """A single Unicode/script finding.

    Attributes:
        kind: One of ``"bidi"``, ``"invisible"``, ``"tatweel"``, ``"bom"``.
        codepoint: The offending code point (e.g. ``"U+202E"``).
        offset: Character offset (0-indexed) into the scanned text.
        char_name: Best-effort Unicode name for the character.
        message: Human-readable description.
    """

    kind: str
    codepoint: str
    offset: int
    char_name: str
    message: str


def _codepoint(ch: str) -> str:
    return f"U+{ord(ch):04X}"


def _name(ch: str) -> str:
    return unicodedata.name(ch, "<unnamed>")


def scan_text(
    text: str,
    allowed_format_chars: frozenset[str] | set[str] | None = None,
) -> list[Issue]:
    """Scan ``text`` for dangerous Unicode/script constructs.

    Detects, with code point and character offset: bidirectional reordering
    controls (Trojan Source class), disallowed invisible/format characters
    (category ``Cf`` plus the wider Default_Ignorable_Code_Point set), Arabic
    tatweel padding, and a byte-order mark anywhere.

    Args:
        text: The text to scan.
        allowed_format_chars: Optional per-call allowlist of format characters
            that should NOT be reported (e.g. legitimate ZWJ ``U+200D`` / ZWNJ
            ``U+200C`` inside string/comment content, or a known-good
            identifier). Bidi reordering controls are NEVER suppressed — they
            are always dangerous in code.

    Returns:
        A list of :class:`Issue` in offset order. Empty if the text is clean.
    """
    allow = frozenset(allowed_format_chars or ())
    issues: list[Issue] = []

    for offset, ch in enumerate(text):
        if ch == BOM:
            if offset == 0:
                issues.append(
                    Issue(
                        kind="bom",
                        codepoint=_codepoint(ch),
                        offset=offset,
                        char_name=_name(ch),
                        message="Byte-order mark (U+FEFF) present in source",
                    )
                )
                continue
            # An interior U+FEFF is not a legitimate BOM: it is a zero-width
            # invisible (category Cf) that desyncs offsets and can smuggle a
            # hidden identifier distinction. Report it as ``invisible`` (not the
            # informational ``bom`` kind) so the git clean filter — which blocks
            # bidi/invisible/tatweel but treats bom as advisory — rejects it
            # instead of letting it reach canonical storage. Respect ``allow``
            # for parity with the general Cf branch below.
            if ch not in allow:
                issues.append(
                    Issue(
                        kind="invisible",
                        codepoint=_codepoint(ch),
                        offset=offset,
                        char_name=_name(ch),
                        message=(
                            f"Interior byte-order mark ({_codepoint(ch)}) — "
                            "zero-width invisible (category Cf)"
                        ),
                    )
                )
            continue

        if ch in BIDI_CONTROLS:
            issues.append(
                Issue(
                    kind="bidi",
                    codepoint=_codepoint(ch),
                    offset=offset,
                    char_name=_name(ch),
                    message=(
                        "Bidirectional reordering control "
                        f"({_codepoint(ch)}) — Trojan Source (CVE-2021-42574)"
                    ),
                )
            )
            continue

        if ch == TATWEEL:
            if ch in allow:
                continue
            issues.append(
                Issue(
                    kind="tatweel",
                    codepoint=_codepoint(ch),
                    offset=offset,
                    char_name=_name(ch),
                    message="Arabic tatweel (U+0640) padding character",
                )
            )
            continue

        # Invisible/format characters. Two overlapping nets: the category-``Cf``
        # controls (word joiner, zero-width space, …) and the full
        # Default_Ignorable_Code_Point set, which additionally covers non-``Cf``
        # invisibles — U+034F, the Hangul fillers, the variation selectors — that
        # ``category == "Cf"`` alone misses (CORE-1559, parity with the JS guard
        # CORE-1556). Both honor ``allow`` so legitimate invisibles inside
        # string/comment content are not reported.
        is_cf = unicodedata.category(ch) == "Cf"
        is_default_ignorable_ch = is_default_ignorable(ch)
        if is_cf or is_default_ignorable_ch:
            if ch in allow:
                continue
            message = (
                f"Invisible/format character ({_codepoint(ch)}, category Cf)"
                if is_cf
                else (
                    f"Default-ignorable character ({_codepoint(ch)}) — "
                    "renders invisibly"
                )
            )
            issues.append(
                Issue(
                    kind="invisible",
                    codepoint=_codepoint(ch),
                    offset=offset,
                    char_name=_name(ch),
                    message=message,
                )
            )

    return issues


def has_trojan_source(text: str) -> bool:
    """Return True if ``text`` contains bidi reordering controls.

    The Trojan Source (CVE-2021-42574) check: any bidirectional
    embedding/override/isolate control (or the Arabic letter mark) in code is
    treated as an attack, because it can make rendered source differ from the
    bytes a compiler sees.
    """
    return any(ch in BIDI_CONTROLS for ch in text)


def strip_bom(text: str) -> str:
    """Strip a single leading byte-order mark (U+FEFF) if present.

    Only a *leading* BOM is removed; interior U+FEFF (suspicious) is left in
    place so :func:`scan_text` can still flag it.
    """
    if text.startswith(BOM):
        return text[len(BOM) :]
    return text
