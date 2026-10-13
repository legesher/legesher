"""The mechanical verdict on one candidate rendering (CORE-1514, CORE-1400).

Extracted from ``scripts/migrate_to_v2.py`` for CORE-1688: the review-bundle
importer must run the SAME checks the migration runs — two validator
implementations would eventually disagree, and the canon gate
(``trg_canon_requires_valid_identifier``) trusts whatever is cached in
``option_validations``. The migration script re-imports everything here, so
its behaviour (and its test suite, ``tests/test_v2_validation_gate.py``) is
unchanged.

The checks are the ones the canon trigger gates on:

* ``identifier_valid`` — Python's own rule made term-aware, so ``except*``
  keeps its structural ``*`` in every locale (PEP 654) without blanket-passing
  a stray asterisk anywhere else.
* ``nfkc_stable`` + ``nfkc_delta_class`` — the fact and the reason; the
  SARA-AM allowance is canon POLICY, never a weakening of the fact.
* ``script_consistent`` — per-character, locale-aware, default-deny.
* ``collides_en_keyword`` — the rendering must not shadow an English keyword.
* ``format_chars_clean`` — no forbidden format / Default_Ignorable character
  outside the locale's ``allowed_format_chars`` policy (CORE-2029; the same
  net the CORE-1591 pack gate runs).
"""

from __future__ import annotations

import keyword
import unicodedata
from dataclasses import dataclass

from legesher_i18n.script_policy import (
    ALWAYS_ALLOWED_SCRIPTS,
    FORBIDDEN_FORMAT_CHARS,
    has_policy,
    is_default_ignorable,
    nfkc_delta_class,
    policy_for,
    scripts_of,
)

__all__ = [
    "NON_PACK_SCRIPTS",
    "SUBTAG_POLICY_ALIASES",
    "VALIDATOR_VERSION",
    "Validation",
    "allowed_format_chars_for",
    "allowed_scripts_for",
    "format_char_violations",
    "validate_surface",
]

#: The validator that actually runs (see :func:`validate_surface`). It is a real
#: version string, NOT the reserved 'migration-seed' -- the canon trigger rejects
#: that value precisely so a stamped row can never pass for a checked one. Bumped
#: to v2 for the CORE-1514 fixes: term-aware identifiers, the SARA-AM NFKC delta
#: class, and real locale-aware script-consistency. Bumped to v3 for CORE-2029:
#: the policy-aware format-char / Default_Ignorable net now runs here too.
VALIDATOR_VERSION = "py-identifier-v3"


@dataclass(frozen=True)
class Validation:
    """The mechanical verdict on one rendering."""

    identifier_valid: bool
    nfkc_stable: bool
    #: WHY the value is NFKC-unstable, or None when it is stable. A fact, kept
    #: separate from the canon policy that acts on it (see validate_surface).
    nfkc_delta_class: str | None
    script_consistent: bool
    collides_en_keyword: bool
    #: No forbidden format / Default_Ignorable character outside the locale's
    #: ``allowed_format_chars`` policy (CORE-2029; the intake half of the
    #: CORE-1591 pack gate). These characters render as nothing yet many are
    #: ``.isidentifier()``-True, NFKC-stable, and script-Inherited, so every
    #: OTHER check here passes them — which is exactly the payload class.
    format_chars_clean: bool


#: Base scripts for the DB languages that do NOT ship a pack yet, so the v2
#: validator can classify their options. ``script_policy.SCRIPT_POLICIES`` is
#: keyed to shipped packs only (``tests/test_script_policy_coverage.py`` forbids
#: orphan entries), so these live here until they ship. Same set as
#: ``migrate_to_v2.BCP47_FALLBACK``.
NON_PACK_SCRIPTS: dict[str, frozenset[str]] = {
    "ne": frozenset({"Devanagari"}),  # Nepali
    "sw": frozenset({"Latin"}),  # Swahili
    "tl": frozenset({"Latin"}),  # Tagalog
    "uk": frozenset({"Cyrillic"}),  # Ukrainian
    "xh": frozenset({"Latin"}),  # Xhosa
}

