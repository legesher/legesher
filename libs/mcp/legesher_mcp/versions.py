"""The supported-Python-version index, derived from the installed packs.

The set of Python grammar versions this server can serve is a property of
the language packs on disk, not of this source file: a pack ships one
``{X.Y}.yml`` per version it covers, and their union is the index. Deriving
the version enum from that index means shipping packs for a new Python
version needs no schema edit here.

Timing: the index is read ONCE at import. The published tool schema has to
stay stable for the life of a session — clients cache it from the
``initialize`` handshake — so a pack installed mid-process does not widen
the accepted versions until restart. Pack *availability* per language is a
different question and is refreshable at runtime (see
``LocalEngine.refresh_packs``).
"""

from __future__ import annotations

from legesher_i18n.pack_loader import LanguagePackLoader

#: The version the tools default to when the caller does not say.
DEFAULT_PYTHON_VERSION = "3.13"

#: Used only when pack discovery finds nothing at all — a bare install with
#: no language packs yet. Publishing an empty enum would make every tool
#: call unschedulable; publishing the documented baseline lets calls through
#: to the engine, which answers with a sanitized ``language_pack_not_found``.
_FALLBACK_VERSIONS: tuple[str, ...] = ("3.10", "3.11", "3.12", "3.13", "3.14")


def _version_sort_key(version: str) -> tuple[int, ...]:
    """Numeric sort so 3.9 precedes 3.10 (string order gets this wrong)."""
    return tuple(int(part) for part in version.split("."))


def discover_python_versions() -> tuple[str, ...]:
    """Python versions covered by the installed packs, numerically sorted.

    Never raises and never returns an empty tuple: discovery touches the
    filesystem and the installed-distribution list, and a server that
    cannot import is worse than one that publishes the baseline.
    """
    try:
        discovered = tuple(LanguagePackLoader().list_available_versions("python"))
    except Exception:  # pragma: no cover — discovery is best-effort at import
        discovered = ()

    if not discovered:
        return _FALLBACK_VERSIONS
    if DEFAULT_PYTHON_VERSION not in discovered:
        # The tools' default must be a member of the published enum or
        # pydantic rejects the parameter default and the server never boots.
        return tuple(sorted({*discovered, DEFAULT_PYTHON_VERSION}, key=_version_sort_key))
    return discovered


#: Python grammar versions with language-pack coverage in this environment.
SUPPORTED_PYTHON_VERSIONS: tuple[str, ...] = discover_python_versions()
