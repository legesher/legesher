# Legesher VS Code Extension

Write Python code in your native language with real-time translation and intelligent IDE support.

**Status**: Production-Ready (Pre-Beta) | **Version**: 0.0.x | **Languages**: 27+ | **VS Code**: 1.85.0+

## Features

### Current (Pre-Beta v0.0.x)

- **Language Server Integration**: Connects to the Legesher language server via LSP
- **Language Selector**: Quick-pick menu to switch between languages (English, Spanish, Arabic, Chinese)
- **Translation Panel**: Side-by-side view showing original code and translated version
- **Synchronized Scrolling**: Scroll both panes together for easy comparison
- **Syntax Highlighting**: Color-coded syntax for both original and translated code
- **Copy Translation**: One-click copy of translated code to clipboard
- **Python Support**: Full support for Python files (`.py`)
- **Status Indicator**: Visual indicator showing connection status and current language
- **Configuration**: Customizable settings for language server connection
- **Telemetry System**: Privacy-focused usage tracking (respects VS Code global settings)
- **Feedback System**: Two-stage prompting for user feedback and GitHub issue integration

### Coming Soon

- Cultural context annotations
- IntelliSense with localized keywords
- Real-time error message translation
- Additional programming languages support

## Requirements

- VS Code 1.85.0 or higher
- Python 3.10 or higher
- Legesher language server installed (`legesher-lsp` command available)

## Installation

### From VSIX (Development)

1. Download the `.vsix` file
2. Open VS Code
3. Go to Extensions view (`Cmd+Shift+X` or `Ctrl+Shift+X`)
4. Click the `...` menu → "Install from VSIX..."
5. Select the downloaded `.vsix` file

### From Source (Development)

```bash
cd libs/vs-code
npm install
npm run compile
```

Then press F5 in VS Code to launch the Extension Development Host.

## Configuration

Access settings via `Code > Preferences > Settings` and search for "Legesher":

### `legesher.targetLanguage`

Target language for code translation.

- **Type**: `string`
- **Default**: `"en"`
- **Options**: `"en"` (English), `"es"` (Spanish), `"ar"` (Arabic), `"zh"` (Chinese)

Example:

```json
{
  "legesher.targetLanguage": "es"
}
```

### `legesher.sourceLanguage`

Source language (Python keywords).

- **Type**: `string`
- **Default**: `"en"`
- **Note**: Only English is currently supported

### `legesher.serverCommand`

Path to the Legesher language server executable.

- **Type**: `string`
- **Default**: `"legesher-lsp"`

Example:

```json
{
  "legesher.serverCommand": "/usr/local/bin/legesher-lsp"
}
```

### `legesher.trace.server`

Enable tracing of communication between VS Code and the language server (useful for debugging).

- **Type**: `string`
- **Options**: `"off"`, `"messages"`, `"verbose"`
- **Default**: `"off"`

### `legesher.enabled`

Enable or disable the Legesher extension.

- **Type**: `boolean`
- **Default**: `true`

## Commands

Access commands via Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`):

### `Legesher: Show Translation Panel`

Open a side-by-side view showing the original Python code and its translation in your selected language.

- **Keyboard**: Available in Command Palette
- **Context Menu**: Right-click in Python files → "Legesher: Show Translation Panel"
- **Editor Toolbar**: Click the split-view icon when editing Python files

### `Legesher: Select Language`

Open a quick-pick menu to choose your target language for translation.

- **Available languages**: English, Spanish (Español), Arabic (العربية), Chinese (中文)
- **Status Bar**: Click the language indicator (e.g., "$(globe) ES") in the bottom-right corner

### `Legesher: Restart Language Server`

Restart the language server connection.

- **Use when**: Language server becomes unresponsive or after configuration changes

## Usage

### Quick Start

1. **Open a Python file** (`.py`)
   - The extension will automatically activate

2. **Select your language**
   - Click the language indicator in the status bar (bottom-right): `$(globe) EN`
   - Choose your preferred language from the quick-pick menu
   - The indicator will update to show your selection (e.g., `$(globe) ES` for Spanish)

3. **View translations**
   - **Command Palette**: Search for "Legesher: Show Translation Panel"
   - **Context Menu**: Right-click in the editor → "Legesher: Show Translation Panel"
   - **Editor Toolbar**: Click the split-view icon

4. **Work with the translation panel**
   - Scroll in either pane to view corresponding sections
   - Click "Copy" to copy the translated code to your clipboard
   - Close the panel anytime by clicking the X

### Status Indicators

Check the status bar (bottom right) for Legesher indicators:

- **Main Status**:
  - `$(check) Legesher` - Connected successfully
  - `$(sync~spin) Legesher` - Connecting...
  - `$(warning) Legesher` - Server not available (limited functionality)
  - `$(error) Legesher` - Connection error
  - `$(circle-slash) Legesher` - Disabled

- **Language Status**:
  - `$(globe) EN` - English (default)
  - `$(globe) ES` - Spanish (Español)
  - `$(globe) AR` - Arabic (العربية)
  - `$(globe) ZH` - Chinese (中文)

## Troubleshooting

### Extension won't activate

- Ensure you have a Python file open (`.py` extension)
- Check the Output panel: View → Output → "Legesher Language Server"

### Language server connection fails

1. Verify the language server is installed:

   ```bash
   legesher-lsp --version
   ```

2. Check the server command in settings (`legesher.serverCommand`)

3. View detailed logs:
   - Set `legesher.trace.server` to `"verbose"`
   - Open Output panel: View → Output → "Legesher Language Server Trace"

4. Try restarting the server:
   - Command Palette → "Legesher: Restart Language Server"

### Still having issues?

- Check the [issue tracker](https://github.com/madiedgar/legesher/issues)
- View [troubleshooting guide](https://docs.legesher.io/troubleshooting)
- Join our [community](https://legesher.io/community)

## Development

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

### Building

```bash
npm install        # Install dependencies
npm run compile    # Compile TypeScript
npm run watch      # Watch mode for development
npm run lint       # Run linting
npm run package    # Create .vsix package
```

### Testing

1. Open this directory in VS Code
2. Press F5 to launch Extension Development Host
3. Open a Python file in the new window
4. Verify the extension activates and connects to the language server

## Architecture

This extension is a thin LSP client that connects to the `legesher-language-server`:

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
│   - Pylance Integration      │
│   - LSP Providers            │
└──────────────────────────────┘
```

## License

See [LICENSE](./LICENSE) file for details.

## Links

- [Homepage](https://legesher.io)
- [Documentation](https://docs.legesher.io)
- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)

---

**Version**: 0.1.0
**Author**: Madison Edgar (<madi@legesher.com>)
**Last Updated**: 2024-11-10