#: The v2 reference layer names some languages by their BCP 47 subtag while
#: the policy tables are keyed by pack id / v1 code (the pack-id divergences
#: the locales card documents: ``no`` is BCP 47 ``nb``, and v2 calls v1's
#: ``tl`` by its modern subtag ``fil``). Without this mapping an ``nb`` or
#: ``fil`` rendering resolves to NO policy and default-denies as
#: script-inconsistent — which is a misclassification of the locale, not a
#: verdict about the word (CORE-1973 found 290 stored verdicts disagreeing
#: with recomputation for exactly this reason).
SUBTAG_POLICY_ALIASES: dict[str, str] = {
    "fil": "tl",  # Filipino/Tagalog: v2 subtag vs the v1 code the tables use
    "nb": "no",  # Norwegian Bokmål: BCP 47 subtag vs the pack id
}


def allowed_scripts_for(code: str) -> frozenset[str] | None:
    """Resolve the Unicode scripts a locale's identifiers may legitimately use.

    Reads the shared, default-deny ``script_policy`` table -- the single source
    of truth the pack auditor also uses, so the v2 validator and the pack audit
    finally agree on what "foreign script" means -- falling back to
    :data:`NON_PACK_SCRIPTS` for the handful of DB-only languages. Returns
    ``None`` for an un-policied code, which the script check treats as a
    violation, never a silent pass.

    Args:
        code: The v1 two-letter language code (``th``, ``ja``, ``no``).

    Returns:
        The allowed scripts, or ``None`` if the code has no policy.
    """
    code = SUBTAG_POLICY_ALIASES.get(code, code)
    if has_policy(code):
        return policy_for(code).scripts
    return NON_PACK_SCRIPTS.get(code)


def allowed_format_chars_for(code: str) -> frozenset[str]:
    """The format characters a locale's identifiers may legitimately carry.

    Resolves exactly as the CORE-1591 pack gate
    (:meth:`legesher_i18n.schema_validator.SchemaValidator.check_format_chars`)
    does: the language's ``allowed_format_chars`` policy entry when one is
    registered (today the Sinhala ZWJ and the Persian/Urdu ZWNJ), and the
    EMPTY set — deny every format char — for an un-policied code. The
    :data:`NON_PACK_SCRIPTS` languages have no policy entry and therefore no
    hole punched, which is correct: none of their orthographies requires one.

    Args:
        code: The language code (``ur``, ``si``, ``th``).

    Returns:
        The allow-listed format characters; empty means deny all.
    """
    code = SUBTAG_POLICY_ALIASES.get(code, code)
    return policy_for(code).allowed_format_chars if has_policy(code) else frozenset()


def format_char_violations(
    surface: str, allowed_format_chars: frozenset[str]
) -> list[str]:
    """The forbidden format / invisible characters present in *surface*.

    The same net, with the same policy semantics, as the pack layer's
    ``check_format_chars`` (CORE-1591): a character the locale explicitly
    allow-lists passes; anything in
    :data:`~legesher_i18n.script_policy.FORBIDDEN_FORMAT_CHARS` (bidi
    controls, tatweel, BOM) or of Unicode category ``Cf``, plus the full
    Default_Ignorable_Code_Point set
    (:func:`~legesher_i18n.script_policy.is_default_ignorable` — U+034F, the
    Hangul fillers, the variation selectors, …), is a violation. The
    non-``Cf`` default-ignorables are the point: they are invisible,
    ``.isidentifier()``-True, NFKC-stable, and script-Inherited, so no other
    mechanical check sees them.

    Args:
        surface: The candidate rendering.
        allowed_format_chars: The locale's policy allowlist
            (:func:`allowed_format_chars_for`).

    Returns:
        The offending characters, deduplicated, in code-point order. Empty
        means the surface is clean.
    """
    violations: list[str] = []
    for ch in sorted(set(surface)):
        if ch in allowed_format_chars:
            continue
        if (
            ch in FORBIDDEN_FORMAT_CHARS
            or unicodedata.category(ch) == "Cf"
            or is_default_ignorable(ch)
        ):
            violations.append(ch)
    return violations


def _is_identifier_char(char: str) -> bool:
    """Whether ``char`` may appear inside a Python identifier (letters/digits/_)."""
    return char == "_" or char.isalnum()


