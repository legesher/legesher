"""Arabic language pack for Python in Legesher.

This package provides Arabic translations for Python keywords and built-ins,
supporting Python versions 3.10 through 3.13.

Special considerations for Arabic:
- Right-to-left (RTL) text direction
- Arabic script rendering
- Cultural programming terminology
"""

__version__ = "0.0.1"

from pathlib import Path

# Package metadata
LANGUAGE = "ar"
TARGET = "python"
PACK_DIR = Path(__file__).parent / "packs"
RTL = True  # Right-to-left language

__all__ = ["__version__", "LANGUAGE", "TARGET", "PACK_DIR", "RTL"]
