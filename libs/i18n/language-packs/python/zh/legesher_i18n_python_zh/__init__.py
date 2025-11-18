"""Chinese (Simplified) language pack for Python in Legesher.

This package provides Chinese (Simplified) translations for Python keywords and built-ins,
supporting Python versions 3.10 through 3.13.
"""

__version__ = "0.0.2"

from pathlib import Path

# Package metadata
LANGUAGE = "zh"
TARGET = "python"
PACK_DIR = Path(__file__).parent / "packs"
RTL = False

__all__ = ["__version__", "LANGUAGE", "TARGET", "PACK_DIR", "RTL"]
