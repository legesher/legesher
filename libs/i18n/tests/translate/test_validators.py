"""Tests for translation validators."""

import pytest
from scripts.translate.validators import TranslationValidator, ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            translation="definir",
            term="def",
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_invalid_result_with_errors(self):
        """Test creating an invalid result with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Contains space"],
            warnings=["Should be capitalized"],
            translation="valor absoluto",
            term="abs",
        )

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1

    def test_string_representation(self):
        """Test string formatting of result."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Long translation"],
            translation="definir",
            term="def",
        )

        result_str = str(result)
        assert "✓ VALID" in result_str
        assert "def" in result_str
        assert "definir" in result_str
        assert "Long translation" in result_str


class TestTranslationValidator:
    """Test TranslationValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return TranslationValidator()

    # Rule 1: No spaces in keywords/builtins
    def test_no_spaces_in_keywords(self, validator):
        """Test that spaces in keywords are flagged as errors."""
        result = validator.validate(
            term="abs",
            translation="valor absoluto",  # Has space
            language_code="es",
            term_type="keyword",
        )

        assert result.is_valid is False
        assert any("space" in err.lower() for err in result.errors)
        assert "valorabsoluto" in result.errors[0]  # Suggests concatenation

    def test_no_spaces_in_builtins(self, validator):
        """Test that spaces in builtins are flagged as errors."""
        result = validator.validate(
            term="print",
            translation="imprimir valor",
            language_code="es",
            term_type="builtin",
        )

        assert result.is_valid is False
        assert any("space" in err.lower() for err in result.errors)

    def test_spaces_allowed_in_exceptions(self, validator):
        """Test that spaces in exceptions are NOT flagged as errors."""
        result = validator.validate(
            term="ValueError",
            translation="Error De Valor",  # Spaces allowed in exceptions
            language_code="es",
            term_type="exception",
        )

        # Should not have space error (exceptions can have spaces)
        space_errors = [err for err in result.errors if "space" in err.lower()]
        assert len(space_errors) == 0

    # Rule 2: No forbidden punctuation
    def test_forbidden_punctuation_slash(self, validator):
        """Test that slashes are flagged."""
        result = validator.validate(
            term="ioerror",
            translation="error de E/S",
            language_code="es",
            term_type="exception",
        )

        assert result.is_valid is False
        assert any("/" in err for err in result.errors)
        assert any("punctuation" in err.lower() for err in result.errors)

    def test_forbidden_punctuation_dash(self, validator):
        """Test that dashes are flagged."""
        result = validator.validate(
            term="import",
            translation="im-port",
            language_code="es",
            term_type="keyword",
        )

        assert result.is_valid is False
        assert any("-" in err for err in result.errors)

    def test_forbidden_punctuation_colon(self, validator):
        """Test that colons are flagged."""
        result = validator.validate(
            term="def",
            translation="def:",
            language_code="es",
            term_type="keyword",
        )

        assert result.is_valid is False
        assert any(":" in err for err in result.errors)

    def test_forbidden_punctuation_multiple(self, validator):
        """Test multiple forbidden punctuation characters."""
        result = validator.validate(
            term="test",
            translation="test-func()",
            language_code="es",
            term_type="builtin",
        )

        assert result.is_valid is False
        # Should flag -, (, and )
        assert any("punctuation" in err.lower() for err in result.errors)

    # Rule 3: Cannot be empty
    def test_empty_translation(self, validator):
        """Test that empty translations are flagged."""
        result = validator.validate(
            term="def",
            translation="",
            language_code="es",
            term_type="keyword",
        )

        assert result.is_valid is False
        assert any("empty" in err.lower() for err in result.errors)

    def test_whitespace_only_translation(self, validator):
        """Test that whitespace-only translations are flagged."""
        result = validator.validate(
            term="def",
            translation="   ",
            language_code="es",
            term_type="keyword",
        )

        assert result.is_valid is False
        assert any("empty" in err.lower() for err in result.errors)

    # Rule 4: Cannot be same as original (for non-English)
    def test_same_as_original_non_english(self, validator):
        """Test warning when translation equals original term."""
        result = validator.validate(
            term="print",
            translation="print",  # Same as English
            language_code="es",
            term_type="builtin",
        )

        # Should be a warning, not an error
        assert any("identical" in warn.lower() for warn in result.warnings)

    def test_same_as_original_english_allowed(self, validator):
        """Test that English language can have identical translations."""
        result = validator.validate(
            term="print",
            translation="print",
            language_code="en",
            term_type="builtin",
        )

        # Should NOT have identical warning for English
        assert not any("identical" in warn.lower() for warn in result.warnings)

    # Rule 5: Check for placeholder patterns
    def test_placeholder_spanish(self, validator):
        """Test detection of Spanish placeholder."""
        result = validator.validate(
            term="globals",
            translation="el término traducido",
            language_code="es",
            term_type="builtin",
        )

        assert result.is_valid is False
        assert any("placeholder" in err.lower() for err in result.errors)

    def test_placeholder_english(self, validator):
        """Test detection of English placeholder."""
        result = validator.validate(
            term="globals",
            translation="the translated term",
            language_code="es",
            term_type="builtin",
        )

        assert result.is_valid is False
        assert any("placeholder" in err.lower() for err in result.errors)

    def test_placeholder_global_variables(self, validator):
        """Test detection of 'the global variables' placeholder."""
        result = validator.validate(
            term="globals",
            translation="the global variables",
            language_code="tr",
            term_type="builtin",
        )

        assert result.is_valid is False
        assert any("placeholder" in err.lower() for err in result.errors)

    # Rule 6: Should not contain English articles
    def test_english_articles_in_translation(self, validator):
        """Test warning for English articles in non-English translation."""
        result = validator.validate(
            term="globals",
            translation="the globals",
            language_code="es",
            term_type="keyword",
        )

        # Should have warning about English words
        assert any("english" in warn.lower() for warn in result.warnings)

    def test_english_articles_multiple(self, validator):
        """Test detection of multiple English words."""
        result = validator.validate(
            term="test",
            translation="a test of the function",
            language_code="fr",
            term_type="builtin",
        )

        assert any("english" in warn.lower() for warn in result.warnings)

    # Rule 7: Capitalization for True/False/None
    def test_true_capitalization_latin(self, validator):
        """Test that True should be capitalized in Latin scripts."""
        result = validator.validate(
            term="True",
            translation="verdadero",  # Lowercase
            language_code="es",
            term_type="builtin",
        )

        # Should have warning about capitalization
        assert any("capital" in warn.lower() for warn in result.warnings)
        assert "Verdadero" in result.warnings[0]  # Suggests capitalized version

    def test_false_capitalization_latin(self, validator):
        """Test that False should be capitalized in Latin scripts."""
        result = validator.validate(
            term="False",
            translation="falso",
            language_code="es",
            term_type="builtin",
        )

        assert any("capital" in warn.lower() for warn in result.warnings)
        assert "Falso" in result.warnings[0]

    def test_none_capitalization_latin(self, validator):
        """Test that None should be capitalized in Latin scripts."""
        result = validator.validate(
            term="None",
            translation="ninguno",
            language_code="es",
            term_type="builtin",
        )

        assert any("capital" in warn.lower() for warn in result.warnings)

    def test_capitalization_non_case_language(self, validator):
        """Test that non-case languages don't get capitalization warnings."""
        # Arabic has no case system
        result = validator.validate(
            term="True",
            translation="صحيح",
            language_code="ar",
            term_type="builtin",
        )

        # Should NOT have capitalization warning
        assert not any("capital" in warn.lower() for warn in result.warnings)

    def test_capitalization_japanese(self, validator):
        """Test Japanese (no case) doesn't get warning."""
        result = validator.validate(
            term="True",
            translation="真",
            language_code="ja",
            term_type="builtin",
        )

        assert not any("capital" in warn.lower() for warn in result.warnings)

    # Rule 8: Check length
    def test_long_translation_warning(self, validator):
        """Test warning for very long translations."""
        long_translation = "a" * 51
        result = validator.validate(
            term="test",
            translation=long_translation,
            language_code="es",
            term_type="keyword",
        )

        assert any("long" in warn.lower() for warn in result.warnings)
        assert "51 chars" in result.warnings[0]

    def test_reasonable_length_no_warning(self, validator):
        """Test that reasonable length has no warning."""
        result = validator.validate(
            term="def",
            translation="definir",
            language_code="es",
            term_type="keyword",
        )

        # Should not have length warning
        assert not any("long" in warn.lower() for warn in result.warnings)

    # Rule 9: Multiple consecutive special chars
    def test_multiple_special_chars(self, validator):
        """Test warning for multiple consecutive special characters."""
        result = validator.validate(
            term="test",
            translation="test--func",
            language_code="es",
            term_type="builtin",
        )

        # Note: This will also trigger punctuation error
        assert any("consecutive" in warn.lower() for warn in result.warnings)

    # Valid translations
    def test_valid_translation_spanish(self, validator):
        """Test a completely valid Spanish translation."""
        result = validator.validate(
            term="def",
            translation="definir",
            language_code="es",
            term_type="keyword",
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_translation_arabic(self, validator):
        """Test a valid Arabic translation."""
        result = validator.validate(
            term="print",
            translation="طباعة",
            language_code="ar",
            term_type="builtin",
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_valid_translation_chinese(self, validator):
        """Test a valid Chinese translation."""
        result = validator.validate(
            term="return",
            translation="返回",
            language_code="zh",
            term_type="keyword",
        )

        assert result.is_valid is True
        assert len(result.errors) == 0


class TestValidatePackFunction:
    """Test validate_pack function for entire language packs."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return TranslationValidator()

    def test_validate_pack_all_valid(self, validator):
        """Test validating a pack with all valid translations."""
        translations = {
            "keywords": {
                "def": "definir",
                "return": "retornar",
                "class": "clase",
            },
            "builtins": {
                "print": "imprimir",
                "len": "longitud",
            },
            "exceptions": {
                "ValueError": "ErrorDeValor",
            },
        }

        results, duplicates = validator.validate_pack("es", translations)

        # All should be valid
        assert all(r.is_valid for r in results)
        assert len(duplicates) == 0

    def test_validate_pack_with_duplicates(self, validator):
        """Test detection of duplicate translations across terms."""
        translations = {
            "keywords": {
                "if": "eğer",
                "except": "eğer",  # DUPLICATE - same translation
            },
            "builtins": {
                "chr": "karakter",
                "ord": "karakter",  # DUPLICATE - same translation
            },
            "exceptions": {},
        }

        results, duplicates = validator.validate_pack("tr", translations)

        # Should detect duplicates
        assert len(duplicates) == 2  # Two duplicate translations
        assert "eğer" in duplicates
        assert "karakter" in duplicates

        # All results should be invalid due to duplicates
        assert all(not r.is_valid for r in results)

        # Each result should have duplicate error
        for result in results:
            assert any("DUPLICATE" in err for err in result.errors)

    def test_validate_pack_mixed_errors(self, validator):
        """Test pack with mix of valid and invalid translations."""
        translations = {
            "keywords": {
                "def": "definir",  # Valid
                "abs": "valor absoluto",  # Invalid - has space
            },
            "builtins": {
                "print": "imprimir",  # Valid
                "globals": "el término traducido",  # Invalid - placeholder
            },
            "exceptions": {},
        }

        results, duplicates = validator.validate_pack("es", translations)

        # Should have both valid and invalid
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = sum(1 for r in results if not r.is_valid)

        assert valid_count == 2  # "def" and "print"
        assert invalid_count == 2  # "abs" and "globals"

    def test_validate_pack_cross_section_duplicates(self, validator):
        """Test duplicate detection across different sections."""
        translations = {
            "keywords": {
                "not": "değil",
            },
            "builtins": {
                "else": "değil",  # Same translation in different section
            },
            "exceptions": {},
        }

        results, duplicates = validator.validate_pack("tr", translations)

        # Should detect cross-section duplicate
        assert "değil" in duplicates
        assert len(duplicates["değil"]) == 2  # Two terms with same translation


class TestValidatorIntegration:
    """Integration tests for validator with real-world scenarios."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return TranslationValidator()

    def test_turkish_duplicates_real_case(self, validator):
        """Test real Turkish duplicate cases from cleanup."""
        # Real duplicates found in Turkish pack
        translations = {
            "keywords": {
                "if": "eğer",
                "except": "eğer",  # Duplicate
                "not": "değil",
                "else": "değilse",  # Contains "değil" but not exact duplicate
            },
            "builtins": {
                "chr": "karakter",
                "ord": "karakter",  # Duplicate
            },
            "exceptions": {},
        }

        results, duplicates = validator.validate_pack("tr", translations)

        # Should find exactly 2 duplicates
        assert len(duplicates) == 2
        assert "eğer" in duplicates
        assert "karakter" in duplicates

        # "değilse" should NOT be flagged as duplicate of "değil"
        assert "değilse" not in duplicates

    def test_spanish_multiword_fixes(self, validator):
        """Test Spanish translations that had multi-word issues."""
        # Real cases from Spanish cleanup
        translations = {
            "keywords": {},
            "builtins": {
                "abs": "valorabsoluto",  # Fixed (was "valor absoluto")
                "globals": "variables_globales",  # Valid with underscore
            },
            "exceptions": {
                "IOError": "ErrorDeES",  # Fixed (was "Error de E/S")
            },
        }

        results, duplicates = validator.validate_pack("es", translations)

        # All should be valid now (after fixes)
        assert all(r.is_valid for r in results)
        assert len(duplicates) == 0

    def test_capitalization_across_languages(self, validator):
        """Test capitalization rules for True/False/None across languages."""
        test_cases = [
            ("es", "Verdadero", True),  # Latin - should be capitalized (valid)
            ("es", "verdadero", False),  # Latin - lowercase (warning)
            ("ar", "صحيح", True),  # Arabic - no case (valid)
            ("ja", "真", True),  # Japanese - no case (valid)
            ("zh", "真", True),  # Chinese - no case (valid)
            ("fr", "Vrai", True),  # Latin - capitalized (valid)
            ("fr", "vrai", False),  # Latin - lowercase (warning)
        ]

        for lang, translation, should_be_valid in test_cases:
            result = validator.validate(
                term="True",
                translation=translation,
                language_code=lang,
                term_type="builtin",
            )

            if should_be_valid:
                # Should not have capitalization warning
                assert not any("capital" in w.lower() for w in result.warnings), (
                    f"{lang} - {translation} should not have capitalization warning"
                )
            else:
                # Should have capitalization warning
                assert any("capital" in w.lower() for w in result.warnings), (
                    f"{lang} - {translation} should have capitalization warning"
                )

    def test_print_summary(self, validator, capsys):
        """Test print_summary output."""
        translations = {
            "keywords": {
                "def": "definir",  # Valid
                "abs": "valor absoluto",  # Invalid
            },
            "builtins": {},
            "exceptions": {},
        }

        results, _ = validator.validate_pack("es", translations)
        validator.print_summary(results)

        captured = capsys.readouterr()
        output = captured.out

        # Should contain summary info
        assert "Validation Summary" in output
        assert "Total translations: 2" in output
        assert "✓ Valid: 1" in output
        assert "✗ Invalid: 1" in output


class TestEmbeddedCommentDetection:
    """Test detection of embedded YAML comments (CORE-529 regression prevention)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return TranslationValidator()

    def test_detects_embedded_comment(self, validator):
        """Test that embedded YAML comment syntax is flagged."""
        # This is what happens when a YAML comment is inside quotes
        result = validator.validate(
            term="abs",
            translation="абсолютноезначение  #абсолютное значение",
            language_code="ru",
            term_type="builtin",
        )

        assert result.is_valid is False
        assert any("embedded yaml comment" in err.lower() for err in result.errors)

    def test_valid_translation_no_hash(self, validator):
        """Test that translations without # are valid."""
        result = validator.validate(
            term="abs",
            translation="абсолютноезначение",
            language_code="ru",
            term_type="builtin",
        )

        # Should not have embedded comment error
        assert not any("embedded" in err.lower() for err in result.errors)

    def test_single_hash_not_flagged(self, validator):
        """Test that single # without double space is not flagged."""
        # A single # in translation is unusual but not the embedded comment bug
        result = validator.validate(
            term="test",
            translation="тест#значение",  # No double space before #
            language_code="ru",
            term_type="keyword",
        )

        # Should not be flagged as embedded comment
        assert not any("embedded yaml comment" in err.lower() for err in result.errors)


class TestApostropheDetection:
    """Test detection of apostrophes in translations (invalid Python identifiers)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return TranslationValidator()

    def test_detects_apostrophe(self, validator):
        """Test that apostrophes are flagged as errors."""
        result = validator.validate(
            term="break",
            translation="s'échapper",
            language_code="fr",
            term_type="keyword",
        )

        assert result.is_valid is False
        assert any("apostrophe" in err.lower() for err in result.errors)

    def test_suggests_removal(self, validator):
        """Test that error suggests removing apostrophe."""
        result = validator.validate(
            term="break",
            translation="s'échapper",
            language_code="fr",
            term_type="keyword",
        )

        assert any("séchapper" in err for err in result.errors)

    def test_valid_without_apostrophe(self, validator):
        """Test that translations without apostrophes pass."""
        result = validator.validate(
            term="break",
            translation="séchapper",
            language_code="fr",
            term_type="keyword",
        )

        # Should not have apostrophe error
        assert not any("apostrophe" in err.lower() for err in result.errors)
