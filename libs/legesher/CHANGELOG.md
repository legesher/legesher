# Changelog - legesher

All notable changes to the legesher main package (CLI) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Changed

- The runtime import hook claims only files it will translate.
  It claimed every `.py` on the path, the standard library and installed
  packages included, and recompiled each from source with no bytecode
  cache, so a standard-library-heavy import cost 7 to 18 times its stock
  cost. Modules in the standard library and installed-package directories
  (including any site-packages or dist-packages directory) now load through
  the stock machinery, and a project file is claimed only when its first 16 KiB
  contain one of the pack's native keywords as a whole word; nothing is
  parsed to decide. Measured with a fresh process per sample, the
  standard-library imports from the ticket now cost 1.05 to 1.21 times
  the unhooked import. A native file whose first native keyword sits past
  that bound is not claimed; per-file language headers (CORE-1539) will
  remove the bound. Files the hook does translate are no longer recompiled
  on every run: their compiled code is cached in `__pycache__` under a
  Legesher-specific name (`<module>.<tag>.legesher-<lang>.pyc`, with the
  usual `.opt-N` tag under `-O`) that the stock loader never opens. The
  cache is keyed by a hash of the source bytes, the pack's language,
  versions and vocabulary, the engine's own code and version, the CLI
  version, the optimization level and the interpreter's bytecode magic
  number, never by modification time. It is written atomically with the
  source file's permissions, skipped under `PYTHONDONTWRITEBYTECODE`, and
  never replaces or removes a stock `.pyc`. `get_bytecode_cache_stats()`
  reports its hits, misses, writes and write errors. [CORE-2205]

### Fixed

- Packages that ship data files now work under the runtime import
  hook. The hook's loader had no resource reader, so `importlib.resources`
  raised "Can't open orphan path" for any package it claimed, and
  `import requests` failed inside certifi. The loader now returns the same
  file reader the stock loader uses. Its `get_data` also translated every
  path it was handed, so `pkgutil.get_data` returned a rewritten text file
  and raised on a binary one; files other than the module's own source now
  come back byte for byte. Module paths are now absolute, as the stock
  finder makes them, so package data found through a relative `sys.path`
  entry still resolves after the working directory changes. The hook still
  reads and writes no bytecode
  cache, so it never runs a stock `.pyc` in place of the source it
  translates. [CORE-2204]
- The runtime import hook now honors PEP 263 coding
  declarations. It read every module as UTF-8, so a module declaring
  `# -*- coding: latin-1 -*-` with non-ASCII latin-1 bytes imported without
  the hook and raised `UnicodeDecodeError` from inside it. Source is now
  decoded the way the stock loader decodes it, and bytes that are invalid
  in the declared encoding raise the same `SyntaxError` stock Python
  raises, naming the file; a file the stock compiler accepts but cannot be
  decoded as text (possible on Python 3.10 to 3.13) is imported untranslated,
  as stock Python imports it. The hook also now resolves module names
  exactly as stock Python does. It leaves names owned by built-in and frozen
  modules alone, so a user's `math.py` no longer replaces the built-in
  `math`, and for everything else it asks the standard path finder which
  file would load and claims only a source file. A compiled extension therefore wins
  over a same-named `.py` file again (mypyc and aiohttp ship such pairs),
  an earlier `sys.path` entry wins over a later one, a lone `.pyc` is left
  to the stock loader, and on a case-insensitive filesystem a name that
  differs only in case no longer loads the wrong file. The path check that
  claimed to prevent traversal is removed: module names are already
  limited to identifiers, which rules out every traversal shape, and the
  check made a symlinked package directory skip translation. [CORE-2206]

## [0.23.0] - 2026-08-16

### Added

