"""The Legesher MCP server: six coarse tools, resources, and prompts.

Design (CORE-1165 architecture doc, §2/§5):

- Task-shaped tools instead of an endpoint mirror; catalog and
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
import unicodedata
from collections.abc import Sequence
from dataclasses import asdict
from typing import Annotated, Any, Literal, cast, get_args

from legesher_core.round_trip import Divergence
from legesher_core.round_trip import verify_round_trip as core_verify_round_trip
from legesher_core.text_identity import compare_key
from legesher_core.tree_sitter.identifier_map import IdentifierMap
from legesher_core.tree_sitter.identifier_validator import IdentifierValidator
from legesher_core.unicode_guard import Issue, scan_identifier, scan_text
from legesher_i18n.script_policy import has_policy, policy_for
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ContentBlock, ToolAnnotations
from pydantic import Field, ValidationError

from . import __version__
from .engine import (
    CATEGORIES,
    LANG_CODE_PATTERN,
    PIVOT_LANGUAGE,
    EngineError,
    LocalEngine,
    TranslationOutcome,
    get_engine,
)
from .schemas import (
    DEFAULT_PYTHON_VERSION,
    LANG_CODE_MAX_LENGTH,
    SNIPPET_MAX_CHARS,
    SOURCE_MAX_CHARS,
    SUPPORTED_PYTHON_VERSIONS,
    CodebaseMapResult,
    CodebaseMapSummary,
    ConstructMapping,
    DivergenceModel,
    ExplainMaterial,
    FileMapEntry,
    IdentifierConflict,
    IdentifierProposal,
    IdentifierValidationResult,
    IdentifierVerdict,
    KeywordMappings,
    LookupResult,
    PythonVersion,
    RoundTripInfo,
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
the prose), lookup_keyword_mapping for quick term lookups,
validate_identifier_translations to check identifier names you invented
before recording them, and map_existing_codebase for a repo-level
legibility report. The language catalog is the legesher://languages
resource; full dictionaries are
legesher://languages/{lang}/terms. X→Y translation pivots through English
(results say so via `pivoted`). Everything runs locally: no network, no
telemetry."""

_LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

#: Derived from the Literal so the accepted names cannot drift from the type.
_LOG_LEVELS: tuple[str, ...] = get_args(_LogLevel)

_DEFAULT_LOG_LEVEL: _LogLevel = "WARNING"


def _log_level_from_env() -> _LogLevel:
    """Log level from LEGESHER_MCP_LOG_LEVEL; quiet (WARNING) by default.

    An unset or unrecognized value must never stop the server from
    booting, so anything invalid falls back to the default.
    """
    raw = os.environ.get("LEGESHER_MCP_LOG_LEVEL", "").strip().upper()
    if raw in _LOG_LEVELS:
        return cast(_LogLevel, raw)
    return _DEFAULT_LOG_LEVEL


#: Cap on how much of a rejection we spell out, so a request with hundreds
#: of bad fields cannot turn the error into the payload.
_MAX_REPORTED_ARGUMENT_ERRORS = 5


def _argument_error_message(exc: ValidationError) -> str:
    """Field-by-field rejection text with nothing the caller sent in it.

    Uses pydantic's ``loc`` (field path) and ``msg`` (the constraint that
    failed) and deliberately drops ``input``, which carries a prefix of the
    submitted value — for the ``source`` fields that is the caller's code.
    """
    errors = exc.errors()
    parts = [
        f"{'.'.join(str(piece) for piece in error['loc']) or '<arguments>'} — {error['msg']}"
        for error in errors[:_MAX_REPORTED_ARGUMENT_ERRORS]
    ]
    if len(errors) > _MAX_REPORTED_ARGUMENT_ERRORS:
        parts.append(f"(+{len(errors) - _MAX_REPORTED_ARGUMENT_ERRORS} more)")
    return "invalid_arguments: " + "; ".join(parts)


