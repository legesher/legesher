"""Tests for BOM stripping + PEP 263 coding-declaration enforcement."""

from legesher_core.utils import check_coding_declaration, strip_bom


class TestStripBom:
    def test_strips_leading_bom(self):
        assert strip_bom("﻿def foo(): pass") == "def foo(): pass"

    def test_noop_without_bom(self):
        assert strip_bom("def foo(): pass") == "def foo(): pass"


class TestCodingDeclaration:
    def test_latin1_declaration_detected(self):
        code = "# -*- coding: latin-1 -*-\nx = 1\n"
        assert check_coding_declaration(code) == "latin-1"

    def test_utf8_declaration_ok(self):
        code = "# -*- coding: utf-8 -*-\nx = 1\n"
        assert check_coding_declaration(code) is None

    def test_utf8_underscore_alias_ok(self):
        code = "# coding: utf_8\nx = 1\n"
        assert check_coding_declaration(code) is None

    def test_no_declaration_returns_none(self):
        assert check_coding_declaration("x = 1\n") is None

    def test_declaration_only_honored_on_first_two_lines(self):
        code = "x = 1\ny = 2\n# coding: latin-1\n"
        assert check_coding_declaration(code) is None


class TestTranslatorIntegration:
    def test_translate_strips_bom_before_processing(
        self, spanish_keywords, spanish_builtins
    ):
        from legesher_core.tree_sitter import TreeSitterTranslator

        t = TreeSitterTranslator(
            keyword_map={v: k for k, v in spanish_keywords.items()},
            builtin_map={v: k for k, v in spanish_builtins.items()},
        )
        code = "﻿def foo():\n    pass\n"
        result = t.translate_code(code, "en", "es")
        assert not result.startswith("﻿")
