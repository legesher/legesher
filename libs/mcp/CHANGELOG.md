# Changelog - legesher-mcp

All notable changes to legesher-mcp are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Added

- Registry listing metadata: `server.json` for the official MCP registry
  (PyPI package, `uvx` runtime, stdio transport, the log-level variable),
  the `mcp-name` ownership marker in the README, `[project.urls]` for the
  PyPI page, a VS Code `mcp.json` example beside the other clients, and
  `docs/registry-listings.md` with the canonical copy every directory
  gets. `tests/test_registry_manifest.py` keeps the manifest pinned to the
  package name, version and the variables the server reads. [CORE-1424]
- Remote transport surface — the pieces a deployment composes into a
  remote MCP server, with local stdio behavior unchanged [CORE-1420]:
  - **Backend seam** (`legesher_mcp.backend`): everything a tool call or
    resource read *does* now sits behind the `Backend` protocol — one
    async method per tool plus the two resource reads, returning the
    exact typed results the tools publish, with expected failures raised
    as `EngineError`. `LocalBackend` carries the orchestration formerly
    in the tool bodies, unchanged. The seam sits at the tool level, not
    the engine level, so a remote implementation is one call per method
    against a hosted API and the two deployments cannot drift.
  - **Server factory**: `create_server(backend=..., gate=..., host=...,
    port=...)` assembles the complete server — all six tools, both
    resources plus the versioned terms template, all three prompts,
    descriptions and annotations — from a backend and an entitlement
    gate; `create_http_app(...)` returns it as an ASGI app for mounting
    behind a deployment's own middleware. The module-level server and the
    stdio entry point are now built through the factory with the
    defaults (`LocalBackend`, no gate).
  - **Entitlement gate** (`legesher_mcp.gate`): a default-open policy
    seam. Gated tools stay *listed* for every caller — entitlement is
    checked only at call time — and an unentitled call answers with an
    actionable message (what the tool does, that it requires a Legesher
    account on the hosted instance, and where to go), never an opaque
    failure. Only `map_existing_codebase` is gateable at all, and only
    where a deployment installs a gate; `validate_identifier_translations`
    is permanently free by construction; the stdio entry and the
    self-host HTTP entry never install one. Per-request context reaches
    the gate through `request_context` (a contextvar an ASGI wrapper
    sets), and the denial copy ships in this package.
  - **Streamable HTTP entry**: `--transport streamable-http` on the
    console script, with `--host` (default `127.0.0.1`; wildcard binds
    are refused) and `--port` (default 8000). Stateless — every request
    self-contained — with plain JSON responses, and the `Origin` header
    validated against the bound interface when present (DNS-rebinding
    defense; a mismatch is rejected with 403, clients that send no
    Origin pass). Ships no authentication: it is the localhost /
    single-user self-host entry; a multi-tenant deployment mounts
    `create_http_app()` behind its own auth middleware instead.
- `verify_round_trip` flag on both `translate_to_native` and
  `translate_to_source` — ask the engine to prove the translation
  round-trips instead of comparing two renderings by eye. The result gains
  a `round_trip` block (absent entirely when the flag is off) carrying the
  byte-for-byte verdict, a quotable single-line `verdict_line`, and each
  divergence located by line and column and named by the token layer that
  broke it — pack layers (`keywords`/`builtins`/`exceptions`/
  `reserved_words`) mean a pack or engine defect, `collision` is an
  identifier spelled like a pack rendering, `identifiers` is expected
  residue, `comments`/`strings` are the caller's own drift. `verified`
  lists only the layers the source actually exercised and came back clean
  — a clean run claims nothing about layers it never touched (coverage
  widens under CORE-1841). `forward_valid` reports whether the canonical
  form compiles, catching the collision that cancels itself on the way
  back; it is `null` when the forward rendering is not English, since the
  compile fact would be unknowable rather than assumed. Divergence
  snippets are truncated to 200 characters with a `truncated` marker, so
  a long line never ships the file back through its own diff. The flag
  doubles translation cost (quadruples via a pivot) and never changes the
  translation itself; a same-language round trip is refused as
  `vacuous_round_trip` rather than reported as a verification it never
  performed.
