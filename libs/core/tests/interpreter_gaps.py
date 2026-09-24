"""Two interpreter-version gaps, pinned once so every sweep names them.

The packages support CPython 3.10 through 3.14, and two behaviours the
engine leans on changed inside that range. Both are pinned here as strict
xfails (or a skip that points at the strict xfail), so a fix, or a
CPython floor bump, reports as XPASS and never as a silent pass.

1. The pure-Python tokenizer (CPython 3.10 and 3.11)
   ``tokenize`` there spells NAME as ``\\w+``. ``\\w`` is ``str.isalnum``
   plus the underscore, which excludes every nonspacing and spacing mark
   (Mn, Mc) and every format character (Cf). A name carrying a vowel
   sign, a virama, a haraka or a joiner lexes as NAME / ERRORTOKEN / NAME
   fragments, while the C tokenizer behind ``tokenize`` from 3.12 on reads
   it as one NAME. ``git_filter._scan_identifier_scripts`` works around
   this for the guard; the token translator does not, so its return hop
   (native -> canonical) never matches a rendering that fragments, and 12
   shipped packs carry such vocabulary in the files these interpreters
   load: ar bn gu he hi kn ml my si te th ur (every Indic script, Thai,
   Myanmar, Sinhala, and a handful of pointed Arabic, Hebrew and Urdu
   values; the three Urdu ones are reached only by ``vocabulary.py``).
   ja's fragmenting value, the katakana middle dot in ``divmod``, lives in
   its 3.13+ files, which gap 2 keeps from loading here at all.

   The forward hop is unaffected: the English source lexes cleanly and
   ``untokenize`` reproduces the replacement bytes verbatim, fragments
   included. So the gap is exactly "a translated token the running
   tokenizer cannot read whole", which :func:`translated_fragments`
   computes from the two renderings rather than from a hand-kept list.

2. Identifier rules before Unicode 15.1 (CPython 3.10 through 3.12)
   Unicode 15.1 added ZWJ, ZWNJ and the katakana middle dot to
   ``Other_ID_Continue``; CPython 3.13 is the first release with those
   tables. The pack schema validator checks every rendering with the
   RUNNING interpreter's ``str.isidentifier()``, so a pack file whose
   values need those rules fails validation, and cannot load at all, on
   the three older interpreters. Two packs do this on purpose: ``si``
   spells its conjuncts with ZWJ from 3.13 on and ships a no-ZWJ variant
   for 3.10 through 3.12 (CORE-1521), and ``ja`` renders ``divmod`` with
   the katakana middle dot from 3.13 on (CORE-1905). The 3.14 files
   extend 3.13, so they inherit the constraint. Not a defect, but a fact
   every test that loads a 3.13+ pack on an older interpreter has to
   know; pinning it here keeps that knowledge in one place.
"""

from __future__ import annotations

import io
import sys
import tokenize
import unicodedata
from collections import Counter

import pytest

# -- gap 1: the pure-Python tokenizer -----------------------------------------

#: True where ``tokenize`` spells NAME as ``\\w+`` (CPython < 3.12).
PURE_PYTHON_TOKENIZER: bool = sys.version_info < (3, 12)


def error_tokens(source: str) -> Counter[str]:
    """Multiset of ERRORTOKEN strings the running ``tokenize`` emits."""
    try:
        return Counter(
            token.string
            for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type == tokenize.ERRORTOKEN
        )
    except tokenize.TokenError:
        return Counter()


def translated_fragments(source: str, native: str) -> list[str]:
    """Fragments of *translated* tokens the running tokenizer cannot read.

    Identifiers pass through translation untouched, so any fragment they
    produce appears in both renderings and cancels out; what remains came
    from a keyword, builtin or exception the pack rendered with a mark or
    a joiner. Non-empty means the return hop cannot match that token.
    """
    return sorted((error_tokens(native) - error_tokens(source)).elements())


