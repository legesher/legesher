"""Schema validation for language packs and version indexes.

This module provides Pydantic models and validation utilities for ensuring
language packs and version indexes conform to the expected schema.

In addition to the original (Pydantic-backed) validation, it provides a
Unicode/script **safety** layer (``check_normalization``,
``check_script_consistency``, ``check_format_chars``,
``check_keyword_collisions``, ``check_min_interpreter_identifier``) plus a
``validate_pack_strict`` aggregator that runs every safety check together with
the previously-dead ``check_duplicates`` / ``check_identifier_validity``
passes. These were added to harden the 51 -> 103 language expansion against the
classes of corruption found in shipped machine-translated packs (NFKC
instability, fullwidth keyword spoofs, foreign-script bleed-through, illegal
bidi/format controls, and live-keyword collisions). See
:mod:`legesher_i18n.script_policy` for the per-language allowlists.
"""

import keyword
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .exceptions import PackValidationError, VersionIndexError
from .script_policy import (
    ALWAYS_ALLOWED_SCRIPTS,
    FORBIDDEN_FORMAT_CHARS,
    has_policy,
    nfkc_delta_class,
    policy_for,
    scripts_of,
)

# Soft keywords that contain special characters but are valid Python syntax
# These are special cases that bypass the normal identifier validation
# Reference: https://docs.python.org/3/reference/lexical_analysis.html#soft-keywords
SOFT_KEYWORDS = {"except*"}

# Pack sections whose values are translation identifiers (the targets the
# safety checks inspect). ``cultural_notes`` and ``metadata`` are excluded
# because they are free prose / structured metadata, not identifiers.
_TRANSLATION_SECTIONS = (
    "keywords",
    "builtins",
    "exceptions",
    "reserved_words",
    "operators",
    "standard_library",
)

# The one intentional cross-section duplicate: ``type`` is both a Python
# keyword (3.12+ ``type`` statement) and a builtin. Packs translate both to the
# same value on purpose, so the strict duplicate check allow-lists exactly this
# (section, key) pair-up: ``keywords.type`` == ``builtins.type``.
_ALLOWED_DUPLICATE_KEYS = frozenset({"type"})

# A pack value is a TERM, not a definition. Machine translation sometimes emits a
# sentence-length gloss in place of a short native word (the CORE-1318 "th max"
# = 45-char definition, "hi isinstance" = 90-char sentence). Such values are
# valid identifiers, so they pass the safety checks, but they are a quality
# defect. The threshold is code points: the shipped legitimate compounds top out
# around the high 30s (German/Finnish/Thai error compounds), while the
# descriptions run 45-110. 40 catches the sentences while sparing real compounds.
# Emitted as a WARNING (advisory), so it surfaces for native review without
# blocking the safety gate.
MAX_TERM_LENGTH = 40


@dataclass(frozen=True)
class Finding:
    """A single validation finding from the script-safety layer.

    Attributes:
        severity: ``"error"`` or ``"warning"``. Errors are pack-corrupting;
            warnings are advisory (none are emitted today but the field keeps
            the report shape stable).
        code: Stable machine-readable code (e.g. ``"nfkc-instability"``,
            ``"foreign-script"``) for grouping and CI filtering.
        location: Human-readable pointer to the offending value, usually
            ``"{section}.{key}"`` (e.g. ``"builtins.bool"``). For a cross-section
            finding (the same value colliding across sections) this is a
            comma-separated list of such pointers (e.g.
            ``"keywords.type, builtins.type"``).
        message: Human-readable explanation of the problem.
    """

    severity: str
    code: str
    location: str
    message: str


