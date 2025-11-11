# Translation Comparison System

The i18n package includes a comprehensive system for comparing AI-generated translations with community translations to ensure high-quality language packs.

## Features

- **Multi-Provider Comparison**: Compare translations from Claude (Anthropic), GPT-4o (OpenAI), Aya 23 (Cohere), and community sources
- **Quality Metrics**: Calculate agreement scores, consensus rates, consistency, and cultural sensitivity
- **Conflict Detection**: Automatically identify and classify translation disagreements
- **Comprehensive Reports**: Generate detailed markdown, HTML, or JSON reports
- **Database Integration**: Store and track translation comparisons over time
- **CLI Tools**: Easy-to-use command-line interface for running comparisons

## Quick Start

### Installation

```bash
# Install with comparison system dependencies
cd libs/i18n
uv install
```

### Python API

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.api.providers import AnthropicProvider
from legesher_i18n.comparison.metrics import MetricsCalculator

# Initialize provider
claude = AnthropicProvider(api_key="your-api-key")

# Run comparison for Spanish
comparator = TranslationComparator(
    providers=[claude],
    language="es",
    python_version="3.13"
)

results = comparator.compare()

# Calculate metrics
calculator = MetricsCalculator()
metrics = calculator.calculate_all(results)

print(f"Agreement Score: {metrics.agreement_score:.2%}")
print(f"Consensus Rate: {metrics.consensus_rate:.2%}")
print(f"Conflicts: {len(metrics.conflicts)}")
```

### CLI Usage

```bash
# Compare translations for Spanish using Claude
legesher-i18n compare es --providers claude

# Generate a comprehensive report
legesher-i18n compare es --providers claude,gpt4 --report --output spanish_report.md

# Compare multiple languages
legesher-i18n compare-multi es,ar,zh --summary
```

## How It Works

### 1. Translation Collection

The system collects translations from multiple sources:

```python
# Providers fetch translations
translations = {
    "claude": {"if": "si", "else": "sino", ...},
    "gpt4": {"if": "si", "else": "sino", ...},
    "community": {"if": "si", "else": "sino", ...}
}
```

### 2. Comparison Analysis

Translations are compared using multiple metrics:

```python
# Agreement score: How well do providers agree?
agreement = calculate_agreement(provider_a, provider_b)  # 0.0 - 1.0

# Consensus detection: Which translations have strong agreement?
consensus = detect_consensus(translations, threshold=0.9)

# Conflict identification: Which translations disagree?
conflicts = detect_conflicts(translations, threshold=0.75)
```

### 3. Metrics Calculation

Comprehensive metrics are calculated:

- **Agreement Score**: Percentage of matching translations between providers
- **Consensus Rate**: Percentage of keywords with ≥90% agreement
- **Consistency Score**: How consistently related keywords are translated
- **Cultural Sensitivity**: Appropriateness for target culture (manual review)

### 4. Report Generation

Results are compiled into actionable reports:

```markdown
## Translation Report: Spanish

### Consensus Translations (80%)
These translations are production-ready...

### Conflicts Detected (20%)
These translations need review...

### Recommendations
1. Accept consensus translations immediately
2. Review medium-conflict cases with community
3. Discuss high-conflict cases before finalizing
```

## AnthropicProvider

The system includes a robust Anthropic Claude integration:

```python
from legesher_i18n.api.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="sk-ant-...",
    model="claude-sonnet-4.5",  # Latest model
    temperature=0.3  # Low temperature for consistency
)

# Translate Python keywords
translations = provider.translate_keywords(
    keywords=["if", "else", "elif", "while", "for"],
    target_language="es",
    python_version="3.13",
    context={
        "include_cultural_notes": True,
        "consider_regional_variations": True
    }
)

print(translations)
# {
#     "if": "si",
#     "else": "sino",
#     "elif": "sino_si",
#     "while": "mientras",
#     "for": "para"
# }
```

### Provider Features

- **Context-Aware**: Understands programming context and Python-specific usage
- **Cultural Sensitivity**: Considers regional variations and cultural appropriateness
- **Consistent Patterns**: Maintains logical consistency across related keywords
- **Batch Processing**: Efficient translation of multiple keywords
- **Quality Validation**: Automatic validation against linguistic standards

## Comparison Workflow

### Basic Workflow

```bash
# 1. Run comparison
legesher-i18n compare es --providers claude

# 2. Review consensus translations
#    (These are production-ready with high agreement)

# 3. Examine conflicts
#    (These need human review)

# 4. Generate report for stakeholders
legesher-i18n report es --output spanish_validation.md

# 5. Accept consensus translations
legesher-i18n accept-consensus es

