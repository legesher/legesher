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
