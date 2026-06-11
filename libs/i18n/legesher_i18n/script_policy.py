"""Per-language Unicode script policy for language-pack safety validation.

This module is the single source of truth for *which Unicode scripts and
format characters are legitimate* in each language pack's translation values.
It backs the script-consistency and format-character checks in
:mod:`legesher_i18n.schema_validator` and the standalone audit in
:mod:`legesher_i18n.scripts.audit_packs`.

Why a script policy exists
--------------------------
Machine-translated packs occasionally smuggle in characters from the wrong
script (Chinese ``布尔`` inside a Polish ``bool``; a stray Cyrillic letter in a
Thai value; a Hangul syllable in a Hindi identifier). Those values still look
plausible and even ``str.isidentifier()``-pass, but they corrupt the pack.
This table lets the validator reject any value whose scripts fall outside the
language's declared allowlist.

Two Unicode "script" pseudo-values are *always* allowed for every language,
because they are script-agnostic by definition:

* ``Common`` — digits, underscore, ASCII punctuation, the space, etc.
* ``Inherited`` — combining marks that take on the script of their base
  character (e.g. the Devanagari virama, Arabic harakat).

Script detection uses :func:`scripts_of`, which is built on the pure-stdlib
:mod:`unicodedata` module via ``Script_Extensions`` semantics approximated
through ``unicodedata.name``-free range tables. No third-party ``regex``
dependency is introduced (deliberate: see CONSTRAINTS in the originating PR).

How to add a new language (51 -> 103 expansion)
-----------------------------------------------
1. Identify the dominant Unicode script(s) the orthography uses. For most
   languages this is exactly one script; Japanese is the notable exception
   (Han + Hiragana + Katakana).
2. Add a :class:`ScriptPolicy` entry to :data:`SCRIPT_POLICIES` keyed by the
   ISO 639 code, listing those scripts in ``scripts``.
3. Set ``direction`` to ``"rtl"`` for right-to-left orthographies
   (Arabic, Hebrew, Thaana, N'Ko, ...), otherwise ``"ltr"``.
4. If — and only if — the orthography *requires* a Unicode format character
   (``Cf``) to form correct identifiers, add it to ``allowed_format_chars``.
   Today that is the Sinhala ZWJ (U+200D, virama+ZWJ+consonant ligatures) and
   the Persian/Urdu ZWNJ (U+200C). Do **not** add format chars speculatively;
   every entry here is a hole punched in the bidi-control denylist.
5. Add a coverage row to ``tests/test_script_policy_coverage.py`` (the test
   asserts every shipped pack code has a policy — a missing entry fails CI).

Default-deny
------------
:func:`policy_for` raises :class:`KeyError` for unknown codes. Callers that
want a soft failure should catch it. There is intentionally **no** permissive
fallback: an un-policied language must not silently pass the script gate.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Named format characters (Unicode general category Cf and friends)
# ---------------------------------------------------------------------------

ZWJ = "\u200d"  # ZERO WIDTH JOINER — legitimate in Sinhala conjuncts
ZWNJ = "\u200c"  # ZERO WIDTH NON-JOINER — legitimate in Persian/Urdu
BOM = "\ufeff"  # ZERO WIDTH NO-BREAK SPACE / BYTE ORDER MARK — never legitimate
TATWEEL = "\u0640"  # ARABIC TATWEEL — category Lm, a decorative elongation only

# Bidirectional control characters. These are *never* legitimate inside an
# identifier translation: they exist to reorder visual runs and are a classic
# homoglyph / Trojan-source attack vector (CVE-2021-42574).
# Built from code points via ``chr()`` so these dangerous characters never
# appear literally in this file (keeps the source auditable and avoids
# Trojan-source linters flagging the policy table itself).
BIDI_CONTROLS: frozenset[str] = frozenset(
    chr(cp)
    for cp in (
        0x202A,  # LEFT-TO-RIGHT EMBEDDING
        0x202B,  # RIGHT-TO-LEFT EMBEDDING
        0x202C,  # POP DIRECTIONAL FORMATTING
        0x202D,  # LEFT-TO-RIGHT OVERRIDE
        0x202E,  # RIGHT-TO-LEFT OVERRIDE
        0x2066,  # LEFT-TO-RIGHT ISOLATE
        0x2067,  # RIGHT-TO-LEFT ISOLATE
        0x2068,  # FIRST STRONG ISOLATE
        0x2069,  # POP DIRECTIONAL ISOLATE
        0x200E,  # LEFT-TO-RIGHT MARK
        0x200F,  # RIGHT-TO-LEFT MARK
        0x061C,  # ARABIC LETTER MARK
    )
)

# Format / invisible characters that are forbidden in *every* language unless a
# language explicitly allow-lists them via ``allowed_format_chars``. Tatweel is
# included here even though its category is Lm (not Cf): it is a pure cosmetic
# elongation with no semantic content and must not appear in an identifier.
FORBIDDEN_FORMAT_CHARS: frozenset[str] = BIDI_CONTROLS | frozenset({BOM, TATWEEL})


@dataclass(frozen=True)
class ScriptPolicy:
    """Allowed scripts and format characters for one language.

    Attributes:
        scripts: Unicode script names (per ``Script_Extensions``) that may
            appear in this language's translation values, **excluding**
            ``Common`` and ``Inherited`` which are always allowed.
        direction: ``"ltr"`` or ``"rtl"`` — the dominant writing direction.
        allowed_format_chars: Unicode format characters (e.g. ZWJ, ZWNJ) that
            this orthography legitimately requires inside identifiers. Empty
            for the vast majority of languages.
        normalization: Unicode normalization form the validator enforces
            stability against. Always ``"NFKC"`` for Python-identifier safety.
    """

    scripts: frozenset[str]
    direction: str = "ltr"
    allowed_format_chars: frozenset[str] = field(default_factory=frozenset)
    normalization: str = "NFKC"


# ---------------------------------------------------------------------------
# Script names always permitted, regardless of language.
# ---------------------------------------------------------------------------

ALWAYS_ALLOWED_SCRIPTS: frozenset[str] = frozenset({"Common", "Inherited"})


def _latin() -> ScriptPolicy:
    """Return the default Latin-script, LTR policy."""
    return ScriptPolicy(scripts=frozenset({"Latin"}))


# ---------------------------------------------------------------------------
# The policy table: one entry per shipped language pack code.
#
# Grouped by script for readability. ``policy_for`` is default-deny, so every
# code under language-packs/python/ MUST appear here (enforced by
# tests/test_script_policy_coverage.py).
# ---------------------------------------------------------------------------

SCRIPT_POLICIES: dict[str, ScriptPolicy] = {
    # --- Arabic script (RTL) -------------------------------------------------
    "ar": ScriptPolicy(scripts=frozenset({"Arabic"}), direction="rtl"),
    "fa": ScriptPolicy(
        scripts=frozenset({"Arabic"}),
        direction="rtl",
        allowed_format_chars=frozenset({ZWNJ}),
    ),
    "ur": ScriptPolicy(
        scripts=frozenset({"Arabic"}),
        direction="rtl",
        allowed_format_chars=frozenset({ZWNJ}),
    ),
    # --- Hebrew script (RTL) -------------------------------------------------
    "he": ScriptPolicy(scripts=frozenset({"Hebrew"}), direction="rtl"),
    # --- Indic & South / Southeast Asian scripts ----------------------------
    "am": ScriptPolicy(scripts=frozenset({"Ethiopic"})),
    "bn": ScriptPolicy(scripts=frozenset({"Bengali"})),
    "gu": ScriptPolicy(scripts=frozenset({"Gujarati"})),
    "hi": ScriptPolicy(scripts=frozenset({"Devanagari"})),
    "kn": ScriptPolicy(scripts=frozenset({"Kannada"})),
    "ml": ScriptPolicy(scripts=frozenset({"Malayalam"})),
    "te": ScriptPolicy(scripts=frozenset({"Telugu"})),
    "si": ScriptPolicy(
        scripts=frozenset({"Sinhala"}),
        allowed_format_chars=frozenset({ZWJ}),
    ),
    "my": ScriptPolicy(scripts=frozenset({"Myanmar"})),
    "th": ScriptPolicy(scripts=frozenset({"Thai"})),
    # --- CJK -----------------------------------------------------------------
    "ja": ScriptPolicy(scripts=frozenset({"Han", "Hiragana", "Katakana"})),
    "ko": ScriptPolicy(scripts=frozenset({"Hangul"})),
    "zh": ScriptPolicy(scripts=frozenset({"Han"})),
    # --- Cyrillic ------------------------------------------------------------
    "ru": ScriptPolicy(scripts=frozenset({"Cyrillic"})),
    "mk": ScriptPolicy(scripts=frozenset({"Cyrillic"})),
    "sr": ScriptPolicy(scripts=frozenset({"Cyrillic"})),
    "mn": ScriptPolicy(scripts=frozenset({"Cyrillic"})),
    # --- Greek ---------------------------------------------------------------
    "el": ScriptPolicy(scripts=frozenset({"Greek"})),
    # --- Latin (explicit non-default member) ---------------------------------
    "uz": _latin(),
    # --- Latin (default group) ----------------------------------------------
    "bs": _latin(),
    "ca": _latin(),
    "cs": _latin(),
    "cy": _latin(),
    "da": _latin(),
    "de": _latin(),
    "en": _latin(),
    "es": _latin(),
    "fi": _latin(),
    "fr": _latin(),
    "ga": _latin(),
    "gd": _latin(),
    "gl": _latin(),
    "hr": _latin(),
    "hu": _latin(),
    "id": _latin(),
    "it": _latin(),
    "lv": _latin(),
    "ms": _latin(),
    "nl": _latin(),
    "no": _latin(),
    "pl": _latin(),
    "pt": _latin(),
    "ro": _latin(),
    "su": _latin(),
    "sv": _latin(),
    "tr": _latin(),
    "vi": _latin(),
}


def policy_for(language: str) -> ScriptPolicy:
    """Return the :class:`ScriptPolicy` for *language* (default-deny).

    Args:
        language: ISO 639 language code (case-insensitive).

    Returns:
        The policy for that language.

    Raises:
        KeyError: If the language has no registered policy. This is a
            deliberate default-deny: an un-policied language must not pass the
            script gate. Callers wanting a soft failure should catch it.
    """
    key = language.lower()
    if key not in SCRIPT_POLICIES:
        raise KeyError(
            f"No script policy registered for language '{language}'. "
            "Add an entry to SCRIPT_POLICIES (see 'How to add a new language' "
            "in legesher_i18n/script_policy.py)."
        )
    return SCRIPT_POLICIES[key]


def has_policy(language: str) -> bool:
    """Return True if *language* has a registered script policy."""
    return language.lower() in SCRIPT_POLICIES


# ---------------------------------------------------------------------------
# Script detection (pure unicodedata — no third-party `regex` dependency).
#
# Unicode does not expose Script / Script_Extensions through the stdlib
# `unicodedata` module directly, so we derive a coarse script name from the
# character's Unicode block via a compact range table. The blocks covered are
# exactly those used by the 51 shipped packs plus the common digits/punctuation
# that map to the script-agnostic "Common" pseudo-script. Anything outside the
# table — letters from a script not in the table, private-use, etc. — is
# reported as "Unknown", which the validator treats as a script violation.
# ---------------------------------------------------------------------------

# (inclusive_start, inclusive_end, script_name)
_SCRIPT_RANGES: tuple[tuple[int, int, str], ...] = (
    # Latin
    (0x0041, 0x005A, "Latin"),
    (0x0061, 0x007A, "Latin"),
    (0x00AA, 0x00AA, "Latin"),
    (0x00BA, 0x00BA, "Latin"),
    (0x00C0, 0x00FF, "Latin"),
    (0x0100, 0x017F, "Latin"),  # Latin Extended-A
    (0x0180, 0x024F, "Latin"),  # Latin Extended-B
    (0x1E00, 0x1EFF, "Latin"),  # Latin Extended Additional (Vietnamese)
    # Greek
    (0x0370, 0x0373, "Greek"),
    (0x0375, 0x0377, "Greek"),
    (0x037A, 0x037D, "Greek"),
    (0x037F, 0x037F, "Greek"),
    (0x0384, 0x0384, "Greek"),
    (0x0386, 0x0386, "Greek"),
    (0x0388, 0x03FF, "Greek"),
    (0x1F00, 0x1FFF, "Greek"),  # Greek Extended
    # Cyrillic
    (0x0400, 0x04FF, "Cyrillic"),
    (0x0500, 0x052F, "Cyrillic"),  # Cyrillic Supplement
    # Hebrew
    (0x0590, 0x05FF, "Hebrew"),
    # Arabic
    (0x0600, 0x06FF, "Arabic"),
    (0x0750, 0x077F, "Arabic"),  # Arabic Supplement
    (0x08A0, 0x08FF, "Arabic"),  # Arabic Extended-A
    (0xFB50, 0xFDFF, "Arabic"),  # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF, "Arabic"),  # Arabic Presentation Forms-B
    # Ethiopic
    (0x1200, 0x137F, "Ethiopic"),
    (0x1380, 0x139F, "Ethiopic"),  # Ethiopic Supplement
    (0x2D80, 0x2DDF, "Ethiopic"),  # Ethiopic Extended
    # Devanagari
    (0x0900, 0x097F, "Devanagari"),
    # Bengali
    (0x0980, 0x09FF, "Bengali"),
    # Gujarati
    (0x0A80, 0x0AFF, "Gujarati"),
    # Kannada
    (0x0C80, 0x0CFF, "Kannada"),
    # Telugu
    (0x0C00, 0x0C7F, "Telugu"),
    # Malayalam
    (0x0D00, 0x0D7F, "Malayalam"),
    # Sinhala
    (0x0D80, 0x0DFF, "Sinhala"),
    # Thai
    (0x0E00, 0x0E7F, "Thai"),
    # Myanmar
    (0x1000, 0x109F, "Myanmar"),
    (0xAA60, 0xAA7F, "Myanmar"),  # Myanmar Extended-A
    # Han (CJK Unified Ideographs + Extension A + compatibility)
    (0x3400, 0x4DBF, "Han"),
    (0x4E00, 0x9FFF, "Han"),
    (0xF900, 0xFAFF, "Han"),  # CJK Compatibility Ideographs
    (0x20000, 0x2A6DF, "Han"),  # CJK Extension B
    # Hiragana
    (0x3041, 0x3096, "Hiragana"),
    (0x309D, 0x309F, "Hiragana"),
    # Katakana
    (0x30A1, 0x30FA, "Katakana"),
    # U+30FC KATAKANA-HIRAGANA PROLONGED SOUND MARK has Script_Extensions
    # {Hira, Kana}; it is a normal part of Japanese identifiers (e.g. サーバー)
    # so we map it to Katakana rather than letting its Lm category read Unknown.
    (0x30FC, 0x30FF, "Katakana"),
    (0x31F0, 0x31FF, "Katakana"),  # Katakana Phonetic Extensions
    # Hangul
    (0x1100, 0x11FF, "Hangul"),  # Hangul Jamo
    (0x3130, 0x318F, "Hangul"),  # Hangul Compatibility Jamo
    (0xA960, 0xA97F, "Hangul"),  # Hangul Jamo Extended-A
    (0xAC00, 0xD7A3, "Hangul"),  # Hangul Syllables
    (0xD7B0, 0xD7FF, "Hangul"),  # Hangul Jamo Extended-B
)


def _script_of_char(char: str) -> str:
    """Return the coarse script name for a single character.

    Common/Inherited classification:

    * Characters whose Unicode general category is a combining mark (``Mn``,
      ``Mc``, ``Me``) are reported as ``Inherited`` *unless* they fall inside a
      script's block range (e.g. the Devanagari virama lives in the Devanagari
      block and should count as Devanagari). The block table is checked first.
    * Digits, underscore, ASCII punctuation, spaces, and any other
      script-agnostic character is reported as ``Common``.
    * A letter from an unrecognised script is reported as ``Unknown`` so the
      validator can flag it.
    """
    cp = ord(char)
    for start, end, name in _SCRIPT_RANGES:
        if start <= cp <= end:
            return name

    category = unicodedata.category(char)
    # Combining marks not inside a known script block inherit their base.
    if category in ("Mn", "Mc", "Me"):
        return "Inherited"
    # Letters / modifier letters / number-letters that we don't recognise are
    # genuinely foreign — surface them as Unknown so the gate can reject.
    if category in ("Lo", "Ll", "Lu", "Lt", "Lm", "Nl"):
        return "Unknown"
    # Everything else (digits, punctuation, separators, format chars handled
    # elsewhere) is script-agnostic.
    return "Common"


def scripts_of(value: str) -> set[str]:
    """Return the set of Unicode scripts present in *value*.

    Built purely on :mod:`unicodedata` and a static block table — no
    third-party ``regex`` dependency. ``Common`` and ``Inherited`` are included
    in the result when present; callers typically subtract
    :data:`ALWAYS_ALLOWED_SCRIPTS` before comparing against an allowlist.

    Format characters (ZWJ, ZWNJ, bidi controls, BOM) report as ``Common`` here
    and are policed separately by the format-character check; do not rely on
    this function to catch them.

    Args:
        value: The string to inspect.

    Returns:
        Set of script names (e.g. ``{"Latin", "Common"}``).
    """
    return {_script_of_char(ch) for ch in value}
