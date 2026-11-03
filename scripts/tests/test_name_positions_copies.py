"""The engine and the language server carry one copy each of ``name_positions`` (CORE-2237).

``name_positions.py`` decides which names keep their spelling where a builtin's
name cannot be the builtin. The token engine (``legesher-core``) and the
language server's type-checker proxy (``legesher-language-server``) must apply
the same rule, or the type checker checks a different program from the one
``legesher run`` executes. The language server does not depend on
legesher-core, so the module ships in both packages, and the copies must be
the same bytes. ``libs/language-server/tests/test_proxy_engine_parity.py``
checks the behaviour; this checks the source, so a one-sided edit fails here
before it can drift.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COPIES = (
    Path("libs/core/legesher_core/name_positions.py"),
    Path("libs/language-server/legesher_language_server/name_positions.py"),
)


def test_both_copies_exist():
    missing = [str(path) for path in COPIES if not (ROOT / path).is_file()]
    assert not missing, f"missing: {missing}"


def test_the_copies_are_identical():
    engine, server = ((ROOT / path).read_bytes() for path in COPIES)
    assert engine == server, (
        f"{COPIES[1]} differs from {COPIES[0]}; edit both, or copy one over the other"
    )
