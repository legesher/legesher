"""Tests for the engine-side Unicode/script security guard."""

from legesher_core import unicode_guard
from legesher_core.unicode_guard import (
    BIDI_CONTROLS,
    DEFAULT_IGNORABLE,
    INVISIBLE_FORMAT,
    Issue,
    has_trojan_source,
    is_default_ignorable,
    scan_text,
    strip_bom,
)

# Default_Ignorable_Code_Point members that are NOT category Cf, so the old
# ``category == "Cf"`` invisible check missed them entirely (CORE-1559 / the
# parallel of the JS gap CORE-1556 closed).
CGJ = chr(0x034F)  # COMBINING GRAPHEME JOINER (Mn)
HANGUL_CHOSEONG_FILLER = chr(0x115F)  # (Lo)
HANGUL_JUNGSEONG_FILLER = chr(0x1160)  # (Lo)
VARIATION_SELECTOR_1 = chr(0xFE00)  # (Mn)
VARIATION_SELECTOR_16 = chr(0xFE0F)  # (Mn)


class TestConstants:
    def test_bidi_controls_contains_rlo_and_pdi(self):
        assert "‮" in BIDI_CONTROLS  # RLO
        assert "⁩" in BIDI_CONTROLS  # PDI
        assert "؜" in BIDI_CONTROLS  # ALM

    def test_invisible_format_contains_zwj_zwnj_and_bom(self):
        assert "‍" in INVISIBLE_FORMAT  # ZWJ
        assert "‌" in INVISIBLE_FORMAT  # ZWNJ
        assert "﻿" in INVISIBLE_FORMAT  # BOM is category Cf

    def test_ascii_not_format(self):
        assert "a" not in INVISIBLE_FORMAT

    def test_default_ignorable_contains_non_cf_marks(self):
        # These are the non-Cf Default_Ignorable code points that the plain
        # ``category == "Cf"`` check cannot see (CORE-1559).
        assert CGJ in DEFAULT_IGNORABLE
        assert HANGUL_CHOSEONG_FILLER in DEFAULT_IGNORABLE
        assert HANGUL_JUNGSEONG_FILLER in DEFAULT_IGNORABLE
        assert VARIATION_SELECTOR_1 in DEFAULT_IGNORABLE
        assert VARIATION_SELECTOR_16 in DEFAULT_IGNORABLE

    def test_default_ignorable_contains_known_cf_overlap(self):
        # BOM and the zero-width invisibles are themselves Default_Ignorable.
        assert "﻿" in DEFAULT_IGNORABLE  # BOM
        assert "​" in DEFAULT_IGNORABLE  # ZERO WIDTH SPACE

    def test_default_ignorable_excludes_plain_letters(self):
        assert "a" not in DEFAULT_IGNORABLE
        assert "ا" not in DEFAULT_IGNORABLE  # Arabic letter alef


class TestIsDefaultIgnorable:
    def test_true_for_non_cf_marks(self):
        assert is_default_ignorable(CGJ)
        assert is_default_ignorable(VARIATION_SELECTOR_16)
        assert is_default_ignorable(HANGUL_JUNGSEONG_FILLER)

    def test_true_for_supplementary_variation_selectors(self):
        assert is_default_ignorable(chr(0xE0100))  # VARIATION SELECTOR-17
        assert is_default_ignorable(chr(0xE01EF))  # VARIATION SELECTOR-256

    def test_false_for_ordinary_characters(self):
        assert not is_default_ignorable("a")
        assert not is_default_ignorable("한")  # Hangul syllable, not a filler
        assert not is_default_ignorable("")


