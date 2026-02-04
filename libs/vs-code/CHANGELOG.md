# Changelog

All notable changes to legesher-vs-code will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

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
