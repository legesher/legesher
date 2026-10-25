# Legesher Language Server

> Language Server Protocol implementation for multilingual Python programming

**Status**: Pre-Beta | **Python**: 3.10-3.14 | **Languages**: 56 | **Version**: see `pyproject.toml`

## Overview

The Legesher Language Server provides LSP support for coding in Python using your native language. It
enables real-time IDE features like hover tooltips, code completion, and diagnostics - all translated to
your preferred language.

### What's Included

✅ **Complete LSP Server** (pygls 2.0, Python 3.13 compatible)

- Language server using `pygls 2.0` framework
- Document state management with version tracking
- Configuration system with Pydantic validation
- Complete LSP lifecycle support

✅ **Four Complete Providers**

- **Hover Provider** (CORE-357): Translated docstrings, keyword docs, cultural comments with LRU caching
- **Completion Provider** (CORE-358): Localized keywords, builtins, user symbols with fuzzy matching
- **Diagnostic Provider** (CORE-359): Translated error messages (41 templates, 17 error types)
- **Semantic Tokens Provider** (CORE-450): Syntax highlighting for translated keywords

✅ **Enhanced Python intelligence** (CORE-360)

- EnhancedIntelligenceProxy for real-time code translation
- Caching with LanguagePackLoader (CORE-446)
- Thread-safe position mapping

## Quick Start

### Installation

```bash
# Using uv
uv pip install -e .

# Using pip
pip install -e .
```

### Usage

```bash
# Start server with Spanish
legesher-lsp --target-lang es

# With Python version specified
legesher-lsp --target-lang fr --python-version 3.11

# With debug logging
legesher-lsp --target-lang es --log-level DEBUG

# Use environment variables
export LEGESHER_TARGET_LANG=es
legesher-lsp
```

### In an editor

The server speaks LSP over stdio, so any LSP client can start `legesher-lsp`.
The Legesher VS Code extension runs it by default: its `legesher.serverCommand`
setting is `legesher-lsp`, so the command has to be on the `PATH` VS Code sees,
or the setting has to hold its full path.

### Configuration

**Environment Variables:**

- `LEGESHER_SOURCE_LANG` - Source code language (default: `en`)
- `LEGESHER_TARGET_LANG` - Target display language (default: `es`)
- `LEGESHER_PYTHON_VERSION` - Python version (auto-detected if not set)
- `LEGESHER_CACHE_SIZE` - Translation cache size (default: 1000)
- `LEGESHER_CACHE_TTL` - Cache TTL in seconds (default: 3600)
- `LEGESHER_LOG_LEVEL` - Logging level (default: INFO)

**CLI Arguments:**

```bash
legesher-lsp --help
```

### Logging

The server logs through the LSP's `window/logMessage` notification, so each
line reaches your editor's output channel at the severity it was written at.
stderr carries only what happens before a client connects, or what would
otherwise be lost.

Nothing verbose is logged by default, and no JSON-RPC payload is: those
payloads carry text out of the file you are editing. Set the client's trace
level to see more. In VS Code that is `legesher.trace.server`:

- `off` (default): the server's own messages, warnings and errors. No text out
  of your file is logged at this level, though an error can still name the
  document's path and the position that failed.
- `messages`: adds the server's debug detail, and some of that detail is read
  out of your file, including the identifier under the cursor, the hover text
  rendered for it, the source line of a syntax error, the path of every
  document you open, change or close, and whatever the bundled Pyright backend
  writes to its own stderr.
- `verbose`: adds full LSP payloads on top, so whole documents and every
  request and response body go into the log as well.

`LEGESHER_LOG_LEVEL=DEBUG` raises verbosity from the first line, before a
client has connected to ask for it. It reaches the same debug lines `messages`
does, so it carries the same caveat.

## Architecture

