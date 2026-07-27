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
   with the ``except*`` soft-keyword allowance). Invalid candidates are
   tolerated in the ``translations`` pool but can never become canonical.
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
SOURCE_TRUST: tuple[str, ...] = (
    "community_review",  # outcome of a native-reviewer pass
    "community",  # community-contributed value
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
    for ``except*``-style soft-keyword translations (optional trailing
    ``*`` on an otherwise-valid identifier).

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
