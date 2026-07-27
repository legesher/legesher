"""Tests for the ``members`` partition (CORE-1582).

Members are property/method-name translations — labels bounded by their
receiver, used by member-bearing targets such as JavaScript. Guarantees:

1. The schema accepts a ``members`` mapping as an MLCP extended field, and
   the shared mapping validator applies to it.
2. The safety layer sees member values (they ride ``_TRANSLATION_SECTIONS``),
   and the duplicate check enforces IN-partition uniqueness while leaving
   cross-partition homonyms legal for members (a member value matching a
   keyword value is intended, not a reversibility break).
3. The loader carries ``members`` through construction and ``extends``
   inheritance, and existing Python packs load with an empty ``members``.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator


def make_schema(**overrides) -> LanguagePackSchema:
    data = {
        "language": "ar",
        "target": "javascript",
        "version": "1.0",
        **overrides,
    }
    return LanguagePackSchema(**data)


class TestSchemaField:
    def test_members_mapping_accepted(self) -> None:
        schema = make_schema(members={"length": "طول", "log": "سجل"})
        assert schema.members == {"length": "طول", "log": "سجل"}

    def test_members_defaults_empty(self) -> None:
        assert make_schema().members == {}

    def test_mapping_validator_applies_to_members(self) -> None:
        with pytest.raises(ValidationError):
            make_schema(members={"length": ""})


class TestSafetyLayer:
    def test_in_partition_duplicate_is_an_error(self) -> None:
        schema = make_schema(members={"floor": "أرضية", "ceil": "أرضية"})
        dup = SchemaValidator.check_duplicates(schema)
        assert dup["member_duplicates"], "same value for two members must flag"
        findings = SchemaValidator.validate_pack_strict(
            schema, "ar", run_min_interpreter=False, run_cross_section=False
        )
        assert any(
            f.code == "duplicate-target" and f.location.startswith("members.")
            for f in findings
        )

    def test_cross_partition_homonym_is_legal_for_members(self) -> None:
        # `in` (keyword) and a member sharing one native word: receiver
        # disambiguates on member-bearing targets — never a collision, even
        # with the cross-section gate ON (members is excluded by design).
        schema = make_schema(
            keywords={"in": "في"},
            members={"includes": "في"},
        )
        dup = SchemaValidator.check_duplicates(schema)
        assert dup["cross_section_collisions"] == []
        findings = SchemaValidator.validate_pack_strict(
            schema, "ar", run_min_interpreter=False, run_cross_section=True
        )
        assert not any(f.code == "duplicate-target" for f in findings)

    def test_member_values_ride_the_safety_checks(self) -> None:
        # A bidi control in a member value must be caught by the strict layer
        # — proof that members joined _TRANSLATION_SECTIONS rather than
        # bypassing the net. Built via model_construct exactly like the audit
        # path (audit_packs bypasses the Pydantic mapping validator, whose
        # isidentifier check would otherwise catch this even earlier).
        schema = LanguagePackSchema.model_construct(
            language="ar",
            target="javascript",
            version="1.0",
            members={"length": "ط" + chr(0x202E) + "ول"},
        )
        findings = SchemaValidator.validate_pack_strict(
            schema, "ar", run_min_interpreter=False, run_cross_section=False
        )
        assert any("members.length" in f.location for f in findings)


class TestLoader:
    def test_merge_carries_members_with_override_precedence(self) -> None:
        loader = LanguagePackLoader()
        merged = loader._merge_packs(
            base={"members": {"length": "طول", "floor": "أرضية"}},
            override={"members": {"floor": "قاع", "log": "سجل"}},
        )
        assert merged["members"] == {"length": "طول", "floor": "قاع", "log": "سجل"}

    def test_python_packs_load_with_empty_members(self) -> None:
        pack = LanguagePackLoader().load("es", version="3.10")
        assert pack.members == {}
        assert "members=0" in repr(pack)
