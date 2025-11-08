# Legesher VS Code Extension

Write Python code in your native language with real-time translation and intelligent IDE support.

## Features

### v0.1.0 (Current)

- **Language Server Integration**: Connects to the Legesher language server via LSP
- **Python Support**: Full support for Python files (`.py`)
- **Status Indicator**: Visual indicator showing connection status
- **Configuration**: Customizable settings for language server connection

### Coming Soon

- Language selector for switching between languages (Spanish, Arabic, Chinese, etc.)
- Side-by-side translation view
- Cultural context annotations
- IntelliSense with localized keywords
- Real-time error message translation

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

### `Legesher: Restart Language Server`

Restart the language server connection.

Access via Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`) and search for "Legesher: Restart".

## Usage

1. Open a Python file (`.py`)
2. The extension will automatically activate
3. Check the status bar (bottom right) for the Legesher indicator:
   - `$(check) Legesher` - Connected successfully
   - `$(sync~spin) Legesher` - Connecting...
   - `$(error) Legesher` - Connection error
   - `$(circle-slash) Legesher` - Disabled

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
**Last Updated**: 2025-11-07
