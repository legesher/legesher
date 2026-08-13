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

# Community intake (CORE-1688/1828) — see docs/intake-moderation-runbook.md.
# Needs $LEGESHER_CONTRIBUTOR_SALT: these mint contributor ids, and the
# importer refuses the public dev salt or one that disagrees with build_meta.
legesher-i18n import-issue <issue-url> --db build/translations_v2.db
legesher-i18n import-review-bundle <file> --db build/translations_v2.db
legesher-i18n quarantine-queue --db build/translations_v2.db
legesher-i18n clear-option <opt_uid> --verdict cleared --by <you> --note "..."
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

- **Change the DB first, not the YAML** (CORE-1400): update the canonical value via `set_selected`, then
  regenerate. Packs are rewritten authoritatively from `selected_translations`, so a YAML-only edit is
  reverted by the next regen and flagged as a blocking `value_changed` by `scripts/verify_pack_regen.py`.
- **New Python version terms**: land in that version's YAML file (the exporter places them by
  `version_added`)
- **A replacement value also needs a candidate row**: `set_selected` alone leaves the selection
  orphaned from the `translations` pool, which `scripts/migrate_to_v2.py` hard-fails on
  (selected ⊆ candidates). Record the new surface via `add_translation` with provenance too.
- **Regenerate downstream artifacts** after a regen: `scripts/generate_reference_docs.py` and
  `scripts/update_pack_readme_counts.py` (repo root), and the docs-site payloads via
  `cd docs && python3 scripts/generate_snippets.py --snippets snippets --out generated` —
  the playground highlights and snippets are built from the shipped packs.
- Run `legesher-i18n validate` and `scripts/verify_pack_regen.py` to check

### Changing Pack Values in Bulk (standing constraints)

These are hard rules for any automated or agent-run change to translated pack values.
They were written after commit `5494504` (2025-12-09) rewrote 476 values across 26
languages by deleting spaces and punctuation — the origin of the concatenation damage
tracked in CORE-1515. Retro: CORE-1713.

**Rule 1 — a data-value change ships alone.**
`5494504` touched 209 files (+4,553 / −5,870) and bundled a doc move to another repo,
a build script, 469 lines of new tests, a new prompt file, *and* a 476-value semantic
rewrite of 26 language packs. The data change was invisible in that diff and nobody
caught it in review. Any change to pack values ships in its own PR, with a per-language
before/after table in the body, and nothing else on the branch.

**Rule 2 — a change to a language's values needs a reader of that language on it.**
The damage commit's own message offered `"error de E/S" → "errordees"` as an example of
success: Spanish for "I/O error" turned into nonsense, printed in the commit body, and
approved by people who don't read Spanish. Mechanical validity is not correctness.

**Rule 3 — "we preserve the original" must be durable and tested, or it is not a
safety net.** The originals were written *inside* the quoted YAML value (packs briefly
shipped `abs: 'valorabsoluto  #valor absoluto'` as a literal identifier), unquoted into
real comments a month later by `fc6d01e`, then silently deleted 14 days after that by
`89f5c8c`. The net lasted six weeks and its disappearance went unnoticed. The only
reason 55 Arabic values are recoverable today is that the `translations` table kept
them by accident of design, not by that plan. If a migration claims to preserve
originals, a test asserts the originals are still retrievable.

**Rule 4 — a validation error states a constraint; it never implies the remedy.**
"Identifiers can't contain spaces" was auto-remediated as "delete the spaces," because
nobody had specified what a multi-word concept *should* look like. Never auto-remediate
a constraint before the remedy is specified. The joiner is declared per language in
`style-guides/<lang>.yml` — in `naming.detail` (prose) today, and in an enumerated,
machine-checkable `naming.word_joiner` once CORE-1602 lands. That declaration is the
only authority, and it is **not** derivable from the script.

**Rule 5 — re-derive the convention before a generation pipeline scales.**
CORE-675 took 29 → 51 languages in March 2026 *after* concatenation had hardened into
house style, so new packs were generated to match a corrupted convention. Before the
next expansion batch runs, confirm the convention it will inherit is the one you want.

> **No "fixer" scripts.** Two orphaned scripts that rewrote pack values in place
> (`scripts/validate/fix_all_validation_issues.py`, `scripts/translate/fix_validation_issues.py`)
> were deleted in CORE-1713. They implemented *contradictory* conventions — one deleted
> spaces, the other replaced them with underscores — and both ran, which is the
> mechanical origin of the mixed convention in the packs today (ar 3 underscore / 67
> bare; he 18/52). Diagnostics may report; they may not write.

### Language Status

All 51 languages are currently **experimental**:

- Translations work but await community validation
- Status defined in `languages.json`
- Will transition to **accepted** after validation

