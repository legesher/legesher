# Changelog - legesher-language-server

All notable changes to legesher-language-server are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

## [0.1.2] - 2026-03-01

### Fixed

- Add MIT LICENSE file — package was legally unusable without it (CORE-622)
- Fix invalid author email domain in pyproject.toml (CORE-665)

### Changed

- **Hover Provider Performance**: Consolidated 4 `LanguagePackLoader.load()` calls into 1
- **Hover Provider Code Quality**: Extracted hardcoded Python version `"3.10"` to `DEFAULT_PYTHON_VERSION` class constant

### Added

- **Bilingual Hover Format**: Hover shows English documentation first, then target language translation
  - Format: `**keyword** — Python keyword` + English doc + divider + `**Legesher ({lang}):** translated`
  - Applies to both keywords and builtins

## [0.1.1] - 2026-01-27

### Changed

- **pygls 2.0 Migration** ([CORE-448](https://linear.app/legesher/issue/CORE-448))
  - Upgraded from pygls 1.3.1 to pygls 2.0.0 for Python 3.13 compatibility
  - Updated import path: `pygls.server.LanguageServer` → `pygls.lsp.server.LanguageServer`
  - Upgraded lsprotocol from 2023.0.1 to 2025.0.0
  - **Breaking**: None for end users (internal dependency upgrade only)
  - **Fixed**: Shutdown handler compatibility with Python 3.13
  - **Fixed**: Removed bound method `__dict__` errors on Python 3.13
  - **Improved**: Test coverage increased from 21% to 70% (306 tests now passing)
  - **Improved**: Un-skipped all integration tests previously blocked by Python 3.13 incompatibility
  - **Verified**: All LSP methods working (initialize, shutdown, didOpen, didChange, didClose)
  - **Verified**: All providers functional (hover, completion, diagnostic)

## [0.1.0] - 2025-11-07

### Added

- **LSP Server Foundation** ([#25](https://github.com/madiedgar/legesher/pull/25), [1f71c25](https://github.com/madiedgar/legesher/commit/1f71c25))
  - Complete Language Server Protocol implementation using `pygls` framework
  - Document state management with version tracking and change events
  - Configuration system with Pydantic validation and environment variable support
  - Full LSP lifecycle support (initialize, initialized, shutdown)
  - Document synchronization (didOpen, didChange, didClose)
  - CLI entry point with language and Python version configuration
  - Stub provider architecture (hover, completion, diagnostic)
  - Test coverage: 100% on config.py (114 tests lines), 100% on document.py (172 test lines)
  - Performance: Sub-millisecond document updates, efficient in-memory state management

- **Hover Provider** ([#26](https://github.com/madiedgar/legesher/pull/26), [9796f52](https://github.com/madiedgar/legesher/commit/9796f52))
  - Translates Python docstrings and provides keyword documentation in target language
  - Docstring translation for functions, classes, and modules
  - Keyword documentation with examples in target language (35 Python keywords)
  - Cultural comment support for @lang: annotations
  - LRU caching for improved performance on repeated hovers
  - Multi-language support (English, Spanish, Arabic, French, German, etc.)
  - AST-based symbol detection with fallback to regex parsing
  - Test coverage: 581 test lines, 77% coverage on hover.py, 80% on keyword_docs.py
  - Implementation: 341 lines (hover.py), 256 lines (keyword_docs.py)

- **Completion Provider** ([#28](https://github.com/madiedgar/legesher/pull/28), [a2d10bd](https://github.com/madiedgar/legesher/commit/a2d10bd))
  - Localized code completion suggestions for multilingual Python development
  - Python keyword completion with translations (if, for, while, def, class, etc.)
  - Built-in function completion (print, len, range, etc.) with localized names
  - User-defined symbol completion (functions, classes, variables from open documents)
  - Fuzzy matching for improved developer experience
  - Context-aware completion items with appropriate LSP CompletionItemKind
  - Efficient caching with configurable TTL and size limits
  - Test coverage: 786 test lines, comprehensive edge case coverage
  - Implementation: 489 lines (completion.py)
  - Performance: <5ms for keyword/builtin completions, <10ms for symbol extraction

- **Diagnostic Provider with Error Translation** ([#30](https://github.com/madiedgar/legesher/pull/30), [28a384c](https://github.com/madiedgar/legesher/commit/28a384c))
  - Translates Python error messages while preserving code identifiers
  - 41 error message templates covering 17 Python error types
  - Multi-language error messages (English, Spanish, Arabic)
  - Variable name preservation in translated errors
  - Template-based translation with intelligent placeholder substitution
  - AST-based error detection and location tracking
  - Supported error types:
    - SyntaxError, IndentationError, TabError, UnexpectedIndent
    - NameError, UnboundLocalError
    - TypeError, AttributeError, ImportError, ModuleNotFoundError
    - ValueError, KeyError, IndexError, ZeroDivisionError
    - FileNotFoundError, OSError, RuntimeError
  - Template caching for improved performance
  - Test coverage: 1,028 test lines (diagnostic_provider), 645 test lines (error_templates)
  - Coverage: 72% on diagnostic.py, 95% on error_templates.py
  - Implementation: 392 lines (diagnostic.py), 404 lines (error_templates.py)

- **Pylance Integration - Phase 1 Foundation** ([#33](https://github.com/madiedgar/legesher/pull/33), [a2186f5](https://github.com/madiedgar/legesher/commit/a2186f5))
  - Foundation architecture for Pylance semantic analysis integration
  - **SourceMap** (338 lines): Bidirectional position mapping between translated and canonical code
    - Line/column offset tracking with high precision
    - Efficient binary search for O(log n) lookups
    - Handles multi-line translations and RTL languages
    - Test coverage: 411 test lines, 20 comprehensive unit tests, 80.43% coverage
  - **TypeAliasGenerator** (315 lines): Generates Python type stubs for translated keywords
    - Creates .pyi stub files for IDE type checking
    - Version-aware type alias generation (Python 3.10-3.13)
    - Preserves Python semantics while enabling native language keywords
    - Test coverage: 319 test lines, 20 comprehensive unit tests
  - **IncrementalTranslator** (261 lines): Optimized incremental translation for real-time editing
    - Efficient diff-based translation for document changes
    - Caches unchanged regions to minimize translation overhead
    - Handles partial document updates with line-level granularity
  - **PylanceProxy** (681 lines): LSP proxy layer for Pylance communication
    - Manages Pylance subprocess lifecycle (start, stop, restart)
    - Translates LSP messages between Legesher and Pylance
    - Document synchronization with automatic translation
    - Cache management for translated documents and type stubs
    - Error handling and graceful degradation
    - Test coverage: 235 test lines (edge cases), 10 comprehensive integration tests
  - Total implementation: 1,595 lines across 4 core components
  - Total test coverage: 965 test lines, 50+ tests, all passing
  - **Status**: Phase 1 Complete (Foundation & Architecture)
  - **Pending**: Phase 2 (Type Inference), Phase 3 (Diagnostics), Phase 4 (Performance)

### Performance

- **Hover Provider**: <5ms per hover with LRU caching
- **Completion Provider**: <5ms for keywords/builtins, <10ms for symbol extraction
- **Diagnostic Provider**: <50ms for full document analysis
- **SourceMap Lookups**: O(log n) with binary search, <1ms for typical files
- **Incremental Translation**: 10-100x faster than full re-translation for small edits
- **Document Synchronization**: Sub-millisecond in-memory state updates
- **Cache Performance**: LRU cache with configurable size (default 1000 items) and TTL (default 3600s)

### Test Coverage

- **Total Test Lines**: 4,559 lines across all test files
- **Config & Document**: 100% coverage (286 test lines)
- **Hover Provider**: 77% coverage (581 test lines)
- **Completion Provider**: Comprehensive coverage (786 test lines)
- **Diagnostic Provider**: 72% coverage (1,673 test lines including error templates)
- **Pylance Integration**: 80.43% coverage on SourceMap (965 test lines)
- **Overall**: High coverage with comprehensive edge case testing

### Technical Details

- **Architecture**: LSP server with pluggable provider architecture
- **Protocol**: Language Server Protocol (LSP) 3.17
- **Transport**: stdio (suitable for VS Code, Zed, and other LSP clients)
- **Dependencies**:
  - pygls >= 2.0.0, < 3.0.0 (LSP framework) - Updated from 1.3.0 in CORE-448
  - pydantic >= 2.5.0 (configuration validation)
  - lru-dict >= 1.3.0 (efficient LRU caching)
- **Supported Python Versions**: 3.10, 3.11, 3.12, 3.13
- **Supported Operating Systems**: Linux, macOS, Windows
- **LSP Methods Implemented**:
  - initialize, initialized, shutdown
  - textDocument/didOpen, textDocument/didChange, textDocument/didClose
  - textDocument/hover, textDocument/completion, textDocument/diagnostic
- **API Stability**: Public API stable, internal API may change
- **Breaking Changes**: None (first release)

### Integration

- **legesher-core**: Token-based translation engine for keyword transformation
- **legesher-i18n**: Language pack system for multi-language support
- **VS Code Extension** (Pending - Cycle 8): Will connect via stdio transport
- **Pylance** (Phase 1 Complete): Foundation for semantic analysis integration

---

## Development Info

### Running Tests

```bash
cd libs/language-server
uv run pytest tests/ -v --cov=legesher_language_server --cov-report=term-missing
```

### Test Coverage Report

```bash
cd libs/language-server
uv run pytest tests/ --cov=legesher_language_server --cov-report=html
open htmlcov/index.html
```

### Type Checking

```bash
cd libs/language-server
uv run mypy legesher_language_server/
```

### Linting

```bash
cd libs/language-server
uv run ruff check legesher_language_server/
```

### Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## Usage

### Starting the Language Server

```bash
# With Spanish target language
legesher-lsp --target-lang es

# With Python version specified
legesher-lsp --target-lang fr --python-version 3.11

# With debug logging
legesher-lsp --target-lang es --log-level DEBUG
```

### Configuration

**Environment Variables:**

- `LEGESHER_SOURCE_LANG` - Source code language (default: en)
- `LEGESHER_TARGET_LANG` - Target display language (default: es)
- `LEGESHER_PYTHON_VERSION` - Python version (auto-detected if not set)
- `LEGESHER_CACHE_SIZE` - Translation cache size (default: 1000)
- `LEGESHER_CACHE_TTL` - Cache TTL in seconds (default: 3600)
- `LEGESHER_LOG_LEVEL` - Logging level (default: INFO)

### VS Code Integration (Upcoming)

```typescript
const serverOptions: ServerOptions = {
  command: "legesher-lsp",
  args: ["--target-lang", targetLang],
  options: { env: { LEGESHER_LOG_LEVEL: "DEBUG" } },
};
```

---

## Roadmap

### Completed ✅

- **Phase 1: Foundation** - LSP server infrastructure, document management, configuration
- **Phase 2A: Core Providers** - Hover, completion, and diagnostic providers
- **Phase 2B: Pylance Integration - Phase 1** - Foundation architecture (SourceMap, TypeAliasGenerator,
  IncrementalTranslator, PylanceProxy)

### In Progress 🔄

- **Phase 2B: Pylance Integration - Phase 2** - Type inference and intelligent completion
- **Phase 2B: Pylance Integration - Phase 3** - Advanced diagnostics and semantic validation
- **Phase 2B: Pylance Integration - Phase 4** - Performance optimization and caching

### Upcoming 📋

- **Cycle 8: VS Code Extension** - Custom UI components and end-to-end integration
- **Future Enhancements**:
  - Signature help provider
  - Code action provider (refactoring support)
  - Rename provider
  - Symbol provider (document outline)
  - Reference provider (find all references)
  - Definition provider (go to definition)

---

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)
- [Architecture Documentation](ARCHITECTURE.md)
- [Legesher Monorepo CHANGELOG](../../CHANGELOG.md)

---

**Part of the Legesher Project** | Making programming multilingual
