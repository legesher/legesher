"""Canonical translation selection for language-pack export (CORE-1400).

This module is the single place that decides which translation value is
*canonical* for a ``(term, language)`` pair. It exists because the
``translations`` table intentionally tolerates dirty candidates (raw model
output such as ``"erreur arithmétique"`` — multi-word, space-containing,
not a Python identifier). Under the options model the candidate pool is
allowed to be messy; what must never be messy is what gets *published*:
the ``selected_translations`` table and everything exported from it.

The rule, in precedence order (documented in
``docs/translation-selection.md``):

1. **Validity gate** — a value is only selectable if it is a valid Python
   identifier after the pack-schema check (PEP 3131 ``str.isidentifier``,
   with a ``*``-suffixed term such as ``except*`` requiring the mirrored
   trailing ``*``). Invalid candidates are tolerated in the
   ``translations`` pool but can never become canonical.
2. **Shipped-pack anchor** — if the language already ships a pack value
   for the term and that value passes the gate, it is canonical. Shipped
   packs have passed the mechanical gates (collision audit, NFKC guard,
   schema validation) and carry surgical curation (CORE-1303, CORE-1317,
   CORE-1318); a regeneration must reproduce them, not revert them.
3. **Source trust** — otherwise the best valid candidate wins, ordered by
   ``SOURCE_TRUST`` (human-reviewed sources above machine output), then by
   confidence (``high`` > ``medium`` > ``low`` > unset), then by a
   deterministic lexicographic tiebreak so repeated runs agree.
4. **No fallback** — if no valid candidate exists the term stays
   unselected and the exporter refuses to emit the pack (fail loudly;
   never silently drop or invent a value).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .schema_validator import LanguagePackSchema, SchemaValidator
from .script_policy import forbidden_letters_in, nfkc_delta_class

# Translation sources ordered from most to least trusted. Sources not in
# this tuple rank below all listed sources. See
# docs/translation-selection.md for the rationale per source.
#
# *** THIS IS THE v1 `translations.source` VOCABULARY. It is NOT the v2
# `option_provenance.source` vocabulary, and the two must not be conflated. ***
#
# They answer different questions and are cut on different axes:
#
#   * THIS one ranks CREDIBILITY -- "whose word do we ship when two candidates
#     both pass the gate?" It is fine-grained on purpose (`claude_agent` above
#     `claude` above `aya`), internal, and free to grow as pipelines change.
#   * The v2 one records OBLIGATION -- "what do we owe for this row?" -- in four
#     values (`legesher` / `upstream` / `community` / `model`). It is PUBLIC: it
#     ships as `options.sources` in the Hugging Face corpus, so it is cut coarse
#     and stable rather than descriptive (CORE-1720).
#
# The overlap is where it misleads. `community` HERE is the v1 label on the
# 2,169 rows lifted wholesale from legesher/legesher-translations -- another
# repository's work, no individual author. In v2 those are `upstream`, and v2's
# `community` means something narrower and newer: a named individual's own
# assertion through the native-review process. Ranking them second here is
# still right (a human wrote them); reading "community" as "our reviewers said
# so" is not.
#
# Mapping, when you need to cross the boundary:
#   community_review                                       -> community
#   community                                              -> upstream
#   yaml-import, yaml_pack, core-1318-fix, machine-composed -> legesher
#   claude, claude_agent, aya                              -> model
# The authoritative version lives in `scripts/migrate_to_v2.SOURCE_MAP`, which
# refuses to migrate a source it has no bucket for.
SOURCE_TRUST: tuple[str, ...] = (
    "community_review",  # outcome of a native-reviewer pass
    "community",  # legesher-translations import (v2: `upstream`)
    "core-1318-fix",  # curated corrections from the CORE-1318 audit
    "machine-composed",  # curated machine composition (e.g. CORE-1317)
    "claude_agent",  # linguist-framed agent output
    "claude",  # single-shot Claude output
    "yaml_pack",  # value imported back from a shipped pack
    "yaml-import",  # bulk import from packs (older, less provenance)
    "aya",  # raw Aya model output
)

_CONFIDENCE_SCORE = {"high": 3, "medium": 2, "low": 1}


@dataclass(frozen=True)
class SelectionResult:
    """The canonical value chosen for a (term, language) pair."""

    translation: str
    reason: str
    source: str | None = None


def is_valid_pack_value(term: str, value: str, language: str | None = None) -> bool:
    """Return True if ``value`` may be published for ``term``.

    Delegates to the pack schema's identifier check so the selection gate
    and the pack-validation gate can never disagree. The check enforces:
    non-empty, no leading/trailing whitespace, no spaces or punctuation,
    valid Python identifier per PEP 3131 — with the documented allowance
    for ``except*``-style soft keywords: a ``*``-suffixed term REQUIRES a
    ``*``-suffixed translation (an otherwise-valid identifier carrying the
    mirrored trailing ``*``), and a term without one cannot take a value
    with one. The mirror was optional until CORE-1839, which is how nine
    packs shipped values that reverse-translated to ``except**``.

    When ``language`` is given, the value must also carry none of the
    letters that language's orthography forbids (``script_policy``
    ``forbidden_letters``: the Russian-only ы э ъ ё for Ukrainian), the same
    rule the pack audit's ``forbidden-letter`` check enforces.

    Args:
        term: The source term (e.g. ``"arithmeticerror"``, ``"except*"``).
        value: The candidate translation value.
        language: The value's language code, or None to skip the
            orthography check.

    Returns:
        True if the value passes the publish gate.
    """
    if not isinstance(value, str) or not value:
        return False
    if value != value.strip():
        return False
    if language is not None and forbidden_letters_in(value, language):
        return False
    return LanguagePackSchema._is_valid_identifier(value, source_key=term)


# A symbol NAME is a short noun phrase ("opening parenthesis", "guion
# bajo"), not the sentence that explains what the symbol does. The cap is
# code points and deliberately generous: the longest English name in the
# inventory is 24 ("triple quotation mark"), and agglutinative languages
# will run longer. 60 leaves room for those while still catching the
# failure mode this exists for — a model answering with the ``role``
# sentence it was given as context instead of the name it was asked for.
MAX_SYMBOL_NAME_LENGTH = 60

# Unicode general categories a symbol name may never contain. Cc/Cf cover
# control and format characters (bidi overrides included); Zl/Zp are the
# line/paragraph separators; Cs/Co/Cn are surrogates, private use, and
# unassigned. Ordinary spaces (Zs) ARE allowed — a symbol name is prose and
# most of them are multi-word.
_FORBIDDEN_NAME_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"})


def vocabulary_value_error(
    section: str, slug: str, value: str, language: str | None = None
) -> str | None:
    """The publish gate for the vocabulary partition (CORE-1396).

    Returns a human-readable reason the value may not be published, or
    ``None`` when it passes. Two sections, two regimes, because the two
    hold different kinds of thing:

    ``symbols``
        Prose — the NAME of a symbol, for teaching text and error
        messages. Never parsed, never executed, so the identifier gate
        would be exactly wrong. What it must be: non-empty, not padded,
        free of control/format characters, and short enough to be a name
        rather than a definition.

    ``variable_conventions``
        Real identifiers — these are names a developer is being advised to
        type into their own code. They take the same PEP 3131 gate as a
        pack translation, plus three rules a translation does not:

        * **No trailing ``*``.** The starred soft-keyword form
          (``except*``) is a term-section device — the star mirrors the
          source term's own star. A variable role never carries one, so no
          recommended name may either. Checked before the identifier gate,
          which (called without a source term) would otherwise
          short-circuit on ``SOFT_KEYWORDS`` and accept the literal
          ``except*`` that the pack-load validator rejects.
        * **No CPython-3.13-only XID character.** Pack values get that
          guarantee from the exporter's interpreter-floor tiering, which
          strips such characters for the pre-3.13 files. Tiering is not
          available here — a recommended NAME has no version-overlay file
          to live in — so the character is refused at the write boundary
          instead.
        * **Normalization-stable.** Python NFKC-folds identifiers at parse
          time, so a value like fullwidth ``ｉ`` would silently bind ``i``
          — the advice a reader sees would not be the identifier the
          interpreter creates. Same allowance as the term-side
          ``check_normalization`` gate (CORE-1514): an NFC-stable value
          whose ONLY NFKC delta is Thai SARA AM (U+0E33) is legitimate
          orthography, folded by CPython itself, and passes.

        This function is called by the pydantic pack-load validator, the
        strict validator, the database write boundary, the exporter and the
        generation script; keeping every rule HERE is what makes those
        layers unable to disagree.

    Both sections also refuse, when ``language`` is given, the letters that
    language's orthography forbids (``script_policy`` ``forbidden_letters``),
    the same rule the term gate applies: a Russian ``ы`` in a Ukrainian
    recommended name is the same leak as one in a Ukrainian keyword.

    Args:
        section: ``"symbols"`` or ``"variable_conventions"``.
        slug: The entry slug, used only in the message.
        value: The candidate value.
        language: The value's language code, or None to skip the
            orthography check.
    """
    if not isinstance(value, str) or not value:
        return f"{section}.{slug}: value is empty"
    if value != value.strip():
        return f"{section}.{slug}: value has leading/trailing whitespace ({value!r})"
    if language is not None and (leaked := forbidden_letters_in(value, language)):
        return (
            f"{section}.{slug}: {value!r} contains {leaked}, letters the "
            f"{language!r} orthography never uses"
        )

    if section == "symbols":
        bad = sorted(
            {c for c in value if unicodedata.category(c) in _FORBIDDEN_NAME_CATEGORIES}
        )
        if bad:
            points = ", ".join(f"U+{ord(c):04X}" for c in bad)
            return f"symbols.{slug}: name contains control/format character(s) {points}"
        if len(value) > MAX_SYMBOL_NAME_LENGTH:
            return (
                f"symbols.{slug}: name is {len(value)} characters; the cap is "
                f"{MAX_SYMBOL_NAME_LENGTH} — a symbol name is a short noun "
                "phrase, not a description of what the symbol does"
            )
        if value.endswith("*"):
            return (
                f"symbols.{slug}: name ends with '*' — a name is the word for "
                "a glyph, not the glyph itself, and the trailing star is the "
                "term sections' soft-keyword marker; no starred value may "
                "enter this partition"
            )
        return None

    if section == "variable_conventions":
        # Before the identifier gate on purpose: _is_valid_identifier with
        # no source term short-circuits on SOFT_KEYWORDS and would accept
        # the literal 'except*' — a verdict the pack-load validator does
        # not share. Rejecting every trailing '*' first makes that
        # short-circuit unreachable from this branch (SOFT_KEYWORDS members
        # all carry the star) and keeps the two layers in agreement.
        if value.endswith("*"):
            return (
                f"variable_conventions.{slug}: '{value}' ends with '*'. The "
                "starred soft-keyword form belongs to the term sections, "
                "where it mirrors the source term's own star; a recommended "
                "variable name cannot carry one"
            )
        if not LanguagePackSchema._is_valid_identifier(value, source_key=None):
            return (
                f"variable_conventions.{slug}: '{value}' is not a valid Python "
                "identifier, so it cannot be recommended as a variable name"
            )
        needs_313 = sorted(
            {c for c in value if c in SchemaValidator._XID_ONLY_FROM_CPYTHON_313}
        )
        if needs_313:
            points = ", ".join(f"U+{ord(c):04X}" for c in needs_313)
            return (
                f"variable_conventions.{slug}: '{value}' uses {points}, which "
                "only became a valid identifier character in CPython 3.13. A "
                "recommended name has no version overlay to be tiered into, so "
                "it must parse on the 3.10 floor — respell it"
            )
        nfc = unicodedata.normalize("NFC", value)
        nfkc = unicodedata.normalize("NFKC", value)
        if not (value == nfc == nfkc):
            # Same allowance as the term-side check_normalization gate
            # (CORE-1514 policy): an NFC-stable value whose ONLY NFKC delta
            # is Thai SARA AM (U+0E33) is legitimate orthography — CPython
            # folds it in identifiers (PEP 3131), so both spellings are one
            # identifier and there is no spoofing surface. Everything else
            # unstable is refused: a fullwidth 'ｉ' would silently bind 'i',
            # making the advice wrong about the very name it recommends.
            if not (
                value == nfc and nfkc_delta_class(value, nfkc=nfkc) == "sara-am-only"
            ):
                return (
                    f"variable_conventions.{slug}: '{value}' is not stable "
                    f"under Unicode normalization (NFC='{nfc}', NFKC='{nfkc}'). "
                    "Python NFKC-folds identifiers at parse time, so the "
                    "spelling recommended and the identifier bound would "
                    "silently differ — respell it in normalized form"
                )
        return None

    return (
        f"unknown vocabulary section '{section}'; expected 'symbols' or "
        "'variable_conventions'"
    )


def source_trust_rank(source: str | None) -> int:
    """Rank a translation source (0 = most trusted).

    Unknown or missing sources rank below every listed source.
    """
    try:
        return SOURCE_TRUST.index(source)  # type: ignore[arg-type]
    except ValueError:
        return len(SOURCE_TRUST)


def confidence_score(confidence: str | None) -> int:
    """Score a confidence label (higher = more confident)."""
    if confidence is None:
        return 0
    return _CONFIDENCE_SCORE.get(str(confidence).lower(), 0)


def select_canonical(
    term: str,
    candidates: list[dict],
    pack_value: str | None = None,
    language: str | None = None,
) -> SelectionResult | None:
    """Choose the canonical translation for a (term, language) pair.

    Args:
        term: The source term name (e.g. ``"arithmeticerror"``).
        candidates: Candidate rows from the ``translations`` pool. Each
            dict needs a ``translation`` key and may carry ``source`` and
            ``confidence``.
        pack_value: The value the shipped pack currently carries for this
            term, if any. When valid it anchors the selection (rule 2).
        language: The pair's language code; when given, rule 1's gate also
            applies the language's forbidden letters.

    Returns:
        A :class:`SelectionResult`, or None when nothing passes the
        validity gate (rule 4 — caller must treat this as an error for
        pack-shipping languages, never fall back to a dirty value).
    """
    # Rule 2: shipped-pack anchor (subject to rule 1's gate).
    if pack_value is not None and is_valid_pack_value(term, pack_value, language):
        matching = next(
            (c for c in candidates if c.get("translation") == pack_value),
            None,
        )
        return SelectionResult(
            translation=pack_value,
            reason="shipped-pack-value",
            source=matching.get("source") if matching else None,
        )

    # Rule 3: best valid candidate by (source trust, confidence, text).
    valid = [
        c
        for c in candidates
        if is_valid_pack_value(term, c.get("translation", ""), language)
    ]
    if not valid:
        return None

    best = min(
        valid,
        key=lambda c: (
            source_trust_rank(c.get("source")),
            -confidence_score(c.get("confidence")),
            c["translation"],
        ),
    )
    return SelectionResult(
        translation=best["translation"],
        reason=(
            f"source-trust:{best.get('source') or 'unknown'}"
            f"/{best.get('confidence') or 'unrated'}"
        ),
        source=best.get("source"),
    )
