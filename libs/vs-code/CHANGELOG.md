# Changelog

All notable changes to legesher-vs-code will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## 0.1.5 (2026-03-01)

### Changed

- **Dependencies**: Update `@vscode/extension-telemetry` 1.5.0 → 1.5.1
- **Dependencies**: Update `@vscode/vsce` 2.32.0 → 3.7.1, eslint 8 → 10, mocha 10 → 11, sinon 19 → 21
- **Dependencies**: Pin `@types/node` to ^20.0.0 and `@types/vscode` to 1.85.0 (match runtime targets)
- **Dependencies**: Update esbuild 0.24.2 → 0.27.3, dotenv 17.2.3 → 17.3.1

## 0.1.4 (2026-02-10)

### Fixed

- **Translation View**: Fix both panels showing English — language pack YAML files now bundled in VSIX (CORE-602)
  - Add `copyLanguagePacks()` to esbuild build process to copy 26 base `3.10.yml` files into extension root
  - Fix `getLanguagePacksPath()` fallback returning unchecked non-existent path
  - Production builds fail-fast when language packs source is missing
  - Log-once diagnostics for path resolution errors and missing translations
  - Idempotent builds with stale `language-packs/` cleanup
  - `.vscodeignore` safeguard comment protecting `language-packs/` from exclusion

## 0.1.3 (2026-02-09)

### Fixed

- **Telemetry Pipeline**: Fix zero events reaching Azure Application Insights (CORE-590)
  - Bundle `@vscode/extension-telemetry` instead of externalizing it — root cause of zero events
  - Inject connection string at build time (production only), runtime env for development
  - Add try/catch error handling to all 11 telemetry methods
- **Missing Telemetry**: Add tracking to previously untracked error paths
  - LSP server errors and connection drops (`client.ts`)
  - Translation panel failures (`panel.ts`)
  - Server not installed path (`extension.ts`)
  - Feedback prompt responses — gave feedback, deferred, opted out (`feedback.ts`)
- **Security**: Remove `/tmp/env-debug.log` debug artifact from `env.ts` that leaked extension paths
- **PII Leakage**: Remove filesystem paths from `env.ts` log messages
- **Telemetry Logging**: Fix misleading telemetry disabled message; `trackActivation` returns silently when reporter is undefined
- **Build Script**: Use case-insensitive grep for connection string validation
- **Tests**: Remove stale walkthrough step tests referencing dead code

### Added

- **Feedback Telemetry**: New `trackFeedbackResponse()` method tracks user responses to feedback prompts
- **Feedback Logging**: Add `Logger.info` calls to feedback.ts for local debugging when telemetry is disabled
- **Build Validation**: Preview release script validates telemetry module is bundled and connection string embedded
- **PII Sanitization**: `trackError()` strips file paths and email addresses before sending
- **Type-Safe Parameters**: `TrackedCommand`, `TrackedErrorType` union types restrict parameters to known values
- **Telemetry Diagnostics**: Log `isTelemetryEnabled`, reporter type, and active status during initialization
- **Tests**: PII sanitization tests (Unix paths, Windows paths, emails, multiple occurrences, safe contexts)

### Changed

- **Dead Code Removal**: Remove unused `trackWalkthroughStep` and `WalkthroughStepId` (moved to CORE-591)
- **Feature Types**: Remove unused `diagnostic` and `run` feature values (moved to CORE-592)
- **.vscodeignore**: Reorganized with section comments; added `.env` exclusion from `.vsix` package

## 0.1.2 (2026-02-04)

### Added

- **Interactive Walkthrough**: 6-step onboarding experience for first-time users
  - Welcome introduction to Legesher
  - Installation guide linking to preview-repo docs
  - Language selection with command integration
  - Translation panel demo with sample Python code
  - Hover translation tutorial
  - Feedback collection step
- **Try Translation Panel Command**: Demo command that creates sample Python file and opens translation panel
- **Walkthrough Telemetry**: Track walkthrough opens and step completions
- **Extension Icon**: Added marketplace icon for better visibility
- **Production Telemetry**: Build system now embeds telemetry connection string for packaged releases
- **Walkthrough Tests**: Comprehensive tests for sample code validation and step configuration

### Changed

- **Onboarding Flow**: Replaced dialog-based welcome with native VS Code walkthrough
- **ML Consent Dialog**: Simplified to single-line message for better popup display
- **Privacy URL**: Updated to point to GitHub PRIVACY_POLICY.md
- **Feedback URL**: Default to legesher.io/go/vs-code-extension-survey
- **Marketplace Metadata**: Updated categories to include "Language Packs", improved keywords for discoverability
- **README**: Rewritten with installation links to preview-repo docs
- **Build System**: Added dotenv integration to inject telemetry connection string at build time

## 0.1.1 (2026-01-27)

### Added

- **Onboarding Dialog** (CORE-477)
  - Welcome dialog on first Python file open with language selection
  - ML training consent dialog (opt-in, GDPR compliant)
  - Reset onboarding command for testing
  - "Learn More" link to privacy documentation

- **Translation Panel** (CORE-361)
  - Side-by-side English/translated code view
  - Syntax highlighting via Prism.js
  - Copy button with feedback
  - Accessible from context menu and editor title bar

- **Language Selection**
  - Status bar language indicator
  - Quick-pick menu with 26 languages
  - Command palette language selection

- **Telemetry & Feedback System**
  - Anonymous usage telemetry via Azure Application Insights
  - Separate ML training consent toggle
  - Feedback command with sentiment selection
  - Respects VS Code global telemetry settings

- **Semantic Token Highlighting**
  - Python keyword, class, function, variable, and parameter scopes

### Changed

- **Build System**: Migrated to esbuild for faster builds
- **CI**: Added Node.js build pipeline replacing VS Code release workflow

## 0.1.0 (2025-11-07)

### Added

- Initial TypeScript extension setup with LSP client [CORE-361]
- Extension activation on Python files
- Language server connection via JSON-RPC
- Status bar indicator showing connection status
- Configuration settings for server command and tracing
- Restart language server command
- Comprehensive error handling and user feedback
- Complete documentation (README, CONTRIBUTING)
- TypeScript project structure with ESLint and build scripts
