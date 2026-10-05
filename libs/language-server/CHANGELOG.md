# Changelog - legesher-language-server

All notable changes to legesher-language-server are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Fixed

- Log records now reach the client through the LSP `window/logMessage`
  notification with the level they were written at, instead of going to stderr
  where an editor renders everything as `[error]`. stdout is not an option:
  under stdio transport it is the JSON-RPC stream itself. Records written
  before the transport exists are held and replayed once it does, so the
  startup lines arrive with a real level; errors are written to stderr
  immediately, since a server that dies during startup has nothing else, and
  the held records go out ahead of them. Nothing held is dropped if the
  connection never arrives at all: the handler drains its buffer to stderr on
  close, which is what `logging.shutdown` does at interpreter exit.
  (CORE-1979)
- pygls's logger is set to WARNING by default, which stops whole JSON-RPC
  payloads (the 8KB `InitializeParams` blob, every response, every
  semantic-token array) from being logged at INFO. Those payloads carry
  document-derived content. (CORE-1979)
- Removed the `DEBUG:`-prefixed instrumentation left in `on_initialize` by the
  CORE-1754/CORE-1776 language-resolution work. What was worth keeping is now
  `logger.debug`; the rest is gone, and the resolved languages are reported in
  a single line after the slots settle. (CORE-1979)
- Hover no longer logs the word under the cursor, or the rendered hover
  content, at INFO. Both are text out of the user's file. (CORE-1979)
- Every request is answered in the language of the document it is about,
  not in the one language the server was started with. Started in Amharic,
  the server highlighted Amharic and English files and returned an empty
  token set for a French or Arabic file open beside them; hover, completion
  and diagnostics were in the same state, and diagnostics reported the
  untranslated keywords as syntax errors. The client now names each
  document's language with a `legesher/documentLanguage` notification, sent
  as the document opens (normally just ahead of its `didOpen`) and again
  whenever the language it resolves for that document changes. The server
  keeps the language per document, forgets it on `didClose`, and falls back
  to the configured file language for a document it has not been told
  about, so a client that never sends the notification is served as before.
  The enhanced-intelligence proxy translates each document with its own
  language's keywords, keeping one translation cache per language. When an
  open document's language changes, including a name that arrives after its
  `didOpen`, the server asks the client to refresh its semantic tokens and
  diagnostics. (CORE-1976)
- A document in a language no pack can serve, because no pack exists for
  that code or its pack fails to load, is no longer answered as an ordinary
  file with nothing in it. Semantic tokens and hover return no result,
  completion and diagnostics return empty lists rather than answers read in
  the wrong language, the user is warned once per language through
  `window/showMessage` when such a document opens, and `legesher/status`
  names the document and the reason. (CORE-1976)

- `legesher-lsp --version`, the `serverInfo` in the `initialize` response and
  the `clientInfo` the server sends to its type-checking backend now report the
  package's real version, read from its installed metadata. They said 0.1.0
  while `__version__` said 0.1.2 and `pyproject.toml` said 0.1.3. `pyproject.toml`
  is now the only place the version is written. (CORE-2203)
- Hover and diagnostics forwarded to the type-checking backend work on a
  document with a translated keyword. Both forwards handed the source map
  `lsprotocol` positions, which cannot be ordered, so its range check raised
  `'<=' not supported between instances of 'Position' and 'Position'`. The
  forward logged that at ERROR, returned nothing, and the request fell back to
  the built-in answer. Positions now enter the source map as its own type and
  become `lsprotocol` positions only in the reply. With forwarding working,
  gaps the error hid now show on those documents: the backend's hover for a
  localized builtin takes precedence over the localized one (CORE-2179); and
  a hover between an edit and the next diagnostics request is answered from
  the text before the edit (CORE-2160). (CORE-2227)
