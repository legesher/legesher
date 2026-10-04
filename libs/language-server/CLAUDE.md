# legesher-language-server - Claude Code Guide

This file provides guidance for working with the `legesher-language-server` package.

## Package Overview

**Version**: see `pyproject.toml` (the only place it is written; `__version__` reads the installed metadata)
**Status**: Production-Ready (Pre-Beta)
**Python**: >=3.10,<4.0
**CLI Entry Point**: `legesher-lsp`

Language Server Protocol (LSP) implementation for IDE integration, built on pygls 2.0.

## Key Capabilities

- **Four LSP Providers**: Hover, Completion, Diagnostic, Semantic Tokens
- **Enhanced Python intelligence**: real-time code translation proxy
- **Multi-Language**: Supports all 51 experimental languages
- **Configuration**: Environment variable and Pydantic-based config
- **pygls 2.0**: Latest LSP library for Python 3.13 compatibility

## Directory Structure

```text
libs/language-server/
├── legesher_language_server/
│   ├── __init__.py           # Package init
│   ├── server.py             # Main LSP server
│   ├── config.py             # Pydantic configuration
│   ├── providers/
│   │   ├── hover.py          # Hover provider (CORE-357)
│   │   ├── completion.py     # Completion provider (CORE-358)
│   │   ├── diagnostic.py     # Diagnostic provider (CORE-359)
│   │   └── semantic_tokens.py # Semantic tokens (CORE-450)
│   └── enhanced_intelligence.py  # Language-server proxy (CORE-360)
├── tests/
│   ├── unit/
│   └── integration/
└── pyproject.toml
```

## LSP Providers

### Hover Provider (CORE-357)

Provides translated docstrings, keyword documentation, and cultural comments on hover.

### Completion Provider (CORE-358)

Localized keyword and builtin completion with fuzzy matching.

### Diagnostic Provider (CORE-359)

Translated error messages with 41 templates across 17 error types.

### Semantic Tokens Provider (CORE-450)

Syntax highlighting for translated keywords.

## Configuration

Via environment variables:

```bash
export LEGESHER_SOURCE_LANG=en        # Source language (default: en)
export LEGESHER_TARGET_LANG=es        # Target language (default: es)
export LEGESHER_PYTHON_VERSION=3.13   # Python version (auto-detected)
export LEGESHER_CACHE_SIZE=1000       # Cache size (default: 1000)
export LEGESHER_CACHE_TTL=3600        # Cache TTL in seconds (default: 3600)
export LEGESHER_LOG_LEVEL=INFO        # Log level (default: INFO)
```

## Running the Server

```bash
# Start LSP server
legesher-lsp

# With specific language
LEGESHER_TARGET_LANG=es legesher-lsp

# With verbose logging
LEGESHER_LOG_LEVEL=DEBUG legesher-lsp

# Check version
legesher-lsp --version
```

## Testing

```bash
cd libs/language-server

# Run all tests
uv run pytest tests/ -v

# Run provider tests
uv run pytest tests/unit/test_providers.py -v

# With coverage
uv run pytest tests/ --cov=legesher_language_server --cov-report=html
```

**Test coverage**: ~70% (improved from 21% after pygls 2.0 migration)

The clean-environment suite (`tests/test_clean_environment.py`) is marked
`scheduled` and deselected by default. It builds the wheels, installs them into
an empty virtualenv and drives an LSP session through the installed
`legesher-lsp`. Run it with `make test-language-server-scheduled` from the repo
root before any release.

## Releases

This package has its own release train, the same model as `legesher-mcp`
(CORE-2203):

- `.github/workflows/release-language-server.yml` runs on a push to `main` that
  touches `libs/language-server/`. It checks the last release tag, runs the
  clean-environment suite, then semantic-release bumps `project.version` and
  tags `language-server-vX.Y.Z`. The config is `[tool.semantic_release]` in
  this package's `pyproject.toml`.
- The next version is computed from every commit in the repository since the
  last `language-server-v*` tag, not only commits under `libs/language-server/`:
  semantic-release scopes by tag, not by path (CORE-1852).
- Do not hand-edit `project.version`. The train refuses to run unless the last
  reachable `language-server-v*` tag matches it; the baseline tag is
  `language-server-v0.1.3`.
- Uploading to PyPI is a separate, manual `publish-pypi.yml` run with the
  `language-server` target, after `legesher-i18n` is on the same index. A PyPI
  upload is public and permanent (CORE-626).

## Dependencies

- `pygls>=2.0.0,<3.0.0` - LSP library (Python 3.13 compatible)
- `pydantic>=2.5.0` - Configuration validation
- `lru-dict>=1.3.0` - Fast LRU caching
- `pyyaml>=6.0.0` - YAML configuration
- `legesher-i18n` - Language pack loading

## Common Tasks

### Adding a New LSP Feature

1. Create provider in `providers/`
2. Register in `server.py`
3. Add tests in `tests/unit/`
4. Update VS Code extension if client-side changes needed

### Debugging LSP Issues

1. Set `LEGESHER_LOG_LEVEL=DEBUG`
2. Check VS Code Output panel → "Legesher Language Server"
3. Use `legesher.trace.server: "verbose"` in VS Code settings

### Testing with VS Code

1. Start server: `legesher-lsp`
2. Configure VS Code: `legesher.serverCommand: "legesher-lsp"`
3. Open Python file to trigger connection

## pygls 2.0 Migration (CORE-448)

The server was migrated from pygls 1.3.1 to 2.0.0 for Python 3.13 compatibility.
Key changes:

- Updated async patterns
- New server lifecycle management
- Improved type annotations

## Related Issues

- CORE-357: Hover provider
- CORE-358: Completion provider
- CORE-359: Diagnostic provider
- CORE-360: enhanced Python intelligence
- CORE-448: pygls 2.0 migration
- CORE-450: Semantic tokens provider
