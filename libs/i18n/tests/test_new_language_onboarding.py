"""Golden onboarding test: what a *new* language pack must satisfy.

This suite doubles as executable documentation for contributors adding a new
script/language during the 51 -> 103 expansion. Each test states one rule a
clean pack must obey and demonstrates both the passing and failing shape via
``validate_pack_strict``. If you are onboarding a language, read this file
top-to-bottom — it is the checklist.

Onboarding checklist (each maps to a test below):
  1. Register a ScriptPolicy for the language code (default-deny otherwise).
  2. All translation values stay within the language's script(s).
  3. Values are NFC/NFKC-stable.
  4. No illegal format/bidi characters (only policy-allow-listed ZWJ/ZWNJ ok).
  5. No value equals a live Python keyword/builtin (except its own target).
  6. ZWJ-bearing values declare python_version_min >= 3.13.
  7. No duplicate targets (except the intentional keywords.type==builtins.type).
  8. If the script is shared with a neighbour whose letters the language does
     not use, declare them as forbidden_letters (tests/test_forbidden_letters.py).
"""

from __future__ import annotations

from legesher_i18n.schema_validator import (
    Finding,
    LanguagePackMetadata,
    LanguagePackSchema,
    SchemaValidator,
)
from legesher_i18n.script_policy import ZWJ

# U+212B ANGSTROM SIGN — a canonical singleton (NFC maps it to U+00C5), built
# from its codepoint so the value is unambiguous regardless of file encoding.
ANGSTROM = chr(0x212B)


def _construct(
    language: str,
    version: str = "3.13",
    *,
    python_version_min: str | None = "3.13",
    **sections,
) -> LanguagePackSchema:
    """Build a merged-pack schema, bypassing Pydantic field validation."""
    metadata = (
        LanguagePackMetadata(python_version_min=python_version_min)
        if python_version_min is not None
        else None
    )
    return LanguagePackSchema.model_construct(
        language=language,
        target="python",
        version=version,
        extends=None,
        keywords=sections.get("keywords", {}),
        builtins=sections.get("builtins", {}),
        exceptions=sections.get("exceptions", {}),
        implicit_params=sections.get("implicit_params", {}),
        operators=sections.get("operators", {}),
        standard_library=sections.get("standard_library", {}),
        cultural_notes=[],
        metadata=metadata,
    )


def _codes(findings: list[Finding]) -> set[str]:
    return {f.code for f in findings}


class TestGoldenCleanPack:
    """A well-formed pack produces zero findings."""

    def test_clean_latin_pack_passes_strict(self) -> None:
        schema = _construct(
            "es",
            keywords={"def": "definir", "class": "clase", "in": "in"},
            builtins={"print": "imprimir", "len": "longitud"},
        )
        assert SchemaValidator.validate_pack_strict(schema) == []

    def test_clean_cyrillic_pack_passes_strict(self) -> None:
        schema = _construct(
            "ru",
            keywords={"def": "определить", "class": "класс"},
            builtins={"print": "печать"},
        )
        assert SchemaValidator.validate_pack_strict(schema) == []

    def test_intentional_type_duplicate_is_allowed(self) -> None:
        # keywords.type == builtins.type is the one sanctioned duplicate.
        schema = _construct(
            "es",
            keywords={"type": "tipo"},
            builtins={"type": "tipo"},
        )
        findings = SchemaValidator.validate_pack_strict(schema)
        assert "duplicate-target" not in _codes(findings)


class TestGoldenViolations:
    """Each onboarding rule, demonstrated by a failing pack."""

    def test_rule1_unregistered_language_default_denies(self) -> None:
        schema = _construct("zz", builtins={"bool": "whatever"})
        findings = SchemaValidator.validate_pack_strict(schema)
        assert "no-policy" in _codes(findings)

    def test_rule2_foreign_script_is_caught(self) -> None:
        # Chinese 布尔 smuggled into a Polish (Latin) bool translation.
        schema = _construct("pl", builtins={"bool": "布尔"})
        assert "foreign-script" in _codes(SchemaValidator.validate_pack_strict(schema))

    def test_rule3_unstable_normalization_is_caught(self) -> None:
        schema = _construct("en", builtins={"len": f"x{ANGSTROM}y"})
        assert "nfkc-instability" in _codes(
            SchemaValidator.validate_pack_strict(schema)
        )

    def test_rule4_illegal_format_char_is_caught(self) -> None:
        schema = _construct("en", keywords={"def": f"de{ZWJ}fine"})
        assert "illegal-format-char" in _codes(
            SchemaValidator.validate_pack_strict(schema)
        )

    def test_rule5_keyword_collision_is_caught(self) -> None:
        schema = _construct("de", builtins={"globals": "global"})
        assert "keyword-collision" in _codes(
            SchemaValidator.validate_pack_strict(schema)
        )

    def test_rule6_zwj_without_313_min_is_caught(self) -> None:
        schema = _construct(
            "si",
            version="3.10",
            python_version_min="3.10",
            keywords={"x": f"අ{ZWJ}ය"},
        )
        assert "min-interpreter-xid" in _codes(
            SchemaValidator.validate_pack_strict(schema)
        )

    def test_rule7_duplicate_target_is_caught(self) -> None:
        schema = _construct(
            "es",
            builtins={"min": "minimo", "max": "minimo"},
        )
        assert "duplicate-target" in _codes(
            SchemaValidator.validate_pack_strict(schema)
        )


class TestGoldenSinhalaConjunct:
    """Sinhala is the load-bearing format-char case — verify end to end."""

    def test_sinhala_zwj_pack_with_313_min_clears_the_zwj_rules(self) -> None:
        # Legitimate Sinhala conjunct using ZWJ, declared for 3.13+. The three
        # ZWJ-/script-sensitive rules must all be satisfied: the allow-listed
        # ZWJ is not an illegal format char, the 3.13 minimum clears the XID
        # trap, and the value stays within the Sinhala script.
        schema = _construct(
            "si",
            version="3.13",
            python_version_min="3.13",
            keywords={"False": "අසත්‍ය", "True": "සත්‍ය"},
        )
        codes = _codes(SchemaValidator.validate_pack_strict(schema))
        assert "illegal-format-char" not in codes
        assert "min-interpreter-xid" not in codes
        assert "foreign-script" not in codes
