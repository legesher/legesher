# legesher-vscode - Claude Code Guide

This file provides guidance for working with the `legesher-vscode` VS Code extension.

## Package Overview

**Version**: 0.1.2
**Status**: Preview
**VS Code**: 1.85.0+
**Language**: TypeScript

VS Code extension providing multilingual Python coding support via LSP client.

## Key Capabilities

- **LSP Client**: Connects to `legesher-language-server`
- **Language Selector**: Quick-pick menu listing all active languages from the registry (currently 51)
- **Translation Panel**: Side-by-side code comparison
- **Synchronized Scrolling**: Both panes scroll together
- **Status Indicators**: Connection status and current language
- **Telemetry**: Privacy-focused usage tracking
- **Feedback System**: Two-stage prompting with GitHub integration

**Note**: The extension supports all 51 languages via `getActiveLanguages()` from the generated language registry.

## Directory Structure

```text
libs/vs-code/
├── src/
│   ├── extension.ts          # Extension entry point
│   ├── client.ts             # LSP client
│   ├── languagePackLoader.ts # Language pack loading
│   ├── telemetry.ts          # Telemetry system
│   ├── feedback.ts           # User feedback
│   ├── utils.ts              # Utilities
│   ├── logger.ts             # Logging
│   └── keywords.ts           # Keyword definitions
├── package.json              # Extension manifest
├── tsconfig.json             # TypeScript config
└── pyproject.toml            # Python tooling (for integration)
```

## Development

### Prerequisites

- Node.js 18+
- npm or pnpm
- VS Code 1.85.0+
- Python 3.10+ (for language server)

### Setup

```bash
cd libs/vs-code
npm install
npm run compile
```

### Running in Development

1. Open `libs/vs-code/` in VS Code
2. Press F5 to launch Extension Development Host
3. Open a Python file in the new window
4. Extension activates automatically

### npm Scripts

```bash
npm run compile    # Compile TypeScript
npm run watch      # Watch mode for development
npm run lint       # Run linting
npm run package    # Create .vsix package
```

## Configuration Options

In VS Code settings (`settings.json`):

```json
{
  "legesher.workingLanguage": "es", // Any of 51 supported languages
  "legesher.knownLanguages": ["es", "en"], // Seeded from workingLanguage when empty
  "legesher.sourceLanguage": "en", // Only en currently
  "legesher.languageDetection": "auto", // auto, off
  "legesher.serverCommand": "legesher-lsp",
  "legesher.trace.server": "off", // off, messages, verbose
  "legesher.enabled": true
}
```

### Language roles (CORE-1760)

`legesher.targetLanguage` is **deprecated** — it meant the file's language and
the reader's language at once, which diverge the moment you open someone
else's file. It is still honoured wherever `legesher.workingLanguage` is not
set, at its own scope: VS Code precedence (folder > workspace > user) decides
first, and only within one scope does the new name outrank the old.

| Role     | Setting                      | Meaning                                |
| -------- | ---------------------------- | -------------------------------------- |
| Canonical| `legesher.sourceLanguage`    | What Python itself defines; the pivot  |
| File     | detected per file            | What a given file is written in        |
| Working  | `legesher.workingLanguage`   | What the user reads and writes in      |
| Known    | `legesher.knownLanguages`    | What the user reads comfortably        |

The file and working languages reach the language server as **separate**
`initializationOptions` slots (`fileLanguage`, `workingLanguage`), plus a
deprecated `targetLanguage` slot mirroring `fileLanguage` for older servers.
Never collapse them client-side — the server cannot un-collapse one value.
The rules live in `src/languageProfile.ts`, which is free of `vscode` imports
so they are unit-testable without an editor host.

## Commands

Access via Command Palette (Cmd+Shift+P / Ctrl+Shift+P):

- **Legesher: Show Translation Panel** - Open side-by-side view
- **Legesher: Select Language** - Choose the working language
- **Legesher: Manage My Languages** - Edit the known-language set
- **Legesher: Restart Language Server** - Restart connection

## Status Bar Indicators

- **Connection**: `$(check) Legesher`, `$(sync~spin) Legesher`, `$(warning) Legesher`
- **Language**: `$(globe) {LANG_CODE}` - The language in effect for this file
- **Mismatch**: `$(search) {FILE} → {WORKING}` - The file is written in a
  language that is neither your working language nor one you have marked as
  known; a file in a known language shows no mismatch

## Telemetry

Privacy-focused telemetry respects VS Code global settings:

```json
{
  "legesher.telemetry.enabled": false,
  "legesher.telemetry.contributeToMLTraining": false
}
```

## Testing

**Note**: No automated tests currently. Manual testing required:

1. Launch Extension Development Host (F5)
2. Open Python file
3. Verify extension activates
4. Test language selection
5. Test translation panel

## Common Tasks

### Adding a New UI Language

1. Update `src/languagePackLoader.ts` with language entry
2. Add to package.json `contributes.configuration` enum
3. Update language selector in `src/extension.ts`
4. Test in Extension Development Host

### Debugging Extension Issues

1. Set `legesher.trace.server: "verbose"`
2. Open Output panel → "Legesher Language Server"
3. Check Developer Tools (Help → Toggle Developer Tools)

### Building for Distribution

```bash
npm run package
# Creates legesher-vscode-{version}.vsix

# Install locally
code --install-extension legesher-vscode-0.1.2.vsix
```

## Architecture

```text
┌─────────────────────────────┐
│   VS Code Extension         │
│   (TypeScript)              │
│   - extension.ts (entry)    │
│   - client.ts (LSP client)  │
└──────────────┬──────────────┘
               │ LSP Protocol (JSON-RPC)
               ↓
┌──────────────────────────────┐
│   Legesher Language Server   │
│   (Python)                   │
│   - Translation Engine       │
│   - LSP Providers            │
└──────────────────────────────┘
```

## Dependencies

- `vscode-languageclient` - LSP client library
- VS Code Extension API

## Related Issues

- CORE-477: Telemetry and feedback system
