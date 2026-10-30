"""Coverage tests for the per-language script policy table.

Asserts that *every* shipped language pack has a registered
:class:`ScriptPolicy`, that direction/normalization invariants hold, and that
unknown codes default-deny. A missing policy entry fails CI — this is the
forcing function that keeps the table in lockstep with the packs as the project
grows from 51 to 103 languages.
"""

from __future__ import annotations

import pytest

from legesher_i18n.script_policy import (
    ALWAYS_ALLOWED_SCRIPTS,
    SCRIPT_POLICIES,
    ZWJ,
    ZWNJ,
    ScriptPolicy,
    has_policy,
    identifier_script_of,
    policy_for,
    scripts_of,
    supported_scripts,
)
from tests import language_packs_root
from tests.interpreter_gaps import NEEDS_UNICODE_15_1

# Shipped packs live at libs/i18n/language-packs/<target>; the target segment
# comes from the shared helper (default python).
_PACKS_ROOT = language_packs_root()


def _shipped_language_codes() -> set[str]:
    """Return every language code under language-packs/python (minus index)."""
    return {
        child.name
        for child in _PACKS_ROOT.iterdir()
        if child.is_dir() and child.name != "version-index.yml"
    }


class TestPolicyCoverage:
    """Every shipped pack must have a policy; the table must be self-consistent."""

    def test_every_shipped_pack_has_a_policy(self) -> None:
        shipped = _shipped_language_codes()
        missing = sorted(code for code in shipped if not has_policy(code))
        assert missing == [], (
            f"Languages without a script policy: {missing}. Add entries to "
            "SCRIPT_POLICIES in legesher_i18n/script_policy.py."
        )

    def test_shipped_pack_count_is_56(self) -> None:
        # Guards against silent drift; bump intentionally with the 103 expansion.
        assert len(_shipped_language_codes()) == 56

    def test_policy_table_has_no_orphans(self) -> None:
        # Every policy entry should correspond to a shipped pack (no dead rows).
        shipped = _shipped_language_codes()
        orphans = sorted(set(SCRIPT_POLICIES) - shipped)
        assert orphans == [], f"Policy entries with no shipped pack: {orphans}"

    @pytest.mark.parametrize("code", sorted(SCRIPT_POLICIES))
    def test_each_policy_is_well_formed(self, code: str) -> None:
        policy = policy_for(code)
        assert isinstance(policy, ScriptPolicy)
        assert policy.direction in ("ltr", "rtl")
        assert policy.normalization == "NFKC"
        assert policy.scripts, f"{code} has an empty script set"
        # Common/Inherited must never be listed explicitly — they're implicit.
        assert not (policy.scripts & ALWAYS_ALLOWED_SCRIPTS)

    def test_rtl_languages(self) -> None:
        rtl = {code for code in SCRIPT_POLICIES if policy_for(code).direction == "rtl"}
        assert rtl == {"ar", "fa", "he", "ur"}

    def test_format_char_allowances_are_minimal(self) -> None:
        # Only si (ZWJ), fa (ZWNJ), ur (ZWNJ) may allow-list a format char.
        with_fmt = {
            code for code in SCRIPT_POLICIES if policy_for(code).allowed_format_chars
        }
        assert with_fmt == {"si", "fa", "ur"}

    def test_unknown_language_default_deny(self) -> None:
        assert not has_policy("xx")
        with pytest.raises(KeyError):
            policy_for("xx")

    def test_policy_lookup_is_case_insensitive(self) -> None:
        assert policy_for("EN") is policy_for("en")


class TestScriptsOf:
    """Spot-check the pure-unicodedata script detector."""

    def test_latin(self) -> None:
        assert scripts_of("define") == {"Latin"}

    def test_common_only(self) -> None:
        assert scripts_of("__2_") == {"Common"}

    def test_mixed_latin_common(self) -> None:
        assert scripts_of("bool_2") == {"Latin", "Common"}

    def test_han(self) -> None:
        assert scripts_of("布尔") == {"Han"}

    def test_cyrillic(self) -> None:
        assert scripts_of("логическое") == {"Cyrillic"}

    def test_greek(self) -> None:
        assert scripts_of("λογικό") == {"Greek"}

    def test_arabic(self) -> None:
        assert scripts_of("تعريف") == {"Arabic"}

    def test_mixed_detects_both(self) -> None:
        # Latin + Han: the foreign-script failure mode.
        assert scripts_of("bool布尔") == {"Latin", "Han"}


