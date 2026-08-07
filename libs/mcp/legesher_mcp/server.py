"""The Legesher MCP server: five coarse tools, resources, and prompts.

Design (CORE-1165 architecture doc, §2/§5):

- Five task-shaped tools instead of an endpoint mirror; catalog and
  dictionary reads are resources, not tools.
- ``explain_in_language`` returns deterministic engine facts — the calling
  model composes the prose.
- ``translate_to_source`` is fixed to the English pivot; a general X→Y is
  ``translate_to_native`` with an explicit ``source_lang``.
- ``map_existing_codebase`` v1 is an orchestration over per-file
  translate + validate.
- Tool errors carry a machine code and a generic message: no stack traces,
  no filesystem paths, no echoed source.

The stdio server is local-only: no network calls, no accounts, no
telemetry of any kind.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Annotated, Literal, cast

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from . import __version__
from .engine import (
    CATEGORIES,
    LANG_CODE_PATTERN,
    PIVOT_LANGUAGE,
    EngineError,
    get_engine,
)
from .schemas import (
    DEFAULT_PYTHON_VERSION,
    LANG_CODE_MAX_LENGTH,
    SOURCE_MAX_CHARS,
    CodebaseMapResult,
    CodebaseMapSummary,
    ConstructMapping,
    ExplainMaterial,
    FileMapEntry,
    KeywordMappings,
    LookupResult,
    PythonVersion,
    SourceFile,
    SyntaxIssueModel,
    TranslatedFile,
    TranslationResult,
    ValidationInfo,
)

_INSTRUCTIONS = """\
Legesher translates Python between natural languages via reviewed language
packs. Use translate_to_native to make code readable in a language,
translate_to_source to get the English-keyword form toolchains understand,
explain_in_language for the engine facts behind an explanation (you write
the prose), lookup_keyword_mapping for quick term lookups, and
map_existing_codebase for a repo-level legibility report. The language
catalog is the legesher://languages resource; full dictionaries are
legesher://languages/{lang}/terms. X→Y translation pivots through English
(results say so via `pivoted`). Everything runs locally: no network, no
telemetry."""

_LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _log_level_from_env() -> _LogLevel:
    """Log level from LEGESHER_MCP_LOG_LEVEL; quiet (WARNING) by default.

    An unset or unrecognized value must never stop the server from
    booting, so anything invalid falls back to the default.
    """
    raw = os.environ.get("LEGESHER_MCP_LOG_LEVEL", "").strip().upper()
    if raw in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        return cast(_LogLevel, raw)
    return "WARNING"


mcp = FastMCP("legesher", instructions=_INSTRUCTIONS, log_level=_log_level_from_env())
# The SDK's FastMCP (1.28) has no version passthrough, and the low-level
# server otherwise reports the SDK's own package version in initialize.
mcp._mcp_server.version = __version__

# Reusable parameter annotations -----------------------------------------

_SourceParam = Annotated[
    str,
    Field(
        min_length=1,
        max_length=SOURCE_MAX_CHARS,
        description="Python source text (a complete file or a fragment).",
    ),
]
_LangParam = Annotated[
    str,
    Field(
        pattern=LANG_CODE_PATTERN,
        min_length=2,
        max_length=LANG_CODE_MAX_LENGTH,
        description="ISO 639 language code from the legesher://languages catalog.",
    ),
]


def _tool_error(exc: EngineError) -> ToolError:
    """Convert an engine failure into a machine-coded MCP tool error."""
    return ToolError(f"{exc.code}: {exc}")


# -- tools ----------------------------------------------------------------


@mcp.tool()
def translate_to_native(
    source: _SourceParam,
    target_lang: _LangParam,
    source_lang: _LangParam = PIVOT_LANGUAGE,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
) -> TranslationResult:
    """Translate Python source code into the caller's natural language.

    Accepts complete files and fragments alike — there is no separate
    snippet mode to choose. When neither language is English the engine
    pivots through English (packs are authored against English) and the
    result reports `pivoted: true`. Formatting, comments, identifiers, and
    string contents are preserved; only keywords, builtins, exceptions,
    and reserved words are translated.
    """
    try:
        outcome = get_engine().translate(
            source=source,
            source_lang=source_lang,
            target_lang=target_lang,
            python_version=python_version,
        )
    except EngineError as exc:
        raise _tool_error(exc) from exc
    return TranslationResult(
        translated_source=outcome.translated_source,
        source_lang=source_lang,
        target_lang=target_lang,
        python_version=python_version,
        pivoted=outcome.pivoted,
    )


@mcp.tool()
def translate_to_source(
    source: _SourceParam,
    source_lang: _LangParam,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
) -> TranslationResult:
    """Translate native-language code back to English-keyword Python.

    The inverse of translate_to_native and the round-trip half of the
    collaboration story: the output is the form the interpreter, the
    toolchain, and upstream collaborators use. The target is fixed to
    English — for a general X→Y translation call translate_to_native with
    an explicit source_lang.
    """
    try:
        outcome = get_engine().translate(
            source=source,
            source_lang=source_lang,
            target_lang=PIVOT_LANGUAGE,
            python_version=python_version,
        )
    except EngineError as exc:
        raise _tool_error(exc) from exc
    return TranslationResult(
        translated_source=outcome.translated_source,
        source_lang=source_lang,
        target_lang=PIVOT_LANGUAGE,
        python_version=python_version,
        pivoted=outcome.pivoted,
    )


@mcp.tool()
def explain_in_language(
    source: _SourceParam,
    explain_in: _LangParam,
    code_lang: _LangParam = PIVOT_LANGUAGE,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
    include_translation: Annotated[
        bool,
        Field(description="Also return the source translated into explain_in."),
    ] = False,
) -> ExplainMaterial:
    """Return the engine facts needed to explain code in a language.

    Deterministic material only — construct-by-construct keyword mappings
    for the constructs actually present in the code, and a static
    (compile-only, never executed) validation result. YOU compose the
    explanation from these facts; the tool never generates prose, so
    engine truth stays distinct from narration.
    """
    engine = get_engine()
    try:
        explain_maps = engine.pack_categories(engine.load_pack(explain_in, python_version))
        code_maps = (
            engine.pack_categories(engine.load_pack(code_lang, python_version))
            if code_lang != PIVOT_LANGUAGE
            else None
        )

        tokenizable = True
        if code_lang == PIVOT_LANGUAGE:
            english = source
        else:
            try:
                english = engine.translate(
                    source=source,
                    source_lang=code_lang,
                    target_lang=PIVOT_LANGUAGE,
                    python_version=python_version,
                ).translated_source
            except EngineError as exc:
                if exc.code != "invalid_source":
                    raise
                tokenizable = False

        if not tokenizable:
            # A tokenization failure is a validation RESULT, not an error.
            return ExplainMaterial(
                code_lang=code_lang,
                explain_in=explain_in,
                python_version=python_version,
                constructs=[],
                validation=ValidationInfo(
                    valid=False,
                    issue=SyntaxIssueModel(message="Source could not be tokenized as Python code."),
                ),
            )

        validation = engine.compile_check(english)
        scan = engine.scan_constructs(english, python_version)

        constructs: list[ConstructMapping] = []
        for category, term in scan.ordered:
            code_map = code_maps[category] if code_maps else {}
            constructs.append(
                ConstructMapping(
                    construct=term,
                    in_code_lang=code_map.get(term, term),
                    in_explain_lang=explain_maps[category].get(term, term),
                    category=category,
                )
            )

        translated_source: str | None = None
        if include_translation:
            translated_source = engine.translate(
                source=source,
                source_lang=code_lang,
                target_lang=explain_in,
                python_version=python_version,
            ).translated_source
    except EngineError as exc:
        raise _tool_error(exc) from exc

    return ExplainMaterial(
        code_lang=code_lang,
        explain_in=explain_in,
        python_version=python_version,
        constructs=constructs,
        validation=ValidationInfo(
            valid=validation.valid,
            issue=(
                SyntaxIssueModel(
                    message=validation.issue.message,
                    line=validation.issue.line,
                    offset=validation.issue.offset,
                )
                if validation.issue
                else None
            ),
        ),
        translated_source=translated_source,
    )


@mcp.tool()
def lookup_keyword_mapping(
    language: _LangParam,
    terms: Annotated[
        list[str] | None,
        Field(
            description=(
                "English terms to look up (e.g. ['def', 'print']). Omit for the full mapping."
            ),
        ),
    ] = None,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
) -> LookupResult:
    """Look up how specific terms render in a language.

    The quick-reference tool: pass English terms for a filtered answer, or
    omit them for the language's full mapping. For browsing the whole
    dictionary prefer the legesher://languages/{lang}/terms resource.
    """
    engine = get_engine()
    try:
        category_maps = engine.pack_categories(engine.load_pack(language, python_version))
    except EngineError as exc:
        raise _tool_error(exc) from exc
    if terms is None:
        mappings = KeywordMappings(**category_maps)
        unmatched: list[str] = []
    else:
        filtered: dict[str, dict[str, str]] = {c: {} for c in CATEGORIES}
        unmatched = []
        for term in terms:
            for category in CATEGORIES:
                translation = category_maps[category].get(term)
                if translation is not None:
                    filtered[category][term] = translation
                    break
            else:
                unmatched.append(term)
        mappings = KeywordMappings(**filtered)

    return LookupResult(
        language=language,
        python_version=python_version,
        mappings=mappings,
        unmatched_terms=unmatched,
    )


@mcp.tool()
def map_existing_codebase(
    files: Annotated[
        list[SourceFile],
        Field(
            min_length=1,
            description=(
                "Files to map. Paths are report labels only — they are "
                "content, never logged, never used to touch the filesystem."
            ),
        ),
    ],
    target_lang: _LangParam,
    source_lang: _LangParam = PIVOT_LANGUAGE,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
    include_translations: Annotated[
        bool,
        Field(description="Also return the translated files (default: report only)."),
    ] = False,
) -> CodebaseMapResult:
    """Report what translating a codebase into a language would look like.

    The legibility report: per-file translatability, construct counts,
    constructs the target language's pack cannot map yet (they stay
    English after translation), and an aggregate coverage summary.
    Orchestrates per-file translate + validate; for a large repo, iterate
    in batches of files across calls.
    """
    engine = get_engine()
    try:
        target_maps = engine.pack_categories(engine.load_pack(target_lang, python_version))
        if source_lang != PIVOT_LANGUAGE:
            engine.load_pack(source_lang, python_version)  # fail fast, sanitized
    except EngineError as exc:
        raise _tool_error(exc) from exc

    entries: list[FileMapEntry] = []
    translated_files: list[TranslatedFile] = []
    unique_constructs: set[tuple[str, str]] = set()
    unmapped_unique: set[str] = set()
    files_translatable = 0
    pivoted = PIVOT_LANGUAGE not in (source_lang, target_lang) and (source_lang != target_lang)

    for entry in files:
        try:
            if source_lang == PIVOT_LANGUAGE:
                english = entry.source
            else:
                english = engine.translate(
                    source=entry.source,
                    source_lang=source_lang,
                    target_lang=PIVOT_LANGUAGE,
                    python_version=python_version,
                ).translated_source
            scan = engine.scan_constructs(english, python_version)
            if not scan.tokenized:
                raise EngineError("invalid_source", "Source could not be tokenized as Python code.")
        except EngineError as exc:
            if exc.code != "invalid_source":
                raise _tool_error(exc) from exc
            entries.append(
                FileMapEntry(
                    path=entry.path,
                    translatable=False,
                    issue=str(exc),
                )
            )
            continue

        unmapped: list[str] = []
        for category, term in scan.ordered:
            unique_constructs.add((category, term))
            if term not in target_maps[category]:
                unmapped.append(term)
                unmapped_unique.add(term)

        validation = engine.compile_check(english)
        issue: str | None = None
        if not validation.valid and validation.issue is not None:
            location = (
                f" (line {validation.issue.line})" if validation.issue.line is not None else ""
            )
            issue = f"syntax: {validation.issue.message}{location}"

        files_translatable += 1
        entries.append(
            FileMapEntry(
                path=entry.path,
                translatable=True,
                construct_counts=scan.counts,
                unmapped_constructs=unmapped,
                issue=issue,
            )
        )

        if include_translations:
            try:
                translated = engine.translate(
                    source=entry.source,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    python_version=python_version,
                ).translated_source
            except EngineError as exc:
                raise _tool_error(exc) from exc
            translated_files.append(TranslatedFile(path=entry.path, translated_source=translated))

    constructs_found = len(unique_constructs)
    constructs_mapped = constructs_found - len(
        {
            (category, term)
            for category, term in unique_constructs
            if term not in target_maps[category]
        }
    )
    return CodebaseMapResult(
        source_lang=source_lang,
        target_lang=target_lang,
        python_version=python_version,
        files=entries,
        summary=CodebaseMapSummary(
            files_total=len(files),
            files_translatable=files_translatable,
            constructs_found=constructs_found,
            constructs_mapped=constructs_mapped,
            coverage_ratio=(constructs_mapped / constructs_found if constructs_found else None),
            unmapped_constructs=sorted(unmapped_unique),
            pivoted=pivoted,
        ),
        translated_files=translated_files if include_translations else None,
    )


# -- resources ------------------------------------------------------------


@mcp.resource("legesher://languages", mime_type="application/json")
def languages_catalog() -> str:
    """The language catalog: code, names, direction, status, pack availability."""
    return json.dumps(
        [asdict(info) for info in get_engine().list_languages()],
        ensure_ascii=False,
        indent=2,
    )


@mcp.resource("legesher://languages/{lang}/terms", mime_type="application/json")
def language_terms(lang: str) -> str:
    """Full term dictionary for one language (default Python version)."""
    engine = get_engine()
    try:
        pack = engine.load_pack(lang, DEFAULT_PYTHON_VERSION)
    except EngineError as exc:
        # Sanitized upstream; safe to surface as the resource error.
        raise ValueError(f"{exc.code}: {exc}") from exc
    return json.dumps(
        {
            "language": lang,
            "python_version": str(pack.version),
            **engine.pack_categories(pack),
        },
        ensure_ascii=False,
        indent=2,
    )


# -- prompts --------------------------------------------------------------


@mcp.prompt(name="explain-in", title="Explain code in a language")
def explain_in_prompt(language: str) -> str:
    """Scaffold "explain the selected code in {language}"."""
    return f"""\
