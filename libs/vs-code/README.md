# Legesher VS Code Extension

Write Python code in your native language with real-time translation and IDE support.

**Version**: 0.1.2 | **Languages**: 51 | **VS Code**: 1.85.0+ | **Status**: Preview

## What This Extension Does

The Legesher VS Code extension provides the UI and editor integration for coding Python in your native language:

- **Language Selector**: Choose from 51 supported languages via status bar or command palette
- **Translation Panel**: Side-by-side view of your code in English and your selected language
- **Onboarding Flow**: First-time setup wizard for language selection and preferences
- **Status Indicators**: Visual feedback for connection status and current language
- **Syntax Highlighting**: Color-coded keywords in translated code view

> **Note**: Full translation capabilities (hover docs, auto-completion, diagnostics) require the
> [Legesher Language Server](../language-server/README.md) to be installed and running.

## Supported Languages

Arabic, Chinese, Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Hungarian,
Indonesian, Italian, Japanese, Korean, Malay, Norwegian, Polish, Portuguese, Russian, Spanish,
Swedish, Thai, Turkish, Vietnamese

All languages are currently in **experimental** status, awaiting community validation.

## Installation

For complete installation instructions (VS Code extension + Python packages), see:

**[Installation Guide](https://github.com/legesher/preview-repo/blob/main/docs/INSTALLATION.md)**

### Quick Install (Extension Only)

1. Download the latest `.vsix` file from [releases](https://github.com/legesher/preview-repo/releases)
2. In VS Code: Extensions (`Cmd+Shift+X`) → `...` menu → "Install from VSIX..."
3. Select the downloaded file

> **Note**: Full features (hover docs, auto-completion, diagnostics) require the complete Legesher package suite.
> See the [Installation Guide](https://github.com/legesher/preview-repo/blob/main/docs/INSTALLATION.md) for details.

## Quick Start

1. **Open a Python file** - The extension activates automatically
2. **Complete onboarding** - Select your preferred language on first launch
3. **Change language anytime** - Click the language indicator in the status bar (e.g., `ES`)
4. **View translations** - Use Command Palette → "Legesher: Show Translation Panel"

## Commands

| Command                             | Description                         |
| ----------------------------------- | ----------------------------------- |
| `Legesher: Select Language`         | Choose your target language         |
| `Legesher: Show Translation Panel`  | Open side-by-side translation view  |
| `Legesher: Restart Language Server` | Reconnect to the language server    |
| `Legesher: Give Feedback`           | Submit feedback about the extension |

## Configuration

Access via Settings (`Cmd+,`) → search "Legesher":

| Setting                      | Default        | Description                    |
| ---------------------------- | -------------- | ------------------------------ |
| `legesher.targetLanguage`    | `en`           | Your preferred coding language |
| `legesher.enabled`           | `true`         | Enable/disable the extension   |
| `legesher.serverCommand`     | `legesher-lsp` | Path to language server        |
| `legesher.trace.server`      | `off`          | Debug logging level            |
| `legesher.telemetry.enabled` | `true`         | Anonymous usage telemetry      |

### Language Codes

```text
ar (Arabic)      da (Danish)      de (German)      el (Greek)
en (English)     es (Spanish)     fi (Finnish)     fr (French)
he (Hebrew)      hi (Hindi)       hu (Hungarian)   id (Indonesian)
it (Italian)     ja (Japanese)    ko (Korean)      ms (Malay)
nl (Dutch)       no (Norwegian)   pl (Polish)      pt (Portuguese)
ru (Russian)     sv (Swedish)     th (Thai)        tr (Turkish)
vi (Vietnamese)  zh (Chinese)
```

## Status Bar Indicators

- **Connection**: `Legesher` with check/warning/error icon
- **Language**: Two-letter code (e.g., `ES` for Spanish) - click to change

## Architecture

```text
┌─────────────────────────────┐
│   VS Code Extension         │  ← This package
│   - UI components           │
│   - Commands & settings     │
│   - LSP client              │
└──────────────┬──────────────┘
               │ Language Server Protocol
               ↓
┌──────────────────────────────┐
│   Legesher Language Server   │  ← Separate package
│   - Translation engine       │
│   - Hover/completion/diag    │
└──────────────────────────────┘
```

## Privacy

- **Telemetry**: Anonymous usage data (can be disabled)
- **No code collection**: Your code never leaves your machine
- Respects VS Code's global telemetry settings

---

**Author**: Madison Edgar - Legesher
**License**: [Apache 2.0](./LICENSE)