class TestIdentifierAllowlist:
    """CORE-1558: the positive, script-aware identifier allowlist.

    :func:`scripts_of` answers "does this pack value stay inside its language's
    scripts". :func:`identifier_script_of` answers the engine's narrower
    question about a character it is about to emit into runnable code, and it
    has to be stricter: the pack classifier reports any unrecognised combining
    mark as ``Inherited``, which would wave through an invisible joiner from a
    script nothing ships.
    """

    #: The cross-engine contract. ``SUPPORTED_SCRIPTS`` in ``@legesher/core``'s
    #: ``script-allowlist.ts`` (the JavaScript engine) carries the same names; the two
    #: engines ship from different repositories, so this list is the forcing
    #: function — adding a language whose script is new fails here, and the
    #: failure is the reminder to update the JavaScript engine in the same beat.
    PINNED_SCRIPTS = {
        "Arabic",
        "Bengali",
        "Cyrillic",
        "Devanagari",
        "Ethiopic",
        "Greek",
        "Gujarati",
        "Han",
        "Hangul",
        "Hebrew",
        "Hiragana",
        "Kannada",
        "Katakana",
        "Latin",
        "Malayalam",
        "Myanmar",
        "Sinhala",
        "Telugu",
        "Thai",
    }

    def test_supported_scripts_is_the_union_of_the_policies(self) -> None:
        expected: set[str] = set()
        for policy in SCRIPT_POLICIES.values():
            expected |= policy.scripts
        assert supported_scripts() == expected

    def test_supported_scripts_matches_the_pinned_cross_engine_list(self) -> None:
        assert supported_scripts() == self.PINNED_SCRIPTS

    def test_supported_scripts_excludes_the_always_allowed_pseudo_scripts(self) -> None:
        assert not (supported_scripts() & ALWAYS_ALLOWED_SCRIPTS)

    def test_rejects_the_tifinagh_consonant_joiner(self) -> None:
        # U+2D7F: Mn + ID_Continue, NOT Default_Ignorable, NFKC-stable — the
        # exact character every property-based net misses.
        assert identifier_script_of("⵿") == "Unknown"

    def test_the_pack_classifier_would_have_admitted_it(self) -> None:
        # Records WHY a second classifier exists: the pack-value fallback calls
        # it Inherited, which an identifier gate must not accept.
        assert scripts_of("⵿") == {"Inherited"}

    def test_keeps_arabic_harakat(self) -> None:
        # Same general category as U+2D7F and essential to Arabic — the reason
        # a blanket Mn rejection is not an option.
        assert identifier_script_of("ً") == "Arabic"

    def test_keeps_generic_combining_marks_as_inherited(self) -> None:
        assert identifier_script_of("́") == "Inherited"  # combining acute

    def test_format_characters_defer_to_the_invisibles_layer(self) -> None:
        # ZWJ/ZWNJ carry no script here: the guard's invisibles net and the
        # per-language allowed_format_chars decide them, so classifying them
        # would double-report or silently re-admit.
        assert identifier_script_of(ZWJ) == "Common"
        assert identifier_script_of(ZWNJ) == "Common"

    def test_ascii_identifier_characters_are_common(self) -> None:
        for char in "0_$":
            assert identifier_script_of(char) == "Common", char

    def test_letters_from_unshipped_scripts_are_unknown(self) -> None:
        assert identifier_script_of("க") == "Unknown"  # Tamil KA

    def test_katakana_middle_dot_resolves_to_katakana(self) -> None:
        # U+30FB is Script=Common but Script_Extensions names Katakana, and the
        # shipped `ja` pack renders `divmod` as ディビジョン・モジュール on 3.13+.
        # A block-only table calls it Unknown and rejects a value we ship.
        assert identifier_script_of("・") == "Katakana"

    @NEEDS_UNICODE_15_1
    def test_the_shipped_japanese_divmod_rendering_is_writable(self) -> None:
        value = "ディビジョン・モジュール"
        assert value.isidentifier()
        allowed = supported_scripts() | ALWAYS_ALLOWED_SCRIPTS
        assert {identifier_script_of(ch) for ch in value} <= allowed

    def test_catalan_interpunct_resolves_to_latin(self) -> None:
        # U+00B7 is a Python identifier character (Other_ID_Continue) and its
        # Script_Extensions include Latin — col·lecció is ordinary Catalan.
        assert identifier_script_of("·") == "Latin"

    def test_ideographic_iteration_mark_resolves_to_han(self) -> None:
        assert identifier_script_of("々") == "Han"

    def test_every_shipped_pack_value_stays_writable(self) -> None:
        # The whole-corpus check: no shipped pack value may contain a character
        # the identifier gate refuses, or the gate breaks Legesher's own output.
        allowed = supported_scripts() | ALWAYS_ALLOWED_SCRIPTS
        offenders: set[str] = set()
        for path in _PACKS_ROOT.rglob("packs/*.yml"):
            for value in _pack_string_values(path):
                if not value.isidentifier():
                    continue
                offenders |= {
                    f"{hex(ord(ch))} in {value}"
                    for ch in value
                    if identifier_script_of(ch) not in allowed
                }
        assert offenders == set()

    def test_every_policy_script_classifies_a_sample_correctly(self) -> None:
        samples = {
            "Arabic": "م",
            "Bengali": "ক",
            "Cyrillic": "д",
            "Devanagari": "क",
            "Ethiopic": "አ",
            "Greek": "α",
            "Gujarati": "ક",
            "Han": "合",
            "Hangul": "합",
            "Hebrew": "א",
            "Hiragana": "あ",
            "Kannada": "ಕ",
            "Katakana": "ア",
            "Latin": "a",
            "Malayalam": "ക",
            "Myanmar": "က",
            "Sinhala": "අ",
            "Telugu": "క",
            "Thai": "ก",
        }
        assert set(samples) == supported_scripts()
        for script, sample in samples.items():
            assert identifier_script_of(sample) == script, script