# 6. Flag conflicts for review
legesher-i18n flag-conflicts es --threshold medium
```

### Advanced Workflow

```python
from legesher_i18n.comparison import TranslationComparator, WorkflowManager
from legesher_i18n.api.providers import AnthropicProvider, OpenAIProvider
from legesher_i18n.db import TranslationDatabase

# Initialize components
providers = [
    AnthropicProvider(api_key="..."),
    OpenAIProvider(api_key="...")
]
db = TranslationDatabase("translations.db")
workflow = WorkflowManager(providers=providers, db=db)

# Run complete validation workflow
results = workflow.validate_language(
    language="es",
    python_version="3.13",
    include_community=True,
    auto_accept_consensus=True,  # Auto-accept high-agreement translations
    flag_conflicts=True,  # Flag conflicts for review
    generate_report=True,  # Generate comprehensive report
    store_results=True  # Store in database
)

print(f"Accepted: {len(results.accepted_translations)}")
print(f"Flagged for review: {len(results.flagged_translations)}")
print(f"Report: {results.report_path}")
```

## Metrics and Scoring

### Agreement Score

Measures translation consistency between providers:

```
Agreement Score = (Matching Translations) / (Total Translations)
```

**Interpretation**:
- **100%**: Perfect agreement across all providers
- **90-99%**: High agreement, minor variations
- **75-89%**: Good agreement, some notable differences
- **60-74%**: Medium conflict, review recommended
- **<60%**: High conflict, community discussion required

### Consensus Rate

Percentage of keywords with strong agreement (≥90%):

```
Consensus Rate = (Keywords with ≥90% Agreement) / (Total Keywords) × 100
```

**Target**: 80%+ consensus rate indicates high-quality language pack

### Conflict Levels

Automatic classification of disagreements:

- **None** (100%): No disagreement
- **Low** (75-89%): Minor differences, accept consensus
- **Medium** (60-74%): Notable differences, community validation recommended
- **High** (<60%): Significant differences, extended discussion required

## Report Examples

The system generates comprehensive reports. See example reports:

- [Spanish Comparison Report](./examples/spanish_comparison_report.md): Detailed analysis of 35 Spanish keyword translations
  - 28 consensus translations (80%)
  - 7 conflicts identified and analyzed
  - Provider performance comparison
  - Cultural adaptation insights

- [Multi-Language Summary](./examples/multi_language_summary.md): Cross-language comparison across Spanish, Arabic, and Chinese
  - Comparative metrics across languages
  - Provider specialization analysis
  - Universal patterns and challenges
  - Language-specific recommendations

### Report Structure

Each report includes:

1. **Executive Summary**: Key metrics and findings
2. **Consensus Translations**: Production-ready translations with 90%+ agreement
3. **Conflicting Translations**: Detailed analysis of disagreements with recommendations
4. **Detailed Metrics**: Agreement matrices, provider comparisons, cultural analysis
5. **Recommendations**: Actionable next steps

## CLI Reference

### Compare Command

```bash
# Basic comparison
legesher-i18n compare <language> [options]

# Options:
#   --providers <list>         Providers to compare (comma-separated)
#   --python-version <version> Python version (default: 3.13)
#   --include-community        Include community translations
#   --confidence <threshold>   Confidence threshold (default: 0.75)
#   --report                   Generate report
#   --output <file>            Output file path
#   --format <format>          Output format (markdown, html, json)

# Examples:
legesher-i18n compare es --providers claude
legesher-i18n compare ar --providers claude,gpt4,aya23 --report
legesher-i18n compare zh --include-community --confidence 0.8
```

### Report Command

```bash
# Generate report from existing comparison
legesher-i18n report <language> [options]

# Options:
#   --output <file>     Output file path
#   --format <format>   Output format (markdown, html, json, csv)
#   --section <name>    Report section (consensus, conflicts, metrics, all)

# Examples:
legesher-i18n report es --output spanish_report.md
legesher-i18n report es --section conflicts --format html
legesher-i18n report es --format json --output data.json
```

### Metrics Command

```bash
# View or export metrics
legesher-i18n metrics <language> [options]

# Options:
#   --format <format>      Output format (text, csv, json)
#   --compare-providers    Show provider comparison
#   --historical           Show historical trends
#   --days <number>        Historical period (default: 30)

# Examples:
legesher-i18n metrics es
legesher-i18n metrics es --format csv --output metrics.csv
legesher-i18n metrics es --historical --days 90
```

## API Documentation

### Core Classes

#### TranslationComparator

Main comparison engine:

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.comparison.models import ComparisonConfig

config = ComparisonConfig(
    language="es",
    python_version="3.13",
    include_cultural_analysis=True,
    confidence_threshold=0.75
)

comparator = TranslationComparator(
    providers=[...],
    config=config
)

results = comparator.compare()
```

