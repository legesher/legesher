# Translation Comparison System - Quick Reference

One-page reference for the Legesher translation comparison system.

## Installation

```bash
cd libs/i18n && uv install
```

## CLI Commands

### Compare Translations

```bash
# Basic comparison
legesher-i18n compare <language>

# Multi-provider comparison
legesher-i18n compare es --providers claude,gpt4,aya23

# With report generation
legesher-i18n compare es --report --output report.md

# Include community translations
legesher-i18n compare es --include-community

# Set confidence threshold
legesher-i18n compare es --confidence 0.8
```

### Generate Reports

```bash
# Markdown report
legesher-i18n report es --output report.md

# HTML report
legesher-i18n report es --format html --output report.html

# JSON data export
legesher-i18n report es --format json --output data.json

# Show only conflicts
legesher-i18n report es --section conflicts
```

### View Metrics

```bash
# Display metrics
legesher-i18n metrics es

# Export to CSV
legesher-i18n metrics es --format csv --output metrics.csv

# Compare providers
legesher-i18n metrics es --compare-providers

# Historical trends
legesher-i18n metrics es --historical --days 30
```

### Multi-Language

```bash
# Compare multiple languages
legesher-i18n compare-multi es,ar,zh

# Generate summary report
legesher-i18n compare-multi es,ar,zh --summary --output summary.md
```

## Python API

### Basic Usage

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.api.providers import AnthropicProvider
from legesher_i18n.comparison.metrics import MetricsCalculator

# Setup
claude = AnthropicProvider(api_key="sk-ant-...")
comparator = TranslationComparator(
    providers=[claude],
    language="es",
    python_version="3.13"
)

# Compare
results = comparator.compare()

# Calculate metrics
calculator = MetricsCalculator()
metrics = calculator.calculate_all(results)

print(f"Agreement: {metrics.agreement_score:.2%}")
print(f"Conflicts: {len(metrics.conflicts)}")
```

### Multi-Provider Comparison

```python
from legesher_i18n.api.providers import (
    AnthropicProvider,
    OpenAIProvider,
    CohereProvider
)

providers = [
    AnthropicProvider(api_key="..."),
    OpenAIProvider(api_key="..."),
    CohereProvider(api_key="...")
]

comparator = TranslationComparator(providers=providers, language="es")
results = comparator.compare()
```

### Generate Reports

```python
from legesher_i18n.reports import ReportGenerator

generator = ReportGenerator()

# Markdown report
md = generator.generate_markdown(results)
with open("report.md", "w") as f:
    f.write(md)

# HTML report
html = generator.generate_html(results)

# JSON data
json_data = generator.generate_json(results)
```

### Detect Conflicts

```python
from legesher_i18n.comparison.metrics import MetricsCalculator

calculator = MetricsCalculator()
conflicts = calculator.detect_conflicts(results, threshold=0.75)

# Filter by severity
high = [c for c in conflicts if c.severity == "high"]
medium = [c for c in conflicts if c.severity == "medium"]

for conflict in high:
    print(f"{conflict.keyword}: {conflict.recommendation}")
```

### Database Integration

```python
from legesher_i18n.db import TranslationDatabase

db = TranslationDatabase("translations.db")

# Store results
db.store_comparison(results)

# Query history
history = db.get_comparison_history(language="es", days=30)

# Provider performance
performance = db.get_provider_performance("claude", days=90)
```

## Configuration

### ComparisonConfig

```python
from legesher_i18n.comparison.models import ComparisonConfig

config = ComparisonConfig(
    language="es",                       # Target language
    python_version="3.13",               # Python version
    include_cultural_analysis=True,      # Cultural insights
    confidence_threshold=0.75            # Consensus threshold (0-1)
)
```

### AnthropicProvider

```python
from legesher_i18n.api.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="sk-ant-...",               # API key
    model="claude-sonnet-4.5",          # Model name
    temperature=0.3                      # Sampling temperature (0-1)
)

translations = provider.translate_keywords(
    keywords=["if", "else", "while"],
    target_language="es",
    python_version="3.13"
)
```

## Metrics Interpretation

### Agreement Score

```text
Score = (Matching Translations) / (Total Translations)
```

- **1.0 (100%)**: Perfect agreement
- **0.9-0.99**: High agreement, minor variations
- **0.75-0.89**: Good agreement, some differences
- **0.6-0.74**: Medium conflict, review recommended
- **<0.6**: High conflict, discussion required

### Consensus Rate

```text
Rate = (Keywords with ≥90% Agreement) / (Total Keywords)
```

Target: **80%+** for production-ready language pack

### Conflict Levels

- **None** (100%): No disagreement
- **Low** (75-89%): Accept consensus
- **Medium** (60-74%): Community validation recommended
- **High** (<60%): Extended discussion required

## Workflows

### Validate New Language Pack

```bash
# 1. Run comparison
legesher-i18n compare fr --providers all