## Translation Database

The consolidated SQLite database at `legesher_i18n/db/translations.db` is the single source of truth for all
translation data. Schema defined in `legesher_i18n/db/schema.py`.

**Features:** WAL mode, foreign keys with cascading deletes, thread-local connection pooling.

### Durable home & sync ritual (CORE-1794)

The database is **untracked** — it never ships in git or in built wheels (the
binary carries unredacted `created_by` reviewer labels the corpus design never
exports). The file on disk here is a **working copy**; the canonical copy lives
in a private data repository, alongside the private contributor identity map
that `scripts/migrate_to_v2.py` loads at import.

- **Every clone sets `LEGESHER_DATA_REPO`** to the path of the data-repository
  checkout (the monorepo never names that repository; ask a maintainer for
  access). A fresh monorepo clone has **no database** until you copy it in:
  `cp "$LEGESHER_DATA_REPO/db/translations.db" legesher_i18n/db/`
- **Every mutating ritual ends with a push to the durable home.** After any
  regen, migration, review import, or term-screening write:

  ```bash
  sqlite3 legesher_i18n/db/translations.db "PRAGMA wal_checkpoint(TRUNCATE);"
  cp legesher_i18n/db/translations.db "$LEGESHER_DATA_REPO/db/translations.db"
  git -C "$LEGESHER_DATA_REPO" commit -am "db: <ritual> [CORE-###]" && \
      git -C "$LEGESHER_DATA_REPO" push
  ```

  An unpushed change exists only on one workstation — local-only is the failure
  mode the durable home exists to prevent.

  `--sync` on an intake import performs this whole sequence, and additionally
  archives the accepted raw payload under `intake/<YYYY-MM>/` in the data home.
  Those payloads are the rebuild source for the intake layer: `migrate_to_v2.py`
  rebuilds from scratch and knows nothing about review sessions, so re-running
  the importer over them is what re-derives it. Screening verdicts are the one
  thing a from-scratch rebuild does not recover — they live in
  `option_screenings` inside the database, so carry the previous copy forward.

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

**Constraint:** `UNIQUE(name, programming_language, category)` — relaxed from `(name, programming_language)`
under CORE-1400 so one surface token can hold two slots (`type` is both the 3.10 builtin and the 3.12 soft
keyword, two term rows).

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

**Invariant (CORE-1400):** every selected value passes the publish gate — a valid Python identifier
(a `*`-suffixed term such as `except*` requires the mirrored trailing `*`, CORE-1839)
— enforced by `set_selected` and by the canonical selection
rule in `legesher_i18n/selection.py`. The candidate pool (`translations`) may be dirty; selections may
not. See [docs/translation-selection.md](docs/translation-selection.md).

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
#   Category-aware since CORE-1400: an explicit category selects among same-name rows.
#   RAISES ValueError on an ambiguous name (e.g. "type") when no category resolves it;
#   allow_duplicate_name=True deliberately adds a new (name, category) slot.
db.get_term_by_name(name, programming_language, category=None)   # no category → lowest-id row
db.get_terms(programming_language, category)

# Translations (complete catalog)
db.add_translation(term_id, language_code, translation, source, ...)  # Returns 0 if duplicate
db.get_translations(term_id, language_code, source)
db.get_translations_joined(language_code, source)  # JOIN with terms for backward compat
db.get_translations_for_term(term_name, language_code, category=None)  # category picks the slot for dual-slot names

# Selected translations (active choices)
db.set_selected(term_id, language_code, translation, selected_by, reason)
#   Enforces the CORE-1400 publish gate (valid identifier; a `*`-suffixed term needs the
#   mirrored `*`) and the
#   collision guard at the write boundary — both raise ValueError.
db.get_selected(term_id, language_code)
db.get_selected_by_name(term_name, language_code, category=None)
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
| `legesher_i18n/db/translations.db`       | The database — untracked working copy (see Durable home ritual) |
| `scripts/translate/pipeline.py`          | Translation pipeline (stores suggestions via `add_translation`) |
| `scripts/translate/import_yaml_to_db.py` | Bulk YAML-to-DB import utility                                  |
| `scripts/translate/yaml_exporter.py`     | DB-to-YAML export (reads ONLY `get_all_selected` — CORE-1400)   |

### Collision Prevention (CORE-605)

A **collision** occurs when the same translated text is the selected translation for 2+ different Python term
**names** in the same language — this breaks round-trip translation (the reverse translator can't determine
which English keyword to map back to). Same-name terms are exempt (CORE-1400): `type`'s builtin and soft-keyword
slots sharing one translation round-trips to the same token and is not an ambiguity.

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
active for a different term **name** in the same programming language raises `ValueError`:

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
