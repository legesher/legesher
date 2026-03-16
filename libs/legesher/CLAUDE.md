# legesher - Claude Code Guide

This file provides guidance for working with the main `legesher` CLI package.

## Package Overview

**Version**: 0.4.0
**Status**: Production-Ready (Pre-Beta)
**Python**: >=3.10,<4.0
**CLI Entry Point**: `legesher`

The main user-facing package providing CLI tools for code translation, git integration,
and metadata viewing.

## Key Capabilities

- **Code Translation**: Convert Python files between 51 languages
- **Git Integration**: Setup and manage git filter integration
- **Metadata**: View and validate language pack information
- **Runtime Import Hooks**: Transparent code translation at import time

## Directory Structure

```text
libs/legesher/
├── legesher/
│   ├── __init__.py       # Package init with version
│   ├── cli/
│   │   ├── __init__.py   # CLI package
│   │   ├── main.py       # CLI entry point
│   │   ├── init.py       # init command
│   │   ├── translate.py  # translate command
│   │   ├── run.py        # run command
│   │   ├── git.py        # git commands (setup, status)
│   │   └── metadata.py   # metadata commands
│   └── config.py         # Configuration management
├── tests/
│   ├── unit/
│   └── integration/
└── pyproject.toml
```

## CLI Commands

### translate - Convert Code

```bash
# Translate file
legesher translate input.py --from es --to en --output output.py

# Translate directory
legesher translate src/ --from es --to en --output translated/

# In-place translation
legesher translate code.py --from es --to en --in-place

# Auto-detect source language
legesher translate input.py --to en -o output.py

# Pipe translation
cat input.py | legesher translate --from es --to en
```

### git - Repository Integration

```bash
# Setup git filters for a repository
legesher git setup

# Show current git configuration
legesher git status
```

### metadata - Language Pack Info

```bash
# List installed language packs
legesher metadata list

# Show details for a language
legesher metadata show es

# Validate metadata
legesher metadata validate
```

## Configuration Files

Configuration is managed via `legesher/config.py` module.

**Project config** (`.legesher/config.yml` in git repo root):

```yaml
language: es
python_version: "3.13"
git:
  canonical_language: en
```

**Global config** (`~/.legesher/config.yml`):

```yaml
language: en
python_version: null # Auto-detect
```

**Precedence** (highest to lowest):

1. Project config (`.legesher/config.yml`)
2. User global config (`~/.legesher/config.yml`)
3. Default values

## Testing

```bash
cd libs/legesher

# Run all tests
uv run pytest tests/ -v

# Run CLI tests
uv run pytest tests/unit/test_cli.py -v

# Run integration tests
uv run pytest tests/integration/ -v

# With coverage
uv run pytest tests/ --cov=legesher --cov-report=html
```

## Dependencies

- `click>=8.0.0` - CLI framework
- `pyyaml>=6.0` - YAML configuration
- `questionary>=2.0.0` - Interactive prompts
- `legesher-core` - Translation engine
- `legesher-i18n` - Language packs

## Common Tasks

### Adding a New CLI Command

1. Create command file in `legesher/cli/`
2. Use Click decorators for argument parsing
3. Register in `legesher/cli/main.py` using `cli.add_command()`
4. Add tests in `tests/`

### Debugging Translation

```bash
# Verbose output
legesher translate input.py --to en --verbose

# Check git configuration
legesher git status

# Verify language pack
legesher metadata show es
```

## Runtime Import Hooks

For transparent translation at import time:

```python
from legesher.runtime import install_hooks

# Install hooks for Spanish code
install_hooks(language='es')

# Now Spanish Python files can be imported directly
import mi_modulo_espanol  # Translated on-the-fly
```

## Integration with Other Packages

- Uses `legesher-core` for actual translation
- Uses `legesher-i18n` for language pack loading
- Git filters call back to this CLI
