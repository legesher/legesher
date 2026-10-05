"""Identifier rules before Unicode 15.1, pinned once for the i18n suite.

The full record of the interpreter gaps lives in ``libs/core/tests/
interpreter_gaps.py`` (gap 2 there). Package test suites cannot import each
other's ``tests`` package, so this module carries the one fact the i18n suite
needs:

Unicode 15.1 added ZWJ, ZWNJ and the katakana middle dot to
``Other_ID_Continue``, and CPython 3.13 is the first release with those
tables. The schema validator and the exporter's publishable-identifier check
use the RUNNING interpreter's ``str.isidentifier()``, so on 3.10 through 3.12
they reject the ``si`` 3.13+ conjuncts (ZWJ, CORE-1521) and the ``ja`` 3.13+
``divmod`` (U+30FB, CORE-1905), and everything built on them: the 3.13 tier
files, and the tooling that exports every tier. That tooling runs on 3.13+ by
design (CORE-1972). Not a defect, but a fact every test that loads or exports
a 3.13+ form on an older interpreter has to know (CORE-2334).
"""

from __future__ import annotations

import unicodedata

import pytest

#: The running interpreter's Unicode tables, as a comparable tuple.
UNICODE_VERSION: tuple[int, ...] = tuple(
    int(part) for part in unicodedata.unidata_version.split(".")
)

#: True where ZWJ, ZWNJ and U+30FB are identifier characters (CPython 3.13+).
IDENTIFIER_RULES_ARE_UNICODE_15_1: bool = UNICODE_VERSION >= (15, 1)

#: Strict, so a test that starts passing on an older interpreter (a 3.13+
#: form dropped from the packs, say) reports XPASS instead of hiding.
NEEDS_UNICODE_15_1 = pytest.mark.xfail(
    not IDENTIFIER_RULES_ARE_UNICODE_15_1,
    strict=True,
    reason=(
        "needs Unicode 15.1 identifier rules (CPython 3.13+): this interpreter's "
        f"tables ({unicodedata.unidata_version}) reject the si ZWJ conjuncts and "
        "the ja katakana middle dot (tests/interpreter_gaps.py; core's gap 2)"
    ),
)
