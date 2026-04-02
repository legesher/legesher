"""Tests for OpenAICompatProvider response parsing."""

import pytest

from legesher_i18n.api.providers.openai_compat import OpenAICompatProvider


class TestParseResponse:
    """Test _parse_response extracts translations from JSON responses."""

    @pytest.fixture
    def provider(self):
        return OpenAICompatProvider(base_url="http://localhost:11434/v1", model="test")

    def test_json_dict_extracts_value(self, provider):
        """JSON dict response should extract the translation value."""
        raw = '{"add": "sumar"}'
        result = provider._parse_response(raw, "add", {"kind": "identifier"})
        assert result == "sumar"

    def test_json_dict_original_key_match(self, provider):
        """Should match the original text as key."""
        raw = '{"calculate_tax": "calcular_impuesto", "income": "ingreso"}'
        result = provider._parse_response(raw, "calculate_tax", {"kind": "identifier"})
        assert result == "calcular_impuesto"

    def test_json_dict_first_value_fallback(self, provider):
        """If original text not in keys, return first value."""
        raw = '{"unknown_key": "traducción"}'
        result = provider._parse_response(raw, "something_else", {"kind": "identifier"})
        assert result == "traducción"

    def test_json_list_extracts_first(self, provider):
        """JSON list response should return first element."""
        raw = '["traducción del texto"]'
        result = provider._parse_response(raw, "original", {"kind": "comment"})
        assert result == "traducción del texto"

    def test_strips_markdown_fences(self, provider):
        """Should strip ```json fences from response."""
        raw = '```json\n{"add": "sumar"}\n```'
        result = provider._parse_response(raw, "add", {"kind": "identifier"})
        assert result == "sumar"

    def test_strips_plain_fences(self, provider):
        """Should strip plain ``` fences."""
        raw = '```\n{"add": "sumar"}\n```'
        result = provider._parse_response(raw, "add", {"kind": "identifier"})
        assert result == "sumar"

    def test_non_json_returns_raw(self, provider):
        """Non-JSON response should be returned as-is."""
        raw = "sumar"
        result = provider._parse_response(raw, "add", {"kind": "identifier"})
        assert result == "sumar"

    def test_no_context_returns_raw(self, provider):
        """Without context, should return raw text unchanged."""
        raw = '{"add": "sumar"}'
        result = provider._parse_response(raw, "add", None)
        assert result == '{"add": "sumar"}'

    def test_empty_dict_returns_cleaned(self, provider):
        """Empty JSON dict should return the cleaned string."""
        raw = "{}"
        result = provider._parse_response(raw, "add", {"kind": "identifier"})
        assert result == "{}"

    def test_chinese_translation(self, provider):
        """Should handle Chinese characters in JSON values."""
        raw = '{"add": "加"}'
        result = provider._parse_response(raw, "add", {"kind": "identifier"})
        assert result == "加"

    def test_urdu_translation(self, provider):
        """Should handle Urdu script in JSON values."""
        raw = '{"add": "اضافہ"}'
        result = provider._parse_response(raw, "add", {"kind": "identifier"})
        assert result == "اضافہ"