class _LegesherMCP(FastMCP):
    """FastMCP with every tool failure spoken in the server's own voice.

    The SDK renders an argument-validation failure as pydantic's raw dump —
    which quotes ``input_value``, i.e. a prefix of whatever the caller sent,
    and links to errors.pydantic.dev. Next to the engine's sanitized
    ``code: message`` errors that is both off-voice and a small leak: the
    echoed prefix of a rejected oversized file is the caller's source.

    ``call_tool`` is the SDK's public entry point for a tool call, so
    overriding it needs no private internals. Four cases:

    - A failure the tools raised themselves is already a machine code plus a
      content-free message — passed through untouched.
    - A ``ToolError`` the SDK raised with no ``__cause__`` is a message the
      SDK composed itself, not an exception repr ("Unknown tool: X" is the
      only such case in 1.28). Safe, and more useful than a generic error.
    - A pydantic ``ValidationError`` **for this tool's argument model**
      becomes ``invalid_arguments``, naming the fields and the constraints
      and never the values.
    - Anything else — an engine-boot failure, a bug, a ValidationError from
      the tool's own output model — collapses to ``internal_error``. Note
      the last one: the SDK's try block wraps the tool body and the result
      conversion too, so not every ValidationError here is the caller's
      fault, and blaming them would invite a retry loop over a server bug.
    """

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> Sequence[ContentBlock] | dict[str, Any]:
        try:
            return await super().call_tool(name, arguments)
        except ToolError as exc:
            cause = exc.__cause__
            if cause is None or isinstance(cause, ToolError):
                raise  # SDK-composed text, or already sanitized by _tool_error
            if isinstance(cause, ValidationError) and cause.title == f"{name}Arguments":
                # The SDK builds the argument model as `{func.__name__}Arguments`
                # (func_metadata.py:258), which is what distinguishes a bad
                # request from a failure inside the tool.
                raise ToolError(_argument_error_message(cause)) from exc
            raise ToolError("internal_error: The server could not complete the request.") from exc


mcp = _LegesherMCP("legesher", instructions=_INSTRUCTIONS, log_level=_log_level_from_env())
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
_VerifyParam = Annotated[
    bool,
    Field(
        description=(
            "Also verify the round trip: translate the result back, compare "
            "byte-for-byte, and check the canonical form compiles. Use this "
            "instead of comparing two renderings yourself — exact comparison "
            "over a long file is not a judgement to make by eye. Doubles "
            "translation cost; quadruples via a pivot."
        ),
    ),
]


#: Every tool on this server is a pure function of its arguments: it reads
#: the locally installed packs, never writes a file, never executes the
#: submitted code (validation is ``compile()`` only), and never opens a
#: socket. Declaring that lets clients skip or downgrade approval prompts.
#: A tool that ever stops matching this description must pass its own
#: annotations — the surface-lock test fails otherwise, which is the point.
_READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _tool_error(exc: EngineError) -> ToolError:
    """Convert an engine failure into a machine-coded MCP tool error."""
    return ToolError(f"{exc.code}: {exc}")


def _finish_from_pivot(
    engine: LocalEngine,
    *,
    english: str,
    original: str,
    source_lang: str,
    target_lang: str,
    python_version: str,
) -> str:
    """Translate to ``target_lang`` reusing an already-computed English form.

    Callers that needed the English pivot for scanning or validation have
    already paid for the X→en hop. Asking the engine for X→Y here would
    silently redo it — the engine has no direct X→Y path, so it always
    pivots. Starting from ``english`` runs the remaining en→Y hop only.

    ``original`` is returned untouched when source and target are the same
    language, preserving the engine's own no-op short-circuit rather than
    round-tripping the text through English for no reason.
    """
    if source_lang == target_lang:
        return original
    outcome = engine.translate(
        source=english,
        source_lang=PIVOT_LANGUAGE,
        target_lang=target_lang,
        python_version=python_version,
    )
    return str(outcome.translated_source)


def _snippet(text: str) -> tuple[str, bool]:
    """Bound one divergence text field for the wire."""
    if len(text) > SNIPPET_MAX_CHARS:
        return text[:SNIPPET_MAX_CHARS], True
    return text, False


