# Legesher I18N Scripts

Automation scripts for maintaining Python language packs.

## Overview

These scripts automate the process of monitoring Python releases, extracting
localizable content, generating translations, and creating language packs.

## Scripts

### 1. `extract_python_content.py`

Extracts localizable content from Python (keywords, built-in functions, types,
docstrings).

**Usage:**

```bash
# Extract from current Python installation
python extract_python_content.py --output python-content-3.13.json --pretty

# Extract from specific version
python extract_python_content.py --version 3.14 --output python-content-3.14.json

# Fetch from GitHub (for uninstalled versions)
python extract_python_content.py --version 3.14 --method github --output python-content-3.14.json
```

**Output:** JSON file with 114 items (39 keywords + 49 builtins + 26 types)

### 2. `monitor_python.py`

Monitors GitHub CPython repository for new major Python releases.

**Usage:**

```bash
# Check for new releases
python monitor_python.py

# Verbose output
python monitor_python.py --verbose

# Specify version-index.yml location
python monitor_python.py --version-index ../programming_languages/python/version-index.yml
```

**Output:** Prints new version (e.g., "3.14") or empty string if none found

### 3. `translate_content.py`

Generates translations with 95%+ reuse of existing language packs.

**Usage:**

```bash
# Translate to Spanish
python translate_content.py \
  --version 3.14 \
  --input python-content-3.14.json \
  --target-language es \
  --output translations/python-3.14-es.json \
  --provider mock

# Use real translation API (DeepL)
export DEEPL_API_KEY=your_key_here
python translate_content.py \
  --version 3.14 \
  --input python-content-3.14.json \
  --target-language es \
  --output translations/python-3.14-es.json \
  --provider deepl
```

**Providers:**

- `mock`: Identity translations (for testing)
- `deepl`: DeepL API (requires `DEEPL_API_KEY`)
- `google`: Google Translate (requires `GOOGLE_API_KEY`)

### 4. `generate_language_pack.py`

Generates complete language packs with inheritance from previous versions.

**Usage:**

```bash
# Generate all packs (base + translations)
python generate_language_pack.py \
  --version 3.14 \
  --input python-content-3.14.json \
  --translations-dir ./translations \
  --languages-dir ../languages

# Generate only base English pack
python generate_language_pack.py \
  --version 3.14 \
  --input python-content-3.14.json \
  --languages-dir ../languages \
  --base-only

# Dry run (don't write files)
python generate_language_pack.py \
  --version 3.14 \
  --input python-content-3.14.json \
  --languages-dir ../languages \
  --dry-run
```

**Output:**

- `programming_languages/python/3.14/en.yml`
- `programming_languages/python/3.14/es.yml`
- `programming_languages/python/3.14/ar.yml`
- `programming_languages/python/3.14/zh.yml`
- Updated `version-index.yml`

### 5. `compare_translations.py`

Compares translations from multiple sources (Claude, GPT-4o, Aya 23, community) and generates detailed comparison
reports with metrics and recommendations.

**Usage:**

```bash
# Compare Spanish translations using mock data
uv run python scripts/compare_translations.py compare --language es --mock

# Compare specific term
uv run python scripts/compare_translations.py compare --language es --term def --mock

# Compare multiple languages
uv run python scripts/compare_translations.py compare -l es -l ar -l zh --mock

# Generate markdown report
uv run python scripts/compare_translations.py compare --language es --mock --output spanish_report.md

# Generate JSON output
uv run python scripts/compare_translations.py compare --language es --mock --format json --output results.json

# Cross-language comparison report
uv run python scripts/compare_translations.py compare -l es -l ar -l zh --mock --output cross_lang_report.md

# List available languages
uv run python scripts/compare_translations.py list-languages

# List available terms for a language
uv run python scripts/compare_translations.py list-terms --language es
```

**Features:**

- **Agreement Metrics**: Calculate agreement scores across translation sources
- **Conflict Detection**: Identify word type, form, length, and semantic conflicts
- **Rich Console Output**: Beautiful tables with color-coded agreement levels
- **Multiple Formats**: Generate markdown or JSON reports
- **Cost Tracking**: Monitor API costs with configurable warnings and limits
- **Mock Data Support**: Test with realistic mock translations without API costs
- **Cross-Language Reports**: Compare translation quality across multiple languages

**Options:**

- `--language` / `-l`: Language(s) to compare (es, ar, zh). Can specify multiple.
- `--term` / `-t`: Specific term to compare (optional)
- `--mock`: Use mock test data instead of real translations
- `--output` / `-o`: Output file path for report
- `--format` / `-f`: Report format (markdown or json)
- `--use-anthropic`: Use Anthropic API for semantic analysis (costs apply)
- `--cost-warning`: Cost warning threshold in USD (default: $50)
- `--cost-limit`: Cost limit threshold in USD (default: $100)

**Output:**

Single language markdown report includes:

- Summary statistics (agreement distribution, review needed)
- Source coverage
- Conflict analysis
- Top disagreements with detailed breakdowns
- Terms requiring human review

