# Legesher Language Server - Architecture

## Overview

The Legesher Language Server provides LSP (Language Server Protocol) support for
multilingual Python programming. It enables IDE features like hover tooltips,
code completion, and diagnostics in the user's native language.

## Architecture

```text
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

```text
1. IDE opens file
   ↓
2. LSP: textDocument/didOpen notification
   ↓
3. DocumentManager.open_document()
   ↓
4. DocumentState created, tracked
```

### Translation Flow (CORE-357+)

```text
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

```text
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

```text
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

## Pylance Integration (CORE-360)

### Overview

The Pylance integration provides advanced Python intelligence (type checking,
advanced hover, go-to-definition) for localized code through a translation
proxy architecture.

**Status**: Foundation ✅ Complete | LSP Communication 🚧 In Progress

### Architecture

```text
┌─────────────────────────────────────────────────┐
│  User Code (Localized)                          │
│  definir foo(x: entero) -> cadena:              │
└──────────────────┬──────────────────────────────┘
                   │ Translation Layer
┌──────────────────▼──────────────────────────────┐
│  Hybrid Python (TypeAlias)                      │
│  from typing import TypeAlias                   │
│  entero: TypeAlias = int                        │
│  cadena: TypeAlias = str                        │
│  def foo(x: entero) -> cadena:                  │
└──────────────────┬──────────────────────────────┘
                   │ Forward to Pylance
┌──────────────────▼──────────────────────────────┐
│  Pylance/Pyright                                │
│  Type checks with TypeAlias understanding       │
│  Returns diagnostics, hover, etc.               │
└──────────────────┬──────────────────────────────┘
                   │ Translate back
┌──────────────────▼──────────────────────────────┐
│  User sees results in original language         │
└─────────────────────────────────────────────────┘
```

### Components

#### 1. SourceMap (`source_map.py`)

Bidirectional position mapping between localized and English code.

**Purpose**: When keywords change length (e.g., `definir` (7) to `def` (3)),
line/column positions shift. SourceMap tracks these shifts for accurate
error reporting.

**Algorithm**: Binary search for O(log n) position lookups.

**Example**:

```python
# Spanish position (0, 10) → English position (0, 6)
source_map.to_english(Position(0, 10))  # Returns Position(0, 6)
source_map.to_original(Position(0, 6))  # Returns Position(0, 10)
```

**Coverage**: 80.43% with 20 comprehensive tests

#### 2. TypeAliasGenerator (`type_alias_generator.py`)

**The Key Innovation**: Generates Python `TypeAlias` statements to preserve localized type hints.

**Problem**: Pylance expects English type names (`int`, `str`), but users write localized types (`entero`, `cadena`).

**Solution**: Instead of translating (losing semantics), generate TypeAlias:

```python
from typing import TypeAlias
entero: TypeAlias = int
cadena: TypeAlias = str

def foo(x: entero) -> cadena:  # ✅ Valid Python, Pylance understands!
    return str(x)
```

**Why This Works**:

- Pylance understands `entero` as `int` via TypeAlias
- Type checking works correctly
- Error messages preserve user's original type names
- Zero translation loss
- Extensible to other languages (JS: `type entero = number;`)

**Features**:

- AST-based type hint extraction
- Support for generics (List[entero], Dict[cadena, entero])
- Union types and Optional
- String annotations (forward references)

**Coverage**: 20 comprehensive tests, all passing

#### 3. IncrementalTranslator (`incremental_translator.py`)

Translation engine with performance optimizations.

**Features**:

- **Content-based caching**: SHA256 hashing for instant cache hits
- **Bidirectional translation**: Spanish ↔ English
- **Integrated SourceMapBuilder**: Builds position mappings during translation
- **Automatic TypeAlias injection**: Prepends TypeAlias block to translated code

**Performance**:

- Target: <50ms translation overhead
- Cache hits: <5ms
- Strategy: Hash unchanged files for instant cache hits

**Example**:

```python
translator = IncrementalTranslator(source_lang="es", target_lang="en", ...)
result = await translator.translate_to_english(spanish_code)
# result.translated_code: English code with TypeAlias
# result.source_map: Position mapping
# result.content_hash: Cache key
```

#### 4. PylanceProxy (`pylance_proxy.py`)

Manages Pyright subprocess and coordinates translation.

**Responsibilities**:

- Start/stop Pyright subprocess
- Auto-detect Pyright installation
- Forward LSP requests with translation
- Graceful degradation when Pylance unavailable
- Performance monitoring

**Lifecycle**:

