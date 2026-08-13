# AI Translation Pipeline (CORE-394)

Automated pipeline to generate translations for Python terms using multiple AI models.

## Overview

This pipeline generates translations for 105 Python terms across 24 languages using two AI models:

1. **Claude 3.5 Sonnet** (Anthropic API) - Premium quality, cloud-based
2. **Aya 23** (Ollama local) - Multilingual specialist, runs locally

**Total Output**: 5,040 translations (105 terms × 24 languages × 2 models)

## Features

- ✅ **Dual Model Support**: Claude (cloud) + Aya (local)
- ✅ **Deep Context Integration**: Uses CORE-393 context documents
- ✅ **Linguistic Standards**: Follows language-specific translation guidelines
- ✅ **Cost Monitoring**: Tracks API costs in real-time with budget limits
- ✅ **Progress Tracking**: Rich progress bars and detailed logging
- ✅ **Dry Run Mode**: Test without making real API calls
- ✅ **Parallel Execution**: Async processing for efficiency
- ✅ **Database Integration**: Stores results in SQLite (CORE-399 schema)
- ✅ **YAML Export**: Automatically generates language pack YAML files
- ✅ **Retry Logic**: Exponential backoff for API failures and rate limits

## Prerequisites

### 1. Anthropic API Key (for Claude)

```bash
# Get your API key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY="your_key_here"
```

### 2. Ollama + Aya 23 (for local translations)

```bash
# Install Ollama
# macOS:
brew install ollama

# Linux:
curl https://ollama.ai/install.sh | sh

# Pull Aya 23 model (~10GB)
ollama pull aya:latest
```

### 3. Python Dependencies

```bash
cd libs/i18n
uv sync
```

## Quick Start

### Test with Dry Run (No API Calls)

```bash
cd libs/i18n
python scripts/translate/run_pipeline.py --dry-run \
  --terms def return print \
  --languages es ar fr
```

**Output**:

```text
Starting Translation Pipeline
Models: claude, aya
Languages: 3
Terms to translate: 3

Total translations to generate: 18

Translating... ████████████████████ 100% 0:00:05

Pipeline Complete!
Total translations: 18
  ✓ Successful: 18
  ✗ Failed: 0

Total cost: $0.00
  claude: $0.00
  aya: $0.00

Duration: 5.2s
```

### Run with Real API (Claude Only)

```bash
python scripts/translate/run_pipeline.py \
  --models claude \
  --terms def return print if for while \
  --languages es ar \
  --max-budget 1.00
```

**Estimated Cost**: ~$0.12 for 12 translations (6 terms × 2 languages × 1 model)

### Full Pipeline

**All Terms, All Languages**

**⚠️ WARNING**: This will generate 5,040 translations and cost ~$53 on Claude API.

```bash
python scripts/translate/run_pipeline.py \
  --models claude aya \
  --max-budget 100.00
```

## CLI Usage

```bash
python scripts/translate/run_pipeline.py [OPTIONS]

Options:
  --models MODEL [MODEL ...]     AI models to use: claude, aya
                                  (default: both)

  --languages CODE [CODE ...]    Target language codes (es, ar, fr, ...)
                                  (default: all 24 languages)

  --terms TERM [TERM ...]        Specific terms to translate
                                  (default: all 105 terms from manifest)

  --dry-run                       Test mode - no real API calls
                                  (default: false)

  --max-budget AMOUNT             Maximum budget in USD (safety limit)
                                  (default: 100.00)

  --context-dir PATH              Directory with context documents
                                  (default: libs/i18n/context/python/)

  --output-db PATH                Output database path
                                  (default: .legesher/translations.db)

  --verbose, -v                   Enable debug logging

  --help, -h                      Show this help message
```

## Architecture

### Components

```text
scripts/translate/
├── models/
│   ├── base.py              # Base interfaces and data models
│   ├── claude_model.py      # Claude 3.5 Sonnet implementation
│   └── aya_model.py         # Aya 23 via Ollama implementation
├── context_loader.py        # Load CORE-393 deep contexts
├── pipeline.py              # Main orchestrator
├── run_pipeline.py          # CLI entry point
└── README.md                # This file
```

### Data Flow

```text
1. Load Context Documents (CORE-393)
   └─> Deep context with etymology, explanations, guidance

2. Load Linguistic Standards
   └─> Language-specific translation conventions

3. For each (term, language, model):
   ├─> Build prompt with context + standards
   ├─> Call AI model (Claude or Aya)
   ├─> Parse JSON response
   ├─> Track cost and progress
   └─> Store in database (CORE-399)

4. Export Results
   └─> YAML format for language packs
```

### Translation Request Structure

```python
TranslationRequest:
  - term: "def"
  - target_language: "es"
  - context: "Deep context document content..."
  - linguistic_standards: "Spanish translation guidelines..."

↓

AI Model (Claude or Aya)

↓

Translation:
  - translation: "definir"
  - alternatives: ["función", "def"]
  - rationale: "Infinitive form is standard for action keywords"
  - word_type: "verb"
  - form: "infinitive"
  - confidence: 0.95
  - cost: $0.004
  - model_name: "claude-3.5-sonnet"
```

## Cost Estimation

### Claude 3.5 Sonnet Pricing

- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

**Per Translation**:

- ~150 input tokens (prompt + context)
- ~50 output tokens (JSON response)
- **Cost**: ~$0.0045 per translation

### Aya 23 Pricing

- **Free** (runs locally via Ollama)
- Requires: ~8GB RAM, ~10GB disk space

