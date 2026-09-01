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
   every entry here is a hole punched in the bidi-control denylist — and the
   :class:`ScriptPolicy` constructor refuses an entry that is in
   :data:`FORBIDDEN_FORMAT_CHARS` or is not category ``Cf``, so the hole can
   never reach a character the net exists to block.
5. Add a coverage row to ``tests/test_script_policy_coverage.py`` (the test
   asserts every shipped pack code has a policy — a missing entry fails CI).

Default-deny
------------
:func:`policy_for` raises :class:`KeyError` for unknown codes. Callers that
want a soft failure should catch it. There is intentionally **no** permissive
fallback: an un-policied language must not silently pass the script gate.
"""

from __future__ import annotations

import bisect
import functools
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
# Split into two halves because consumers need different ones. In an
# IDENTIFIER all twelve are forbidden, and BIDI_CONTROLS (the union) is what
# the pack auditor and the format-char gate check. In FREE TEXT — a review
# comment, a rationale — only the embeddings/overrides/isolates are a smell:
# the MARKS are ordinary punctuation in Arabic and Urdu prose, and the intake
# path exists to serve exactly those locales, so flagging every RTL comment
# would train a maintainer to ignore the screen.
BIDI_EMBEDDINGS: frozenset[str] = frozenset(
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
    )
)

BIDI_MARKS: frozenset[str] = frozenset(
    chr(cp)
    for cp in (
        0x200E,  # LEFT-TO-RIGHT MARK
        0x200F,  # RIGHT-TO-LEFT MARK
        0x061C,  # ARABIC LETTER MARK
    )
)

BIDI_CONTROLS: frozenset[str] = BIDI_EMBEDDINGS | BIDI_MARKS

# Format / invisible characters that are forbidden in *every* language unless a
# language explicitly allow-lists them via ``allowed_format_chars``. Tatweel is
# included here even though its category is Lm (not Cf): it is a pure cosmetic
# elongation with no semantic content and must not appear in an identifier.
FORBIDDEN_FORMAT_CHARS: frozenset[str] = BIDI_CONTROLS | frozenset({BOM, TATWEEL})


# ---------------------------------------------------------------------------
# Default_Ignorable_Code_Point ranges (start, end_inclusive), sorted by start.
# ---------------------------------------------------------------------------
#
# These code points render as nothing yet many of them are valid identifier
# characters (``.isidentifier()``-True) AND NFKC-stable, so neither the
# category-``Cf`` net in ``check_format_chars`` nor the normalization check
# rejects them, and the non-``Cf`` members (U+034F COMBINING GRAPHEME JOINER is
# Mn -> script "Inherited"; the Hangul fillers are Lo inside Hangul blocks)
# sail through the script-consistency gate too. A pack value
# ``valid<U+034F>name`` renders identically to ``validname`` but is a
# different identifier — the gap CORE-1591 closes at the pack layer.
#
# ``unicodedata`` does not expose the Default_Ignorable_Code_Point property, so
# this is a static table transcribed from the Unicode Character Database
# DerivedCoreProperties.txt (Unicode 15.1; the property set is unchanged in
# 16.0). Reserved (Cn) sub-ranges are included so the net stays complete as
# those code points are assigned in future Unicode versions.
#
# NOTE: this table mirrors ``legesher_core.unicode_guard._DEFAULT_IGNORABLE_RANGES``
# (the engine-side half of the same fix, CORE-1559). legesher-i18n is the
# dependency leaf of the workspace — legesher-core depends on it, not vice
# versa — so the table is duplicated here rather than imported. Consolidation
# into one shared table is tracked as CORE-1597.
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
    translation values. Backed by a static Unicode 15.1 range table because
    ``unicodedata`` does not expose the property. Per-language allow-listing
    (Sinhala ZWJ, Persian/Urdu ZWNJ) is applied by the caller
    (``SchemaValidator.check_format_chars``), not here.
    """
    if not ch:
        return False
    cp = ord(ch[0])
    idx = bisect.bisect_right(_DEFAULT_IGNORABLE_STARTS, cp) - 1
    if 0 <= idx < len(_DEFAULT_IGNORABLE_RANGES):
        start, end = _DEFAULT_IGNORABLE_RANGES[idx]
        return start <= cp <= end
    return False


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

    Raises:
        ValueError: if ``allowed_format_chars`` names a character in
            :data:`FORBIDDEN_FORMAT_CHARS` or one that is not category ``Cf``.
            Every consumer of the allowlist — the pack gate, the intake gates,
            the canon backfill — checks it BEFORE the forbidden set, so an
            entry here is an unconditional hole through the whole net. Bidi
            controls, the BOM, and tatweel are never orthography: no policy
            may ever allowlist one, and this constructor is where that stops
            being a social rule (CORE-2029 review finding).
    """

    scripts: frozenset[str]
    direction: str = "ltr"
    allowed_format_chars: frozenset[str] = field(default_factory=frozenset)
    normalization: str = "NFKC"

    def __post_init__(self) -> None:
        forbidden = self.allowed_format_chars & FORBIDDEN_FORMAT_CHARS
        if forbidden:
            raise ValueError(
                "allowed_format_chars may never include a forbidden format "
                "character (bidi controls, BOM, tatweel): "
                + ", ".join(f"U+{ord(ch):04X}" for ch in sorted(forbidden))
            )
        non_format = {
            ch for ch in self.allowed_format_chars if unicodedata.category(ch) != "Cf"
        }
        if non_format:
            raise ValueError(
                "allowed_format_chars is a hole punched for format (Cf) "
                "characters an orthography requires; these are not Cf: "
                + ", ".join(f"U+{ord(ch):04X}" for ch in sorted(non_format))
            )


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


# ---------------------------------------------------------------------------
# Positive identifier allowlist (CORE-1558).
#
# The pack validator asks "does this value stay inside its language's scripts".
# The engine asks a narrower question of every identifier it is about to emit
# into runnable code: "is this character required by SOME supported script".
# The two share this module's range table so the answer cannot drift, but they
# need different fallbacks — see :func:`identifier_script_of`.
# ---------------------------------------------------------------------------

#: Combining-mark blocks that belong to no script of their own: they attach to
#: a base character from whatever script precedes them (Latin diacritics,
#: Greek/Cyrillic accents, IPA marks). :func:`identifier_script_of` reports
#: these — and only these — as ``Inherited``.
_GENERIC_MARK_RANGES: tuple[tuple[int, int], ...] = (
    (0x0300, 0x036F),  # Combining Diacritical Marks
    (0x1AB0, 0x1AFF),  # Combining Diacritical Marks Extended
    (0x1DC0, 0x1DFF),  # Combining Diacritical Marks Supplement
    (0x20D0, 0x20F0),  # Combining Diacritical Marks for Symbols
    (0xFE20, 0xFE2F),  # Combining Half Marks
)

#: Script-agnostic characters legitimate *inside an identifier*: the ASCII
#: digits plus the connector/currency characters the target languages accept
#: (``_`` in Python, ``_`` and ``$`` in JavaScript). Deliberately tiny — the
#: wide ``Common`` pseudo-script also covers spaces and punctuation, which can
#: never appear in an identifier and so must not be waved through here.
_IDENTIFIER_COMMON: frozenset[str] = frozenset("0123456789_$")

#: Identifier characters whose Unicode ``Script`` is ``Common`` but whose
#: ``Script_Extensions`` name a real script, resolved to that script.
#:
#: The block table above is a ``Script`` approximation, and ``Script`` alone is
#: wrong for characters a specific orthography owns while Unicode files them as
#: shared. U+30FB KATAKANA MIDDLE DOT is the one that bites: the shipped ``ja``
#: pack renders ``divmod`` as ``ディビジョン・モジュール`` on 3.13+, so a table
#: without it rejects a value Legesher itself ships. The JavaScript engine has
#: the real property (``\p{Script_Extensions=…}``) and admits these already;
#: this list is how the Python side reaches the same answer (CORE-1558).
#:
#: Only characters whose Unicode NAME does not already name their script belong
#: here — the rest are resolved by :data:`_SCRIPT_NAME_PREFIXES` below.
#:
#: Consulted only by :func:`identifier_script_of`. The pack-value classifier is
#: left alone — widening it would change what the validator accepts in values,
#: which is a separate decision.
_IDENTIFIER_SCX_RANGES: tuple[tuple[int, int, str], ...] = (
    (0x00B7, 0x00B7, "Latin"),  # MIDDLE DOT — the Catalan interpunct (l·l)
    (0x02B0, 0x02FF, "Latin"),  # Spacing Modifier Letters — Uzbek oʻ / maʼno
    # Phonetic / modifier-letter blocks. Their names say MODIFIER LETTER SMALL
    # TURNED ALPHA, never LATIN, so nothing downstream can place them; they are
    # Latin-alphabet phonetic notation and several are ordinary orthography.
    (0x1D2C, 0x1D6A, "Latin"),  # Phonetic Extensions
    (0x1D9B, 0x1DBF, "Latin"),  # Phonetic Extensions Supplement
    (0x2C60, 0x2C7F, "Latin"),  # Latin Extended-C
    (0xA717, 0xA721, "Latin"),  # modifier tone + stress letters
    (0xA770, 0xA770, "Latin"),  # MODIFIER LETTER US
    (0xA788, 0xA788, "Latin"),  # MODIFIER LETTER LOW CIRCUMFLEX ACCENT
    (0xA7F2, 0xA7F9, "Latin"),  # Latin Extended-D modifier capitals
    (0xAB5C, 0xAB69, "Latin"),  # Latin Extended-E modifier letters
    (0x10780, 0x107BA, "Latin"),  # Latin Extended-F
    (0x3005, 0x3007, "Han"),  # ideographic iteration/closing marks, number zero
    (0x3021, 0x3029, "Han"),  # Hangzhou numerals one..nine
    (0x3038, 0x303B, "Han"),  # Hangzhou tens + vertical ideographic iteration
)

#: Unicode NAME prefixes that identify a character's script, consulted when the
#: block tables miss.
#:
#: A block table cannot be complete: the supported scripts occupy ~340 disjoint
#: runs of identifier characters across the code space (Latin Extended-C/D/E,
#: IPA Extensions, Arabic Extended-B, Hebrew presentation forms, Cyrillic
#: Extended-B/C, halfwidth katakana, the astral kana, CJK Extensions B–I …),
#: and a positive allowlist turns every omission into a rejection of legitimate
#: code — ~29,000 characters were refused before this fallback existed, CJK
#: Extension C–I alone accounting for 27,906.
#:
#: Deriving the script from the character's name is the heuristic an earlier
#: engine used and this module's docstring warns against — correctly, for
#: *detecting* confusables, where a name says nothing about what a character
#: looks like. It is sound in the other direction: a character named ``LATIN
#: SMALL LETTER SCHWA`` really is Latin, so admitting it cannot be a false
#: accept. The failure mode is the safe one — an unnamed or oddly-named
#: character reports ``Unknown`` and is refused. U+2D7F is named ``TIFINAGH
#: CONSONANT JOINER``: Tifinagh is not here, so it stays out.
_SCRIPT_NAME_PREFIXES: dict[str, str] = {
    "ARABIC": "Arabic",
    "BENGALI": "Bengali",
    "CJK": "Han",
    "CYRILLIC": "Cyrillic",
    "DEVANAGARI": "Devanagari",
    "ETHIOPIC": "Ethiopic",
    "GREEK": "Greek",
    "GUJARATI": "Gujarati",
    "HANGUL": "Hangul",
    "HEBREW": "Hebrew",
    "HIRAGANA": "Hiragana",
    "IDEOGRAPHIC": "Han",
    "KANGXI": "Han",
    "KANNADA": "Kannada",
    "KATAKANA": "Katakana",
    "KATAKANA-HIRAGANA": "Katakana",
    "LATIN": "Latin",
    "MALAYALAM": "Malayalam",
    "MYANMAR": "Myanmar",
    "SINHALA": "Sinhala",
    "TELUGU": "Telugu",
    "THAI": "Thai",
}


@functools.lru_cache(maxsize=4096)
def _script_from_name(char: str) -> str:
    """Return the script named by ``char``'s Unicode name, or ``"Unknown"``.

    Scans the whole name, not just its head: the script keyword is the head for
    ``LATIN SMALL LETTER SCHWA`` but sits behind a qualifier in ``HALFWIDTH
    KATAKANA LETTER WO``, ``MODIFIER LETTER CYRILLIC EN``, and ``COMBINING
    DEVANAGARI DIGIT ZERO``. A name that mentions no supported script — every
    Tangut character has no name at all, and ``TIFINAGH CONSONANT JOINER``,
    ``MATHEMATICAL BOLD CAPITAL A`` and ``MUSICAL SYMBOL COMBINING STEM`` name
    none of them — returns ``Unknown`` and is refused.
    """
    name = unicodedata.name(char, "")
    if not name:
        return "Unknown"
    for token in name.split(" "):
        script = _SCRIPT_NAME_PREFIXES.get(token)
        if script is not None:
            return script
    return "Unknown"


def identifier_script_of(char: str) -> str:
    """Return the script of *char* for identifier-allowlist purposes.

    Stricter than the pack-value classifier behind :func:`scripts_of`, which
    reports **any** unrecognised combining mark as ``Inherited``. That fallback
    is right for translation values — an unknown mark beside a known base is
    usually a diacritic — but it is a hole in an identifier gate: U+2D7F
    TIFINAGH CONSONANT JOINER is an invisible ``Mn`` that is *not*
    Default_Ignorable, so it would ride through as ``Inherited`` and split one
    visible identifier into two runtime bindings (CORE-1558). Here only the
    generic combining-mark blocks are ``Inherited``; a mark belonging to an
    unsupported script reports ``Unknown``.

    Format and default-ignorable characters report ``Common`` because they are
    policed by a different layer — the guard's invisibles net, and the
    per-language ``allowed_format_chars`` hole punched for the Sinhala ZWJ and
    the Persian/Urdu ZWNJ. Classifying them here would double-report the same
    character or, worse, silently re-admit one.

    Args:
        char: A single character from an identifier.

    Returns:
        A script name, ``"Common"``, ``"Inherited"``, or ``"Unknown"``.
    """
    if unicodedata.category(char) == "Cf" or is_default_ignorable(char):
        return "Common"

    cp = ord(char)
    for start, end, name in _SCRIPT_RANGES:
        if start <= cp <= end:
            return name
    for start, end, name in _IDENTIFIER_SCX_RANGES:
        if start <= cp <= end:
            return name
    for start, end in _GENERIC_MARK_RANGES:
        if start <= cp <= end:
            return "Inherited"
    if char in _IDENTIFIER_COMMON:
        return "Common"
    return _script_from_name(char)


@functools.lru_cache(maxsize=1)
def supported_scripts() -> frozenset[str]:
    """Return every Unicode script some shipped language pack legitimately uses.

    Derived from :data:`SCRIPT_POLICIES` rather than hardcoded, so a new
    language's script becomes writable in identifiers the moment its policy
    lands — and no earlier. ``Common`` and ``Inherited`` are excluded; callers
    add :data:`ALWAYS_ALLOWED_SCRIPTS` themselves.

    The engine's positive identifier allowlist (CORE-1558) is this set. Its
    JavaScript twin — ``SUPPORTED_SCRIPTS`` in ``@legesher/core``'s
    ``script-allowlist.ts`` — mirrors the same names by hand, because the two
    engines ship from different repositories;
    ``tests/test_script_policy_coverage.py`` pins the list so a change here
    fails loudly rather than drifting apart unnoticed.
    """
    return frozenset().union(*(policy.scripts for policy in SCRIPT_POLICIES.values()))


# ---------------------------------------------------------------------------
# NFKC delta classification — shared with the v2 canon gate (CORE-1514).
# ---------------------------------------------------------------------------

#: Thai SARA AM and its NFKC decomposition (NIKHAHIT + SARA AA). U+0E33 is the
#: single source of NFKC instability across the shipped Thai pack values.
SARA_AM = "ำ"
_SARA_AM_NFKC = unicodedata.normalize("NFKC", SARA_AM)  # "ํา"


def nfkc_delta_class(value: str, nfkc: str | None = None) -> str | None:
    """Classify WHY *value* is NFKC-unstable, or return None when it is stable.

    ``"sara-am-only"`` — the ONLY unstable character is U+0E33 (Thai SARA AM),
    and decomposing it reproduces the NFKC form exactly. CPython itself NFKC-
    folds identifiers (PEP 3131), so both spellings are one identifier at
    runtime and there is no spoofing surface; legitimate Thai orthography.
    ``"other"`` — any other instability, which stays a hard defect.

    This mirrors the policy the v2 canon gate applies in
    ``scripts/migrate_to_v2.py`` (CORE-1514), so the pack auditor and the corpus
    validator agree on what "dirty" means.

    Args:
        value: The string to classify.
        nfkc: The NFKC normalization of *value*, if the caller already computed
            it (``check_normalization`` and ``validate_surface`` both do). Passed
            in to avoid a redundant ``unicodedata.normalize`` pass; computed here
            when ``None``.
    """
    if nfkc is None:
        nfkc = unicodedata.normalize("NFKC", value)
    if nfkc == value:
        return None
    unstable = {c for c in value if unicodedata.normalize("NFKC", c) != c}
    if unstable == {SARA_AM} and value.replace(SARA_AM, _SARA_AM_NFKC) == nfkc:
        return "sara-am-only"
    return "other"
