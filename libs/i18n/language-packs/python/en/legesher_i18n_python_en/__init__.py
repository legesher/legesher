"""English language pack for Python in Legesher.

This package provides English translations for Python keywords and built-ins,
supporting Python versions 3.10 through 3.13.
"""

__version__ = "0.0.4"

from pathlib import Path

# Package metadata
LANGUAGE = "en"
TARGET = "python"
PACK_DIR = Path(__file__).parent / "packs"
RTL = False

__all__ = ["__version__", "LANGUAGE", "TARGET", "PACK_DIR", "RTL"]
