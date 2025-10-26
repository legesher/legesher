"""Schema validation for language packs and version indexes.

This module provides Pydantic models and validation utilities for ensuring
language packs and version indexes conform to the expected schema.
"""

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from .exceptions import PackValidationError


class LanguagePackMetadata(BaseModel):
    """Metadata section of a language pack."""

    python_version_min: Optional[str] = None
    python_version_max: Optional[str] = None
    compatibility_tested: list[str] = Field(default_factory=list)
    last_updated: Optional[str] = None
    community_reviewed: bool = False
    author: Optional[str] = None
    license: Optional[str] = None


class LanguagePackSchema(BaseModel):
    """Schema for language pack YAML files."""

    language: str = Field(..., min_length=2, max_length=10)
    target: str = Field(..., min_length=2)
    version: str = Field(..., pattern=r"^\d+\.\d+$")
    extends: Optional[str] = None
    keywords: dict[str, str] = Field(default_factory=dict)
    builtins: dict[str, str] = Field(default_factory=dict)
    metadata: Optional[LanguagePackMetadata] = None

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validate language code format (ISO 639-1)."""
        if not v.isalpha():
            raise ValueError(f"Language code must be alphabetic: {v}")
        return v.lower()

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        """Validate target language (programming language)."""
        allowed_targets = ["python", "javascript", "java", "rust", "go", "ruby"]
        if v.lower() not in allowed_targets:
            # For now, allow any target but warn in future versions
            pass
        return v.lower()

    @field_validator("extends")
    @classmethod
    def validate_extends_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate extends path for security (prevent path traversal).

        Allows one level up for version inheritance (e.g., ../3.10/es.yml)
        but prevents deeper traversal or absolute paths.
        """
        if v is None:
            return v

        # Reject absolute paths
        if v.startswith("/"):
            raise ValueError(f"Absolute paths not allowed in extends: {v}")

        # Allow one level up for version inheritance (../X.Y/file.yml)
        if ".." in v:
            # Count occurrences of ../
            if v.count("../") > 1:
                raise ValueError(
                    f"Multiple parent directory traversal not allowed: {v}"
                )

            # Must start with exactly one ../
            if not v.startswith("../"):
                raise ValueError(f"Invalid path traversal pattern: {v}")

        # Extends should be a relative path to YAML
        if not (v.endswith(".yml") or v.endswith(".yaml")):
            raise ValueError(f"Extends must point to a YAML file: {v}")

        return v

    @field_validator("keywords", "builtins")
    @classmethod
    def validate_mappings(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate keyword/builtin mappings."""
        for key, value in v.items():
            if not key or not value:
                raise ValueError("Empty keys or values not allowed in mappings")
            if not isinstance(value, str):
                raise ValueError(f"Mapping values must be strings: {key}={value}")
        return v


class SchemaValidator:
    """Utilities for validating language packs and checking completeness."""

    @staticmethod
    def validate_pack(pack_data: dict[str, Any], pack_path: Path) -> LanguagePackSchema:
        """Validate a language pack against the schema.

        Args:
            pack_data: Raw pack data from YAML
            pack_path: Path to pack file (for error messages)

        Returns:
            Validated LanguagePackSchema instance

        Raises:
            PackValidationError: If validation fails
        """
        try:
            return LanguagePackSchema(**pack_data)
        except Exception as e:
            errors = [str(e)]
            raise PackValidationError(str(pack_path), errors)

    @staticmethod
    def check_required_fields(pack_data: dict[str, Any], pack_path: Path) -> list[str]:
        """Check if all required fields are present.

        Args:
            pack_data: Raw pack data from YAML
            pack_path: Path to pack file (for error messages)

        Returns:
            List of missing field names (empty if all present)
        """
        required = ["language", "target", "version"]
        missing = []

        for field in required:
            if field not in pack_data:
                missing.append(field)

        return missing

    @staticmethod
    def check_completeness(
        pack_schema: LanguagePackSchema,
        expected_keywords: Optional[set[str]] = None,
    ) -> list[str]:
        """Check if a language pack is complete.

        Optionally compare against a set of expected keywords to find missing
        translations.

        Args:
            pack_schema: Validated language pack
            expected_keywords: Set of keywords that should be present

        Returns:
            List of warning messages about missing translations
        """
        warnings = []

        # Check if pack has any keywords
        if not pack_schema.keywords:
            warnings.append("No keywords defined in pack")

        # Check against expected keywords if provided
        if expected_keywords:
            defined = set(pack_schema.keywords.keys())
            missing = expected_keywords - defined

            if missing:
                warnings.append(
                    f"Missing translations for {len(missing)} keywords: "
                    f"{', '.join(sorted(list(missing)[:10]))}"
                    + ("..." if len(missing) > 10 else "")
                )

        # Check metadata completeness
        if not pack_schema.metadata:
            warnings.append("No metadata section defined")
        elif pack_schema.metadata:
            if not pack_schema.metadata.last_updated:
                warnings.append("Metadata missing last_updated field")
            if not pack_schema.metadata.python_version_min:
                warnings.append("Metadata missing python_version_min field")

        return warnings

    @staticmethod
    def validate_inheritance_path(extends_path: str, current_pack_path: Path) -> Path:
        """Validate and resolve an inheritance path.

        Args:
            extends_path: Path from extends field (relative)
            current_pack_path: Path to current pack file

        Returns:
            Resolved absolute path to parent pack

        Raises:
            PackValidationError: If path is invalid or insecure
        """
        try:
            # Resolve path relative to current pack
            pack_dir = current_pack_path.parent
            resolved = (pack_dir / extends_path).resolve()

            # Security check: Ensure resolved path doesn't escape pack directory
            # Get the root language packs directory (should be libs/i18n/languages/)
            pack_root = current_pack_path
            while (
                pack_root.parent.name != "languages" and pack_root.parent != pack_root
            ):
                pack_root = pack_root.parent

            if pack_root.parent.name == "languages":
                language_root = pack_root.parent

                # Ensure resolved path is within language packs directory
                try:
                    resolved.relative_to(language_root)
                except ValueError:
                    raise PackValidationError(
                        str(current_pack_path),
                        [
                            f"Path traversal detected: {extends_path} escapes pack directory"
                        ],
                    )

            # Check if file exists
            if not resolved.exists():
                raise PackValidationError(
                    str(current_pack_path), [f"Parent pack not found: {extends_path}"]
                )

            return resolved

        except Exception as e:
            if isinstance(e, PackValidationError):
                raise
            raise PackValidationError(
                str(current_pack_path), [f"Invalid extends path: {extends_path} - {e}"]
            )

    @staticmethod
    def get_validation_report(
        pack_schema: LanguagePackSchema,
        expected_keywords: Optional[set[str]] = None,
    ) -> dict[str, Any]:
        """Generate a comprehensive validation report for a pack.

        Args:
            pack_schema: Validated language pack
            expected_keywords: Set of keywords that should be present

        Returns:
            Dictionary with validation results and statistics
        """
        warnings = SchemaValidator.check_completeness(pack_schema, expected_keywords)

        return {
            "valid": True,
            "language": pack_schema.language,
            "target": pack_schema.target,
            "version": pack_schema.version,
            "has_inheritance": pack_schema.extends is not None,
            "keywords_count": len(pack_schema.keywords),
            "builtins_count": len(pack_schema.builtins),
            "warnings": warnings,
            "has_metadata": pack_schema.metadata is not None,
            "completeness_score": (
                1.0 - (len(warnings) / 10.0) if warnings else 1.0
            ),  # Simple scoring
        }
