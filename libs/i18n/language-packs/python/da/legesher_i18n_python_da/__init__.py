"""Danish language pack for Python in Legesher.

This package provides Danish translations for Python keywords and built-ins,
supporting Python versions 3.10 through 3.14.
"""

__version__ = "0.0.3"

from pathlib import Path

# Package metadata
LANGUAGE = "da"
TARGET = "python"
PACK_DIR = Path(__file__).parent / "packs"

__all__ = ["__version__", "LANGUAGE", "TARGET", "PACK_DIR"]
