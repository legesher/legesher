"""Tests that the git clean filter fails closed on Trojan Source input."""

import io
import sys

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


class TestCleanRejectsUnsupportedScriptIdentifiers:
    """CORE-1558: the positive, script-aware identifier allowlist.

    U+2D7F TIFINAGH CONSONANT JOINER is a nonspacing mark (``Mn``) that is a
    valid ``ID_Continue`` character, NFKC-stable, and NOT Default_Ignorable —
    so the bidi, invisibles, and Default_Ignorable layers all pass it. Nothing
    but membership of a supported script tells it apart from the Arabic
    harakat, which are ``Mn`` too and which Arabic cannot be written without.
    """

    TIFINAGH_JOINER = chr(0x2D7F)

    def test_clean_rejects_tifinagh_joiner_in_identifier(self, spanish_filter):
        malicious = f"to{self.TIFINAGH_JOINER}tal = 1\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1
        assert out.getvalue() == ""

    def test_clean_rejects_the_shadowed_binding_pair(self, spanish_filter):
        # The exploit shape: two bindings a reviewer reads as one name.
        malicious = f"total = 1\nto{self.TIFINAGH_JOINER}tal = 2\nprint(total)\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(malicious), out)
        assert exit_code == 1
        assert self.TIFINAGH_JOINER not in out.getvalue()

    def test_the_earlier_layers_do_not_catch_it(self, spanish_filter):
        # Guards the premise: if scan_text ever starts flagging U+2D7F on its
        # own, this test says so instead of the script layer looking redundant.
        from legesher_core import unicode_guard

        assert unicode_guard.scan_text(f"to{self.TIFINAGH_JOINER}tal") == []

    def test_clean_accepts_the_same_identifier_without_the_joiner(
        self, spanish_filter, spanish_keywords
    ):
        code = f"{spanish_keywords['def']} f():\n    total = 1\n"
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(code), out)
        assert exit_code == 0

    def test_clean_accepts_tifinagh_joiner_inside_a_string_literal(
        self, spanish_filter, spanish_keywords
    ):
        # Prose in any script stays legal: only identifiers become bindings.
        code = (
            f"{spanish_keywords['def']} f():\n"
            f'    x = "ⵜⴰ{self.TIFINAGH_JOINER}ⵎⴰⵣⵉⵖⵜ"\n'
        )
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO(code), out)
        assert exit_code == 0
        assert self.TIFINAGH_JOINER in out.getvalue()

    def test_clean_accepts_arabic_identifier_with_harakat(self, spanish_filter):
        # The false-positive that would make this feature unshippable.
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO("مَرْحَبًا = 1\n"), out)
        assert exit_code == 0

    def test_clean_passes_through_unparseable_source(self, spanish_filter):
        # The identifier scan cannot tokenize incomplete code; a mid-edit
        # `git add` must not start failing because of it.
        out = io.StringIO()
        exit_code = spanish_filter.clean(io.StringIO("def f)(:\n"), out)
        assert exit_code == 0


class TestCleanIdentifierScanIsVersionIndependent:
    """The scan must not depend on the tokenizer producing a NAME token.

    On CPython 3.10 and 3.11 ``tokenize`` is the pure-Python implementation
    whose name pattern is ``\\w+``, which does not match a nonspacing mark:
    ``to<U+2D7F>tal`` lexes as NAME / ERRORTOKEN / NAME and the mark belongs to
    no NAME token. A NAME-driven scan is silently inert on half the supported
    interpreters, for exactly the character class this check exists to catch.
    """

    TIFINAGH_JOINER = chr(0x2D7F)

    def test_joiner_is_caught_whatever_the_tokenizer_calls_it(self, spanish_filter):
        source = f"to{self.TIFINAGH_JOINER}tal = 1\n"
        out = io.StringIO()
        assert spanish_filter.clean(io.StringIO(source), out) == 1

    def test_the_scan_does_not_read_name_tokens(self, spanish_filter):
        # Pins the mechanism, not just the outcome: findings come from code
        # position, so they survive a tokenizer that never forms the name.
        issues = spanish_filter._scan_identifier_scripts(
            f"to{self.TIFINAGH_JOINER}tal = 1\n"
        )
        assert [(i.kind, i.codepoint, i.offset) for i in issues] == [
            ("script", "U+2D7F", 2)
        ]

    def test_offsets_survive_a_form_feed_inside_a_string(self, spanish_filter):
        # str.splitlines breaks on U+000C and the tokenizer does not, so a line
        # table built from splitlines drifts by one per occurrence.
        source = f'x = "a\fb"\ny = to{self.TIFINAGH_JOINER}tal\n'
        issues = spanish_filter._scan_identifier_scripts(source)
        assert [i.offset for i in issues] == [source.index(self.TIFINAGH_JOINER)]


