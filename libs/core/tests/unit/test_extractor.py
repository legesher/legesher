"""Tests for TranslatableExtractor — AST element extraction for LLM translation.

Tests that the extractor correctly identifies translatable elements (identifiers,
comments, docstrings, strings) while skipping keywords, builtins, dunders,
stdlib imports, shebangs, encoding declarations, and cultural comments.
"""

import pytest

from legesher_core.token_mapper import TokenMapper
from legesher_core.tree_sitter.extractor import (
    CULTURAL_COMMENT_PATTERN,
    DUNDER_PATTERN,
    ENCODING_PATTERN,
    SHEBANG_PATTERN,
    STDLIB_MODULES,
    TranslatableExtractor,
)
from legesher_core.types import TranslatableElement

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def keyword_map():
    """Minimal keyword map for testing."""
    return {
        "def": "definir",
        "class": "clase",
        "if": "si",
        "return": "retornar",
        "import": "importar",
        "from": "desde",
        "for": "para",
        "in": "en",
        "pass": "pasar",
        "True": "Verdadero",
        "False": "Falso",
        "None": "Nada",
    }


@pytest.fixture
def builtin_map():
    """Minimal builtin map for testing."""
    return {
        "print": "imprimir",
        "len": "longitud",
        "range": "rango",
        "int": "entero",
        "str": "cadena",
        "list": "lista",
        "dict": "diccionario",
        "type": "tipo",
    }


@pytest.fixture
def mapper(keyword_map, builtin_map):
    return TokenMapper(keyword_map, builtin_map)


@pytest.fixture
def extractor(mapper):
    return TranslatableExtractor(mapper)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _texts(elements, kind=None):
    """Return list of text values, optionally filtered by kind."""
    if kind is not None:
        return [e.text for e in elements if e.kind == kind]
    return [e.text for e in elements]


def _roles(elements, kind="identifier"):
    """Return list of (text, role) tuples for identifiers."""
    return [(e.text, e.role) for e in elements if e.kind == kind]


# ===========================================================================
# Happy path: extraction of each element type
# ===========================================================================


class TestExtractIdentifiers:
    """Tests for identifier extraction."""

    def test_extracts_function_name(self, extractor):
        elements = extractor.extract("def my_function(): pass")
        ids = _texts(elements, "identifier")
        assert "my_function" in ids

    def test_extracts_class_name(self, extractor):
        elements = extractor.extract("class MyClass: pass")
        ids = _texts(elements, "identifier")
        assert "MyClass" in ids

    def test_extracts_parameter_names(self, extractor):
        elements = extractor.extract("def foo(name, count): pass")
        ids = _texts(elements, "identifier")
        assert "foo" in ids
        assert "name" in ids
        assert "count" in ids

    def test_extracts_variable_names(self, extractor):
        elements = extractor.extract("result = 42")
        ids = _texts(elements, "identifier")
        assert "result" in ids

    def test_extracts_attribute_names(self, extractor):
        elements = extractor.extract("obj.attribute")
        ids = _texts(elements, "identifier")
        assert "obj" in ids
        assert "attribute" in ids


class TestExtractComments:
    """Tests for comment extraction."""

    def test_extracts_regular_comment(self, extractor):
        elements = extractor.extract("# This is a comment")
        comments = _texts(elements, "comment")
        assert len(comments) == 1
        assert "This is a comment" in comments[0]

    def test_extracts_inline_comment(self, extractor):
        elements = extractor.extract("x = 1  # inline comment")
        comments = _texts(elements, "comment")
        assert len(comments) == 1


class TestExtractDocstrings:
    """Tests for docstring extraction."""

    def test_extracts_function_docstring(self, extractor):
        code = 'def foo():\n    """This is a docstring"""\n    pass'
        elements = extractor.extract(code)
        docstrings = [e for e in elements if e.kind == "docstring"]
        assert len(docstrings) == 1
        assert "This is a docstring" in docstrings[0].text

    def test_extracts_class_docstring(self, extractor):
        code = 'class Foo:\n    """Class docstring"""\n    pass'
        elements = extractor.extract(code)
        docstrings = [e for e in elements if e.kind == "docstring"]
        assert len(docstrings) == 1
        assert "Class docstring" in docstrings[0].text

    def test_extracts_module_docstring(self, extractor):
        code = '"""Module docstring"""\nx = 1'
        elements = extractor.extract(code)
        docstrings = [e for e in elements if e.kind == "docstring"]
        assert len(docstrings) == 1
        assert "Module docstring" in docstrings[0].text


