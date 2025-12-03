# Legesher Language Server

> Language Server Protocol implementation for multilingual Python programming

**Status**: Production-Ready (Pre-Beta) | **Version**: 0.0.x | **Python**: 3.10-3.14 | **Languages**: 27+

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

✅ **Pylance Integration** (CORE-360)

- PylanceProxy for real-time code translation
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
│  legesher-core      │
│  legesher-i18n      │
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

**Status:** 🔄 In Progress (Error templates complete, provider integration pending)

**Completed:**

- 41 error message templates covering 17 Python error types
- Multi-language support (English, Spanish, Arabic)
- Variable name preservation
- Template-based translation with caching

**Pending:**

- Integration with diagnostic provider
- AST-based error detection
- LSP diagnostic object creation

**Supported Error Types:**

- SyntaxError, IndentationError, NameError
- TypeError, AttributeError, ImportError
- ValueError, KeyError, IndexError, ZeroDivisionError

**Example Translation:**

English: `SyntaxError: expected ':'`
Spanish: `ErrorDeSintaxis: se esperaba ':'`
Arabic: `خطأ في بناء الجملة: متوقع ':'`

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

**Test Results (306 tests passing):**

- All server integration tests passing
- All provider tests passing
- Some test fixtures need updating for new provider behavior (tests expected stubs, got working providers)

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

**Complete:**

- ✅ `config.py`: 100% coverage (CORE-356)
- ✅ `document.py`: 100% coverage (CORE-356)
- ✅ `providers/hover.py`: 581 test lines, comprehensive coverage (CORE-357)
- ✅ `providers/completion.py`: 786 test lines, comprehensive coverage (CORE-358)
- ✅ `utils/error_templates.py`: 641 test lines, 95% coverage (CORE-359 utility)

**In Progress:**

- 🔄 `providers/diagnostic.py`: Stub, needs integration with error_templates (CORE-359)
- 🔄 `server.py`: Integration testing (CORE-360)

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
| `textDocument/diagnostic` | 🔄 Stub (templates ready) | CORE-359 |

## For VS Code Extension Developers

The VS Code extension (Cycle 8) will:

1. Start `legesher-lsp` as a child process
2. Connect via stdio transport
3. Configure source/target languages via initialization params
4. Handle LSP requests/responses
5. Render translated content in custom UI

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

Multiple licenses apply - see LICENSE files in the monorepo root.

## Related Documentation

- [Architecture Documentation](ARCHITECTURE.md)
- [Complete Architecture Guide](../../../planning/architecture/complete-architecture-guide.md)
- [Implementation Roadmap](../../../planning/architecture/implementation-roadmap.md)
- [MLCP Specification](../../../planning/architecture/mlcp-v1.md)

## Roadmap

### Completed

**Phase 1: Foundation (CORE-356)** ✅

- LSP server infrastructure
- Document management
- Configuration system

**Phase 2A: Python Language Server - Core Providers** ✅

- ✅ CORE-357: Hover provider (translated docstrings)
- ✅ CORE-358: Completion provider (localized keywords & symbols)

### In Progress

**Phase 2A: Diagnostic Provider (CORE-359)**

- ✅ Error message templates (41 templates, 17 error types)
- 🔄 Diagnostic provider integration (AST parsing, error detection)

**Phase 2A: Python Language Server - Integration (CORE-360)**

- 🔄 CORE-360: Pylance integration

### Upcoming

**Cycle 8: VS Code Extension**

- Custom UI components
- End-to-end integration testing

---

**Part of the Legesher Project** | [legesher.io](https://legesher.io)
