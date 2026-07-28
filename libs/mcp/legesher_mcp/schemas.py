"""Typed input/output shapes for the five MCP tools.

Outputs are Pydantic models so the MCP SDK publishes an output schema for
every tool and returns structured content alongside the text rendering.
Shapes follow the MCP architecture design (CORE-1165 §2): translation
results are the ``TranslateResponse`` shape; ``explain_in_language``
returns deterministic engine facts (constructs + validation), never prose.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

#: Python grammar versions with language-pack coverage.
PythonVersion = Literal["3.10", "3.11", "3.12", "3.13", "3.14"]

DEFAULT_PYTHON_VERSION: PythonVersion = "3.13"

#: Static backstop on source-field length (characters). This is an input
#: sanity bound for the parser — the same static backstop the open REST
#: schemas use — NOT a usage ceiling; the local server meters nothing.
SOURCE_MAX_CHARS = 2_000_000

#: Length bound for language-code fields (registry pattern is the gate).
LANG_CODE_MAX_LENGTH = 16


class ToolResult(BaseModel):
    """Base class for tool outputs (unknown fields rejected)."""

    model_config = ConfigDict(extra="forbid")


class TranslationResult(ToolResult):
    """Translated source plus the parameters that produced it."""

    translated_source: str
    source_lang: str
    target_lang: str
    python_version: PythonVersion
    pivoted: bool = Field(
        description=(
            "True when translated via the English pivot (X→en→Y): the "
            "engine has no direct X→Y path, so both hops rode language "
            "packs and round-trip fidelity depends on both."
        )
    )


class SyntaxIssueModel(ToolResult):
    """Location and message of a syntax problem (1-based line/column)."""

    message: str
    line: int | None = None
    offset: int | None = None


class ValidationInfo(ToolResult):
    """Static (compile-only) validation result. Code is never executed."""

    valid: bool
    issue: SyntaxIssueModel | None = None


class ConstructMapping(ToolResult):
    """One construct present in the code, mapped across both languages."""

    #: Python name differs from the wire name ("construct") only because
    #: the wire name shadows pydantic's deprecated ``BaseModel.construct``.
    english_term: str = Field(alias="construct", description="Canonical English term.")
    in_code_lang: str = Field(description="How the construct is spelled in the code's language.")
    in_explain_lang: str = Field(
        description=(
            "How the construct is spelled in the explanation language "
            "(falls back to the English spelling when the pack has no "
            "entry — untranslated constructs render in English)."
        )
    )
    category: str = Field(description="keywords | builtins | exceptions | reserved_words")


class ExplainMaterial(ToolResult):
    """Engine facts for explaining code — the calling model writes the prose."""

    code_lang: str
    explain_in: str
    python_version: PythonVersion
    constructs: list[ConstructMapping]
    validation: ValidationInfo
    translated_source: str | None = Field(
        default=None,
        description="The code translated into explain_in, when requested.",
    )


class KeywordMappings(ToolResult):
    """English → translated mappings, keyed by category."""

    keywords: dict[str, str] = Field(default_factory=dict)
    builtins: dict[str, str] = Field(default_factory=dict)
    exceptions: dict[str, str] = Field(default_factory=dict)
    reserved_words: dict[str, str] = Field(default_factory=dict)


class LookupResult(ToolResult):
    """Keyword-mapping lookup for one language."""

    language: str
    python_version: PythonVersion
    mappings: KeywordMappings
    unmatched_terms: list[str] = Field(
        default_factory=list,
        description="Requested terms with no entry in any category.",
    )


class FileMapEntry(ToolResult):
    """Per-file report row for map_existing_codebase."""

    path: str = Field(description="Caller-supplied label, echoed back verbatim (never logged).")
    translatable: bool
    construct_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Construct occurrences per category in this file.",
    )
    unmapped_constructs: list[str] = Field(
        default_factory=list,
        description=(
            "English constructs present in the file with no entry in the "
            "target language's pack (they stay English after translation)."
        ),
    )
    issue: str | None = Field(
        default=None, description="Why the file could not be mapped, if it couldn't."
    )


class TranslatedFile(ToolResult):
    """One translated file, when include_translations was requested."""

    path: str
    translated_source: str


class CodebaseMapSummary(ToolResult):
    """Aggregate coverage over the mapped batch."""

    files_total: int
    files_translatable: int
    constructs_found: int = Field(description="Unique constructs seen across the batch.")
    constructs_mapped: int = Field(
        description="Of those, how many the target pack has entries for."
    )
    coverage_ratio: float | None = Field(
        description=("constructs_mapped / constructs_found; null when no constructs were found.")
    )
    unmapped_constructs: list[str] = Field(
        default_factory=list,
        description="Unique English constructs without target-pack entries.",
    )
    pivoted: bool = Field(description="True when mapping went through the English pivot.")


class CodebaseMapResult(ToolResult):
    """Legibility report: what translating this codebase would look like."""

    source_lang: str
    target_lang: str
    python_version: PythonVersion
    files: list[FileMapEntry]
    summary: CodebaseMapSummary
    translated_files: list[TranslatedFile] | None = None


class SourceFile(BaseModel):
    """One input file for map_existing_codebase."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        min_length=1,
        max_length=1024,
        description=(
            "Report label only — treated as content: echoed back to the "
            "caller, never logged, never used to touch the filesystem."
        ),
    )
    source: str = Field(
        min_length=1,
        max_length=SOURCE_MAX_CHARS,
        description="The file's Python source text.",
    )