class LanguagePackMetadata(BaseModel):
    """Metadata section of a language pack.

    Optional descriptive fields that accompany the translations in a pack
    YAML file. None of these fields affect translation behavior; they exist
    for provenance, compatibility tracking, and community review workflows.

    Attributes:
        python_version_min: Minimum Python version the pack targets.
        python_version_max: Maximum Python version the pack targets.
        compatibility_tested: Python versions this pack has been validated against.
        last_updated: ISO 8601 date of the last edit to this pack.
        community_reviewed: True once the pack has passed community validation.
        author: Pack contributor name or handle.
        license: SPDX license identifier for the translations.
    """

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

    Attributes:
        language: Target natural language code (ISO 639-1 or 639-2).
        target: Target programming language (e.g., ``"python"``).
        version: Python version string (e.g., ``"3.13"``).
        extends: Optional relative path to a parent pack for inheritance.
        keywords: Python keyword translations (e.g., ``{"def": "definir"}``).
        builtins: Built-in function and type translations.
        exceptions: Exception class name translations.
        reserved_words: Translations for Python conventions like ``self`` and
            ``cls`` that aren't actual Python keywords but are treated
            deterministically by Legesher (CORE-710).
        operators: Operator translations (MLCP extended field).
        standard_library: Stdlib symbol translations (MLCP extended field).
        cultural_notes: Per-term cultural context notes.
        metadata: Optional pack metadata block.
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
    reserved_words: dict[str, str] = Field(default_factory=dict)

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
        "keywords",
        "builtins",
        "exceptions",
        "reserved_words",
        "operators",
        "standard_library",
    )
    @classmethod
    def validate_mappings(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate keyword/builtin/exception/reserved_word/operator/stdlib mappings.

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
    """Validate language packs and check completeness against the canonical pack.

    Wraps Pydantic validation with domain-specific checks: path-traversal
    prevention for ``extends`` references, completeness scoring against the
    English reference pack, and human-readable error messages suitable for
    CLI output. All methods are static — the class is a namespace for
    related validation routines.

    Example:
        >>> import yaml
        >>> from pathlib import Path
        >>> pack_path = Path("libs/i18n/language-packs/python/es/legesher_i18n_python_es/packs/3.10.yml")
        >>> pack_data = yaml.safe_load(pack_path.read_text())
        >>> schema = SchemaValidator.validate_pack(pack_data, pack_path)
        >>> schema.language
        'es'
    """

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
        results: dict[str, Any] = {
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

        Two classes of collision are detected:

        1. **Intra-section duplicates** — two source terms in the SAME
           section (e.g., two keywords) mapping to the same translation.
           Each section produces its own ``{section}_duplicates`` list.
        2. **Cross-section collisions** (CORE-710) — the SAME translation
           value appears in TWO OR MORE different sections (e.g., a
           ``reserved_words.self`` value matching a ``keywords.in`` value).
           This is exactly the AYA-213 Cycle-4 Urdu failure mode the
           reserved_words category was introduced to prevent: at runtime
           the dispatch order resolves keyword first, so the
           reserved-word value silently round-trips to the wrong source
           token. ``cross_section_collisions`` lists these.

        Args:
            pack_schema: Validated language pack

        Returns:
            Dictionary with duplicate detection results:
            - passed: bool - True if no duplicates found
            - keyword_duplicates: list of conflicts in keywords
            - builtin_duplicates: list of conflicts in builtins
            - exception_duplicates: list of conflicts in exceptions
            - reserved_word_duplicates: list of conflicts in reserved words
            - operator_duplicates: list of conflicts in operators
            - stdlib_duplicates: list of conflicts in standard_library
            - cross_section_collisions: list of values appearing in
              multiple sections (CORE-710 reversibility guard)
        """

        def find_duplicate_values(mappings: dict[str, str]) -> list[dict[str, Any]]:
            """Find values that appear multiple times within ONE section."""
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

        def find_cross_section_collisions(
            sections: list[tuple[str, dict[str, str]]],
        ) -> list[dict[str, Any]]:
            """Find translation values appearing in two or more sections.

            Each entry's ``locations`` lists every (section, source_key)
            pair where the translation appears. Only collisions spanning
            at least two distinct sections are reported — pure intra-section
            duplicates are caught by ``find_duplicate_values`` above and
            would double-count if included here.
            """
            by_value: dict[str, list[tuple[str, str]]] = {}
            for section_name, mapping in sections:
                for source_key, target_value in mapping.items():
                    by_value.setdefault(target_value, []).append(
                        (section_name, source_key)
                    )

            collisions = []
            for translation, locations in by_value.items():
                sections_seen = {section for section, _ in locations}
                if len(sections_seen) > 1:
                    collisions.append(
                        {
                            "translation": translation,
                            "locations": [
                                {"section": s, "source_key": k}
                                for s, k in sorted(locations)
                            ],
                            "count": len(locations),
                        }
                    )
            return collisions

        keyword_duplicates = find_duplicate_values(pack_schema.keywords)
        builtin_duplicates = find_duplicate_values(pack_schema.builtins)
        exception_duplicates = find_duplicate_values(pack_schema.exceptions)
        reserved_word_duplicates = find_duplicate_values(pack_schema.reserved_words)
        operator_duplicates = find_duplicate_values(pack_schema.operators)
        stdlib_duplicates = find_duplicate_values(pack_schema.standard_library)

        cross_section_collisions = find_cross_section_collisions(
            [
                ("keyword", pack_schema.keywords),
                ("builtin", pack_schema.builtins),
                ("exception", pack_schema.exceptions),
                ("reserved_word", pack_schema.reserved_words),
                ("operator", pack_schema.operators),
                ("standard_library", pack_schema.standard_library),
            ]
        )

        total_duplicates = (
            len(keyword_duplicates)
            + len(builtin_duplicates)
            + len(exception_duplicates)
            + len(reserved_word_duplicates)
            + len(operator_duplicates)
            + len(stdlib_duplicates)
            + len(cross_section_collisions)
        )

        return {
            "passed": total_duplicates == 0,
            "keyword_duplicates": keyword_duplicates,
            "builtin_duplicates": builtin_duplicates,
            "exception_duplicates": exception_duplicates,
            "reserved_word_duplicates": reserved_word_duplicates,
            "operator_duplicates": operator_duplicates,
            "stdlib_duplicates": stdlib_duplicates,
            "cross_section_collisions": cross_section_collisions,
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
            "reserved_words_count": len(pack_schema.reserved_words),
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
            - invalid_reserved_words: list - Reserved words with invalid translations
            - total_issues: int - Total number of invalid translations
            - issues: list - Human-readable issue descriptions
        """
        invalid_keywords = []
        invalid_builtins = []
        invalid_exceptions = []
        invalid_reserved_words = []
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
        invalid_reserved_words = check_mapping(
            pack_schema.reserved_words, "reserved_word"
        )

        total_issues = (
            len(invalid_keywords)
            + len(invalid_builtins)
            + len(invalid_exceptions)
            + len(invalid_reserved_words)
        )

        return {
            "passed": total_issues == 0,
            "invalid_keywords": invalid_keywords,
            "invalid_builtins": invalid_builtins,
            "invalid_exceptions": invalid_exceptions,
            "invalid_reserved_words": invalid_reserved_words,
            "total_issues": total_issues,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # Unicode / script safety layer (51 -> 103 expansion hardening).
    #
    # Each ``check_*`` below returns a list[Finding]; ``validate_pack_strict``
    # aggregates them with the legacy duplicate / identifier checks. They are
    # deliberately granular so callers (the audit script, tests) can run one in
    # isolation. None of them load YAML or touch the filesystem — they operate
    # purely on a validated, inheritance-merged ``LanguagePackSchema``.
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_translation_items(
        pack_schema: "LanguagePackSchema",
    ) -> list[tuple[str, str, str]]:
        """Yield ``(section, key, value)`` for every translation in the pack.

        Covers all six identifier-bearing sections (keywords, builtins,
        exceptions, reserved_words, operators, standard_library). Prose and
        metadata are excluded.
        """
        items: list[tuple[str, str, str]] = []
        for section in _TRANSLATION_SECTIONS:
            mapping: dict[str, str] = getattr(pack_schema, section, {}) or {}
            for key, value in mapping.items():
                items.append((section, key, value))
        return items

    @staticmethod
    def check_normalization(pack_schema: "LanguagePackSchema") -> list["Finding"]:
        """Flag values that are not stable under NFC/NFKC normalization.

        Rule: ``value == NFC(value) == NFKC(value)``. A value that changes under
        either form is unstable: Python applies NFKC to identifiers at parse
        time, so an unnormalized source value will not round-trip and may even
        compile to a *different* identifier than the bytes on disk. Real example:
        Thai SARA AM (U+0E33) and Lao U+0EB3 decompose under NFC/NFKC.

        Returns a list of error :class:`Finding`. The ``*`` suffix of a
        soft-keyword translation is stripped before checking so ``excepto*``
        normalizes as ``excepto``.
        """
        findings: list[Finding] = []
        for section, key, value in SchemaValidator._iter_translation_items(pack_schema):
            core = SchemaValidator._strip_soft_keyword_marker(value)
            nfc = unicodedata.normalize("NFC", core)
            nfkc = unicodedata.normalize("NFKC", core)
            if core == nfc == nfkc:
                continue
            # CORE-1514 policy, shared with the v2 canon gate: legitimate Thai
            # orthography whose ONLY NFKC delta is SARA AM (U+0E33) is not a
            # defect -- CPython folds it in identifiers (PEP 3131), so both
            # spellings are one identifier. It must still be NFC-stable (SARA AM
            # is; a value that is *also* NFC-unstable is a different problem).
            if core == nfc and nfkc_delta_class(core, nfkc=nfkc) == "sara-am-only":
                continue
            findings.append(
                Finding(
                    severity="error",
                    code="nfkc-instability",
                    location=f"{section}.{key}",
                    message=(
                        f"Value '{value}' is not stable under Unicode "
                        f"normalization (NFC='{nfc}', NFKC='{nfkc}'). "
                        "Python NFKC-folds identifiers at parse time, so "
                        "the source value will not round-trip."
                    ),
                )
            )
        return findings

    @staticmethod
    def check_script_consistency(
        pack_schema: "LanguagePackSchema",
        language: str | None = None,
    ) -> list["Finding"]:
        """Flag values containing scripts outside the language's allowlist.

        Uses :func:`legesher_i18n.script_policy.scripts_of` (pure unicodedata)
        and the per-language allowlist in
        :data:`legesher_i18n.script_policy.SCRIPT_POLICIES`. ``Common`` and
        ``Inherited`` are always allowed. Catches foreign-script bleed-through
        such as Chinese ``布尔`` inside a Polish ``bool`` or a stray Cyrillic
        letter in a Thai value.

        Args:
            pack_schema: Validated, merged pack.
            language: Language code to police against. Defaults to
                ``pack_schema.language``. Default-deny: an unknown code yields a
                single ``no-policy`` finding rather than silently passing.
        """
        lang = (language or pack_schema.language).lower()
        if not has_policy(lang):
            return [
                Finding(
                    severity="error",
                    code="no-policy",
                    location=f"<pack:{lang}>",
                    message=(
                        f"No script policy registered for '{lang}'. Add an "
                        "entry to legesher_i18n.script_policy.SCRIPT_POLICIES "
                        "before shipping this language."
                    ),
                )
            ]

        policy = policy_for(lang)
        allowed = policy.scripts | ALWAYS_ALLOWED_SCRIPTS
        findings: list[Finding] = []
        for section, key, value in SchemaValidator._iter_translation_items(pack_schema):
            # Format chars (ZWJ/ZWNJ/bidi/BOM) are policed separately; strip the
            # language's explicitly-allowed ones so they don't muddy the script
            # set, and drop a trailing soft-keyword ``*``.
            core = SchemaValidator._strip_soft_keyword_marker(value)
            cleaned = "".join(
                ch for ch in core if ch not in policy.allowed_format_chars
            )
            present = scripts_of(cleaned)
            offending = present - allowed
            if offending:
                findings.append(
                    Finding(
                        severity="error",
                        code="foreign-script",
                        location=f"{section}.{key}",
                        message=(
                            f"Value '{value}' contains script(s) "
                            f"{sorted(offending)} not allowed for '{lang}' "
                            f"(allowed: {sorted(policy.scripts)})."
                        ),
                    )
                )
        return findings

    @staticmethod
    def check_format_chars(
        pack_schema: "LanguagePackSchema",
        language: str | None = None,
    ) -> list["Finding"]:
        """Flag illegal Unicode format / bidi-control characters in values.

        Rejects every character in
        :data:`legesher_i18n.script_policy.FORBIDDEN_FORMAT_CHARS` (bidi
        controls U+202A-202E / U+2066-2069 / U+200E / U+200F / U+061C, the
        tatweel U+0640, and the BOM U+FEFF) plus any other Unicode ``Cf``
        (format) character, *unless* the language's policy explicitly
        allow-lists it. Today only Sinhala (ZWJ U+200D) and Persian/Urdu (ZWNJ
        U+200C) allow a format char.

        Args:
            pack_schema: Validated, merged pack.
            language: Language code. Defaults to ``pack_schema.language``.
                Unknown codes fall back to an empty allowlist (deny all format
                chars).
        """
        lang = (language or pack_schema.language).lower()
        allowed_fmt: frozenset[str] = (
            policy_for(lang).allowed_format_chars if has_policy(lang) else frozenset()
        )

        findings: list[Finding] = []
        for section, key, value in SchemaValidator._iter_translation_items(pack_schema):
            for ch in value:
                if ch in allowed_fmt:
                    continue
                is_forbidden = ch in FORBIDDEN_FORMAT_CHARS
                is_format_cat = unicodedata.category(ch) == "Cf"
                if is_forbidden or is_format_cat:
                    findings.append(
                        Finding(
                            severity="error",
                            code="illegal-format-char",
                            location=f"{section}.{key}",
                            message=(
                                f"Value '{value}' contains illegal format "
                                f"character U+{ord(ch):04X} "
                                f"({unicodedata.name(ch, 'UNNAMED')}). "
                                "Bidi controls, tatweel, BOM, and unlisted "
                                "zero-width joiners are not permitted."
                            ),
                        )
                    )
        return findings

    @staticmethod
    def check_keyword_collisions(
        pack_schema: "LanguagePackSchema",
    ) -> list["Finding"]:
        """Flag values that collide with a *live* Python keyword or builtin.

        A translation must not equal — nor NFKC-fold to — a real Python
        keyword, soft keyword, or builtin name **unless** it is that key's own
        English translation target (e.g. ``in`` legitimately translating the
        ``in`` keyword). This catches two failure modes:

        * **Active-keyword collision**: a translation for one term happens to be
          another live keyword/builtin (e.g. a ``globals`` value rendered as
          ``global``, an ``except*`` value rendered as ``except``, a ``print``
          value rendered as ``in``) — at runtime the dispatch silently
          mis-resolves.
        * **Fullwidth spoof**: ``'ｉｆ'`` is ``str.isidentifier()``-True and
          NFKC-folds to ``if``; the NFKC comparison catches it.

        ``except*``-awareness: the self-exemption is **star-exact** — only
        ``except*`` -> ``except*`` is exempt. ``except*`` -> ``except`` (star
        dropped) is flagged, because the bare ``except`` collides with the live
        keyword. Collision detection itself compares the star-stripped, NFKC-
        folded core against the live-name set.
        """
        import builtins as _builtins

        # ``__builtins__`` is a module in normal execution but a dict under
        # exec/REPL; ``dir(_builtins)`` on the canonical module is reliable.
        live_names = set(keyword.kwlist) | set(keyword.softkwlist) | set(dir(_builtins))

        findings: list[Finding] = []
        for section, key, value in SchemaValidator._iter_translation_items(pack_schema):
            # Self-exemption is exact (star-aware): the value must equal the key
            # verbatim. This keeps `except*` -> `except*` exempt while flagging
            # `except*` -> `except`.
            if value == key:
                continue

            core = SchemaValidator._strip_soft_keyword_marker(value)
            folded = unicodedata.normalize("NFKC", core)

            for candidate in {core, folded}:
                if candidate not in live_names:
                    continue
                findings.append(
                    Finding(
                        severity="error",
                        code="keyword-collision",
                        location=f"{section}.{key}",
                        message=(
                            f"Value '{value}' collides with the live Python "
                            f"name '{candidate}' (NFKC-folded), but this entry "
                            f"translates '{key}'. A translation must not equal "
                            "another keyword/builtin."
                        ),
                    )
                )
                break
        return findings

    # Characters that only became valid in identifiers on newer interpreters.
    # The behavior boundary is CPython version, not a single Unicode version:
    # 3.10/3.11/3.12 ship Unicode 13.0/14.0/15.0 and raise SyntaxError on these,
    # while 3.13+ (Unicode 15.1) accepts them as XID — the exact Sinhala-ZWJ
    # trap. We do a *static* membership test rather than calling ``compile()`` so
    # the check is deterministic regardless of the interpreter running the gate.
    # ZWJ (U+200D) is the load-bearing case; ZWNJ (U+200C) follows the same rule.
    _XID_ONLY_FROM_CPYTHON_313: frozenset[str] = frozenset({"\u200d", "\u200c"})

    @staticmethod
    def check_min_interpreter_identifier(
        pack_schema: "LanguagePackSchema",
        language: str | None = None,
        min_version: str | None = None,
    ) -> list["Finding"]:
        """Flag values that aren't valid identifiers on the pack's *minimum* CPython.

        The Sinhala ZWJ trap: ``virama + ZWJ + consonant`` is a valid identifier
        on CPython 3.13+ (Unicode 13.0 XID update) but a ``SyntaxError`` on
        3.10-3.12. A value that requires a format char allow-listed by the
        language's policy is therefore only safe if the pack declares a minimum
        interpreter of 3.13 or newer.

        This is a **static** XID check (never calls ``compile()``): if a value
        contains any character in
        :data:`SchemaValidator._XID_ONLY_FROM_CPYTHON_313` and the declared minimum
        interpreter is < 3.13, it is flagged. Conservative by design — it errs
        toward warning the maintainer rather than trusting the running
        interpreter's Unicode version.

        Args:
            pack_schema: Validated, merged pack.
            language: Unused today (kept for signature symmetry with the other
                language-scoped checks and future per-language XID rules).
            min_version: Minimum CPython version string (e.g. ``"3.10"``).
                Defaults to ``pack_schema.metadata.python_version_min`` when
                present, else the pack ``version``.
        """
        del language  # reserved for future per-language XID nuance
        declared = min_version
        if declared is None and pack_schema.metadata is not None:
            declared = pack_schema.metadata.python_version_min
        if declared is None:
            declared = pack_schema.version

        supports_unicode13_xid = SchemaValidator._version_at_least(declared, 3, 13)
        if supports_unicode13_xid:
            return []

        findings: list[Finding] = []
        for section, key, value in SchemaValidator._iter_translation_items(pack_schema):
            offending = sorted(
                {ch for ch in value if ch in SchemaValidator._XID_ONLY_FROM_CPYTHON_313}
            )
            if offending:
                pretty = ", ".join(f"U+{ord(ch):04X}" for ch in offending)
                findings.append(
                    Finding(
                        severity="error",
                        code="min-interpreter-xid",
                        location=f"{section}.{key}",
                        message=(
                            f"Value '{value}' uses {pretty}, which only became "
                            f"a valid identifier character in CPython 3.13 "
                            f"(Unicode 13.0 XID). The pack declares minimum "
                            f"interpreter '{declared}'; this raises SyntaxError "
                            "on 3.10-3.12. Raise python_version_min to '3.13'."
                        ),
                    )
                )
        return findings

    @staticmethod
    def _version_at_least(version: str | None, major: int, minor: int) -> bool:
        """Return True if dotted *version* string is >= (major, minor).

        Parses leading ``X.Y`` and ignores any suffix. Unparseable or None
        versions return False (conservative: treat as too old).
        """
        if not version:
            return False
        parts = version.split(".")
        try:
            v_major = int(parts[0])
            v_minor = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError):
            return False
        return (v_major, v_minor) >= (major, minor)

    @staticmethod
    def _strict_duplicate_findings(
        pack_schema: "LanguagePackSchema",
        *,
        include_cross_section: bool = True,
    ) -> list["Finding"]:
        """Wrap ``check_duplicates`` output as Findings, allow-listing type==type.

        Intra-section duplicates and cross-section collisions both become
        ``duplicate-target`` findings. The intentional ``keywords.type ==
        builtins.type`` overlap is suppressed: it is the one duplicate the
        language packs ship on purpose.

        Intra-section duplicates always run: in-partition reversibility (Rule 2)
        applies to *every* target, including JavaScript ``members``. The
        ``include_cross_section`` toggle governs only the cross-partition
        collision pass, which is Python-specific: CPython's ``tokenize``
        dispatches tokens flat, so a value shared across partitions round-trips
        to the wrong token (CORE-710). JavaScript's acorn AST is category-aware,
        so cross-partition homonyms (e.g. a member and a builtin) are legal;
        callers auditing a non-Python target pass ``include_cross_section=False``
        (CORE-1372). The toggle is target-neutral by design — the target→toggle
        decision lives in the caller, never as an ``if target ==`` branch here.
        """
        dup = SchemaValidator.check_duplicates(pack_schema)
        findings: list[Finding] = []

        section_map = {
            "keyword_duplicates": "keywords",
            "builtin_duplicates": "builtins",
            "exception_duplicates": "exceptions",
            "reserved_word_duplicates": "reserved_words",
            "operator_duplicates": "operators",
            "stdlib_duplicates": "standard_library",
        }
        for dup_key, section in section_map.items():
            for entry in dup.get(dup_key, []):
                terms = entry["source_terms"]
                if set(terms) <= _ALLOWED_DUPLICATE_KEYS:
                    continue
                findings.append(
                    Finding(
                        severity="error",
                        code="duplicate-target",
                        location=f"{section}.{'/'.join(terms)}",
                        message=(
                            f"Translation '{entry['translation']}' is reused "
                            f"for {len(terms)} terms in {section}: "
                            f"{', '.join(terms)}."
                        ),
                    )
                )

        for collision in (
            dup.get("cross_section_collisions", []) if include_cross_section else []
        ):
            keys = {loc["source_key"] for loc in collision.get("locations", [])}
            if keys <= _ALLOWED_DUPLICATE_KEYS:
                continue
            locations = ", ".join(
                f"{loc['section']}.{loc['source_key']}"
                for loc in collision.get("locations", [])
            )
            findings.append(
                Finding(
                    severity="error",
                    code="duplicate-target",
                    location=locations,
                    message=(
                        f"Translation '{collision['translation']}' appears in "
                        f"multiple sections ({locations}); each target must be "
                        "unique across the resolved pack."
                    ),
                )
            )
        return findings

    @staticmethod
    def _strict_identifier_findings(
        pack_schema: "LanguagePackSchema",
    ) -> list["Finding"]:
        """Wrap the legacy ``check_identifier_validity`` output as Findings."""
        result = SchemaValidator.check_identifier_validity(pack_schema)
        findings: list[Finding] = []
        for section, dict_key in (
            ("keywords", "invalid_keywords"),
            ("builtins", "invalid_builtins"),
            ("exceptions", "invalid_exceptions"),
            ("reserved_words", "invalid_reserved_words"),
        ):
            for entry in result.get(dict_key, []):
                findings.append(
                    Finding(
                        severity="error",
                        code="invalid-identifier",
                        location=f"{section}.{entry['key']}",
                        message=(
                            f"Value '{entry['value']}' {entry['reason']}; not a "
                            "valid Python identifier."
                        ),
                    )
                )
        return findings

    @staticmethod
    def _strip_soft_keyword_marker(value: str) -> str:
        """Drop the trailing ``*`` that marks a soft-keyword translation.

        Soft keywords (``match``, ``case``, ``type``, ``_``) carry a trailing
        ``*`` in pack values to flag that they are contextual keywords. The
        marker is not part of the identifier, so it must be removed before a
        value is normalized, script-checked, collision-checked, or measured.
        """
        return value[:-1] if value.endswith("*") else value

    @staticmethod
    def check_ascii_digits(pack_schema: "LanguagePackSchema") -> list["Finding"]:
        """Flag identifiers that contain non-ASCII decimal digits.

        Style guides require ASCII digits 0-9 in identifiers: native digit
        systems (Arabic-Indic ٠-٩, Devanagari १-९, Thai ๑-๙, …) are
        identifier-legal but mixing digit systems in one file is a UTS #39
        confusable hazard and complicates bidi runs. Emitted as a warning (the
        ASCII-digit policy is advisory). The trailing ``*`` of a soft-keyword
        translation is stripped before scanning, matching the other checks.
        """
        findings: list[Finding] = []
        for section, key, value in SchemaValidator._iter_translation_items(pack_schema):
            core = SchemaValidator._strip_soft_keyword_marker(value)
            bad = sorted(
                {
                    c
                    for c in core
                    if unicodedata.category(c) == "Nd" and not ("0" <= c <= "9")
                }
            )
            if bad:
                cps = ", ".join(f"U+{ord(c):04X}" for c in bad)
                findings.append(
                    Finding(
                        severity="warning",
                        code="non-ascii-digit",
                        location=f"{section}.{key}",
                        message=(
                            f"Value '{core}' uses non-ASCII digit(s) ({cps}); "
                            "identifiers must use ASCII digits 0-9."
                        ),
                    )
                )
        return findings

    @staticmethod
    def check_term_length(pack_schema: "LanguagePackSchema") -> list["Finding"]:
        """Flag sentence-length values — a description used where a term belongs.

        Length is measured in CODE POINTS on the soft-keyword-stripped core, so a
        short multi-byte native word (e.g. a 10-character Thai term whose UTF-8
        length exceeds the threshold) is not penalised. Emitted as a WARNING: a
        long identifier is valid Python, so this is a quality signal for native
        review, not a safety failure. See :data:`MAX_TERM_LENGTH`.
        """
        findings: list[Finding] = []
        for section, key, value in SchemaValidator._iter_translation_items(pack_schema):
            core = SchemaValidator._strip_soft_keyword_marker(value)
            if len(core) >= MAX_TERM_LENGTH:
                findings.append(
                    Finding(
                        severity="warning",
                        code="descriptions-as-terms",
                        location=f"{section}.{key}",
                        message=(
                            f"Value '{value}' is {len(core)} code points — a "
                            f"sentence, not a term (limit {MAX_TERM_LENGTH}). A "
                            "translation should be a short native word; this "
                            "looks like a definition and needs retranslation."
                        ),
                    )
                )
        return findings

    @staticmethod
    def validate_pack_strict(
        pack_schema: "LanguagePackSchema",
        language: str | None = None,
        *,
        run_min_interpreter: bool = True,
        run_cross_section: bool = True,
    ) -> list["Finding"]:
        """Run every safety check and return all Findings (empty == clean).

        The gate is safety/correctness-first: every ``error`` flags something
        that breaks code or is a Unicode/confusable hazard. A small set of
        advisory ``warning`` checks (non-ASCII digits, description-length) ride
        along so the audit can surface them for native review — ``audit_packs``
        fails CI on errors only, never on these warnings. Stylistic preferences
        beyond them (naming, phrasing) stay guidance for the translation prompt
        (PromptBuilder, CORE-1395), so this takes no style guide. Aggregates,
        in order:

        1. :meth:`check_normalization`
        2. :meth:`check_script_consistency`
        3. :meth:`check_format_chars`
        4. :meth:`check_keyword_collisions`
        5. :meth:`check_min_interpreter_identifier`
        6. the previously-dead :meth:`check_duplicates`
           (via :meth:`_strict_duplicate_findings`, type==type allow-listed)
        7. the previously-dead :meth:`check_identifier_validity`
           (via :meth:`_strict_identifier_findings`)
        8. :meth:`check_ascii_digits` — the ASCII-digit policy (warning)
        9. :meth:`check_term_length` — description-as-term length (warning)

        Two of the aggregated checks are Python-specific and are gated by the
        ``run_min_interpreter`` / ``run_cross_section`` toggles (CORE-1372):

        * ``check_min_interpreter_identifier`` guards the CPython 3.13 XID trap —
          meaningless for a non-CPython runtime.
        * the cross-section collision pass inside ``_strict_duplicate_findings``
          guards CPython's flat ``tokenize`` dispatch; JavaScript's acorn AST is
          category-aware, so cross-partition homonyms are legal there (D4).

        Both default to ``True`` (today's Python behaviour). Callers auditing a
        non-Python target pass ``False``. The toggles are booleans, not a target
        string: the target→toggle mapping stays in the caller so the engine never
        forks on ``if target == "python"`` (CORE-1503's "per-target data, not
        per-target code paths" rule). The remaining Python-isms — the keyword
        set in :meth:`check_keyword_collisions` and the ``str.isidentifier``
        grammar in :meth:`check_identifier_validity` — are the per-target
        identifier/keyword profile owned by CORE-1503, not gated here.

        Args:
            pack_schema: Validated, inheritance-merged pack.
            language: Language code to police against. Defaults to
                ``pack_schema.language``.
            run_min_interpreter: Run the CPython-XID min-interpreter check.
                Set ``False`` for non-CPython targets.
            run_cross_section: Run the cross-partition collision pass. Set
                ``False`` for targets whose runtime dispatches by AST category
                (e.g. JavaScript) rather than a flat token stream.

        Returns:
            A flat ``list[Finding]`` mixing errors and advisory warnings. No
            ``severity == "error"`` finding means the pack passes the blocking
            gate; an entirely empty list means it is clean of warnings too.
        """
        lang = language or pack_schema.language
        findings: list[Finding] = []
        findings += SchemaValidator.check_normalization(pack_schema)
        findings += SchemaValidator.check_script_consistency(pack_schema, lang)
        findings += SchemaValidator.check_format_chars(pack_schema, lang)
        findings += SchemaValidator.check_keyword_collisions(pack_schema)
        if run_min_interpreter:
            findings += SchemaValidator.check_min_interpreter_identifier(
                pack_schema, lang
            )
        findings += SchemaValidator._strict_duplicate_findings(
            pack_schema, include_cross_section=run_cross_section
        )
        findings += SchemaValidator._strict_identifier_findings(pack_schema)
        findings += SchemaValidator.check_ascii_digits(pack_schema)
        findings += SchemaValidator.check_term_length(pack_schema)
        return findings
