"""Schema validation for language packs and version indexes.

This module provides Pydantic models and validation utilities for ensuring
language packs and version indexes conform to the expected schema.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .exceptions import PackValidationError, VersionIndexError

# Soft keywords that contain special characters but are valid Python syntax
# These are special cases that bypass the normal identifier validation
# Reference: https://docs.python.org/3/reference/lexical_analysis.html#soft-keywords
SOFT_KEYWORDS = {"except*"}


class LanguagePackMetadata(BaseModel):
    """Metadata section of a language pack."""

    python_version_min: str | None = None
    python_version_max: str | None = None
    compatibility_tested: list[str] = Field(default_factory=list)
    last_updated: str | None = None
    community_reviewed: bool = False
    author: str | None = None
    license: str | None = None


class CulturalNote(BaseModel):
    """Cultural context note for a translation."""

    keyword: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)
    language: str = Field(..., min_length=2, max_length=10)


class LanguagePackSchema(BaseModel):
    """Schema for language pack YAML files.

    Conforms to MLCP v1.0 specification for multilingual code protocol.
    Reference: private-working-memory/planning/architecture/mlcp-v1.md
    """

    # MLCP v1.0 Core Required Fields
    language: str = Field(..., min_length=2, max_length=3)
    target: str = Field(..., min_length=2)
    version: str = Field(..., pattern=r"^\d+\.\d+$")

    # MLCP v1.0 Optional Fields
    extends: str | None = None
    keywords: dict[str, str] = Field(default_factory=dict)
    builtins: dict[str, str] = Field(default_factory=dict)
    exceptions: dict[str, str] = Field(default_factory=dict)

    # MLCP v1.0 Extended Optional Fields
    operators: dict[str, str] = Field(default_factory=dict)
    standard_library: dict[str, str] = Field(default_factory=dict)
    cultural_notes: list[CulturalNote] = Field(default_factory=list)

    # Metadata
    metadata: LanguagePackMetadata | None = None

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validate language code format (ISO 639-1/639-2).

        ISO 639-1: 2-letter codes (primary standard)
        ISO 639-2: 3-letter codes (extended support)
        """
        if not v.isalpha():
            raise ValueError(f"Language code must be alphabetic: {v}")

        # Enforce ISO 639 standards: 2 or 3 letters only
        if len(v) not in (2, 3):
            raise ValueError(
                f"Language code must be 2 or 3 letters (ISO 639-1/639-2): '{v}' "
                f"has {len(v)} letters"
            )

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
    def validate_extends_path(cls, v: str | None) -> str | None:
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

    @field_validator(
        "keywords", "builtins", "exceptions", "operators", "standard_library"
    )
    @classmethod
    def validate_mappings(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate keyword/builtin/exception/operator/stdlib mappings.

        Translations must be valid Python identifiers to work with the
        TokenTranslator, which uses Python's tokenize module.
        """
        for key, value in v.items():
            if not key or not value:
                raise ValueError("Empty keys or values not allowed in mappings")
            if not isinstance(value, str):
                raise ValueError(f"Mapping values must be strings: {key}={value}")

            # Check for leading/trailing whitespace
            if value != value.strip():
                raise ValueError(
                    f"Translation has leading/trailing whitespace: '{key}' -> '{value}'. "
                    f"Use '{value.strip()}' instead."
                )

            # Check for valid Python identifier (required for TokenTranslator)
            # Note: We use a relaxed check that allows Unicode letters per PEP 3131
            # Special case: soft keywords like 'except*' can have translations ending with '*'
            if not cls._is_valid_identifier(value, source_key=key):
                raise ValueError(
                    f"Translation is not a valid Python identifier: '{key}' -> '{value}'. "
                    "Translations must not contain spaces, punctuation, or escape sequences."
                )
        return v

    @classmethod
    def _is_valid_identifier(cls, value: str, source_key: str | None = None) -> bool:
        """Check if a value is a valid Python identifier or soft keyword.

        Per PEP 3131, Python identifiers can contain Unicode letters and digits,
        but must start with a letter or underscore, and cannot contain spaces
        or most punctuation.

        Special case: Soft keywords like 'except*' (Python 3.11+) are allowed
        even though they contain special characters. Translations of soft keywords
        (e.g., 'excepto*' for Spanish 'except*') are also allowed.

        Args:
            value: The translation value to check
            source_key: The original English keyword (used to detect soft keyword translations)

        Returns:
            True if valid Python identifier or soft keyword, False otherwise
        """
        if not value:
            return False

        # Allow soft keywords (e.g., 'except*' in Python 3.11+)
        if value in SOFT_KEYWORDS:
            return True

        # Allow translations of soft keywords (e.g., 'excepto*' for 'except*')
        # If the source key is a soft keyword, allow the translation to follow the same pattern
        if source_key in SOFT_KEYWORDS and value.endswith("*"):
            # Validate the base part (without the *)
            base_value = value[:-1]
            if base_value and cls._is_valid_identifier(base_value):
                return True

        # Quick check: if it contains spaces, it's invalid
        if " " in value:
            return False

        # Check for common invalid characters (escape sequences, punctuation)
        invalid_chars = [
            "\\",
            "«",
            "»",
            "¢",
            "£",
            "~",
            "@",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
        ]
        for char in invalid_chars:
            if char in value:
                return False

        # Use Python's isidentifier() for the actual check
        # This handles Unicode letters properly per PEP 3131
        return value.isidentifier()


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
        expected_keywords: set[str] | None = None,
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
    def validate_inheritance_path(
        extends_path: str,
        current_pack_path: Path,
        sandbox_root: Path,
    ) -> Path:
        """Validate and resolve an inheritance path.

        The sandbox check is unconditional: the resolved path must stay
        within ``sandbox_root``. Callers pick the sandbox root appropriate
        for the pack layout in use — currently always the ``packs/``
        directory that contains the current pack file.

        Args:
            extends_path: Path from extends field (relative)
            current_pack_path: Path to current pack file
            sandbox_root: Directory that the resolved path must stay within

        Returns:
            Resolved absolute path to parent pack

        Raises:
            PackValidationError: If path is invalid or insecure
        """
        try:
            # Resolve path relative to current pack
            pack_dir = current_pack_path.parent
            resolved = (pack_dir / extends_path).resolve()

            # Ensure resolved path is within the sandbox, regardless of layout
            sandbox_resolved = sandbox_root.resolve()
            try:
                resolved.relative_to(sandbox_resolved)
            except ValueError:
                raise PackValidationError(
                    str(current_pack_path),
                    [
                        f"Path traversal detected: {extends_path} escapes sandbox "
                        f"root {sandbox_resolved}"
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
    def check_completeness_enhanced(
        pack_schema: LanguagePackSchema,
        version_index_path: Path | None = None,
    ) -> dict[str, Any]:
        """Enhanced completeness checking with version-index integration.

        Provides detailed analysis of pack completeness including:
        - Percentage of expected keywords translated
        - Missing critical keywords
        - Metadata completeness score
        - Recommendations for improvement

        Args:
            pack_schema: Validated language pack
            version_index_path: Optional path to version-index.yml

        Returns:
            Dictionary with enhanced completeness results:
            - completeness_percentage: float - 0.0 to 1.0
            - missing_keywords: list - Keywords that should be translated
            - missing_builtins: list - Critical builtins not translated
            - metadata_score: float - Metadata completeness (0.0 to 1.0)
            - recommendations: list - Actionable improvement suggestions
            - passed: bool - True if meets minimum threshold (90%)
        """
        results = {
            "completeness_percentage": 0.0,
            "missing_keywords": [],
            "missing_builtins": [],
            "metadata_score": 0.0,
            "recommendations": [],
            "passed": False,
        }

        # Get expected keywords from version index if available
        expected_keywords: set[str] = set()
        if version_index_path and version_index_path.exists():
            try:
                from .version_index import VersionIndex

                index = VersionIndex.load(version_index_path)
                expected_keywords = index.get_all_keywords(pack_schema.version)
            except (VersionIndexError, Exception):
                # Fall back to basic check if version index unavailable
                pass

        # Calculate keyword completeness
        if expected_keywords:
            defined_keywords = set(pack_schema.keywords.keys())
            missing = expected_keywords - defined_keywords
            results["missing_keywords"] = sorted(list(missing))
            results["completeness_percentage"] = (
                len(defined_keywords) / len(expected_keywords)
                if expected_keywords
                else 0.0
            )
        elif pack_schema.keywords:
            # No version index, but pack has keywords - give benefit of doubt
            results["completeness_percentage"] = 0.75
        else:
            results["completeness_percentage"] = 0.0
            results["recommendations"].append(
                "No keywords defined - add translations for Python keywords"
            )

        # Check for critical builtins (commonly used)
        critical_builtins = {"print", "len", "range", "str", "int", "list", "dict"}
        defined_builtins = set(pack_schema.builtins.keys())
        missing_builtins = critical_builtins - defined_builtins
        results["missing_builtins"] = sorted(list(missing_builtins))

        if missing_builtins:
            results["recommendations"].append(
                f"Add translations for critical builtins: {', '.join(sorted(list(missing_builtins)[:5]))}"
            )

        # Calculate metadata completeness score
        metadata_score = 0.0
        if pack_schema.metadata:
            # Each field worth ~14% (7 fields total)
            if pack_schema.metadata.last_updated:
                metadata_score += 0.14
            if pack_schema.metadata.python_version_min:
                metadata_score += 0.14
            if pack_schema.metadata.python_version_max:
                metadata_score += 0.14
            if pack_schema.metadata.compatibility_tested:
                metadata_score += 0.14
            if pack_schema.metadata.author:
                metadata_score += 0.14
            if pack_schema.metadata.license:
                metadata_score += 0.14
            if pack_schema.metadata.community_reviewed:
                metadata_score += 0.14

            results["metadata_score"] = min(metadata_score, 1.0)
        else:
            results["recommendations"].append(
                "Add metadata section with author, last_updated, and version info"
            )

        # Generate recommendations based on completeness
        if results["completeness_percentage"] < 0.5:
            results["recommendations"].append(
                f"Pack is only {results['completeness_percentage']:.0%} complete - add more keyword translations"
            )
        elif results["completeness_percentage"] < 0.9:
            results["recommendations"].append(
                f"Pack is {results['completeness_percentage']:.0%} complete - {len(results['missing_keywords'])} keywords remaining"
            )

        # Check if pack passes minimum threshold (90% keywords + 50% metadata)
        results["passed"] = (
            results["completeness_percentage"] >= 0.9
            and results["metadata_score"] >= 0.5
        )

        return results

    @staticmethod
    def check_duplicates(pack_schema: LanguagePackSchema) -> dict[str, Any]:
        """Check for duplicate translations (reversibility issues).

        Detects when multiple source terms map to the same target translation,
        which can cause ambiguity when translating back to the source language.

        Args:
            pack_schema: Validated language pack

        Returns:
            Dictionary with duplicate detection results:
            - passed: bool - True if no duplicates found
            - keyword_duplicates: list of conflicts in keywords
            - builtin_duplicates: list of conflicts in builtins
            - operator_duplicates: list of conflicts in operators
            - stdlib_duplicates: list of conflicts in standard_library
        """

        def find_duplicate_values(mappings: dict[str, str]) -> list[dict[str, Any]]:
            """Find values that appear multiple times."""
            reverse_map: dict[str, list[str]] = {}
            for key, value in mappings.items():
                if value in reverse_map:
                    reverse_map[value].append(key)
                else:
                    reverse_map[value] = [key]

            duplicates = []
            for translation, source_terms in reverse_map.items():
                if len(source_terms) > 1:
                    duplicates.append(
                        {
                            "translation": translation,
                            "source_terms": sorted(source_terms),
                            "count": len(source_terms),
                        }
                    )

            return duplicates

        keyword_duplicates = find_duplicate_values(pack_schema.keywords)
        builtin_duplicates = find_duplicate_values(pack_schema.builtins)
        exception_duplicates = find_duplicate_values(pack_schema.exceptions)
        operator_duplicates = find_duplicate_values(pack_schema.operators)
        stdlib_duplicates = find_duplicate_values(pack_schema.standard_library)

        total_duplicates = (
            len(keyword_duplicates)
            + len(builtin_duplicates)
            + len(exception_duplicates)
            + len(operator_duplicates)
            + len(stdlib_duplicates)
        )

        return {
            "passed": total_duplicates == 0,
            "keyword_duplicates": keyword_duplicates,
            "builtin_duplicates": builtin_duplicates,
            "exception_duplicates": exception_duplicates,
            "operator_duplicates": operator_duplicates,
            "stdlib_duplicates": stdlib_duplicates,
            "total_conflicts": total_duplicates,
        }

    @staticmethod
    def check_mlcp_conformance(pack_schema: LanguagePackSchema) -> dict[str, Any]:
        """Check MLCP v1.0 specification conformance.

        Validates that the language pack conforms to the Multilingual Code Protocol
        v1.0 specification as defined in private-working-memory/planning/architecture/mlcp-v1.md

        Args:
            pack_schema: Validated language pack

        Returns:
            Dictionary with MLCP conformance results:
            - conformance_level: str - "core" | "extended" | "full"
            - passed: bool - True if meets at least "core" level
            - checks: dict - Individual check results
            - spec_version: str - MLCP version checked against
            - issues: list - Any conformance issues found
        """
        checks = {}
        issues = []

        # MLCP v1.0 Core Required Fields
        checks["has_language_field"] = bool(pack_schema.language)
        checks["has_target_field"] = bool(pack_schema.target)
        checks["has_version_field"] = bool(pack_schema.version)

        if not all(
            [
                checks["has_language_field"],
                checks["has_target_field"],
                checks["has_version_field"],
            ]
        ):
            issues.append(
                "Missing MLCP v1.0 core required fields (language, target, version)"
            )

        # ISO 639-1 Language Code Validation
        checks["valid_iso639_code"] = (
            len(pack_schema.language) == 2 and pack_schema.language.isalpha()
        )
        if not checks["valid_iso639_code"]:
            issues.append(
                f"Language code '{pack_schema.language}' is not a valid ISO 639-1 code (must be 2 letters)"
            )

        # Version Format Validation (X.Y)
        checks["valid_version_format"] = bool(
            pack_schema.version and "." in pack_schema.version
        )
        if not checks["valid_version_format"]:
            issues.append(
                f"Version '{pack_schema.version}' does not match MLCP format (expected X.Y)"
            )

        # MLCP v1.0 Extended: Keywords OR Builtins (at least one)
        checks["has_translations"] = bool(pack_schema.keywords or pack_schema.builtins)
        if not checks["has_translations"]:
            issues.append(
                "MLCP Extended requires either keywords or builtins translations"
            )

        # MLCP v1.0 Extended: Metadata section
        checks["has_metadata"] = pack_schema.metadata is not None
        if not checks["has_metadata"]:
            issues.append("MLCP Extended recommends metadata section")

        # Metadata Required Fields (if metadata exists)
        if pack_schema.metadata:
            checks["has_mlcp_version"] = True  # Not in our schema yet, but should be
            checks["has_authors"] = bool(pack_schema.metadata.author)
            checks["has_last_updated"] = bool(pack_schema.metadata.last_updated)

            if not checks["has_authors"]:
                issues.append(
                    "Metadata missing 'author' field (MLCP v1.0 recommendation)"
                )
            if not checks["has_last_updated"]:
                issues.append(
                    "Metadata missing 'last_updated' field (MLCP v1.0 requirement)"
                )
        else:
            checks["has_mlcp_version"] = False
            checks["has_authors"] = False
            checks["has_last_updated"] = False

        # Security: Path Traversal Prevention (already enforced by Pydantic)
        checks["security_path_traversal"] = True  # Validated by field_validator

        # MLCP v1.0 Full: Optional Extended Fields
        checks["has_operators"] = bool(pack_schema.operators)
        checks["has_stdlib"] = bool(pack_schema.standard_library)
        checks["has_cultural_notes"] = bool(pack_schema.cultural_notes)

        # Determine conformance level
        core_passed = all(
            [
                checks["has_language_field"],
                checks["has_target_field"],
                checks["has_version_field"],
                checks["valid_iso639_code"],
                checks["valid_version_format"],
                checks["security_path_traversal"],
            ]
        )

        extended_passed = core_passed and all(
            [
                checks["has_translations"],
                checks["has_metadata"],
                checks["has_last_updated"],
            ]
        )

        full_passed = extended_passed and any(
            [
                checks["has_operators"],
                checks["has_stdlib"],
                checks["has_cultural_notes"],
            ]
        )

        if full_passed:
            conformance_level = "full"
        elif extended_passed:
            conformance_level = "extended"
        elif core_passed:
            conformance_level = "core"
        else:
            conformance_level = "non-conformant"

        return {
            "conformance_level": conformance_level,
            "passed": core_passed,
            "checks": checks,
            "spec_version": "1.0",
            "issues": issues,
            "core_conformant": core_passed,
            "extended_conformant": extended_passed,
            "full_conformant": full_passed,
        }

    @staticmethod
    def get_validation_report(
        pack_schema: LanguagePackSchema,
        expected_keywords: set[str] | None = None,
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
            "exceptions_count": len(pack_schema.exceptions),
            "warnings": warnings,
            "has_metadata": pack_schema.metadata is not None,
            "completeness_score": (
                1.0 - (len(warnings) / 10.0) if warnings else 1.0
            ),  # Simple scoring
        }

    @staticmethod
    def check_identifier_validity(pack_schema: LanguagePackSchema) -> dict[str, Any]:
        """Check if all translations are valid Python identifiers.

        Validates that translations can work with the TokenTranslator, which uses
        Python's tokenize module and requires translations to be valid identifiers.

        Args:
            pack_schema: Validated language pack

        Returns:
            Dictionary with validation results:
            - passed: bool - True if all translations are valid identifiers
            - invalid_keywords: list - Keywords with invalid translations
            - invalid_builtins: list - Builtins with invalid translations
            - invalid_exceptions: list - Exceptions with invalid translations
            - total_issues: int - Total number of invalid translations
            - issues: list - Human-readable issue descriptions
        """
        invalid_keywords = []
        invalid_builtins = []
        invalid_exceptions = []
        issues = []

        def check_mapping(
            mappings: dict[str, str], category: str
        ) -> list[dict[str, str]]:
            """Check a mapping dict for invalid identifiers."""
            invalid = []
            for key, value in mappings.items():
                # Check for whitespace
                if value != value.strip():
                    invalid.append(
                        {
                            "key": key,
                            "value": value,
                            "reason": "has leading/trailing whitespace",
                        }
                    )
                    issues.append(
                        f"{category}: '{key}' -> '{value}' has leading/trailing whitespace"
                    )
                # Check for spaces within
                elif " " in value:
                    invalid.append(
                        {
                            "key": key,
                            "value": value,
                            "reason": "contains spaces",
                        }
                    )
                    issues.append(f"{category}: '{key}' -> '{value}' contains spaces")
                # Check for invalid characters (pass source_key for soft keyword support)
                elif not LanguagePackSchema._is_valid_identifier(value, source_key=key):
                    invalid.append(
                        {
                            "key": key,
                            "value": value,
                            "reason": "not a valid Python identifier",
                        }
                    )
                    issues.append(
                        f"{category}: '{key}' -> '{value}' is not a valid Python identifier"
                    )
            return invalid

        invalid_keywords = check_mapping(pack_schema.keywords, "keyword")
        invalid_builtins = check_mapping(pack_schema.builtins, "builtin")
        invalid_exceptions = check_mapping(pack_schema.exceptions, "exception")

        total_issues = (
            len(invalid_keywords) + len(invalid_builtins) + len(invalid_exceptions)
        )

        return {
            "passed": total_issues == 0,
            "invalid_keywords": invalid_keywords,
            "invalid_builtins": invalid_builtins,
            "invalid_exceptions": invalid_exceptions,
            "total_issues": total_issues,
            "issues": issues,
        }
