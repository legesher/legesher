# Changelog - legesher-mcp

All notable changes to legesher-mcp are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Added

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
  over generated prose). Free forever, Apache-2.0, no telemetry — the local
  server makes no network calls and emits nothing. [CORE-1175]
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
