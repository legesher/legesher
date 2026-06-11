"""Tests for the per-language script allowlist (``check_script_consistency``).

Synthetic fixtures. The check rejects any value whose Unicode scripts fall
outside the language's policy (``Common``/``Inherited`` always allowed). This
is the foreign-script bleed-through guard: Chinese inside a Polish value, a
stray Cyrillic letter in Thai, a Hangul syllable in Hindi, etc.
"""

from __future__ import annotations

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator


def _schema(language: str, version: str = "3.13", **sections) -> LanguagePackSchema:
    """Build a schema bypassing Pydantic field validation (see other suites)."""
    return LanguagePackSchema.model_construct(
        language=language,
        target="python",
        version=version,
        extends=None,
        keywords=sections.get("keywords", {}),
        builtins=sections.get("builtins", {}),
        exceptions=sections.get("exceptions", {}),
        reserved_words=sections.get("reserved_words", {}),
        operators=sections.get("operators", {}),
        standard_library=sections.get("standard_library", {}),
        cultural_notes=[],
        metadata=None,
    )


class TestScriptConsistency:
    """Values must stay within the language's declared script(s)."""

    def test_latin_value_in_latin_pack_passes(self) -> None:
        schema = _schema("pl", builtins={"bool": "logiczna"})
        assert SchemaValidator.check_script_consistency(schema, "pl") == []

    def test_han_value_in_polish_pack_is_flagged(self) -> None:
        # Chinese 布尔 smuggled into a Polish (Latin) bool translation.
        schema = _schema("pl", builtins={"bool": "布尔"})
        findings = SchemaValidator.check_script_consistency(schema, "pl")
        assert len(findings) == 1
        assert findings[0].code == "foreign-script"
        assert findings[0].location == "builtins.bool"
        assert "Han" in findings[0].message

    def test_cyrillic_letter_in_thai_pack_is_flagged(self) -> None:
        # Thai value with a single Cyrillic 'а' (U+0430) mixed in.
        schema = _schema("th", builtins={"len": "ความยาва"})
        findings = SchemaValidator.check_script_consistency(schema, "th")
        assert len(findings) == 1
        assert findings[0].code == "foreign-script"

    def test_hangul_in_hindi_pack_is_flagged(self) -> None:
        # Hangul U+B7FD inside a Devanagari value.
        schema = _schema("hi", exceptions={"keyboardinterrupt": "कुंजीपटल럽"})
        findings = SchemaValidator.check_script_consistency(schema, "hi")
        assert len(findings) == 1
        assert "Hangul" in findings[0].message

    def test_native_script_passes_for_each_family(self) -> None:
        cases = {
            "ru": "логическое",  # Cyrillic
            "el": "λογικό",  # Greek
            "he": "בוליאני",  # Hebrew
            "th": "ตรรกะ",  # Thai
            "ja": "ブール論",  # Katakana + Han
            "ko": "불린",  # Hangul
            "zh": "布尔",  # Han
        }
        for lang, value in cases.items():
            schema = _schema(lang, builtins={"bool": value})
            assert SchemaValidator.check_script_consistency(schema, lang) == [], lang

    def test_digits_and_underscore_are_common_and_allowed(self) -> None:
        schema = _schema("pl", builtins={"bool": "bool_2"})
        assert SchemaValidator.check_script_consistency(schema, "pl") == []

    def test_unknown_language_is_default_deny(self) -> None:
        schema = _schema("pl", builtins={"bool": "logiczna"})
        # Police it against a code with no policy: single no-policy finding.
        findings = SchemaValidator.check_script_consistency(schema, "xx")
        assert len(findings) == 1
        assert findings[0].code == "no-policy"

    def test_sinhala_zwj_does_not_trip_script_check(self) -> None:
        # Sinhala value using the allow-listed ZWJ: virama + ZWJ ligature.
        value = "අසත්‍ය"  # Sinhala with legitimate ZWJ
        schema = _schema("si", keywords={"False": value})
        assert SchemaValidator.check_script_consistency(schema, "si") == []