class TestExtractStrings:
    """Tests for string literal extraction."""

    def test_extracts_string_literal(self, extractor):
        elements = extractor.extract('x = "Hello world"')
        strings = [e for e in elements if e.kind == "string"]
        assert len(strings) == 1
        assert "Hello world" in strings[0].text

    def test_extracts_single_quoted_string(self, extractor):
        elements = extractor.extract("x = 'Hello world'")
        strings = [e for e in elements if e.kind == "string"]
        assert len(strings) == 1


# ===========================================================================
# Skip rules: elements that must NOT be extracted
# ===========================================================================


class TestSkipKeywords:
    """Keywords should be handled by TreeSitterTranslator, not extracted."""

    @pytest.mark.parametrize("keyword", ["def", "class", "if", "return"])
    def test_skips_keyword(self, extractor, keyword):
        # Keywords appear as node types, not as identifiers in tree-sitter,
        # but when they do appear as identifiers the mapper filters them.
        code = f"{keyword} foo(): pass" if keyword in ("def", "class") else "x = 1"
        elements = extractor.extract(code)
        ids = _texts(elements, "identifier")
        assert keyword not in ids


class TestSkipBuiltins:
    """Builtins should be handled by TreeSitterTranslator, not extracted."""

    @pytest.mark.parametrize("builtin", ["print", "len", "range"])
    def test_skips_builtin(self, extractor, builtin):
        code = f"{builtin}(x)"
        elements = extractor.extract(code)
        ids = _texts(elements, "identifier")
        assert builtin not in ids


class TestSkipDunders:
    """Dunder/magic methods must be preserved verbatim."""

    @pytest.mark.parametrize("dunder", ["__init__", "__str__", "__repr__", "__len__"])
    def test_skips_dunder(self, extractor, dunder):
        code = f"class Foo:\n    def {dunder}(self): pass"
        elements = extractor.extract(code)
        ids = _texts(elements, "identifier")
        assert dunder not in ids


class TestSkipStdlibImports:
    """Standard library module names in import statements should be skipped."""

    def test_skips_import_os(self, extractor):
        elements = extractor.extract("import os")
        ids = _texts(elements, "identifier")
        assert "os" not in ids

    def test_skips_from_pathlib_import(self, extractor):
        elements = extractor.extract("from pathlib import Path")
        ids = _texts(elements, "identifier")
        assert "pathlib" not in ids
        # Path is also stdlib, but it's not in the stdlib_modules set
        # (it's the submodule name; pathlib is the module)

    def test_skips_import_json(self, extractor):
        elements = extractor.extract("import json")
        ids = _texts(elements, "identifier")
        assert "json" not in ids

    def test_stdlib_modules_is_frozenset(self):
        assert isinstance(STDLIB_MODULES, frozenset)
        assert "os" in STDLIB_MODULES
        assert "pathlib" in STDLIB_MODULES
        assert "json" in STDLIB_MODULES


class TestSkipSpecialComments:
    """Shebangs, encoding declarations, and cultural comments must be skipped."""

    def test_skips_shebang(self, extractor):
        code = "#!/usr/bin/env python\nx = 1"
        elements = extractor.extract(code)
        comments = _texts(elements, "comment")
        for c in comments:
            assert not c.startswith("#!")

    def test_skips_encoding_declaration(self, extractor):
        code = "# -*- coding: utf-8 -*-\nx = 1"
        elements = extractor.extract(code)
        comments = _texts(elements, "comment")
        for c in comments:
            assert "coding" not in c

    def test_skips_cultural_comment(self, extractor):
        code = "#@culture[es]: explanation text\nx = 1"
        elements = extractor.extract(code)
        comments = _texts(elements, "comment")
        for c in comments:
            assert "@culture" not in c

    def test_skips_empty_comment(self, extractor):
        code = "#\nx = 1"
        elements = extractor.extract(code)
        comments = [e for e in elements if e.kind == "comment"]
        assert len(comments) == 0


