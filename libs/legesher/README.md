# legesher

> Command-line interface for coding in any language

**Status**: Pre-Beta | **Languages**: 51 | **Version**: see `pyproject.toml`

The legesher CLI is your gateway to programming in your native language. Translate Python code between English and localized
keywords, manage git integration for collaborative workflows, and configure your multilingual development environment.

## About

The `legesher` package provides command-line tools for developers who want to write code in their native language
instead of English. It handles:

- **Project Setup**: `legesher init` scaffolds configuration, git integration, and AI context
- **Code Translation**: Convert Python files between languages using language packs
- **Execution**: `legesher run` executes a native-language file directly
- **Git Integration**: Seamlessly collaborate with English-speaking developers via git filters
- **Configuration**: Manage project and user settings for language preferences
- **Metadata**: Inspect and validate the translation history recorded for your files

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
legesher init --language es

# Translate a Python file to Spanish
legesher translate mi_codigo.py --to es

# Set up git integration for collaborative development
legesher git setup

# View available language packs
legesher-i18n registry list
```

## Commands

### `legesher init`

Scaffold Legesher in a Python project: write `.legesher/config.yml`, optionally wire the git filters, and
optionally generate AI context files.

```bash
# Interactive setup
legesher init

# Pre-select languages and skip the prompts
legesher init --language es --language fr --git --no-ai-context
```

### `legesher translate`

Translate Python source files between languages.

```bash
# Translate a single file to Spanish
legesher translate app.py --to es

# Translate to English (canonical form). --from defaults to en, so name the source
legesher translate mi_app.py --from es --to en

# Translate between two non-English languages
legesher translate code.py --from es --to fr

# Translate and write to different file
legesher translate input.py --to es --output salida.py

# Translate an entire directory
legesher translate src/ --to es --output traducido/
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
- `--from LANG`: Source language code (default: `en`)
- `--output PATH`: Output file or directory. Omitted, a single file goes to stdout and a directory goes to a
  sibling `<dir>_translated/`. Your input file is never overwritten in place