Cross-language report includes:

- Executive summary
- Language performance comparison
- Translation source analysis
- Top disagreements per language
- Recommendations

## Complete Workflow

### Manual Process

```bash
# 1. Check for new Python release
NEW_VERSION=$(python scripts/monitor_python.py)

if [ -n "$NEW_VERSION" ]; then
  echo "New Python $NEW_VERSION detected!"

  # 2. Extract content
  python scripts/extract_python_content.py \
    --version "$NEW_VERSION" \
    --output "/tmp/python-content-$NEW_VERSION.json" \
    --pretty

  # 3. Generate translations for each language
  for LANG in es ar zh; do
    python scripts/translate_content.py \
      --version "$NEW_VERSION" \
      --input "/tmp/python-content-$NEW_VERSION.json" \
      --target-language "$LANG" \
      --output "/tmp/translations/python-$NEW_VERSION-$LANG.json" \
      --provider mock
  done

  # 4. Generate language packs
  python scripts/generate_language_pack.py \
    --version "$NEW_VERSION" \
    --input "/tmp/python-content-$NEW_VERSION.json" \
    --translations-dir "/tmp/translations" \
    --languages-dir "languages"

  echo "✅ Language packs generated for Python $NEW_VERSION"
else
  echo "No new Python version detected"
fi
```

### Automated Process (GitHub Actions)

The workflow is automated via `.github/workflows/monitor-python-releases.yml`:

**Manual Trigger:**

1. Go to Actions tab in GitHub
2. Select "Monitor Python Releases"
3. Click "Run workflow"
4. Optionally specify Python version
5. Workflow creates PR automatically

**Automatic Mode (when enabled):**

- Runs weekly on Mondays at noon UTC
- Checks for new Python releases
- Creates PR automatically if new version found

## Requirements

```toml
dependencies = [
    "packaging>=23.0",
    "pydantic>=2.0",
    "pyyaml>=6.0",
]
```

Optional for translation APIs:

```bash
pip install deepl
pip install google-cloud-translate
```

## Testing

Each script includes a `--dry-run` mode for safe testing:

```bash
# Test extraction
python extract_python_content.py --version 3.14 --output /tmp/test.json

# Test translation (mock provider)
python translate_content.py \
  --version 3.14 \
  --input /tmp/test.json \
  --target-language es \
  --output /tmp/test-es.json \
  --provider mock

# Test pack generation (dry run)
python generate_language_pack.py \
  --version 3.14 \
  --input /tmp/test.json \
  --languages-dir ../languages \
  --dry-run
```

## Architecture

```text
monitor_python.py → Detects Python 3.14
      ↓
extract_python_content.py → Extracts 114 items
      ↓
translate_content.py → Translates new items (95%+ reuse)
      ↓
generate_language_pack.py → Creates YAML packs
      ↓
GitHub Actions → Creates PR for review
```

## Key Features

### Smart Translation Reuse

- **95%+ reuse rate**: Most keywords/builtins unchanged between versions
- **API cost savings**: Only translate 2-5 new items per version
- **Consistency**: Same translations across versions

### Inheritance Model

- **Extends previous version**: Avoids duplication
- **Automatic parent detection**: Finds latest previous version
- **Diff tracking**: Records what changed between versions

### Comprehensive Content

- **39 keywords**: All hard + soft keywords
- **49 built-in functions**: With docstrings for hover
- **26 built-in types**: Core types (exceptions deferred to Phase 2)
- **Total: 114 items** per language pack

## Maintenance

### Adding a New Language

1. Add language code to `generate_language_pack.py`
2. Add language name mapping
3. Run workflow or scripts manually

**Step 1** - Add language code to `generate_language_pack.py`:

```python
self.supported_languages = ["es", "ar", "zh", "fr"]  # Add "fr"
```

**Step 2** - Add language name mapping:

```python
language_names = {
    "es": "Spanish",
    "ar": "Arabic",
    "zh": "Chinese",
    "fr": "French",  # Add this
}
```

**Step 3** - Run workflow or scripts manually

### Updating Translation Provider

Edit `translate_content.py` to add new provider:

```python
class MyTranslationProvider:
    def translate(self, text: str, target_lang: str) -> str:
        # Your implementation
        return translated_text
```

## Troubleshooting

### GitHub API Rate Limit

```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

### Translation API Errors

```bash
# Test with mock provider first
python translate_content.py --provider mock ...

# Check API key
echo $DEEPL_API_KEY
```

### Pack Generation Fails

```bash
# Verify version-index.yml exists
ls programming_languages/python/version-index.yml

# Check parent version
cat programming_languages/python/version-index.yml
```

## Reference

- **CORE-381**: Auto-Update GitHub Actions Workflow
- **CORE-346**: Version-Aware Language Packs
- **Research**: `documentation/research/python-localization-inventory.md` (in private-working-memory)

## License

MIT License - See root LICENSE file
