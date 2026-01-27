# legesher-i18n - Claude Code Guide

This file provides guidance for working with the `legesher-i18n` package.

## Package Overview

**Version**: 0.4.0
**Status**: Production-Ready (Pre-Beta)
**Python**: >=3.10,<4.0

Internationalization infrastructure with 26 language packs, version-aware inheritance,
and multi-provider translation API.

## Key Capabilities

- **26 Language Packs**: All in experimental status (see `languages.json`)
- **Version-Aware Loading**: Automatic Python 3.10-3.14 adaptation
- **Pack Inheritance**: Child packs inherit from parents, reducing duplication
- **Translation API**: Multi-provider support (Anthropic, Google, DeepL, LibreTranslate)
- **Schema Validation**: Pydantic-based with security checks
- **CLI Tools**: validate, show, registry, export commands

## Directory Structure

```text
libs/i18n/
├── legesher_i18n/
│   ├── __init__.py           # Public API
│   ├── cli.py                # CLI commands
│   ├── pack_loader.py        # Pack loading with inheritance
│   ├── schema_validator.py   # Validation logic
│   ├── version_detector.py   # Python version detection
│   ├── language_registry.py  # Language metadata API
│   ├── languages.json        # SOURCE OF TRUTH for languages
│   └── api/
│       ├── providers/        # Translation providers
│       ├── usage_tracker.py  # API usage tracking
│       └── dashboard.py      # Usage dashboard
├── language-packs/
│   └── python/
│       ├── ar/, da/, de/, ...  # 26 language packs
│       └── version-index.yml   # Python version inheritance
└── tests/
```

## Language Pack Structure

Each language pack at `language-packs/python/{lang}/`:

```text
{lang}/
├── legesher_i18n_python_{lang}/
│   ├── __init__.py
│   └── packs/
│       ├── 3.10.yml   # Base file with ALL translations
│       ├── 3.11.yml   # extends: 3.10.yml (only new terms)
│       ├── 3.12.yml   # extends: 3.11.yml
│       ├── 3.13.yml   # extends: 3.12.yml
│       └── 3.14.yml   # extends: 3.13.yml
├── pyproject.toml
├── CHANGELOG.md
├── README.md
└── REFERENCE.md
```

## Key APIs

### Loading Language Packs

```python
from legesher_i18n import load_language_pack

# Auto-detect Python version
pack = load_language_pack('es')

# Explicit version
pack = load_language_pack('es', version='3.11')

# Get translations
pack.get_keyword_translation('def')      # "definir"
pack.get_builtin_translation('print')    # "imprimir"
```

### Language Registry

```python
from legesher_i18n import (
    LANGUAGE_METADATA,
    get_language_name,
    get_native_name,
    is_rtl_language,
    is_supported_language,
    get_available_language_codes,
)

# Check if language is supported
is_supported_language('es')  # True

# Get native name
get_native_name('ar')  # "العربية"
```

## CLI Commands

```bash
# Validate packs
legesher-i18n validate path/to/pack.yml
legesher-i18n validate path/to/pack.yml --strict

# Show versions
legesher-i18n show es
legesher-i18n show ar --target python

# Registry commands
legesher-i18n registry list
legesher-i18n registry validate --lang es

# Export
legesher-i18n export json --lang es
legesher-i18n export csv --lang ar
```

## Testing

```bash
cd libs/i18n

# Run all tests
uv run pytest tests/ -v

# Run CLI tests
uv run pytest tests/test_cli.py -v

# With coverage
uv run pytest tests/ --cov=legesher_i18n --cov-report=html
```

## Translation API (Optional)

Install with API support:

```bash
pip install legesher-i18n[api]
```

```python
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import LibreTranslateProvider

coordinator = TranslationCoordinator(
    providers=[LibreTranslateProvider()],
)

result = await coordinator.translate("Hello", "en", "es")
```

## Common Tasks

### Adding a New Language Pack

1. Create directory: `language-packs/python/{lang}/`
2. Copy structure from existing pack (e.g., `ar/`)
3. Create YAML files with `extends` for inheritance
4. Update root `pyproject.toml` sources and workspace
5. Run `uv sync`
6. Add entry to `languages.json`

### Updating Translations

- **Existing terms**: Update in `3.10.yml` (base file)
- **New Python version terms**: Add only to that version's YAML file
- Run `legesher-i18n validate` to check

### Language Status

All 26 languages are currently **experimental**:

- Translations work but await community validation
- Status defined in `languages.json`
- Will transition to **accepted** after validation

## Source of Truth

- **Language metadata**: `legesher_i18n/languages.json`
- **Pack versions**: Defined in each pack's `pyproject.toml` file (currently 0.0.1–0.0.2)
- **Python version keywords**: `language-packs/python/version-index.yml`
