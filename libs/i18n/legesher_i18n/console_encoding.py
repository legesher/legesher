"""Make standard output safe for text that is not plain ASCII.

Windows Python does not default ``sys.stdout`` to UTF-8. When stdout is a
pipe rather than a console — which is what a subprocess, a pre-commit hook
and a CI step all hand it — the encoding falls back to the machine's ANSI
code page (``cp1252`` on GitHub's runners). Printing any character outside
that page then raises ``UnicodeEncodeError`` from inside ``print`` itself.

That failure mode is nastier than it sounds, because the program dies
*while describing what it did*, so the exit code describes the reporting
rather than the work. CORE-1927: ``validate_language_pack_yaml.py`` ran a
pack through every check, passed, then died on
``print("\N{WHITE HEAVY CHECK MARK} All language packs valid")`` and exited
1 with an empty stdout. A valid pack was reported invalid; an invalid one
produced no error text at all, because the same crash hit the line that
prints the errors.

This matters most for a project whose whole subject is non-English text.
Every language pack is full of characters cp1252 has never heard of, and a
contributor on Windows is exactly the person we cannot afford to greet
with a traceback about a code page.
"""

from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    """Re-encode ``sys.stdout`` and ``sys.stderr`` as UTF-8.

    Call once at an entry point, before anything prints. Idempotent, and a
    no-op where the streams already speak UTF-8 — which is every POSIX
    default, so this costs nothing on the platforms it is not for.

    ``errors="replace"`` is deliberate. The point is that no output
    statement may ever be the thing that kills the process: if a stream
    somehow cannot represent a character, the right outcome is a ``?`` and
    a program that keeps running, not an abort.

    Streams that cannot be reconfigured are skipped rather than forced.
    ``sys.stdout`` is not always a ``TextIOWrapper`` — pytest's capture
    replaces it, as do embedding hosts — and a missing ``reconfigure`` is a
    normal condition there, not an error.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):  # pragma: no cover - stream-dependent
            # A detached or already-closed stream. Printing is about to be
            # the least of the caller's problems; do not add to them.
            pass
