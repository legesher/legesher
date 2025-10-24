"""Tests for schema_validator module."""

import pytest
from pathlib import Path

from legesher_i18n.schema_validator import (
    LanguagePackSchema,
    SchemaValidator,
    LanguagePackMetadata,
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
            "language": "test",
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
            "language": "test",
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
            "language": "test",
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
            "language": "test",
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
            "language": "test",
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
        current_path = Path("/project/languages/python/3.11/es.yml")
        extends = "../3.10/es.yml"

        # This should be allowed (one level up for version inheritance)
        # SchemaValidator.validate_inheritance_path would check this
        # Implementation depends on actual directory structure

    def test_validate_unsafe_parent_path(self):
        """Test rejection of unsafe parent path."""
        # Path traversal attempts should be rejected
        # Tested through PackValidationError in validate_extends_path validator
        pass
