"""The VS Code extension's icon fits the Marketplace's size limit.

The Visual Studio Marketplace rejects a package whose icon is larger than
1024 by 1024 pixels, and it rejects it at publish time, after the version has
been tagged and released on GitHub. A release built with the 2006 by 2006
icon could not be published at all. This guard reads the PNG header of the
icon ``libs/vs-code/package.json`` names and fails before the release does,
naming the file and its size.

Run with:  uv run pytest scripts/tests -q
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXTENSION = REPO / "libs/vs-code"
MARKETPLACE_MAX = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _icon_path() -> Path:
    manifest = json.loads((EXTENSION / "package.json").read_text(encoding="utf-8"))
    return EXTENSION / manifest["icon"]


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert header[:8] == PNG_SIGNATURE, f"{path.relative_to(REPO)} is not a PNG"
    assert header[12:16] == b"IHDR", f"{path.relative_to(REPO)} has no IHDR chunk first"
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def test_icon_fits_the_marketplace_limit() -> None:
    icon = _icon_path()
    width, height = _png_size(icon)
    assert width <= MARKETPLACE_MAX and height <= MARKETPLACE_MAX, (
        f"{icon.relative_to(REPO)} is {width}x{height}; the Marketplace rejects icons "
        f"larger than {MARKETPLACE_MAX}x{MARKETPLACE_MAX}"
    )


def test_icon_is_square() -> None:
    icon = _icon_path()
    width, height = _png_size(icon)
    assert width == height, f"{icon.relative_to(REPO)} is {width}x{height}, not square"