class TestCleanIdentifierFormatAllowlist:
    """A format character licensed in prose must not be licensed in a name."""

    VARIATION_SELECTOR_16 = chr(0xFE0F)
    ZWJ = chr(0x200D)
    ZWNJ = chr(0x200C)

    def test_invisible_in_a_comment_does_not_license_one_in_an_identifier(
        self, spanish_filter
    ):
        # U+FE0F is legitimate emoji presentation in a string, so the
        # string/comment allowlist collects it — and before this scan existed,
        # that licensed it inside a name too, where it silently splits one
        # visible identifier into two bindings.
        vs = self.VARIATION_SELECTOR_16
        source = f'BANNER = "flag{vs} deploy"\nis_ad{vs}min = True\n'
        out = io.StringIO()
        assert spanish_filter.clean(io.StringIO(source), out) == 1
        assert out.getvalue() == ""

    @pytest.mark.skipif(
        sys.version_info < (3, 13),
        reason="ZWJ is an identifier character only from CPython 3.13 "
        "(Unicode 15.1), so the si pack is version-tiered and the 3.13 tier "
        "does not load below it",
    )
    def test_sinhala_zwj_conjunct_is_accepted_under_si(self):
        # The `si` policy declares the ZWJ its conjuncts require.
        source = f"විද්{self.ZWJ}යා = 1\n"
        out = io.StringIO()
        sinhala = GitFilter(language="si", python_version="3.13")
        assert sinhala.clean(io.StringIO(source), out) == 0

    def test_persian_zwnj_is_accepted_under_fa(self):
        source = f"می{self.ZWNJ}رود = 1\n"
        out = io.StringIO()
        persian = GitFilter(language="fa", python_version="3.13")
        assert persian.clean(io.StringIO(source), out) == 0

    def test_persian_zwnj_is_still_rejected_under_a_language_without_it(
        self, spanish_filter
    ):
        source = f"می{self.ZWNJ}رود = 1\n"
        out = io.StringIO()
        assert spanish_filter.clean(io.StringIO(source), out) == 1


class TestCleanAcceptsLegitimateOrthography:
    """The allowlist is positive, so every omission rejects real code."""

    @pytest.mark.skipif(
        sys.version_info < (3, 13),
        reason="U+30FB is an identifier character only from CPython 3.13 "
        "(Unicode 15.1); the ja pack is version-tiered and its 3.13 tier does "
        "not load below that floor",
    )
    def test_accepts_the_ja_packs_own_divmod_rendering(self):
        # A block-only script table refuses U+30FB, which would make the gate
        # reject a keyword Legesher itself ships.
        out = io.StringIO()
        japanese = GitFilter(language="ja", python_version="3.13")
        assert japanese.clean(io.StringIO("ディビジョン・モジュール = 1\n"), out) == 0

    @pytest.mark.parametrize(
        ("language", "source", "why"),
        [
            ("uz", "oʻzgaruvchi = 1\n", "U+02BB — Uzbek orthography"),
            ("es", "xəbər = 1\n", "U+0259 — Latin schwa (IPA Extensions)"),
            ("zh", "\U0002a700 = 1\n", "CJK Extension C"),
            ("el", "a·b = 1\n", "U+0387 — Greek ano teleia"),
            ("ca", "col·leccio = 1\n", "U+00B7 — the Catalan interpunct"),
            ("ru", "ⷠab = 1\n", "U+2DE0 — combining Cyrillic"),
        ],
    )
    def test_accepts(self, language, source, why):
        out = io.StringIO()
        filt = GitFilter(language=language, python_version="3.13")
        assert filt.clean(io.StringIO(source), out) == 0, why
