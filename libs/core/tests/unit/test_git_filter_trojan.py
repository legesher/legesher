"""Tests that the git clean filter fails closed on Trojan Source input."""

import io

import pytest

from legesher_core.git_filter import GitFilter


@pytest.fixture
def spanish_filter():
    return GitFilter(language="es", python_version="3.13")


class TestCleanRejectsTrojanSource:
    def test_clean_rejects_rlo_reorder(self, spanish_filter):
        malicious = 'x = "user‮"\nprint(x)\n'
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1  # fail closed
        assert "‮" not in out.getvalue()
        assert out.getvalue() == ""  # nothing written to stdout

    def test_clean_rejects_invisible_zero_width(self, spanish_filter):
        malicious = "ad​min = True\n"  # zero-width space hides split
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1
        assert "​" not in out.getvalue()

    def test_clean_rejects_interior_bom(self, spanish_filter):
        # A leading BOM is stripped and allowed; an INTERIOR U+FEFF is a
        # zero-width invisible and must fail the filter, not slip through as an
        # advisory "bom" issue (CORE-1557).
        malicious = "ad﻿min = True\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1
        assert "﻿" not in out.getvalue()
        assert out.getvalue() == ""


class TestCleanRejectsDefaultIgnorable:
    """CORE-1559: the clean filter must fail closed on Default_Ignorable marks
    that are NOT category Cf (combining grapheme joiner, Hangul fillers,
    variation selectors), closing the parallel of the JS gap CORE-1556 fixed.
    """

    def test_clean_rejects_interior_combining_grapheme_joiner(self, spanish_filter):
        cgj = chr(0x034F)
        # `total` and `to<CGJ>tal` are visually identical but distinct bindings.
        malicious = f"total = 1\nto{cgj}tal = 2\nprint(total, to{cgj}tal)\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1
        assert cgj not in out.getvalue()
        assert out.getvalue() == ""

    def test_clean_rejects_trailing_variation_selector(self, spanish_filter):
        vs1 = chr(0xFE00)
        malicious = f"total{vs1} = 1\nprint(total{vs1})\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1
        assert vs1 not in out.getvalue()

    def test_clean_rejects_hangul_filler_identifier(self, spanish_filter):
        filler = chr(0x115F)
        malicious = f"{filler}x = 1\nprint({filler}x)\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1
        assert filler not in out.getvalue()


class TestCleanAcceptsLegitimateContent:
    def test_clean_accepts_normal_rtl_string_literal(
        self, spanish_filter, spanish_keywords
    ):
        code = f'{spanish_keywords["def"]} f():\n    x = "مرحبا"\n'
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(code), out)
        assert exit_code == 0
        assert "مرحبا" in out.getvalue()

    def test_clean_strips_leading_bom(self, spanish_filter, spanish_keywords):
        code = f"﻿{spanish_keywords['def']} f():\n    pass\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(code), out)
        assert exit_code == 0
        assert not out.getvalue().startswith("﻿")

    def test_clean_accepts_emoji_variation_selector_in_string(
        self, spanish_filter, spanish_keywords
    ):
        # A variation selector (U+FE0F) is Default_Ignorable, but inside a
        # string literal it is legitimate emoji presentation — the string/comment
        # allowlist must keep letting it through (preserve existing behavior).
        heart = "❤️"  # ❤️ = HEAVY BLACK HEART + VARIATION SELECTOR-16
        code = f'{spanish_keywords["def"]} f():\n    x = "{heart}"\n'
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(code), out)
        assert exit_code == 0
        assert "️" in out.getvalue()
