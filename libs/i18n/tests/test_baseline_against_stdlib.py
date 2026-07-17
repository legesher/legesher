"""Reconcile the English baseline term sets against the running interpreter.

This is the durable guard that would have caught the two defects behind
CORE-1317: a *fabricated* exception (``basegeneratorexit``, which does not exist
in CPython) and a *missing* real one (``systemerror``). It resolves
``version_index`` (base terms from ``term_definitions`` + per-version deltas
from ``version-index.yml``) for the *running* Python version and compares each
category to ``keyword.kwlist`` / ``keyword.softkwlist`` and ``dir(builtins)`` —
the actual source of truth. Run under a matrix (e.g. 3.10 and 3.13) it validates
the per-version deltas as well as the base.

Known, intentional deviations from a naive stdlib comparison are encoded as
explicit allowlists below; anything outside them fails the test.
"""

import builtins
import keyword
import sys

from legesher_i18n.version_index import VersionIndex
from legesher_i18n.term_definitions import get_exceptions_for_version
from tests import language_packs_root

REAL_INDEX_PATH = language_packs_root() / "version-index.yml"
RUNNING_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


def _index() -> VersionIndex:
    return VersionIndex.load(REAL_INDEX_PATH)


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
    # Non-exception, non-dunder names in ``builtins``, lowercased.
    return {
        name.lower()
        for name in dir(builtins)
        if not (name.startswith("__") and name.endswith("__"))
        and not _is_exception(getattr(builtins, name))
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
#  - type: tracked as the PEP 695 keyword (@3.12)
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
    "type",
}


class TestExceptionsAgainstStdlib:
    """Exceptions must be exactly the real stdlib set — no fabrications, no gaps."""

    def test_no_fabricated_exceptions(self):
        leg = _index().get_all_exceptions(RUNNING_VERSION)
        fabricated = leg - _stdlib_exceptions()
        assert not fabricated, (
            f"Legesher lists exception(s) with no CPython counterpart on "
            f"{RUNNING_VERSION}: {sorted(fabricated)} "
            f"(this is exactly the 'basegeneratorexit' class of defect)."
        )

    def test_no_missing_exceptions(self):
        leg = _index().get_all_exceptions(RUNNING_VERSION)
        missing = _stdlib_exceptions() - leg - EXCEPTIONS_STDLIB_ONLY
        assert not missing, (
            f"Real CPython exception(s) absent from the Legesher baseline on "
            f"{RUNNING_VERSION}: {sorted(missing)} "
            f"(this is exactly the missing-'systemerror' class of defect)."
        )

    def test_term_definitions_mirror_version_index(self):
        # EXCEPTIONS_3_11 / EXCEPTIONS_3_13 (term_definitions, used by
        # classify_term) must agree with version-index.yml added_exceptions.
        assert set(
            get_exceptions_for_version(RUNNING_VERSION)
        ) == _index().get_all_exceptions(RUNNING_VERSION)


class TestKeywordsAgainstStdlib:
    def test_keywords_reconcile(self):
        leg = {k.lower() for k in _index().get_all_keywords(RUNNING_VERSION)}
        std = _stdlib_keywords()
        assert std - leg <= KEYWORDS_STDLIB_ONLY, (
            f"unexpected missing keywords: {sorted((std - leg) - KEYWORDS_STDLIB_ONLY)}"
        )
        assert leg - std <= KEYWORDS_LEGESHER_ONLY, (
            f"unexpected extra keywords: {sorted((leg - std) - KEYWORDS_LEGESHER_ONLY)}"
        )


class TestBuiltinsAgainstStdlib:
    def test_no_fabricated_builtins(self):
        leg = {b.lower() for b in _index().get_all_builtins(RUNNING_VERSION)}
        fabricated = leg - _stdlib_builtins()
        assert not fabricated, (
            f"Legesher lists builtin(s) not in CPython: {sorted(fabricated)}"
        )

    def test_builtins_reconcile(self):
        leg = {b.lower() for b in _index().get_all_builtins(RUNNING_VERSION)}
        missing = _stdlib_builtins() - leg
        assert missing <= BUILTINS_STDLIB_ONLY, (
            f"unexpected missing builtins: {sorted(missing - BUILTINS_STDLIB_ONLY)}"
        )