- Forwarded hover and diagnostic ranges land on the right characters when a
  translated keyword follows other code on its line, starts any line of an
  indented block but the first, or sits below a multi-line string or a
  backslash continuation. The source map behind both forwards counted each
  token's width but not the spaces between tokens, counted an indent only on
  the line that opened its block, and counted a new line only at a line end.
  So it placed such a keyword too far left, and below a docstring as many
  lines too high as the docstring had line breaks. A range the backend
  returned there came back on the wrong characters: Pyright's undefined-name
  diagnostic for `indefinido`, after `sino` on its line, covered `o indefini`.
  Each translated word is now mapped at its own line, shifted by the width
  change of the words translated before it on that line. (CORE-2343)
- The text forwarded to the type-checking backend is translated the way
  `legesher run` translates a file: localized builtins, exceptions and
  implicit parameters along with the keywords. The proxy translated keywords
  only, so Pyright reported every localized builtin (`imprimir`), exception
  (`errordevalor`) and type in an annotation (`entero`) as undefined, and a
  localized `self` (`mismo`) as a misnamed parameter. Like the engine, the
  proxy renames every name spelled like one of these, a user's own variable
  or attribute included (CORE-1107), so the backend sees the same shadowing
  the run does. Two differences from the run remain: the proxy matches a
  word only as typed, where the engine also matches its other Unicode forms
  (CORE-2352), and it spells `NotImplemented` and `Ellipsis` as Python does,
  where the engine does not yet (CORE-2219). Hovering a localized builtin
  now shows the backend's English description of the Python builtin in place
  of `Unknown`, still ahead of the localized hover (CORE-2179). (CORE-2342)

### Added

- `logging_setup.LspLogHandler`, and `trace` support: the client's trace value
  sets verbosity. It is read from `initializationOptions`, from the `trace`
  field on the initialize request, or from a `$/setTrace` notification
  mid-session. `messages` raises this package's own logging; only `verbose`
  turns payload logging on. No text out of the open file is logged at `off`,
  though an error can still name the document's path; at `messages` the
  package's debug lines name the identifier under the cursor, the hover text
  rendered for it, the path of each document opened, changed or closed, and
  whatever the bundled Pyright backend writes to its own stderr. Anything
  unrecognised is treated
  as `off`, so a client's typo cannot silently enable it. (CORE-1979)

- `file_language` and `working_language` configuration fields, read from
  `initializationOptions` as separate `fileLanguage` and `workingLanguage` slots
  with the same fail-secure validation as the original pair. `fileLanguage`
  keeps `target_language` in lockstep so providers written against the old slot
  keep parsing files correctly, and a client that sends only the deprecated
  `targetLanguage` seeds all three roles — older clients keep working
  unchanged. (CORE-1760)

- `legesher/documentLanguage`, a client-to-server notification carrying
  `{uri, language}`: the language one document is written in. The server does
  no detection of its own; a client that does not send it has every document
  served in the configured file language. (CORE-1976)

- `legesher/status` now also lists each document the server has open or has
  been told about, as `documents`: its `uri`, the `language` it is served in,
  whether that came from the `client` or is the `configured` fallback
  (`source`), whether a pack can serve it (`served`), and why not (`detail`).
  The enhanced-intelligence fields are unchanged. (CORE-1976)

- A release train of its own, the model `legesher-mcp` uses: semantic-release
  tags `language-server-vX.Y.Z`, and the manual PyPI publish workflow has a
  `language-server` target, so editors other than VS Code can install the
  server by name once it is published. Each release is gated on a
  clean-environment suite that installs the built wheels into an empty
  virtualenv and runs an LSP session through the installed `legesher-lsp` in
  Spanish, Amharic and Arabic. (CORE-2203)

### Changed

- A `LanguageServerConfig` built with only `target_language` now sets
  `file_language` to match, and one built with only `file_language` sets
  `target_language`, so the lockstep the deprecated slot documents holds from
  construction and not only through the entry points. Providers now fall back
  to `file_language`, so without this a configuration written the old way
  would have been served in English. (CORE-1976)

