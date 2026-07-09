# Changelog - legesher

All notable changes to the legesher main package (CLI) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

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

- **CLI Translation Command** ([#19](https://github.com/madiedgar/legesher/pull/19), [61c1dfc](https://github.com/madiedgar/legesher/commit/61c1dfc))
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

- **Git Integration Commands** ([#21](https://github.com/madiedgar/legesher/pull/21), [573bde6](https://github.com/madiedgar/legesher/commit/573bde6))
  - `legesher git setup` command for interactive git filter configuration
  - `legesher git status` command to display current filter state
  - Automatic `.gitattributes` configuration for `*.py` files
  - Git filter registration (clean/smudge) with proper error handling
  - Support for both project-level and global git configuration
  - Python version specification during setup (3.10, 3.11, 3.12, 3.13)
  - Interactive language selection with validation
  - Repository detection and error handling for non-git directories
  - Test coverage: 19 CLI tests covering all git command scenarios

- **Configuration Management System** ([#21](https://github.com/madiedgar/legesher/pull/21), [573bde6](https://github.com/madiedgar/legesher/commit/573bde6))
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

- **Metadata Management CLI** ([#29](https://github.com/madiedgar/legesher/pull/29), [a51bfa4](https://github.com/madiedgar/legesher/commit/a51bfa4))
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

- **Initial Monorepo Setup** ([#4](https://github.com/madiedgar/legesher/pull/4), [a31a990](https://github.com/madiedgar/legesher/commit/a31a990))
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

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)
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