# 2. Review consensus
legesher-i18n report fr --section consensus

# 3. Identify conflicts
legesher-i18n report fr --section conflicts --threshold high

# 4. Generate full report
legesher-i18n report fr --output french_validation.md
```

### Update Existing Pack

```bash
# 1. Compare with community
legesher-i18n compare es --include-community

# 2. Find discrepancies
legesher-i18n diff es

# 3. Generate change report
legesher-i18n report es --output updates.md
```

### Quality Check

```bash
# 1. Multi-language comparison
legesher-i18n compare-multi es,ar,zh,fr,de

# 2. Summary report
legesher-i18n report-multi --output summary.md

# 3. Export metrics
legesher-i18n metrics --format csv --output metrics.csv
```

## Common Patterns

### Accept Consensus Translations

```python
# Filter high-agreement translations
consensus = [
    kw for kw in results.keywords
    if kw.agreement_score >= 0.9
]

# Create language pack
pack = {kw.keyword: kw.consensus for kw in consensus}
```

### Flag Conflicts for Review

```python
# Identify conflicts
conflicts = calculator.detect_conflicts(results)

# Group by severity
flagged = {
    "high": [c for c in conflicts if c.severity == "high"],
    "medium": [c for c in conflicts if c.severity == "medium"],
    "low": [c for c in conflicts if c.severity == "low"]
}

# Create review list
for keyword in flagged["high"]:
    print(f"TODO: Review {keyword.keyword}")
```

### Track Provider Performance

```python
# Calculate provider metrics
for provider in results.providers:
    score = calculator.calculate_agreement(
        provider,
        "community",
        results.translations
    )
    print(f"{provider}: {score:.2%}")
```

## File Locations

### Documentation

- Main docs: `TRANSLATION_COMPARISON.md`
- Quick start: `README.md` (comparison section)
- Examples: `examples/`
- This reference: `COMPARISON_QUICKREF.md`

### Implementation

- Comparison: `legesher_i18n/comparison/`
- Providers: `legesher_i18n/api/providers/`
- Reports: `legesher_i18n/reports/`
- Database: `legesher_i18n/db/`

### Examples

- Spanish report: `examples/spanish_comparison_report.md`
- Multi-language: `examples/multi_language_summary.md`
- Examples guide: `examples/README.md`

## Environment Variables

```bash
# API Keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export COHERE_API_KEY="..."

# Database
export TRANSLATION_DB_PATH="translations.db"

# Configuration
export DEFAULT_CONFIDENCE_THRESHOLD="0.75"
export DEFAULT_PYTHON_VERSION="3.13"
```

## Troubleshooting

### Low Agreement Scores

```python
# Check configuration
print(config.python_version)  # Verify correct version
print(config.language)         # Verify correct language code

# Review provider responses
for kw in results.keywords:
    print(f"{kw.keyword}: {kw.translations}")
```

### API Rate Limiting

```python
# Use batch processing
provider.batch_translate(keywords, batch_size=5)

# Add delays
import time
for batch in batches:
    provider.translate(batch)
    time.sleep(1)
```

### Cultural Conflicts

```python
# Include cultural analysis
config.include_cultural_analysis = True

# Review with native speakers
for conflict in high_conflicts:
    print(f"Review needed: {conflict.keyword}")
    print(f"Options: {conflict.translations}")
    print(f"Cultural note: {conflict.cultural_note}")
```

## Best Practices

1. **Use multiple providers** for validation
2. **Set appropriate thresholds** (0.75 for balanced, 0.85 for strict)
3. **Include cultural analysis** for new languages
4. **Generate reports** for stakeholder review
5. **Store results** in database for tracking

## Resources

- Detailed docs: `TRANSLATION_COMPARISON.md`
- Example reports: `examples/`
- Translation API: `docs/translation-api.md`
- Database schema: `docs/database-schema.md`
- Issues: <https://github.com/legesher/legesher/issues>

---

**Quick Ref Version**: 1.0
**Last Updated**: 2025-11-11
**Full Documentation**: See `TRANSLATION_COMPARISON.md`