class TestDefaultIgnorableRejection:
    """CORE-1559: reject the full Default_Ignorable set, not just category Cf.

    Parity with the JS guard's ``\\p{Default_Ignorable_Code_Point}`` net
    (CORE-1556). These render as nothing yet are valid identifier characters
    and NFKC-stable, so two visually identical identifiers can differ by one of
    them in the runnable canonical output — the WYSIWYG bypass this guard exists
    to surface.
    """

    def test_rejects_combining_grapheme_joiner(self):
        issues = scan_text(f"to{CGJ}tal")
        assert any(i.kind == "invisible" and i.offset == 2 for i in issues)
        assert any(i.codepoint == "U+034F" for i in issues)

    def test_rejects_hangul_choseong_filler(self):
        issues = scan_text(f"a{HANGUL_CHOSEONG_FILLER}b")
        assert any(i.kind == "invisible" and i.codepoint == "U+115F" for i in issues)

    def test_rejects_hangul_jungseong_filler(self):
        issues = scan_text(f"a{HANGUL_JUNGSEONG_FILLER}b")
        assert any(i.kind == "invisible" and i.codepoint == "U+1160" for i in issues)

    def test_rejects_variation_selector_1(self):
        issues = scan_text(f"total{VARIATION_SELECTOR_1}")
        assert any(i.kind == "invisible" and i.codepoint == "U+FE00" for i in issues)

    def test_rejects_variation_selector_16(self):
        issues = scan_text(f"total{VARIATION_SELECTOR_16}")
        assert any(i.kind == "invisible" and i.codepoint == "U+FE0F" for i in issues)

    def test_two_visually_identical_bindings_both_flagged(self):
        # total vs to<CGJ>tal look identical but are distinct bindings.
        issues = scan_text(f"total = 1\nto{CGJ}tal = 2\n")
        assert any(i.codepoint == "U+034F" for i in issues)

    def test_default_ignorable_respects_allowlist(self):
        # Parity with the Cf branch: an allowlisted DI char (e.g. an emoji
        # variation selector inside a string literal) is not reported.
        issues = scan_text(
            f"x = {VARIATION_SELECTOR_16}", allowed_format_chars={VARIATION_SELECTOR_16}
        )
        assert all(i.codepoint != "U+FE0F" for i in issues)

    def test_leading_bom_still_allowed_at_index_zero(self):
        # BOM is Default_Ignorable, but a leading BOM must stay the advisory
        # ``bom`` kind (index-0 exception preserved), never a blocking invisible.
        issues = scan_text("﻿x")
        assert issues[0].kind == "bom"
        assert issues[0].offset == 0
        assert all(i.kind != "invisible" for i in issues)


class TestHasTrojanSource:
    def test_classic_cve_2021_42574_comment_reorder(self):
        sample = (
            'access_level = "user"\n'
            'if access_level != "user‮ ⁦# Check if admin⁩ ⁦":\n'
            "    grant_admin()\n"
        )
        assert has_trojan_source(sample) is True

    def test_clean_code_is_not_trojan(self):
        assert has_trojan_source("def foo():\n    return 42\n") is False

    def test_rtl_string_literal_without_controls_is_clean(self):
        assert has_trojan_source('msg = "مرحبا"\n') is False


class TestScanText:
    def test_detects_rlo_with_offset_and_codepoint(self):
        text = "x‮y"
        issues = scan_text(text)
        assert len(issues) == 1
        assert issues[0].kind == "bidi"
        assert issues[0].codepoint == "U+202E"
        assert issues[0].offset == 1

    def test_detects_invisible_zero_width_space(self):
        text = "ab​cd"  # U+200B ZERO WIDTH SPACE, category Cf
        issues = scan_text(text)
        assert any(i.kind == "invisible" and i.offset == 2 for i in issues)

    def test_detects_tatweel_with_offset(self):
        text = "naـme"
        issues = scan_text(text)
        assert any(i.kind == "tatweel" and i.offset == 2 for i in issues)

    def test_interior_bom_reported_as_blocking_invisible(self):
        # An interior U+FEFF is a zero-width invisible, not a legitimate BOM.
        # It must surface as the blocking ``invisible`` kind (not the advisory
        # ``bom`` kind) so the git clean filter rejects it (CORE-1557).
        issues = scan_text("abc﻿def")
        interior = [i for i in issues if i.offset == 3]
        assert interior and interior[0].kind == "invisible"
        assert all(i.kind != "bom" for i in issues)

    def test_interior_bom_respects_allowlist(self):
        # Parity with the general Cf branch: an allowlisted interior FEFF
        # (e.g. inside a string/comment token) is not reported.
        issues = scan_text("abc﻿def", allowed_format_chars={"﻿"})
        assert all(i.offset != 3 for i in issues)

    def test_leading_bom_reported_as_bom(self):
        issues = scan_text("﻿x")
        assert issues[0].kind == "bom"
        assert issues[0].offset == 0

    def test_clean_text_returns_empty(self):
        assert scan_text("def foo():\n    return 42\n") == []

    def test_issue_is_frozen_dataclass(self):
        issue = Issue("bidi", "U+202E", 0, "X", "msg")
        assert hash(issue) is not None


class TestAllowlist:
    def test_allowed_zwj_is_not_reported(self):
        text = "x‍y"  # ZWJ between two letters
        assert any(i.codepoint == "U+200D" for i in scan_text(text))
        issues = scan_text(text, allowed_format_chars={"‍"})
        assert all(i.codepoint != "U+200D" for i in issues)

    def test_allowlist_never_suppresses_bidi(self):
        issues = scan_text("x‮y", allowed_format_chars={"‮"})
        assert any(i.kind == "bidi" for i in issues)


class TestStripBom:
    def test_strips_leading_bom(self):
        assert strip_bom("﻿hello") == "hello"

    def test_leaves_interior_bom(self):
        assert strip_bom("a﻿b") == "a﻿b"

    def test_noop_without_bom(self):
        assert strip_bom("hello") == "hello"

    def test_module_exposes_strip_bom(self):
        assert unicode_guard.strip_bom("﻿z") == "z"