### Total Costs (Estimated)

| Scope                           | Translations | Claude Cost | Aya Cost  | Total      |
| ------------------------------- | ------------ | ----------- | --------- | ---------- |
| Test (3 terms × 3 langs)        | 18           | $0.08       | $0.00     | $0.08      |
| Small (10 terms × 5 langs)      | 100          | $0.45       | $0.00     | $0.45      |
| Medium (50 terms × 12 langs)    | 1,200        | $5.40       | $0.00     | $5.40      |
| **Full (105 terms × 24 langs)** | **5,040**    | **$22.68**  | **$0.00** | **$22.68** |

**Note**: Actual costs may vary based on context length and response size.

## Safety Features

### Budget Limits

The pipeline enforces strict budget limits to prevent unexpected costs:

```python
# Default safety limit: $100
python run_pipeline.py --max-budget 100.00
```

Pipeline will stop immediately if cost exceeds limit.

### Dry Run Mode

Test the pipeline without making real API calls:

```python
python run_pipeline.py --dry-run
```

- Returns mock translations
- $0.00 cost
- Tests all logic except actual API calls

### Progress Monitoring

Real-time progress bar shows:

- Current translation being processed
- Percentage complete
- Estimated time remaining
- Running cost total

## Testing

### Run Tests

```bash
cd libs/i18n
uv run pytest tests/translate/ -v
```

### Test Coverage

```bash
uv run pytest tests/translate/ --cov=scripts.translate
```

**Coverage Target**: 80%+

### Unit Tests

- ✅ Model initialization
- ✅ Cost estimation
- ✅ Dry-run translations
- ✅ JSON parsing (with markdown code blocks)
- ✅ Request/response data models

## Troubleshooting

### Error: "ANTHROPIC_API_KEY environment variable must be set"

```bash
# Set API key
export ANTHROPIC_API_KEY="your_key_here"

# Or add to .env file
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

### Error: "Could not connect to Ollama"

```bash
# Check Ollama is running
ollama list

# Start Ollama service
ollama serve

# Pull Aya model
ollama pull aya:latest
```

### Error: "No context document found for term 'X'"

Context documents from CORE-393 are required. Check:

```bash
# Verify context documents exist
ls libs/i18n/context/python/

# Should contain: def.md, return.md, print.md, etc.
```

### Error: "Budget limit reached"

Increase budget limit or reduce scope:

```bash
# Increase limit
python run_pipeline.py --max-budget 200.00

# Or reduce scope
python run_pipeline.py --languages es ar fr  # Only 3 languages
```

## Integration with Other Issues

### CORE-393: Deep Context Documents

This pipeline requires deep context documents for each Python term:

- Location: `libs/i18n/context/python/*.md`
- Provides: Etymology, explanations, translation guidance
- Status: Must be completed before running full pipeline

### CORE-399: Translation Database

Results are stored in SQLite database:

- Schema: `translations`, `reviews`, `deep_contexts`, `linguistic_standards`
- Location: `.legesher/translations.db`
- Used by: Translation comparison (CORE-396), language pack generation

### CORE-396: Translation Comparison

Generated translations will be compared with community translations to assess quality and identify best approaches per language.

## Development

### Adding a New Model

1. Create `models/new_model.py`:

```python
from .base import TranslationModel, Translation, TranslationRequest

class NewModel(TranslationModel):
    async def translate(self, request: TranslationRequest) -> Translation:
        # Implement translation logic
        pass

    def get_model_name(self) -> str:
        return "new-model-name"

    def estimate_cost(self, request: TranslationRequest) -> float:
        return 0.0
```

1. Register in `pipeline.py`:

```python
if 'newmodel' in config.models:
    self.models['newmodel'] = NewModel(dry_run=config.dry_run)
```

1. Add tests in `tests/translate/test_models.py`

### Project Structure

```text
libs/i18n/
├── scripts/translate/          # Pipeline code
│   ├── models/                 # AI model implementations
│   ├── context_loader.py       # Context and standards loaders
│   ├── pipeline.py             # Main orchestrator
│   ├── run_pipeline.py         # CLI script
│   └── README.md               # This file
├── context/python/             # Deep context documents (CORE-393)
├── docs/                       # Documentation
│   └── linguistic-standards.md # Translation guidelines
├── data/                       # Data files
│   └── python-terms-manifest.json  # Term list and metadata
└── tests/translate/            # Unit tests
    └── test_models.py
```

## Recent Improvements

Implemented in this version:

- ✅ **Database Storage** (CORE-399): All translations stored in SQLite with full metadata
- ✅ **YAML Export**: Automatic generation of language pack YAML files after pipeline run
- ✅ **Retry Logic**: Exponential backoff for API failures (3 retries, 1s → 2s → 4s delays)
- ✅ **Fixed datetime deprecation**: Updated to use `datetime.now(timezone.utc)` instead of `datetime.utcnow()`

## Future Enhancements

Planned for future phases:

- [ ] Comparison reports (CORE-396)
- [ ] Resume capability (checkpoint/restart)
- [ ] Batch processing optimization
- [ ] GPT-4o model support
- [ ] Custom prompt templates
- [ ] Translation quality scoring
- [ ] Parallel rate limiting improvements

## Support

- **Issue**: CORE-394
- **Documentation**: [Legesher Docs](https://docs.legesher.io)
- **Repository**: [github.com/legesher/legesher](https://github.com/legesher/legesher)

## License

Apache License 2.0 - See [LICENSE](../../../../LICENSE) for details.
