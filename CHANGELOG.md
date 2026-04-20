# Changelog - Legesher Monorepo

All notable changes to the Legesher project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Changed

- **core + i18n**: `mypy --strict` now passes on the public API surface (19 files
  across `legesher_core`, `legesher_i18n`, and `legesher-language-server`). Closed
  ANN201/ANN001 gaps on public signatures, added precise `dict[str, Any]` /
  `list[tuple[str, str]]` annotations, and typed the lazy-import factory helpers
  in `language_interface.py` via `TYPE_CHECKING` imports. Tightened
  `create_translator`'s and `create_translator_from_config`'s `builtin_map`
  parameter from `BuiltinMap | None = None` to required `BuiltinMap` — the
  previous Optional annotation was a lie, since `TokenMapper` explicitly
  rejects both `None` and `{}`, so every caller would eventually raise at
  runtime. Added `py.typed` markers to `legesher_core` and `legesher_i18n`
  (plus the required `[tool.pdm.build]` config in `libs/core/pyproject.toml`
  so the marker ships in the wheel) for PEP 561 support. Internal helpers
  (`tree_sitter/` extractor/parser/identifier_validator) and body-level
  `translator.py` issues remain out of scope per the issue description.
  (CORE-1183)
- **core**: Declare `pyyaml>=6.0` as a direct dependency of `legesher-core`.
  `legesher_core.metadata` imports `yaml` but `pyyaml` was only reaching the
  installed environment transitively via `legesher-i18n`. Making the
  dependency direct tightens the declared contract so `legesher-core`
  doesn't break if that transitive path ever changes. No lockfile
  additions. (CORE-1183, PR #226 review)
- **language-server**: Loosen the 1.2× threshold in
  `TestCompletionProviderPerformance::test_completion_caching_performance` to
  2.0×. The test measures microsecond-scale durations where `perf_counter()`
  resolution and GC jitter dominate on shared CI runners; the tighter
  threshold flaked intermittently on GitHub Actions. 2.0× still captures the
  intent ("caching does not make things slower") without the noise.
  (CORE-1183, PR #226 CI unblock)
- **docs**: Google-style docstrings filled in for the public API surface that PyPI
  consumers encounter via `help(symbol)` and IDE hover — `legesher_core` classes
  (`TranslationScope`, `TranslatorBackend` type alias), `legesher_i18n` classes
  (`LanguagePackLoader`, `PromptBuilder`, `StyleGuideLoader`, `LanguagePackMetadata`,
  `LanguagePackSchema`, `SchemaValidator`, `PythonVersionDetector`, `PythonVersionInfo`,
  `VersionIndex`), and the `legesher-language-server` module docstring. Each public
  symbol now has structured `Args`, `Returns`, `Raises`, `Attributes`, and `Example`
  sections where applicable, with translation-ready prose suitable for the future
  multilingual API reference pipeline. Docstring-only — no behavior changes.
  (CORE-1173, #225)

## [0.9.2] - 2026-04-20

### Fixed

- **i18n**: Collapse duplicate `__all__` assignment in `legesher_i18n/__init__.py`.
  Python was re-binding on the second assignment so the first list was dead code, and
  the two lists had silently drifted — `PromptBuilder` and `StyleGuideLoader` were
  missing from the live `__all__`, and `load_language_pack` was missing from the dead
  one. `from legesher_i18n import *` now correctly includes all 30 exported names.
  Direct imports (`from legesher_i18n import PromptBuilder`) were unaffected.
  (CORE-1174, #224)

## [0.9.1] - 2026-04-17

### Changed

- **ci**: Split lint and test jobs out of `release-foundation.yml` and
  `release-language-packs.yml` into a new unified `.github/workflows/ci.yml`
  (CORE-1122). The new workflow runs on `pull_request` and `push` to main, giving
  contributors fast automated feedback on PRs for the first time. Release
  workflows now only handle the release pipeline. PR runs use a tiered matrix
  (ubuntu-only) to save credits; push-to-main keeps the full matrix as a
  pre-merge safety net. Concurrency control cancels stale PR runs on new pushes
  but never cancels main runs. Unblocks PR #207 (CORE-388/389/390) — its
  Codecov integration can activate once rebased on new main.

### Fixed

- **legesher**: `ruff format` drift on `libs/legesher/tests/unit/test_cli_translate.py`
  cleared to keep the new PR-triggered CI green on its first run (CORE-1122).

## [0.9.0] - 2026-04-10

### Added

- **language-server**: Context-aware semantic tokens for class names, function names, and
  first parameter (self/cls) in translated code — adds a state machine to the tokenizer
  that colors `ListaCompleta` as a class name after `clase`, `__init__` as a function name
  after `definir`, and `propio` as a parameter after `(` (CORE-895, #199)

### Security

- **repo**: Pre-open-source security audit remediations (CORE-721, #206) — harden
  `.gitignore` with crypto/credential file patterns (`*.key`, `*.pem`, `*.p12`, `*.pfx`,
  `credentials.json`, `secrets/`), re-enable CodeQL workflow with push/PR/weekly triggers
  (was `workflow_dispatch` only), and remove private Linear workspace URLs from source
  code and documentation. Full audit found no secrets in git history, clean OWASP review,
  and license boundary intact.

## [0.8.1] - 2026-04-03

## [0.8.0] - 2026-04-02

### Added

- **language-server**: Extend semantic tokens to highlight translated builtins and exceptions —
  builtin types (`int`/`str`/`float`) colored as teal, builtin functions (`print`/`input`/`len`)
  as yellow, exceptions (`ValueError`/`errordevalor`) as green (CORE-709, #194)
- **i18n**: Per-language style guides and PromptBuilder for context-aware LLM translation
  prompts (CORE-706, #193)
- **core**: Full LLM-powered code translation — translate identifiers, comments, docstrings,
  and string literals via pluggable LLM backends (AYA-191, #189)
  - `LLMTranslator`: composes TreeSitterTranslator (keywords/builtins) with LLM backend
  - `TranslatableExtractor`: AST walker extracting all translatable elements with context
  - `IdentifierMap`: cross-file/cross-language translation glossary with JSON persistence
  - `IdentifierValidator`: Python identifier validation with RTL/Unicode support
  - `TranslationLogger`: JSONL training data collection for future model fine-tuning
  - `TextTranslationBackend` protocol: dependency inversion for LLM backends
  - `TranslationScope`: toggle translation of identifiers/comments/docstrings/strings
- **i18n**: Cohere Aya API translation provider for hosted Aya models (AYA-191)
- **i18n**: OpenAI-compatible translation provider for local models — works with vLLM,
  Ollama, llama.cpp, LocalAI, or any `/v1/chat/completions` endpoint (AYA-191)
- **i18n**: `ProviderBackendAdapter` bridging async TranslationCoordinator to sync
  TextTranslationBackend protocol (AYA-191)
- **cli**: `--full` flag for `legesher translate` enabling LLM translation (AYA-191)
- **cli**: `--llm-backend` option (anthropic, cohere-aya, openai-compat) (AYA-191)
- **cli**: `--llm-base-url` for custom OpenAI-compatible endpoints (AYA-191)
- **cli**: `--identifier-map` for cross-file translation consistency (AYA-191)
- **cli**: `--checkpoint` for resuming interrupted batch translation jobs (AYA-191)

### Fixed

- **core**: Escape closing quote sequences in LLM string/docstring translations to prevent
  breaking out of string literals (AYA-191)
- **core**: Handle multi-line LLM comment responses by prefixing each line with `#` (AYA-191)
- **core**: F-string `string_content` nodes reconstructed as raw text instead of
  re-wrapping in quotes (AYA-191, #191)
- **core**: Comment text sent to LLM without `#` prefix, preventing double `##` in output (AYA-191, #191)
- **i18n**: Cohere/OpenAI-compat provider exceptions wrapped in `TranslationError` for
  coordinator fallback handling (AYA-191)
- **i18n**: OpenAI-compat provider handles `base_url` with or without `/v1` suffix (AYA-191)
- **i18n**: Batch adapter returns original text for failed translations, preventing
  IdentifierMap poisoning with empty strings (AYA-191)
- **cli**: `--full` mode enforces English source (`--from en`) with clear error (AYA-191)
- **cli**: Provider name mapping for `--llm-backend` CLI values (AYA-191)

## [0.7.3] - 2026-03-19

### Language Pack Versions

| Pack           | Version | Changed? |
| -------------- | ------- | -------- |
| i18n-python-zh | 0.0.4   | Yes      |
| i18n-python-es | 0.0.3   | Yes      |
| i18n-python-ur | 0.0.2   | Yes      |

### Fixed

- **i18n-python-zh**: 33 translation corrections from native speaker review (NextME14) — removed
  English words (`elseif`, `ValueError`, `Nosuchfileordirectory`), fixed meaningless characters
  (`玪抑` for lambda), standardized Unicode exceptions to use `统一码` (AYA-160)
- **i18n-python-es**: 5 quality fixes — replaced placeholder text (`eltérminotraducido`),
  non-words (`ipsislo`), and verbose descriptions with proper Spanish translations (AYA-160)
- **i18n-python-ur**: Applied 2 native speaker ([@rafaym1](https://github.com/rafaym1))
  suggestions — `type` and `userwarning` translations updated (AYA-160)

### Added

- Community review translation suggestions added to translations.db for zh, ur, and es
  with source `community_review` (NextME14 zh review,
  [@sarr266](https://github.com/sarr266)/[@rafaym1](https://github.com/rafaym1)
  ur reviews, Universal Python ur alternatives, Latino es alternatives)

## [0.7.2] - 2026-03-18

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.9.2   | Yes      |
| legesher-i18n            | 0.9.2   | —        |
| legesher (CLI)           | 0.9.2   | —        |
| legesher-language-server | 0.1.2   | —        |
| legesher-vscode          | 0.1.5   | —        |
| legesher-home            | 0.1.0   | —        |

### Fixed

- **legesher-core**: Fix TreeSitterTranslator crashing on ~0.6% of Python files with
  non-UTF-8 bytes in string literals when translating to multi-byte languages (CORE-799)

## [0.7.1] - 2026-03-16

## [0.7.0] - 2026-03-16

### Added

- **legesher-i18n**: 22 new language packs — expanding Legesher from 29 → 51
  supported languages (CORE-675, CORE-707)
  - Bengali, Bosnian, Catalan, Croatian, Czech, Galician, Gujarati, Irish,
    Kannada, Latvian, Macedonian, Malayalam, Mongolian, Burmese, Persian,
    Romanian, Scottish Gaelic, Serbian, Sundanese, Telugu, Uzbek, Welsh
  - 3,850 new translations with zero collisions across all 51 languages
  - Each pack: 37 keywords, 72 builtins, 66 exceptions (Python 3.10–3.14)
  - Translation sources: Aya-101 AI Model (21 packs), Claude AI (Bosnian)
  - Persian (fa) is the 4th RTL language; 3 Celtic languages added (ga, gd, cy)

### Changed

- Updated all documentation, tests, and configuration references from 29 → 51
  languages across root CLAUDE.md, README.md, libs/i18n, libs/legesher,
  libs/vs-code, and docs site

## [0.6.0] - 2026-03-11

### Added

- **legesher-i18n**: 3 new language packs — Amharic (am), Sinhala (si), and Urdu (ur),
  expanding Legesher from 26 → 29 supported languages (CORE-687)
  - **Amharic (አማርኛ)**: First Ge'ez-script language in Legesher — 37 keywords,
    72 builtins, 66 exceptions across Python 3.10–3.14 (CORE-690)
  - **Sinhala (සිංහල)**: First South Asian script language — 37 keywords,
    72 builtins, 66 exceptions across Python 3.10–3.14 (CORE-1128)
  - **Urdu (اردو)**: Third RTL language (joining Arabic and Hebrew) — 37 keywords,
    72 builtins, 66 exceptions across Python 3.10–3.14 (CORE-1071)
  - Zero translation collisions across all 29 languages
  - 540 new translations added to the translation database
- **legesher-i18n**: Generic HuggingFace translation engine with pluggable model profiles,
  enabling new AI translation models to be added with ~10 lines of config (CORE-686)
  - Local inference engine with lazy model loading and device auto-detection
    (CUDA/MPS/CPU)
  - HF Inference API engine with rate limiting for cloud-based translation
  - 4 pre-registered Tiny Aya (3.35B) profiles for underserved languages
  - New CLI flags: `--models hf|hf-api|tiny-aya|tiny-aya-api`,
    `--hf-profile <name>`, `--tiny-aya-variant earth|fire|water|global`
- **docs**: Vercel deployment for docs.legesher.io with Astro adapter (CORE-1194)

## [0.5.1] - 2026-03-01

> Includes changes from individually-released packages since v0.5.0:
> vs-code 0.1.2–0.1.5, language-server 0.1.2.

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.7.1   | Yes      |
| legesher-i18n            | 0.7.1   | Yes      |
| legesher (CLI)           | 0.7.1   | —        |
| legesher-language-server | 0.1.2   | Yes      |
| legesher-vscode          | 0.1.5   | Yes      |
| legesher-home            | 0.1.0   | —        |

### Added

- **legesher-i18n**: Consolidate 3 translation databases into normalized
  4-table schema with `selected_translations` tracking (CORE-594)
- **legesher-language-server**: Bilingual hover format showing English docs
  first, then target language translation

### Fixed

- **legesher-core**: Replace `datetime.UTC` with `timezone.utc` for
  Python 3.10 compatibility (CORE-662)
- **legesher-i18n**: Resolve 41 translation collisions across 17 languages
  where the same translated word mapped to 2+ Python terms, breaking
  round-trip translation (CORE-605)
  - Add `find_collisions()` API and `db collisions` CLI command
  - Add collision guard to `set_selected()` preventing future collisions
  - Upgrade pre-commit YAML validator from warnings to errors for duplicates
  - Bump affected language packs to v0.0.3: ar, el, fi, he, hi, hu, it,
    ko, no, pl, pt, ru, sv, th, tr, vi, zh
- **legesher-language-server**: Add MIT LICENSE file (CORE-622)
- **legesher-language-server**: Fix invalid author email domain (CORE-665)
- **legesher-vscode**: Fix Translation View showing English on both
  panels — bundle language pack YAML files in VSIX (CORE-602)
- **legesher-vscode**: Fix telemetry pipeline — zero events reaching
  Azure Application Insights (CORE-590)
  - Bundle `@vscode/extension-telemetry` instead of externalizing it
  - Add try/catch error handling to all 11 telemetry methods, PII
    sanitization, type-safe union types
  - Add missing telemetry to LSP errors, translation failures, feedback
    responses, server-not-installed path
  - Remove `/tmp/env-debug.log` security artifact, filesystem paths from
    log messages
  - Add feedback `Logger.info` calls, telemetry diagnostic logging,
    build validation in preview script
  - Remove dead code (`trackWalkthroughStep`, unused feature values) —
    tracked in CORE-591, CORE-592

### Changed

- **CI**: Auto-stamp changelogs on foundation release (CORE-608)
  - Add `scripts/stamp-changelog-release.py` to stamp `[Unreleased]`
    headings and update Package Versions table
  - Add stamp step to `release-foundation.yml` workflow
- **legesher-vscode**: Release v0.1.2 with marketplace improvements
  (CORE-558)
  - Add extension icon for better visibility
  - Inject telemetry connection string at build time
  - Fix security issue: remove connection string from logs
  - Update README and marketplace metadata
- **legesher-vscode**: Update dependencies — `@vscode/extension-telemetry`
  1.5.0 → 1.5.1, `@vscode/vsce` 2.32.0 → 3.7.1, eslint 8 → 10
- **legesher-language-server**: Consolidate hover provider
  `LanguagePackLoader.load()` calls (4 → 1)

## [0.5.0] - 2026-02-01

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.5.0   | Yes      |
| legesher-i18n            | 0.5.0   | Yes      |
| legesher (CLI)           | 0.5.0   | Yes      |
| legesher-language-server | 0.1.1   | Yes      |
| legesher-vscode          | 0.1.1   | —        |
| legesher-home            | 0.1.0   | —        |

### Fixed

- **legesher-i18n**: Fix 33 mixed-script translations across Greek,
  Hebrew, Russian, Arabic, Finnish packs (CORE-531)
- **legesher-i18n**: Fix Japanese `in` keyword invalid identifier, add
  missing `type` builtin to es/ar (CORE-531)
- **legesher-core**: Fix `TokenTranslator` compound keyword (`except*`)
  lookahead handling (CORE-531)

### Changed

- **legesher-language-server**: Bump to 0.1.1 for pygls 2.0 migration
  (CORE-448)
- **legesher-i18n**: Bundle all 26 language pack YAML files directly in
  the i18n wheel (CORE-559)
- **legesher CLI**: Add `legesher config` command (CORE-563),
  non-interactive `legesher init` (CORE-562), fix `--version`
  (CORE-560), dynamic language help text (CORE-561)
- **Docs**: Fix CLI flags `--from`/`--to`, remove non-existent commands,
  update config references (CORE-564–566)
- **CI**: Add cross-platform lint and test workflows

## [0.4.0] - 2026-01-27

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.4.0   | —        |
| legesher-i18n            | 0.4.0   | —        |
| legesher (CLI)           | 0.4.0   | —        |
| legesher-language-server | 0.1.0   | —        |
| legesher-vscode          | 0.1.1   | —        |
| legesher-home            | 0.1.0   | Yes      |

### Changed

- **legesher-home**: Renamed from `legesher-pride` to `legesher-home` (CORE-515)
- Version bump across all foundation packages to 0.4.0

## [0.3.0] - 2026-01-26

### Package Versions

| Package                  | Version       | Changed? |
| ------------------------ | ------------- | -------- |
| legesher-core            | 0.3.0         | —        |
| legesher-i18n            | 0.3.0 (0.2.1) | Yes      |
| legesher (CLI)           | 0.3.0         | —        |
| legesher-language-server | 0.1.0         | —        |
| legesher-vscode          | 0.1.1         | —        |
| legesher-home            | 0.1.0         | —        |

### Added

- **legesher-i18n**: Keyword Registry CLI Tool with export, validate, and REFERENCE.md auto-generation (CORE-555)

## [0.2.0] - 2026-01-26

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.2.0   | —        |
| legesher-i18n            | 0.2.0   | Yes      |
| legesher (CLI)           | 0.2.0   | —        |
| legesher-language-server | 0.1.0   | —        |
| legesher-vscode          | 0.1.1   | —        |
| legesher-home            | 0.1.0   | —        |

### Added

- **legesher-i18n**: Complete all 26 language translations via Aya AI Model pipeline (CORE-530)
- **legesher-i18n**: Python 3.14 language pack support, Spanish YAML boolean fix

## [0.1.1] - 2026-01-23

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.1.1   | —        |
| legesher-i18n            | 0.1.1   | Yes      |
| legesher (CLI)           | 0.1.1   | —        |
| legesher-language-server | 0.1.0   | —        |
| legesher-vscode          | 0.1.1   | Yes      |
| legesher-home            | 0.1.0   | —        |

### Fixed

- **legesher-i18n**: Fix YAML exporter term_type from database (CORE-460)

### Added

- **legesher-i18n**: REFERENCE.md quick guides for all 25 language packs
- **legesher-vscode**: Onboarding dialog, translation panel, language selection, telemetry, feedback system (CORE-477)
- **legesher-vscode**: CI build pipeline with esbuild

### Removed

- **legesher-i18n**: Legacy language pack archives

## [0.1.0] - 2025-11-07

### First Public Release

The inaugural release of Legesher as a unified monorepo, enabling developers to code
in their native language instead of English.

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.1.0   | Yes      |
| legesher-i18n            | 0.1.0   | Yes      |
| legesher (CLI)           | 0.1.0   | Yes      |
| legesher-language-server | 0.1.0   | Yes      |
| legesher-vscode          | 0.1.0   | Yes      |

See individual package changelogs for full details:

- [legesher-core](libs/core/CHANGELOG.md) — Translation engine, git filters, metadata tracking
- [legesher-i18n](libs/i18n/CHANGELOG.md) — Language pack system, translation API, validation CLI
- [legesher (CLI)](libs/legesher/CHANGELOG.md) — translate, git, metadata commands
- [legesher-language-server](libs/language-server/CHANGELOG.md) — LSP with hover, completion, diagnostics
- [legesher-vscode](libs/vs-code/CHANGELOG.md) — VS Code extension with LSP client

---

## Project Overview

### Language Support

- **29 Languages**: am, ar, da, de, el, en, es, fi, fr, he, hi, hu, id, it,
  ja, ko, ms, nl, no, pl, pt, ru, si, sv, th, tr, ur, vi, zh
- **RTL Support**: Full right-to-left text handling for Arabic, Hebrew, and Urdu
- **Version-Aware**: Python 3.10, 3.11, 3.12, 3.13, 3.14 with pack inheritance

### Translation Engine

- **Token-Based Translator**: Preserves all formatting and comments (<2ms per file)
- **Tree-sitter Translator**: AST-based, production-ready (~160us for medium files)
- **Round-Trip Fidelity**: 100% (EN to ES to EN is byte-identical)
- **Git Filters**: Canonical English storage with automatic translation on checkout

### IDE Integration

- **Language Server**: Full LSP with hover, completion, diagnostics, semantic tokens
- **VS Code Extension**: Onboarding, translation panel, language selection, telemetry
- **Editor-Agnostic**: LSP design supports any compatible editor

### CLI Tools

- `legesher translate` — file, directory, and stdin/stdout translation
- `legesher run` — execute native-language Python directly
- `legesher git setup/status` — configure git filter integration
- `legesher config` — project configuration management
- `legesher init` — interactive and non-interactive project setup
- `legesher metadata` — translation history and audit trail

### Infrastructure

- **Monorepo**: UV workspace with 6 packages and pdm-backend builds
- **CI/CD**: Cross-platform lint and test workflows, semantic release
- **Pre-commit**: ruff, markdownlint, YAML validation, changelog enforcement
- **Testing**: 1,686+ automated tests across all packages

---

## Contributors

- **Madison Edgar** ([@madiedgar](https://github.com/madiedgar)) — Lead developer
- **Historical Contributors**: All contributors from the original
  Legesher repositories (2019-2024)

---

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)
- [Documentation](https://docs.legesher.io)

---

**Format**: [Keep a Changelog](https://keepachangelog.com/)
**Versioning**: [Semantic Versioning](https://semver.org/)
**License**: Multi-license (MIT for core packages, see [LICENSE](LICENSE))