- `validate_identifier_translations` — the deterministic layer for the part
  of localized code that has no pack. Keywords are dictionary lookups;
  identifiers are invented by the model, so this is the check they get
  instead. Given proposed source/translation pairs it reports five
  failures: `malformed` (not a valid Python identifier), `unsafe_text`
  (bidi controls and invisibles, via the shared Unicode guard, with the
  target language's `script_policy` allowing the format characters its
  script actually needs — Sinhala joins consonants with virama+ZWJ, so
  U+200D is orthography there and a blanket rejection would refuse the
  vocabulary Legesher itself ships),
  `reserved_term` (a name the pack claims — exact *and* NFKC+casefold, so
  a case variant of `definir` is caught too), *drift* — one concept
  acquiring a second term — and *collision* — one term acquiring a second
  concept. Drift and collision are checked against the existing glossary
  and against the rest of the batch, so a first session with no glossary
  yet still has to be self-consistent, and comparison is NFKC+casefold so
  a decomposed twin is the same term rather than a second one. Both sides
  of a pair are checked, not just the translation: an `accepted` key is
  described as ready to merge into your glossary, so a source that is not
  itself an identifier is rejected rather than seeded as a key nothing in
  code can match. The conflict-free pairs come back in `accepted`,
  NFC-normalized per the storage contract.

  The pack, Unicode, and well-formedness checks are the ones
  `register_map.correction` already applies to register-map identifier
  entries, reusing `IdentifierValidator`, the Unicode guard, and
  `compare_key` rather than re-deriving them — a different artifact, but
  the same question about what makes a rendering legal. The tool sees only
  what you pass it, so it cannot speak for checks that need the register
  map itself: homonyms and retired aliases stay `legesher map --edit`'s to
  catch.

  Recording is the caller's: the server takes the glossary as content,
  returns a mapping, and writes nothing — the local server's no-filesystem
  posture is unchanged and all six tools remain read-only. In a repo, that
  file is `.legesher/identifier_map.json`, which the `legesher` CLI already
  maintains. [CORE-1670]

- Independent release train. `legesher-mcp` now versions itself: its own
  `[tool.semantic_release]` config, `mcp-v{version}` tags, and
  `release-mcp.yml` triggered by changes under `libs/mcp/`. It no longer
  inherits the foundation suite's version or bumps when the foundation
  releases. `major_on_zero` is off, so a breaking change goes 0.1.0 → 0.2.0
  and 1.0.0 stays a deliberate promotion. The release-tier suites run as a
  gate *before* the version step, which makes the clean-environment wheel
  spawn test a real gate on cutting a release rather than a checklist item.
  [CORE-1851]
- MCP tests run in CI. `libs/mcp` was absent from `ci.yml`, so its suite had
  never run there; it now runs on every PR with coverage reported to Codecov.
  [CORE-1851]
- All five tools declare MCP annotations matching their actual posture —
  `readOnlyHint`, `idempotentHint`, `destructiveHint: false`, and
  `openWorldHint: false` — so clients can reduce or skip approval prompts
  for a server that never writes, never executes submitted code, and never
  opens a socket. A surface-lock test asserts them. [CORE-1814]
- `legesher://languages/{lang}/terms/{python_version}` — the term dictionary
  for a specific Python grammar. The unversioned URI still resolves to the
  default version. [CORE-1806]
- Release-tier test suites, excluded from the default run and available as
  `make test-mcp-scheduled`: an all-packs round-trip sweep asserting the
  byte-identical guarantee through an MCP session across every installed
  pack [CORE-1745], and a clean-environment spawn test that builds the
  wheels, installs them into a fresh virtualenv in an empty directory, and
  drives a stdio session with a stripped environment — a publish gate, since
  it is what proves the artifact works outside the workspace [CORE-1746].
- Agent-session artifacts for localized code (CORE-1421, CORE-1422):
  `templates/AGENTS-template.md` — the copy-into-your-repo `AGENTS.md`
  language-policy declaration (eight rules: write natively, keywords only
  through the deterministic tools, one-concept-one-term naming backed by a
  project glossary table, and the byte-identical round-trip guarantee) —
  and `skills/legesher-localized-code/SKILL.md`, the Agent Skills-format
  stable-knowledge playbook (mental model, tool selection, the
  write → round-trip → validate workflow, naming discipline, long-session
  drift recovery). README section explains the split: the policy file and
  skill are the declaration/playbook half, the server's deterministic
  tools are the guarantee.