```text
┌─────────────────────┐
│  IDE/Editor         │
│  (VS Code, Zed)     │
└──────────┬──────────┘
           │ LSP (stdio)
┌──────────▼──────────┐
│  Language Server    │
│  ├─ Server          │
│  ├─ DocumentManager │
│  ├─ Config          │
│  └─ Providers       │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  legesher-i18n      │
│  (language packs)   │
└─────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Features

### Hover Provider (CORE-357)

Translates Python docstrings and provides keyword documentation in the target language.

**Status:** ✅ Complete

**Features:**

- Docstring translation for functions, classes, modules
- Keyword documentation in target language
- Cultural comments for context
- Fast caching for repeated hovers

### Completion Provider (CORE-358)

Provides localized code completion suggestions.

**Status:** ✅ Complete

**Features:**

- Localized Python keywords
- Translated built-in functions
- User-defined symbols with context
- Fuzzy matching for better UX

### Diagnostic Provider (CORE-359)

Translates Python error messages while preserving code identifiers.

**Status:** ✅ Complete. The provider is registered on `textDocument/diagnostic` and parses the document for
syntax errors before translating the message.

**Features:**

- 41 error message templates covering 17 Python error types
- Translated messages for English, Spanish, and Arabic. Other languages get the untranslated CPython message
- Variable name preservation
- Template-based translation with caching

**Error Types With Templates:**

- AssertionError, AttributeError, FileNotFoundError, ImportError, IndentationError
- IndexError, KeyError, KeyboardInterrupt, ModuleNotFoundError, NameError
- RecursionError, RuntimeError, StopIteration, SyntaxError, TypeError
- ValueError, ZeroDivisionError

**Example Translation:**

The diagnostic carries the message body only; the exception type name is not prefixed.

English: `expected ':'`
Spanish: `se esperaba ':'`
Arabic: `متوقع ':'`

A message with no matching template is passed through in English rather than half-translated. For the
localized *type* names, see the language packs, which `legesher-runtime` uses when rendering tracebacks.

## Migration Notes

### pygls 2.0 Migration (CORE-448)

**Migration completed**: 2025-11-29

The language server has been successfully migrated from pygls 1.3.1 to pygls 2.0.0, resolving Python 3.13
compatibility issues and enabling full integration testing.

**Key Changes:**

- **Import path updated**: `from pygls.server import LanguageServer` → `from pygls.lsp.server import LanguageServer`
- **Python 3.13 support**: pygls 2.0 fixes bound method compatibility issues with Python 3.13
- **Handler signatures**: No changes required - existing handler signatures remain compatible
- **Test coverage**: Increased from 21% to 70% by un-skipping integration tests
- **Dependencies**: Also upgraded `lsprotocol` from 2023.0.1 to 2025.0.0

**What Works:**

✅ All LSP lifecycle methods (initialize, shutdown, didOpen, didChange, didClose)
✅ Hover provider with Spanish/Arabic keyword translations
✅ Completion provider with 67+ keyword and builtin suggestions
✅ Diagnostic provider with translated error messages
✅ Python 3.13 compatibility verified

**Breaking Changes:**

None for users. This is an internal dependency upgrade with no API changes.

**For Contributors:**

If you encounter import errors with `pygls.server.LanguageServer`, update to use `pygls.lsp.server.LanguageServer`.

## Development

### Running Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=legesher_language_server --cov-report=term-missing

# Specific test file
pytest tests/test_config.py -v

# With debug output
pytest tests/ -v -s --log-cli-level=DEBUG
```

### Test Coverage

Most modules have a matching test module under `tests/`. Two do not: `incremental_translator.py` is
exercised only indirectly, through the `enhanced_intelligence` tests, and `__main__.py` has no test at all.
Run the suite with coverage to see the current numbers rather than trusting a figure written down here:

```bash
pytest tests/ --cov=legesher_language_server --cov-report=term-missing
```

### Code Quality

```bash
# Type checking
mypy legesher_language_server/

# Linting
ruff check legesher_language_server/

# Format
ruff format legesher_language_server/
```

## LSP Methods Supported

| Method | Status | Issue |
|--------|--------|-------|
| `initialize` | ✅ Implemented | CORE-356 |
| `initialized` | ✅ Implemented | CORE-356 |
| `shutdown` | ✅ Implemented | CORE-356 |
| `textDocument/didOpen` | ✅ Implemented | CORE-356 |
| `textDocument/didChange` | ✅ Implemented | CORE-356 |
| `textDocument/didClose` | ✅ Implemented | CORE-356 |
| `textDocument/hover` | ✅ Implemented | CORE-357 |
| `textDocument/completion` | ✅ Implemented | CORE-358 |
| `textDocument/diagnostic` | ✅ Implemented | CORE-359 |
| `textDocument/semanticTokens/full` | ✅ Implemented | CORE-450 |
| `legesher/status` (request) | ✅ Implemented | CORE-1886, CORE-1976 |
| `legesher/documentLanguage` (notification) | ✅ Implemented | CORE-1976 |

`legesher/documentLanguage` carries `{uri, language}`: the language one document
is written in. The server answers every request about that document in its
language, and falls back to the configured file language for a document it has
not been told about. `legesher/status` reports whether enhanced intelligence is
running and, under `documents`, the language each open document is served in,
with the reason when no pack can serve it.

## For VS Code Extension Developers

The [Legesher VS Code extension](../vs-code/README.md) does this, and any other LSP client would do the same:

1. Start `legesher-lsp` as a child process
2. Connect via stdio transport
3. Configure the source, file and working languages via initialization params
4. Send `legesher/documentLanguage` for each document just before its `didOpen`,
   and again when the language you resolve for it changes
5. Handle LSP requests/responses
6. Render translated content in custom UI

Example VS Code client configuration:

```typescript
const serverOptions: ServerOptions = {
  command: 'legesher-lsp',
  args: ['--target-lang', targetLang],
  options: { env: { LEGESHER_LOG_LEVEL: 'DEBUG' } }
};
```

## Dependencies

### Runtime

- `pygls>=2.0.0,<3.0.0` - LSP framework (**Updated to v2.0** - CORE-448)
- `pydantic>=2.5.0` - Configuration validation
- `lru-dict>=1.3.0` - LRU caching
- `pyyaml>=6.0.0` - Language pack YAML loading
- `legesher-i18n` - Language pack loading

### Development

- `pytest>=7.4.0`
- `pytest-asyncio>=0.21.0`
- `pytest-cov>=4.1.0`
- `mypy>=1.5.0`
- `ruff>=0.1.0`

## Contributing

This package is part of the Legesher monorepo. See the [main README](../../README.md) for contribution guidelines.

## License

Apache License 2.0 - see [LICENSE](LICENSE).

## Related Documentation

- [Architecture Documentation](ARCHITECTURE.md)
- [Test Quick Reference](TEST_QUICK_REFERENCE.md)
- [Monorepo README](../../README.md)

---

**Part of the Legesher Project** | [legesher.io](https://legesher.io)
