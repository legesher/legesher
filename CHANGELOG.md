# Changelog - Legesher Monorepo

All notable changes to the Legesher project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.4.1   | Yes      |
| legesher-i18n            | 0.4.1   | Yes      |
| legesher (CLI)           | 0.4.0   | Yes      |
| legesher-language-server | 0.1.1   | Yes      |
| legesher-vscode          | 0.1.1   | —        |
| legesher-home            | 0.1.0   | —        |

### Fixed

- **legesher-i18n**: Fix 33 mixed-script translations across Greek, Hebrew, Russian, Arabic, Finnish packs (CORE-531)
- **legesher-i18n**: Fix Japanese `in` keyword invalid identifier, add missing `type` builtin to es/ar (CORE-531)
- **legesher-core**: Fix `TokenTranslator` compound keyword (`except*`) lookahead handling (CORE-531)

### Changed

- **legesher-language-server**: Bump to 0.1.1 for pygls 2.0 migration (CORE-448)
- **legesher-i18n**: Bundle all 26 language pack YAML files directly in the i18n wheel (CORE-559)
- **legesher CLI**: Add `legesher config` command (CORE-563),
  non-interactive `legesher init` (CORE-562), fix `--version` (CORE-560),
  dynamic language help text (CORE-561)
- **Docs**: Fix CLI flags `--from`/`--to`, remove non-existent commands, update config references (CORE-564–566)
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

- **26 Languages**: ar, da, de, el, en, es, fi, fr, he, hi, hu, id, it,
  ja, ko, ms, nl, no, pl, pt, ru, sv, th, tr, vi, zh
- **RTL Support**: Full right-to-left text handling for Arabic and Hebrew
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