def _pack_string_values(path) -> list[str]:
    """Yield every string leaf of a pack YAML file."""
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []

    values: list[str] = []
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, str):
            values.append(node)
    return values


class TestFormatCharAllowlistGuard:
    """No policy may punch a hole for a character the net exists to block.

    Every consumer of ``allowed_format_chars`` — the pack gate
    (``check_format_chars``), the intake gates, the carried-forward canon
    backfill — checks the allowlist BEFORE the forbidden set, deliberately
    (parity across layers). That ordering makes an allowlisted bidi control an
    unconditional pass through every layer at once, so the guarantee belongs
    in the type, not in review habits (CORE-2029 review finding).
    """

    def test_no_registered_policy_allowlists_a_forbidden_char(self) -> None:
        import unicodedata

        from legesher_i18n.script_policy import FORBIDDEN_FORMAT_CHARS

        for code, policy in SCRIPT_POLICIES.items():
            leaked = policy.allowed_format_chars & FORBIDDEN_FORMAT_CHARS
            assert not leaked, f"{code}: allowlists forbidden {sorted(leaked)}"
            non_cf = [
                f"U+{ord(ch):04X}"
                for ch in policy.allowed_format_chars
                if unicodedata.category(ch) != "Cf"
            ]
            assert non_cf == [], f"{code}: non-Cf allowlist entries {non_cf}"

    def test_the_constructor_refuses_a_bidi_control(self) -> None:
        # Spelled as an escape so the dangerous character never appears
        # literally in this file (the script_policy convention).
        with pytest.raises(ValueError, match=r"U\+202B"):
            ScriptPolicy(
                scripts=frozenset({"Arabic"}),
                allowed_format_chars=frozenset({"\u202b"}),
            )

    def test_the_constructor_refuses_tatweel_and_bom(self) -> None:
        from legesher_i18n.script_policy import BOM, TATWEEL

        for ch in (TATWEEL, BOM):
            with pytest.raises(ValueError, match="forbidden"):
                ScriptPolicy(
                    scripts=frozenset({"Arabic"}),
                    allowed_format_chars=frozenset({ch}),
                )

    def test_the_constructor_refuses_a_non_format_character(self) -> None:
        # Inert-looking but wrong in kind: the allowlist is for Cf characters
        # an orthography requires, and a letter here is a category error.
        with pytest.raises(ValueError, match="not Cf"):
            ScriptPolicy(
                scripts=frozenset({"Latin"}),
                allowed_format_chars=frozenset({"a"}),
            )

    def test_the_legitimate_holes_still_construct(self) -> None:
        # The guard must not refuse the two real orthographic requirements.
        assert policy_for("si").allowed_format_chars == frozenset({ZWJ})
        assert policy_for("fa").allowed_format_chars == frozenset({ZWNJ})
