"""Shared JSON parsing utilities for translation model responses.

This module provides common JSON parsing and repair utilities used by
multiple translation model implementations (Aya-101 HF, Aya Inference API, etc.).
"""

import json
import logging
import re

logger = logging.getLogger(__name__)


def parse_json_response(response_text: str) -> dict:
    """Parse JSON from model response with multiple fallback strategies.

    Args:
        response_text: Raw response from the translation model

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If JSON cannot be extracted or parsed with any strategy
    """
    # Strategy 1: Try to extract from markdown code blocks
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

    # Strategy 2: Find raw JSON object (greedy match)
    json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    matches = re.finditer(json_pattern, response_text, re.DOTALL)

    for match in matches:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try to repair this candidate
            repaired = repair_json(json_str)
            if repaired:
                return repaired

    # Strategy 3: Extract field by field with regex
    logger.warning("Standard JSON parsing failed, attempting field extraction")
    extracted = extract_fields_from_text(response_text)
    if extracted and "translation" in extracted:
        return extracted

    # All strategies failed
    logger.error(f"Could not parse JSON from model response: {response_text[:500]}...")
    raise ValueError("Failed to parse JSON after trying all strategies")


def repair_json(json_str: str) -> dict | None:
    """Attempt to repair malformed JSON.

    Args:
        json_str: Potentially malformed JSON string

    Returns:
        Parsed dict if repair successful, None otherwise
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

    This is a fallback for when JSON parsing fails completely.
    It attempts to extract individual field values using various patterns.

    Args:
        text: Response text

    Returns:
        Dictionary with extracted fields
    """
    result = {}

    # Extract translation (most important field)
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

    # Extract word_type
    word_type_match = re.search(r'"word_type"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
    if word_type_match:
        result["word_type"] = word_type_match.group(1)

    # Extract form
    form_match = re.search(r'"form"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
    if form_match:
        result["form"] = form_match.group(1)

    # Extract confidence (as float)
    confidence_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', text, re.IGNORECASE)
    if confidence_match:
        try:
            result["confidence"] = float(confidence_match.group(1))
        except ValueError:
            result["confidence"] = 0.7

    # Extract alternatives array
    alternatives_match = re.search(
        r'"alternatives"\s*:\s*\[(.*?)\]', text, re.IGNORECASE | re.DOTALL
    )
    if alternatives_match:
        # Extract quoted strings from array
        alt_strings = re.findall(r'"([^"]*)"', alternatives_match.group(1))
        result["alternatives"] = alt_strings

    # Extract rationale
    rationale_match = re.search(r'"rationale"\s*:\s*"([^"]*)"', text, re.IGNORECASE)
    if rationale_match:
        result["rationale"] = rationale_match.group(1)

    if result:
        logger.info(f"Extracted fields from malformed response: {result}")
    return result
