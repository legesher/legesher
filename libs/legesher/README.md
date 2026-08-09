# legesher

> Command-line interface for coding in any language

**Status**: Production-Ready (Pre-Beta) | **Version**: 0.0.x | **Languages**: 27+

The legesher CLI is your gateway to programming in your native language. Translate Python code between English and localized
keywords, manage git integration for collaborative workflows, and configure your multilingual development environment.

## About

The `legesher` package provides command-line tools for developers who want to write code in their native language
instead of English. It handles:

- **Code Translation**: Convert Python files between languages using language packs
- **Git Integration**: Seamlessly collaborate with English-speaking developers via git filters
- **Configuration**: Manage project and global settings for language preferences
- **Metadata**: View and validate language pack information
- **Discovery**: Explore available language packs and their capabilities

This is the main user-facing package in the Legesher ecosystem, built on top of `legesher-core` and `legesher-i18n`.

## Installation

```bash
pip install legesher
```

Or install from source in the monorepo:

```bash
cd libs/legesher
pip install -e .
```

## Quick Start

```bash
# Initialize a new project with Spanish language pack
legesher config init --language es

# Translate a Python file to Spanish
legesher translate mi_codigo.py --to es

# Set up git integration for collaborative development
legesher git setup

# View available language packs
legesher info --list
```

## Commands

### `legesher translate`

Translate Python source files between languages.

```bash
# Translate a single file to Spanish
legesher translate app.py --to es

# Translate to English (canonical form)
legesher translate mi_app.py --to en

# Translate with explicit source language
legesher translate code.py --from es --to fr

# Translate and write to different file
legesher translate input.py --to es --output salida.py

# Translate entire directory (recursive)
legesher translate src/ --to es --recursive
```

**Full LLM Translation** (translates identifiers, comments, strings, docstrings):

```bash
# Full translation with Anthropic Claude
legesher translate src/ --to es --full --llm-backend anthropic

# Full translation with local model (vLLM, Ollama, llama.cpp)
legesher translate src/ --to ur --full --llm-backend openai-compat \
    --llm-base-url http://localhost:8000

# Batch with cross-file consistency and resume
legesher translate src/ --to zh --full \
    --identifier-map .legesher/identifier_map.json \
    --checkpoint .legesher/checkpoint.txt
```

**Options:**

- `--to LANG`: Target language code (required)
- `--from LANG`: Source language code (auto-detected if not specified)
- `--output PATH`: Output file path (default: overwrite input)
- `--full`: Enable full LLM translation (identifiers, comments, strings, docstrings)
- `--llm-backend`: LLM backend: `anthropic`, `cohere-aya`, or `openai-compat` (default: anthropic)
- `--llm-base-url`: Base URL for openai-compat backend (e.g., `http://localhost:8000`)
- `--identifier-map PATH`: Load/save identifier glossary for cross-file consistency
- `--checkpoint PATH`: Resume interrupted batch jobs

**Example Output:**

```bash
$ legesher translate hello.py --to es
Translating hello.py (en → es)...
✓ Translation complete: hello.py
  5 keywords translated
  1 builtin function translated
```

### `legesher git`

Manage git filter integration for multilingual repositories.

```bash
# Set up git filters for current repository
legesher git setup

# Set up with specific language
legesher git setup --language es

# Remove git filters
legesher git remove

# Check git filter status
legesher git status
```

**Subcommands:**

- **`setup`**: Configure git clean/smudge filters to store code in canonical English while working in your native language
- **`remove`**: Remove git filter configuration from repository
- **`status`**: Display current git filter configuration and language settings

**Example Output:**

```bash
$ legesher git setup --language es
Setting up git filters for Spanish (es)...
✓ Git filters configured in .git/config
✓ Git attributes created in .gitattributes
✓ Project configuration saved to .legesher/config.yml

Your repository is now configured for multilingual development:
  Working language: Spanish (es)
  Storage format: English (canonical)
  Git filters: Active
```

### `legesher map`

Inspect and correct the Legesher map (the `.legesher/` artifacts). A bad
coinage is fixed by editing the map — the code itself never changes.
Requires a built register map (`.legesher/register_map.json`).

