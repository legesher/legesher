# Changelog

All notable changes to legesher-vs-code will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## Unreleased

### Added

- **Unicode highlighting**: a translated file no longer opens covered in warnings. VS Code's
  ambiguous-character check reports Arabic Alef (U+0627) as a likely impersonation of Latin `l`,
  Cyrillic small a (U+0430) of `a` and Turkish dotless i (U+0131) of `i`, so it fired on nearly every
  identifier in a Legesher file. When such a file is on screen the extension now offers, once, to add
  `editor.unicodeHighlight.allowedCharacters` to **that workspace's** settings — carrying only the
  characters that file's own language pack uses that VS Code would otherwise flag, which is two for
  Arabic, one for Amharic, twelve for Russian. `Don't Ask Again` suppresses the offer everywhere,
  `Not Now` defers it to the next session. Nothing is read from or written to your own settings and
  no `configurationDefaults` ship, so the check is untouched on every other repository you open:
  invisible- and bidi-character detection stays on and every *other* script's confusables stay
  flagged. The offer is gated on workspace trust — VS Code registers the setting `restricted: true`,
  so an untrusted repository's allowance is ignored outright, and Legesher neither prompts nor
  writes in one. Legesher's own guards are narrower than the check being relaxed and do not replace
  it: the git clean filter rejects bidi controls, `Cf` and `Default_Ignorable` invisibles, tatweel
  and unsupported-script identifier characters on commit, but nothing at the Legesher layer looks
  for confusables — see the README's "What does not" section.
  `editor.unicodeHighlight.allowedLocales`, the setting this looks like it should use, cannot do the
  job: VS Code's locale table holds only its own display languages, so `{"ar": true}` is discarded
  silently, and its per-locale maps cannot reach the shared table that holds Arabic Alef in any case
  (CORE-1978)
- **Language profile**: the language roles are named — canonical / file / working / known — so one
  setting no longer has to mean both the language a file is written in and the language you want to
  read it in. `legesher.workingLanguage` is the language you read and write in;
  `legesher.knownLanguages` is the set you read comfortably, seeded from your working language so
  nothing needs configuring to start. A `Legesher: Manage My Languages` command edits the known set,
  the language picker lists known languages first under a separator, and a file already written in a
  language you know raises no mismatch signal. The file and working languages are sent to the
  language server as separate slots, so cross-language rendering has somewhere to say which language
  to render into (CORE-1760)

### Deprecated

- **`legesher.targetLanguage`**: replaced by `legesher.workingLanguage`. Still honoured wherever the
  new setting is not set, at its own scope — VS Code precedence (folder > workspace > user) decides
  first, and only within one scope does the new name outrank the old, so a project that pins the old
  key still beats your global preference. Existing configurations keep working with no action needed,
  and choosing a language from the picker migrates the setting for you (CORE-1760)

### Fixed

- **Language selector**: picking a language now takes effect in a project that sets
  `legesher.targetLanguage` in its workspace settings. The pick was written to user settings, which the
  workspace value outranks, so the language never changed while the notification said it had. Each
  setting is now written at the scope that supplies its value, and the notification names that scope
  when it is not your own settings (CORE-1776)
- **Language server**: a failed server start no longer leaves the extension claiming the previous
  language is running. Switching back to that language now restarts the server instead of collapsing
  into a no-op that never retried (CORE-1776)
- **Language server**: a folder- or workspace-scoped `legesher.sourceLanguage` now reaches the server.
  The client re-read the configuration without the document's URI, so it started the server with a
  different pair than the one the extension recorded (CORE-1776)
- **Mixed-language projects**: files written in different languages now work side by side in one
  window. The language server answered in one language at a time, so a file in any other language got
  no highlighting, hover or completion, which looked like the extension had stopped working, and
  switching to it restarted the server. The extension now tells the server each file's language as the
  file opens, and again whenever the language it resolves for that file changes, and the server answers
  each file in its own language. Apart from `Legesher: Restart Language Server`, the server restarts only
  when the configured languages change: a pick from the language selector, or an edit to
  `legesher.workingLanguage` or `legesher.sourceLanguage`.
  Content detection now runs when a Python file opens, not only when its editor is focused. A file
  whose language has no language pack now raises a one-time warning naming that language instead of
  quietly getting nothing (CORE-1976)

### Security

