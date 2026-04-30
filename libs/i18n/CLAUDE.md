# legesher-i18n - Claude Code Guide

This file provides guidance for working with the `legesher-i18n` package.

## Package Overview

**Version**: 0.4.0
**Status**: Production-Ready (Pre-Beta)
**Python**: >=3.10,<4.0

Internationalization infrastructure with 51 language packs, version-aware inheritance,
and multi-provider translation API.

## Key Capabilities

- **51 Language Packs**: All in experimental status (see `languages.json`)
- **Version-Aware Loading**: Automatic Python 3.10-3.14 adaptation
- **Pack Inheritance**: Child packs inherit from parents, reducing duplication
- **Translation API**: Multi-provider support (Anthropic, Google, DeepL, LibreTranslate)
- **Schema Validation**: Pydantic-based with security checks
- **CLI Tools**: validate, show, registry, export commands
- **Reserved Words** (CORE-710): `self`/`cls` translated deterministically
  per pack via the new `reserved_words:` YAML section. Distinct from
  `keywords:` because they're Python conventions (not actual reserved
  words in the language). Eliminates LLM-driven self-reference drift
  and keyword collisions (see `scripts/translate/prompts/reserved_words_prompt.md`).

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
│       ├── am/, ar/, bn/, bs/, ...  # 51 language packs
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

All 51 languages are currently **experimental**:

- Translations work but await community validation
- Status defined in `languages.json`
- Will transition to **accepted** after validation

## Translation Database

The consolidated SQLite database at `legesher_i18n/db/translations.db` is the single source of truth for all
translation data. Schema defined in `legesher_i18n/db/schema.py`.

**Features:** WAL mode, foreign keys with cascading deletes, thread-local connection pooling.

### Tables

#### `terms` — Canonical reserved words

Extensible across programming languages. Python's `def` and a future TypeScript `function` are separate rows.

| Column                 | Type          | Notes                                                                                                            |
| ---------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------- |
| `id`                   | INTEGER PK    | Auto-increment                                                                                                   |
| `name`                 | TEXT NOT NULL | e.g., `def`, `True`, `print`                                                                                     |
| `programming_language` | TEXT NOT NULL | e.g., `python`                                                                                                   |
| `category`             | TEXT NOT NULL | `keyword`, `builtin_func`, `builtin_type`, `special_constant`, `exception`, `reserved_word` (CORE-710: self/cls) |
| `subcategory`          | TEXT          | Keywords: `control_flow`, `iteration`, `structure`, etc. Exceptions: `base`, `arithmetic`, etc.                  |
| `version_added`        | TEXT          | Python version when term was introduced                                                                          |
| `description`          | TEXT          | Optional human-readable description                                                                              |

**Constraint:** `UNIQUE(name, programming_language)`

#### `languages` — Language registry

62 languages total: 51 with YAML packs, 11 legacy community languages.

| Column                                                    | Type          | Notes                               |
| --------------------------------------------------------- | ------------- | ----------------------------------- |
| `code`                                                    | TEXT PK       | ISO 639-1 (e.g., `es`, `ar`, `zh`)  |
| `name`                                                    | TEXT NOT NULL | English name                        |
| `native_name`                                             | TEXT NOT NULL | Native script name                  |
| `direction`                                               | TEXT          | `ltr` or `rtl`                      |
| `status`                                                  | TEXT          | `experimental` or `accepted`        |
| `has_yaml_pack`                                           | BOOLEAN       | Whether a YAML language pack exists |
| `iso639_2`, `bcp47`, `family`, `script`, `numeral_system` | TEXT          | Extended metadata                   |

#### `translations` — Complete catalog of translation suggestions

Every suggestion lives here — model-generated candidates AND active YAML pack values.

| Column            | Type          | Notes                                                      |
| ----------------- | ------------- | ---------------------------------------------------------- |
| `id`              | INTEGER PK    | Auto-increment                                             |
| `term_id`         | INTEGER FK    | References `terms(id)` ON DELETE CASCADE                   |
| `language_code`   | TEXT FK       | References `languages(code)` ON DELETE CASCADE             |
| `translation`     | TEXT NOT NULL | The translated text                                        |
| `source`          | TEXT NOT NULL | Origin: `aya`, `community`, `anthropic`, `yaml_pack`, etc. |
| `model_version`   | TEXT          | e.g., `aya-101`, `claude-3.5-sonnet`                       |
| `word_type`       | TEXT          | Grammatical word type                                      |
| `word_form`       | TEXT          | Word form variation                                        |
| `confidence`      | TEXT          | `high`, `medium`, `low`                                    |
| `model_rationale` | TEXT          | AI model reasoning                                         |
| `created_by`      | TEXT          | Creator identifier                                         |

**Constraint:** `UNIQUE(term_id, language_code, source, translation)` — prevents duplicate suggestions
from the same source. `INSERT OR IGNORE` in `add_translation()` silently skips duplicates.

#### `selected_translations` — Active translation per term+language

Tracks which translation is currently chosen for YAML packs. Decouples "what we chose" from "who suggested it."

| Column             | Type          | Notes                                          |
| ------------------ | ------------- | ---------------------------------------------- |
| `id`               | INTEGER PK    | Auto-increment                                 |
| `term_id`          | INTEGER FK    | References `terms(id)` ON DELETE CASCADE       |
| `language_code`    | TEXT FK       | References `languages(code)` ON DELETE CASCADE |
| `translation`      | TEXT NOT NULL | The chosen translation text                    |
| `selected_by`      | TEXT          | Who/what made the selection                    |
| `selection_reason` | TEXT          | Why this translation was chosen                |

**Constraint:** `UNIQUE(term_id, language_code)` — exactly one active translation per term+language.

