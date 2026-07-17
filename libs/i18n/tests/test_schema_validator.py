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
                "license": "Apache-2.0",
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


class TestCheckIdentifierValidity:
    """CORE-1112: coverage for ``SchemaValidator.check_identifier_validity``.

    The method validates that every translation in a pack (keywords,
    builtins, exceptions) is a syntactically valid Python identifier —
    required because the TokenTranslator feeds translations through
    Python's ``tokenize`` module, which rejects whitespace-laden or
    otherwise-malformed names.

    In normal usage this check is redundant with Pydantic's field
    validators (which reject invalid translations at schema construction
    time). The method exists as defense-in-depth for callers that build
    schemas via ``model_construct`` or otherwise bypass validation, so
    these tests do the same to exercise every rejection branch.
    """

    def _make_schema(self, validate: bool = True, **overrides) -> LanguagePackSchema:
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {},
            "builtins": {},
            "exceptions": {},
        }
        data.update(overrides)
        if validate:
            return LanguagePackSchema(**data)
        # Bypass field validators to reach the check_identifier_validity
        # defense-in-depth branches
        return LanguagePackSchema.model_construct(**data)

    def test_all_valid_translations_pass(self):
        schema = self._make_schema(
            keywords={"def": "definir", "class": "clase"},
            builtins={"print": "imprimir", "len": "longitud"},
            exceptions={"ValueError": "ErrorDeValor"},
        )
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is True
        assert result["total_issues"] == 0
        assert result["invalid_keywords"] == []
        assert result["invalid_builtins"] == []
        assert result["invalid_exceptions"] == []
        assert result["issues"] == []

    def test_leading_trailing_whitespace_rejected(self):
        schema = self._make_schema(
            validate=False,
            keywords={"def": " definir"},
            builtins={"print": "imprimir "},
            exceptions={"ValueError": "\tErrorDeValor"},
        )
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is False
        assert result["total_issues"] == 3
        for entry in (
            result["invalid_keywords"]
            + result["invalid_builtins"]
            + result["invalid_exceptions"]
        ):
            assert entry["reason"] == "has leading/trailing whitespace"
        # Issues list carries a human-readable entry per category
        assert any("whitespace" in issue for issue in result["issues"])

    def test_embedded_spaces_rejected(self):
        schema = self._make_schema(
            validate=False,
            keywords={"def": "definir funcion"},
        )
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is False
        assert result["total_issues"] == 1
        assert result["invalid_keywords"][0]["reason"] == "contains spaces"
        assert any("contains spaces" in issue for issue in result["issues"])

    def test_invalid_identifier_characters_rejected(self):
        schema = self._make_schema(
            validate=False,
            keywords={"def": "123start"},  # can't start with digit
            builtins={"print": "has-dash"},  # hyphens not allowed
        )
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is False
        assert result["total_issues"] == 2
        assert (
            result["invalid_keywords"][0]["reason"] == "not a valid Python identifier"
        )
        assert (
            result["invalid_builtins"][0]["reason"] == "not a valid Python identifier"
        )

    def test_mixed_problems_are_all_reported(self):
        schema = self._make_schema(
            validate=False,
            keywords={
                "def": "definir",  # valid
                "class": " clase",  # whitespace
                "if": "if with space",  # space
                "for": "123bad",  # invalid identifier
            },
        )
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is False
        assert result["total_issues"] == 3
        # Each category in the issues list carries the offending key
        assert any("'class'" in issue for issue in result["issues"])
        assert any("'if'" in issue for issue in result["issues"])
        assert any("'for'" in issue for issue in result["issues"])

    def test_soft_keyword_except_star_accepted(self):
        """`except*` is a Python 3.11+ soft keyword and must be treated as
        valid even though ``*`` isn't a regular identifier character.
        Verifies the ``source_key=`` plumbing into ``_is_valid_identifier``.
        """
        schema = self._make_schema(keywords={"except*": "excepto*"})
        result = SchemaValidator.check_identifier_validity(schema)
        assert result["passed"] is True
        assert result["total_issues"] == 0


