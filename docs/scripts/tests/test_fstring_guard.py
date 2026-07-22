"""The generator must import on Python 3.10+ (CORE-1574).

`tokenize.FSTRING_START/MIDDLE/END` exist only on Python 3.12+ (PEP 701). The
snippet generator builds its token-category map with `getattr` so that an older
build-image `python3` — e.g. Vercel's — does not raise `AttributeError` at
import and fail the docs build. This test simulates that older interpreter by
removing the FSTRING attributes in a subprocess before importing the module.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]


def test_generator_imports_without_fstring_token_types():
    """Deleting the 3.12+ FSTRING token types must not break the import."""
    script = textwrap.dedent(
        f"""
        import sys, tokenize
        # Simulate a pre-3.12 interpreter: these attributes do not exist there.
        for _name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
            if hasattr(tokenize, _name):
                delattr(tokenize, _name)
        sys.path.insert(0, {str(SCRIPTS_DIR)!r})
        import generate_snippets as g
        cats = set(g._TOKEN_CATEGORIES.values())
        assert cats == {{"string", "comment", "number"}}, cats
        # No FSTRING token type leaked into the map.
        assert all(t is not None for t in g._TOKEN_CATEGORIES), g._TOKEN_CATEGORIES
        print("ok")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"import failed without FSTRING:\n{result.stderr}"
    assert "ok" in result.stdout