def _divergence_model(divergence: Divergence) -> DivergenceModel:
    """Project a core divergence onto the bounded wire shape."""
    expected, expected_truncated = _snippet(divergence.expected)
    actual, actual_truncated = _snippet(divergence.actual)
    return DivergenceModel(
        line=divergence.line,
        offset=divergence.offset,
        expected=expected,
        actual=actual,
        truncated=expected_truncated or actual_truncated,
        kind=divergence.kind.value,
        layer=divergence.layer.value if divergence.layer is not None else None,
    )


def _round_trip(
    engine: LocalEngine,
    *,
    source: str,
    forward: TranslationOutcome,
    source_lang: str,
    through_lang: str,
    python_version: str,
) -> RoundTripInfo:
    """Verify the round trip, reusing the already-computed forward hop.

    The forward hop is the translation the caller asked for: it already ran
    (so its failures already surfaced as ordinary tool errors, flag or no
    flag), and the adapter serves its result rather than translating the
    same hop twice. Only the return hop reaches the engine, and a failure
    there is a verdict inside the report, never an exception.

    Classification runs against the non-pivot language's pack — the side
    whose renderings can diverge — preferring the source side when neither
    language is English (the compared strings are written in it).

    Raises:
        EngineError: ``vacuous_round_trip`` when both languages are the
            same — the engine short-circuits identity, so both hops would
            be no-ops and the comparison would verify nothing.
    """
    pack_lang = source_lang if source_lang != PIVOT_LANGUAGE else through_lang
    pack = engine.load_pack(pack_lang, python_version)

    def hop(text: str, src: str, tgt: str, version: str) -> tuple[str, bool]:
        if text == source and src == source_lang and tgt == through_lang:
            return forward.translated_source, forward.pivoted
        outcome = engine.translate(
            source=text, source_lang=src, target_lang=tgt, python_version=version
        )
        return outcome.translated_source, outcome.pivoted

    # compile_check understands English keywords only, and the validator
    # receives the forward rendering — which is canonical English exactly
    # when the trip goes THROUGH the pivot language. Anywhere else the
    # compile fact is unknown, not assumed: forward_valid stays null.
    validate = (
        (lambda text: engine.compile_check(text).valid) if through_lang == PIVOT_LANGUAGE else None
    )

    try:
        report = core_verify_round_trip(
            source,
            source_lang,
            through_lang,
            python_version,
            translate=hop,
            pack=pack,
            validate=validate,
        )
    except ValueError as exc:
        raise EngineError(
            "vacuous_round_trip",
            "source and verification languages are identical; the round trip would verify nothing",
        ) from exc

    return RoundTripInfo(
        round_trips=report.round_trips,
        forward_valid=report.forward_valid,
        verdict_line=report.verdict_line,
        divergence_count=report.divergence_count,
        divergences=[_divergence_model(d) for d in report.divergences],
        verified=sorted(layer.value for layer in report.verified),
        grammar_version=report.grammar_version,
        pivoted=report.pivoted,
        schema_version=report.schema_version,
    )


def _translate(
    source: str,
    source_lang: str,
    target_lang: str,
    python_version: str,
    verify: bool,
) -> TranslationResult:
    """The one translation body both translate tools share.

    The two tools differ only in which side is fixed; a duplicated body is
    how the verify plumbing drifts between them (one contract, one
    implementation - the same rule this feature exists to apply).
    """
    engine = get_engine()
    try:
        outcome = engine.translate(
            source=source,
            source_lang=source_lang,
            target_lang=target_lang,
            python_version=python_version,
        )
        round_trip = (
            _round_trip(
                engine,
                source=source,
                forward=outcome,
                source_lang=source_lang,
                through_lang=target_lang,
                python_version=python_version,
            )
            if verify
            else None
        )
    except EngineError as exc:
        raise _tool_error(exc) from exc
    return TranslationResult(
        translated_source=outcome.translated_source,
        source_lang=source_lang,
        target_lang=target_lang,
        python_version=python_version,
        pivoted=outcome.pivoted,
        round_trip=round_trip,
    )


# -- tools ----------------------------------------------------------------


