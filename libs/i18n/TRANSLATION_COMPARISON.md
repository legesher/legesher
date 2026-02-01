# Translation Comparison System

The Legesher i18n package includes a comprehensive translation comparison system
that enables comparison of AI-generated translations with community translations,
helping ensure high-quality language packs.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [CLI Usage](#cli-usage)
- [Metrics and Scoring](#metrics-and-scoring)
- [Report Generation](#report-generation)
- [Examples](#examples)
- [Contributing](#contributing)

## Overview

The Translation Comparison System provides tools to:

1. **Compare translations** from multiple AI providers (Claude, GPT-4o, Aya 23, etc.)
2. **Calculate metrics** (agreement scores, consistency, cultural sensitivity)
3. **Identify conflicts** between different translation approaches
4. **Generate reports** documenting translation quality and recommendations
5. **Validate translations** against community standards

### Why Translation Comparison?

Creating high-quality programming language translations requires:

- **Accuracy**: Translations must preserve semantic meaning
- **Cultural appropriateness**: Keywords should feel natural to native speakers
- **Consistency**: Related keywords should follow logical patterns
- **Community consensus**: Translations should reflect community preferences

The comparison system helps achieve these goals by systematically evaluating multiple translation sources.

## Features

### Multi-Provider Comparison

Compare translations from multiple AI providers:

- **Anthropic Claude**: Strong cultural awareness, consistent patterns
- **OpenAI GPT-4o**: Clear, concise translations
- **Cohere Aya 23**: Specialized in non-Western languages
- **Community translations**: Existing validated translations

### Comprehensive Metrics

Calculate detailed quality metrics:

- **Agreement scores**: How well providers agree on translations
- **Consensus rate**: Percentage of keywords with strong agreement
- **Consistency scores**: Internal consistency of translation patterns
- **Cultural sensitivity**: Appropriateness for target culture
- **Conflict detection**: Automatic identification of disagreements

### Detailed Reports

Generate comprehensive reports including:

- Executive summaries with key metrics
- Consensus translations (ready for production)
- Conflicting translations with recommendations
- Provider performance comparisons
- Cultural adaptation analysis
- Actionable recommendations

### Database Integration

Store and query translation comparisons:

- Historical tracking of translation evolution
- Version-aware comparison across Python versions
- Provider performance tracking over time
- Community feedback integration

## Quick Start

### Installation

```bash
cd libs/i18n
uv install
```

### Basic Usage

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.api.providers import AnthropicProvider
from legesher_i18n.comparison.metrics import MetricsCalculator
from legesher_i18n.comparison.models import ComparisonConfig

# Configure comparison
config = ComparisonConfig(
    language="es",
    python_version="3.13",
    include_cultural_analysis=True
)

# Initialize provider
claude = AnthropicProvider(api_key="your-api-key")

# Create comparator
comparator = TranslationComparator(
    providers=[claude],
    config=config
)

# Run comparison
results = comparator.compare()

# Calculate metrics
calculator = MetricsCalculator()
metrics = calculator.calculate_all(results)

print(f"Agreement Score: {metrics.agreement_score:.2%}")
print(f"Consensus Rate: {metrics.consensus_rate:.2%}")
print(f"Conflicts Detected: {len(metrics.conflicts)}")
```

### CLI Usage

```bash
# Compare translations for Spanish
legesher-i18n compare es --providers claude,gpt4,aya23

# Generate report
legesher-i18n compare es --report --output spanish_report.md

# Compare with community translations
legesher-i18n compare es --include-community --confidence-threshold 0.8

# Multi-language comparison
legesher-i18n compare-multi es,ar,zh --summary
```

## Architecture

### Component Overview

```text
legesher_i18n/
├── api/
│   └── providers/
│       ├── base.py          # Base provider interface
│       ├── anthropic.py     # Claude integration
│       ├── openai.py        # GPT-4o integration (planned)
│       └── cohere.py        # Aya 23 integration (planned)
├── comparison/
│   ├── models.py            # Data models for comparison
│   ├── comparator.py        # Comparison engine
│   ├── metrics.py           # Metrics calculation
│   └── validators.py        # Translation validation
├── reports/
│   ├── generator.py         # Report generation
│   └── templates/           # Report templates
└── db/
    ├── schema.py            # Database schema
    └── database.py          # Database operations
```

### Data Flow

```text
1. Translation Sources
   ├── AI Providers (Claude, GPT-4o, Aya 23)
   └── Community Translations

2. Comparison Engine
   ├── Normalize translations
   ├── Calculate pairwise comparisons
   └── Detect conflicts

3. Metrics Calculator
   ├── Agreement scores
   ├── Consistency checks
   └── Cultural analysis

4. Report Generator
   ├── Consensus translations
   ├── Conflict analysis
   └── Recommendations

5. Database Storage
   ├── Historical tracking
   └── Version management
```

## API Documentation

### TranslationComparator

Main class for comparing translations across providers.

```python
class TranslationComparator:
    """
    Compare translations from multiple providers.

    This class orchestrates translation comparison by:
    1. Fetching translations from all configured providers
    2. Normalizing translation formats
    3. Performing pairwise comparisons
    4. Detecting conflicts and consensus

    Args:
        providers: List of translation providers to compare
        config: Configuration for comparison behavior

    Example:
        >>> from legesher_i18n.comparison import TranslationComparator
        >>> from legesher_i18n.api.providers import AnthropicProvider
        >>>
        >>> claude = AnthropicProvider(api_key="...")
        >>> comparator = TranslationComparator(
        ...     providers=[claude],
        ...     config=ComparisonConfig(language="es")
        ... )
        >>> results = comparator.compare()
        >>> print(f"Compared {len(results.keywords)} keywords")
    """

    def __init__(
        self,
        providers: list[TranslationProvider],
        config: ComparisonConfig
    ):
        """Initialize comparator with providers and configuration."""

    def compare(self) -> ComparisonResults:
        """
        Run comparison across all providers.

        Returns:
            ComparisonResults containing all translations and metrics

        Raises:
            ComparisonError: If comparison fails
        """

    def compare_keyword(self, keyword: str) -> KeywordComparison:
        """
        Compare translations for a single keyword.

        Args:
            keyword: English Python keyword to compare

        Returns:
            KeywordComparison with all provider translations
        """
```

### MetricsCalculator

Calculate quality metrics for translation comparisons.

```python
class MetricsCalculator:
    """
    Calculate comprehensive metrics for translation comparisons.

    Provides multiple metric types:
    - Agreement: How well providers agree on translations
    - Consistency: Internal consistency of translation patterns
    - Consensus: Percentage of translations with strong agreement
    - Conflicts: Identification of disagreements

    Example:
        >>> calculator = MetricsCalculator()
        >>> metrics = calculator.calculate_all(comparison_results)
        >>> print(f"Agreement: {metrics.agreement_score:.2%}")
        >>> print(f"Conflicts: {len(metrics.conflicts)}")
    """

    def calculate_all(self, results: ComparisonResults) -> ComparisonMetrics:
        """
        Calculate all available metrics.

        Args:
            results: Comparison results from TranslationComparator

        Returns:
            ComparisonMetrics with all calculated metrics
        """

    def calculate_agreement(
        self,
        provider_a: str,
        provider_b: str,
        translations: dict
    ) -> float:
        """
        Calculate agreement score between two providers.

        Args:
            provider_a: First provider name
            provider_b: Second provider name
            translations: Dictionary of translations by keyword

        Returns:
            Agreement score (0.0 to 1.0)

        Example:
            >>> score = calculator.calculate_agreement(
            ...     "claude", "gpt4", translations
            ... )
            >>> print(f"Agreement: {score:.2%}")
        """

    def detect_conflicts(
        self,
        results: ComparisonResults,
        threshold: float = 0.75
    ) -> list[TranslationConflict]:
        """
        Identify translation conflicts.

        Args:
            results: Comparison results
            threshold: Agreement threshold below which conflicts are detected

        Returns:
            List of detected conflicts with severity and recommendations

        Example:
            >>> conflicts = calculator.detect_conflicts(results)
            >>> for conflict in conflicts:
            ...     print(f"{conflict.keyword}: {conflict.severity}")
        """
```

### AnthropicProvider

Translation provider using Claude API.

```python
class AnthropicProvider(TranslationProvider):
    """
    Translation provider using Anthropic's Claude API.

    Supports multiple Claude models:
    - claude-sonnet-4.5: Latest flagship model (default)
    - claude-sonnet-3.5: Previous generation
    - claude-opus-3: Highest quality (slower)

    Features:
    - Context-aware translations with technical understanding
    - Cultural sensitivity and regional awareness
    - Consistent translation patterns
    - Batch processing support

    Args:
        api_key: Anthropic API key
        model: Claude model to use (default: claude-sonnet-4.5)
        temperature: Sampling temperature (0.0-1.0, default: 0.3)

    Example:
        >>> provider = AnthropicProvider(
        ...     api_key="sk-ant-...",
        ...     model="claude-sonnet-4.5",
        ...     temperature=0.3
        ... )
        >>> translations = provider.translate_keywords(
        ...     keywords=["if", "else", "while"],
        ...     target_language="es",
        ...     python_version="3.13"
        ... )
        >>> print(translations["if"])  # "si"
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4.5",
        temperature: float = 0.3
    ):
        """Initialize Anthropic provider."""

    def translate_keywords(
        self,
        keywords: list[str],
        target_language: str,
        python_version: str,
        context: Optional[dict] = None
    ) -> dict[str, str]:
        """
        Translate Python keywords to target language.

        Args:
            keywords: List of English Python keywords
            target_language: Target language code (e.g., "es")
            python_version: Python version (e.g., "3.13")
            context: Optional additional context for translation

        Returns:
            Dictionary mapping keywords to translations

        Raises:
            ProviderError: If API request fails
            ValidationError: If translations fail validation
        """

    def batch_translate(
        self,
        keywords: list[str],
        target_language: str,
        batch_size: int = 10
    ) -> dict[str, str]:
        """
        Translate keywords in batches for efficiency.

        Args:
            keywords: List of keywords to translate
            target_language: Target language code
            batch_size: Number of keywords per batch

        Returns:
            Dictionary of all translations
        """
```

### ComparisonModels

Data models for comparison system.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class ComparisonConfig(BaseModel):
    """Configuration for translation comparison."""

    language: str = Field(description="Target language code (e.g., 'es')")
    python_version: str = Field(default="3.13", description="Python version")
    include_cultural_analysis: bool = Field(
        default=True,
        description="Include cultural sensitivity analysis"
    )
    confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for consensus"
    )

class KeywordComparison(BaseModel):
    """Comparison results for a single keyword."""

    keyword: str = Field(description="English Python keyword")
    translations: dict[str, str] = Field(
        description="Provider translations (provider_name -> translation)"
    )
    agreement_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Agreement score across providers"
    )
    consensus: Optional[str] = Field(
        default=None,
        description="Consensus translation if agreement high enough"
    )
    conflict_level: Literal["none", "low", "medium", "high"] = Field(
        description="Conflict severity level"
    )

class ComparisonResults(BaseModel):
    """Complete comparison results."""

    language: str
    python_version: str
    keywords: list[KeywordComparison]
    timestamp: str
    metadata: dict

class ComparisonMetrics(BaseModel):
    """Calculated metrics for comparison."""

    agreement_score: float = Field(description="Overall agreement (0.0-1.0)")
    consensus_rate: float = Field(description="% of keywords with consensus")
    consistency_score: float = Field(description="Pattern consistency score")
    conflicts: list[TranslationConflict]
    provider_scores: dict[str, ProviderMetrics]
```

## CLI Usage

### Basic Commands

```bash
# Compare translations
legesher-i18n compare <language> [options]

# Generate report
legesher-i18n report <language> [options]

# Multi-language comparison
legesher-i18n compare-multi <languages> [options]

# View metrics
legesher-i18n metrics <language> [options]
```

### Compare Command

```bash
# Compare Spanish translations from multiple providers
legesher-i18n compare es --providers claude,gpt4,aya23

# Include community translations
legesher-i18n compare es --providers claude --include-community

# Specify Python version
legesher-i18n compare es --python-version 3.11

# Set confidence threshold
legesher-i18n compare es --confidence-threshold 0.8

# Output to JSON
legesher-i18n compare es --format json --output results.json
```

### Report Command

```bash
# Generate full report
legesher-i18n report es --output spanish_report.md

# Report only conflicts
legesher-i18n report es --section conflicts

# Report only consensus
legesher-i18n report es --section consensus

# HTML report
legesher-i18n report es --format html --output report.html
```

### Multi-Language Command

```bash
# Compare multiple languages
legesher-i18n compare-multi es,ar,zh

# Generate summary report
legesher-i18n compare-multi es,ar,zh --summary --output summary.md

# Cross-language analysis
legesher-i18n compare-multi es,ar,zh --cross-analysis
```

### Metrics Command

```bash
# View metrics summary
legesher-i18n metrics es

# Export metrics to CSV
legesher-i18n metrics es --format csv --output metrics.csv

# Provider comparison
legesher-i18n metrics es --compare-providers

# Historical metrics
legesher-i18n metrics es --historical --days 30
```

## Metrics and Scoring

### Agreement Score

Measures how well providers agree on translations:

```python
Agreement = (Number of Matching Translations) / (Total Translations)
```

- **1.0 (100%)**: Perfect agreement
- **0.9-0.99**: High agreement, minor variations
- **0.75-0.89**: Good agreement, some differences
- **0.6-0.74**: Medium agreement, notable conflicts
- **<0.6**: Low agreement, significant conflicts

### Consensus Rate

Percentage of keywords with strong agreement (≥90%):

```python
Consensus Rate = (Keywords with ≥90% Agreement) / (Total Keywords)
```

### Consistency Score

How consistently a provider translates related keywords:

```python
# Example: Control flow consistency
control_flow = ["if", "elif", "else", "while", "for"]
pattern_consistency = similarity(translations[control_flow])
```

### Cultural Sensitivity Score

Manual review score (1-10) evaluating:

- Cultural appropriateness
- Regional awareness
- Technical context understanding
- Community alignment

### Conflict Levels

- **None**: 100% agreement
- **Low**: 75-89% agreement - Accept consensus
- **Medium**: 60-74% agreement - Review recommended
- **High**: <60% agreement - Community discussion required

## Report Generation

### Report Structure

Generated reports include:

1. **Executive Summary**
   - Overall metrics
   - Key findings
   - Provider performance

2. **Consensus Translations**
   - High-agreement keywords
   - Production-ready translations
   - Usage examples

3. **Conflicting Translations**
   - Disagreements between providers
   - Conflict severity
   - Recommendations

4. **Detailed Analysis**
   - Agreement matrices
   - Cultural sensitivity analysis
   - Pattern consistency

5. **Recommendations**
   - Immediate actions
   - Validation needed
   - Community discussion items

### Customizing Reports

```python
from legesher_i18n.reports import ReportGenerator, ReportConfig

config = ReportConfig(
    include_cultural_analysis=True,
    include_provider_comparison=True,
    conflict_threshold=0.75,
    sections=[
        "executive_summary",
        "consensus_translations",
        "conflicts",
        "metrics",
        "recommendations"
    ],
    format="markdown"  # or "html", "json"
)

generator = ReportGenerator(config=config)
report = generator.generate(comparison_results)
```

### Report Formats

- **Markdown**: Human-readable, version-controllable
- **HTML**: Interactive, with charts and visualizations
- **JSON**: Machine-readable, for further processing
- **CSV**: Spreadsheet-compatible, for analysis

## Examples

### Example 1: Basic Comparison

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.api.providers import AnthropicProvider
from legesher_i18n.comparison.models import ComparisonConfig

# Setup
config = ComparisonConfig(language="es", python_version="3.13")
claude = AnthropicProvider(api_key="your-key")
comparator = TranslationComparator(providers=[claude], config=config)

# Run comparison
results = comparator.compare()

# Access results
for keyword_comp in results.keywords:
    print(f"{keyword_comp.keyword}: {keyword_comp.consensus}")
    if keyword_comp.conflict_level != "none":
        print(f"  Conflict: {keyword_comp.conflict_level}")
```

### Example 2: Multi-Provider Comparison

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.api.providers import (
    AnthropicProvider,
    OpenAIProvider,
    CohereProvider
)

# Setup multiple providers
providers = [
    AnthropicProvider(api_key="anthropic-key"),
    OpenAIProvider(api_key="openai-key"),
    CohereProvider(api_key="cohere-key")
]

config = ComparisonConfig(language="ar")
comparator = TranslationComparator(providers=providers, config=config)

# Compare
results = comparator.compare()

# Find best provider
from legesher_i18n.comparison.metrics import MetricsCalculator
calculator = MetricsCalculator()
metrics = calculator.calculate_all(results)

for provider, scores in metrics.provider_scores.items():
    print(f"{provider}: {scores.agreement_with_community:.2%}")
```

### Example 3: Generating Reports

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.reports import ReportGenerator
from legesher_i18n.api.providers import AnthropicProvider

# Run comparison
claude = AnthropicProvider(api_key="your-key")
comparator = TranslationComparator(providers=[claude], config={"language": "zh"})
results = comparator.compare()

# Generate report
generator = ReportGenerator()

# Markdown report
md_report = generator.generate_markdown(results)
with open("chinese_report.md", "w") as f:
    f.write(md_report)

# HTML report with charts
html_report = generator.generate_html(results, include_charts=True)
with open("chinese_report.html", "w") as f:
    f.write(html_report)

# JSON for analysis
json_report = generator.generate_json(results)
with open("chinese_data.json", "w") as f:
    f.write(json_report)
```

### Example 4: Detecting Conflicts

```python
from legesher_i18n.comparison import TranslationComparator
from legesher_i18n.comparison.metrics import MetricsCalculator

# Run comparison
comparator = TranslationComparator(...)
results = comparator.compare()

# Detect conflicts
calculator = MetricsCalculator()
conflicts = calculator.detect_conflicts(results, threshold=0.75)

# Handle conflicts by severity
high_conflicts = [c for c in conflicts if c.severity == "high"]
medium_conflicts = [c for c in conflicts if c.severity == "medium"]

print(f"High priority conflicts requiring discussion: {len(high_conflicts)}")
for conflict in high_conflicts:
    print(f"  {conflict.keyword}:")
    for provider, translation in conflict.translations.items():
        print(f"    {provider}: {translation}")
    print(f"  Recommendation: {conflict.recommendation}")
```

### Example 5: Database Integration

```python
from legesher_i18n.db import TranslationDatabase
from legesher_i18n.comparison import TranslationComparator

# Initialize database
db = TranslationDatabase("translations.db")

# Run comparison
comparator = TranslationComparator(...)
results = comparator.compare()

# Store results
db.store_comparison(results)

# Query historical data
history = db.get_comparison_history(language="es", days=30)
print(f"Agreement trend: {[h.agreement_score for h in history]}")

# Track provider performance over time
provider_history = db.get_provider_performance("claude", days=90)
print(f"Claude average agreement: {sum(h.agreement for h in provider_history) / len(provider_history):.2%}")
```

## Example Reports

See the `examples/` directory for complete example reports:

- [Spanish Comparison Report](./examples/spanish_comparison_report.md): Detailed analysis of Spanish translations
- [Multi-Language Summary](./examples/multi_language_summary.md): Cross-language comparison across Spanish, Arabic, and Chinese

## Contributing

### Adding New Providers

To add a new translation provider:

1. Create provider class in `legesher_i18n/api/providers/`
2. Implement `TranslationProvider` interface
3. Add tests in `tests/api/providers/`
4. Update documentation

Example:

```python
from legesher_i18n.api.providers.base import TranslationProvider

class NewProvider(TranslationProvider):
    def translate_keywords(
        self,
        keywords: list[str],
        target_language: str,
        python_version: str
    ) -> dict[str, str]:
        # Implementation
        pass
```

### Improving Metrics

To add new metrics:

1. Add calculation method to `MetricsCalculator`
2. Update `ComparisonMetrics` model
3. Add tests in `tests/comparison/test_metrics.py`
4. Update report templates

### Report Templates

Customize report templates in `legesher_i18n/reports/templates/`:

- `markdown_template.md.j2`: Markdown reports
- `html_template.html.j2`: HTML reports
- `summary_template.md.j2`: Summary reports

## Resources

- **Translation API Documentation**: [`docs/translation-api.md`](../docs/translation-api.md)
- **Database Schema**: [`docs/database-schema.md`](../docs/database-schema.md)
- **Linguistic Standards**: [`docs/linguistic-standards.md`](../docs/linguistic-standards.md)
- **Example Reports**: [`examples/`](./examples/)

## License

This translation comparison system is part of the Legesher project and is licensed under the MIT License.
