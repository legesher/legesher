# Legesher VS Code Extension

Write Python code in your native language with real-time translation and IDE support.

**Languages**: 51 | **VS Code**: 1.110.0+ | **Status**: Preview

The version this README ships with is the `version` field in `package.json`.

## What This Extension Does

The Legesher VS Code extension provides the UI and editor integration for coding Python in your native language:

- **Language Selector**: Choose from 51 supported languages via status bar or command palette
- **Translation Panel**: Side-by-side view of your code in English and your selected language
- **Onboarding Flow**: First-time setup wizard for language selection and preferences
- **Status Indicators**: Visual feedback for connection status and current language
- **Syntax Highlighting**: Color-coded keywords in translated code view

> **Note**: Hover, completion, diagnostics and keyword highlighting come from the
> [Legesher language server](../language-server/README.md), a separate Python package. See
> [The language server](#the-language-server) below.

## Supported Languages

Amharic, Arabic, Bengali, Bosnian, Burmese, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English,
Finnish, French, Galician, German, Greek, Gujarati, Hebrew, Hindi, Hungarian, Indonesian, Irish, Italian,
Japanese, Kannada, Korean, Latvian, Macedonian, Malay, Malayalam, Mongolian, Norwegian, Persian, Polish,
Portuguese, Romanian, Russian, Scottish Gaelic, Serbian, Sinhala, Spanish, Sundanese, Swedish, Telugu, Thai,
Turkish, Ukrainian, Urdu, Uzbek, Vietnamese, Welsh

All languages are currently in **experimental** status, awaiting community validation.

### Right-to-left languages

Arabic, Hebrew, Persian, and Urdu are right-to-left languages. Legesher translates their keywords the
same way it translates any other language's, and the translation panel applies right-to-left direction
and alignment when one of them is active. The VS Code editor itself is unchanged: it renders
right-to-left code with the plain bidirectional algorithm, which VS Code does not yet let an extension
influence.

## Installation

For complete installation instructions (VS Code extension + Python packages), see:

**[Getting Started](https://docs.legesher.io/getting-started/)**

### Quick Install (Extension Only)

1. Download the latest `.vsix` file from [releases](https://github.com/legesher/legesher/releases)
2. In VS Code: Extensions (`Cmd+Shift+X`) → `...` menu → "Install from VSIX..."
3. Select the downloaded file

### The language server

The extension does not bundle its language server. It runs the command in
`legesher.serverCommand`, which defaults to `legesher-lsp`. That command comes
from the `legesher-language-server` Python package, which is not on PyPI yet.
When it is installed, it has to be on the `PATH` VS Code sees, or
`legesher.serverCommand` has to hold its full path.

Hover, completion, diagnostics and keyword highlighting all come from the
server. Without it the extension still starts: the language picker and the
translation panel work, and the status bar item shows a warning whose tooltip
names the package it needs.

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

| Setting                                     | Default        | Description                                 |
| ------------------------------------------- | -------------- | ------------------------------------------- |
| `legesher.workingLanguage`                  | `en`           | The language you read and write in          |
| `legesher.knownLanguages`                   | `[]`           | The languages you read comfortably          |
| `legesher.sourceLanguage`                   | `en`           | The vocabulary translations route through   |
| `legesher.languageDetection`                | `auto`         | Infer each file's language from it          |
| `legesher.enabled`                          | `true`         | Enable/disable the extension                |
| `legesher.serverCommand`                    | `legesher-lsp` | Command that starts the language server     |
| `legesher.trace.server`                     | `off`          | Debug logging level                         |
| `legesher.telemetry.enabled`                | `false`        | Usage telemetry (see Privacy below)         |
| `legesher.telemetry.contributeToMLTraining` | `false`        | Record consent for ML training (see below)  |

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
  its contents (`legesher.languageDetection`). Each open file is served in its
  own file language, so files in different languages work side by side in one
  window.
- **Known languages** (`legesher.knownLanguages`) — the languages you read
  comfortably. Legesher lists these first in the language picker and stays
  quiet about files already written in one of them, instead of flagging every
  file that is not in your working language. Seeded from your working language,
  so there is nothing to configure to get started; edit it with
  `Legesher: Manage My Languages`.
- **Pivot** (`legesher.sourceLanguage`) — the terms Python itself defines,
  which every translation routes through. This is the run form, not a
  canonical form: a file's canonical form is whatever its author wrote.

### Language Codes

```text
am (Amharic)          ar (Arabic)           bn (Bengali)          bs (Bosnian)
ca (Catalan)          cs (Czech)            cy (Welsh)            da (Danish)
de (German)           el (Greek)            en (English)          es (Spanish)
fa (Persian)          fi (Finnish)          fr (French)           ga (Irish)
gd (Scottish Gaelic)  gl (Galician)         gu (Gujarati)         he (Hebrew)
hi (Hindi)            hr (Croatian)         hu (Hungarian)        id (Indonesian)
it (Italian)          ja (Japanese)         kn (Kannada)          ko (Korean)
lv (Latvian)          mk (Macedonian)       ml (Malayalam)        mn (Mongolian)
ms (Malay)            my (Burmese)          nl (Dutch)            no (Norwegian)
pl (Polish)           pt (Portuguese)       ro (Romanian)         ru (Russian)
si (Sinhala)          sr (Serbian)          su (Sundanese)        sv (Swedish)
te (Telugu)           th (Thai)             tr (Turkish)          uk (Ukrainian)
ur (Urdu)             uz (Uzbek)            vi (Vietnamese)       zh (Chinese)
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
| `unicode_guard.scan_text` | `legesher guard` (`libs/core/legesher_core/guard.py`), run by the pre-commit hook on commit where it is installed (a client-side check `--no-verify` skips) | Bidi reordering controls, category-`Cf` invisibles, the full `Default_Ignorable` set, Arabic tatweel, and an interior byte-order mark |
| `unicode_guard.scan_identifier` | Same guard, on commit | Every identifier character must belong to a script some shipped language pack uses |
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
  content and no identifiers we collect; the bundled
  `@vscode/extension-telemetry` library adds a pseudonymous machine id.
  One property carries free text: the message of an error the extension did
  not write. It is scrubbed of paths, emails, URLs and addresses before it is
  sent, but the scrubber works on shapes, so a fragment of a path that looks
  like an ordinary word can survive
- **ML training**: A separate opt-in
  (`legesher.telemetry.contributeToMLTraining`, also off by default). Today this
  setting only records your answer: the extension sends no translation
  corrections, and no telemetry event is gated on it. It is here so the consent
  is on record before any such event exists. If that changes, it will be in the
  changelog and here first. See
  [privacy](https://docs.legesher.io/privacy#ml-training)
- **No code collection**: Your code never leaves your machine
- Respects VS Code's global telemetry settings

---

**Author**: Madison Edgar - Legesher
**License**: [Apache 2.0](./LICENSE)
