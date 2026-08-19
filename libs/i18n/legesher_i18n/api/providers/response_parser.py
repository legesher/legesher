"""Shared response parsing for LLM translation providers.

Extracts translation values from JSON responses produced by the
PromptBuilder's structured output format.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from legesher_i18n.llm_json import strip_code_fences

logger = logging.getLogger(__name__)


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

    # Strip markdown code fences if present (shared helper — CORE-1804)
    cleaned = strip_code_fences(raw_text)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.debug("Response is not JSON, using raw text: %s", cleaned[:100])
        return cleaned

    # JSON dict — either {"original": "translated"} (mapping format) or a
    # linguistic-metadata object with a "translation" key (term format).
    if isinstance(parsed, dict):
        if original_text in parsed:
            return str(parsed[original_text])
        if "translation" in parsed:
            return str(parsed["translation"])
        if parsed:
            return str(next(iter(parsed.values())))

    # JSON list: ["translated text 1", ...] — return first item
    if isinstance(parsed, list) and parsed:
        return str(parsed[0])

    return cleaned
