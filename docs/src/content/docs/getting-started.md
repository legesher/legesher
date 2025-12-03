---
title: Getting Started with Legesher
description: Quick start guide for coding in your native language with Legesher
---

# Getting Started with Legesher

Welcome to Legesher! This guide will help you start coding in your native language.

## Quick Start

### 1. Install the VS Code Extension

Install from the VS Code Marketplace:

- Search for "Legesher" in the Extensions panel
- Click "Install"

Or install manually:

```bash
code --install-extension legesher.legesher-vscode
```

### 2. Select Your Language

After installation, you'll see a welcome dialog. Click **"Choose Your Language"** to select your preferred coding language.

Or manually:

1. Open Command Palette (⌘⇧P or Ctrl+Shift+P)
2. Type "Legesher: Select Language"
3. Choose your language from the list

### 3. Start Coding

Open a Python file and start typing! Legesher will:

- ✅ Provide keyword suggestions in your language
- ✅ Show hover documentation in your language
- ✅ Translate Python builtins
- ✅ Support IntelliSense in your native language

## Supported Languages

Legesher currently supports Python 3.10+ with translations in:

- **Arabic** (العربية)
- **Chinese Simplified** (简体中文)
- **English** (English)
- **French** (Français)
- **Spanish** (Español)
- And 20+ more languages!

See [Language Codes](/language-codes/) for the complete list.

## Features

### Keyword Translation

Write Python keywords in your native language:

```python
# Spanish example
función saludar(nombre):
    imprimir(f"¡Hola, {nombre}!")

si __nombre__ == "__principal__":
    saludar("Mundo")
```

### Git Integration

Your code is stored in English in git, but you see it in your language:

- **Your view:** Code in your native language
- **Git storage:** English (for universal collaboration)
- **Automatic translation:** Both directions, seamlessly

### IntelliSense Support

Get completions, hover docs, and diagnostics in your language:

- Type `imprimir` and see suggestions for `print()`
- Hover over functions to see localized documentation
- Error messages in your language

## Settings

### Telemetry

Control what data Legesher collects:

**Basic telemetry** (enabled by default):

```json
{
  "legesher.telemetry.enabled": true
}
```

**ML training contributions** (opt-in only):

```json
{
  "legesher.telemetry.contributeToMLTraining": false
}
```

[Learn more about privacy →](/privacy/)

### Language Selection

Change your coding language anytime:

1. Click the language indicator in the status bar (bottom right)
2. Or use Command Palette: "Legesher: Select Language"

## Troubleshooting

### Extension not activating?

1. Check that you have Python installed
2. Open a `.py` file to trigger activation
3. Check the Output panel: View → Output → Select "Legesher Language Server"

### Translations not showing?

1. Verify language selection: Check status bar
2. Restart language server: Command Palette → "Legesher: Restart Language Server"
3. Check for errors in Output panel

### Need help?

- 📖 [Read the FAQ](/faq/)
- 🐛 [Report an issue](https://github.com/legesher/legesher/issues)
- 💬 [Join our community](https://discord.gg/legesher)

## What's Next?

- Learn about [version-aware language packs](/guides/language-packs/)
- Understand [git workflow with Legesher](/guides/git-workflow/)
- Contribute translations via the [community platform](/guides/community-contributions/)

---

**Ready to code?** Open a Python file and start typing in your language! 🚀