@mcp.tool(annotations=_READ_ONLY)
def translate_to_native(
    source: _SourceParam,
    target_lang: _LangParam,
    source_lang: _LangParam = PIVOT_LANGUAGE,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
    verify_round_trip: _VerifyParam = False,
) -> TranslationResult:
    """Translate Python source code into the caller's natural language.

    Accepts complete files and fragments alike — there is no separate
    snippet mode to choose. When neither language is English the engine
    pivots through English (packs are authored against English) and the
    result reports `pivoted: true`. Formatting, comments, identifiers, and
    string contents are preserved; only keywords, builtins, exceptions,
    and reserved words are translated.
    """
    return _translate(source, source_lang, target_lang, python_version, verify_round_trip)


@mcp.tool(annotations=_READ_ONLY)
def translate_to_source(
    source: _SourceParam,
    source_lang: _LangParam,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
    verify_round_trip: _VerifyParam = False,
) -> TranslationResult:
    """Translate native-language code back to English-keyword Python.

    The inverse of translate_to_native and the round-trip half of the
    collaboration story: the output is the form the interpreter, the
    toolchain, and upstream collaborators use. The target is fixed to
    English — for a general X→Y translation call translate_to_native with
    an explicit source_lang.
    """
    return _translate(source, source_lang, PIVOT_LANGUAGE, python_version, verify_round_trip)


@mcp.tool(annotations=_READ_ONLY)
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
            translated_source = _finish_from_pivot(
                engine,
                english=english,
                original=source,
                source_lang=code_lang,
                target_lang=explain_in,
                python_version=python_version,
            )
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


@mcp.tool(annotations=_READ_ONLY)
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


#: Where a drift or collision was found. Narrower than IdentifierConflict's
#: full `against` set, because only these two can own a prior rendering.
_ConflictOrigin = Literal["glossary", "batch"]


def _nfc(text: str) -> str:
    """The storage form. Values are stored NFC and compared NFKC+fold."""
    return unicodedata.normalize("NFC", text)


def _identifier_issues(
    value: str,
    is_identifier: bool,
    allowed_format_chars: frozenset[str] = frozenset(),
) -> list[Issue]:
    """Unicode-contract findings for one proposed identifier.

    The text-level checks (bidi, invisibles, Default_Ignorable, tatweel, BOM)
    always run. The positive script allowlist (CORE-1558) runs only when
    ``value`` is a valid identifier: it closes the class no property-based net
    can see — U+2D7F is ``Mn`` + ``ID_Continue``, NFKC-stable, and not
    Default_Ignorable, so it satisfies ``str.isidentifier()`` and would
    otherwise be merged into the glossary — but a value that is not an
    identifier at all has already been reported as ``malformed``, and calling
    its spaces a Unicode-contract violation would only bury the real problem.
    """
    issues = scan_text(value, allowed_format_chars=allowed_format_chars)
    if is_identifier:
        issues += [
            issue
            for issue in scan_identifier(value, allowed_format_chars)
            if issue.kind == "script"
        ]
        issues.sort(key=lambda issue: issue.offset)
    return issues


def _pack_collision(candidate: str, pack: Any) -> str | None:
    """The pack entry ``candidate`` takes, or None.

    Mirrors ``register_map.correction._validate_pack`` so the MCP tool and
    the CLI write path agree about what collides: the exact sweep first
    (CORE-710), then NFKC+casefold, which catches case variants and
    decomposed forms an equality check misses. ``members`` is in the domain
    because the MLCP members partition is an identifier class (CORE-1372) —
    a no-op for Python, wrong for JS the moment the section is populated.
    """
    exact = IdentifierMap().validate_against_pack(candidate, pack)
    if exact is not None:
        return exact
    key = compare_key(candidate)
    for section, mapping in (
        ("keyword", pack.keywords),
        ("builtin", pack.builtins),
        ("exception", pack.exceptions),
        ("implicit_param", pack.implicit_params),
        ("member", getattr(pack, "members", {}) or {}),
    ):
        for source_key, target_value in mapping.items():
            if compare_key(target_value) == key:
                return f"{section}:{source_key}"
    return None


