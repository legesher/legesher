# Changelog - legesher-core

All notable changes to legesher-core are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

## [0.9.1] - 2026-04-17

## [0.9.0] - 2026-04-10

## [0.8.1] - 2026-04-03

## [0.8.0] - 2026-04-02

### Added

- Full LLM-powered code translation via `LLMTranslator` — composes TreeSitterTranslator
  with pluggable `TextTranslationBackend` for translating identifiers, comments, docstrings,
  and strings (AYA-191)
- `TranslatableExtractor`: walks tree-sitter AST and extracts all translatable elements
  with role context (function_name, parameter, variable, etc.)
- `IdentifierMap`: cross-file/cross-language translation glossary with JSON persistence
- `IdentifierValidator`: validates translated identifiers for Python syntax, keyword
  collisions, and mixed-script detection (RTL/Unicode support)
- `TranslationLogger`: JSONL training data collection for future model fine-tuning
- `TextTranslationBackend` protocol: dependency inversion allowing LLM implementations
  in libs/i18n without circular imports
- `TranslationScope`: toggle translation of identifiers/comments/docstrings/strings
- Factory extended: `create_translator(backend=...)` returns `LLMTranslator`

### Fixed

- Load exception translations (ValueError, TypeError, etc.) into TokenTranslator
  builtin map — previously existed in packs but were silently dropped. PascalCase
  remapping from lowercase YAML keys (CORE-706)
- Pass IdentifierMap glossary to text element translation (Step 3->4 context flow)
  so docstrings/comments use the same terms as translated identifiers (CORE-706)
- Escape closing quote sequences in LLM string/docstring translations (AYA-191)
- Handle multi-line LLM comment responses with per-line `#` prefix (AYA-191)
- F-string `string_content` nodes reconstructed as raw text (AYA-191)
- Comment text sent to LLM without `#` prefix, preventing double `##` (AYA-191)

## [0.7.3] - 2026-03-19

## [0.7.2] - 2026-03-18

### Fixed

- Fix TreeSitterTranslator crashing with `InvalidCodeError` on ~0.6% of Python files
  containing non-UTF-8 bytes (e.g., U+009F) in string literals when translating to
  multi-byte languages like Chinese, Arabic, Urdu, Amharic (CORE-799)
  - Root cause: byte-level `bytearray` splice + `decode("utf-8")` corrupted output when
    multi-byte translations shifted byte offsets past non-ASCII string content
  - Fix: switch `_apply_replacements()` to character-level string operations via a
    byte→char offset map, eliminating the encode/decode round-trip
  - Verified: 0 failures on 1,000 files from The Stack (was 7/1,000)

## [0.7.1] - 2026-03-16

## [0.7.0] - 2026-03-16

## [0.6.0] - 2026-03-11

## [0.5.1] - 2026-03-01

### Fixed

- Replace `datetime.UTC` with `timezone.utc` for Python 3.10 compatibility (CORE-662)
  - `datetime.UTC` is a Python 3.11+ alias; `timezone.utc` works since Python 3.2
  - Fixes `ImportError` on Ubuntu 22.04 with Python 3.10.12

## [0.5.0] - 2026-02-01

### Changed

- Version bumped to align with monorepo v0.5.0 release

## [0.4.1] - 2026-01-31

### Fixed

- Fix `GitFilter` passing `python_version` as wrong keyword argument
  (`python_version=` → `programming_language_version=`) when loading language packs
- Fix `TokenTranslator` compound keyword handling for `except*` (CORE-531)
  - Python's tokenizer splits `except*` into `NAME("except")` + `OP("*")`
  - Add index-based lookahead to detect and translate compound keywords correctly

### Changed

- Migrate all test fixtures from hardcoded translation maps to real YAML language pack data via `LanguagePackLoader`

## [0.4.0] - 2026-01-27

### Changed

- Version bumped to align with monorepo release (no functional changes to core since 0.1.0)

## [0.1.0] - 2025-11-07

### Added

