# legesher-i18n

**Internationalization and Language Pack Management for Legesher**

Version-aware language pack loading with inheritance, Python version detection, and schema validation for multilingual programming.

## Overview

The `legesher-i18n` package provides the core internationalization infrastructure for Legesher, enabling developers to code in their native language. It includes:

- **Version-Aware Language Packs**: Automatic adaptation to Python 3.10-3.13+ with inheritance
- **Auto-Detection**: Detects Python version from `pyproject.toml`, `.python-version`, or runtime
- **Pack Inheritance**: Child packs inherit from parents, defining only what's new
- **Schema Validation**: Pydantic-based validation with security checks
- **Performance**: Caching for fast repeated loads

## Installation

```bash
# From monorepo root
uv install

# Or install package directly
uv add legesher-i18n
```

## Quick Start

### Basic Usage

```python
from legesher_i18n import load_language_pack

# Auto-detect Python version and load Spanish pack
pack = load_language_pack('es')

# Get keyword translations
print(pack.get_keyword_translation('def'))      # "definir"
print(pack.get_keyword_translation('class'))    # "clase"
print(pack.get_builtin_translation('print'))    # "imprimir"
```

### Explicit Version

```python
# Load pack for specific Python version
pack = load_language_pack('es', version='3.11')

# Python 3.11+ specific keyword
print(pack.get_keyword_translation('except*'))  # "excepto*"
```

## Features

### Version-Aware Language Packs

Language packs automatically adapt to different Python versions:

- **Python 3.10+**: Includes `match`/`case` (pattern matching)
- **Python 3.11+**: Adds `except*` (exception groups)
- **Python 3.12+**: Adds `type` (type parameter syntax)
- **Python 3.13**: No new keywords (inherits from 3.12)

### Supported Languages

Current MVP includes:

- **Spanish (es)**: Complete translations for Python 3.10-3.13
- **Arabic (ar)**: Complete translations for Python 3.10-3.13

## Development

### Running Tests

```bash
# From package directory
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=legesher_i18n --cov-report=html
```

## License

MIT License - see [LICENSE](LICENSE) file

## Links

- [Legesher Monorepo](../../README.md)
- [Implementation Roadmap](../../docs/src/content/docs/architecture/implementation-roadmap.md)
