# legesher-i18n

Version-aware language pack loading with inheritance, Python version detection, schema validation, and
dynamic translation API for multilingual programming.

## Overview

The `legesher-i18n` package provides the core internationalization infrastructure for Legesher,
enabling developers to code in their native language. It includes:

- **Version-Aware Language Packs**: Automatic adaptation to Python 3.10-3.13+ with inheritance
- **Auto-Detection**: Detects Python version from `pyproject.toml`, `.python-version`, or runtime
- **Pack Inheritance**: Child packs inherit from parents, defining only what's new
- **Schema Validation**: Pydantic-based validation with security checks
- **Performance**: Caching for fast repeated loads
- **Translation API**: Multi-provider dynamic translation with quality-based fallback (NEW!)

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

### Translation API (Optional)

Dynamic translation support for content not in language packs:

```bash
# Install with API support
pip install legesher-i18n[api]
```

```python
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import LibreTranslateProvider

# Free, self-hosted translation (no API key required)
coordinator = TranslationCoordinator(
    providers=[LibreTranslateProvider()],
)

result = await coordinator.translate("Hello, world!", "en", "es")
print(result.text)  # "¡Hola, mundo!"
```

**Features:**

- Multi-provider support (DeepL, Google Translate, LibreTranslate)
- Automatic quality-based fallback
- Usage tracking and cost monitoring
- SQLite and Redis caching
- CLI tools for monitoring

**Documentation:**

- [Full API Documentation](docs/translation-api.md)
- [Quick Start Guide](docs/translation-api-quickstart.md)

## CLI Tools

The `legesher-i18n` package includes powerful command-line tools for validating and managing language packs.

### Installation

After installing the package, the `legesher-i18n` CLI is automatically available:

```bash
uv pip install -e libs/i18n
legesher-i18n --help
```

### Available Commands

#### `validate` - Validate Language Packs

Validate language pack files with schema validation, completeness checks, and inheritance verification.

```bash
# Validate a single pack
legesher-i18n validate libs/i18n/languages/python/3.13/es.yml

# Strict mode (fail on warnings)
legesher-i18n validate libs/i18n/languages/python/3.13/es.yml --strict
```

**Example Output:**

```
Validating: libs/i18n/languages/python/3.13/es.yml
✅ Schema validation passed

Loading pack with inheritance...
✅ Pack loaded successfully

Pack Information:
   Language: es
   Target: python
   Version: 3.13
   Keywords: 37
   Builtins: 34
   Inheritance: 3.10 → 3.11 → 3.12 → 3.13

✅ Validation complete! (0 warnings)
```

**Validation Checks:**
- Schema validation (required fields, types, format)
- Completeness checks (keywords, metadata)
- Inheritance chain verification
- Path traversal security checks

#### `show` - Display Version Information

Show all available versions for a language with keyword counts and inheritance chains.

```bash
# Show all versions for Spanish
legesher-i18n show es

# Show versions for specific target
legesher-i18n show ar --target python
```

**Example Output:**

```
       ES Language Packs for Python
┏━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Version ┃ Keywords ┃ Builtins ┃ Extends ┃
┡━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ 3.10    │       37 │       34 │ —       │
│ 3.11    │        1 │        0 │ → 3.10  │
│ 3.12    │        1 │        0 │ → 3.11  │
│ 3.13    │        0 │        0 │ → 3.12  │
└─────────┴──────────┴──────────┴─────────┘

Found 4 version(s) for es
```

### Compatibility Matrix Generator

Generate comprehensive Markdown tables showing keyword availability across Python versions:

```bash
# Generate matrix for Spanish
python libs/i18n/scripts/generate_compatibility_matrix.py es

# Save to file
python libs/i18n/scripts/generate_compatibility_matrix.py es \
  --output docs/compatibility/es-keywords.md
```

**Generated Output:**

The script creates a Markdown table showing which keywords are available in each Python version, with version-specific keywords clearly marked (e.g., `except*` only appears in Python 3.11+).

### Integration Examples

#### Pre-commit Hook

Automatically validate language packs before committing:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-language-packs
        name: Validate language packs
        entry: uv run legesher-i18n validate
        language: system
        files: 'libs/i18n/languages/.*\.yml$'
        pass_filenames: true
```

**Setup:**

```bash
pip install pre-commit
pre-commit install
```

See [Pre-commit Integration Guide](../../docs/development/pre-commit-language-packs.md) for details.

#### CI/CD Validation

Validate language packs in GitHub Actions:

```yaml
# .github/workflows/validate-packs.yml
name: Validate Language Packs

on:
  pull_request:
    paths:
      - 'libs/i18n/languages/**/*.yml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: |
          cd libs/i18n
          uv sync
          uv run legesher-i18n validate languages/**/*.yml --strict
```

See [CI Integration Guide](../../docs/development/ci-language-pack-validation.md) for more strategies.

## Development

### Running Tests

```bash
# From package directory
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=legesher_i18n --cov-report=html

# Run CLI tests specifically
uv run pytest tests/test_cli.py -v
```

### Creating Language Packs

See the [Language Pack Creation Guide](../../docs/guides/creating-language-packs.md) for instructions on creating new language packs.

### Project Structure

```
libs/i18n/
├── legesher_i18n/
│   ├── __init__.py          # Public API
│   ├── cli.py               # CLI commands
│   ├── pack_loader.py       # Pack loading with inheritance
│   ├── schema_validator.py  # Validation logic
│   ├── version_detector.py  # Python version detection
│   └── version_index.py     # Version index management
├── languages/
│   └── python/
│       ├── 3.10/            # Python 3.10 packs
│       ├── 3.11/            # Python 3.11 packs
│       ├── 3.12/            # Python 3.12 packs
│       └── 3.13/            # Python 3.13 packs
├── scripts/
│   └── generate_compatibility_matrix.py
└── tests/
    ├── test_cli.py          # CLI command tests
    ├── test_pack_loader.py  # Pack loading tests
    └── test_schema_validator.py
```

## License

MIT License - see [LICENSE](LICENSE) file

## Links

- [Legesher Monorepo](../../README.md)
- [Implementation Roadmap](../../docs/src/content/docs/architecture/implementation-roadmap.md)
- [Pre-commit Integration](../../docs/development/pre-commit-language-packs.md)
- [CI/CD Integration](../../docs/development/ci-language-pack-validation.md)
