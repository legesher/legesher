"""The one JSON parser for LLM translation responses.

CORE-1804: JSON fence-stripping and object extraction previously existed in
four places (``claude_model``, the Anthropic provider, the generation-side
``json_utils``, and the API-side ``response_parser``), each with its own
regexes and repair behavior. This module is now the single implementation;
the other call sites delegate here.

The extraction ladder (fenced block → raw object → repair → field-by-field
regex) comes from the generation-side ``json_utils``, which was the most
battle-tested of the four against small-model output.
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

# Patterns for stripping markdown code fences from a whole response.
_FENCE_START = re.compile(r"^```(?:json)?\s*")
_FENCE_END = re.compile(r"\s*```$")


def strip_code_fences(text: str) -> str:
    """Strip a surrounding markdown code fence, if present."""
    cleaned = text.strip()
    cleaned = _FENCE_START.sub("", cleaned)
    cleaned = _FENCE_END.sub("", cleaned)
    return cleaned.strip()


def parse_json_object(response_text: str) -> dict:
    """Parse a JSON object from a model response, with fallback strategies.

    Args:
        response_text: Raw response text from the model.

    Returns:
        Parsed JSON dictionary.

    Raises:
        ValueError: If no JSON object can be extracted with any strategy.
    """
    # Strategy 1: extract from a markdown code block
    code_block_pattern = r"```(?:json)?\s*(\{[^`]*?\})\s*```"
    match = re.search(code_block_pattern, response_text, re.DOTALL)

    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.debug("Failed to parse JSON from code block, trying repair")
            repaired = repair_json(json_str)
            if repaired:
                return repaired

    # Strategy 2: find a raw JSON object
    json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    matches = re.finditer(json_pattern, response_text, re.DOTALL)

    for match in matches:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            repaired = repair_json(json_str)
            if repaired:
                return repaired

    # Strategy 3: extract field by field with regex
    logger.warning("Standard JSON parsing failed, attempting field extraction")
    extracted = extract_fields_from_text(response_text)
    if extracted and "translation" in extracted:
        return extracted

    logger.error(f"Could not parse JSON from model response: {response_text[:500]}...")
    raise ValueError("Failed to parse JSON after trying all strategies")


def repair_json(json_str: str) -> dict | None:
    """Attempt to repair malformed JSON.

    Args:
        json_str: Potentially malformed JSON string.

    Returns:
        Parsed dict if repair succeeded, None otherwise.
    """
    # Remove trailing commas before closing braces/brackets
    repaired = re.sub(r",(\s*[}\]])", r"\1", json_str)

    # Remove any text after the final closing brace
    brace_match = re.search(r"\}[^}]*$", repaired)
    if brace_match:
        repaired = repaired[: brace_match.start() + 1]

    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        # Try adding missing closing braces
        open_braces = repaired.count("{")
        close_braces = repaired.count("}")
        if open_braces > close_braces:
            repaired += "}" * (open_braces - close_braces)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    return None


def extract_fields_from_text(text: str) -> dict:
    """Extract translation fields from text using regex patterns.

    Last-resort fallback for when JSON parsing fails completely.

    Args:
        text: Response text.

    Returns:
        Dictionary with extracted fields (may be empty).
    """
    result: dict = {}

    translation_patterns = [
        r'"translation"\s*:\s*"([^"]*)"',
        r"'translation'\s*:\s*'([^']*)'",
        r'translation:\s*"([^"]*)"',
        r"translation:\s*([^\s,}\n]+)",
    ]

    for pattern in translation_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["translation"] = match.group(1)
            break

    word_type_match = re.search(r'"word_type"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
    if word_type_match:
        result["word_type"] = word_type_match.group(1)

    form_match = re.search(r'"form"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
    if form_match:
        result["form"] = form_match.group(1)

    confidence_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', text, re.IGNORECASE)
    if confidence_match:
        try:
            result["confidence"] = float(confidence_match.group(1))
        except ValueError:
            result["confidence"] = 0.7

    alternatives_match = re.search(
        r'"alternatives"\s*:\s*\[(.*?)\]', text, re.IGNORECASE | re.DOTALL
    )
    if alternatives_match:
        alt_strings = re.findall(r'"([^"]*)"', alternatives_match.group(1))
        result["alternatives"] = alt_strings

    rationale_match = re.search(r'"rationale"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
    if rationale_match:
        result["rationale"] = rationale_match.group(1)

    if result:
        logger.info(f"Extracted fields from malformed response: {result}")
    return result