```bash
# Fix the Spanish rendering of an identifier everywhere
legesher map edit calculate_tax --lang es --to calcular_impuesto

# Fix one exact map entry
legesher map edit --node-id n000042 --file src/tax.py --lang es --to calcular_impuesto

# Skip language-pack collision validation
legesher map edit calculate_tax --lang es --to calcular_impuesto --no-pack-check
```

**Subcommands:**

- **`edit`**: Correct an identifier's rendering for one language. The new
  value is re-validated first (valid Python identifier, language-pack
  reserved terms, repo homonyms, Unicode contract). On accept: the map is
  saved with per-language provenance, the old rendering stays resolvable
  as an alias, a lineage event is appended to `.legesher/mapping_log.jsonl`,
  stale translation-memory segments are invalidated entry-scoped, and any
  occurrences of the identifier inside strings/docstrings/comments are
  reported for manual review (never rewritten).

### `legesher config`

Manage project and global configuration.

```bash
# Initialize project configuration
legesher config init --language es

# Set default language for project
legesher config set language es

# Get current language setting
legesher config get language

# List all configuration settings
legesher config list

# Set global (user-level) configuration
legesher config set language es --global

# Remove a configuration setting
legesher config unset language
```

**Configuration Locations:**

- **Project**: `.legesher/config.yml` (current directory)
- **Global**: `~/.legesher/config.yml` (user home directory)

**Available Settings:**

- `language`: Default language code (e.g., `es`, `fr`, `ar`)
- `python_version`: Target Python version (e.g., `3.12`, `3.11`)
- `git.enabled`: Enable git filter integration (boolean)
- `git.auto_setup`: Automatically set up git filters on init (boolean)

**Example Output:**

```bash
$ legesher config list
Project configuration (.legesher/config.yml):
  language: es
  python_version: 3.12
  git.enabled: true
  git.auto_setup: false

Global configuration (~/.legesher/config.yml):
  language: en
```

### `legesher metadata`

View and validate language pack metadata.

```bash
# Show metadata for specific language pack
legesher metadata es

# Show metadata for specific Python version
legesher metadata es --python-version 3.12

# Validate language pack integrity
legesher metadata es --validate

# Show detailed metadata (including all keywords)
legesher metadata es --verbose

# Export metadata as JSON
legesher metadata es --format json
```

**Example Output:**

```bash
$ legesher metadata es
Language Pack: Spanish (es)
Python Version: 3.12 (with inheritance from 3.11, 3.10)
Total Keywords: 35
Total Builtins: 71
Maintainer: Legesher Community
License: Apache-2.0

Keyword Coverage:
  ✓ if → si
  ✓ for → para
  ✓ while → mientras
  ✓ def → def
  ✓ class → clase
  ... (30 more)

Run with --verbose to see complete translation mappings.
```

### `legesher info`

Display information about language packs and system status.

```bash
# List all available language packs
legesher info --list

# Show detailed information for specific pack
legesher info --pack es

# Show system status and configuration
legesher info --status

# Check for language pack updates (future)
legesher info --check-updates
```

**Example Output:**

```bash
$ legesher info --list
Available Language Packs:

  es - Spanish (Español)
    Python: 3.10, 3.11, 3.12
    Keywords: 35 | Builtins: 71
    Status: ✓ Installed

  fr - French (Français)
    Python: 3.10, 3.11, 3.12
    Keywords: 35 | Builtins: 71
    Status: ✗ Not installed

  ar - Arabic (العربية)
    Python: 3.10, 3.11, 3.12
    Keywords: 35 | Builtins: 71
    Status: ✗ Not installed

Install a language pack: pip install legesher-i18n-python-<code>
```

## Configuration

The legesher CLI uses YAML configuration files for project and user settings.

### Project Configuration

Create `.legesher/config.yml` in your project root:

```yaml
# Default language for this project
language: es

# Target Python version
python_version: "3.12"

# Git integration settings
git:
  enabled: true
  auto_setup: false

# Translation preferences
translation:
  preserve_comments: true
  preserve_docstrings: true
```

### Global Configuration

