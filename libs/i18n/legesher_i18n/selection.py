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

from dataclasses import dataclass

from .schema_validator import LanguagePackSchema

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


def is_valid_pack_value(term: str, value: str) -> bool:
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

    Args:
        term: The source term (e.g. ``"arithmeticerror"``, ``"except*"``).
        value: The candidate translation value.

    Returns:
        True if the value passes the publish gate.
    """
    if not isinstance(value, str) or not value:
        return False
    if value != value.strip():
        return False
    return LanguagePackSchema._is_valid_identifier(value, source_key=term)


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
) -> SelectionResult | None:
    """Choose the canonical translation for a (term, language) pair.

    Args:
        term: The source term name (e.g. ``"arithmeticerror"``).
        candidates: Candidate rows from the ``translations`` pool. Each
            dict needs a ``translation`` key and may carry ``source`` and
            ``confidence``.
        pack_value: The value the shipped pack currently carries for this
            term, if any. When valid it anchors the selection (rule 2).

    Returns:
        A :class:`SelectionResult`, or None when nothing passes the
        validity gate (rule 4 — caller must treat this as an error for
        pack-shipping languages, never fall back to a dirty value).
    """
    # Rule 2: shipped-pack anchor (subject to rule 1's gate).
    if pack_value is not None and is_valid_pack_value(term, pack_value):
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
        c for c in candidates if is_valid_pack_value(term, c.get("translation", ""))
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