- `--full`: Enable full LLM translation (identifiers, comments, strings, docstrings)
- `--llm-backend`: LLM backend: `anthropic`, `cohere-aya`, or `openai-compat` (default: anthropic)
- `--llm-base-url`: Base URL for openai-compat backend (e.g., `http://localhost:8000`)
- `--llm-model`: Model name for any backend (default: the backend's own default)
- `--identifier-map PATH`: Load/save identifier glossary for cross-file consistency
  (default: `.legesher/identifier_map.json`); `--no-identifier-map` disables it
- `--checkpoint PATH`: Resume interrupted batch jobs

**Example Output:**

```bash
$ legesher translate hello.py --to es
definir greet():
    imprimir("hi")

$ legesher translate hello.py --to es --output hola.py
✓ Translated hello.py → hola.py
```

### `legesher run`

Execute a native-language Python file.

```bash
legesher run programa.py --lang es

# Pass arguments through to the script
legesher run programa.py --lang es --args "--verbose input.txt"
```

`--lang` wins. Without it the language comes from the `language:` key in `.legesher/config.yml`,
falling back to `en` when that key is absent. A config written by `legesher init` does not have that
key (see [Configuration](#configuration)), so dropping `--lang` there runs the file untranslated and
Python raises `SyntaxError`. Pass `--lang`, or write the config with `legesher git setup`.

### `legesher git`

Manage git filter integration for multilingual repositories.

```bash
# Set up git filters for current repository
legesher git setup

# Set up with specific language
legesher git setup --language es

# Check git filter status
legesher git status
```

**Subcommands:**

- **`setup`**: Configure git clean/smudge filters to store code in canonical English while working in your native language
- **`status`**: Display current git filter configuration and language settings

**Example Output:**

```bash
$ legesher git setup --language es
✓ Found git repository at: /path/to/repo

Validating language pack 'es'...
✓ Loaded language pack: es (39 keywords, 143 builtins)

Creating configuration...
✓ Saved project config to: /path/to/repo/.legesher/config.yml

Configuring git filters...

Configuring .gitattributes...
✓ Updated .gitattributes

Initializing metadata system...
✓ Created metadata directory: /path/to/repo/.legesher/metadata
✓ Metadata will be tracked in git
✓ Metadata system initialized successfully

Verifying setup...
✓ Git filter setup verified

============================================================
✓ Git filter setup complete!
============================================================

Your repository is now configured for multilingual code.
Language: es
Storage: English (canonical)
```

The trailing "Next steps" list is omitted above. The `143 builtins` in that output is not the pack's
built-in count: the translator merges the pack's 70 exception names into its built-in map before
reporting, so `143` is the pack's 73 built-ins plus its 70 exceptions. The per-category counts are in
[legesher-i18n](../i18n/README.md#supported-languages).

### `legesher config`

Manage project and global configuration.

Project configuration is created by `legesher init` or `legesher git setup`; `config` reads and writes it
afterwards. `get` and `list` report the keys that are actually in the files, so what they show depends on
which of those two commands wrote the config (see [Configuration](#configuration)).

```bash
# Set default language for project
legesher config set language es

# Get the key back
legesher config get language

# List all configuration settings (user-level merged with project)
legesher config list

# Set user-level configuration
legesher config set language es --global
```

`config get` exits 1 with `Key '<key>' not found.` when the key is absent from both files: it does not
fall back to the built-in defaults.

**Configuration Locations:**

- **Project**: `.legesher/config.yml` (current directory)
- **User**: `~/.legesher/config.yml` (user home directory)

**Available Settings** (the keys the runtime reads, and the ones `legesher git setup` writes):

- `language`: Default language code (e.g., `es`, `fr`, `ar`)
- `python_version`: Target Python version (e.g., `3.12`, `3.11`), or `null` to auto-detect
- `git.canonical_language`: The language stored in the repository (default `en`)
- `git.filter_enabled`: Enable git filter integration (boolean)
- `runtime.cache_size`: Translation cache size. Honoured when present; neither command writes it out
- `metadata.enabled`, `metadata.directory`, `metadata.track_in_git`,
  `metadata.verbose_history`, `metadata.max_history_entries`: Metadata tracking

`legesher init` writes a different set of keys (`languages`, `git.enabled`, `ai_context.*`,
`translation.*`, `editor.*`). `config get` and `config list` will report those verbatim, but nothing in
the runtime consults them.

### `legesher metadata`

Inspect the translation metadata Legesher records for the files in your repository. Every subcommand except
`list` takes a file path, not a language code.

```bash
# Show metadata for one file
legesher metadata show src/calculator.py

# Show the clean/smudge history for a file
legesher metadata history src/calculator.py --limit 20

# List every file with recorded metadata
legesher metadata list

# Show the raw YAML
legesher metadata raw src/calculator.py

# Check a metadata file is present, valid YAML, and complete
legesher metadata validate src/calculator.py
```

Every subcommand takes `--repo PATH` to point at a repository other than the current directory.

To inspect a *language pack* rather than a file's history, use the `legesher-i18n` CLI:

```bash
legesher-i18n registry list
legesher-i18n validate libs/i18n/language-packs/python/es/legesher_i18n_python_es/packs/3.13.yml
```

## Configuration

The legesher CLI uses YAML configuration files for project and user settings: `.legesher/config.yml`
in a project, `~/.legesher/config.yml` for user-wide defaults.

> **Known issue: `legesher init` and `legesher git setup` write two different, incompatible shapes.**
> `git setup` writes the shape the runtime reads. `init` writes its own shape, which the runtime does
> not understand, so after `legesher init --language es` the working language silently falls back to
> `en`: `legesher git status` reports `Language: en`, `legesher run` without `--lang` fails to compile
> the file, `config get language` exits 1, and the git clean filter stores your file unchanged instead
> of translating it to English. Reconciling the two is tracked as its own issue. Until it lands, run
> `legesher git setup --language <code>` after `legesher init` (it rewrites `config.yml` in the shape
> everything else reads, and leaves the generated AI context files alone).

### Project configuration written by `legesher git setup`

This is the shape `LegesherConfig` loads, and the keys `legesher config` documents above:

```yaml
language: es
python_version: null      # null means auto-detect
git:
  canonical_language: en
  filter_enabled: true
metadata:
  enabled: true
  directory: .legesher/metadata
  track_in_git: true
  verbose_history: false
  max_history_entries: 100
```

### Project configuration written by `legesher init`

Same path, different keys. Nothing in the runtime reads the keys unique to
this shape; `python_version` and `git.canonical_language` are shared with the
shape above and are read:

```yaml
# Languages enabled in this project
languages:                # a list, not the single `language:` string above
  - es

python_version: "3.13"

git:
  enabled: true           # not git.filter_enabled
  canonical_language: "en"

ai_context:
  enabled: true
  context_files:
    - AI-CONTEXT-es.md

translation:
  default_source: "en"
  default_target: "es"
  preserve_comments: true
  preserve_strings: true

editor:
  lsp_hover: true
  inline_completion: true
  bilingual_tooltips: true
```

### User Configuration

`~/.legesher/config.yml` holds user-wide defaults and uses the same keys as the `git setup` shape.

### Configuration Precedence

Settings are resolved in this order (highest to lowest priority):

1. Command-line flags (e.g., `--language es`)
2. Project configuration (`.legesher/config.yml`)
3. User configuration (`~/.legesher/config.yml`)
4. Built-in defaults

## Examples

### Example 1: Starting a New Spanish Project

```bash
# Create project directory
mkdir mi_proyecto
cd mi_proyecto
git init

# Initialize legesher configuration (writes config.yml, git filters, AI context)
legesher init --language es --git --python-version 3.13

# Rewrite config.yml in the shape the runtime reads. Without this the filters are
# installed but inert, and your code is stored in Spanish. See Configuration above
legesher git setup --language es --python-version 3.13

# Create a Python file in Spanish. Keywords and builtins are Spanish;
# your own names, and everything inside strings, stay as you write them
cat > hola.py << 'EOF'
definir saludar(nombre):
    """Saluda a una persona por su nombre."""
    imprimir(f"¡Hola, {nombre}!")

saludar("Mundo")
EOF

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
legesher git setup --language es

# Translate existing code to Spanish for local development
legesher translate src/ --to es --output src_es/

# Work in Spanish...
# All commits automatically store in English via git filters
```

### Example 3: Switching Between Languages

```bash
# Currently working in Spanish (config written by `legesher git setup --language es`)
legesher config get language
# Output: es

# Translate the codebase to French
legesher translate src_es/ --from es --to fr --output src_fr/

# Update configuration
legesher config set language fr

# Now working in French!
```

### Example 4: Checking a File's Translation Record

```bash
# Show what Legesher has recorded for a file
legesher metadata show src/calculator.py

# Check that record is present and well-formed
legesher metadata validate src/calculator.py
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
├── legesher/
│   ├── __init__.py
│   ├── config.py           # Configuration loading and precedence
│   ├── cli/
│   │   ├── main.py         # Main CLI entry point
│   │   ├── init.py         # init command
│   │   ├── translate.py    # translate command
│   │   ├── run.py          # run command
│   │   ├── git.py          # git command group
│   │   ├── config_cmd.py   # config command group
│   │   └── metadata.py     # metadata command group
│   └── runtime/
│       ├── import_hook.py  # Import hook for `legesher run`
│       ├── source_mapper.py
│       └── error_handler.py
├── tests/
├── pyproject.toml
└── README.md
```

## Contributing

We welcome contributions! Please see:

- [CONTRIBUTING.md](../../CONTRIBUTING.md) in the monorepo root
- [Development Guide](../../DEVELOPMENT.md)
- [Open Issues](https://github.com/legesher/legesher/issues)

## License

Apache License 2.0 - see [LICENSE](./LICENSE) for details.

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
- **[legesher-i18n-python-es](../i18n/language-packs/python/es/README.md)**: Spanish language pack for Python
- **[legesher-language-server](../language-server/README.md)**: LSP implementation for IDE integration
- **[legesher-runtime](../runtime/README.md)**: Localized tracebacks, used by `legesher run`

---

**Part of the Legesher Project** - Empowering developers to code in their native language.
