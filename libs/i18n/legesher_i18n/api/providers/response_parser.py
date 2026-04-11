"""Shared response parsing for LLM translation providers.

Extracts translation values from JSON responses produced by the
PromptBuilder's structured output format.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Patterns for stripping markdown code fences
_FENCE_START = re.compile(r"^```(?:json)?\s*")
_FENCE_END = re.compile(r"\s*```$")


def parse_llm_response(
    raw_text: str,
    original_text: str,
    context: dict[str, Any] | None,
) -> str:
    """Extract the translation from an LLM response.

    When *context* is provided (PromptBuilder was used), the response
    is expected to be JSON.  Extracts the translation value from
    the JSON dict or list.  Falls back to raw text if parsing fails.

    Parameters
    ----------
    raw_text:
        Raw text from the LLM response.
    original_text:
        The original text that was sent for translation (used as a
        lookup key in JSON dict responses).
    context:
        The context dict that was forwarded to the provider.  If
        ``None``, the response is returned as-is (legacy mode).

    Returns
    -------
    str
        The extracted translation.
    """
    if context is None:
        return raw_text

    # Strip markdown code fences if present
    cleaned = raw_text.strip()
    cleaned = _FENCE_START.sub("", cleaned)
    cleaned = _FENCE_END.sub("", cleaned)
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug("Response is not JSON, using raw text: %s", cleaned[:100])
        return cleaned

    # JSON dict: {"original": "translated"} — extract the value
    if isinstance(parsed, dict):
        if original_text in parsed:
            return str(parsed[original_text])
        if parsed:
            return str(next(iter(parsed.values())))

    # JSON list: ["translated text 1", ...] — return first item
    if isinstance(parsed, list) and parsed:
        return str(parsed[0])

    return cleaned
