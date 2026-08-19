# legesher-i18n

Industrial-strength internationalization infrastructure with 51 language packs, version-aware inheritance,
and multi-provider translation API for multilingual programming.

**Status**: Production-Ready (Pre-Beta) | **Version**: 0.2.x | **Python**: 3.10-3.14

## Overview

The `legesher-i18n` package provides the core internationalization infrastructure for Legesher,
enabling developers to code in their native language. It includes:

- **51 Complete Language Packs**: Support for am, ar, bn, bs, ca, cs, cy, da, de, el, en, es, fa, fi, fr, ga, gd,
  gl, gu, he, hi, hr, hu, id, it, ja, kn, ko, lv, mk, ml, mn, ms, my, nl, no, pl, pt, ro, ru, si, sr, su, sv,
  te, th, tr, ur, uz, vi, zh
- **Version-Aware Language Packs**: Automatic adaptation to Python 3.10-3.14 with inheritance
- **Auto-Detection**: Detects Python version from `pyproject.toml`, `.python-version`, or runtime
- **Pack Inheritance**: Child packs inherit from parents, defining only what's new
- **Schema Validation**: Pydantic-based validation with security checks
- **High Performance**: Thread-safe LRU caching for fast repeated loads
- **Translation API**: Multi-provider dynamic translation with quality-based fallback and cost tracking

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

**51 complete language packs** - All support Python 3.10-3.14 with version inheritance:

- **Amharic (am)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Arabic (ar)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Bengali (bn)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Bosnian (bs)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Catalan (ca)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Czech (cs)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Welsh (cy)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Danish (da)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **German (de)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Greek (el)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **English (en)**: 37 keywords, 72 builtins, 66 exceptions - Canonical reference
- **Spanish (es)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Persian (fa)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Finnish (fi)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **French (fr)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Irish (ga)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Scottish Gaelic (gd)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Galician (gl)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Gujarati (gu)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Hebrew (he)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Hindi (hi)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Croatian (hr)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Hungarian (hu)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Indonesian (id)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Italian (it)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Japanese (ja)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Kannada (kn)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Korean (ko)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Latvian (lv)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Macedonian (mk)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Malayalam (ml)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Mongolian (mn)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Malay (ms)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Burmese (my)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Dutch (nl)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Norwegian (no)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Polish (pl)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Portuguese (pt)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Romanian (ro)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Russian (ru)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Sinhala (si)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Serbian (sr)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Sundanese (su)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Swedish (sv)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Telugu (te)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Thai (th)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Turkish (tr)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Urdu (ur)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Uzbek (uz)**: 37 keywords, 72 builtins, 66 exceptions - Tiny Aya Model translations
- **Vietnamese (vi)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations
- **Chinese Simplified (zh)**: 37 keywords, 72 builtins, 66 exceptions - Aya AI Model translations

Each language pack is independently versioned at `libs/i18n/language-packs/python/{lang}/`

**Note**: Language packs are currently in pre-beta (v0.0.x) and awaiting community validation before v0.1.0 release.

### Pack validation & script policy

Beyond schema validation, packs are guarded by a Unicode/script **safety layer**
that hardens the 51 → 103 language expansion against the corruption classes seen
in machine-translated packs. The policy lives in
`legesher_i18n/script_policy.py` — one `ScriptPolicy` per language declaring its
allowed Unicode script(s), writing direction, and any legitimately-required
format characters. `SchemaValidator.validate_pack_strict` runs every check and
returns a list of `Finding`s (empty == clean):

| Check | Catches |
| --- | --- |
| `check_normalization` | values that aren't NFC/NFKC-stable (e.g. Thai SARA AM) |
| `check_script_consistency` | foreign-script bleed-through (Chinese in a Polish value, Cyrillic in Thai, …) |
| `check_format_chars` | bidi controls, tatweel, BOM, and un-allow-listed zero-width joiners |
| `check_keyword_collisions` | values that equal/NFKC-fold to a live keyword/builtin (incl. the fullwidth `ｉｆ`→`if` spoof) |
| `check_min_interpreter_identifier` | ZWJ-bearing values whose pack declares a minimum interpreter < 3.13 |
| `check_duplicates` / `check_identifier_validity` | duplicate targets and non-identifier values |