Create `~/.legesher/config.yml` for user-wide defaults:

```yaml
# Your preferred default language
language: es

# Default Python version
python_version: "3.12"

# CLI preferences
cli:
  color: true
  verbose: false
```

### Configuration Precedence

Settings are resolved in this order (highest to lowest priority):

1. Command-line flags (e.g., `--language es`)
2. Environment variables (e.g., `LEGESHER_LANGUAGE=es`)
3. Project configuration (`.legesher/config.yml`)
4. Global configuration (`~/.legesher/config.yml`)
5. Built-in defaults

## Examples

### Example 1: Starting a New Spanish Project

```bash
# Create project directory
mkdir mi_proyecto
cd mi_proyecto

# Initialize legesher configuration
legesher config init --language es

# Create a Python file in Spanish
cat > hola.py << 'EOF'
def saludar(nombre):
    """Saluda a una persona por su nombre."""
    imprimir(f"¡Hola, {nombre}!")

si __nombre__ == "__principal__":
    saludar("Mundo")
EOF

# Set up git integration
legesher git setup

# Initialize git repository
git init
git add .
git commit -m "Initial commit"

# File is stored in English in git, but you work in Spanish!
```

### Example 2: Contributing to English Projects

```bash
# Clone an English Python project
git clone https://github.com/example/python-project.git
cd python-project

# Set up legesher to work in Spanish
legesher config init --language es
legesher git setup

# Translate existing code to Spanish for local development
legesher translate src/ --to es --recursive

# Work in Spanish...
# All commits automatically store in English via git filters
```

### Example 3: Switching Between Languages

```bash
# Currently working in Spanish
legesher config get language
# Output: es

# Translate current codebase to French
legesher translate src/ --to fr --recursive

# Update configuration
legesher config set language fr

# Now working in French!
```

### Example 4: Validating Language Packs

```bash
# Check language pack integrity
legesher metadata es --validate

# View complete translation mappings
legesher metadata es --verbose

# Export metadata for tooling integration
legesher metadata es --format json > es-metadata.json
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=legesher --cov-report=html

# Run specific test file
pytest tests/test_cli.py
```

### Project Structure

```text
libs/legesher/
├── src/legesher/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── commands/
│   │   ├── translate.py    # Translation command
│   │   ├── git.py          # Git integration command
│   │   ├── config.py       # Configuration command
│   │   ├── metadata.py     # Metadata command
│   │   └── info.py         # Info command
│   ├── config/
│   │   └── manager.py      # Configuration management
│   └── utils/
│       ├── output.py       # CLI output formatting
│       └── validation.py   # Input validation
├── tests/
│   ├── test_cli.py
│   ├── test_translate.py
│   ├── test_git.py
│   ├── test_config.py
│   └── test_metadata.py
├── pyproject.toml
└── README.md
```

## Contributing

We welcome contributions! Please see:

- [CONTRIBUTING.md](../../CONTRIBUTING.md) in the monorepo root
- [Development Guide](../../docs/development/DEVELOPMENT.md)
- [Open Issues](https://github.com/legesher/legesher/issues?q=is%3Aissue+is%3Aopen+label%3Alegesher-cli)

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Links

- **Monorepo**: [legesher/legesher](https://github.com/legesher/legesher)
- **Documentation**: [docs.legesher.io](https://docs.legesher.io)
- **Language Packs**: [legesher-i18n packages](https://pypi.org/search/?q=legesher-i18n)
- **Changelog**: [CHANGELOG.md](./CHANGELOG.md)
- **Issues**: [GitHub Issues](https://github.com/legesher/legesher/issues)
- **Discussions**: [GitHub Discussions](https://github.com/legesher/legesher/discussions)

## Related Packages

- **[legesher-core](../core/README.md)**: Core translation engine and AST utilities
- **[legesher-i18n](../i18n/README.md)**: Language pack registry and translation API
- **[legesher-i18n-python-es](../i18n-python-es/README.md)**: Spanish language pack for Python
- **[language-server](../language-server/README.md)**: LSP implementation for IDE integration

---

**Part of the Legesher Project** - Empowering developers to code in their native language.
