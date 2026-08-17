"""Tests for the minimum-interpreter XID check.

Synthetic fixtures. The Sinhala ZWJ trap: ``virama + ZWJ + consonant`` is a
valid identifier on CPython 3.13+ (Unicode 15.1 XID) but a ``SyntaxError`` on
3.10-3.12. The check is static (never calls ``compile()``): a value using a
post-Unicode-15.0 XID character is flagged when the pack's declared minimum
interpreter is < 3.13.

The character set is the measured 3.10 -> 3.13 delta, not a denylist of the
traps someone had already hit. ``TestTheXIDDeltaTable`` pins the table itself;
``TestKatakanaMiddleDot`` is the case the old two-member denylist missed.
"""

from __future__ import annotations

import sys
import unicodedata

import pytest

from legesher_i18n.schema_validator import (
    _XID_CHARS_ADDED_BY_CPYTHON_313,
    _XID_RANGES_ADDED_BY_CPYTHON_313,
    LanguagePackSchema,
    SchemaValidator,
)
from legesher_i18n.script_policy import ZWJ

#: U+30FB, the character that shipped in ``ja``'s 3.10 pack and is a hard
#: SyntaxError there. Its halfwidth twin is U+FF65.
KATAKANA_MIDDLE_DOT = "\u30fb"
HALFWIDTH_KATAKANA_MIDDLE_DOT = "\uff65"


def _schema(
    language: str,
    version: str,
    *,
    python_version_min: str | None = None,
    **sections,
) -> LanguagePackSchema:
    """Build a schema bypassing Pydantic, optionally setting metadata min."""
    metadata = None
    if python_version_min is not None:
        from legesher_i18n.schema_validator import LanguagePackMetadata

        metadata = LanguagePackMetadata(python_version_min=python_version_min)
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
        metadata=metadata,
    )


