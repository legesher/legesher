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
    _UNICODE_OF_CPYTHON,
    _XID_ADDED_BY_CPYTHON,
    _XID_CHARS_ADDED_BY_CPYTHON_313,
    _XID_RANGES_ADDED_BY_CPYTHON_313,
    _XID_RANGES_ADDED_BY_CPYTHON_314,
    _XID_RANGES_ADDED_BY_CPYTHON_315,
    LanguagePackSchema,
    SchemaValidator,
    interpreter_needed_for_identifier,
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
        implicit_params=sections.get("implicit_params", {}),
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


# -- one measured delta per CPython release (CORE-2832) ------------------------

#: Each release's range table, its measured size, and the release it was
#: measured against (the interpreter on which none of its members is valid).
RELEASES = {
    (3, 13): (_XID_RANGES_ADDED_BY_CPYTHON_313, 77, 5674, (3, 10)),
    (3, 14): (_XID_RANGES_ADDED_BY_CPYTHON_314, 31, 4433, (3, 13)),
    (3, 15): (_XID_RANGES_ADDED_BY_CPYTHON_315, 27, 4699, (3, 14)),
}
RUNNING = sys.version_info[:2]

#: A character first accepted by each release, from its table: U+088F ARABIC
#: LETTER NOON WITH RING ABOVE (Unicode 17, CPython 3.15) and U+0897 ARABIC
#: PEPET (Unicode 16, CPython 3.14), both Arabic script, so a pack in a
#: language that already ships could reach them.
ONLY_FROM_315 = "\u088f"
ONLY_FROM_314 = "\u0897"


def _label(release: tuple[int, int]) -> str:
    return f"{release[0]}.{release[1]}"


class TestOneDeltaPerRelease:
    """The per-release tables, checked rather than trusted."""

    def test_every_release_with_a_table_is_registered(self) -> None:
        assert set(_XID_ADDED_BY_CPYTHON) == set(RELEASES)
        assert set(_UNICODE_OF_CPYTHON) == set(RELEASES)

    @pytest.mark.parametrize("release", sorted(RELEASES), ids=_label)
    def test_the_table_is_sorted_disjoint_and_the_measured_size(self, release) -> None:
        ranges, n_ranges, n_points, _base = RELEASES[release]
        previous_last = -1
        for first, last in ranges:
            assert first <= last, f"inverted range U+{first:04X}-U+{last:04X}"
            assert first > previous_last + 1, f"U+{first:04X} overlaps or abuts"
            previous_last = last
        assert len(ranges) == n_ranges
        assert len(_XID_ADDED_BY_CPYTHON[release]) == n_points

    def test_no_character_is_claimed_by_two_releases(self) -> None:
        seen: dict[str, tuple[int, int]] = {}
        for release, added in sorted(_XID_ADDED_BY_CPYTHON.items()):
            for ch in added:
                assert ch not in seen, (
                    f"U+{ord(ch):04X} listed for {_label(seen[ch])} and {_label(release)}"
                )
                seen[ch] = release

    @pytest.mark.parametrize("release", sorted(RELEASES), ids=_label)
    def test_ordinary_identifier_characters_are_in_no_table(self, release) -> None:
        for char in "aZ0_ぁ漢กعअ":
            assert char not in _XID_ADDED_BY_CPYTHON[release]

    @pytest.mark.parametrize("release", sorted(RELEASES), ids=_label)
    def test_every_member_is_an_identifier_char_from_its_release_on(
        self, release
    ) -> None:
        if RUNNING < release:
            pytest.skip(f"only CPython {_label(release)}+ can confirm this half")
        offenders = [
            f"U+{ord(ch):04X}"
            for ch in _XID_ADDED_BY_CPYTHON[release]
            if not ("a" + ch).isidentifier()
        ]
        assert offenders == [], f"listed but not XID_Continue here: {offenders[:10]}"

    @pytest.mark.parametrize("release", sorted(RELEASES), ids=_label)
    def test_no_member_is_an_identifier_char_before_its_release(self, release) -> None:
        """The other half: on the release a table was measured against, or older,
        none of its members is valid. On 3.13 this proves the 3.14 and 3.15
        tables name nothing 3.13 already accepted."""
        base = RELEASES[release][3]
        if RUNNING > base:
            pytest.skip(f"only CPython {_label(base)} or older can confirm this half")
        accepted = [
            f"U+{ord(ch):04X}"
            for ch in _XID_ADDED_BY_CPYTHON[release]
            if ("a" + ch).isidentifier()
        ]
        assert accepted == [], (
            f"already XID_Continue on {_label(RUNNING)}: {accepted[:10]}"
        )


