"""The backend seam: everything a tool call does, behind one protocol.

The MCP layer (``server.py``) owns transport, schemas, and error
rendering; what a tool call or resource read *does* is a single method on
a :class:`Backend`. The seam sits at the **tool** level, not the engine
level, and that placement is the point (CORE-1165 §7, CORE-1420):

- :class:`LocalBackend` — the default — carries the full orchestration
  over the locally installed engine: pivot handling, explain composition,
  identifier validation, per-file map aggregation.
- A remote deployment implements the same protocol where each method is
  exactly **one** call against a hosted API that performs the same
  orchestration server-side (``/v1/translate``, ``/v1/explain``,
  ``/v1/map``, ``/v1/languages*``). An engine-level seam would force such
  a deployment to re-run the orchestration client-side, and the two
  deployments would drift; a tool-level seam makes drift structurally
  impossible, because there is nothing left to re-implement.

Contract, for any implementation:

- Methods return the exact typed results the tools publish
  (``schemas.py`` models, :class:`LanguageInfo`, :class:`LanguageTerms`)
  — the MCP layer renders them without addition.
- Expected failures raise :class:`EngineError`: a machine ``code`` plus a
  content-free message, safe to hand to the caller verbatim. Anything
  else is treated as a server bug and collapses to ``internal_error``.
- Arguments arrive already validated by the tool schemas (patterns, size
  bounds, enums); implementations may enforce their own invariants on
  top but must not rely on anything looser.
- Methods are ``async`` so a remote implementation can await its calls;
  :class:`LocalBackend` computes synchronously inside them, exactly as
  the tool bodies always have.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable
from typing import Any, Literal, Protocol, TypedDict, runtime_checkable

from legesher_core.round_trip import Divergence
from legesher_core.round_trip import verify_round_trip as core_verify_round_trip
from legesher_core.text_identity import compare_key
from legesher_core.tree_sitter.identifier_map import IdentifierMap
from legesher_core.tree_sitter.identifier_validator import IdentifierValidator
from legesher_core.unicode_guard import Issue, scan_identifier, scan_text
from legesher_i18n.script_policy import has_policy, policy_for

from .engine import (
    CATEGORIES,
    PIVOT_LANGUAGE,
    EngineError,
    LanguageInfo,
    LocalEngine,
    TranslationOutcome,
    get_engine,
)
from .schemas import (
    SNIPPET_MAX_CHARS,
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
    RoundTripInfo,
    SourceFile,
    SyntaxIssueModel,
    TranslatedFile,
    TranslationResult,
    ValidationInfo,
)

__all__ = [
    "Backend",
    "EngineError",
    "LanguageInfo",
    "LanguageTerms",
    "LocalBackend",
]


class LanguageTerms(TypedDict):
    """One language's full term dictionary for one Python version.

    Key order is the rendered document's order — the resource serializes
    this mapping as-is.
    """

    language: str
    python_version: str
    keywords: dict[str, str]
    builtins: dict[str, str]
    exceptions: dict[str, str]
    implicit_params: dict[str, str]


@runtime_checkable
class Backend(Protocol):
    """What serves the six tools and the two resource reads.

    One method per tool operation plus the resource reads — see the
    module docstring for why the seam sits at this level and what every
    implementation must uphold.
    """

    async def translate_to_native(
        self,
        *,
        source: str,
        source_lang: str,
        target_lang: str,
        python_version: str,
        verify_round_trip: bool,
    ) -> TranslationResult:
        """Translate source code into ``target_lang``."""
        ...

    async def translate_to_source(
        self,
        *,
        source: str,
        source_lang: str,
        python_version: str,
        verify_round_trip: bool,
    ) -> TranslationResult:
        """Translate native-language code back to the English-keyword form."""
        ...

    async def explain_in_language(
        self,
        *,
        source: str,
        explain_in: str,
        code_lang: str,
        python_version: str,
        include_translation: bool,
    ) -> ExplainMaterial:
        """Engine facts for explaining ``source`` in ``explain_in``."""
        ...

    async def lookup_keyword_mapping(
        self,
        *,
        language: str,
        terms: list[str] | None,
        python_version: str,
    ) -> LookupResult:
        """How ``terms`` (or the full mapping) render in ``language``."""
        ...

    async def validate_identifier_translations(
        self,
        *,
        proposals: list[IdentifierProposal],
        target_lang: str,
        glossary: dict[str, str] | None,
        python_version: str,
    ) -> IdentifierValidationResult:
        """Check proposed identifier translations against pack, glossary, batch."""
        ...

    async def map_existing_codebase(
        self,
        *,
        files: list[SourceFile],
        target_lang: str,
        source_lang: str,
        python_version: str,
        include_translations: bool,
    ) -> CodebaseMapResult:
        """The legibility report over a batch of files."""
        ...

    async def list_languages(self) -> list[LanguageInfo]:
        """The language catalog (the ``legesher://languages`` resource)."""
        ...

    async def language_terms(self, *, language: str, python_version: str) -> LanguageTerms:
        """One language's term dictionary (the ``.../terms`` resources)."""
        ...


# -- shared translation/verification helpers --------------------------------


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

    # The forward request, captured under distinct names: the hop callback's
    # parameters must carry the core protocol's names (``TranslateFn``), which
    # shadow this scope's identically named variables.
    forward_source, forward_source_lang = source, source_lang

    def hop(
        source: str, source_lang: str, target_lang: str, python_version: str
    ) -> tuple[str, bool]:
        if (
            source == forward_source
            and source_lang == forward_source_lang
            and target_lang == through_lang
        ):
            return forward.translated_source, forward.pivoted
        outcome = engine.translate(
            source=source,
            source_lang=source_lang,
            target_lang=target_lang,
            python_version=python_version,
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


# -- identifier-validation helpers ------------------------------------------


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

    Mirrors the map engine's pack-collision validation (both sides share
    ``text_identity.compare_key``) so the MCP tool and the map write path
    agree about what collides: the exact sweep first
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


class LocalBackend:
    """The default backend: full orchestration over the local engine.

    Behavior is exactly what the tools have always done — the bodies moved
    here from the tool functions unchanged when the seam was introduced.
    """

    def __init__(self, engine_factory: Callable[[], LocalEngine] | None = None) -> None:
        #: Resolved per call, never cached at construction: the process-wide
        #: engine can be swapped (pack refresh, fault injection in tests),
        #: and construction must not pay for pack discovery a request may
        #: never need.
        self._engine_factory: Callable[[], LocalEngine] = (
            engine_factory if engine_factory is not None else get_engine
        )

    def _engine(self) -> LocalEngine:
        return self._engine_factory()

    # -- translation -------------------------------------------------------

    async def translate_to_native(
        self,
        *,
        source: str,
        source_lang: str,
        target_lang: str,
        python_version: str,
        verify_round_trip: bool,
    ) -> TranslationResult:
        return self._translate(source, source_lang, target_lang, python_version, verify_round_trip)

    async def translate_to_source(
        self,
        *,
        source: str,
        source_lang: str,
        python_version: str,
        verify_round_trip: bool,
    ) -> TranslationResult:
        return self._translate(
            source, source_lang, PIVOT_LANGUAGE, python_version, verify_round_trip
        )

    def _translate(
        self,
        source: str,
        source_lang: str,
        target_lang: str,
        python_version: str,
        verify: bool,
    ) -> TranslationResult:
        """The one translation body both translate methods share.

        The two tools differ only in which side is fixed; a duplicated body
        is how the verify plumbing drifts between them (one contract, one
        implementation - the same rule this feature exists to apply).
        """
        engine = self._engine()
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
        return TranslationResult(
            translated_source=outcome.translated_source,
            source_lang=source_lang,
            target_lang=target_lang,
            python_version=python_version,
            pivoted=outcome.pivoted,
            round_trip=round_trip,
        )

    # -- explanation material ----------------------------------------------

    async def explain_in_language(
        self,
        *,
        source: str,
        explain_in: str,
        code_lang: str,
        python_version: str,
        include_translation: bool,
    ) -> ExplainMaterial:
        engine = self._engine()
        explain_maps = engine.pack_categories(engine.load_pack(explain_in, python_version))
        code_maps = (
            engine.pack_categories(engine.load_pack(code_lang, python_version))
            if code_lang != PIVOT_LANGUAGE
            else None
        )

        tokenizable = True
        english = source
        if code_lang != PIVOT_LANGUAGE:
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

    # -- term lookup ---------------------------------------------------------

    async def lookup_keyword_mapping(
        self,
        *,
        language: str,
        terms: list[str] | None,
        python_version: str,
    ) -> LookupResult:
        engine = self._engine()
        category_maps = engine.pack_categories(engine.load_pack(language, python_version))
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

    # -- identifier validation ----------------------------------------------

    async def validate_identifier_translations(
        self,
        *,
        proposals: list[IdentifierProposal],
        target_lang: str,
        glossary: dict[str, str] | None,
        python_version: str,
    ) -> IdentifierValidationResult:
        engine = self._engine()
        pack = engine.load_pack(target_lang, python_version)

        # Both sides are normalized: an NFD source key would otherwise never
        # match an NFC proposal, so drift would go unreported and the merged
        # glossary would gain a second key for one concept.
        established = {_nfc(source): _nfc(term) for source, term in (glossary or {}).items()}
        # One concept, one term — in both directions, each side carrying where
        # it came from. Accepted proposals join as the batch is walked, so a
        # batch with no glossary behind it still has to be self-consistent.
        # Comparison is NFKC+casefold (compare_key), so an NFD twin or a case
        # variant is the same term, not a second one.
        translation_of: dict[str, tuple[str, _ConflictOrigin]] = {
            source: (term, "glossary") for source, term in established.items()
        }
        owners_of: dict[str, tuple[set[str], _ConflictOrigin]] = {}
        for source, term in established.items():
            owners, _origin = owners_of.setdefault(compare_key(term), (set(), "glossary"))
            owners.add(source)

        # Format characters this locale's script legitimately needs inside an
        # identifier. Without it the Unicode gate rejects orthography the
        # language requires: Sinhala forms conjuncts with virama+ZWJ, so
        # `සත්‍ය` — the value Legesher's own `si` pack ships for `True` on
        # 3.13+ — scans as an `invisible` U+200D and every Sinhala proposal is
        # refused. Default-deny is still the rule; `policy_for` opens exactly
        # the characters a registered script declares, and bidi controls are
        # never suppressed by this argument.
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
            # rewrite a settled entry to a case or fullwidth variant —
            # precisely the confusable NFKC exists to keep out of storage.
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

            # The SOURCE is checked too. It becomes a key in ``accepted``,
            # which the response describes as ready to merge into the project
            # glossary, so an unvalidated source lets `{"calculate tax": "..."}`
            # come back ok=true and seed a glossary key that can never match an
            # identifier in code. English source identifiers carry no format
            # characters, so the scan runs default-deny here regardless of the
            # target locale's policy.
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
                            f"{issue.codepoint} {issue.char_name} at {issue.offset}"
                            for issue in issues
                        ),
                    )
                )

            reserved = _pack_collision(candidate, pack)
            if reserved is not None:
                conflicts.append(
                    IdentifierConflict(kind="reserved_term", against="pack", detail=reserved)
                )

            if prior is not None and compare_key(prior[0]) != compare_key(candidate):
                conflicts.append(
                    IdentifierConflict(kind="drift", against=prior[1], detail=prior[0])
                )

            owned = owners_of.get(compare_key(candidate))
            if owned is not None and source not in owned[0]:
                conflicts.append(
                    IdentifierConflict(
                        kind="collision", against=owned[1], detail=sorted(owned[0])[0]
                    )
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

    # -- codebase mapping ----------------------------------------------------

    async def map_existing_codebase(
        self,
        *,
        files: list[SourceFile],
        target_lang: str,
        source_lang: str,
        python_version: str,
        include_translations: bool,
    ) -> CodebaseMapResult:
        engine = self._engine()
        target_maps = engine.pack_categories(engine.load_pack(target_lang, python_version))
        if source_lang != PIVOT_LANGUAGE:
            engine.load_pack(source_lang, python_version)  # fail fast, sanitized

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
                    raise EngineError(
                        "invalid_source", "Source could not be tokenized as Python code."
                    )
            except EngineError as exc:
                if exc.code != "invalid_source":
                    raise
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
                translated = _finish_from_pivot(
                    engine,
                    english=english,
                    original=entry.source,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    python_version=python_version,
                )
                translated_files.append(
                    TranslatedFile(path=entry.path, translated_source=translated)
                )

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

    # -- resource reads ------------------------------------------------------

    async def list_languages(self) -> list[LanguageInfo]:
        return self._engine().list_languages()

    async def language_terms(self, *, language: str, python_version: str) -> LanguageTerms:
        engine = self._engine()
        pack = engine.load_pack(language, python_version)
        categories = engine.pack_categories(pack)
        return LanguageTerms(
            language=language,
            python_version=str(pack.version),
            keywords=categories["keywords"],
            builtins=categories["builtins"],
            exceptions=categories["exceptions"],
            implicit_params=categories["implicit_params"],
        )