@mcp.tool(annotations=_READ_ONLY)
def validate_identifier_translations(
    proposals: Annotated[
        list[IdentifierProposal],
        Field(
            min_length=1,
            description="Proposed identifier translations to check, as source/translation pairs.",
        ),
    ],
    target_lang: _LangParam,
    glossary: Annotated[
        dict[str, str] | None,
        Field(
            description=(
                "The project's existing identifier translations for this "
                "one language, flat: {source_identifier: translation}. If "
                "your repo has .legesher/identifier_map.json, that file is "
                "nested by language — send the slice for target_lang (what "
                "IdentifierMap.get_glossary(target_lang) returns), not the "
                "file verbatim. Pass it as content: the server never reads "
                "your filesystem. Omit on a first pass."
            ),
        ),
    ] = None,
    python_version: PythonVersion = DEFAULT_PYTHON_VERSION,
) -> IdentifierValidationResult:
    """Check proposed identifier translations before you record them.

    Packs make keywords deterministic; identifiers have no pack, so this is
    the guarantee they get instead. Each proposal is checked for a name the
    pack has reserved, for drift (one concept acquiring a second term) and
    for collision (one term acquiring a second concept) — against both the
    existing glossary and the rest of the batch.

    Returns a verdict per proposal plus ``accepted``, the conflict-free
    subset as a mapping ready to merge into the project glossary. Recording
    it is the caller's to do: this server writes nothing.
    """
    engine = get_engine()
    try:
        pack = engine.load_pack(target_lang, python_version)
    except EngineError as exc:
        raise _tool_error(exc) from exc

    # Both sides are normalized: an NFD source key would otherwise never match
    # an NFC proposal, so drift would go unreported and the merged glossary
    # would gain a second key for one concept.
    established = {_nfc(source): _nfc(term) for source, term in (glossary or {}).items()}
    # One concept, one term — in both directions, each side carrying where it
    # came from. Accepted proposals join as the batch is walked, so a batch
    # with no glossary behind it still has to be self-consistent. Comparison
    # is NFKC+casefold (compare_key), so an NFD twin or a case variant is the
    # same term, not a second one.
    translation_of: dict[str, tuple[str, _ConflictOrigin]] = {
        source: (term, "glossary") for source, term in established.items()
    }
    owners_of: dict[str, tuple[set[str], _ConflictOrigin]] = {}
    for source, term in established.items():
        owners, _origin = owners_of.setdefault(compare_key(term), (set(), "glossary"))
        owners.add(source)

    # Format characters this locale's script legitimately needs inside an
    # identifier. Without it the Unicode gate rejects orthography the language
    # requires: Sinhala forms conjuncts with virama+ZWJ, so `සත්‍ය` — the value
    # Legesher's own `si` pack ships for `True` on 3.13+ — scans as an
    # `invisible` U+200D and every Sinhala proposal is refused. Default-deny is
    # still the rule; `policy_for` opens exactly the characters a registered
    # script declares, and bidi controls are never suppressed by this argument.
    allowed_format_chars = (
        policy_for(target_lang).allowed_format_chars if has_policy(target_lang) else frozenset()
    )

    verdicts: list[IdentifierVerdict] = []
    accepted: dict[str, str] = {}

    for proposal in proposals:
        # Storage is NFC; every check below runs on the stored form.
        source = _nfc(proposal.source)
        candidate = _nfc(proposal.translation)

        # A variant spelling of this source's own established term is the
        # same term under the contract, so settle on the spelling already
        # recorded. Taking the proposal's instead would let a merge quietly
        # rewrite a settled entry to a case or fullwidth variant — precisely
        # the confusable NFKC exists to keep out of storage.
        prior = translation_of.get(source)
        if prior is not None and compare_key(prior[0]) == compare_key(candidate):
            candidate = prior[0]

        conflicts: list[IdentifierConflict] = []

        candidate_is_identifier = IdentifierValidator().is_valid(candidate)
        source_is_identifier = IdentifierValidator().is_valid(source)

        if not candidate_is_identifier:
            conflicts.append(
                IdentifierConflict(
                    kind="malformed",
                    against="python",
                    detail="must satisfy str.isidentifier() and not be a Python keyword",
                )
            )

        # The SOURCE is checked too. It becomes a key in ``accepted``, which the
        # response describes as ready to merge into the project glossary, so an
        # unvalidated source lets `{"calculate tax": "..."}` come back ok=true
        # and seed a glossary key that can never match an identifier in code.
        # English source identifiers carry no format characters, so the scan
        # runs default-deny here regardless of the target locale's policy.
        if not source_is_identifier:
            conflicts.append(
                IdentifierConflict(
                    kind="malformed",
                    against="python",
                    detail=(
                        f"source {source!r} must satisfy str.isidentifier() and "
                        f"not be a Python keyword"
                    ),
                )
            )

        source_issues = _identifier_issues(source, source_is_identifier)
        if source_issues:
            conflicts.append(
                IdentifierConflict(
                    kind="unsafe_text",
                    against="unicode_contract",
                    detail="; ".join(
                        f"source {issue.codepoint} {issue.char_name} at {issue.offset}"
                        for issue in source_issues
                    ),
                )
            )

        issues = _identifier_issues(candidate, candidate_is_identifier, allowed_format_chars)
        if issues:
            conflicts.append(
                IdentifierConflict(
                    kind="unsafe_text",
                    against="unicode_contract",
                    detail="; ".join(
                        f"{issue.codepoint} {issue.char_name} at {issue.offset}" for issue in issues
                    ),
                )
            )

        reserved = _pack_collision(candidate, pack)
        if reserved is not None:
            conflicts.append(
                IdentifierConflict(kind="reserved_term", against="pack", detail=reserved)
            )

        if prior is not None and compare_key(prior[0]) != compare_key(candidate):
            conflicts.append(IdentifierConflict(kind="drift", against=prior[1], detail=prior[0]))

        owned = owners_of.get(compare_key(candidate))
        if owned is not None and source not in owned[0]:
            conflicts.append(
                IdentifierConflict(kind="collision", against=owned[1], detail=sorted(owned[0])[0])
            )

        verdicts.append(
            IdentifierVerdict(
                source=source,
                translation=candidate,
                proposed=(proposal.translation if proposal.translation != candidate else None),
                ok=not conflicts,
                conflicts=conflicts,
            )
        )
        if not conflicts:
            accepted[source] = candidate
            translation_of.setdefault(source, (candidate, "batch"))
            owners, _origin = owners_of.setdefault(compare_key(candidate), (set(), "batch"))
            owners.add(source)

    return IdentifierValidationResult(
        target_lang=target_lang,
        python_version=python_version,
        results=verdicts,
        accepted=accepted,
    )


