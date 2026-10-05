"""Interpreter-version gaps, pinned once for the MCP suite (CORE-2334).

The full record lives in ``libs/core/tests/interpreter_gaps.py``. Package test
suites cannot import each other's ``tests`` package, so this module carries
the parts the MCP suite needs, under the same names:

1. The pure-Python tokenizer (CPython 3.10 and 3.11) reads a rendering that
   carries a combining mark or a joiner as NAME/ERRORTOKEN fragments, so the
   return hop never matches it (CORE-2192).
2. Identifier rules before Unicode 15.1 (CPython 3.10 to 3.12) reject the
   ``si`` ZWJ conjuncts and the ``ja`` katakana middle dot that the 3.13+
   pack files carry.

And one fact about the corpus: the server translates for a target grammar
(``python_version``), but it compiles and tokenizes with the interpreter it
runs on, so a sweep can only cover the files this interpreter can compile.
"""

from __future__ import annotations

import io
import sys
import tokenize
import unicodedata
from collections import Counter

import pytest

#: The interpreter running the suite, as ``X.Y``.
RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


def _parts(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def grammar_this_interpreter_can_compile(target: str) -> str:
    """The lower of ``target`` and the running interpreter's version."""
    return min(target, RUNNING_VERSION, key=_parts)


# -- gap 1: the pure-Python tokenizer -----------------------------------------

#: True where ``tokenize`` spells NAME as ``\\w+`` (CPython < 3.12).
PURE_PYTHON_TOKENIZER: bool = sys.version_info < (3, 12)


def _error_tokens(source: str) -> Counter[str]:
    try:
        return Counter(
            token.string
            for token in tokenize.generate_tokens(io.StringIO(source).readline)
            if token.type == tokenize.ERRORTOKEN
        )
    except tokenize.TokenError:
        return Counter()


def xfail_if_return_hop_is_inert(request: pytest.FixtureRequest, source: str, native: str) -> None:
    """Mark the running test xfail(strict) when gap 1 applies to it.

    Decided from the actual renderings: any fragment the native form has and
    the source does not came from a translated token, which the return hop
    then never matches, so byte-identity is exactly predicted to fail.
    """
    if not PURE_PYTHON_TOKENIZER:
        return
    fragments = sorted((_error_tokens(native) - _error_tokens(source)).elements())
    if fragments:
        shown = ", ".join(f"U+{ord(ch):04X}" for ch in dict.fromkeys(fragments))
        request.applymarker(
            pytest.mark.xfail(
                strict=True,
                reason=(
                    f"CORE-2192: pure-Python tokenize (CPython {RUNNING_VERSION}) "
                    f"reads {shown} as ERRORTOKEN fragments, so the return hop "
                    "never matches the rendering they belong to "
                    "(tests/interpreter_gaps.py, gap 1)"
                ),
            )
        )


# -- gap 2: identifier rules before Unicode 15.1 -------------------------------

#: True where ZWJ, ZWNJ and U+30FB are identifier characters (CPython 3.13+).
IDENTIFIER_RULES_ARE_UNICODE_15_1: bool = tuple(
    int(part) for part in unicodedata.unidata_version.split(".")
) >= (15, 1)

#: Strict, so a test that starts passing on an older interpreter reports XPASS.
NEEDS_UNICODE_15_1 = pytest.mark.xfail(
    not IDENTIFIER_RULES_ARE_UNICODE_15_1,
    strict=True,
    reason=(
        "needs Unicode 15.1 identifier rules (CPython 3.13+): this interpreter's "
        f"tables ({unicodedata.unidata_version}) reject the si ZWJ conjuncts and "
        "the ja katakana middle dot (tests/interpreter_gaps.py, gap 2)"
    ),
)