- **Error telemetry**: an error report can no longer carry your home directory off the machine. Every
  event the extension authors is built from an enumerated vocabulary except one property, the text of
  the error itself, and that was scrubbed by two patterns that recognised only `/`-rooted paths. A
  Windows path (`C:\Users\jane\...`), a UNC share (`\\server\share\...`), an IP address, a URL and a
  bare hostname such as `jane-macbook.local` all went through untouched. The scrubber now works the
  other way round: the message is split into tokens and a token has to be recognised as safe to
  survive. Words in any script, numbers, version numbers, the extension's own `legesher.*` setting
  names and `key:value` pairs of safe halves are kept, so the report still says what went wrong;
  anything else is replaced with `<path>`, `<email>`, `<url>`, `<ip>` or `<redacted>`. That now
  includes a drive-relative path such as `C:jane`, a drive marker in the value half of a pair such as
  `cwd:C:jsmith`, and a percent-encoded path such as `C%3A%5CUsers%5Cjane`; a path in quotes is
  collapsed whole, so Node's `scandir 'C:\Users\Jane Smith'` reports as `scandir <path>`. Telemetry
  remains off unless you turn it on, and VS Code's own telemetry setting still gates it (CORE-596)

- **Error telemetry, what is still sent**: a path containing a space that is *not* in quotes keeps its
  last segment, so `Unable to resolve workspace folder C:\Users\Jane Smith` is sent as
  `... <path> Smith`. Nothing marks where such a path ends, so the scrubber cannot tell that segment
  from the sentence that might follow it. Personal data written as an ordinary word is also kept on
  purpose: a machine name such as `jane-macbook` or `JANE-PC`, a username in `user:jsmith`, a person's
  name in prose, a phone number. Each has the same shape as the diagnostic text around it, so removing
  it would mean removing the diagnosis. The full list is in the source and is pinned by the unit tests,
  so it cannot change quietly (CORE-596)

- **Server command**: `legesher.serverCommand` is now `machine-overridable` scoped and is restricted
  in untrusted workspaces. The setting names an executable the extension spawns on activation, and it
  carried no scope restriction and no `capabilities.untrustedWorkspaces` declaration, so a cloned
  repository's `.vscode/settings.json` could point the extension at an arbitrary binary once the
  workspace was trusted with nothing in the manifest flagging the setting to VS Code's trust
  machinery. A project can still pin its own server binary in a workspace you trust; in an untrusted
  workspace only your user-level value or the bundled default is used (CORE-2030)

- **Dependencies**: cleared all known npm audit advisories in the extension's dependency tree
  (13 advisories, 7 high) — lockfile-only bumps; the one bundled runtime package moved is
  `js-yaml` 4.2.0 → 4.3.1 (quadratic-CPU `!!omap` advisory), which ships in the packaged extension

- **Language selector**: a language change that does not take effect now says so. A settings write that
  fails, or that a narrower scope overrides, raises a warning naming what is still in effect instead of
  reporting success; a language the server never loaded is shown in the status bar as `(inactive)` with
  the reason, instead of being displayed as though it were running (CORE-1776)

### Added

- **Telemetry**: language changes are now recorded as transitions — what triggered the change (picker,
  settings edit, editor switch, activation, restart), which scope or mechanism supplied the language,
  and whether it was applied, unchanged, failed, or had no server to apply to. Previously only picker
  changes were recorded, and they were recorded before the write they described, so a change that
  silently did nothing still reported success (CORE-1776)
- **Telemetry**: settings writes record their scope and whether they took effect, and content detection
  records its decisions and scores — the thresholds have never been measured against real files
  (CORE-1776)

### Changed

- **Language packs**: pack files are now validated at load — a 1 MiB size cap and a runtime shape check on
  keywords/builtins/exceptions; malformed or oversized packs are skipped with a warning instead of being trusted (CORE-1453)
- **Telemetry**: defaults to OFF — opt in via `legesher.telemetry.enabled` (CORE-1586)
- **Settings**: `legesher.targetLanguage` and `legesher.sourceLanguage` now say which is which —
  the target language is your own preference and changes only what you see; the source language is a
  property of the repository, describing what its files are actually stored in (CORE-1847)
- **Status bar**: a project-level language is described as a "project setting" rather than
  distinguishing folder from workspace. Legesher's settings are window-scoped, for which VS Code
  never applies a per-folder value, so the distinction named something that cannot differ (CORE-1847)
- **Performance**: content-based language detection is memoized per document and version, instead of
  re-tokenizing the whole file on every editor switch (CORE-1776)
- **Telemetry**: a language transition now describes the language server's configured languages only.
  Switching between files detected in different languages no longer starts the server again, so it no
  longer records a transition; detection's own events still record what each file resolved to
  (CORE-1976)

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
