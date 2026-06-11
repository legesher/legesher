"""Tests for the format/bidi-control character check (``check_format_chars``).

Synthetic fixtures. Legitimate uses: ZWJ (U+200D) in Sinhala conjuncts, ZWNJ
(U+200C) in Persian/Urdu. Everything else — bidi controls, tatweel, BOM, and
ZWJ/ZWNJ in languages that don't allow-list them — is rejected.
"""

from __future__ import annotations

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator
from legesher_i18n.script_policy import BOM, TATWEEL, ZWJ, ZWNJ

LRO = "\u202d"  # LEFT-TO-RIGHT OVERRIDE (bidi control)
RLO = "\u202e"  # RIGHT-TO-LEFT OVERRIDE (bidi control)
ARABIC_LETTER_MARK = "\u061c"


def _schema(language: str, version: str = "3.13", **sections) -> LanguagePackSchema:
    """Build a schema *bypassing* Pydantic field validation.

    The safety layer is deterministic and interpreter-independent; the legacy
    Pydantic ``_is_valid_identifier`` check is neither (it relies on the running
    interpreter's ``str.isidentifier`` Unicode version and an incomplete
    invalid-char denylist). To exercise the safety check on values the legacy
    check would inconsistently reject, we construct the model directly.
    """
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


class TestFormatChars:
    """Format/bidi controls are denied unless the policy allow-lists them."""

    def test_clean_latin_value_passes(self) -> None:
        schema = _schema("en", keywords={"def": "define"})
        assert SchemaValidator.check_format_chars(schema, "en") == []

    def test_sinhala_zwj_is_allowed(self) -> None:
        # Sinhala virama + ZWJ + consonant: legitimate conjunct.
        value = f"අ{ZWJ}ය"
        schema = _schema("si", keywords={"x": value})
        assert SchemaValidator.check_format_chars(schema, "si") == []

    def test_persian_zwnj_is_allowed(self) -> None:
        value = f"اب{ZWNJ}ج"
        schema = _schema("fa", keywords={"x": value})
        assert SchemaValidator.check_format_chars(schema, "fa") == []

    def test_zwj_in_latin_pack_is_flagged(self) -> None:
        # ZWJ is fine in Sinhala but not in a Latin pack that doesn't list it.
        schema = _schema("en", keywords={"def": f"de{ZWJ}fine"})
        findings = SchemaValidator.check_format_chars(schema, "en")
        assert len(findings) == 1
        assert findings[0].code == "illegal-format-char"

    def test_bidi_override_is_flagged(self) -> None:
        schema = _schema("ar", keywords={"def": f"تعريف{RLO}"})
        findings = SchemaValidator.check_format_chars(schema, "ar")
        assert len(findings) == 1
        assert findings[0].code == "illegal-format-char"

    def test_lro_in_latin_is_flagged(self) -> None:
        schema = _schema("en", keywords={"def": f"de{LRO}fine"})
        assert len(SchemaValidator.check_format_chars(schema, "en")) == 1

    def test_tatweel_is_flagged_even_in_arabic(self) -> None:
        # Tatweel (U+0640) is category Lm, a cosmetic elongation; never allowed.
        schema = _schema("ar", keywords={"def": f"تعر{TATWEEL}يف"})
        findings = SchemaValidator.check_format_chars(schema, "ar")
        assert len(findings) == 1
        assert findings[0].code == "illegal-format-char"

    def test_bom_is_flagged(self) -> None:
        schema = _schema("en", keywords={"def": f"{BOM}define"})
        assert len(SchemaValidator.check_format_chars(schema, "en")) == 1

    def test_arabic_letter_mark_is_flagged(self) -> None:
        schema = _schema("ar", keywords={"def": f"تعريف{ARABIC_LETTER_MARK}"})
        assert len(SchemaValidator.check_format_chars(schema, "ar")) == 1

    def test_zwnj_in_sinhala_is_flagged(self) -> None:
        # Sinhala allow-lists ZWJ but NOT ZWNJ — so a ZWNJ must still be caught.
        schema = _schema("si", keywords={"x": f"අ{ZWNJ}ය"})
        findings = SchemaValidator.check_format_chars(schema, "si")
        assert len(findings) == 1
        assert findings[0].code == "illegal-format-char"
