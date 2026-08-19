"""JSON parsing for translation model responses — shim over the shared parser.

CORE-1804: the implementation moved to ``legesher_i18n.llm_json`` so the
generation and API layers share one JSON parser. This module re-exports the
same names for existing imports.
"""

from legesher_i18n.llm_json import (
    extract_fields_from_text,
    parse_json_object as parse_json_response,
    repair_json,
)

__all__ = ["parse_json_response", "repair_json", "extract_fields_from_text"]