Explain the selected code in {language}.

1. Call the explain_in_language tool with the code and \
explain_in="{language}" (set code_lang if the code is not written in \
English-keyword Python). The tool returns engine facts: the constructs \
present with their names in both languages, and a static validation result.
2. Write the explanation yourself, in {language}, walking the code \
construct by construct. Use the tool's mappings for every keyword, \
builtin, and exception you name — do not invent translations.
3. Keep engine facts distinct from your narration: the mappings and the \
validation verdict come from the engine; everything else is your reading \
of the code. If validation reported an issue, mention it plainly with its \
line number."""


@mcp.prompt(name="translate-review", title="Translate and review a source pair")
def translate_review_prompt(target_lang: str) -> str:
    """Walk a source/translated pair: translate, validate, summarize."""
    return f"""\
Translate the provided code into {target_lang} and review the result.

1. Call translate_to_native with target_lang="{target_lang}" (set \
source_lang if the code is not English-keyword Python). Note whether the \
result says pivoted: true — pivoted translations went through English and \
round-trip fidelity depends on both hops.
2. Call explain_in_language on the ORIGINAL code with \
explain_in="{target_lang}" to get the construct mappings and the \
validation verdict.
3. Summarize: what was translated (keywords, builtins, exceptions, \
reserved words — cite the mappings), what was left untouched \
(identifiers, strings, comments, and any construct without a pack \
entry), and the validation result. Flag anything that did not map."""


@mcp.prompt(name="legibility-report", title="Codebase legibility report")
def legibility_report_prompt(target_lang: str) -> str:
    """Drive map_existing_codebase and render a stakeholder-readable report."""
    return f"""\
Produce a legibility report: what would translating this codebase into \
{target_lang} look like?

1. Call map_existing_codebase with the provided files and \
target_lang="{target_lang}" (batch the files across several calls if \
there are many). Leave include_translations false unless the reader asked \
to see translated code.
2. Render the result for a non-engineering reader: how many files are \
translatable, the coverage ratio as a percentage, and what the unmapped \
constructs mean in practice (they stay in English after translation).
3. List per-file problems (files that could not be mapped, syntax \
issues) with their paths, and close with a plain-language recommendation \
on whether the codebase is ready to be worked on in {target_lang}."""


def main() -> None:
    """Run the Legesher MCP server on stdio (local engine, no telemetry)."""
    mcp.run(transport="stdio")
