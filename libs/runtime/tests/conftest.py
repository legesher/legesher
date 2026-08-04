"""Shared helpers: raise real exceptions from a controlled on-disk script."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


class Captured:
    def __init__(self, exc_info, path: Path):
        self.exc_type, self.exc_value, self.exc_tb = exc_info
        self.path = path

    def normalize(self, rendered: str) -> str:
        """Make renderer output stable: the tmp script path becomes script.py."""
        return rendered.replace(str(self.path), "script.py")


@pytest.fixture
def raise_from_script(tmp_path: Path):
    """Run ``code`` from a real file and capture the exception it raises.

    A real on-disk file keeps ``linecache`` honest, so the traceback carries
    the actual source lines (and their PEP 657 caret lines) exactly as a user
    would see them.
    """

    def _raise(code: str) -> Captured:
        path = tmp_path / "script.py"
        path.write_text(code, encoding="utf-8")
        compiled = compile(code, str(path), "exec")
        try:
            exec(compiled, {"__name__": "__main__"})  # noqa: S102
        except BaseException:
            return Captured(sys.exc_info(), path)
        raise AssertionError("script did not raise")

    return _raise
