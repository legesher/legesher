# legesher-i18n

Industrial-strength internationalization infrastructure with 56 language packs, version-aware inheritance,
and multi-provider translation API for multilingual programming.

**Status**: Pre-Beta | **Python**: 3.10-3.14 | **Version**: see `pyproject.toml`

## Overview

The `legesher-i18n` package provides the core internationalization infrastructure for Legesher,
enabling developers to code in their native language. It includes:

- **56 Complete Language Packs**: Support for am, ar, bn, bs, ca, cs, cy, da, de, el, en, es, fa, fi, fr, ga, gd,
  gl, gu, he, hi, hr, hu, id, it, ja, kn, ko, lv, mk, ml, mn, ms, my, ne, nl, no, pl, pt, ro, ru, si, sr, su, sv,
  sw, te, th, tl, tr, uk, ur, uz, vi, xh, zh
- **Version-Aware Language Packs**: Automatic adaptation to Python 3.10-3.14 with inheritance
- **Auto-Detection**: Detects Python version from `pyproject.toml`, `.python-version`, or runtime
- **Pack Inheritance**: Child packs inherit from parents, defining only what's new
- **Schema Validation**: Pydantic-based validation with security checks
- **High Performance**: Thread-safe LRU caching for fast repeated loads
- **Translation API**: Multi-provider dynamic translation with quality-based fallback and cost tracking

## Installation

```bash
# From monorepo root
uv sync --all-extras

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
- **Python 3.13**: No new keywords (inherits from 3.12), one new exception
- **Python 3.14**: No new terms yet (inherits from 3.13)

### Supported Languages

**56 complete language packs** - All support Python 3.10-3.14 with version inheritance, and all carry the same
term coverage:

- **Keywords**: 39 (the 3.10 set plus `except*` in 3.11 and `type` in 3.12)
- **Built-ins**: 73 built-in functions, types, and constants
- **Exceptions**: 70 exception classes

Those are the pack's own categories. `legesher-core` merges exception names into the built-in map when
it loads a pack, so anything reporting `get_pack_info()` — `legesher git setup`, for one — says
`143 builtins`, which is these 73 plus these 70, not a disagreement with the numbers above.

Codes: am, ar, bn, bs, ca, cs, cy, da, de, el, en, es, fa, fi, fr, ga, gd, gl, gu, he, hi, hr, hu, id, it, ja, kn,
ko, lv, mk, ml, mn, ms, my, ne, nl, no, pl, pt, ro, ru, si, sr, su, sv, sw, te, th, tl, tr, uk, ur, uz, vi, xh, zh

`en` is Python's own vocabulary, the run form every pack maps to. Every other pack is machine-generated and awaiting
native-speaker review; which model produced a given pack is recorded in that pack's `metadata.author` field, and
each pack ships its own README at `libs/i18n/language-packs/python/{lang}/README.md` with its counts and Python
version coverage.

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

- Multi-provider support (Anthropic, Cohere Aya, DeepL, Google Translate, LibreTranslate, and any
  OpenAI-compatible endpoint). The `api` extra installs the DeepL and Google clients plus `httpx`; the Anthropic
  provider additionally needs the `anthropic` SDK
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
legesher-i18n validate libs/i18n/language-packs/python/es/legesher_i18n_python_es/packs/3.13.yml

# Strict mode (fail on warnings). Point it at the base pack: a leaf version file
# warns that it defines no keywords of its own, which --strict turns into a failure
legesher-i18n validate libs/i18n/language-packs/python/es/legesher_i18n_python_es/packs/3.10.yml --strict
```

**Example Output:**

```text
Validating: libs/i18n/language-packs/python/es/legesher_i18n_python_es/packs/3.13.yml
✅ Schema validation passed
⚠️  Warning: No keywords defined in pack

Loading pack with inheritance...
✅ Pack loaded successfully

Pack Information:
   Language: es
   Target: python
   Version: 3.13
   Keywords: 39
   Builtins: 73
   Inheritance: <abs path>/packs/3.10.yml → <abs path>/packs/3.11.yml → <abs path>/packs/3.12.yml → <abs path>/packs/3.13.yml

✅ Validation complete! (1 warning)
```

Two things in that output are expected and not defects in the pack. The "No keywords defined in pack"
warning is about the 3.13 file on its own: 3.13 adds no keywords of its own and inherits all 39 from
3.12, which is why the resolved count below it is still 39. `--strict` turns that warning into a
failure, so do not point `--strict` at a leaf version file. And `Inheritance:` prints the four absolute
file paths, not the short `3.10 → 3.11 → …` form; they are elided above for width.

**Validation Checks:**

- Schema validation (required fields, types, format)
- Completeness checks (keywords, metadata)
- Inheritance chain verification
- Path traversal security checks

#### `registry list` - List the Shipped Packs

List every pack in the registry with its term counts and completeness.

```bash
legesher-i18n registry list

# For a specific target and Python version
legesher-i18n registry list --target python --version 3.13
```

**Example Output:**

```text
│ es   │ ES       │       39 │       73 │ ✓ complete │
│ fr   │ FR       │       39 │       73 │ ✓ complete │
...
Found 56 language pack(s)
```

#### `export` - Export Pack Contents

`export json`, `export csv`, and `export all` write a pack's terms out for tooling or review.

### Compatibility Matrix Generator (currently broken)

`scripts/generate_compatibility_matrix.py` was written to emit a Markdown table of keyword availability
per Python version. **It does not run today.** It still reads packs from a `libs/i18n/languages/`
directory that no longer exists, so every invocation exits 1:

```text
$ python libs/i18n/scripts/generate_compatibility_matrix.py es
Generating compatibility matrix for es...
Error: Languages directory not found: .../libs/i18n/languages
```

Porting it to the `language-packs/python/{lang}/` layout is open work. Until then, use
`legesher-i18n registry list` for per-pack counts, and each pack's own README for its Python version
coverage.

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
        files: '^libs/i18n/language-packs/.*/packs/.*\.yml$'
        pass_filenames: true
```

**Setup:**

```bash
pip install pre-commit
pre-commit install
```

This repository's own `.pre-commit-config.yaml` already wires up the pack hooks.

#### CI/CD Validation

Validate language packs in GitHub Actions:

```yaml
name: Validate Language Packs

on:
  pull_request:
    paths:
      - "libs/i18n/language-packs/**/*.yml"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv run python -m legesher_i18n.scripts.audit_packs
```

This repository runs that audit in `.github/workflows/validate-packs.yml`.

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

The "how to add a new language" walkthrough lives in the module docstring of
`legesher_i18n/script_policy.py`, and the checklist it encodes is a golden test in
`tests/test_new_language_onboarding.py`.

### Project Structure

```text
libs/i18n/
├── legesher_i18n/
│   ├── __init__.py          # Public API
│   ├── cli.py               # CLI commands
│   ├── pack_loader.py       # Pack loading with inheritance
│   ├── schema_validator.py  # Validation logic
│   ├── script_policy.py     # Per-language Unicode/script policy
│   ├── term_definitions.py  # The canonical term inventory
│   ├── version_detector.py  # Python version detection
│   └── version_index.py     # Version index management
├── language-packs/
│   └── python/
│       └── {lang}/          # One independently versioned package per language
│           └── legesher_i18n_python_{lang}/packs/{3.10..3.14}.yml
├── scripts/
│   └── generate_compatibility_matrix.py
└── tests/
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) file

## Links

- [Legesher Monorepo](../../README.md)
- [Translation API](docs/translation-api.md)
- [Validation](docs/VALIDATION.md)
- [Quality gates](docs/quality-gates.md)
