"""Tests for the engine-side Unicode/script security guard."""

from legesher_core import unicode_guard
from legesher_core.unicode_guard import (
    BIDI_CONTROLS,
    INVISIBLE_FORMAT,
    Issue,
    has_trojan_source,
    scan_text,
    strip_bom,
)


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

    def test_detects_bom_anywhere(self):
        text = "abc﻿def"
        issues = scan_text(text)
        assert any(i.kind == "bom" and i.offset == 3 for i in issues)

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