### Source Values

| Source      | Meaning                                                              |
| ----------- | -------------------------------------------------------------------- |
| `yaml_pack` | Backfilled from current YAML language packs                          |
| `aya`       | Generated by the Aya AI model                                        |
| `community` | Human community contributions (legacy)                               |
| `claude`    | Generated by Claude for collision resolution or translation pipeline |
| `anthropic` | Generated by Anthropic Claude models (translation API provider)      |
| `unknown`   | Legacy rows where source was not recorded                            |

### Key API Methods (`TranslationDatabase`)

```python
from legesher_i18n.db.database import TranslationDatabase

db = TranslationDatabase()  # Uses default path, or pass db_path="..."

# Terms
db.get_or_create_term(name, programming_language, category, subcategory)
db.get_term_by_name(name, programming_language)
db.get_terms(programming_language, category)

# Translations (complete catalog)
db.add_translation(term_id, language_code, translation, source, ...)  # Returns 0 if duplicate
db.get_translations(term_id, language_code, source)
db.get_translations_joined(language_code, source)  # JOIN with terms for backward compat
db.get_translations_for_term(term_name, language_code)

# Selected translations (active choices)
db.set_selected(term_id, language_code, translation, selected_by, reason)
db.get_selected(term_id, language_code)
db.get_selected_by_name(term_name, language_code)
db.get_all_selected()
db.remove_selected(term_id, language_code)

# Utilities
db.get_stats()
db.close()
```

### Common Queries

```sql
-- All translations for a term across languages
SELECT l.name, t.translation, t.source, t.confidence
FROM translations t
JOIN terms tm ON t.term_id = tm.id
JOIN languages l ON t.language_code = l.code
WHERE tm.name = 'def' AND tm.programming_language = 'python';

-- Languages with most translation coverage
SELECT language_code, COUNT(DISTINCT term_id) as terms_covered
FROM translations
GROUP BY language_code
ORDER BY terms_covered DESC;

-- Compare suggestions vs selected for a language
SELECT tm.name, t.translation, t.source,
       CASE WHEN s.translation = t.translation THEN 'SELECTED' ELSE '' END as status
FROM translations t
JOIN terms tm ON t.term_id = tm.id
LEFT JOIN selected_translations s
  ON s.term_id = t.term_id AND s.language_code = t.language_code
WHERE t.language_code = 'es'
ORDER BY tm.name, t.source;
```

### Database Key Files

| File                                     | Purpose                                                         |
| ---------------------------------------- | --------------------------------------------------------------- |
| `legesher_i18n/db/schema.py`             | Table definitions and indexes                                   |
| `legesher_i18n/db/database.py`           | `TranslationDatabase` class with all CRUD methods               |
| `legesher_i18n/db/translations.db`       | The consolidated SQLite database                                |
| `scripts/translate/pipeline.py`          | Translation pipeline (stores suggestions via `add_translation`) |
| `scripts/translate/import_yaml_to_db.py` | Bulk YAML-to-DB import utility                                  |
| `scripts/translate/yaml_exporter.py`     | DB-to-YAML export (uses `get_translations_joined`)              |

### Collision Prevention (CORE-605)

A **collision** occurs when the same translated text is the selected translation for 2+ different Python terms
in the same language — this breaks round-trip translation (the reverse translator can't determine which English
keyword to map back to).

**Detection:**

```python
db = TranslationDatabase()
collisions = db.find_collisions()                          # All languages
collisions = db.find_collisions(language_code="fi")        # Single language
collisions = db.find_collisions(programming_language="python")  # Scoped by language (default)
```

Collisions are scoped by `programming_language` — Python's `def` and a future TypeScript `function` sharing
a translation are NOT collisions (different runtime contexts).

**Prevention:**

`set_selected()` includes a collision guard (default on). Attempting to select a translation that's already
active for another term in the same programming language raises `ValueError`:

```python
db.set_selected(term_id=1, language_code="fi", translation="ja")
db.set_selected(term_id=2, language_code="fi", translation="ja")  # ValueError!

# Escape hatch for migrations:
db.set_selected(term_id=2, language_code="fi", translation="ja", allow_collision=True)
```

**CLI:**

```bash
uv run legesher-i18n db collisions                    # Human-readable report
uv run legesher-i18n db collisions --language fi       # Filter by language
uv run legesher-i18n db collisions --json              # Machine-readable output
```

**Resolution patterns for new languages** — use these disambiguation strategies:

- `anext` vs `next`: prefix with async equivalent (e.g., Finnish `seuraava` → `seuraavaasync`)
- `global` vs `globals`: use plural/function form for `globals`
- `if` vs `elif`: compound "else+if" for `elif`
- `except` vs `exception`: class form suffix for `exception`
- `chr` vs `ord`: use distinct descriptive words (character vs ordinal)
- `import` vs `input`: more specific word for `input` (entry/data input)

### Database CLI Commands

```bash
uv run legesher-i18n db stats      # Show row counts and coverage
uv run legesher-i18n db init       # Initialize (or verify) database
uv run legesher-i18n db vacuum     # Compact the database file
uv run legesher-i18n db collisions # Check for translation collisions

# Direct SQLite access
sqlite3 legesher_i18n/db/translations.db ".tables"
sqlite3 legesher_i18n/db/translations.db ".schema translations"
```

## Source of Truth

- **Language metadata**: `legesher_i18n/languages.json`
- **Translation data**: `legesher_i18n/db/translations.db`
- **Pack versions**: Defined in each pack's `pyproject.toml` file (currently 0.0.1–0.0.3)
- **Python version keywords**: `language-packs/python/version-index.yml`
