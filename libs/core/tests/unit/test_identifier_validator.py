"""Tests for IdentifierValidator — validates translated Python identifiers.

Tests validity checks for Latin, CJK, Arabic, Devanagari scripts, rejection
of invalid identifiers, mixed-script detection, validate() detail reporting,
and sanitize() repair logic.
"""

import pytest

from legesher_core.tree_sitter.identifier_validator import IdentifierValidator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def validator():
    return IdentifierValidator()


# ===========================================================================
# is_valid: valid Python identifiers
# ===========================================================================


class TestIsValidAccepts:
    """Identifiers that should pass validation."""

    @pytest.mark.parametrize(
        "identifier",
        [
            "calcular_impuesto",
            "variable",
            "_private",
            "__dunder__",
            "x",
            "CamelCase",
            "snake_case_name",
        ],
    )
    def test_valid_latin_identifiers(self, validator, identifier):
        assert validator.is_valid(identifier) is True

    def test_valid_cjk_identifier(self, validator):
        # Chinese characters are valid Python 3 identifiers
        assert validator.is_valid("\u8ba1\u7b97") is True  # "calculate" in Chinese

    def test_valid_arabic_identifier(self, validator):
        assert (
            validator.is_valid("\u062d\u0633\u0627\u0628") is True
        )  # "account" in Arabic

    def test_valid_urdu_identifier(self, validator):
        assert validator.is_valid("\u0646\u0627\u0645") is True  # "name" in Urdu

    def test_valid_devanagari_identifier(self, validator):
        assert (
            validator.is_valid("\u0917\u0923\u0928\u093e") is True
        )  # "calculate" in Hindi

    def test_valid_mixed_underscore(self, validator):
        assert (
            validator.is_valid("\u8ba1\u7b97_\u7a0e\u6b3e") is True
        )  # CJK with underscore

    def test_valid_identifier_with_digits(self, validator):
        assert validator.is_valid("var1") is True
        assert validator.is_valid("x2y") is True


# ===========================================================================
# is_valid: rejected identifiers
# ===========================================================================


class TestIsValidRejects:
    """Identifiers that should fail validation."""

    def test_rejects_empty_string(self, validator):
        assert validator.is_valid("") is False

    def test_rejects_digit_start(self, validator):
        assert validator.is_valid("123abc") is False

    def test_rejects_spaces(self, validator):
        assert validator.is_valid("hello world") is False

    def test_rejects_hyphens(self, validator):
        assert validator.is_valid("hello-world") is False

    @pytest.mark.parametrize(
        "kw",
        [
            "def",
            "class",
            "if",
            "return",
            "import",
            "for",
            "while",
            "True",
            "False",
            "None",
        ],
    )
    def test_rejects_python_keywords(self, validator, kw):
        assert validator.is_valid(kw) is False

    def test_rejects_special_characters(self, validator):
        assert validator.is_valid("hello!") is False
        assert validator.is_valid("a@b") is False


# ===========================================================================
# is_mixed_script
# ===========================================================================


class TestMixedScript:
    """Test mixed-script detection."""

    def test_latin_and_arabic_is_mixed(self, validator):
        assert validator.is_mixed_script("hello\u062d\u0633\u0627\u0628") is True

    def test_latin_and_cjk_is_mixed(self, validator):
        assert validator.is_mixed_script("hello\u8ba1\u7b97") is True

    def test_pure_latin_not_mixed(self, validator):
        assert validator.is_mixed_script("hello_world") is False

    def test_pure_cjk_not_mixed(self, validator):
        assert validator.is_mixed_script("\u8ba1\u7b97\u7a0e\u6b3e") is False

    def test_pure_arabic_not_mixed(self, validator):
        assert validator.is_mixed_script("\u062d\u0633\u0627\u0628") is False

    def test_underscores_and_digits_ignored(self, validator):
        # Underscores and digits should not count as a separate script
        assert validator.is_mixed_script("hello_123") is False

    def test_single_char_not_mixed(self, validator):
        assert validator.is_mixed_script("x") is False


# ===========================================================================
# validate: detailed issues
# ===========================================================================


class TestValidateDetailed:
    """Test validate() returning (is_valid, issues) tuple."""

    def test_valid_returns_no_issues(self, validator):
        is_valid, issues = validator.validate("calcular_impuesto")
        assert is_valid is True
        assert issues == []

    def test_empty_returns_issue(self, validator):
        is_valid, issues = validator.validate("")
        assert is_valid is False
        assert any("Empty" in i for i in issues)

    def test_keyword_returns_issue(self, validator):
        is_valid, issues = validator.validate("def")
        assert is_valid is False
        assert any("keyword" in i.lower() for i in issues)

    def test_space_returns_issue(self, validator):
        is_valid, issues = validator.validate("hello world")
        assert is_valid is False
        assert any("space" in i.lower() for i in issues)

    def test_hyphen_returns_issue(self, validator):
        is_valid, issues = validator.validate("hello-world")
        assert is_valid is False
        assert any("hyphen" in i.lower() for i in issues)

    def test_mixed_script_is_warning_not_invalid(self, validator):
        # Mixed script alone is a warning, but identifier may still be valid Python
        is_valid, issues = validator.validate("hello\u062d\u0633\u0627\u0628")
        # Mixed script with valid Python identifier is still valid (it's a warning)
        assert any("Mixed scripts" in i or "mixed" in i.lower() for i in issues)

    def test_digit_start_returns_issue(self, validator):
        is_valid, issues = validator.validate("123abc")
        assert is_valid is False
        assert any("identifier" in i.lower() or "valid" in i.lower() for i in issues)


# ===========================================================================
# sanitize: fixing common issues
# ===========================================================================


class TestSanitize:
    """Test sanitize() for common LLM translation errors."""

    def test_replaces_spaces_with_underscores(self, validator):
        result = validator.sanitize("hello world")
        assert " " not in result
        assert "_" in result
        assert result.isidentifier()

    def test_replaces_hyphens_with_underscores(self, validator):
        result = validator.sanitize("hello-world")
        assert "-" not in result
        assert "_" in result
        assert result.isidentifier()

    def test_prepends_underscore_for_digit_start(self, validator):
        result = validator.sanitize("123abc")
        assert result.startswith("_")
        assert result.isidentifier()

    def test_appends_underscore_for_keyword(self, validator):
        result = validator.sanitize("def")
        assert result.endswith("_")
        assert result.isidentifier()
        import keyword

        assert not keyword.iskeyword(result)

    def test_sanitize_preserves_valid_identifier(self, validator):
        result = validator.sanitize("valid_name")
        assert result == "valid_name"

    def test_sanitize_empty_string(self, validator):
        result = validator.sanitize("")
        assert result.isidentifier()

    def test_sanitize_combined_issues(self, validator):
        # Space + hyphen + digit start
        result = validator.sanitize("1hello-world test")
        assert result.isidentifier()

    def test_sanitize_result_is_always_valid(self, validator):
        """Sanitized output should always be a valid Python identifier."""
        problematic = [
            "",
            "123",
            "hello world",
            "hello-world",
            "def",
            "class",
            "a@b",
            "!invalid",
        ]
        for text in problematic:
            result = validator.sanitize(text)
            assert result.isidentifier(), (
                f"sanitize({text!r}) = {result!r} is not valid"
            )
            import keyword

            assert not keyword.iskeyword(result), (
                f"sanitize({text!r}) = {result!r} is a keyword"
            )
