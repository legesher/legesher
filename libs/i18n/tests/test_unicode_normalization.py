"""Tests for the NFC/NFKC-stability check (``check_normalization``).

Synthetic fixtures only — these assert the *gate behaviour*, not the state of
any shipped pack. A value is safe iff ``value == NFC == NFKC``; Python NFKC-
folds identifiers at parse time, so an unstable value cannot round-trip.

Fixtures are built from explicit codepoints via ``chr`` so they are unambiguous
regardless of source-file encoding, and each test asserts its own instability
via :mod:`unicodedata` *before* feeding it to the check — the suite can never
silently rely on a "bad" string that turns out to be stable.
"""

from __future__ import annotations

import unicodedata

from legesher_i18n.schema_validator import (
    Finding,
    LanguagePackSchema,
    SchemaValidator,
)

# U+212B ANGSTROM SIGN is a canonical singleton: NFC (and NFKC) maps it to
# U+00C5 LATIN CAPITAL LETTER A WITH RING ABOVE -> NFC-unstable.
ANGSTROM = chr(0x212B)

# U+FF21 FULLWIDTH LATIN CAPITAL LETTER A folds only under NFKC (NFC leaves it
# unchanged), exercising the NFKC arm of the rule independently of NFC.
FULLWIDTH_A = chr(0xFF21)

# Thai KHO KHWAI + SARA AA — an NFC/NFKC-stable Thai value, so it must NOT flag.
# (Contrast SARA AM U+0E33, which DOES decompose under NFKC to U+0E4D U+0E32 and
# is the real-world source of the 24 unstable th pack values this gate catches.)
THAI_STABLE = chr(0x0E04) + chr(0x0E32)


def _schema(language: str, **sections: dict[str, str]) -> LanguagePackSchema:
    """Build a schema bypassing Pydantic field validation.

    The safety layer is deterministic; the legacy Pydantic identifier check is
    interpreter-version-dependent. We construct directly so the safety check is
    tested in isolation.
    """
    return LanguagePackSchema.model_construct(
        language=language,
        target="python",
        version="3.13",
        extends=None,
        keywords=sections.get("keywords", {}),
        builtins=sections.get("builtins", {}),
        exceptions=sections.get("exceptions", {}),
        implicit_params=sections.get("implicit_params", {}),
        operators=sections.get("operators", {}),
        standard_library=sections.get("standard_library", {}),
        cultural_notes=[],
        metadata=None,
    )


class TestNormalizationStability:
    """A value must be identical under both NFC and NFKC."""

    def test_pure_ascii_is_stable(self) -> None:
        schema = _schema("en", keywords={"def": "define", "class": "klass"})
        assert SchemaValidator.check_normalization(schema) == []

    def test_nfc_unstable_value_is_flagged(self) -> None:
        # Premise: the fixture really is NFC-unstable.
        assert unicodedata.normalize("NFC", ANGSTROM) != ANGSTROM
        schema = _schema("en", builtins={"len": f"x{ANGSTROM}y"})
        findings = SchemaValidator.check_normalization(schema)
        assert len(findings) == 1
        assert findings[0].code == "nfkc-instability"
        assert findings[0].location == "builtins.len"
        assert isinstance(findings[0], Finding)

    def test_nfkc_only_unstable_value_is_flagged(self) -> None:
        # Premise: NFC leaves it alone but NFKC folds it.
        assert unicodedata.normalize("NFC", FULLWIDTH_A) == FULLWIDTH_A
        assert unicodedata.normalize("NFKC", FULLWIDTH_A) != FULLWIDTH_A
        schema = _schema("en", builtins={"len": FULLWIDTH_A})
        findings = SchemaValidator.check_normalization(schema)
        assert len(findings) == 1
        assert findings[0].code == "nfkc-instability"

    def test_already_normalized_value_passes(self) -> None:
        # The NFC form of the Angstrom sign is stable and must pass.
        stable = unicodedata.normalize("NFC", ANGSTROM)
        assert unicodedata.normalize("NFKC", stable) == stable
        schema = _schema("en", builtins={"len": f"x{stable}y"})
        assert SchemaValidator.check_normalization(schema) == []

    def test_stable_thai_passes(self) -> None:
        # Stable Thai must not be flagged (guards against false positives).
        assert unicodedata.normalize("NFKC", THAI_STABLE) == THAI_STABLE
        schema = _schema("th", builtins={"len": THAI_STABLE})
        assert SchemaValidator.check_normalization(schema) == []

    def test_thai_sara_am_only_is_allowed(self) -> None:
        # CORE-1514 policy: SARA AM (U+0E33) decomposes under NFKC to U+0E4D
        # U+0E32, but CPython itself NFKC-folds identifiers (PEP 3131), so both
        # spellings are ONE identifier at runtime -- no spoofing surface. When
        # the ONLY NFKC delta is SARA AM, legitimate Thai orthography passes; the
        # pack auditor and the v2 canon gate agree on this.
        sara_am = chr(0x0E04) + chr(0x0E33)
        assert unicodedata.normalize("NFC", sara_am) == sara_am  # NFC-stable
        assert unicodedata.normalize("NFKC", sara_am) != sara_am  # NFKC-unstable
        schema = _schema("th", builtins={"len": sara_am})
        assert SchemaValidator.check_normalization(schema) == []

    def test_sara_am_mixed_with_another_instability_is_still_flagged(self) -> None:
        # The allowance is SARA-AM-*only*. A value that is also unstable for
        # another reason (here NFC-unstable Angstrom) is not legitimate Thai and
        # must still be flagged.
        mixed = chr(0x0E04) + chr(0x0E33) + ANGSTROM
        assert unicodedata.normalize("NFC", mixed) != mixed
        schema = _schema("th", builtins={"len": mixed})
        findings = SchemaValidator.check_normalization(schema)
        assert len(findings) == 1
        assert findings[0].code == "nfkc-instability"

    def test_soft_keyword_star_is_stripped_before_check(self) -> None:
        # The trailing '*' of a soft-keyword translation must not be treated as
        # an instability; an otherwise-stable base passes.
        schema = _schema("es", keywords={"except*": "excepto*"})
        assert SchemaValidator.check_normalization(schema) == []

    def test_findings_are_per_value(self) -> None:
        bad = f"x{ANGSTROM}y"
        schema = _schema(
            "en",
            builtins={"len": bad, "abs": bad, "ok": "naa"},
        )
        findings = SchemaValidator.check_normalization(schema)
        assert len(findings) == 2
        assert {f.location for f in findings} == {"builtins.len", "builtins.abs"}
