"""Tests for term classifier (CORE-460).

Tests TERM_TYPE_YAML_SECTIONS mapping and helper functions.
"""

from scripts.translate.term_classifier import (
    TERM_TYPE_YAML_SECTIONS,
    classify_term,
    get_yaml_section_for_term_type,
    is_valid_term_type,
    is_python_term,
    KEYWORDS_BASE,
    BUILTIN_FUNCTIONS,
    BUILTIN_TYPES,
    EXCEPTIONS,
    SPECIAL_CONSTANTS,
    HELPER_TERMS,
)


class TestTermTypeYamlSectionsMapping:
    """Test TERM_TYPE_YAML_SECTIONS mapping."""

    def test_keyword_maps_to_keywords(self):
        assert TERM_TYPE_YAML_SECTIONS["keyword"] == "keywords"

    def test_builtin_func_maps_to_builtins(self):
        assert TERM_TYPE_YAML_SECTIONS["builtin_func"] == "builtins"

    def test_builtin_type_maps_to_builtins(self):
        assert TERM_TYPE_YAML_SECTIONS["builtin_type"] == "builtins"

    def test_exception_maps_to_exceptions(self):
        assert TERM_TYPE_YAML_SECTIONS["exception"] == "exceptions"

    def test_special_constant_maps_to_builtins(self):
        assert TERM_TYPE_YAML_SECTIONS["special_constant"] == "builtins"

    def test_helper_maps_to_none(self):
        assert TERM_TYPE_YAML_SECTIONS["helper"] is None

    def test_unknown_maps_to_none(self):
        assert TERM_TYPE_YAML_SECTIONS["unknown"] is None


class TestGetYamlSectionForTermType:
    """Test get_yaml_section_for_term_type() function."""

    def test_returns_keywords_for_keyword(self):
        assert get_yaml_section_for_term_type("keyword") == "keywords"

    def test_returns_builtins_for_builtin_func(self):
        assert get_yaml_section_for_term_type("builtin_func") == "builtins"

    def test_returns_exceptions_for_exception(self):
        assert get_yaml_section_for_term_type("exception") == "exceptions"

    def test_returns_none_for_helper(self):
        assert get_yaml_section_for_term_type("helper") is None

    def test_returns_none_for_unknown(self):
        assert get_yaml_section_for_term_type("unknown") is None

    def test_returns_none_for_invalid_type(self):
        assert get_yaml_section_for_term_type("invalid") is None


class TestIsValidTermType:
    """Test is_valid_term_type() function."""

    def test_valid_types(self):
        assert is_valid_term_type("keyword")
        assert is_valid_term_type("builtin_func")
        assert is_valid_term_type("builtin_type")
        assert is_valid_term_type("exception")
        assert is_valid_term_type("special_constant")
        assert is_valid_term_type("helper")
        assert is_valid_term_type("unknown")

    def test_invalid_types(self):
        assert not is_valid_term_type("invalid")
        assert not is_valid_term_type("")
        assert not is_valid_term_type("KEYWORD")


class TestClassifyTerm:
    """Test classify_term() returns correct categories."""

    def test_keywords(self):
        assert classify_term("def") == "keyword"
        assert classify_term("return") == "keyword"
        assert classify_term("class") == "keyword"

    def test_builtin_functions(self):
        assert classify_term("print") == "builtin_func"
        assert classify_term("len") == "builtin_func"

    def test_builtin_types(self):
        assert classify_term("str") == "builtin_type"
        assert classify_term("int") == "builtin_type"

    def test_exceptions(self):
        assert classify_term("ValueError") == "exception"
        assert classify_term("TypeError") == "exception"

    def test_special_constants(self):
        assert classify_term("ellipsis") == "special_constant"

    def test_helper_terms(self):
        assert classify_term("README") == "helper"

    def test_unknown_terms(self):
        assert classify_term("xyz123") == "unknown"


class TestIsPythonTerm:
    """Test is_python_term() function."""

    def test_python_terms_return_true(self):
        assert is_python_term("def")
        assert is_python_term("print")
        assert is_python_term("ValueError")

    def test_non_python_terms_return_false(self):
        assert not is_python_term("README")
        assert not is_python_term("xyz123")


class TestTermListConsistency:
    """Test term lists classify correctly."""

    def test_keywords_classify_as_keyword(self):
        for term in KEYWORDS_BASE:
            assert classify_term(term) == "keyword"

    def test_builtin_functions_classify_as_builtin_func(self):
        for term in BUILTIN_FUNCTIONS:
            assert classify_term(term) == "builtin_func"

    def test_builtin_types_classify_as_builtin_type(self):
        for term in BUILTIN_TYPES:
            assert classify_term(term) == "builtin_type"

    def test_exceptions_classify_as_exception(self):
        for term in EXCEPTIONS:
            assert classify_term(term) == "exception"

    def test_special_constants_classify_as_special_constant(self):
        for term in SPECIAL_CONSTANTS:
            assert classify_term(term) == "special_constant"

    def test_helper_terms_classify_as_helper(self):
        for term in HELPER_TERMS:
            assert classify_term(term) == "helper"
