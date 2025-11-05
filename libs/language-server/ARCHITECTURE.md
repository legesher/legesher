# Legesher Language Server - Architecture

## Overview

The Legesher Language Server provides LSP (Language Server Protocol) support for multilingual Python programming. It enables IDE features like hover tooltips, code completion, and diagnostics in the user's native language.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  IDE/Editor (VS Code, Cursor, Zed)              │
│  └─ LSP Client                                  │
└─────────────────┬───────────────────────────────┘
                  │ LSP Protocol (JSON-RPC via stdio)
┌─────────────────▼───────────────────────────────┐
│  legesher-language-server                       │
│  ├── Server (pygls 1.3)                         │
│  ├── Document Manager                           │
│  ├── Configuration System                       │
│  └── Providers (stubs)                          │
│      ├── Hover (CORE-357)                       │
│      ├── Completion (CORE-358)                  │
│      └── Diagnostic (CORE-359)                  │
└─────────────────┬───────────────────────────────┘
                  │ Dependencies
┌─────────────────▼───────────────────────────────┐
│  legesher-core (Phase 1)                        │
│  └── TokenTranslator                            │
│  legesher-i18n (Phase 1)                        │
│  └── LanguagePack                               │
└─────────────────────────────────────────────────┘
```

## Components

### 1. Server (`server.py`)

**Responsibility:** Core LSP server using pygls framework

**Features:**

- Server lifecycle management (initialize, shutdown)
- Document synchronization (open, change, close)
- Feature registration and routing
- Provider coordination

**Status:** CORE-356 (Foundation implemented, integration testing needed)

### 2. Document Manager (`document.py`)

**Responsibility:** Track open documents and their state

**Features:**

- Document lifecycle tracking
- Version management
- Translation caching
- Line-level access

**Status:** ✅ Complete (100% test coverage)

### 3. Configuration (`config.py`)

**Responsibility:** Server configuration management

**Features:**

- Environment variable loading
- Python version detection
- Language validation
- Cache configuration

**Status:** ✅ Complete (100% test coverage)

### 4. Providers (`providers/`)

**Responsibility:** LSP feature implementations

**Modules:**

- `hover.py` - Translated docstrings and tooltips (CORE-357)
- `completion.py` - Localized code completion (CORE-358)
- `diagnostic.py` - Translated error messages (CORE-359)

**Status:** 🔄 Stubs created (full implementation in subsequent issues)

## Data Flow

### Document Open Flow

```
1. IDE opens file
   ↓
2. LSP: textDocument/didOpen notification
   ↓
3. DocumentManager.open_document()
   ↓
4. DocumentState created, tracked
```

### Translation Flow (CORE-357+)

```
1. User requests hover/completion
   ↓
2. Provider retrieves DocumentState
   ↓
3. Extract code element
   ↓
4. TokenTranslator translates (legesher-core)
   ↓
5. Cache translated result
   ↓
6. Return to IDE
```

## Configuration

### Environment Variables

- `LEGESHER_SOURCE_LANG` - Source code language (default: `en`)
- `LEGESHER_TARGET_LANG` - Target display language (default: `es`)
- `LEGESHER_PYTHON_VERSION` - Python version (auto-detected)
- `LEGESHER_CACHE_SIZE` - Translation cache size (default: 1000)
- `LEGESHER_CACHE_TTL` - Cache TTL in seconds (default: 3600)
- `LEGESHER_LOG_LEVEL` - Logging level (default: INFO)

### CLI Usage

```bash
# Basic usage
legesher-lsp --target-lang es

# With Python version
legesher-lsp --target-lang fr --python-version 3.11

# With debug logging
legesher-lsp --target-lang es --log-level DEBUG
```

## Dependencies

### Core Dependencies

- `pygls>=1.3.0,<2.0.0` - LSP framework
- `pydantic>=2.5.0` - Configuration validation
- `lru-dict>=1.3.0` - LRU caching

### Dev Dependencies

- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting

## Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=legesher_language_server

# Run specific test module
pytest tests/test_config.py -v

# Run with debug output
pytest tests/ -v -s
```

### Test Coverage (CORE-356)

- `config.py`: 100% ✅
- `document.py`: 100% ✅
- `providers/`: Stubs (tested in CORE-357, 358, 359)
- `server.py`: Integration testing in progress

## Integration with VS Code (Cycle 8)

The VS Code extension will:

1. Start `legesher-lsp` process
2. Connect via stdio transport
3. Configure source/target languages
4. Handle LSP requests/responses
5. Render translated content in UI

See [Integration Guide](docs/integration-guide.md) for details.

## Future Work

### CORE-357: Hover Provider

- Translate docstrings
- Show type hints in target language
- Cache hover results

### CORE-358: Completion Provider

- Translate keywords
- Translate builtins
- Context-aware suggestions

### CORE-359: Diagnostic Provider

- Translate Python error messages
- Translate syntax errors
- Translate type errors

### CORE-360: Pylance Integration

- Proxy Python intelligence
- Combine Pylance + translation
- Seamless developer experience

## Performance Considerations

- **Initialization**: <1s target
- **Document Sync**: <10ms target
- **Caching**: LRU with TTL to reduce translation overhead
- **Async**: All LSP handlers are async for non-blocking I/O

## Security

- Local-first processing (no cloud required)
- No telemetry or analytics
- Input validation on all LSP messages
- Sandboxed via stdio transport

## References

- [LSP Specification](https://microsoft.github.io/language-server-protocol/)
- [pygls Documentation](https://pygls.readthedocs.io/)
- [Legesher Architecture Guide](../../../planning/architecture/complete-architecture-guide.md)