# ===========================================================================
# F-string handling
# ===========================================================================


class TestFStringHandling:
    """F-strings: extract string_content parts, skip interpolation expressions."""

    def test_extracts_fstring_text_parts(self, extractor):
        code = 'x = f"Hello {name}, welcome!"'
        elements = extractor.extract(code)
        strings = [e for e in elements if e.kind == "string"]
        texts = [e.text for e in strings]
        # Should have the text parts, not the {name} expression
        assert any("Hello" in t or "welcome" in t for t in texts)

    def test_does_not_extract_fstring_expression_as_string(self, extractor):
        code = 'x = f"Result: {value + 1}"'
        elements = extractor.extract(code)
        strings = [e for e in elements if e.kind == "string"]
        # The expression "value + 1" should not appear as a string
        for s in strings:
            assert "value + 1" not in s.text


# ===========================================================================
# Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge cases and robustness tests."""

    def test_empty_file(self, extractor):
        elements = extractor.extract("")
        assert elements == []

    def test_whitespace_only(self, extractor):
        elements = extractor.extract("   \n\n   ")
        assert elements == []

    def test_syntax_error_handled_gracefully(self, extractor):
        # tree-sitter is error-tolerant, so this should not raise
        code = "def foo(:\n    pass"
        elements = extractor.extract(code)
        # Should return some elements without raising
        assert isinstance(elements, list)

    def test_elements_sorted_by_start_byte(self, extractor):
        code = "x = 1\n# comment\ny = 2"
        elements = extractor.extract(code)
        for i in range(len(elements) - 1):
            assert elements[i].start_byte <= elements[i + 1].start_byte


# ===========================================================================
# Role classification
# ===========================================================================


class TestRoleClassification:
    """Test that identifiers are classified with the correct role."""

    def test_function_name_role(self, extractor):
        elements = extractor.extract("def my_func(): pass")
        roles = _roles(elements)
        assert ("my_func", "function_name") in roles

    def test_class_name_role(self, extractor):
        elements = extractor.extract("class MyClass: pass")
        roles = _roles(elements)
        assert ("MyClass", "class_name") in roles

    def test_parameter_role(self, extractor):
        elements = extractor.extract("def foo(param): pass")
        roles = _roles(elements)
        assert ("param", "parameter") in roles

    def test_variable_role(self, extractor):
        elements = extractor.extract("result = 42")
        roles = _roles(elements)
        assert ("result", "variable") in roles

    def test_attribute_role(self, extractor):
        elements = extractor.extract("obj.my_attr")
        roles = _roles(elements)
        assert ("my_attr", "attribute") in roles


# ===========================================================================
# Context and naming convention
# ===========================================================================


class TestContextExtraction:
    """Test that elements carry surrounding code context."""

    def test_identifier_has_surrounding_code(self, extractor):
        code = "x = 1\ndef calculate_total(items):\n    return sum(items)\ny = 2"
        elements = extractor.extract(code)
        func_elem = next((e for e in elements if e.text == "calculate_total"), None)
        assert func_elem is not None
        assert "surrounding_code" in func_elem.context
        assert func_elem.context["surrounding_code"]  # non-empty

    def test_identifier_has_line_number(self, extractor):
        code = "x = 1\ny = 2"
        elements = extractor.extract(code)
        y_elem = next((e for e in elements if e.text == "y"), None)
        assert y_elem is not None
        assert "line" in y_elem.context
        assert y_elem.context["line"] == 1  # 0-indexed line