class TestCheckCompletenessEnhanced:
    """CORE-1112: coverage for ``SchemaValidator.check_completeness_enhanced``.

    Exercises the version-index load path (lines 409-416), the
    missing-keyword computation when a version index is available
    (lines 420-423), and each branch of the metadata completeness score.
    """

    def _schema(self, **overrides) -> LanguagePackSchema:
        data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir", "class": "clase"},
            "builtins": {"print": "imprimir"},
            "exceptions": {},
        }
        data.update(overrides)
        return LanguagePackSchema(**data)

    def test_no_version_index_path_falls_back_to_heuristic(self):
        """Without a version_index_path, completeness defaults to 0.75 when
        the pack has keywords (the benefit-of-the-doubt branch)."""
        schema = self._schema()
        result = SchemaValidator.check_completeness_enhanced(schema, None)
        assert result["completeness_percentage"] == 0.75
        assert result["missing_keywords"] == []

    def test_version_index_path_does_not_exist_falls_back(self):
        """A version_index_path that doesn't exist should skip the load
        entirely and use the heuristic."""
        schema = self._schema()
        result = SchemaValidator.check_completeness_enhanced(
            schema, Path("/nonexistent/version-index.yml")
        )
        assert result["completeness_percentage"] == 0.75

    def test_version_index_load_populates_missing_keywords(self, tmp_path):
        """A valid version-index.yml is loaded and used to compute missing
        keywords and actual completeness percentage."""
        # Minimal real-schema version-index: 3.10 has "match" and "case"
        # as its added_keywords. The test schema defines neither, so both
        # should be flagged as missing.
        index_path = tmp_path / "version-index.yml"
        index_path.write_text(
            "python_versions:\n"
            "  '3.10':\n"
            "    added_keywords:\n"
            "      - match\n"
            "      - case\n"
            "    added_builtins: []\n"
            "    removed_keywords: []\n"
            "    removed_builtins: []\n"
            "    base:\n",
            encoding="utf-8",
        )
        # VersionIndex.get_all_keywords returns the full standard set for
        # the version (not just added_keywords), so a minimally-populated
        # pack will show many missing keywords and a low completeness.
        schema = self._schema()  # has only "def" and "class"
        result = SchemaValidator.check_completeness_enhanced(schema, index_path)
        missing = set(result["missing_keywords"])
        assert "match" in missing  # declared in this version-index
        assert "case" in missing
        assert "def" not in missing  # defined in the schema
        assert "class" not in missing
        # Low but non-zero completeness
        assert 0.0 < result["completeness_percentage"] < 0.2

    def test_version_index_load_error_falls_back_silently(self, tmp_path):
        """Broken version-index.yml should be caught by the except branch
        and the method should degrade to the heuristic."""
        index_path = tmp_path / "bad-index.yml"
        index_path.write_text(":\n:invalid-yaml:\n", encoding="utf-8")
        schema = self._schema()
        result = SchemaValidator.check_completeness_enhanced(schema, index_path)
        # Falls back to heuristic when load fails
        assert result["completeness_percentage"] == 0.75

    def test_missing_critical_builtins_recommendation(self):
        """When critical builtins (print/len/range/...) are missing,
        the method surfaces a recommendation."""
        schema = self._schema(builtins={})
        result = SchemaValidator.check_completeness_enhanced(schema, None)
        assert any("critical builtins" in rec for rec in result["recommendations"])

    def test_metadata_score_accumulates_all_fields(self):
        """Fully populated metadata should max out the score (~1.0),
        hitting every branch in the per-field scoring ladder."""
        schema = self._schema(
            metadata={
                "last_updated": "2026-01-01",
                "python_version_min": "3.10",
                "python_version_max": "3.13",
                "compatibility_tested": ["3.10", "3.11"],
                "author": "test",
                "license": "Apache-2.0",
                "community_reviewed": True,
            },
        )
        result = SchemaValidator.check_completeness_enhanced(schema, None)
        # 7 fields × 0.14 each, capped at 1.0
        assert result["metadata_score"] == pytest.approx(0.98, abs=0.01)

    def test_no_keywords_no_metadata_surfaces_recommendations(self):
        """Empty keywords/metadata should surface targeted recommendations."""
        schema = self._schema(keywords={}, metadata=None)
        result = SchemaValidator.check_completeness_enhanced(schema, None)
        assert result["completeness_percentage"] == 0.0
        assert any("No keywords" in rec for rec in result["recommendations"])


