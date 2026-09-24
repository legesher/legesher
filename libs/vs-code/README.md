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

| Command                             | Description                          |
| ----------------------------------- | ------------------------------------ |
| `Legesher: Select Language`         | Choose the language you work in      |
| `Legesher: Manage My Languages`     | Edit the set of languages you read   |
| `Legesher: Show Translation Panel`  | Open side-by-side translation view   |
| `Legesher: Restart Language Server` | Reconnect to the language server     |
| `Legesher: Give Feedback`           | Submit feedback about the extension  |

## Configuration

Access via Settings (`Cmd+,`) → search "Legesher":

| Setting                      | Default        | Description                            |
| ---------------------------- | -------------- | -------------------------------------- |
| `legesher.workingLanguage`   | `en`           | The language you read and write in     |
| `legesher.knownLanguages`    | `[]`           | The languages you read comfortably     |
| `legesher.sourceLanguage`    | `en`           | The language the project is stored in  |
| `legesher.languageDetection` | `auto`         | Infer each file's language from it     |
| `legesher.enabled`           | `true`         | Enable/disable the extension           |
| `legesher.serverCommand`     | `legesher-lsp` | Path to language server                |
| `legesher.trace.server`      | `off`          | Debug logging level                    |
| `legesher.telemetry.enabled` | `false`        | Usage telemetry (see Privacy below)    |

> **`legesher.targetLanguage` is deprecated.** It was one setting for two
> different things — the language a file is written in, and the language you
> want to read it in — which are only the same on your own files. Use
> `legesher.workingLanguage` instead. Existing settings keep working: the old
> name is still honoured wherever the new one is not set.

### Language roles

Legesher distinguishes four roles, so opening someone else's file does the
right thing:

- **Working language** (`legesher.workingLanguage`) — what you read and write
  in. Change it from the status bar or `Legesher: Select Language`.
- **File language** — what a given file is actually written in, detected from
  its contents (`legesher.languageDetection`).
- **Known languages** (`legesher.knownLanguages`) — the languages you read
  comfortably. Legesher lists these first in the language picker and stays
  quiet about files already written in one of them, instead of flagging every
  file that is not in your working language. Seeded from your working language,
  so there is nothing to configure to get started; edit it with
  `Legesher: Manage My Languages`.
- **Canonical** (`legesher.sourceLanguage`) — the English terms Python itself
  defines, which every translation routes through.

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

## Unicode Highlighting

VS Code marks characters that could be confused with an ASCII character. It is a
defence against Trojan Source (CVE-2021-42574), and on an ASCII codebase it is a
good one. On a Legesher file it fires on almost every identifier: Arabic Alef
(U+0627) is reported as a likely impersonation of Latin `l`, Cyrillic small a
(U+0430) of `a`, Turkish dotless i (U+0131) of `i`.

When you open a translated file in a script that this happens to, Legesher offers
once to fix it. Accepting writes `editor.unicodeHighlight.allowedCharacters` into
**this workspace's** settings, listing only the characters the language pack for
that file uses that VS Code would otherwise flag. That is typically a handful
(two for Arabic, one for Amharic, twelve for Russian). `Don't Ask Again` suppresses
the offer everywhere; `Not Now` defers it to your next session.

The extension never changes this setting globally and ships no
`configurationDefaults`, so the check keeps working exactly as before on every
other repository you open. Only the derived characters are written: VS Code
merges object-valued settings across scopes, so characters you have allowed for
yourself keep working here without being copied into a file your teammates pull.

### Workspace trust is the outer gate

`editor.unicodeHighlight.allowedCharacters` is registered by VS Code with
`restricted: true`. A workspace value for it is **ignored** until you grant the
workspace trust, so a repository you have not trusted cannot use this setting to
switch off its own confusable warnings, whether it ships the setting itself or
gets Legesher to write it. The offer is therefore gated on
`workspace.isTrusted` as well: Legesher does not prompt, and does not write, in
a repository you have declined to trust. This is the strongest protection in the
design, and it is VS Code's, not ours.

### What stays switched on

Accepting the offer relaxes one specific check for a handful of characters. What
still runs, and where:

| Protection | Where it runs | What it covers |
| --- | --- | --- |
| `editor.unicodeHighlight.invisibleCharacters` | VS Code, never touched by this extension | Zero-width and bidi-control characters, in the editor |
| `editor.unicodeHighlight.ambiguousCharacters` | VS Code, still on | Confusables from every *other* script: a Cyrillic small a in an Arabic file is still flagged |
| `unicode_guard.scan_text` | Legesher git clean filter (`libs/core/legesher_core/git_filter.py`), on commit | Bidi reordering controls, category-`Cf` invisibles, the full `Default_Ignorable` set, Arabic tatweel, and a byte-order mark |
| `unicode_guard.scan_identifier` | Same filter, on commit | Every identifier character must belong to a script some shipped language pack uses |
| Store-NFC / compare-NFKC+fold identity | Legesher engine (`libs/core/legesher_core/text_identity.py`) | Canonically equivalent spellings hash and compare alike, in the pack and corpus pipeline |

### What does not

Be precise about the gap this opens, because the table above is easy to read as
more than it is:

- **Nothing at the Legesher layer replaces the confusable check for the
  characters being allowed.** `unicode_guard` has no confusable or homoglyph
  table at all; it is an invisible-character and script-membership guard. Once
  Arabic Alef is allowed in a workspace, no Legesher check will tell you that an
  identifier using it could be read as a Latin `l`.
- **Mixed-script identifiers produce no editor diagnostic.**
  `IdentifierValidator.is_mixed_script`
  (`libs/core/legesher_core/tree_sitter/identifier_validator.py`) is a real
  mixed-script check, but it is reachable only through that class's `validate()`
  and `script_report()`, and the language server calls neither. No diagnostic
  reaches a file you have open.
- The clean-filter guards above run **on commit**, not as you type, so they
  catch a bad character on the way into git rather than on screen.

The characters being allowed are the ones the project's own packs are written
in, and the allowance is per workspace, per character, and only after you grant
trust. That is the trade, stated plainly rather than implied by a list of
guards that cover something else.

### Why not `allowedLocales`

`editor.unicodeHighlight.allowedLocales` looks like the right instrument and is
not: VS Code's locale table covers only its own display languages, so an entry
like `{"ar": true}` is discarded silently, and its per-locale maps cannot reach
the shared table that holds Arabic Alef. `libs/vs-code/src/unicodeHighlight.ts`
records the evidence.

## Privacy

- **Telemetry**: Usage data, off by default (opt-in). Events contain no code
  content, no file paths, and no identifiers we collect; the bundled
  `@vscode/extension-telemetry` library adds a pseudonymous machine id
- **No code collection**: Your code never leaves your machine
- Respects VS Code's global telemetry settings

---

**Author**: Madison Edgar - Legesher
**License**: [Apache 2.0](./LICENSE)
