"""Typed input/output shapes for the five MCP tools.

Outputs are Pydantic models so the MCP SDK publishes an output schema for
every tool and returns structured content alongside the text rendering.
Shapes follow the MCP architecture design (CORE-1165 §2): translation
results are the ``TranslateResponse`` shape; ``explain_in_language``
returns deterministic engine facts (constructs + validation), never prose.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)

from .versions import DEFAULT_PYTHON_VERSION, SUPPORTED_PYTHON_VERSIONS

#: Python grammar versions with language-pack coverage — the enum published
#: in every tool schema. Built from the pack version index at import
#: (see ``versions.py``) so shipping packs for a new Python version needs no
#: edit here. Static checkers see ``str``: the members are only knowable at
#: runtime, and the engine validates the value against the packs anyway.
if TYPE_CHECKING:
    PythonVersion = str
else:
    PythonVersion = Literal[SUPPORTED_PYTHON_VERSIONS]

__all__ = [
    "DEFAULT_PYTHON_VERSION",
    "SUPPORTED_PYTHON_VERSIONS",
    "PythonVersion",
    "LANG_CODE_MAX_LENGTH",
    "SOURCE_MAX_CHARS",
    "SNIPPET_MAX_CHARS",
    "CodebaseMapResult",
    "CodebaseMapSummary",
    "ConstructMapping",
    "DivergenceModel",
    "ExplainMaterial",
    "FileMapEntry",
    "IdentifierConflict",
    "IdentifierProposal",
    "IdentifierValidationResult",
    "IdentifierVerdict",
    "KeywordMappings",
    "LookupResult",
    "RoundTripInfo",
    "SourceFile",
    "SyntaxIssueModel",
    "ToolResult",
    "TranslatedFile",
    "TranslationResult",
    "ValidationInfo",
]

#: Static backstop on source-field length (characters). This is an input
#: sanity bound for the parser — the same static backstop the open REST
#: schemas use — NOT a usage ceiling; the local server meters nothing.
SOURCE_MAX_CHARS = 2_000_000

#: Length bound for language-code fields (registry pattern is the gate).
LANG_CODE_MAX_LENGTH = 16

#: Bound on divergence snippet fields (characters). A physical line is
#: unbounded below SOURCE_MAX_CHARS — 2 MB legally fits on one line — so
#: unbounded snippets would put copies of the file on the wire through the
#: field that exists to avoid exactly that.
SNIPPET_MAX_CHARS = 200

#: Length bound for identifier fields. Generous next to any real name —
#: a sanity bound on input, not a naming rule.
IDENTIFIER_MAX_LENGTH = 512


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
    round_trip: RoundTripInfo | None = Field(
        default=None,
        description=(
            "Round-trip verification result. Present only when the tool was "
            "called with verify_round_trip: true; absent otherwise."
        ),
    )

    @model_serializer(mode="wrap")
    def _omit_unrequested_round_trip(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        """Serialize with ``round_trip`` ABSENT — not null — when the flag
        was off: a null field is still tokens in every response."""
        # The wrap handler is typed as returning Any; for a model this is
        # the serialized mapping, and the isinstance guard keeps the cast
        # honest for exotic serialization contexts.
        data = cast("dict[str, Any]", handler(self))
        if isinstance(data, dict) and data.get("round_trip") is None:
            data.pop("round_trip", None)
        return data


class DivergenceModel(ToolResult):
    """One located difference (1-based line/column). Text fields are
    truncated to SNIPPET_MAX_CHARS: a physical line is unbounded below
    SOURCE_MAX_CHARS, and unbounded lines put copies of the file on the
    wire through the field that exists to avoid exactly that."""

    line: int
    offset: int | None = None
    expected: str = Field(max_length=SNIPPET_MAX_CHARS)
    actual: str = Field(max_length=SNIPPET_MAX_CHARS)
    truncated: bool = False
    kind: str
    layer: str | None = Field(
        default=None,
        description=(
            "keywords | builtins | exceptions | implicit_params | collision | "
            "identifiers | comments | strings. Routes the fix: pack layers are "
            "engine/pack defects, collision is a known identifier class "
            "(CORE-1840), identifiers are expected residue, comments/strings "
            "are the writer's own drift."
        ),
    )


class RoundTripInfo(ToolResult):
    """Result of verifying that translating back reproduces the input."""

    round_trips: bool
    forward_valid: bool | None = Field(
        description=(
            "Whether the canonical form compiles. A round trip can be "
            "byte-identical over an invalid canonical form when a collision "
            "cancels itself; this field carries that fact."
        )
    )
    verdict_line: str = Field(
        description=(
            "Single-line verdict stating its own limits; contains no source "
            "content. Quote it rather than restating the verdict in your own "
            "words."
        )
    )
    divergence_count: int
    divergences: list[DivergenceModel]
    verified: list[str] = Field(
        description=(
            "Layers this run actually exercised AND found clean. A clean "
            "result says nothing about layers absent from this list."
        )
    )
    grammar_version: str
    pivoted: bool
    schema_version: str


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
    category: str = Field(description="keywords | builtins | exceptions | implicit_params")


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
    implicit_params: dict[str, str] = Field(default_factory=dict)


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


class IdentifierProposal(BaseModel):
    """One proposed identifier translation, awaiting validation."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(
        min_length=1,
        max_length=IDENTIFIER_MAX_LENGTH,
        description="The canonical (source-language) identifier, e.g. 'calculate_tax'.",
    )
    translation: str = Field(
        min_length=1,
        max_length=IDENTIFIER_MAX_LENGTH,
        description="The proposed rendering in the target language.",
    )