- Initial Legesher MCP server package: the engine's translation capability
  as a Model Context Protocol stdio server, per the CORE-1165 architecture
  design (five coarse tools, resources over tool-shaped reads, engine facts
  over generated prose). Free forever, Apache-2.0; every tool call is
  served by the local engine. [CORE-1175]
  - **Tools**: `translate_to_native` (files and fragments alike; X→Y pivots
    through English and reports `pivoted`), `translate_to_source` (fixed to
    the English pivot), `explain_in_language` (deterministic engine facts:
    per-construct mappings + compile-only validation; the calling model
    writes the prose), `lookup_keyword_mapping` (term quick-reference with
    canonical PascalCase exception spellings), and `map_existing_codebase`
    (per-file legibility report — translatability, construct counts,
    unmapped constructs, aggregate coverage — orchestrating per-file
    translate + validate).
  - **Resources**: `legesher://languages` (catalog with pack availability)
    and `legesher://languages/{lang}/terms` (full dictionary).
  - **Prompts**: `explain-in`, `translate-review`, `legibility-report`.
  - **Entry point**: `legesher-mcp` console script (stdio transport) so
    `uvx legesher-mcp` / `uv run legesher-mcp` work; official `mcp` Python
    SDK (FastMCP) pinned `>=1.16.0,<2.0.0`.
  - **Error hygiene**: tool errors carry a machine code
    (`unsupported_language`, `language_pack_not_found`, `invalid_source`)
    with generic messages — no stack traces, filesystem paths, or echoed
    source; language codes pass the registry pattern before any pack
    resolution (path-traversal guard); validation is `compile()`-only.
  - **Tests**: 36 tests exercising every tool, resource, and prompt through
    the MCP layer (SDK in-memory session plus one real stdio subprocess),
    including unsupported-language, pack-not-found, oversized-input, and
    malformed-input paths.

### Changed

- **The no-telemetry promise is withdrawn.** The README, the package
  docstring and the server's MCP instructions said the stdio server would
  never emit telemetry ("emits no events, pings, or metrics of any kind").
  That claim is retracted ahead of the code: a coming release adds optional
  usage telemetry (tool name, call count, error class, server and engine
  versions, a random install id; never source, identifiers, translated
  text, prompts or paths), off by default and enabled only by
  `LEGESHER_MCP_TELEMETRY=on`, with `DO_NOT_TRACK=1` or
  `LEGESHER_TELEMETRY_DISABLED=1` always honoured. This version still
  sends nothing. The wording changes first so that no public
  release carries a promise the next one breaks. The published surface
  digest moves with the instructions text. [CORE-2252]
- Engine failures (and gate denials) now surface as their machine code
  directly — `unsupported_language: ...` — instead of inside the SDK's
  `Error executing tool <name>: ...` wrapper, so the code stays first,
  which is what tool-calling models key on. [CORE-1420]
- Pack availability is now refreshable instead of computed once per process:
  the scan expires after a TTL, and `LocalEngine.refresh_packs()` drops
  every pack-derived cache explicitly. A pack installed mid-session is
  picked up without a restart — irrelevant for a stdio lifetime, wrong for
  a long-lived server. [CORE-1806]
- The `python_version` enum published in every tool schema is derived from
  the installed packs' version index rather than hand-maintained, so packs
  for a new Python version need no schema edit. [CORE-1806]
- Argument-validation failures now speak in the server's own voice —
  `invalid_arguments: <field> — <constraint>`. The SDK's raw pydantic dump
  quoted the rejected value back, which for the `source` fields meant a
  prefix of the caller's code appeared in the error. Field names and
  constraints are kept; values are not. [CORE-1744]
- Unexpected failures (including engine-boot failures) collapse to a generic
  `internal_error` instead of surfacing an exception message that can carry
  filesystem paths. [CORE-1744]

### Fixed

- The `legesher://languages/{lang}/terms` resources now check the language
  code against the registry pattern *before* any backend sees it, matching
  the guard the tool parameters have always had. A resource URI carries no
  argument model, so whatever matched the URI template's `[^/]+` reached
  the backend verbatim — harmless against the local backend, which
  allowlists the code before it touches a pack, but a backend is free to
  put that value in a request path, and a value carrying `?`, `#`, or an
  encoded traversal could then move the request somewhere nobody chose. A
  well-formed code the catalog does not list still reaches the backend and
  is refused there, so registry membership stays the backend's call.
  [CORE-1423]

- `explain_in_language` and `map_existing_codebase` computed the English
  pivot twice per file when the input was not English — once to scan and
  validate, then again inside the X→Y translation. The second hop now
  starts from the pivot form already computed, roughly halving the
  translation work on non-English input. [CORE-1806]
- The stdio server identifies itself truthfully and quietly — the MCP
  `initialize` handshake reports `legesher-mcp`'s own package version
  instead of the SDK's [CORE-1737], and the default log level is WARNING
  so a normal session writes no log noise to stderr; set
  `LEGESHER_MCP_LOG_LEVEL` (DEBUG…CRITICAL) to restore verbose logging for
  troubleshooting [CORE-1738]. The reported version now reads from the
  installed distribution's metadata, so it cannot drift from the version
  in the wheel. [CORE-1749]
