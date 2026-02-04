# Contributing to Legesher VS Code Extension

Thank you for your interest in contributing to the Legesher VS Code extension!

## Development Setup

### Prerequisites

- Node.js 18+ and npm
- VS Code 1.85.0 or higher
- Python 3.10+ (for running the language server)
- Git

### Getting Started

1. **Clone the repository**:

   ```bash
   git clone https://github.com/madiedgar/legesher.git
   cd legesher/libs/vs-code
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Open in VS Code**:

   ```bash
   code .
   ```

4. **Run the extension**:
   - Press `F5` to launch the Extension Development Host
   - A new VS Code window will open with the extension loaded
   - Open a Python file to test the extension

## Project Structure

```text
libs/vs-code/
├── src/
│   ├── extension.ts      # Main extension entry point
│   └── client.ts         # LSP client configuration
├── out/                  # Compiled JavaScript (generated)
├── syntaxes/            # Syntax highlighting definitions (future)
├── icons/               # Extension icons (future)
├── package.json         # Extension manifest
├── tsconfig.json        # TypeScript configuration
├── .eslintrc.json       # ESLint configuration
└── README.md
```

## Development Workflow

### Compile TypeScript

```bash
# One-time compilation
npm run compile

# Watch mode (auto-recompile on changes)
npm run watch
```

### Linting

```bash
# Run ESLint
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix
```

### Testing

#### Manual Testing

1. Press `F5` in VS Code to launch Extension Development Host
2. Open a Python file
3. Verify:
   - Extension activates (check status bar)
   - Language server connects
   - No errors in Developer Tools Console (`Help > Toggle Developer Tools`)

#### Check Logs

- **Extension Output**: View → Output → "Legesher Language Server"
- **Developer Console**: Help → Toggle Developer Tools → Console tab
- **Trace Logs**: Enable via `legesher.trace.server` setting

### Packaging

Create a `.vsix` file for distribution:

```bash
npm run package
```

This creates `legesher-vscode-0.1.2.vsix` that can be installed in VS Code.

## Making Changes

### Code Style

- Follow TypeScript best practices
- Use meaningful variable and function names
- Add JSDoc comments for public APIs
- Run `npm run lint` before committing

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:

```text
feat(extension): add language selector status bar item
fix(client): handle server connection timeout
docs(readme): update installation instructions
```

### Branch Naming

```text
<type>/<issue-key>-<short-description>

Examples:
- feat/core-361-vs-code-extension-setup
- fix/core-362-connection-timeout
- docs/core-363-update-readme
```

### Pull Request Process

1. Create a new branch from `main`
1. Make your changes
1. Run `npm run lint` and fix any issues
1. Test thoroughly in Extension Development Host
1. Update documentation if needed
1. Commit with conventional commit messages
1. Push to your fork
1. Open a Pull Request

## Architecture Guidelines

### Extension Entry Point (`extension.ts`)

The main entry point should:

- Initialize the extension
- Create UI elements (status bar, commands)
- Start the language client
- Handle activation/deactivation

**Key functions**:

- `activate()`: Called when extension activates
- `deactivate()`: Called when extension deactivates

### LSP Client (`client.ts`)

The LSP client should:

- Configure server options (command, args, environment)
- Configure client options (document selectors, synchronization)
- Handle errors and connection issues
- Provide validation utilities

### Configuration

Add new settings in `package.json` under `contributes.configuration`:

```json
{
  "contributes": {
    "configuration": {
      "properties": {
        "legesher.newSetting": {
          "type": "string",
          "default": "value",
          "description": "Description of the setting"
        }
      }
    }
  }
}
```

Access in code:

```typescript
const config = vscode.workspace.getConfiguration('legesher');
const value = config.get<string>('newSetting');
```

### Adding Commands

1. Register in `package.json`:

```json
{
  "contributes": {
    "commands": [
      {
        "command": "legesher.myCommand",
        "title": "Legesher: My Command"
      }
    ]
  }
}
```

2. Implement in `extension.ts`:

```typescript
context.subscriptions.push(
    vscode.commands.registerCommand('legesher.myCommand', async () => {
        // Command implementation
    })
);
```

## Debugging

### Debug Extension

1. Press `F5` to launch Extension Development Host
2. Set breakpoints in TypeScript files
3. Debugger will pause at breakpoints

### Debug Language Server

The language server runs as a separate process. To debug:

1. Add launch configuration in `.vscode/launch.json`
2. Use `--log-file` flag with the server command
3. Check server logs for issues

### Common Issues

**Extension doesn't activate**:

- Check `activationEvents` in `package.json`
- Verify you have a Python file open
- Check Developer Tools Console for errors

**Language server connection fails**:

- Verify `legesher-language-server` is in PATH
- Check `legesher.serverCommand` setting
- Enable trace logs (`legesher.trace.server: "verbose"`)

**TypeScript compilation errors**:

- Run `npm install` to ensure dependencies are up to date
- Check `tsconfig.json` settings
- Verify TypeScript version: `npx tsc --version`

## Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [vscode-languageclient](https://github.com/microsoft/vscode-languageserver-node)

## Getting Help

- Check existing [issues](https://github.com/madiedgar/legesher/issues)
- Join our [Discord community](https://legesher.io/discord)
- Read the [documentation](https://docs.legesher.io)

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct](../../CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to Legesher!** 🌍✨