- New **`legesher map edit`** command: fix a bad coinage by editing the map,
  never refactoring code. Corrects an identifier's rendering for one language
  (`legesher map edit calculate_tax --lang es --to calcular_impuesto`),
  re-validating the new value first — it must be a valid Python identifier,
  clear of language-pack reserved terms (skippable with `--no-pack-check`),
  clear of repo homonyms (including other identifiers' retired renderings),
  and clean under the Unicode contract. Requires a built register map
  (`.legesher/register_map.json`). The pack version for validation resolves
  `--python-version` → `.legesher/config.yml` → the running interpreter. On
  accept the map is saved with per-language provenance (`--edited-by`; only
  the edited language's review status resets), the old rendering stays
  resolvable as an alias for old branches and PR diffs, stale
  translation-memory segments are invalidated entry-scoped, and — after the
  artifacts are saved — a lineage event is appended to
  `.legesher/mapping_log.jsonl`. Occurrences of the identifier inside
  strings/docstrings/comments are reported for manual review (never
  rewritten). Target one exact entry with `--node-id`/`--file`. [CORE-1676]
- `legesher run` now renders **localized tracebacks**: uncaught exceptions
  print with the traceback structure, exception type name, and error message
  in the script's language (via the new `legesher-runtime` package). The
  language comes from `.legesher/config.yml` as before, `--lang` overrides.
  Messages the catalog does not know pass through untranslated, and any
  rendering problem falls back to the previous traceback behavior. For
  frames compiled from translated source, the traceback shows the native
  source line and drops the fine-grained caret markers (their columns were
  computed against the translated text; correct column re-mapping is a
  tracked follow-up — no caret beats a wrong caret). [CORE-1679]

### Changed

- **The CLI is now licensed under the Apache License 2.0, with no dual-license
  option.** It previously declared `Apache-2.0 OR LicenseRef-Commercial` and
  reserved cloud sync, collaboration, team management, and analytics for a paid
  tier — capabilities this package does not contain and never has. Those live in
  the hosted service, where access is gated by account and API key rather than by
  a source license. This is a loosening: every right the Apache half granted is
  unchanged, and nothing was published under the dual license. (CORE-1680)

## [0.22.0] - 2026-07-15

## [0.21.3] - 2026-07-12

## [0.21.2] - 2026-07-12

## [0.21.1] - 2026-07-12

## [0.21.0] - 2026-07-11

### Added

- **`--global` flag for `legesher config set`** (CORE-574): writes values to
  the user-level config (`~/.legesher/config.yml`) instead of the project
  config. `config get`/`list` now read the user-level config merged with the
  project config (top-level merge matching `LegesherConfig.load()`: a project
  section replaces the user section of the same name), and `config set`
  reports which config file it wrote. A config file whose YAML root is not a
  mapping now produces a clear CLI error instead of a crash, and is never
  overwritten.

## [0.20.0] - 2026-07-09

## [0.19.0] - 2026-07-09

## [0.18.1] - 2026-07-09

## [0.18.0] - 2026-07-09

## [0.17.1] - 2026-07-09

## [0.17.0] - 2026-07-09

## [0.16.0] - 2026-07-09

## [0.15.0] - 2026-07-09

## [0.14.0] - 2026-07-05

## [0.13.1] - 2026-07-05

## [0.13.0] - 2026-06-11

## [0.12.0] - 2026-06-11

## [0.11.3] - 2026-06-11

## [0.11.2] - 2026-05-14

## [0.11.1] - 2026-05-07

## [0.11.0] - 2026-05-03

## [0.10.1] - 2026-05-01

### Fixed

- **`test_translate_with_classes` integration test** ([CORE-1126]):
  tightened assertion from the pre-CORE-710 `self`-preserved
  contract to the strict post-CORE-710 contract (Spanish pack
  translates `self -> mismo` via `reserved_words`). Test was
  silently red on `main` since v0.10.0; release-foundation didn't
  gate on CI so it shipped anyway. No product behavior change.

## [0.10.0] - 2026-05-01

## [0.9.3] - 2026-04-29

### Changed

- Version bumped in lockstep with `legesher-core` and `legesher-i18n` for the
  CORE-710 release cohort. No functional changes to the CLI itself; the new
  `reserved_words` translation category flows transparently through this
  package's `legesher translate` and `legesher run` commands via the
  underlying `legesher-core` translator backends. [CORE-710]

## [0.9.2] - 2026-04-20

## [0.9.1] - 2026-04-17

## [0.9.0] - 2026-04-10

## [0.8.1] - 2026-04-03

## [0.8.0] - 2026-04-02

### Added

- `--full` flag for `legesher translate` enabling LLM-powered full code translation
  (identifiers, comments, docstrings, strings) (AYA-191)
- `--llm-backend` option: choose between `anthropic`, `cohere-aya`, `openai-compat`
- `--llm-base-url` for custom OpenAI-compatible endpoints (local models)
- `--identifier-map` for cross-file translation consistency (JSON glossary)
- `--checkpoint` for resuming interrupted batch translation jobs (plaintext, one path per line)
- `--llm-model` for specifying model name with openai-compat backend
  (e.g., `--llm-model aya:latest`) (CORE-706)
- `--no-identifier-map` flag for batch-translating unrelated files independently
  without cross-contamination (CORE-706)
- Auto-save IdentifierMap to `.legesher/identifier_map.json` by default in `--full`
  mode — committable to git as a living project dictionary (CORE-706)

### Fixed

- `--full` mode enforces English source (`--from en`) with clear error message (AYA-191)
- Provider name mapping for `--llm-backend` CLI values to provider `.name` attributes (AYA-191)

## [0.7.3] - 2026-03-19

## [0.7.2] - 2026-03-18

- Version bump to align with foundation suite (no functional changes)

## [0.7.1] - 2026-03-16

## [0.7.0] - 2026-03-16

## [0.6.0] - 2026-03-11

## [0.5.1] - 2026-03-01

### Changed

- Version bumped to align with monorepo v0.5.1 release (no functional changes)

## [0.5.0] - 2026-02-01

### Added

- **`legesher config` Command** (CORE-563)
  - `legesher config list` to display current configuration
  - `legesher config get <key>` to retrieve specific settings
  - `legesher config set <key> <value>` to update settings
  - Reads from `.legesher/config.yml`

- **Non-Interactive `legesher init` Mode** (CORE-562)
  - `legesher init` now works in non-TTY environments (CI/scripts)
  - All options provided via flags skip interactive prompts
  - Flags: `-l/--language`, `--no-git`, `--no-ai-context`

### Fixed

- **`legesher --version` Shows Correct Version** (CORE-560)
  - Now uses `importlib.metadata.version()` instead of hardcoded string

- **Dynamic Language Help Text** (CORE-561)
  - `legesher translate --help` now shows all 26 supported languages
  - Dynamically generated from installed language packs

### Changed

- Migrate all test fixtures from hardcoded translation maps to real YAML language pack data via `LanguagePackLoader`
- Fix `test_all_spanish_keywords_work` to use fixture values instead of shadowed hardcoded list

## [0.4.0] - 2026-01-27

### Changed

- Version bumped to align with monorepo release (no functional changes to CLI since 0.1.0)

## [0.1.0] - 2025-11-07

### Added

- **CLI Translation Command** (#19, 61c1dfc)
  - Comprehensive `legesher translate` command for code translation
  - Single file translation with `--from`, `--to`, `--output` flags
  - Stdin/stdout support for Unix piping workflows (`cat file.py | legesher translate`)
  - Recursive directory translation with structure preservation
  - Progress indication for batch directory operations
  - File permission preservation (executable bits maintained)
  - User-friendly error messages with actionable suggestions
  - Comprehensive help text with usage examples
  - Support for English, Spanish, and Arabic translations
  - Cross-platform compatibility (Linux, macOS, Windows)
  - Test coverage: 66 tests (37 unit + 29 integration), 97% coverage

- **Git Integration Commands** (#21, 573bde6)
  - `legesher git setup` command for interactive git filter configuration
  - `legesher git status` command to display current filter state
  - Automatic `.gitattributes` configuration for `*.py` files
  - Git filter registration (clean/smudge) with proper error handling
  - Support for both project-level and global git configuration
  - Python version specification during setup (3.10, 3.11, 3.12, 3.13)
  - Interactive language selection with validation
  - Repository detection and error handling for non-git directories
  - Test coverage: 19 CLI tests covering all git command scenarios

- **Configuration Management System** (#21, 573bde6)
  - `LegesherConfig` class for managing `.legesher/config.yml` files
  - Project-level configuration in `.legesher/config.yml`
  - User-level configuration in `~/.legesher/config.yml`
  - Configuration precedence: project config overrides user config
  - YAML-based configuration with human-readable format
  - Language preference storage (e.g., `es` for Spanish)
  - Python version specification (3.10, 3.11, 3.12, 3.13)
  - Git integration settings (enabled/disabled state)
  - Automatic git repository root detection
  - Configuration validation with error reporting
  - Test coverage: 32 tests covering loading, saving, precedence, and error handling

- **Metadata Management CLI** (#29, a51bfa4)
  - `legesher metadata show` command to display file translation history
  - `legesher metadata history` command to view all translation records
  - `legesher metadata list` command to list tracked files
  - `legesher metadata validate` command to verify metadata integrity
  - `legesher metadata raw` command for viewing raw YAML metadata
  - Colorized output for improved readability (success/warning/error states)
  - Support for both absolute and relative file paths
  - Integration with git commit tracking
  - Enables debugging translation issues and history archaeology
  - JSON output option for programmatic access

- **Initial Monorepo Setup** (#4, a31a990)
  - UV-based monorepo structure with workspace configuration
  - Package dependency hierarchy (Tier 3 user-facing tool)
  - Dependencies on `legesher-core` and `legesher-i18n`
  - MIT OR LicenseRef-Commercial dual licensing structure
  - Python 3.10+ support
  - Package metadata and classification
  - Entry point registration: `legesher` CLI command
  - Development dependencies: pytest, pytest-cov, ruff, black, mypy

### Dependencies

- **Core Dependencies**:
  - `click>=8.0.0` - CLI framework for command-line interface
  - `pyyaml>=6.0` - YAML parsing for configuration files
  - `legesher-core` - Token translation engine and git filters
  - `legesher-i18n` - Language pack system

- **Development Dependencies**:
  - `pytest>=8.0.0` - Testing framework
  - `pytest-cov>=4.1.0` - Test coverage reporting
  - `pytest-asyncio>=0.23.0` - Async test support
  - `ruff>=0.1.0` - Fast Python linter
  - `black>=24.0.0` - Code formatter
  - `mypy>=1.8.0` - Static type checker

### CLI Commands

The legesher package provides the following CLI commands:

#### Translation Commands

```bash
# Translate a single file
legesher translate input.py --from es --to en --output output.py

# Translate from stdin to stdout
cat input.py | legesher translate --from es --to en

# Translate an entire directory
legesher translate src/ --from es --to en --output translated/
```

#### Git Integration Commands

```bash
# Setup git filters for automatic translation
legesher git setup

# Setup with specific language and Python version
legesher git setup --language es --python-version 3.12

# Setup git filters globally (all repositories)
legesher git setup --global

# Check git filter status
legesher git status
```

#### Metadata Commands

```bash
# Show translation history for a file
legesher metadata show path/to/file.py

# View all translation records
legesher metadata history

# List all tracked files
legesher metadata list

# Validate metadata integrity
legesher metadata validate

# View raw YAML metadata
legesher metadata raw path/to/file.py
```

### Configuration

Configuration is stored in YAML format:

**Project-level** (`.legesher/config.yml`):

```yaml
language: es
python_version: "3.12"
git:
  enabled: true
metadata:
  enabled: true
  directory: .legesher/metadata
  track_in_git: false
```

**User-level** (`~/.legesher/config.yml`):

```yaml
language: es
python_version: "3.12"
```

Project configuration takes precedence over user configuration.

### Performance

- **Translation Speed**: <2ms average per file (inherited from legesher-core)
- **Directory Translation**: Progress indication for large directories
- **Batch Operations**: Efficient file handling with minimal overhead
- **Memory Usage**: <50MB for typical CLI operations

### Test Coverage

- **Unit Tests**: 88 tests covering CLI commands, configuration, and error handling
- **Integration Tests**: 29 tests with real file I/O and git operations
- **Total**: 117 tests with 91%+ overall coverage
- **Cross-Platform**: All tests pass on Linux, macOS, and Windows

### Technical Details

- **Architecture**: Click-based CLI with modular command structure
- **Configuration**: YAML-based with precedence resolution
- **Error Handling**: User-friendly error messages with suggestions
- **Extensibility**: Modular design for adding new commands
- **API Stability**: CLI interface stable, internal API may change
- **Breaking Changes**: None (first release)

### Known Limitations

- Direct X→Y translation not yet supported (use X→EN→Y workflow)
- Git filter setup requires manual confirmation for global configuration
- Metadata tracking disabled by default (must be enabled in config)

---

## Development Info

### Running Tests

```bash
cd libs/legesher
uv run pytest tests/ -v
```

### Coverage Report

```bash
cd libs/legesher
uv run pytest tests/ --cov=legesher --cov-report=html
open htmlcov/index.html
```

### Code Quality

```bash
# Run linter
uv run ruff check .

# Run formatter
uv run black .

# Run type checker
uv run mypy legesher/
```

### Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## Links

- [GitHub Repository](https://github.com/legesher/legesher)
- [Issue Tracker](https://github.com/legesher/legesher/issues)
- [Legesher Monorepo CHANGELOG](../../CHANGELOG.md)
- [legesher-core CHANGELOG](../core/CHANGELOG.md)
- [legesher-i18n CHANGELOG](../i18n/CHANGELOG.md)

---

## Package Structure

```text
legesher/
├── legesher/
│   ├── cli/
│   │   ├── main.py         # CLI entry point and command registration
│   │   ├── translate.py    # Translation command implementation
│   │   ├── git.py          # Git integration commands
│   │   └── metadata.py     # Metadata management commands
│   └── config.py           # Configuration management system
├── tests/
│   ├── unit/               # Unit tests for CLI commands and config
│   └── integration/        # Integration tests with file I/O and git
├── pyproject.toml          # Package configuration
├── README.md               # Package documentation
└── CHANGELOG.md            # This file
```

---

## Related Packages

- **legesher-core**: Token translation engine, git filters, metadata tracking
- **legesher-i18n**: Language pack system with Python keyword translations
- **legesher-language-server**: LSP server for IDE integration (future)
- **legesher-home**: Digital home and community platform (future)

---

## License

Dual licensed under MIT OR LicenseRef-Commercial.

See [LICENSE](../../LICENSE) for details.