class TestReservedWordsField:
    """Test reserved_words schema field (CORE-710)."""

    def test_reserved_words_optional_for_backward_compat(self):
        """A pack without reserved_words: section validates and defaults to empty."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
        }
        schema = LanguagePackSchema(**pack_data)
        assert schema.reserved_words == {}

    def test_reserved_words_accepts_valid_translations(self):
        """A pack with valid self/cls translations validates."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": "propio", "cls": "clase"},
        }
        schema = LanguagePackSchema(**pack_data)
        assert schema.reserved_words == {"self": "propio", "cls": "clase"}

    def test_reserved_words_rejects_value_with_whitespace(self):
        """validate_mappings rejects multi-word values for reserved_words."""
        import pytest
        from pydantic import ValidationError

        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": "propio mismo"},  # space → invalid identifier
        }
        with pytest.raises(ValidationError):
            LanguagePackSchema(**pack_data)

    def test_reserved_words_rejects_empty_value(self):
        """Empty translations are rejected like any other category."""
        import pytest
        from pydantic import ValidationError

        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": ""},
        }
        with pytest.raises(ValidationError):
            LanguagePackSchema(**pack_data)

    def test_check_duplicates_detects_reserved_word_duplicates(self):
        """Duplicate translations within reserved_words are surfaced."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": "propio", "cls": "propio"},
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        assert result["passed"] is False
        assert len(result["reserved_word_duplicates"]) == 1
        assert result["reserved_word_duplicates"][0]["translation"] == "propio"
        assert set(result["reserved_word_duplicates"][0]["source_terms"]) == {
            "cls",
            "self",
        }
        assert result["total_conflicts"] >= 1

    def test_check_duplicates_clean_when_reserved_words_unique(self):
        """No duplicates surfaced when reserved_word translations are unique."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": "propio", "cls": "clase"},
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        assert result["passed"] is True
        assert result["reserved_word_duplicates"] == []

    def test_check_identifier_validity_includes_reserved_words(self):
        """check_identifier_validity exposes invalid_reserved_words list."""
        # Valid case: result includes the key with empty list
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": "propio"},
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_identifier_validity(schema)
        assert "invalid_reserved_words" in result
        assert result["invalid_reserved_words"] == []
        assert result["passed"] is True

    def test_get_validation_report_includes_reserved_words_count(self):
        """The validation report exposes reserved_words_count for symmetry."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "reserved_words": {"self": "propio", "cls": "clase"},
        }
        schema = LanguagePackSchema(**pack_data)
        report = SchemaValidator.get_validation_report(schema)
        assert "reserved_words_count" in report
        assert report["reserved_words_count"] == 2

    def test_get_validation_report_zero_reserved_words_when_absent(self):
        """Backward-compat: reserved_words_count is 0 when section omitted."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir"},
        }
        schema = LanguagePackSchema(**pack_data)
        report = SchemaValidator.get_validation_report(schema)
        assert report["reserved_words_count"] == 0


