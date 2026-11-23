"""Reconcile the English baseline term sets against the running interpreter.

This is the durable guard that would have caught the two defects behind
CORE-1317: a *fabricated* exception (``basegeneratorexit``, which does not exist
in CPython) and a *missing* real one (``systemerror``). It resolves
``version_index`` (base terms from ``term_definitions`` + per-version deltas
from ``version-index.yml``) for the *running* Python version and compares each
category to ``keyword.kwlist`` / ``keyword.softkwlist`` and ``dir(builtins)`` —
the actual source of truth. Run under a matrix (e.g. 3.10 and 3.13) it validates
the per-version deltas as well as the base.

Every reconciliation runs against two sources. ``version-index`` is the index
file. ``term-definitions`` is the code-side inventory on its own
(``term_definitions.VERSION_ADDITIONS``), which registers a Python release
before the packs ship a tier for it, so it is checked against the interpreter
without waiting for the index.

Known, intentional deviations from a naive stdlib comparison are encoded as
explicit allowlists below; anything outside them fails the test.
"""

import builtins
import keyword
import sys

import pytest

from legesher_i18n.exceptions import UnsupportedVersionError
from legesher_i18n.term_definitions import (
    VERSION_ADDITIONS,
    get_builtins_for_version,
    get_exceptions_for_version,
    get_keywords_for_version,
)
from legesher_i18n.version_index import VersionIndex
from tests import language_packs_root

REAL_INDEX_PATH = language_packs_root() / "version-index.yml"
RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

SECTIONS = ("keywords", "builtins", "exceptions")


def _index() -> VersionIndex:
    return VersionIndex.load(REAL_INDEX_PATH)


def _version_key(version: str) -> tuple[int, int]:
    major, minor = version.split(".")[:2]
    return int(major), int(minor)


INDEXED_VERSIONS = sorted(_index().versions, key=_version_key)

# Releases the term inventory registers whose index entry has not landed.
#
# The index lists a release only once every pack ships a file for it: the pack
# tests and the review-template contract read the index as the list of tier
# files on disk. So the inventory learns a release first and the index entry
# follows with the pack tier. Until then the index cannot answer for that
# release, and the index-side cases below are strict xfails on it.
#
# An entry leaves this ledger in the change that adds the release to
# ``version-index.yml``; ``test_the_ledger_names_only_releases_the_index_lacks``
# fails on every interpreter until it does.
INDEX_ENTRY_PENDING = {
    "3.15": "the 3.15 index entry lands with the 3.15 pack tier [CORE-2833]",
}


def _index_marks() -> list:
    reason = INDEX_ENTRY_PENDING.get(RUNNING_VERSION)
    if reason is None:
        return []
    return [
        pytest.mark.xfail(strict=True, raises=UnsupportedVersionError, reason=reason)
    ]


def _index_pending(test):
    """Mark a test that reads the index at the running version."""
    for mark in _index_marks():
        test = mark(test)
    return test


def _index_terms() -> dict[str, set[str]]:
    return _index().get_all_terms(RUNNING_VERSION)


def _inventory_terms(version: str = RUNNING_VERSION) -> dict[str, set[str]]:
    return {
        "keywords": set(get_keywords_for_version(version)),
        "builtins": set(get_builtins_for_version(version)),
        "exceptions": set(get_exceptions_for_version(version)),
    }


@pytest.fixture(
    params=[
        pytest.param(_index_terms, id="version-index", marks=_index_marks()),
        pytest.param(_inventory_terms, id="term-definitions"),
    ]
)
def terms(request) -> dict[str, set[str]]:
    """The running interpreter's term sets, from each source in turn."""
    return request.param()


def _is_exception(obj) -> bool:
    return isinstance(obj, type) and issubclass(obj, BaseException)


def _stdlib_exceptions() -> set[str]:
    # Real ``BaseException`` subclasses exposed as builtins, lowercased.
    # Underscore-prefixed internals (e.g. ``_IncompleteInputError`` @3.13) are
    # implementation details Legesher deliberately does not translate.
    return {
        name.lower()
        for name in dir(builtins)
        if not name.startswith("_") and _is_exception(getattr(builtins, name))
    }


def _stdlib_keywords() -> set[str]:
    return {k.lower() for k in keyword.kwlist} | {k.lower() for k in keyword.softkwlist}


def _stdlib_builtins() -> set[str]:
    # Non-exception names in ``builtins``, lowercased. Dunder names are NOT
    # filtered out: two of them are pack terms (``__import__``, and
    # ``__lazy_import__`` from 3.15), and a scan that skipped dunders could
    # not tell a tracked one from one listed for the wrong release.
    return {
        name.lower()
        for name in dir(builtins)
        if not _is_exception(getattr(builtins, name))
    }


# --- documented, intentional deviations -----------------------------------

# Keywords Legesher does not translate: the ``_`` match-anything wildcard (a
# soft keyword that is not a nameable token). Legesher additionally carries
# ``except*`` as its own representation of the PEP 654 star form.
KEYWORDS_STDLIB_ONLY = {"_"}
KEYWORDS_LEGESHER_ONLY = {"except*"}

