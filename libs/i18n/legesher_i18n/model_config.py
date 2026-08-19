"""Model identifiers for LLM providers — one place, env-overridable.

CORE-1804: the Anthropic model ID was pinned in two constructors
(generation-side ``ClaudeModel`` and API-side ``AnthropicProvider``) with no
override anywhere. This module is now the only place a default model ID
lives.

Override
--------

Set the environment variable::

    LEGESHER_ANTHROPIC_MODEL=claude-<model-id>

Pricing is configured separately — Legesher ships no rates. See
``legesher_i18n/api/rates.py`` (``LEGESHER_RATES_FILE`` or the inline
``LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK`` / ``_OUTPUT_PER_MTOK``
variables). Without a configured rate, costs report as unknown and the
generation pipeline's ``--max-budget`` guard cannot enforce.
"""

from __future__ import annotations

import os

ANTHROPIC_MODEL_ENV = "LEGESHER_ANTHROPIC_MODEL"

DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"


def anthropic_model() -> str:
    """Return the configured Anthropic model ID.

    Resolution order: ``LEGESHER_ANTHROPIC_MODEL`` env var, then the
    packaged default. Read per call so tests and long-lived processes see
    environment changes.
    """
    return os.getenv(ANTHROPIC_MODEL_ENV, "").strip() or DEFAULT_ANTHROPIC_MODEL