class TestCrossSectionCollisions:
    """Test cross-section collision detection in check_duplicates (CORE-710).

    Pre-Copilot-review-fix: check_duplicates only detected duplicates
    WITHIN each section. The AYA-213 Cycle-4 Urdu failure mode (a
    reserved_word value matching a keyword value in the same pack) would
    pass validation silently. These tests pin the cross-section detection.
    """

    def test_clean_pack_passes_cross_section_check(self):
        """A pack with distinct values across all sections has no collisions."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "definir", "class": "clase"},
            "builtins": {"print": "imprimir"},
            "exceptions": {"ValueError": "ErrorValor"},
            "reserved_words": {"self": "propio", "cls": "claseref"},
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        assert result["passed"] is True
        assert result["cross_section_collisions"] == []

    def test_keyword_reserved_word_collision_detected(self):
        """The exact AYA-213 Cycle-4 Urdu failure mode.

        keyword.in -> X and reserved_word.self -> X. At runtime the
        translator dispatches keyword first, so the reserved-word value
        silently round-trips to `in` instead of `self`. Pre-CORE-710 this
        was the SyntaxError-on-round-trip bug. The validator must catch it.
        """
        pack_data = {
            "language": "ur",
            "target": "python",
            "version": "3.10",
            "keywords": {"in": "miyn"},  # Latin proxy for مین
            "reserved_words": {"self": "miyn"},  # would collide
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        assert result["passed"] is False
        assert len(result["cross_section_collisions"]) == 1
        col = result["cross_section_collisions"][0]
        assert col["translation"] == "miyn"
        assert col["count"] == 2
        sections = {loc["section"] for loc in col["locations"]}
        assert sections == {"keyword", "reserved_word"}

    def test_keyword_builtin_collision_detected(self):
        """Same value across keyword + builtin also flagged."""
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "shared"},
            "builtins": {"print": "shared"},
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        assert result["passed"] is False
        assert len(result["cross_section_collisions"]) == 1

    def test_intra_section_dup_not_double_counted_as_cross_section(self):
        """Two keywords mapping to same value: only intra-section counts.

        cross_section_collisions only fires when a value appears in
        TWO OR MORE DIFFERENT sections. Pure intra-section duplicates
        are caught by find_duplicate_values and shouldn't be
        double-counted in the cross-section list.
        """
        pack_data = {
            "language": "es",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "shared", "class": "shared"},  # intra-dup only
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        assert result["passed"] is False
        assert len(result["keyword_duplicates"]) == 1
        # Cross-section list must NOT include this since both occurrences
        # are in the same section
        assert result["cross_section_collisions"] == []

    def test_total_conflicts_includes_cross_section(self):
        """total_conflicts must include cross-section collisions."""
        pack_data = {
            "language": "ur",
            "target": "python",
            "version": "3.10",
            "keywords": {"in": "miyn", "def": "shared", "class": "shared"},
            "reserved_words": {"self": "miyn"},
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        # 1 intra-section keyword dup (def/class -> shared)
        # 1 cross-section collision (miyn in keyword + reserved_word)
        assert result["total_conflicts"] == 2

    def test_three_way_cross_section_collision(self):
        """A value in three sections is reported with all three locations."""
        pack_data = {
            "language": "zz",
            "target": "python",
            "version": "3.10",
            "keywords": {"def": "X"},
            "builtins": {"print": "X"},
            "exceptions": {"ValueError": "X"},
        }
        schema = LanguagePackSchema(**pack_data)
        result = SchemaValidator.check_duplicates(schema)
        assert len(result["cross_section_collisions"]) == 1
        col = result["cross_section_collisions"][0]
        assert col["count"] == 3
        sections = {loc["section"] for loc in col["locations"]}
        assert sections == {"keyword", "builtin", "exception"}

    def test_all_51_real_packs_have_no_cross_section_collisions(self):
        """Real packs in the repo should be clean.

        Regression guard: if a future pack edit introduces a cross-section
        collision, this test fails so the issue is caught at PR time
        rather than at runtime via the AYA-213 failure mode.
        """
        import yaml

        from legesher_i18n.language_registry import get_active_language_codes

        from tests import pack_file

        broken = []
        for lang_code in get_active_language_codes():
            yml = pack_file(lang_code, "3.10")
            if not yml.exists():
                continue
            data = yaml.safe_load(yml.read_text(encoding="utf-8"))
            schema = LanguagePackSchema(**data)
            result = SchemaValidator.check_duplicates(schema)
            if result["cross_section_collisions"]:
                broken.append((lang_code, result["cross_section_collisions"]))
        assert not broken, f"Cross-section collisions in real packs: {broken}"
