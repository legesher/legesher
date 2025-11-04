"""Tests for schema_validator module."""

import pytest
from pathlib import Path

from legesher_i18n.schema_validator import (
    LanguagePackSchema,
    SchemaValidator,
)
from legesher_i18n.exceptions import PackValidationError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLanguagePackSchema:
    """Test Pydantic schema validation."""

    def test_valid_pack_data(self):
        """Test validation of correct pack data."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir", "class": "clase"},
            "builtins": {"print": "imprimir"},
        }

        schema = LanguagePackSchema(**data)

        assert schema.language == "es"
        assert schema.target == "python"
        assert schema.version == "3.10"
        assert len(schema.keywords) == 2

    def test_missing_required_fields(self):
        """Test validation fails with missing required fields."""
        data = {
            "language": "es",
            # Missing target and version
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            LanguagePackSchema(**data)

    def test_invalid_version_format(self):
        """Test validation fails with invalid version format."""
        data = {
            "language": "es",
            "target": "python",
            "version": "invalid",  # Should be X.Y format
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            LanguagePackSchema(**data)

    def test_path_traversal_in_extends(self):
        """Test validation catches path traversal in extends field."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "extends": "../../etc/passwd",  # Malicious
        }

        with pytest.raises(Exception):  # Should be caught by validator
            LanguagePackSchema(**data)

    def test_language_code_normalization(self):
        """Test language code is normalized to lowercase."""
        data = {
            "language": "ES",  # Uppercase
            "target": "PYTHON",
            "version": "3.10",
        }

        schema = LanguagePackSchema(**data)

        assert schema.language == "es"  # Normalized to lowercase
        assert schema.target == "python"

    def test_metadata_optional(self):
        """Test that metadata is optional."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            # No metadata
        }

        schema = LanguagePackSchema(**data)
        assert schema.metadata is None

    def test_metadata_fields(self):
        """Test metadata validation."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "metadata": {
                "python_version_min": "3.10",
                "last_updated": "2025-10-23",
                "author": "Test Author",
                "community_reviewed": True,
            },
        }

        schema = LanguagePackSchema(**data)
        assert schema.metadata is not None
        assert schema.metadata.python_version_min == "3.10"
        assert schema.metadata.community_reviewed is True


