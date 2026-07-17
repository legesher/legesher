"""Test package for legesher-i18n.

Shared helpers for locating shipped packs on disk. Centralising the
``language-packs/<target>`` root and the ``legesher_i18n_<target>_<lang>``
module-directory convention here keeps the programming-language *target* out of
individual test path literals (CORE-1372): the default is ``python`` today, and
a single edit retargets every path-hardcoded test rather than N scattered ones.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_TARGET = "python"

# libs/i18n — the package root holding both ``legesher_i18n`` and
# ``language-packs``. This file is tests/__init__.py, so parent.parent is libs/i18n.
I18N_ROOT = Path(__file__).resolve().parent.parent


def language_packs_root(target: str = DEFAULT_TARGET) -> Path:
    """Return the on-disk ``language-packs/<target>`` root."""
    return I18N_ROOT / "language-packs" / target


def pack_module_dir_name(lang: str, target: str = DEFAULT_TARGET) -> str:
    """Return the per-language module directory name (``legesher_i18n_<target>_<lang>``)."""
    return f"legesher_i18n_{target}_{lang}"


def pack_file(lang: str, version: str, target: str = DEFAULT_TARGET) -> Path:
    """Return the path to a concrete pack YAML on disk."""
    return (
        language_packs_root(target)
        / lang
        / pack_module_dir_name(lang, target)
        / "packs"
        / f"{version}.yml"
    )