@mcp.tool(annotations=_READ_ONLY)
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
                translated = _finish_from_pivot(
                    engine,
                    english=english,
                    original=entry.source,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    python_version=python_version,
                )
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


def _terms_document(lang: str, python_version: str) -> str:
    """Render one language's full term dictionary for one Python version."""
    if python_version not in SUPPORTED_PYTHON_VERSIONS:
        # Gate before the loader: the version is joined into a pack filename
        # downstream, and the loader's own ValueError is not in our voice.
        raise ValueError(
            f"unsupported_python_version: {python_version[:16]!r}. "
            f"Supported: {', '.join(SUPPORTED_PYTHON_VERSIONS)}."
        )
    engine = get_engine()
    try:
        pack = engine.load_pack(lang, python_version)
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


@mcp.resource("legesher://languages/{lang}/terms", mime_type="application/json")
def language_terms(lang: str) -> str:
    """Full term dictionary for one language (default Python version)."""
    return _terms_document(lang, DEFAULT_PYTHON_VERSION)


@mcp.resource("legesher://languages/{lang}/terms/{python_version}", mime_type="application/json")
def language_terms_for_version(lang: str, python_version: str) -> str:
    """Full term dictionary for one language at a specific Python version.

    The explicit-version form of the resource above, for callers pinned to
    a grammar other than the default — pack contents differ by version
    (`match`/`case` in 3.10, `except*` in 3.11, and so on).
    """
    return _terms_document(lang, python_version)


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