class TestSchemaValidator:
    """Test SchemaValidator utility methods."""

    def test_validate_pack_success(self):
        """Test successful pack validation."""
        data = {
            "language": "en",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "test_def"},
        }

        pack_path = Path("/test/pack.yml")
        schema = SchemaValidator.validate_pack(data, pack_path)

        assert isinstance(schema, LanguagePackSchema)

    def test_validate_pack_failure(self):
        """Test pack validation failure."""
        data = {
            "language": "en",
            # Missing required fields
        }

        pack_path = Path("/test/pack.yml")

        with pytest.raises(PackValidationError) as exc_info:
            SchemaValidator.validate_pack(data, pack_path)

        assert "pack.yml" in str(exc_info.value)

    def test_check_required_fields(self):
        """Test checking for required fields."""
        data = {"language": "es"}  # Missing target and version

        missing = SchemaValidator.check_required_fields(data, Path("/test/pack.yml"))

        assert "target" in missing
        assert "version" in missing
        assert "language" not in missing

    def test_check_completeness_no_keywords(self):
        """Test completeness check with no keywords."""
        pack_data = {
            "language": "en",
            "target": "python",
            "version": "3.10",
        }

        schema = LanguagePackSchema(**pack_data)
        warnings = SchemaValidator.check_completeness(schema)

        assert len(warnings) > 0
        assert any("No keywords" in w for w in warnings)

    def test_check_completeness_missing_keywords(self):
        """Test completeness check with expected keywords."""
        pack_data = {
            "language": "en",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "test_def"},
        }

        schema = LanguagePackSchema(**pack_data)
        expected_keywords = {"def", "class", "if", "for"}

        warnings = SchemaValidator.check_completeness(schema, expected_keywords)

        assert len(warnings) > 0
        assert any("Missing translations" in w for w in warnings)

    def test_check_completeness_no_metadata(self):
        """Test completeness check flags missing metadata."""
        pack_data = {
            "language": "en",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "test_def"},
        }

        schema = LanguagePackSchema(**pack_data)
        warnings = SchemaValidator.check_completeness(schema)

        assert any("No metadata" in w for w in warnings)

    def test_get_validation_report(self):
        """Test generating validation report."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir", "class": "clase"},
            "builtins": {"print": "imprimir"},
            "metadata": {
                "last_updated": "2025-10-23",
                "python_version_min": "3.10",
            },
        }

        schema = LanguagePackSchema(**pack_data)
        report = SchemaValidator.get_validation_report(schema)

        assert report["valid"] is True
        assert report["language"] == "es"
        assert report["keywords_count"] == 2
        assert report["builtins_count"] == 1
        assert report["has_metadata"] is True
        assert "completeness_score" in report


class TestInheritancePathValidation:
    """Test validation of inheritance paths."""

    def test_validate_safe_parent_path(self):
        """Test validation of safe parent path."""
        # TODO: Implement path validation tests
        # This should test that relative paths like "../3.10/es.yml" are safe
        pass

    def test_validate_unsafe_parent_path(self):
        """Test rejection of unsafe parent path."""
        # Path traversal attempts should be rejected
        # Tested through PackValidationError in validate_extends_path validator
        pass


class TestMLCPExtendedFields:
    """Test MLCP v1.0 extended fields (CORE-348)."""

    def test_operators_field(self):
        """Test operators field validation."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "operators": {"and": "y", "or": "o", "not": "no"},
        }

        schema = LanguagePackSchema(**data)
        assert len(schema.operators) == 3
        assert schema.operators["and"] == "y"

    def test_standard_library_field(self):
        """Test standard_library field validation."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "standard_library": {"os": "sistema", "math": "matematicas"},
        }

        schema = LanguagePackSchema(**data)
        assert len(schema.standard_library) == 2
        assert schema.standard_library["os"] == "sistema"

    def test_cultural_notes_field(self):
        """Test cultural_notes field validation."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "cultural_notes": [
                {
                    "keyword": "range",
                    "note": "En español, 'rango' puede significar 'rank' o 'range'",
                    "language": "es",
                }
            ],
        }

        schema = LanguagePackSchema(**data)
        assert len(schema.cultural_notes) == 1
        assert schema.cultural_notes[0].keyword == "range"
        assert "rank" in schema.cultural_notes[0].note

    def test_all_mlcp_extended_fields(self):
        """Test pack with all MLCP extended fields."""
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "builtins": {"print": "imprimir"},
            "operators": {"and": "y"},
            "standard_library": {"os": "sistema"},
            "cultural_notes": [
                {"keyword": "test", "note": "Test note", "language": "es"}
            ],
        }

        schema = LanguagePackSchema(**data)
        assert schema.keywords
        assert schema.builtins
        assert schema.operators
        assert schema.standard_library
        assert schema.cultural_notes