# Exceptions in the running interpreter that Legesher intentionally does not
# track: WindowsError is a Windows-only alias of OSError (absent from
# dir(builtins) on Linux/macOS), so it surfaces only on the Windows CI leg.
EXCEPTIONS_STDLIB_ONLY = {"windowserror"}

# Builtins Legesher intentionally does not track as builtins:
#  - REPL/site helpers injected by site.py that Legesher does not track
#    (copyright, credits, license, exit, quit)
#  - True/False/None: tracked as keywords (their real token category)
#  - the ``builtins`` module's own attributes (``__doc__``, ``__name__``,
#    ``__package__``, ``__spec__``, ``__loader__``), the ``__debug__``
#    constant, and ``__build_class__``, which the ``class`` statement calls
#    and nobody writes. None is a word a programmer types.
# ``type`` is tracked BOTH as a builtin (BUILTIN_TYPES) and as the PEP 695
# keyword (@3.12) since CORE-1400 — the two are distinct pack slots.
# NOTE: names Legesher DOES track (e.g. `help`) must NOT be listed here — an
# allowlist entry for a tracked name would mask a real "term dropped" defect.
BUILTINS_STDLIB_ONLY = {
    "copyright",
    "credits",
    "license",
    "exit",
    "quit",
    "true",
    "false",
    "none",
    "__build_class__",
    "__debug__",
    "__doc__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}


def test_the_ledger_names_only_releases_the_index_lacks():
    # Runs on every interpreter, so the change that adds a release to the
    # index cannot leave its ledger entry behind (the strict xfails alone
    # would only notice on that release's own interpreter).
    stale = sorted(set(INDEX_ENTRY_PENDING) & set(INDEXED_VERSIONS))
    assert stale == [], f"indexed now, remove from INDEX_ENTRY_PENDING: {stale}"
    # A ledger entry must be a release the inventory really registers, newer
    # than every indexed one. Anything else is a hole in the index, not a
    # pending entry, and must fail in the open.
    newest_indexed = _version_key(INDEXED_VERSIONS[-1])
    for version in INDEX_ENTRY_PENDING:
        assert version in VERSION_ADDITIONS, version
        assert _version_key(version) > newest_indexed, version


def test_every_release_the_inventory_registers_is_indexed_or_pending():
    unaccounted = sorted(
        set(VERSION_ADDITIONS) - set(INDEXED_VERSIONS) - set(INDEX_ENTRY_PENDING)
    )
    assert unaccounted == [], unaccounted


@pytest.mark.parametrize("version", INDEXED_VERSIONS)
@pytest.mark.parametrize("section", SECTIONS)
def test_term_definitions_agree_with_the_index_at_every_indexed_version(
    version, section
):
    # Not only at the running version: the two copies must agree for every
    # release the index lists, on whichever interpreter runs the suite.
    assert (
        _inventory_terms(version)[section] == _index().get_all_terms(version)[section]
    )


class TestExceptionsAgainstStdlib:
    """Exceptions must be exactly the real stdlib set — no fabrications, no gaps."""

    def test_no_fabricated_exceptions(self, terms):
        leg = terms["exceptions"]
        fabricated = leg - _stdlib_exceptions()
        assert not fabricated, (
            f"Legesher lists exception(s) with no CPython counterpart on "
            f"{RUNNING_VERSION}: {sorted(fabricated)} "
            f"(this is exactly the 'basegeneratorexit' class of defect)."
        )

    def test_no_missing_exceptions(self, terms):
        leg = terms["exceptions"]
        missing = _stdlib_exceptions() - leg - EXCEPTIONS_STDLIB_ONLY
        assert not missing, (
            f"Real CPython exception(s) absent from the Legesher baseline on "
            f"{RUNNING_VERSION}: {sorted(missing)} "
            f"(this is exactly the missing-'systemerror' class of defect)."
        )

    @_index_pending
    def test_term_definitions_mirror_version_index(self):
        # The per-release lists in term_definitions (used by classify_term)
        # must agree with version-index.yml for the running interpreter.
        assert _inventory_terms() == _index_terms()


class TestKeywordsAgainstStdlib:
    def test_keywords_reconcile(self, terms):
        leg = {k.lower() for k in terms["keywords"]}
        std = _stdlib_keywords()
        assert std - leg <= KEYWORDS_STDLIB_ONLY, (
            f"unexpected missing keywords: {sorted((std - leg) - KEYWORDS_STDLIB_ONLY)}"
        )
        assert leg - std <= KEYWORDS_LEGESHER_ONLY, (
            f"unexpected extra keywords: {sorted((leg - std) - KEYWORDS_LEGESHER_ONLY)}"
        )


class TestBuiltinsAgainstStdlib:
    def test_no_fabricated_builtins(self, terms):
        leg = {b.lower() for b in terms["builtins"]}
        fabricated = leg - _stdlib_builtins()
        assert not fabricated, (
            f"Legesher lists builtin(s) not in CPython {RUNNING_VERSION}: "
            f"{sorted(fabricated)}"
        )

    def test_builtins_reconcile(self, terms):
        leg = {b.lower() for b in terms["builtins"]}
        missing = _stdlib_builtins() - leg
        assert missing <= BUILTINS_STDLIB_ONLY, (
            f"unexpected missing builtins: {sorted(missing - BUILTINS_STDLIB_ONLY)}"
        )
