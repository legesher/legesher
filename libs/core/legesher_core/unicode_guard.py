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


@functools.lru_cache(maxsize=1)
def _compute_invisible_format() -> frozenset[str]:
    chars: set[str] = set()
    for cp in range(0x110000):
        ch = chr(cp)
        if unicodedata.category(ch) == "Cf":
            chars.add(ch)
    return frozenset(chars)


def __getattr__(name: str) -> Any:
    # ``INVISIBLE_FORMAT`` (the full set of category-Cf characters) is computed
    # lazily on first access so importing this module stays cheap: scan_text
    # checks ``category`` inline and never materializes the whole set. Exposed
    # for callers/tests that want to test membership directly.
    if name == "INVISIBLE_FORMAT":
        return _compute_invisible_format()
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
    (category ``Cf``), Arabic tatweel padding, and a byte-order mark anywhere.

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

        if unicodedata.category(ch) == "Cf":
            if ch in allow:
                continue
            issues.append(
                Issue(
                    kind="invisible",
                    codepoint=_codepoint(ch),
                    offset=offset,
                    char_name=_name(ch),
                    message=(
                        f"Invisible/format character ({_codepoint(ch)}, category Cf)"
                    ),
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