def _tokenizer_gap_reason(fragments: list[str]) -> str:
    shown = ", ".join(f"U+{ord(ch):04X}" for ch in dict.fromkeys(fragments))
    return (
        f"pure-Python tokenize (CPython {sys.version_info.major}."
        f"{sys.version_info.minor}) spells NAME as \\w+, which excludes marks "
        f"and format characters; the return hop reads {shown} as ERRORTOKEN "
        "fragments and never matches the rendering they belong to "
        "(tests/interpreter_gaps.py, gap 1)"
    )


def xfail_if_return_hop_is_inert(
    request: pytest.FixtureRequest, source: str, native: str
) -> None:
    """Mark the running test xfail(strict) when gap 1 applies to it.

    Applied from inside the test body, once the forward rendering exists,
    so the decision is made from the actual bytes rather than predicted.
    Byte-identity is exactly predicted: a fragmenting translated token is
    never matched, so the return differs. A no-op with the C tokenizer.
    """
    if not PURE_PYTHON_TOKENIZER:
        return
    fragments = translated_fragments(source, native)
    if fragments:
        request.applymarker(
            pytest.mark.xfail(strict=True, reason=_tokenizer_gap_reason(fragments))
        )


def skip_if_return_hop_is_inert(source: str, native: str, *, pinned_by: str) -> None:
    """Skip a test whose outcome gap 1 makes meaningless, naming the pin.

    For anything downstream of byte-identity (does the returned source
    compile?) the gap does not predict the outcome: a fragmented keyword
    leaves a syntax error behind, a fragmented builtin leaves a name that
    still parses. The defect is already pinned, strictly, by ``pinned_by``
    on the same case; this only keeps the downstream check from reporting
    noise on either side.
    """
    if not PURE_PYTHON_TOKENIZER:
        return
    fragments = translated_fragments(source, native)
    if fragments:
        pytest.skip(f"{_tokenizer_gap_reason(fragments)}; pinned by {pinned_by}")


# -- gap 2: identifier rules before Unicode 15.1 -------------------------------

#: The running interpreter's Unicode tables, as a comparable tuple.
UNICODE_VERSION: tuple[int, ...] = tuple(
    int(part) for part in unicodedata.unidata_version.split(".")
)

#: True where ZWJ, ZWNJ and U+30FB are identifier characters (CPython 3.13+).
IDENTIFIER_RULES_ARE_UNICODE_15_1: bool = UNICODE_VERSION >= (15, 1)

#: (language, pack version) files whose renderings are identifiers only
#: under Unicode 15.1 rules. Strict: an entry that loads on an older
#: interpreter is a stale row, and a new one that does not load is a new
#: failure, never hidden.
UNLOADABLE_BEFORE_UNICODE_15_1: frozenset[tuple[str, str]] = frozenset(
    {
        ("ja", "3.13"),  # divmod: katakana middle dot U+30FB
        ("ja", "3.14"),
        ("si", "3.13"),  # conjuncts spelled with ZWJ U+200D
        ("si", "3.14"),
    }
)


def unloadable_here(code: str, version: str) -> str | None:
    """Why ``(code, version)`` cannot load on this interpreter, or None."""
    if IDENTIFIER_RULES_ARE_UNICODE_15_1:
        return None
    if (code, version) not in UNLOADABLE_BEFORE_UNICODE_15_1:
        return None
    return (
        f"{code} {version}: renderings that are identifiers only from Unicode "
        f"15.1 (CPython 3.13), and the schema validator checks "
        f"str.isidentifier() with this interpreter's tables "
        f"({unicodedata.unidata_version}); the pack file fails validation "
        "(tests/interpreter_gaps.py, gap 2)"
    )


def xfail_if_unloadable_here(
    request: pytest.FixtureRequest, code: str, version: str
) -> None:
    """Mark the running test xfail(strict) when gap 2 applies to it."""
    reason = unloadable_here(code, version)
    if reason:
        request.applymarker(pytest.mark.xfail(strict=True, reason=reason))