class IdentifierConflict(ToolResult):
    """One reason a proposal is not safe to record."""

    kind: Literal["malformed", "unsafe_text", "reserved_term", "drift", "collision"] = Field(
        description=(
            "malformed — not a valid Python identifier; "
            "unsafe_text — violates the Unicode contract (bidi controls, "
            "invisibles); "
            "reserved_term — the translation is a name the pack has claimed; "
            "drift — this source already has a different translation "
            "(one concept, two terms); "
            "collision — this translation already belongs to a different "
            "source (two concepts, one term)."
        )
    )
    against: Literal["python", "unicode_contract", "pack", "glossary", "batch"] = Field(
        description="What the translation was checked against."
    )
    detail: str = Field(
        description=(
            "For reserved_term, the pack entry taken, e.g. 'keyword:def'. "
            "For malformed/unsafe_text, why it was rejected. Otherwise the "
            "other side of the conflict — the competing translation (drift) "
            "or the competing source identifier (collision)."
        )
    )


class IdentifierVerdict(ToolResult):
    """The verdict for one proposal."""

    source: str
    translation: str = Field(
        description=(
            "The rendering to record — NFC-normalized, and settled to the "
            "glossary's existing spelling when the proposal was a variant of "
            "it. Use this value, not the one you proposed."
        )
    )
    proposed: str | None = Field(
        default=None,
        description=(
            "Set only when `translation` differs from what was proposed — "
            "echoes the original so the substitution is visible rather than "
            "silent. Write `translation` to the glossary and use it in code."
        ),
    )
    ok: bool = Field(description="True when no conflicts were found — safe to record.")
    conflicts: list[IdentifierConflict] = Field(default_factory=list)


class IdentifierValidationResult(ToolResult):
    """Per-proposal verdicts plus the glossary entries that are safe to record."""

    target_lang: str
    python_version: PythonVersion
    results: list[IdentifierVerdict]
    accepted: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "The conflict-free proposals as a source -> translation mapping, "
            "ready to merge into the project glossary. The caller persists it; "
            "this server writes nothing. Both sides are NFC-normalized per the "
            "storage contract — so if your glossary holds a source key in a "
            "different normal form, merge on the normalized key rather than "
            "adding this one alongside it."
        ),
    )


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
