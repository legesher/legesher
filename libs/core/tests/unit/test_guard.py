"""The guard refuses what the clean filter no longer can (CORE-1841).

A clean filter cannot refuse: git treats a failing filter as a passthrough and
commits the file unchanged. So the Unicode refusals the filter used to raise
(CORE-1343, CORE-1557, CORE-1558, CORE-1559) are the guard's now, and it adds
the keyword check: a staged file whose keywords are not in its block's stored
form. Cases carried over from the filter's Trojan Source suite keep their
original intent, with "exit 1" becoming "a finding".
"""

import sys

import pytest

from legesher_core import unicode_guard
from legesher_core.guard import (
    Finding,
    check_blob,
    check_source,
    identifier_script_issues,
    scan_unicode,
)
from legesher_core.stored_form import keyword_table

ES = keyword_table("es")
AR = keyword_table("ar")


def kinds(text: str, language: str = "es") -> list[str]:
    return [issue.kind for issue in scan_unicode(text, language)]


class TestTrojanSource:
    def test_rlo_reorder_in_a_string(self):
        assert kinds('x = "user\u202e"\nprint(x)\n') == ["bidi"]

    def test_zero_width_space_splitting_a_name(self):
        assert kinds("ad\u200bmin = True\n") == ["invisible"]

    def test_interior_bom(self):
        # A leading BOM is allowed; an interior U+FEFF is a zero-width
        # invisible, not an advisory (CORE-1557).
        assert kinds("ad\ufeffmin = True\n") == ["invisible"]

    def test_a_leading_bom_is_allowed(self):
        assert kinds("\ufeffdefinir f():\n    pasar\n") == []


class TestDefaultIgnorable:
    """CORE-1559: Default_Ignorable marks that are not category Cf."""

    def test_interior_combining_grapheme_joiner(self):
        cgj = chr(0x034F)
        assert "invisible" in kinds(f"total = 1\nto{cgj}tal = 2\n")

    def test_trailing_variation_selector(self):
        vs1 = chr(0xFE00)
        assert "invisible" in kinds(f"total{vs1} = 1\n")

    def test_hangul_filler_identifier(self):
        filler = chr(0x115F)
        assert "invisible" in kinds(f"{filler}x = 1\n")


class TestLegitimateContent:
    def test_rtl_string_literal(self):
        assert kinds('definir f():\n    x = "مرحبا"\n') == []

    def test_emoji_variation_selector_in_a_string(self):
        assert kinds('definir f():\n    x = "\u2764\ufe0f"\n') == []


