# legesher-language-server - Claude Code Guide

This file provides guidance for working with the `legesher-language-server` package.

## Package Overview

**Version**: 0.1.0
**Status**: Production-Ready (Pre-Beta)
**Python**: >=3.10,<4.0
**CLI Entry Point**: `legesher-lsp`

Language Server Protocol (LSP) implementation for IDE integration, built on pygls 2.0.

## Key Capabilities

- **Four LSP Providers**: Hover, Completion, Diagnostic, Semantic Tokens
- **Pylance Integration**: Real-time code translation proxy
- **Multi-Language**: Supports all 26 experimental languages
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
│   └── pylance/              # Pylance integration (CORE-360)
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
- CORE-360: Pylance integration
- CORE-448: pygls 2.0 migration
- CORE-450: Semantic tokens provider