#### MetricsCalculator

Calculate quality metrics:

```python
from legesher_i18n.comparison.metrics import MetricsCalculator

calculator = MetricsCalculator()
metrics = calculator.calculate_all(results)

# Access specific metrics
print(metrics.agreement_score)  # Overall agreement
print(metrics.consensus_rate)  # % with consensus
print(metrics.conflicts)  # List of conflicts
```

#### AnthropicProvider

Claude integration:

```python
from legesher_i18n.api.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="sk-ant-...",
    model="claude-sonnet-4.5",
    temperature=0.3
)

translations = provider.translate_keywords(
    keywords=["if", "else", "while"],
    target_language="es",
    python_version="3.13"
)
```

### Data Models

All comparison data uses Pydantic models for validation:

```python
from legesher_i18n.comparison.models import (
    ComparisonConfig,      # Configuration
    KeywordComparison,     # Single keyword comparison
    ComparisonResults,     # Full comparison results
    ComparisonMetrics,     # Calculated metrics
    TranslationConflict    # Conflict details
)
```

## Database Integration

Store and query translation comparisons:

```python
from legesher_i18n.db import TranslationDatabase

db = TranslationDatabase("translations.db")

# Store comparison results
db.store_comparison(results)

# Query historical data
history = db.get_comparison_history(
    language="es",
    days=30
)

# Track provider performance
performance = db.get_provider_performance(
    provider="claude",
    language="es",
    days=90
)

# Query specific translations
translation_history = db.get_translation_history(
    keyword="if",
    language="es"
)
```

## Best Practices

### 1. Multiple Providers

Use multiple providers for better validation:

```python
# Good: Multiple perspectives
providers = [claude, gpt4, aya23]

# Better: Include community baseline
providers = [claude, gpt4, aya23, community]
```

### 2. Confidence Thresholds

Adjust thresholds based on your needs:

```python
# Strict: High-quality pack with few conflicts
config = ComparisonConfig(confidence_threshold=0.85)

# Balanced: Good quality with reasonable validation effort
config = ComparisonConfig(confidence_threshold=0.75)

# Permissive: Capture more alternatives for review
config = ComparisonConfig(confidence_threshold=0.60)
```

### 3. Cultural Analysis

Always include cultural analysis for new languages:

```python
config = ComparisonConfig(
    include_cultural_analysis=True,  # Important!
    consider_regional_variations=True
)
```

### 4. Report Generation

Generate reports for stakeholder review:

```python
# For technical review: JSON data
generator.generate_json(results)

# For community review: Markdown with examples
generator.generate_markdown(results)

# For presentation: HTML with charts
generator.generate_html(results, include_charts=True)
```

### 5. Database Tracking

Store results for historical analysis:

```python
# Always store results
db.store_comparison(results)

# Track trends over time
trends = db.get_agreement_trends(language="es", days=180)

# Identify improving/declining patterns
if trends[-1] < trends[0]:
    print("Warning: Agreement declining over time")
```

## Troubleshooting

### Common Issues

**Issue**: Low agreement scores across all providers
```python
# Solution: Check if keywords are correct
# Verify Python version matches
# Review provider configurations
```

**Issue**: API rate limiting
```python
# Solution: Use batch processing
provider.batch_translate(keywords, batch_size=5)

# Or add delays between requests
import time
time.sleep(1)  # Between batches
```

**Issue**: Cultural conflicts in reports
```python
# Solution: Include native speaker review
# Consider regional variants
# Engage community for validation
```

## Contributing

### Adding New Providers

1. Implement `TranslationProvider` interface
2. Add to `legesher_i18n/api/providers/`
3. Add tests in `tests/api/providers/`
4. Update documentation

### Improving Metrics

1. Add calculation method to `MetricsCalculator`
2. Update `ComparisonMetrics` model
3. Add tests
4. Update report templates

### Translating to New Languages

1. Run comparison with multiple providers
2. Review consensus translations
3. Validate conflicts with native speakers
4. Generate and review report
5. Submit language pack

## Further Reading

- **Detailed Documentation**: [TRANSLATION_COMPARISON.md](./TRANSLATION_COMPARISON.md)
- **Example Reports**: [examples/](./examples/)
- **Translation API Guide**: [docs/translation-api.md](./docs/translation-api.md)
- **Database Schema**: [docs/database-schema.md](./docs/database-schema.md)
- **Linguistic Standards**: [docs/linguistic-standards.md](./docs/linguistic-standards.md)

## Support

- **Issues**: https://github.com/legesher/legesher/issues
- **Discussions**: https://github.com/legesher/legesher/discussions
- **Discord**: https://discord.gg/legesher
- **Documentation**: https://docs.legesher.io