class TestNamingConventionDetection:
    """Test naming convention detection in identifier context."""

    @pytest.mark.parametrize(
        "name,expected_convention",
        [
            ("my_function", "snake_case"),
            ("MyClass", "PascalCase"),
            ("myVariable", "camelCase"),
            ("MAX_RETRIES", "SCREAMING_SNAKE_CASE"),
            ("simple", "lowercase"),
        ],
    )
    def test_naming_convention(self, extractor, name, expected_convention):
        code = f"{name} = 42"
        elements = extractor.extract(code)
        elem = next((e for e in elements if e.text == name), None)
        assert elem is not None
        assert elem.context.get("naming_convention") == expected_convention


# ===========================================================================
# Regex patterns (unit tests for the constants)
# ===========================================================================


class TestRegexPatterns:
    """Test the regex patterns used for filtering."""

    @pytest.mark.parametrize(
        "text",
        ["__init__", "__str__", "__repr__", "__len__", "__eq__", "__hash__"],
    )
    def test_dunder_pattern_matches(self, text):
        assert DUNDER_PATTERN.match(text) is not None

    @pytest.mark.parametrize(
        "text",
        ["_private", "normal", "__leading", "trailing__", "no_dunder"],
    )
    def test_dunder_pattern_does_not_match(self, text):
        assert DUNDER_PATTERN.match(text) is None

    def test_shebang_pattern(self):
        assert SHEBANG_PATTERN.match("#!/usr/bin/env python") is not None
        assert SHEBANG_PATTERN.match("# regular comment") is None

    def test_encoding_pattern(self):
        assert ENCODING_PATTERN.match("# -*- coding: utf-8 -*-") is not None
        assert ENCODING_PATTERN.match("# coding=utf-8") is not None
        assert ENCODING_PATTERN.match("# regular comment") is None

    def test_cultural_comment_pattern(self):
        assert CULTURAL_COMMENT_PATTERN.match("#@culture[es]: text") is not None
        assert CULTURAL_COMMENT_PATTERN.match("# @culture[ar]: text") is not None
        assert CULTURAL_COMMENT_PATTERN.match("# normal comment") is None


# ===========================================================================
# TranslatableElement dataclass
# ===========================================================================


class TestTranslatableElement:
    """Tests for the TranslatableElement dataclass properties."""

    def test_element_is_frozen(self):
        elem = TranslatableElement(
            kind="identifier",
            text="foo",
            start_byte=0,
            end_byte=3,
            role="variable",
            context={},
        )
        with pytest.raises(AttributeError):
            elem.text = "bar"

    def test_element_optional_fields(self):
        elem = TranslatableElement(
            kind="string",
            text="hello",
            start_byte=0,
            end_byte=7,
            role="other",
            context={},
            quote_style='"',
            prefix="f",
        )
        assert elem.quote_style == '"'
        assert elem.prefix == "f"

    def test_element_defaults(self):
        elem = TranslatableElement(
            kind="identifier",
            text="x",
            start_byte=0,
            end_byte=1,
            role="variable",
            context={},
        )
        assert elem.quote_style is None
        assert elem.prefix is None