class TestDuplicateDetection:
    """Test duplicate translation detection (CORE-348)."""

    def test_no_duplicates(self):
        """Test pack with no duplicate translations."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir", "class": "clase"},
            "builtins": {"print": "imprimir", "len": "longitud"},
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)

        assert result["passed"] is True
        assert len(result["keyword_duplicates"]) == 0
        assert len(result["builtin_duplicates"]) == 0
        assert result["total_conflicts"] == 0

    def test_keyword_duplicates(self):
        """Test detection of duplicate keyword translations."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {
                "def": "definir",
                "class": "definir",  # Duplicate!
                "if": "si",
            },
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)

        assert result["passed"] is False
        assert len(result["keyword_duplicates"]) == 1
        assert result["keyword_duplicates"][0]["translation"] == "definir"
        assert set(result["keyword_duplicates"][0]["source_terms"]) == {"class", "def"}
        assert result["total_conflicts"] == 1

    def test_builtin_duplicates(self):
        """Test detection of duplicate builtin translations."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "builtins": {
                "print": "imprimir",
                "len": "imprimir",  # Duplicate!
            },
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)

        assert result["passed"] is False
        assert len(result["builtin_duplicates"]) == 1
        assert result["builtin_duplicates"][0]["translation"] == "imprimir"

    def test_operator_duplicates(self):
        """Test detection of duplicate operator translations."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "operators": {"and": "y", "or": "y"},  # Both map to "y"
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)

        assert result["passed"] is False
        assert len(result["operator_duplicates"]) == 1

    def test_multiple_duplicates_across_types(self):
        """Test detection of duplicates in multiple sections."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "palabra", "class": "palabra"},
            "builtins": {"print": "funcion", "len": "funcion"},
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)

        assert result["passed"] is False
        assert result["total_conflicts"] == 2
        assert len(result["keyword_duplicates"]) == 1
        assert len(result["builtin_duplicates"]) == 1


class TestEnhancedCompleteness:
    """Test enhanced completeness checking (CORE-348)."""

    def test_completeness_without_version_index(self):
        """Test completeness when version index is unavailable."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir", "class": "clase"},
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_completeness_enhanced(schema)

        # Should give benefit of doubt without version index
        assert result["completeness_percentage"] == 0.75
        assert "completeness_percentage" in result
        assert "missing_keywords" in result

    def test_missing_critical_builtins(self):
        """Test detection of missing critical builtins."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            # No builtins at all
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_completeness_enhanced(schema)

        assert len(result["missing_builtins"]) > 0
        assert "print" in result["missing_builtins"]
        assert any("critical builtins" in rec for rec in result["recommendations"])

    def test_metadata_score(self):
        """Test metadata completeness scoring."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "metadata": {
                "last_updated": "2025-10-23",
                "python_version_min": "3.10",
                "author": "Test Author",
                "license": "MIT",
            },
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_completeness_enhanced(schema)

        assert result["metadata_score"] > 0.0
        assert result["metadata_score"] <= 1.0

    def test_completeness_recommendations(self):
        """Test that recommendations are generated."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            # Minimal pack
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_completeness_enhanced(schema)

        assert len(result["recommendations"]) > 0
        assert any("keywords" in rec.lower() for rec in result["recommendations"])


class TestMLCPConformance:
    """Test MLCP v1.0 conformance checking (CORE-348)."""

    def test_core_conformance(self):
        """Test pack meets MLCP core requirements."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_mlcp_conformance(schema)

        assert result["passed"] is True
        assert result["conformance_level"] == "core"
        assert result["core_conformant"] is True
        assert result["spec_version"] == "1.0"

    def test_extended_conformance(self):
        """Test pack meets MLCP extended requirements."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "metadata": {
                "last_updated": "2025-10-23",
                "author": "Test",
            },
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_mlcp_conformance(schema)

        assert result["passed"] is True
        assert result["conformance_level"] == "extended"
        assert result["core_conformant"] is True
        assert result["extended_conformant"] is True

    def test_full_conformance(self):
        """Test pack meets MLCP full requirements."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
            "operators": {"and": "y"},  # Extended field
            "metadata": {
                "last_updated": "2025-10-23",
                "author": "Test",
            },
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_mlcp_conformance(schema)

        assert result["passed"] is True
        assert result["conformance_level"] == "full"
        assert result["full_conformant"] is True

    def test_non_conformant(self):
        """Test pack that doesn't meet MLCP requirements."""
        pack_data = {
            "language": "español",  # Invalid ISO 639-1 (too long)
            "target": "python",
            "version": "3.10",
        }

        with pytest.raises(Exception):  # Should fail Pydantic validation
            LanguagePackSchema(**pack_data)

    def test_conformance_issues_reported(self):
        """Test that conformance issues are properly reported."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            # No keywords or metadata
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_mlcp_conformance(schema)

        assert len(result["issues"]) > 0
        assert any("metadata" in issue.lower() for issue in result["issues"])

    def test_iso_639_1_validation(self):
        """Test ISO 639-1 language code validation."""
        pack_data = {
            "language": "es",  # Valid 2-letter code
            "target": "python",
            "version": "3.10",
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_mlcp_conformance(schema)

        assert result["checks"]["valid_iso639_code"] is True

    def test_version_format_validation(self):
        """Test version format validation (X.Y)."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",  # Valid X.Y format
        }

        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_mlcp_conformance(schema)

        assert result["checks"]["valid_version_format"] is True