Audit every working-tree pack:

```bash
# From libs/i18n/
python -m legesher_i18n.scripts.audit_packs            # all packs
python -m legesher_i18n.scripts.audit_packs --lang si  # one language
```

The `validate-packs` CI workflow runs this audit in **non-blocking** report mode
while data-correction work is in flight; it flips to blocking before the 103
expansion.

#### Adding a language safely

When onboarding a new script/language, satisfy the checklist encoded as a golden
test in `tests/test_new_language_onboarding.py`:

1. **Register a `ScriptPolicy`** in `SCRIPT_POLICIES` keyed by the ISO 639 code
   — listing the orthography's Unicode script(s), `direction` (`"ltr"`/`"rtl"`),
   and any required format char (only Sinhala ZWJ and Persian/Urdu ZWNJ today).
   There is **no permissive fallback**: an unregistered code is default-denied.
2. All translation values must stay within the declared script(s).
3. Values must be NFC/NFKC-stable.
4. No illegal format/bidi characters (only the policy's allow-listed ones).
5. No value may equal a live Python keyword/builtin (except its own target).
6. ZWJ-bearing values must declare `python_version_min >= 3.13`.
7. No duplicate targets (except the intentional `keywords.type == builtins.type`).
8. Add a coverage row by ensuring `tests/test_script_policy_coverage.py` passes
   (it asserts every shipped pack code has a policy — a missing entry fails CI).

The full "how to add a new language" walkthrough lives in the module docstring of
`legesher_i18n/script_policy.py`.

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

### Model and pricing configuration

Model IDs and pricing live in configuration, never in code (CORE-1804):

| Variable | Purpose |
|---|---|
| `LEGESHER_ANTHROPIC_MODEL` | Anthropic model ID used by both the generation pipeline and the translation API (default lives in `legesher_i18n/model_config.py`) |
| `LEGESHER_RATES_FILE` | JSON file of operator-supplied provider rates (see `legesher_i18n/api/rates.py`) |
| `LEGESHER_RATE_ANTHROPIC_INPUT_PER_MTOK` / `LEGESHER_RATE_ANTHROPIC_OUTPUT_PER_MTOK` | Inline per-provider rate overrides |

Legesher ships no prices. Without a configured rate, costs report as
unknown (API layer) or `0.0` (generation pipeline, with a warning at
startup) and the pipeline's `--max-budget` guard cannot enforce.

## CLI Tools

The `legesher-i18n` package includes powerful command-line tools for validating and managing
language packs.

### CLI Usage

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
legesher-i18n validate libs/i18n/programming_languages/python/3.13/es.yml

# Strict mode (fail on warnings)
legesher-i18n validate libs/i18n/programming_languages/python/3.13/es.yml --strict
```

**Example Output:**

```text
Validating: libs/i18n/programming_languages/python/3.13/es.yml
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

```text
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

The script creates a Markdown table showing which keywords are available in each
Python version, with version-specific keywords clearly marked (e.g., `except*`
only appears in Python 3.11+).

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
      - "libs/i18n/languages/**/*.yml"

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

See the [Language Pack Creation Guide](../../docs/guides/creating-language-packs.md)
for instructions on creating new language packs.

### Project Structure

```text
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

Apache License 2.0 - see [LICENSE](LICENSE) file

## Links

- [Legesher Monorepo](../../README.md)
- [Implementation Roadmap](../../docs/src/content/docs/architecture/implementation-roadmap.md)
- [Pre-commit Integration](../../docs/development/pre-commit-language-packs.md)
- [CI/CD Integration](../../docs/development/ci-language-pack-validation.md)