class TestExtractorSkipsReservedWords:
    """Test that the extractor skips self/cls so they don't reach the LLM (CORE-710)."""

    def _build_extractor(self) -> TranslatableExtractor:
        from legesher_core.token_mapper import TokenMapper

        # Minimal mapper — enough for the extractor to differentiate
        # keywords/builtins from user identifiers.
        mapper = TokenMapper(
            keyword_map={"def": "definir", "class": "clase", "return": "retornar"},
            builtin_map={"print": "imprimir"},
        )
        return TranslatableExtractor(mapper)

    def test_implicit_params_constant_contains_self_and_cls(self):
        """The module-level constant lists exactly the conventions we skip."""
        from legesher_core.tree_sitter.extractor import IMPLICIT_PARAMS

        assert IMPLICIT_PARAMS == frozenset({"self", "cls"})

    def test_self_in_method_signature_is_skipped(self):
        """def __init__(self, x): self.x = x — self should never reach LLM."""
        extractor = self._build_extractor()
        code = "class Foo:\n    def __init__(self, x):\n        self.x = x\n"
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        assert "self" not in identifier_texts, (
            f"Expected 'self' to be skipped; got identifiers: {identifier_texts}"
        )

    def test_cls_in_classmethod_is_skipped(self):
        """@classmethod def make(cls): return cls() — cls should never reach LLM."""
        extractor = self._build_extractor()
        code = (
            "class Foo:\n    @classmethod\n    def make(cls):\n        return cls()\n"
        )
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        assert "cls" not in identifier_texts, (
            f"Expected 'cls' to be skipped; got identifiers: {identifier_texts}"
        )

    def test_self_in_attribute_access_is_skipped(self):
        """self.x references in method body should also be skipped (saves LLM tokens).

        The translator's dispatch order (implicit_param_map before IdentifierMap)
        ensures the substitution happens correctly at output time without
        the LLM needing to see self at all.
        """
        extractor = self._build_extractor()
        code = (
            "class Foo:\n"
            "    def increment(self):\n"
            "        self.count = self.count + 1\n"
        )
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        # self appears 3x in the source but should be 0x in extracted identifiers
        assert identifier_texts.count("self") == 0
        # but `count` (a real user identifier) should still be extracted
        assert "count" in identifier_texts

    def test_user_identifiers_still_surface_to_llm(self):
        """Non-reserved identifiers (class/function/var names) still reach LLM."""
        extractor = self._build_extractor()
        code = "class Widget:\n    def render(self, height):\n        self.h = height\n"
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        assert "Widget" in identifier_texts
        assert "render" in identifier_texts
        assert "height" in identifier_texts
        assert "h" in identifier_texts

    def test_skip_applies_at_module_level_too(self):
        """def foo(self): outside a class body — non-conventional but still skipped.

        Pragmatic choice documented in the plan: we don't inspect decorators
        or require a class ancestor. Treating self/cls consistently in all
        positions matches the staticmethod edge case decision.
        """
        extractor = self._build_extractor()
        code = "def helper(self):\n    return self\n"
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        assert "self" not in identifier_texts
        # `helper` is still a real identifier
        assert "helper" in identifier_texts

    def test_keywords_still_take_precedence_over_implicit_param_skip(self):
        """A literal Python keyword wins over reserved-word skip.

        Defensive: if `def` were ever added to IMPLICIT_PARAMS by mistake,
        the keyword check (which runs first) would still prevent the
        keyword from being extracted as a user identifier.
        """
        extractor = self._build_extractor()
        code = "def foo():\n    pass\n"
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        # `def` is a keyword, not extracted; `foo` is a function name, extracted
        assert "def" not in identifier_texts
        assert "foo" in identifier_texts

    def test_self_in_nested_class_body_is_skipped(self):
        """Nested classes — `class A: class B: def foo(self):` — also skipped."""
        extractor = self._build_extractor()
        code = (
            "class Outer:\n"
            "    class Inner:\n"
            "        def method(self):\n"
            "            return self.value\n"
        )
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        assert "self" not in identifier_texts
        # Nested class names still extracted
        assert "Outer" in identifier_texts
        assert "Inner" in identifier_texts

    def test_self_in_lambda_is_skipped(self):
        """Lambda using self — `lambda self: self.x` — also skipped.

        Edge case: lambdas inside classes (sometimes used for property
        definitions) might bind self. Our skip-everywhere policy handles
        this without special-casing.
        """
        extractor = self._build_extractor()
        code = "f = lambda self: self.x\n"
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        assert "self" not in identifier_texts
        # `f` and `x` (attribute) still extracted
        assert "f" in identifier_texts

    def test_skip_does_not_affect_non_reserved_short_identifiers(self):
        """Single-letter identifiers like `e` (loop var) are NOT skipped.

        The skip is ONLY for self/cls — short names like `e`, `x`, `i`
        still go through identifier translation since they don't match
        the reserved-word set.
        """
        extractor = self._build_extractor()
        code = (
            "def foo():\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError as e:\n"
            "        x = e.args\n"
        )
        elements = extractor.extract(code)
        identifier_texts = [e.text for e in elements if e.kind == "identifier"]
        # `e` and `x` are user identifiers; should still surface to LLM
        assert "e" in identifier_texts
        assert "x" in identifier_texts