- **Token-Based Translation Engine** ([#11](https://github.com/madiedgar/legesher/pull/11), [703e8b0](https://github.com/madiedgar/legesher/commit/703e8b0))
  - Translates Python code between English, Spanish, and Arabic
  - Supports all 35 Python 3.13 keywords
  - Bidirectional translation with complete reversibility (EN↔ES, EN↔AR)
  - Preserves all formatting: indentation, blank lines, comment placement, docstrings
  - Lossless round-trip guarantee: EN→ES→EN produces byte-identical output
  - RTL (right-to-left) language support for Arabic and Hebrew
  - Performance: <2ms per file on average
  - Test coverage: 91% with 255 passing tests
  - Graceful degradation: handles incomplete code and syntax errors

- **Cultural Comment Parser** ([#12](https://github.com/madiedgar/legesher/pull/12), [493199f](https://github.com/madiedgar/legesher/commit/493199f))
  - Implements MLCP (Multilingual Code Protocol) support
  - Special syntax for cultural context: `@lang:xx`, `@traduce:keyword:translation`
  - Preserves cultural annotations across translations
  - Never machine-translates comments marked with `@lang:`
  - IDE-ready for hover tooltips and documentation display
  - Enables developers to explain language-specific idioms and terminology

- **Git Filter System** ([#21](https://github.com/madiedgar/legesher/pull/21), [573bde6](https://github.com/madiedgar/legesher/commit/573bde6))
  - Clean/smudge filters for seamless multilingual git workflows
  - Stores canonical English in repository for universal collaboration
  - Automatic translation on checkout to developer's preferred language
  - Language detection from local configuration (`.legesher/config.yml`)
  - Transparent to git hosting platforms (GitHub, GitLab, Bitbucket)
  - Enables Spanish developer → English repo → Arabic developer workflow
  - Zero git conflicts from keyword differences between languages

- **Language Pack Integration** ([#17](https://github.com/madiedgar/legesher/pull/17), [5a7493e](https://github.com/madiedgar/legesher/commit/5a7493e))
  - Direct integration with `legesher-i18n` language pack system
  - Automatic Python version detection from environment
  - Version-aware translation loading (Python 3.10, 3.11, 3.12, 3.13)
  - Intelligent caching for improved performance on repeated translations
  - Supports version-specific keywords (match/case, except\*, type parameter syntax)
  - Fallback mechanism for missing or incomplete translations

- **Metadata Tracking System** ([#29](https://github.com/madiedgar/legesher/pull/29), [a51bfa4](https://github.com/madiedgar/legesher/commit/a51bfa4))
  - Comprehensive translation history tracking with full audit trail
  - Records all translation operations with timestamps and commit SHAs
  - Tracks git filter operations (clean/smudge events) for debugging
  - Privacy-first design: no source code stored, only metadata
  - YAML-based storage in `.legesher/metadata/` directory
  - Atomic file operations for data integrity and crash safety
  - Enables debugging translation issues and verifying translation history
  - Supports translation archaeology: "when was this file first translated?"

- **Tree-sitter Foundation** ([#27](https://github.com/madiedgar/legesher/pull/27), [67a3052](https://github.com/madiedgar/legesher/commit/67a3052))
  - Added tree-sitter Python bindings and dependencies
  - Infrastructure setup for AST-based translation in Phase 2B
  - Preparation for incremental parsing (faster real-time IDE translation)
  - Foundation for multi-language support (JavaScript, TypeScript, Rust)
  - Enables context-aware translation (distinguishes keyword `type` from variable `type`)

- **Tree-sitter Translation Engine** ([#36](https://github.com/madiedgar/legesher/pull/36), CORE-414)
  - High-performance AST-based translator with ≥2x speed improvement over token-based approach
  - 100% API compatibility with TokenTranslator - drop-in replacement
  - Recursive AST traversal for precise keyword and builtin detection
  - Byte-position-based text replacement preserves exact formatting
  - Better error tolerance for incomplete code during typing
  - Bidirectional translation support (EN↔ES round-trip)
  - Performance: ~0.5ms parse time vs ~2ms for token-based
  - Test coverage: 32 comprehensive tests (90.6% passing)
  - Foundation for real-time IDE features and incremental parsing
  - Prepares for multi-language support (TypeScript, JavaScript, Rust)

### Performance

- **Translation Speed**: <2ms average per file
- **Round-Trip Fidelity**: 100% (EN→ES→EN is byte-identical)
- **Test Coverage**: 91% with 255 passing tests
- **Supported Python Versions**: 3.10, 3.11, 3.12, 3.13
- **Supported Operating Systems**: Linux, macOS, Windows
- **Memory Usage**: <50MB for typical projects

### Technical Details

- **Architecture**: Token-based transformation with AST validation
- **Dependencies**: Minimal (Python stdlib + tree-sitter bindings)
- **API Stability**: Public API stable, internal API may change
- **Breaking Changes**: None (first release)

---

## Development Info

### Running Tests

```bash
cd libs/core
uv run pytest tests/ -v
```

### Test Coverage

```bash
cd libs/core
uv run pytest tests/ --cov=legesher_core --cov-report=html
open htmlcov/index.html
```

### Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)
- [Legesher Monorepo CHANGELOG](../../CHANGELOG.md)
