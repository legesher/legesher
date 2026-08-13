"""Operator-supplied price rates for translation providers.

We do not know what a model costs. Prices change without notice, differ by
contract and region, and a figure we hardcode is wrong the moment a provider
updates a price list — quietly, and by a ratio nobody notices.

So Legesher ships **no rates**. An operator who wants cost reporting or a
dollar budget supplies the prices they are actually billed, which are the only
prices that are true for them.

When no rate is configured the answer is **unknown**, not zero. A confident
wrong number is worse than an absent one: absent invites you to go look, zero
invites you to stop thinking about it.

Configuration
-------------

Point ``LEGESHER_RATES_FILE`` at a JSON file::

    {
      "anthropic":   {"input_per_million_tokens": 3.0,
                      "output_per_million_tokens": 15.0},
      "cohere_aya":  {"per_million_chars": 0.50},
      "google":      {"per_million_chars": 20.0}
    }

Or set a single provider inline::

    LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK=3.0
    LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK=15.0
    LEGESHER_RATE_COHERE_AYA_PER_MCHAR=0.50

Rates are read once per process. Nothing here reaches the network, and no
rate is ever inferred from a model name.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

RATES_FILE_ENV = "LEGESHER_RATES_FILE"
_INLINE_PREFIX = "LEGESHER_RATE_"


@lru_cache(maxsize=1)
def _rate_table() -> dict[str, dict[str, float]]:
    table: dict[str, dict[str, float]] = {}

    path = os.getenv(RATES_FILE_ENV)
    if path:
        try:
            loaded = json.loads(Path(path).read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                table.update({k: v for k, v in loaded.items() if isinstance(v, dict)})
            else:
                logger.warning("%s is not a JSON object; ignoring", RATES_FILE_ENV)
        except (OSError, json.JSONDecodeError) as exc:
            # Never fail a translation because a rate file is unreadable —
            # cost reporting is an accessory, translation is the product.
            logger.warning("could not read %s (%s); costs stay unknown", path, exc)

    # Inline overrides win: LEGESHER_RATE_<PROVIDER>_<UNIT>
    suffixes = {
        "_INPUT_PER_MTOK": "input_per_million_tokens",
        "_OUTPUT_PER_MTOK": "output_per_million_tokens",
        "_PER_MCHAR": "per_million_chars",
    }
    for key, raw in os.environ.items():
        if not key.startswith(_INLINE_PREFIX):
            continue
        for suffix, field in suffixes.items():
            if key.endswith(suffix):
                provider = key[len(_INLINE_PREFIX) : -len(suffix)].lower()
                try:
                    table.setdefault(provider, {})[field] = float(raw)
                except ValueError:
                    logger.warning("%s is not a number; ignoring", key)
                break

    return table


def rates_for(provider: str) -> dict[str, float] | None:
    """Configured rates for a provider, or None when the operator set none."""
    return _rate_table().get(provider) or None


def cost_for_chars(provider: str, characters: int) -> float | None:
    """Cost in USD, or **None** when no rate is configured."""
    rates = rates_for(provider)
    if not rates or "per_million_chars" not in rates:
        return None
    return (characters / 1_000_000) * rates["per_million_chars"]


def cost_for_tokens(
    provider: str, input_tokens: int, output_tokens: int
) -> float | None:
    """Cost in USD, or **None** when no rate is configured.

    Requires both directions: a half-configured rate would under-report, which
    is the failure mode a budget guard can least afford.
    """
    rates = rates_for(provider)
    if not rates:
        return None
    inp = rates.get("input_per_million_tokens")
    out = rates.get("output_per_million_tokens")
    if inp is None or out is None:
        return None
    return (input_tokens / 1_000_000) * inp + (output_tokens / 1_000_000) * out


def format_cost(cost: float | None) -> str:
    """Render a cost for humans — never a fabricated zero."""
    return "unknown" if cost is None else f"${cost:.4f}"


def reset_cache() -> None:
    """Forget the cached table. For tests and for reloading after a config change."""
    _rate_table.cache_clear()