class TestMinInterpreterIdentifier:
    """ZWJ-bearing values require a declared minimum interpreter of 3.13+."""

    def test_zwj_value_with_min_310_is_flagged(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.10", python_version_min="3.10", keywords={"x": value})
        findings = SchemaValidator.check_min_interpreter_identifier(schema, "si")
        assert len(findings) == 1
        assert findings[0].code == "min-interpreter-xid"
        assert findings[0].location == "keywords.x"

    def test_zwj_value_with_min_313_passes(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.13", python_version_min="3.13", keywords={"x": value})
        assert SchemaValidator.check_min_interpreter_identifier(schema, "si") == []

    def test_zwj_value_with_min_314_passes(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.14", python_version_min="3.14", keywords={"x": value})
        assert SchemaValidator.check_min_interpreter_identifier(schema, "si") == []

    def test_plain_value_with_min_310_passes(self) -> None:
        # No ZWJ -> nothing version-sensitive -> always fine.
        schema = _schema("si", "3.10", python_version_min="3.10", keywords={"x": "අය"})
        assert SchemaValidator.check_min_interpreter_identifier(schema, "si") == []

    def test_min_version_argument_overrides_metadata(self) -> None:
        value = f"අ{ZWJ}ය"
        schema = _schema("si", "3.13", python_version_min="3.13", keywords={"x": value})
        # Explicit override to an old interpreter re-flags it.
        findings = SchemaValidator.check_min_interpreter_identifier(
            schema, "si", min_version="3.11"
        )
        assert len(findings) == 1

    def test_falls_back_to_pack_version_when_no_metadata(self) -> None:
        value = f"අ{ZWJ}ය"
        # No metadata; pack version is 3.10 -> flagged.
        schema = _schema("si", "3.10", keywords={"x": value})
        findings = SchemaValidator.check_min_interpreter_identifier(schema, "si")
        assert len(findings) == 1

    def test_version_at_least_helper(self) -> None:
        assert SchemaValidator._version_at_least("3.13", 3, 13) is True
        assert SchemaValidator._version_at_least("3.14", 3, 13) is True
        assert SchemaValidator._version_at_least("3.12", 3, 13) is False
        assert SchemaValidator._version_at_least("3.10", 3, 13) is False
        assert SchemaValidator._version_at_least(None, 3, 13) is False
        assert SchemaValidator._version_at_least("garbage", 3, 13) is False


class TestKatakanaMiddleDot:
    """CORE-1905: U+30FB is a 3.13-only identifier character too.

    ``ja`` shipped ``divmod: ディビジョン・モジュール`` in a pack declaring a 3.10
    floor. U+30FB KATAKANA MIDDLE DOT separates the two halves of the compound
    reading and entered XID_Continue only in Unicode 15.1, so that value was a
    hard SyntaxError on every interpreter the pack claimed to support. The gate
    did not flag it because its character set named ZWJ and ZWNJ and nothing
    else.
    """

    def test_middle_dot_with_min_310_is_flagged(self) -> None:
        value = f"ディビジョン{KATAKANA_MIDDLE_DOT}モジュール"
        schema = _schema(
            "ja", "3.10", python_version_min="3.10", builtins={"divmod": value}
        )
        findings = SchemaValidator.check_min_interpreter_identifier(schema, "ja")
        assert len(findings) == 1
        assert findings[0].code == "min-interpreter-xid"
        assert findings[0].location == "builtins.divmod"
        assert "U+30FB" in findings[0].message

    def test_halfwidth_middle_dot_with_min_310_is_flagged(self) -> None:
        value = f"ディビジョン{HALFWIDTH_KATAKANA_MIDDLE_DOT}モジュール"
        schema = _schema(
            "ja", "3.10", python_version_min="3.10", builtins={"divmod": value}
        )
        findings = SchemaValidator.check_min_interpreter_identifier(schema, "ja")
        assert [f.code for f in findings] == ["min-interpreter-xid"]
        assert "U+FF65" in findings[0].message

    def test_middle_dot_with_min_313_passes(self) -> None:
        value = f"ディビジョン{KATAKANA_MIDDLE_DOT}モジュール"
        schema = _schema(
            "ja", "3.13", python_version_min="3.13", builtins={"divmod": value}
        )
        assert SchemaValidator.check_min_interpreter_identifier(schema, "ja") == []

    def test_the_dot_free_form_passes_under_the_310_rules(self) -> None:
        """The value the 3.10 pack now ships must clear the version-aware check.

        Asserted through the checker, not through this interpreter's
        ``str.isidentifier()``: the tests run on 3.13, where the DOTTED form is
        an identifier too, so the build interpreter cannot tell the two apart.
        """
        dot_free = "ディビジョンモジュール"
        schema = _schema(
            "ja", "3.10", python_version_min="3.10", builtins={"divmod": dot_free}
        )
        assert SchemaValidator.check_min_interpreter_identifier(schema, "ja") == []
        # ...and the dotted form it replaced does NOT.
        dotted = f"ディビジョン{KATAKANA_MIDDLE_DOT}モジュール"
        flagged = _schema(
            "ja", "3.10", python_version_min="3.10", builtins={"divmod": dotted}
        )
        assert SchemaValidator.check_min_interpreter_identifier(flagged, "ja") != []


class TestTheXIDDeltaTable:
    """The pinned 3.10 -> 3.13 table, checked rather than trusted."""

    def test_the_table_is_sorted_and_disjoint(self) -> None:
        previous_last = -1
        for first, last in _XID_RANGES_ADDED_BY_CPYTHON_313:
            assert first <= last, f"inverted range U+{first:04X}-U+{last:04X}"
            assert first > previous_last + 1, (
                f"range U+{first:04X}- overlaps or abuts the one before it; "
                f"adjacent ranges must be merged so the table has one spelling"
            )
            previous_last = last

    def test_the_table_expands_to_the_measured_delta(self) -> None:
        assert len(_XID_RANGES_ADDED_BY_CPYTHON_313) == 77
        assert len(_XID_CHARS_ADDED_BY_CPYTHON_313) == 5674

    def test_the_known_members_are_present(self) -> None:
        for char in (ZWJ, "\u200c", KATAKANA_MIDDLE_DOT, HALFWIDTH_KATAKANA_MIDDLE_DOT):
            assert char in _XID_CHARS_ADDED_BY_CPYTHON_313, (
                f"U+{ord(char):04X} {unicodedata.name(char, '')} missing from the "
                f"delta table"
            )

    def test_ordinary_identifier_characters_are_absent(self) -> None:
        """The table names what CHANGED, not what is legal."""
        for char in "aZ0_ぁ漢ก":
            assert char not in _XID_CHARS_ADDED_BY_CPYTHON_313

    @pytest.mark.skipif(
        sys.version_info < (3, 13),
        reason="only an interpreter at 3.13+ can confirm the 3.13 half",
    )
    def test_every_member_is_an_identifier_char_on_this_interpreter(self) -> None:
        """Half the table is re-derivable here; the 3.10 half is not.

        ``unicodedata`` reports only the running interpreter's Unicode version,
        so a test on 3.13 can prove every listed codepoint IS XID_Continue now,
        but not that it was absent on 3.10. That half is the pinned measurement
        in the source comment. A codepoint that fails here is a table entry that
        was never valid anywhere.
        """
        offenders = [
            f"U+{ord(ch):04X}"
            for ch in _XID_CHARS_ADDED_BY_CPYTHON_313
            if not ("a" + ch).isidentifier()
        ]
        assert offenders == [], f"listed but not XID_Continue here: {offenders[:10]}"
