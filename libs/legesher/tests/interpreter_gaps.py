"""Interpreter-version gaps, pinned once for the CLI suite (CORE-2192).

The full record lives in ``libs/core/tests/interpreter_gaps.py``. Package test
suites cannot import each other's ``tests`` package, so this module carries the
part the CLI suite needs, under the same name (as ``libs/mcp/tests`` does):

1. The pure-Python tokenizer (CPython 3.10 and 3.11) reads a rendering that
   carries a combining mark or a joiner as NAME/ERRORTOKEN fragments, so the
   return hop never matches it. ``legesher run`` and the git clean filter both
   tokenize the file they are given, so on those interpreters a program in
   such a script neither runs nor has a stray keyword normalized.
"""

from __future__ import annotations

import io
import sys
import tokenize
from collections import Counter

import pytest

#: The interpreter running the suite, as ``X.Y``.
RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

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


def xfail_if_return_hop_is_inert(
    request: pytest.FixtureRequest, source: str, native: str
) -> None:
    """Mark the running test xfail(strict) when gap 1 applies to it.

    Decided from the actual renderings: any fragment the native form has and
    the source does not came from a translated token, which the return hop
    then never matches, so the failure is exactly predicted. Strict, so a
    case that starts passing on an older interpreter reports XPASS.
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
