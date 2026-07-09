"""Tests for the pack safety gate's ASCII-digit check (CORE-1354):

* ``check_ascii_digits`` — identifiers must use ASCII digits 0-9.

The validation gate is safety/correctness-only; stylistic rules (e.g.
identifier length) are guidance for the translation prompt (PromptBuilder,
CORE-1395), not pack warnings, so ``validate_pack_strict`` takes no style guide.

Synthetic fixtures only — these assert gate behaviour, not the state of any
shipped pack. Digit fixtures are built from explicit codepoints via ``chr`` so
they are unambiguous regardless of source encoding, and each asserts its own
premise before feeding the check.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from types import SimpleNamespace

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator
from legesher_i18n.scripts import audit_packs

DEVANAGARI_ONE = chr(0x0967)  # १  — category Nd, not ASCII
ARABIC_INDIC_ZERO = chr(0x0660)  # ٠  — category Nd, not ASCII


def _schema(language: str, **sections: dict[str, str]) -> LanguagePackSchema:
    return LanguagePackSchema.model_construct(
        language=language,
        target="python",
        version="3.13",
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


class TestAsciiDigits:
    def test_ascii_digits_pass(self) -> None:
        schema = _schema("en", keywords={"var": "x2", "other": "base64"})
        assert SchemaValidator.check_ascii_digits(schema) == []

    def test_native_digit_is_flagged(self) -> None:
        assert unicodedata.category(DEVANAGARI_ONE) == "Nd"
        schema = _schema("hi", builtins={"len": f"लंबाई{DEVANAGARI_ONE}"})
        findings = SchemaValidator.check_ascii_digits(schema)
        assert len(findings) == 1
        assert findings[0].code == "non-ascii-digit"
        assert findings[0].severity == "warning"
        assert "U+0967" in findings[0].message

    def test_arabic_indic_digit_is_flagged(self) -> None:
        # A second native-digit script (Arabic-Indic ٠), not "multiple scripts":
        # confirms the check is not Devanagari-specific.
        assert unicodedata.category(ARABIC_INDIC_ZERO) == "Nd"
        schema = _schema("ar", keywords={"k": f"قيمة{ARABIC_INDIC_ZERO}"})
        codes = [f.code for f in SchemaValidator.check_ascii_digits(schema)]
        assert codes == ["non-ascii-digit"]


class TestStrictWiring:
    """validate_pack_strict aggregates the always-on safety checks."""

    def test_ascii_digits_aggregated(self) -> None:
        # The ASCII-digit policy runs as part of validate_pack_strict, with no
        # style guide required.
        schema = _schema("hi", builtins={"len": f"लंबाई{DEVANAGARI_ONE}"})
        findings = SchemaValidator.validate_pack_strict(schema, "hi")
        assert any(f.code == "non-ascii-digit" for f in findings)


class TestAuditGateSeam:
    """The audit CLI feeds the merged pack into the gate."""

    def test_audit_pack_file_runs_gate(self) -> None:
        # A merged pack carrying a native digit, fed through the audit's
        # per-file entry point, must surface the gate's non-ascii-digit
        # finding — proving audit_packs -> validate_pack_strict is wired.
        pack = SimpleNamespace(
            language="hi",
            target="python",
            version="3.13",
            keywords={},
            builtins={"len": f"लंबाई{DEVANAGARI_ONE}"},
            exceptions={},
            reserved_words={},
            metadata=None,
        )
        loader = SimpleNamespace(load=lambda *args, **kwargs: pack)
        pack_file = Path(
            "libs/i18n/language-packs/python/hi/legesher_i18n_python_hi/packs/3.13.yml"
        )
        lang, version, findings = audit_packs._audit_pack_file(loader, pack_file)
        assert (lang, version) == ("hi", "3.13")
        assert any(f.code == "non-ascii-digit" for f in findings)