```python
# Initialization
proxy = PylanceProxy(config)

# On server start
await proxy.start()  # Starts Pyright subprocess

# On hover request
hover = await proxy.forward_hover(params)

# On server shutdown
await proxy.stop()  # Graceful Pyright termination
```

**Auto-detection**: Checks npm global, system PATH, configured path

**Graceful Degradation**: Falls back to basic providers if Pyright not found

### Translation Flow

#### Hover Example

```text
1. User hovers at Position(0, 10) in Spanish code
      ↓
2. Translate document to English (cached if unchanged)
      ↓
3. Map position: Spanish (0, 10) → English (0, 6)
      ↓
4. Send textDocument/hover to Pyright with English position
      ↓
5. Pyright returns hover info at English position
      ↓
6. Map position back: English (0, 6) → Spanish (0, 10)
      ↓
7. Translate hover content (if needed)
      ↓
8. Return to user
```

#### Diagnostic Example

```text
1. Document changed notification
      ↓
2. Translate document to English + generate TypeAlias
      ↓
3. Send textDocument/diagnostic to Pyright
      ↓
4. Pyright returns type errors
      ↓
5. Map error positions back to Spanish
      ↓
6. Translate error messages using error_templates
      ↓
7. Merge with basic diagnostics (syntax errors)
      ↓
8. Return combined diagnostics to user
```

### Performance Considerations

**Target**: <50ms overhead per request

**Strategies**:

1. **Content-based caching**: Unchanged files = instant cache hit
2. **Lazy translation**: Only translate on first request
3. **Position mapping optimization**: O(log n) binary search
4. **TypeAlias caching**: Reuse generated aliases
5. **Speculative translation**: Pre-translate likely requests

**Monitoring**:

```python
stats = proxy.get_performance_stats()
# Returns: request_count, average_latency_ms, cache_size, etc.
```

### Configuration

```python
# Environment variables
LEGESHER_PYLANCE_ENABLED=true    # Enable/disable Pylance
LEGESHER_PYLANCE_PATH=/path/to/pyright  # Custom path (optional)

# In code
config = LanguageServerConfig(
    pylance_enabled=True,
    pylance_path=None,  # Auto-detect
)
```

### Error Handling

**Pyright Not Found**:

```python
# Logs warning, disables Pylance features
logger.warning("Pyright not found. Install with: npm install -g pyright")
# Falls back to basic providers (hover, completion, diagnostics)
```

**Pyright Crashes**:

```python
# Detects process exit, logs error
# Falls back to basic providers
# Future: Auto-restart after delay
```

**Translation Errors**:

```python
# Returns original code unchanged
# Logs error for debugging
# Server remains functional
```

### Testing

**Unit Tests**: 40 tests, all passing

- SourceMap: 20 tests (80.43% coverage)
- TypeAliasGenerator: 20 tests (comprehensive)

**Integration Tests**: Planned

- Mock Pyright server
- End-to-end translation validation
- Performance benchmarks

**Real-world Scenarios**:

- Spanish function definitions
- Complex generic types
- Multi-line statements
- Error message translation

### Future Enhancements

**LSP Communication** (CORE-360 completion):

- Full JSON-RPC 2.0 implementation
- textDocument/hover with translation
- textDocument/diagnostic with merging
- Initialization handshake

**Advanced Features** (Future sprints):

- Go-to-definition across files
- Find references with translation
- Symbol renaming
- Code actions / quick fixes
- Workspace-wide symbol search

**Performance Optimizations** (Future sprints):

- Incremental document updates
- Streaming translation for large files
- Parallel translation requests
- Persistent cache across sessions

### Known Limitations

**Current** (Foundation phase):

- LSP communication not yet implemented (stubs in place)
- Hover/diagnostic forward returns None (falls back to basic providers)
- Integration tests pending

**Architectural**:

- Requires Pyright/Pylance installation (graceful degradation if missing)
- TypeAlias approach requires Python 3.10+ (typing.TypeAlias)
- Position mapping assumes keywords don't span multiple lines

### References

- [LSP Specification](https://microsoft.github.io/language-server-protocol/)
- [Pyright Documentation](https://github.com/microsoft/pyright)
- [TypeAlias (PEP 613)](https://peps.python.org/pep-0613/)
- [JSON-RPC 2.0](https://www.jsonrpc.org/specification)

---

## Future Work

### CORE-360: Complete Pylance Integration

- ✅ Foundation architecture (SourceMap, TypeAlias, Translator, Proxy)
- ✅ Comprehensive tests (40 tests passing)
- 🚧 LSP communication (JSON-RPC message passing)
- 📋 Integration tests with mock Pyright
- 📋 Performance benchmarks
- 📋 Documentation updates

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
