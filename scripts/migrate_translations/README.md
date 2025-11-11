# Translation Migration Scripts

This directory contains scripts for extracting and migrating community translation data from the legacy `legesher/legesher-translations` repository into the Legesher monorepo.

## Overview

The legacy repository used a **branch-per-language** approach with YAML files containing translations and community review comments. These scripts extract that data and migrate it into the SQLite database used by the new i18n system.

## Scripts

### 1. `reconnaissance.py`

Analyzes the legacy repository structure to identify translation branches and count available data.

**Usage:**

```bash
uv run python reconnaissance.py
```

### 2. `extract_python_translations.py`

Extracts Python keywords and builtins from the legacy YAML files, preserving community review comments with emoji votes and @mentions.

**Features:**

- Filters out Crowdin duplicate branches (`l10n_*`)
- Excludes `i18n-dialect-translation` branch
- Preserves community review comments
- Extracts emoji votes (✅, 🤔, ❓, ❌)
- Captures @mentions of reviewers
- Identifies alternative translation suggestions

**Usage:**

```bash
uv run python extract_python_translations.py
```

**Output:** JSON files in `migration_data/extracted_translations/` (one per language)

### 3. `populate_from_json.py` ⭐

**One-time migration script** that imports extracted translations and reviews into the SQLite database.

**Usage:**

```bash
cd scripts/migrate_translations
PYTHONPATH=../../libs/i18n uv run python populate_from_json.py
```

**What it does:**

- Reads all JSON files from `migration_data/extracted_translations/`
- Inserts translations into the `translations` table with `source="community"`
- Inserts reviews into the `reviews` table with:
  - Emoji votes mapped to vote types (approved/suggest_revision/rejected)
  - @mentions extracted to `reviewer_github` field
  - Alternative suggestions stored as JSON
  - Review source set to `"legacy_repo"`

**Output:**

```
Languages migrated:    24
Translations inserted: 2169
Reviews inserted:      611
Errors encountered:    0
```

### 4. `validate_migration.py`

Validates that all data was successfully migrated by comparing JSON counts to database counts.

**Usage:**

```bash
cd scripts/migrate_translations
PYTHONPATH=../../libs/i18n uv run python validate_migration.py
```

**Output:** Generates `migration_data/migration_report.md` with detailed validation results.

### 5. `convert_to_yaml_language_packs.py`

Converts extracted translations into the new YAML language pack format.

**Usage:**

```bash
uv run python convert_to_yaml_language_packs.py
```

## Migration History (CORE-395)

### One-Time Migration Completed

**Date:** 2025-11-11
**Task:** [CORE-395] Parse and Migrate Community Translation Data

**Results:**

- ✅ All 24 languages migrated successfully
- ✅ 2,169 translations imported
- ✅ 611 community reviews preserved
- ✅ Zero data loss confirmed
- ✅ All validations passed

**Languages Migrated:**
Arabic (ar), Bengali (bn), Welsh (cy), Greek (el), Spanish (es), Finnish (fi), French (fr), Gaelic (ga), Gujarati (gu), Hebrew (he), Hindi (hi), Indonesian (id), Malayalam (ml), Nepali (ne), Dutch (nl), Polish (pl), Portuguese (pt), Russian (ru), Swahili (sw), Telugu (te), Tagalog (tl), Ukrainian (uk), Urdu (ur), Xhosa (xh)

**Community Engagement Highlights:**

- **Arabic (ar):** 101 reviews - extensive community discussion
- **French (fr):** 104 reviews - complete review coverage
- **Indonesian (id):** 104 reviews - complete review coverage
- **Polish (pl):** 104 reviews - complete review coverage
- **Russian (ru):** 104 reviews - complete review coverage

**Branch Filtering:**
The extraction script now filters out Crowdin duplicate branches:

- ✅ Excludes branches with `l10n_` prefix (Crowdin auto-generated)
- ✅ Excludes `i18n-dialect-translation` branch
- ✅ Uses only original community branches (e.g., `arabic-translation`, `spanish-translation`)

### Database Location

The migrated data is stored in:

```
libs/i18n/legesher_i18n/db/translations.db
```

### Validation Report

Full validation report available at:

```
scripts/migrate_translations/migration_data/migration_report.md
```

## Future Work

The `legesher-translations` repository will be merged into this monorepo in another form. These migration scripts served their purpose for the one-time data migration and can be deleted or archived after this PR merges.

## Notes

- **Migration scripts are temporary** - They were created for a one-time migration and don't need long-term maintenance
- **Source data preserved** - Original JSON files remain in `migration_data/extracted_translations/` for reference
- **Review metadata preserved** - All emoji votes, @mentions, and alternative suggestions were successfully captured
- **Mixed branch sources** - Some extracted data came from `l10n_*` branches before filtering was implemented, but data is identical to original branches

## Questions?

For questions about the migration or data structure, see:

- Database schema: `libs/i18n/docs/database-schema.md`
- Linear issue: [CORE-395](https://linear.app/legesher/issue/CORE-395)
