"""Macedonian language pack for Python in Legesher."""

from pathlib import Path

__version__ = "0.0.2"

LANGUAGE = "mk"
TARGET = "python"
PACK_DIR = Path(__file__).parent / "packs"

__all__ = ["__version__", "LANGUAGE", "TARGET", "PACK_DIR"]