class TestInterpreterNeededForIdentifier:
    def test_values_python_310_accepts_need_nothing(self) -> None:
        for value in ("definir", "تعريف", "परिभाषितकरना", "අර්ථදක්වන්න", "定义"):
            assert interpreter_needed_for_identifier(value) is None

    def test_each_release_is_named_by_its_own_characters(self) -> None:
        assert interpreter_needed_for_identifier(f"අ{ZWJ}ය") == (3, 13)
        assert interpreter_needed_for_identifier(f"ب{ONLY_FROM_314}") == (3, 14)
        assert interpreter_needed_for_identifier(f"ب{ONLY_FROM_315}") == (3, 15)

    def test_the_newest_release_wins(self) -> None:
        value = f"අ{ZWJ}ය{ONLY_FROM_315}{ONLY_FROM_314}"
        assert interpreter_needed_for_identifier(value) == (3, 15)


class TestTheGateIsOneRulePerRelease:
    """A value that needs release V fails in any tier whose floor is below V."""

    @pytest.mark.parametrize(
        ("char", "release"),
        [(ZWJ, "3.13"), (ONLY_FROM_314, "3.14"), (ONLY_FROM_315, "3.15")],
        ids=["3.13", "3.14", "3.15"],
    )
    def test_a_value_is_refused_one_release_below_what_it_needs(
        self, char, release
    ) -> None:
        below = f"3.{int(release.split('.')[1]) - 1}"
        value = f"ب{char}ب"
        schema = _schema("ar", below, python_version_min=below, keywords={"def": value})
        findings = SchemaValidator.check_min_interpreter_identifier(schema, "ar")
        assert [f.code for f in findings] == ["min-interpreter-xid"]
        message = findings[0].message
        assert findings[0].location == "keywords.def"
        assert f"U+{ord(char):04X}" in message
        assert f"CPython {release}" in message
        assert f"python_version_min to '{release}'" in message

    @pytest.mark.parametrize(
        ("char", "release"),
        [(ZWJ, "3.13"), (ONLY_FROM_314, "3.14"), (ONLY_FROM_315, "3.15")],
        ids=["3.13", "3.14", "3.15"],
    )
    def test_the_same_value_passes_at_the_release_it_needs(self, char, release) -> None:
        value = f"ب{char}ب"
        schema = _schema(
            "ar", release, python_version_min=release, keywords={"def": value}
        )
        assert SchemaValidator.check_min_interpreter_identifier(schema, "ar") == []

    def test_a_finding_names_only_what_the_floor_cannot_parse(self) -> None:
        value = f"අ{ZWJ}ය{ONLY_FROM_315}"
        schema = _schema("si", "3.13", python_version_min="3.13", keywords={"x": value})
        (finding,) = SchemaValidator.check_min_interpreter_identifier(schema, "si")
        assert "U+088F" in finding.message
        assert "U+200D" not in finding.message  # 3.13 parses the joiner
        (finding,) = SchemaValidator.check_min_interpreter_identifier(
            schema, "si", min_version="3.10"
        )
        assert "U+088F" in finding.message and "U+200D" in finding.message
