"""Coverage tests for the per-language script policy table.

Asserts that *every* shipped language pack has a registered
:class:`ScriptPolicy`, that direction/normalization invariants hold, and that
unknown codes default-deny. A missing policy entry fails CI — this is the
forcing function that keeps the table in lockstep with the packs as the project
grows from 51 to 103 languages.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from legesher_i18n.script_policy import (
    ALWAYS_ALLOWED_SCRIPTS,
    SCRIPT_POLICIES,
    ScriptPolicy,
    has_policy,
    policy_for,
    scripts_of,
)

# language-packs/python lives at libs/i18n/language-packs/python; this test file
# is at libs/i18n/tests/test_*.py.
_PACKS_ROOT = Path(__file__).resolve().parents[1] / "language-packs" / "python"


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

    def test_shipped_pack_count_is_51(self) -> None:
        # Guards against silent drift; bump intentionally with the 103 expansion.
        assert len(_shipped_language_codes()) == 51

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
