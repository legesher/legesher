# Legesher Language Server

> Language Server Protocol implementation for multilingual Python programming

**Status**: Foundation Complete (CORE-356) | **Phase**: 2A - Python Language Server | **Cycle**: 7

## Overview

The Legesher Language Server provides LSP support for coding in Python using your native language. It enables real-time IDE features like hover tooltips, code completion, and diagnostics - all translated to your preferred language.

### What's Included (CORE-356)

✅ **Core Infrastructure**

- LSP server using `pygls 1.3`
- Document management with version tracking
- Configuration system (env vars + CLI args)
- Server lifecycle (initialize, shutdown, document sync)

🔄 **Provider Stubs** (Full implementation in CORE-357, 358, 359)

- Hover provider (translated docstrings)
- Completion provider (localized keywords)
- Diagnostic provider (translated errors)

### What's Next

- **CORE-357**: Hover provider implementation
- **CORE-358**: Completion provider implementation
- **CORE-359**: Diagnostic translator implementation
- **CORE-360**: Pylance integration
- **Cycle 8**: VS Code extension with custom UI

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

```
legesher-lsp --help
```

## Architecture

```
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

### Test Coverage (CORE-356)

- ✅ `config.py`: 100% coverage
- ✅ `document.py`: 100% coverage
- 🔄 `server.py`: Integration testing (VS Code integration in Cycle 8)
- 🔄 `providers/`: Stubs (full tests in CORE-357, 358, 359)

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
| `textDocument/hover` | 🔄 Stub | CORE-357 |
| `textDocument/completion` | 🔄 Stub | CORE-358 |
| `textDocument/diagnostic` | 🔄 Stub | CORE-359 |

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

- `pygls>=1.3.0,<2.0.0` - LSP framework
- `pydantic>=2.5.0` - Configuration validation
- `lru-dict>=1.3.0` - LRU caching

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

**Completed (CORE-356)**

- ✅ LSP server foundation
- ✅ Document management
- ✅ Configuration system
- ✅ Provider stubs

**In Progress (Cycle 7)**

- 🔄 CORE-357: Hover provider
- 🔄 CORE-358: Completion provider
- 🔄 CORE-359: Diagnostic translator
- 🔄 CORE-360: Pylance integration

**Upcoming (Cycle 8)**

- VS Code extension
- Custom UI components
- End-to-end integration testing

---

**Part of the Legesher Project** | [legesher.io](https://legesher.io)