class TestUnsupportedScriptIdentifiers:
    """CORE-1558: U+2D7F passes the bidi, invisible and Default_Ignorable
    layers; only script membership tells it from the Arabic harakat."""

    TIFINAGH_JOINER = chr(0x2D7F)

    def test_tifinagh_joiner_in_a_name(self):
        assert kinds(f"to{self.TIFINAGH_JOINER}tal = 1\n") == ["script"]

    def test_the_earlier_layers_do_not_catch_it(self):
        assert unicode_guard.scan_text(f"to{self.TIFINAGH_JOINER}tal") == []

    def test_the_same_name_without_the_joiner(self):
        assert kinds("definir f():\n    total = 1\n") == []

    def test_the_joiner_inside_a_string_literal(self):
        assert kinds(f'x = "ⵜⴰ{self.TIFINAGH_JOINER}ⵎⴰⵣⵉⵖⵜ"\n') == []

    def test_arabic_name_with_harakat(self):
        assert kinds("مَرْحَبًا = 1\n") == []

    def test_unparseable_source_gets_the_whole_text_scan_only(self):
        assert kinds("def f)(:\n") == []

    def test_the_scan_does_not_read_name_tokens(self):
        # Findings come from code position, so they survive a tokenizer that
        # never forms the name (CPython 3.10 and 3.11).
        issues = identifier_script_issues(f"to{self.TIFINAGH_JOINER}tal = 1\n", "es")
        assert [(i.kind, i.codepoint, i.offset) for i in issues] == [
            ("script", "U+2D7F", 2)
        ]

    def test_a_lone_cr_does_not_shift_the_spans(self):
        # Regression: the line table broke at a lone CR while tokenize did
        # not, so every span after it landed at the wrong offset and a name
        # in an unsupported script passed the staged check.
        source = "a = 1\rb\U00013000 = 2\n'xxxxxxxxxxxx'\n"
        issues = identifier_script_issues(source, "es")
        assert [(i.kind, i.offset) for i in issues] == [("script", 7)]

    def test_code_after_a_comment_ending_in_a_lone_cr_is_scanned(self):
        # Python ends the comment at the CR and runs the next line; tokenize
        # over the raw text reads it all as one comment, exempt from the scan.
        source = "# note\rb\U00013000 = 2\n"
        issues = identifier_script_issues(source, "es")
        assert [(i.kind, i.offset) for i in issues] == [("script", 8)]

    def test_a_lone_cr_that_breaks_tokenize_does_not_disable_the_scan(self):
        # Security re-review of CORE-1841: over the raw text tokenize fails
        # (the CR is not a line break to it), the spans come back None and the
        # scan skipped the file, although Python compiles and runs it.
        source = 'y\u13a0\r# c"""q\n'
        compile(source, "probe", "exec")
        assert [(i.kind, i.codepoint) for i in scan_unicode(source, "es")] == [
            ("script", "U+13A0")
        ]

    def test_a_string_after_such_a_lone_cr_is_still_prose(self):
        # With the lone-CR view the spans are exact, so the fail-closed scan
        # of the whole text is not needed and a string stays prose.
        source = 'y = 1\r# c"""q\ns = \'\u13a0\'\n'
        compile(source, "probe", "exec")
        assert scan_unicode(source, "es") == []

    def test_source_python_runs_but_tokenize_cannot_read_is_scanned_whole(
        self, monkeypatch
    ):
        # Fail closed: without string and comment spans, every character of a
        # file that compiles is treated as code position.
        from legesher_core import guard

        monkeypatch.setattr(guard, "_literal_spans", lambda source: None)
        issues = identifier_script_issues("b\U00013000 = 2\n", "es")
        assert [(i.kind, i.offset) for i in issues] == [("script", 1)]

    def test_the_whole_text_scan_prints_no_warnings_about_the_users_code(
        self, monkeypatch
    ):
        import warnings

        from legesher_core import guard

        monkeypatch.setattr(guard, "_literal_spans", lambda source: None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            identifier_script_issues("x = '\\d'\n", "es")
        assert [w for w in caught if issubclass(w.category, SyntaxWarning)] == []

    def test_a_character_in_a_string_after_a_lone_cr_is_prose(self):
        source = "a = 1\rb = '\U00013000'\n"
        assert identifier_script_issues(source, "es") == []

    def test_offsets_survive_a_form_feed_inside_a_string(self):
        source = f'x = "a\fb"\ny = to{self.TIFINAGH_JOINER}tal\n'
        issues = identifier_script_issues(source, "es")
        assert [i.offset for i in issues] == [source.index(self.TIFINAGH_JOINER)]


class TestIdentifierFormatAllowlist:
    VARIATION_SELECTOR_16 = chr(0xFE0F)
    ZWJ = chr(0x200D)
    ZWNJ = chr(0x200C)

    def test_an_invisible_in_prose_does_not_license_one_in_a_name(self):
        vs = self.VARIATION_SELECTOR_16
        source = f'BANNER = "flag{vs} deploy"\nis_ad{vs}min = True\n'
        assert "invisible" in kinds(source)

    @pytest.mark.skipif(
        sys.version_info < (3, 13),
        reason="ZWJ is an identifier character only from CPython 3.13 "
        "(Unicode 15.1), so the si pack's 3.13 tier does not load below it",
    )
    def test_sinhala_zwj_conjunct_under_si(self):
        assert kinds(f"විද්{self.ZWJ}යා = 1\n", "si") == []

    def test_persian_zwnj_under_fa(self):
        assert kinds(f"می{self.ZWNJ}رود = 1\n", "fa") == []

    def test_persian_zwnj_under_a_language_without_it(self):
        assert "invisible" in kinds(f"می{self.ZWNJ}رود = 1\n", "es")


class TestLegitimateOrthography:
    @pytest.mark.skipif(
        sys.version_info < (3, 13),
        reason="U+30FB is an identifier character only from CPython 3.13",
    )
    def test_the_ja_packs_own_divmod_rendering(self):
        assert kinds("ディビジョン・モジュール = 1\n", "ja") == []

    @pytest.mark.parametrize(
        ("language", "source", "why"),
        [
            ("uz", "oʻzgaruvchi = 1\n", "U+02BB, Uzbek orthography"),
            ("es", "xəbər = 1\n", "U+0259, Latin schwa (IPA Extensions)"),
            ("zh", "\U0002a700 = 1\n", "CJK Extension C"),
            ("el", "a·b = 1\n", "U+0387, Greek ano teleia"),
            ("ca", "col·leccio = 1\n", "U+00B7, the Catalan interpunct"),
            ("ru", "ⷠab = 1\n", "U+2DE0, combining Cyrillic"),
        ],
    )
    def test_accepts(self, language, source, why):
        assert kinds(source, language) == [], why


class TestCheckSource:
    def test_a_clean_spanish_file_has_no_findings(self):
        text = "definir f(x):\n    si x:\n        devolver 1\n"
        assert check_source(text, path="a.py", local=ES) == []

    def test_an_english_stray_is_reported_where_it_stands(self):
        text = "definir f(x):\n    if x:\n        devolver 1\n"
        (finding,) = check_source(text, path="src/a.py", local=ES)
        assert (finding.path, finding.line, finding.column, finding.check) == (
            "src/a.py",
            2,
            5,
            "keyword",
        )
        assert "`if`" in finding.message and "`si`" in finding.message

    def test_the_stored_version_decides_the_block(self):
        stored = "def f(x):\n    return x\n"
        text = "def f(x):\n    si x:\n        return x\n"
        (finding,) = check_source(text, path="a.py", local=ES, stored=stored)
        assert (finding.line, finding.column) == (2, 5)
        assert "`si`" in finding.message and "`if`" in finding.message

    def test_an_arabic_stray_column_counts_characters(self):
        text = "تعريف f(x):\n    إذا x:\n        return x\n"
        (finding,) = check_source(text, path="a.py", local=AR)
        assert (finding.line, finding.column) == (3, 9)

    def test_a_leading_bom_is_not_a_column(self):
        text = "\ufeffif x:\n    devolver\n    pasar\n"
        (finding,) = check_source(text, path="a.py", local=ES)
        assert (finding.line, finding.column) == (1, 1)

    def test_a_lone_cr_is_a_line(self):
        text = "a = 1\rb\U00013000 = 2\n"
        (finding,) = check_source(text, path="a.py", local=ES)
        assert (finding.line, finding.column, finding.check) == (2, 2, "unicode")

    def test_a_unicode_finding_carries_line_and_column(self):
        text = "definir f():\n    ad\u200bmin = 1\n"
        (finding,) = check_source(text, path="a.py", local=ES)
        assert (finding.line, finding.column, finding.check) == (2, 7, "unicode")
        assert "U+200B" in finding.message

    def test_findings_are_ordered_by_position(self):
        text = 'definir f(x):\n    x = "\u202e"\n    return 1\n    pasar\n'
        findings = check_source(text, path="a.py", local=ES)
        assert [(f.line, f.check) for f in findings] == [
            (2, "unicode"),
            (3, "keyword"),
        ]

    def test_format_is_path_line_column(self):
        text = "definir f(x):\n    if x:\n        devolver 1\n"
        (finding,) = check_source(text, path="a.py", local=ES)
        assert finding.format().startswith("a.py:2:5: keyword: ")


class TestCheckBlob:
    """The guard reads bytes: an encoding it cannot vouch for is a finding."""

    def test_utf8_is_checked_as_text(self):
        data = "definir f(x):\n    if x:\n        devolver 1\n".encode()
        (finding,) = check_blob(data, path="a.py", local=ES)
        assert finding.check == "keyword"

    def test_bytes_that_are_not_utf8_are_a_finding(self):
        data = b"# coding: cp1256\nx\xdc = 1\n"
        (finding,) = check_blob(data, path="a.py", local=ES)
        assert (finding.check, finding.line) == ("encoding", 1)
        assert "cp1256" in finding.message

    def test_undecodable_bytes_without_a_declaration_are_a_finding(self):
        (finding,) = check_blob(b"x = '\xff'\n", path="a.py", local=ES)
        assert finding.check == "encoding"
        assert "UTF-8" in finding.message

    def test_a_utf7_declaration_is_a_finding_even_in_ascii(self):
        # Pure ASCII, so it decodes as UTF-8, but Python would decode it as
        # UTF-7 and run what `+...-` sequences hide.
        data = b"# -*- coding: utf-7 -*-\ns = 'a+ACI- ; t = 1'\n"
        (finding,) = check_blob(data, path="a.py", local=ES)
        assert finding.check == "encoding"
        assert "utf-7" in finding.message

    @pytest.mark.parametrize(
        "cookie", [b"# coding: utf-8\n", b"# -*- coding: utf_8 -*-\n"]
    )
    def test_a_utf8_declaration_is_fine(self, cookie):
        assert check_blob(cookie + b"x = 1\n", path="a.py", local=ES) == []

    @pytest.mark.parametrize(
        "cookie",
        [b"# -*- coding: utf8 -*-\n", b"# coding: UTF8\n", b"# coding: ascii\n"],
    )
    def test_other_spellings_of_utf8_and_ascii_are_fine(self, cookie):
        assert check_blob(cookie + b"x = 1\n", path="a.py", local=ES) == []

    def test_an_ascii_declaration_over_non_ascii_bytes_is_a_finding(self):
        (finding,) = check_blob(
            "# coding: ascii\nx = 'é'\n".encode(), path="a.py", local=ES
        )
        assert finding.check == "encoding"

    def test_a_utf8_bom_is_fine(self):
        assert check_blob(b"\xef\xbb\xbfx = 1\n", path="a.py", local=ES) == []


class TestLegesherArtifacts:
    """CORE-1323: files under `.legesher/` parse, match their own format, and
    never point outside the repository. Map-engine artifacts are opaque here:
    their format is never described or checked."""

    def check(self, path, data, mode="100644"):
        from legesher_core.guard import check_artifact

        return check_artifact(path, data, mode=mode)

    def test_a_symlink_under_legesher_is_a_finding(self):
        (finding,) = self.check(".legesher/config.yml", b"/etc/passwd", mode="120000")
        assert (finding.check, finding.path) == ("artifact", ".legesher/config.yml")
        assert "symlink" in finding.message

    def test_a_valid_config(self):
        data = b"language: es\ngit:\n  enabled: true\nmetadata:\n  directory: .legesher/metadata\n"
        assert self.check(".legesher/config.yml", data) == []

    def test_config_that_is_not_yaml(self):
        (finding,) = self.check(".legesher/config.yml", b"language: [es\n")
        assert "YAML" in finding.message

    @pytest.mark.parametrize("directory", ["../outside", "/etc/legesher", "a/../../b"])
    def test_a_config_path_that_leaves_the_repository(self, directory):
        data = f"metadata:\n  directory: {directory}\n".encode()
        (finding,) = self.check(".legesher/config.yml", data)
        assert "metadata.directory" in finding.message

    def test_metadata_missing_required_fields(self):
        (finding,) = self.check(".legesher/metadata/src/a.py.yml", b"file: src/a.py\n")
        assert "original_language" in finding.message

    def test_metadata_whose_file_leaves_the_repository(self):
        data = (
            b"file: ../../etc/passwd\noriginal_language: es\ncanonical_language: es\n"
            b"python_version: '3.13'\ncreated_at: x\nupdated_at: x\ntranslations: {}\n"
            b"history: []\n"
        )
        (finding,) = self.check(".legesher/metadata/src/a.py.yml", data)
        assert "`file`" in finding.message

    def test_a_valid_translation_memory(self):
        import json

        from legesher_core.translation_memory.model import TranslationMemoryDocument

        data = json.dumps(TranslationMemoryDocument().to_dict()).encode()
        assert self.check(".legesher/translation_memory.json", data) == []

    def test_a_translation_memory_of_another_kind(self):
        (finding,) = self.check(
            ".legesher/translation_memory.json",
            b'{"artifact": "other", "schema_version": "1.0.0"}',
        )
        assert finding.check == "artifact"

    def test_json_that_does_not_parse(self):
        (finding,) = self.check(".legesher/identifier_map.json", b"{not json")
        assert "JSON" in finding.message

    def test_an_identifier_map_of_the_wrong_shape(self):
        (finding,) = self.check(".legesher/identifier_map.json", b'{"identifiers": []}')
        assert finding.check == "artifact"

    def test_a_valid_identifier_map(self):
        data = b'{"version": 1, "source_lang": "en", "identifiers": {"total": {"es": "total"}}}'
        assert self.check(".legesher/identifier_map.json", data) == []

    def test_other_files_are_opaque(self):
        # Formats this toolchain does not own (the map engine's files, for
        # one) are never parsed, so nothing about them is described here.
        assert self.check(".legesher/register_map.json", b"\x00 anything") == []
        assert self.check(".legesher/whatever/x.bin", b"{not json") == []


class TestArtifactReviewRegressions:
    """From the review of CORE-1323."""

    def check(self, path, data, mode="100644"):
        from legesher_core.guard import check_artifact

        return check_artifact(path, data, mode=mode)

    def test_legesher_itself_as_a_symlink(self):
        (finding,) = self.check(".legesher", b"../outside", mode="120000")
        assert "symlink" in finding.message

    def test_a_case_variant_of_the_directory_is_checked(self):
        data = b"metadata:\n  directory: ../../outside\n"
        (finding,) = self.check(".LEGESHER/Config.yml", data)
        assert "metadata.directory" in finding.message

    @pytest.mark.parametrize(
        "directory",
        [
            "meta/sub",
            "docs/metadata",
            ".",
            ".legesher/../meta/sub",
            ".legesher/metadata/../../meta",
            ".legesher\\..\\meta",
        ],
    )
    def test_the_metadata_directory_stays_under_legesher(self, directory):
        # A directory elsewhere could reach outside through a symlink in the
        # tree; under .legesher/ every entry is itself checked.
        data = f"metadata:\n  directory: {directory}\n".encode()
        (finding,) = self.check(".legesher/config.yml", data)
        assert "metadata.directory" in finding.message

    @pytest.mark.parametrize(
        ("path", "data"),
        [
            (".legesher/identifier_map.json", b"[" * 100_000 + b"]" * 100_000),
            (".legesher/translation_memory.json", b"[" * 100_000 + b"]" * 100_000),
            (".legesher/config.yml", b"a: " + b"[" * 20_000 + b"]" * 20_000 + b"\n"),
        ],
        ids=["identifier-map", "translation-memory", "config"],
    )
    def test_deep_nesting_is_a_finding_not_a_crash(self, path, data):
        (finding,) = self.check(path, data)
        assert finding.check == "artifact"

    def test_an_oversized_artifact_is_a_finding(self):
        (finding,) = self.check(
            ".legesher/config.yml", b"a: 1\n" + b"#" * (6 * 1024 * 1024)
        )
        assert "too large" in finding.message


class TestFindingPaths:
    def test_a_path_with_a_control_character_is_quoted(self):
        finding = Finding("a\n::stop-commands::x\n.py", 1, 2, "unicode", "m")
        assert finding.format() == '"a\\n::stop-commands::x\\n.py":1:2: unicode: m'

    def test_an_ordinary_path_is_left_as_is(self):
        assert (
            Finding("src/ñ.py", 1, 2, "unicode", "m").format()
            == "src/ñ.py:1:2: unicode: m"
        )
