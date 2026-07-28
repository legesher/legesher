"""Tests for the format/bidi-control character check (``check_format_chars``).

Synthetic fixtures. Legitimate uses: ZWJ (U+200D) in Sinhala conjuncts, ZWNJ
(U+200C) in Persian/Urdu. Everything else — bidi controls, tatweel, BOM, and
ZWJ/ZWNJ in languages that don't allow-list them — is rejected.

CORE-1591 widens the net to the full Default_Ignorable_Code_Point set: the
non-``Cf`` invisibles (U+034F COMBINING GRAPHEME JOINER, the Hangul fillers,
the variation selectors, the Mongolian FVS) are ``.isidentifier()``-True and
NFKC-stable, so ``valid<U+034F>name`` renders identically to ``validname``
yet is a different identifier. Those must be blocking findings too.
"""

from __future__ import annotations

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator
from legesher_i18n.script_policy import (
    BOM,
    TATWEEL,
    ZWJ,
    ZWNJ,
    is_default_ignorable,
)

LRO = "\u202d"  # LEFT-TO-RIGHT OVERRIDE (bidi control)
RLO = "\u202e"  # RIGHT-TO-LEFT OVERRIDE (bidi control)
ARABIC_LETTER_MARK = "\u061c"

# Non-Cf Default_Ignorable code points (the CORE-1591 gap): all render as
# nothing, all are valid identifier characters, none are category Cf — so the
# pre-CORE-1591 Cf net missed every one of them.
CGJ = "\u034f"  # COMBINING GRAPHEME JOINER (Mn)
HANGUL_CHOSEONG_FILLER = "\u115f"  # HANGUL CHOSEONG FILLER (Lo)
HANGUL_JUNGSEONG_FILLER = "\u1160"  # HANGUL JUNGSEONG FILLER (Lo)
HANGUL_FILLER = "\u3164"  # HANGUL FILLER (Lo)
VS16 = "\ufe0f"  # VARIATION SELECTOR-16 (Mn)
MONGOLIAN_FVS1 = "\u180b"  # MONGOLIAN FREE VARIATION SELECTOR ONE (Mn)


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


class TestDefaultIgnorableTable:
    """The static Default_Ignorable_Code_Point table (mirrors unicode_guard)."""

    def test_ticket_examples_are_default_ignorable(self) -> None:
        # The CORE-1591 verified set: every one is .isidentifier()-True in an
        # identifier tail yet renders as nothing.
        for ch in (
            CGJ,
            HANGUL_CHOSEONG_FILLER,
            HANGUL_JUNGSEONG_FILLER,
            HANGUL_FILLER,
            VS16,
            MONGOLIAN_FVS1,
        ):
            assert is_default_ignorable(ch), f"U+{ord(ch):04X} must be in the table"

    def test_cf_members_are_covered_too(self) -> None:
        # The wider net includes the Cf members (ZWJ/ZWNJ/BOM, soft hyphen) —
        # per-language allow-listing happens in check_format_chars, not here.
        for ch in (ZWJ, ZWNJ, BOM, "\u00ad"):
            assert is_default_ignorable(ch), f"U+{ord(ch):04X} must be in the table"

    def test_supplementary_variation_selectors_covered(self) -> None:
        assert is_default_ignorable("\U000e0100")  # VARIATION SELECTOR-17
        assert is_default_ignorable("\U000e01ef")  # VARIATION SELECTOR-256

    def test_reserved_cn_subranges_covered(self) -> None:
        # Unassigned code points inside the property's reserved blocks stay
        # covered so the net does not lag future Unicode assignments.
        assert is_default_ignorable("\u2065")  # <reserved> (Cn) inside U+2060..U+206F
        assert is_default_ignorable("\U000e0080")

    def test_ordinary_characters_are_not_default_ignorable(self) -> None:
        for ch in ("a", "අ", "정", "ي", "0", "_", TATWEEL):
            assert not is_default_ignorable(ch), f"U+{ord(ch):04X} wrongly flagged"

    def test_empty_string_is_not_default_ignorable(self) -> None:
        assert not is_default_ignorable("")


