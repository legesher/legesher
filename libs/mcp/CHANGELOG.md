# Changelog - legesher-mcp

All notable changes to legesher-mcp are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Added

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
