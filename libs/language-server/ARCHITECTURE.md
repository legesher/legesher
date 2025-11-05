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
│  └── Providers                                  │
│      ├── Hover (CORE-357) ✅                    │
│      ├── Completion (CORE-358) ✅               │
│      └── Diagnostic (CORE-359) 🔄               │
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

**Location:** `legesher_language_server/providers/`

**Status:**

- ✅ `hover.py`: Complete (CORE-357) - 347 lines
- ✅ `completion.py`: Complete (CORE-358) - 500 lines
- 🔄 `diagnostic.py`: Stub (CORE-359) - 39 lines, needs integration with error_templates.py

**Utilities:**

- ✅ `utils/error_templates.py`: Complete - 401 lines, 41 templates, 17 error types
- ✅ `utils/keyword_docs.py`: Complete - 235 lines

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

### Diagnostic Flow (CORE-359)

```
1. IDE sends textDocument/diagnostic request
   ↓
2. provide_diagnostics() called
   ↓
3. DiagnosticProvider._parse_syntax_errors()
   ↓
4. For each error:
   - Extract error type and message
   - _extract_variables() finds identifiers to preserve
   - _get_translation_template() looks up template
   - _translate_error_message() performs translation with caching
   - _create_diagnostic() creates LSP Diagnostic object
   ↓
5. Return list of translated Diagnostic objects to IDE
```

## Provider Details

### Diagnostic Provider (CORE-359)

**Location:** `legesher_language_server/providers/diagnostic.py`

**Status:** 🔄 In Progress

**Completed:**

- ✅ Error message templates utility (`utils/error_templates.py`)
  - 41 error message templates
  - 17 Python error types
  - Multi-language support (English, Spanish, Arabic)
  - Variable substitution with `.format()`
  - 641 test lines, 95% coverage

**Pending Integration:**

- Main diagnostic provider (`diagnostic.py` currently a stub)
- AST-based error detection
- Integration with error templates
- LSP Diagnostic object creation
- Variable name preservation in error messages

**Planned Architecture:**

```
User Code → AST Parser → Error Detection → Translation → LSP Diagnostic
                                                ↓
                                        ErrorMessageTemplates ✅
                                                ↓
                                        Module-level Cache
```

**Planned Features:**

- Parse Python code using AST
- Detect syntax errors, indentation errors, tab errors
- Translate error messages using templates
- Preserve variable names and identifiers
- Create LSP Diagnostic objects
- Performance: <50ms for cached errors, <500ms for new errors

**Variable Preservation (Planned):**

Variables, function names, and module names will never be translated:

```python
# English
NameError: name 'imprimir' is not defined

# Spanish (planned)
ErrorDeNombre: el nombre 'imprimir' no está definido

# 'imprimir' is preserved in both
```

**Future Integration (CORE-360):**

- Pylance integration for semantic errors
- Type checker integration (mypy, pyright)
- Linter integration (ruff, pylint)

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

### Test Coverage

**Complete:**

- ✅ `config.py`: 100% (CORE-356)
- ✅ `document.py`: 100% (CORE-356)
- ✅ `providers/hover.py`: 581 test lines (CORE-357)
- ✅ `providers/completion.py`: 786 test lines (CORE-358)
- ✅ `utils/error_templates.py`: 641 test lines, 95% coverage (CORE-359)

**In Progress:**

- 🔄 `providers/diagnostic.py`: Stub, no tests yet (CORE-359)
- 🔄 `server.py`: Integration testing (CORE-360)

## Integration with VS Code (Cycle 8)

The VS Code extension will:

1. Start `legesher-lsp` process
2. Connect via stdio transport
3. Configure source/target languages
4. Handle LSP requests/responses
5. Render translated content in UI

See [Integration Guide](docs/integration-guide.md) for details.

## Future Work

### CORE-359: Complete Diagnostic Provider

- Integrate error_templates.py with diagnostic.py provider
- Implement AST-based error detection
- Create LSP Diagnostic objects
- Add variable name preservation

### CORE-360: Pylance Integration

- Proxy Python intelligence
- Combine Pylance + translation
- Seamless developer experience
- Advanced semantic error detection

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