## [0.1.3] - 2026-04-29

### Changed

- Expand the package module docstring from a single description sentence into a full
  Google-style block documenting LSP capabilities (Hover, Completion, Diagnostics,
  Semantic Tokens), environment variable configuration, and an example launch command.
  Fixes two inaccuracies caught in review: `LEGESHER_TARGET_LANG` default is `"en"`
  (matches `config.py:191`), not `"es"`; and the package supports Python 3.10+ per
  `requires-python`, not just 3.13+. Docstring-only; no code behavior changes.
  (CORE-1173)

### Added

- **Reserved Words plumbing**: `SemanticTokensProvider` now lazy-loads
  `pack.reserved_words` into a `_translated_reserved_words` set alongside
  keywords/builtins/exceptions. Visual semantic-token styling is
  foundational data path only — actual highlighting is deferred to
  CORE-1060. [CORE-710]

- **Semantic Tokens — Context-Aware Highlighting** (CORE-895, #199)
  - Class names after `class`/`clase` highlighted as `TOKEN_TYPE_CLASS` (teal)
  - Function names after `def`/`definir` highlighted as `TOKEN_TYPE_FUNCTION` (yellow)
  - First parameter (self/cls/propio) highlighted as `TOKEN_TYPE_PARAMETER` (blue)
  - Lightweight state machine using `_reverse_keyword_map` for keyword resolution
  - Works for all 51 supported languages including RTL scripts

- **Semantic Tokens — Builtins & Exceptions** (CORE-709, #194)
  - Translated builtin functions (`print`→`imprimir`) highlighted as `TOKEN_TYPE_FUNCTION` (yellow)
  - Translated builtin types (`int`→`entero`, `float`→`flotante`) highlighted as `TOKEN_TYPE_CLASS` (teal)
  - Translated exceptions (`ValueError`→`errordevalor`) highlighted as `TOKEN_TYPE_CLASS` (teal)
  - English builtins/exceptions highlighted in mixed-language code
  - Pre-computed `_BUILTIN_CASE_MAP` for O(1) exception name resolution

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

- **pygls 2.0 Migration** (CORE-448)
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

- **LSP Server Foundation** (#25, 1f71c25)
  - Complete Language Server Protocol implementation using `pygls` framework
  - Document state management with version tracking and change events
  - Configuration system with Pydantic validation and environment variable support
  - Full LSP lifecycle support (initialize, initialized, shutdown)
  - Document synchronization (didOpen, didChange, didClose)
  - CLI entry point with language and Python version configuration
  - Stub provider architecture (hover, completion, diagnostic)
  - Test coverage: 100% on config.py (114 tests lines), 100% on document.py (172 test lines)
  - Performance: Sub-millisecond document updates, efficient in-memory state management

- **Hover Provider** (#26, 9796f52)
  - Translates Python docstrings and provides keyword documentation in target language
  - Docstring translation for functions, classes, and modules
  - Keyword documentation with examples in target language (35 Python keywords)
  - Cultural comment support for @lang: annotations
  - LRU caching for improved performance on repeated hovers
  - Multi-language support (English, Spanish, Arabic, French, German, etc.)
  - AST-based symbol detection with fallback to regex parsing
  - Test coverage: 581 test lines, 77% coverage on hover.py, 80% on keyword_docs.py
  - Implementation: 341 lines (hover.py), 256 lines (keyword_docs.py)

- **Completion Provider** (#28, a2d10bd)
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

- **Diagnostic Provider with Error Translation** (#30, 28a384c)
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

- **Pylance Integration - Phase 1 Foundation** (#33, a2186f5)
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

- [GitHub Repository](https://github.com/legesher/legesher)
- [Issue Tracker](https://github.com/legesher/legesher/issues)
- [Architecture Documentation](ARCHITECTURE.md)
- [Legesher Monorepo CHANGELOG](../../CHANGELOG.md)

---

**Part of the Legesher Project** | Making programming multilingual
