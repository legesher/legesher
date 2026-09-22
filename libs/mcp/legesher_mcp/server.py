"""The Legesher MCP server: six coarse tools, resources, and prompts.

Design (CORE-1165 architecture doc, §2/§5; CORE-1420 §3/§7/§8):

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

This module owns transport, schemas, and error rendering. What a tool call
or resource read *does* lives behind the :class:`~legesher_mcp.backend.Backend`
seam, and :func:`create_server` assembles the complete server — every tool,
resource, and prompt — from a backend plus an entitlement gate
(:mod:`legesher_mcp.gate`; default-open, so nothing is gated unless a
deployment installs a policy).

Two transports serve the same server:

- **stdio** (the default, and what ``legesher-mcp`` runs): local-only —
  no network calls, no accounts, no telemetry.
- **streamable HTTP** (``legesher-mcp --transport streamable-http``):
  the same tools bound to one interface, loopback by default. Stateless,
  plain JSON responses, with the ``Origin`` header validated against the
  bound interface when present (DNS-rebinding defense). This entry ships
  no authentication and is meant for localhost and single-user self-host
  use; a multi-tenant deployment mounts :func:`create_http_app` behind
  its own auth middleware instead.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import asdict
from typing import Annotated, Any, Literal, cast, get_args

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ContentBlock, ToolAnnotations
from pydantic import Field, ValidationError
from starlette.applications import Starlette

from . import __version__
from .backend import Backend, LocalBackend
from .engine import (
    LANG_CODE_PATTERN,
    PIVOT_LANGUAGE,
    EngineError,
    get_engine,
)
from .gate import (
    EntitlementGate,
    allow_all,
    current_request_context,
    denial_message,
)
from .schemas import (
    DEFAULT_PYTHON_VERSION,
    LANG_CODE_MAX_LENGTH,
    SOURCE_MAX_CHARS,
    SUPPORTED_PYTHON_VERSIONS,
    CodebaseMapResult,
    ExplainMaterial,
    IdentifierProposal,
    IdentifierValidationResult,
    LookupResult,
    PythonVersion,
    SourceFile,
    TranslationResult,
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
    and links to errors.pydantic.dev — and wraps every tool-body exception
    in an "Error executing tool <name>: …" prefix. Next to the engine's
    sanitized ``code: message`` errors that is both off-voice and a small
    leak: the echoed prefix of a rejected oversized file is the caller's
    source.

    ``call_tool`` is the SDK's public entry point for a tool call, so
    overriding it needs no private internals. Five cases:

    - A ``ToolError`` the SDK raised with no ``__cause__`` is a message the
      SDK composed itself, not an exception repr ("Unknown tool: X" is the
      only such case in 1.28). Safe, and more useful than a generic error.
    - A ``ToolError`` a tool body raised itself (a gate denial) is already
      a machine code plus a content-free message — re-raised without the
      SDK's wrapper prefix, so the code stays first.
    - An :class:`EngineError` from the backend is the expected-failure
      contract: rendered as its machine ``code: message``, verbatim.
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
            if cause is None:
                raise  # SDK-composed text ("Unknown tool: X")
            if isinstance(cause, ToolError):
                raise cause  # already in the server's voice; drop the wrapper prefix
            if isinstance(cause, EngineError):
                raise _tool_error(cause) from exc
            if isinstance(cause, ValidationError) and cause.title == f"{name}Arguments":
                # The SDK builds the argument model as `{func.__name__}Arguments`
                # (func_metadata.py:258), which is what distinguishes a bad
                # request from a failure inside the tool.
                raise ToolError(_argument_error_message(cause)) from exc
            raise ToolError("internal_error: The server could not complete the request.") from exc


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


#: The one tool a gate is consulted for. Kept in lockstep with
#: :data:`legesher_mcp.gate.GATEABLE_TOOLS` (asserted by the gate suite):
#: the gate module owns the set and the denial copy, this module owns the
#: single call site — no dispatch table, so a tool cannot become gated by
#: a data change alone.
_GATED_MAP_TOOL = "map_existing_codebase"

#: Loopback names the SDK's transport security recognizes; a bind to one of
#: these gets the SDK's own loopback allowlist (any loopback origin, any
#: port), which is the right shape for the local default.
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def _transport_security_for(host: str) -> TransportSecuritySettings | None:
    """The DNS-rebinding defense matching the bound interface.

    The streamable HTTP endpoint validates the ``Origin`` header when
    present: a cross-origin browser page (the DNS-rebinding vector) is
    rejected with 403, while MCP clients that send no Origin pass — they
    are not browsers and the header is not theirs to fake. The allowlist
    follows the bind: a loopback bind accepts loopback origins (via the
    SDK's own default), any other single interface accepts only origins
    naming that interface. The ``Host`` header is validated the same way.
    """
    if host in _LOOPBACK_HOSTS:
        return None  # the SDK installs its loopback allowlist for these
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[host, f"{host}:*"],
        allowed_origins=[
            f"http://{host}",
            f"http://{host}:*",
            f"https://{host}",
            f"https://{host}:*",
        ],
    )


def create_server(
    *,
    backend: Backend | None = None,
    gate: EntitlementGate | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> _LegesherMCP:
    """Build the complete Legesher MCP server from a backend and a gate.

    The factory is the assembly point: all six tools, both resources (plus
    the versioned terms template), and all three prompts are registered
    against ``backend``, with ``gate`` consulted for the gateable tool.
    The tool functions themselves stay thin — validate arguments against
    the published schemas, call the backend, render the typed result.

    Args:
        backend: What serves the calls. Defaults to :class:`LocalBackend`
            over the process-wide local engine.
        gate: The entitlement policy. Defaults to
            :func:`~legesher_mcp.gate.allow_all` — nothing is gated. The
            stdio entry and the self-host HTTP entry never pass one.
        host: Interface for the HTTP transport (ignored on stdio).
            Loopback by default; the Origin/Host allowlist derives from it.
        port: Port for the HTTP transport (ignored on stdio).

    Returns:
        A ready FastMCP server. Run it (``.run(transport=...)``) or mount
        its ASGI app (see :func:`create_http_app`). The HTTP posture is
        stateless with plain JSON responses.
    """
    resolved_backend: Backend = (
        backend
        if backend is not None
        # Late-bound on purpose: the process-wide engine accessor can be
        # swapped (pack refresh, fault injection in tests) and must be
        # re-read per call, through this module's namespace.
        else LocalBackend(engine_factory=lambda: get_engine())
    )
    resolved_gate: EntitlementGate = gate if gate is not None else allow_all

    server = _LegesherMCP(
        "legesher",
        instructions=_INSTRUCTIONS,
        log_level=_log_level_from_env(),
        host=host,
        port=port,
        stateless_http=True,
        json_response=True,
        transport_security=_transport_security_for(host),
    )
    # The SDK's FastMCP (1.28) has no version passthrough, and the low-level
    # server otherwise reports the SDK's own package version in initialize.
    server._mcp_server.version = __version__

    # -- tools ----------------------------------------------------------------

    @server.tool(annotations=_READ_ONLY)
    async def translate_to_native(
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
        return await resolved_backend.translate_to_native(
            source=source,
            source_lang=source_lang,
            target_lang=target_lang,
            python_version=python_version,
            verify_round_trip=verify_round_trip,
        )

    @server.tool(annotations=_READ_ONLY)
    async def translate_to_source(
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
        return await resolved_backend.translate_to_source(
            source=source,
            source_lang=source_lang,
            python_version=python_version,
            verify_round_trip=verify_round_trip,
        )

    @server.tool(annotations=_READ_ONLY)
    async def explain_in_language(
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
        return await resolved_backend.explain_in_language(
            source=source,
            explain_in=explain_in,
            code_lang=code_lang,
            python_version=python_version,
            include_translation=include_translation,
        )

    @server.tool(annotations=_READ_ONLY)
    async def lookup_keyword_mapping(
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
        return await resolved_backend.lookup_keyword_mapping(
            language=language,
            terms=terms,
            python_version=python_version,
        )

    @server.tool(annotations=_READ_ONLY)
    async def validate_identifier_translations(
        proposals: Annotated[
            list[IdentifierProposal],
            Field(
                min_length=1,
                description=(
                    "Proposed identifier translations to check, as source/translation pairs."
                ),
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
        return await resolved_backend.validate_identifier_translations(
            proposals=proposals,
            target_lang=target_lang,
            glossary=glossary,
            python_version=python_version,
        )

    @server.tool(annotations=_READ_ONLY)
    async def map_existing_codebase(
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
        # The one gated call site (see gate.py for the policy semantics).
        # The tool is always LISTED; entitlement is checked at call time,
        # and a denial is the package's actionable message, never a
        # missing tool or an opaque failure.
        decision = resolved_gate(_GATED_MAP_TOOL, current_request_context())
        if not decision.allowed:
            raise ToolError(denial_message(_GATED_MAP_TOOL, decision.detail))
        return await resolved_backend.map_existing_codebase(
            files=files,
            target_lang=target_lang,
            source_lang=source_lang,
            python_version=python_version,
            include_translations=include_translations,
        )

    # -- resources ------------------------------------------------------------

    @server.resource("legesher://languages", mime_type="application/json")
    async def languages_catalog() -> str:
        """The language catalog: code, names, direction, status, pack availability."""
        return json.dumps(
            [asdict(info) for info in await resolved_backend.list_languages()],
            ensure_ascii=False,
            indent=2,
        )

    async def _terms_document(lang: str, python_version: str) -> str:
        """Render one language's full term dictionary for one Python version."""
        if python_version not in SUPPORTED_PYTHON_VERSIONS:
            # Gate before the backend: the version is joined into a pack
            # filename downstream, and the loader's own ValueError is not in
            # our voice.
            raise ValueError(
                f"unsupported_python_version: {python_version[:16]!r}. "
                f"Supported: {', '.join(SUPPORTED_PYTHON_VERSIONS)}."
            )
        try:
            document = await resolved_backend.language_terms(
                language=lang, python_version=python_version
            )
        except EngineError as exc:
            # Sanitized upstream; safe to surface as the resource error.
            raise ValueError(f"{exc.code}: {exc}") from exc
        return json.dumps(document, ensure_ascii=False, indent=2)

    @server.resource("legesher://languages/{lang}/terms", mime_type="application/json")
    async def language_terms(lang: str) -> str:
        """Full term dictionary for one language (default Python version)."""
        return await _terms_document(lang, DEFAULT_PYTHON_VERSION)

    @server.resource(
        "legesher://languages/{lang}/terms/{python_version}", mime_type="application/json"
    )
    async def language_terms_for_version(lang: str, python_version: str) -> str:
        """Full term dictionary for one language at a specific Python version.

        The explicit-version form of the resource above, for callers pinned to
        a grammar other than the default — pack contents differ by version
        (`match`/`case` in 3.10, `except*` in 3.11, and so on).
        """
        return await _terms_document(lang, python_version)

    # -- prompts --------------------------------------------------------------

    @server.prompt(name="explain-in", title="Explain code in a language")
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

    @server.prompt(name="translate-review", title="Translate and review a source pair")
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

    @server.prompt(name="legibility-report", title="Codebase legibility report")
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

    return server


def create_http_app(
    *,
    backend: Backend | None = None,
    gate: EntitlementGate | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> Starlette:
    """The server as an ASGI app serving the streamable HTTP transport.

    For embedding: a deployment mounts this behind its own middleware —
    TLS termination, authentication, and a wrapper that resolves the
    caller and exposes it to the entitlement gate via
    :func:`legesher_mcp.gate.request_context`. The app is stateless
    (every request self-contained, no server-held session) and answers
    with plain JSON, and it validates the ``Origin`` header against
    ``host`` when the header is present (see
    :func:`_transport_security_for`).

    The returned Starlette app owns a lifespan that must run (any ASGI
    server does this; an in-process harness has to enter it explicitly).
    """
    return create_server(backend=backend, gate=gate, host=host, port=port).streamable_http_app()


#: The default server: local backend, no gate — what stdio serves and what
#: the test suites exercise. Local and self-hosted use is never gated.
mcp = create_server()


#: Binds that mean "every interface". The open HTTP entry has no
#: authentication, so refusing these is a guardrail, not a limitation: a
#: deployment that genuinely wants a wide bind fronts the ASGI app from
#: create_http_app() with its own auth instead.
_WILDCARD_HOSTS = frozenset({"", "0.0.0.0", "::", "[::]"})  # noqa: S104  # nosec B104


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """The console entry's arguments: transport, and where HTTP binds."""
    parser = argparse.ArgumentParser(
        prog="legesher-mcp",
        description=(
            "Legesher MCP server. Runs on stdio by default (what MCP client "
            "configs spawn); --transport streamable-http serves the same "
            "tools over HTTP on one interface, loopback by default."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="Transport to serve (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help=(
            "Interface for streamable-http (default: 127.0.0.1). One "
            "concrete interface only; wildcard binds are refused."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for streamable-http (default: 8000).",
    )
    args = parser.parse_args(argv)
    if args.host in _WILDCARD_HOSTS:
        parser.error(
            "refusing a wildcard bind: the HTTP entry has no authentication, "
            "so it binds one concrete interface (default 127.0.0.1). To serve "
            "beyond localhost, bind that interface's address explicitly — or "
            "put your own auth in front via create_http_app()."
        )
    return args


def main() -> None:
    """Run the Legesher MCP server (local engine, no telemetry).

    stdio by default; ``--transport streamable-http`` serves the same
    server over HTTP, bound to ``--host``/``--port``.
    """
    args = _parse_args()
    if args.transport == "streamable-http":
        create_server(host=args.host, port=args.port).run(transport="streamable-http")
        return
    mcp.run(transport="stdio")