class TestDefaultIgnorableInValues:
    """Pack values bearing ANY Default_Ignorable code point are blocked.

    These are the CORE-1591 failing examples: every character below passes the
    script-consistency gate (Mn reads as Inherited, the Hangul fillers read as
    Hangul) and the pre-fix Cf-only format net, yet renders invisibly.
    """

    def test_cgj_in_latin_value_is_flagged(self) -> None:
        # 'valid<U+034F>name' renders identically to 'validname'.
        schema = _schema("en", keywords={"def": f"valid{CGJ}name"})
        findings = SchemaValidator.check_format_chars(schema, "en")
        assert len(findings) == 1
        assert findings[0].severity == "error"
        assert findings[0].code == "default-ignorable-char"
        assert "034F" in findings[0].message

    def test_hangul_filler_in_korean_value_is_flagged(self) -> None:
        # U+3164 sits in the Hangul Compatibility Jamo block, so the script
        # gate reads it as plain Hangul — only the default-ignorable net can
        # catch it.
        schema = _schema("ko", keywords={"def": f"정의{HANGUL_FILLER}"})
        findings = SchemaValidator.check_format_chars(schema, "ko")
        assert len(findings) == 1
        assert findings[0].code == "default-ignorable-char"

    def test_hangul_jungseong_filler_is_flagged(self) -> None:
        schema = _schema("ko", keywords={"def": f"정{HANGUL_JUNGSEONG_FILLER}의"})
        findings = SchemaValidator.check_format_chars(schema, "ko")
        assert len(findings) == 1
        assert findings[0].code == "default-ignorable-char"

    def test_vs16_in_latin_value_is_flagged(self) -> None:
        schema = _schema("en", keywords={"def": f"define{VS16}"})
        findings = SchemaValidator.check_format_chars(schema, "en")
        assert len(findings) == 1
        assert findings[0].code == "default-ignorable-char"

    def test_mongolian_fvs_is_flagged(self) -> None:
        # Mongolian pack policy is Cyrillic; U+180B is Mn -> Inherited, so it
        # sails through the script gate.
        schema = _schema("mn", keywords={"def": f"функц{MONGOLIAN_FVS1}"})
        findings = SchemaValidator.check_format_chars(schema, "mn")
        assert len(findings) == 1
        assert findings[0].code == "default-ignorable-char"

    def test_clean_native_values_still_pass(self) -> None:
        # Negative control: ordinary native values with combining marks must
        # not trip the wider net.
        for lang, value in (
            ("ko", "정의"),
            ("hi", "परिभाषा"),  # Devanagari with combining vowel signs
            ("ar", "تعريف"),
            ("th", "กำหนด"),  # Thai with SARA AM
            ("en", "define"),
        ):
            schema = _schema(lang, keywords={"def": value})
            assert SchemaValidator.check_format_chars(schema, lang) == [], (
                f"clean {lang} value '{value}' must pass"
            )

    def test_sinhala_zwj_still_allowed_with_wider_net(self) -> None:
        # ZWJ is Default_Ignorable AND Cf, but Sinhala explicitly allow-lists
        # it — the CORE-1591 net must not break the legitimate conjunct path.
        schema = _schema("si", keywords={"x": f"අ{ZWJ}ය"})
        assert SchemaValidator.check_format_chars(schema, "si") == []

    def test_persian_zwnj_still_allowed_with_wider_net(self) -> None:
        schema = _schema("fa", keywords={"x": f"اب{ZWNJ}ج"})
        assert SchemaValidator.check_format_chars(schema, "fa") == []

    def test_cf_members_keep_illegal_format_char_code(self) -> None:
        # Existing Cf semantics are unchanged: a ZWJ in a non-allow-listing
        # language still reports as illegal-format-char, not the new code.
        schema = _schema("en", keywords={"def": f"de{ZWJ}fine"})
        findings = SchemaValidator.check_format_chars(schema, "en")
        assert len(findings) == 1
        assert findings[0].code == "illegal-format-char"

    def test_validate_pack_strict_blocks_default_ignorable(self) -> None:
        # End-to-end through the aggregate gate the audit uses: the finding
        # must be a blocking error.
        schema = _schema("en", keywords={"def": f"valid{CGJ}name"})
        findings = SchemaValidator.validate_pack_strict(schema, "en")
        codes = {f.code for f in findings if f.severity == "error"}
        assert "default-ignorable-char" in codes