def _structural_affixes(term_name: str) -> tuple[str, str]:
    """The leading/trailing NON-identifier characters the source term carries.

    A faithful translation of ``except*`` (PEP 654) must keep the trailing
    ``*``; the identifier check validates the *stem* and requires the surface to
    mirror these affixes. Today ``except*`` is the only term that exercises this,
    but the logic generalizes to any structural affix (a future ``*args``). A
    term that is already a valid identifier -- every dunder included -- has none.
    """
    start = 0
    while start < len(term_name) and not _is_identifier_char(term_name[start]):
        start += 1
    end = len(term_name)
    while end > start and not _is_identifier_char(term_name[end - 1]):
        end -= 1
    return term_name[:start], term_name[end:]


def _identifier_valid(surface: str, term_name: str) -> bool:
    """Term-aware Python-identifier check.

    A plain ``str.isidentifier()`` refuses ``except*`` in every locale forever
    (the literal ``*``) and would blanket-accept a stray ``*`` on any other term.
    Instead, carry the structural affixes of the SOURCE term: the surface must
    mirror them exactly, and the stem between them must be a valid identifier.
    """
    prefix, suffix = _structural_affixes(term_name)
    if not surface.startswith(prefix) or not surface.endswith(suffix):
        return False
    if len(surface) < len(prefix) + len(suffix):
        return False
    stem = (
        surface[len(prefix) : len(surface) - len(suffix)]
        if suffix
        else surface[len(prefix) :]
    )
    return stem.isidentifier()


def _script_consistent(surface: str, allowed_scripts: frozenset[str] | None) -> bool:
    """Real, per-character, locale-aware script-consistency.

    Every letter's script must fall within the locale's allowlist (``Common``
    and ``Inherited`` are always allowed). This is the honest version of the old
    ``len(scripts) <= 1`` heuristic, which was wrong in both directions: it
    passed an NFKC-stable Cyrillic-in-Thai confusable, and it flagged legitimate
    Japanese (Han + Kana). An un-policied locale is default-deny.
    """
    if allowed_scripts is None:
        return False
    present = scripts_of(surface) - ALWAYS_ALLOWED_SCRIPTS
    return present <= allowed_scripts


def validate_surface(
    surface: str,
    term_name: str,
    allowed_scripts: frozenset[str] | None,
    allowed_format_chars: frozenset[str] = frozenset(),
) -> Validation:
    """Run the mechanical checks the canon trigger gates on.

    This is the honest version of what the migration used to *stamp*. The
    previous script wrote ``identifier_valid = 1, nfkc_stable = 1`` for every
    canon-bound row under ``validator_version = 'migration-seed'`` without
    running anything, which made the CORE-1400 gate circular: "pack_export
    reproduces all 5,136 selections" was true *because the gate was bypassed*.
    Two real defects were hiding under the stamp (Amharic ``ከቀረ*``, and 25
    NFKC-unstable Thai renderings) -- and the Q7 triage (CORE-1514) then found
    the honest v1 check was itself over- AND under-inclusive: it refused all 25
    of those Thai SARA-AM selections and every locale's ``except*``, while
    passing 12 of 15 mixed-script confusables. This v2 check fixes all three.

    Args:
        surface: The NFC-normalized rendering.
        term_name: The English source term (e.g. ``except*``), so the identifier
            check can carry the term's structural affixes.
        allowed_scripts: The Unicode scripts legitimate for this locale (see
            :func:`allowed_scripts_for`), or ``None`` for an un-policied locale.
        allowed_format_chars: The format characters the locale's policy
            allow-lists (see :func:`allowed_format_chars_for`). Defaults to the
            EMPTY set — deny every format char — so a caller that does not
            resolve the policy gets the stricter verdict, never a silent pass.

    Returns:
        The verdict. ``identifier_valid`` is Python's own rule made term-aware;
        ``nfkc_delta_class`` records why an unstable value is unstable;
        ``script_consistent`` is checked against the locale's real allowlist;
        and ``format_chars_clean`` runs the CORE-1591 net with the locale's
        policy (CORE-2029).
    """
    nfkc = unicodedata.normalize("NFKC", surface)
    return Validation(
        identifier_valid=_identifier_valid(surface, term_name),
        nfkc_stable=nfkc == surface,
        nfkc_delta_class=nfkc_delta_class(surface, nfkc=nfkc),
        script_consistent=_script_consistent(surface, allowed_scripts),
        collides_en_keyword=keyword.iskeyword(surface),
        format_chars_clean=not format_char_violations(surface, allowed_format_chars),
    )
