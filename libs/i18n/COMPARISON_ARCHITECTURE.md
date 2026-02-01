# Translation Comparison System - Architecture

Visual overview of the Legesher translation comparison system architecture.

## System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Translation Comparison System                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  Input Layer                                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Claude     │  │   GPT-4o     │  │   Aya 23     │  │  Community   │  │
│  │ (Anthropic)  │  │  (OpenAI)    │  │  (Cohere)    │  │ Translations │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │                  │          │
│         └──────────────────┴──────────────────┴──────────────────┘          │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Provider Layer                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  TranslationProvider (Base Interface)                              │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │  - translate_keywords(keywords, language, version) -> dict         │    │
│  │  - batch_translate(keywords, language, batch_size) -> dict         │    │
│  │  - validate_translation(keyword, translation) -> bool              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         │                          │                          │            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│  │ Anthropic   │          │   OpenAI    │          │   Cohere    │        │
│  │  Provider   │          │   Provider  │          │   Provider  │        │
│  └─────────────┘          └─────────────┘          └─────────────┘        │
│                                                                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Comparison Layer                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  TranslationComparator                                             │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │  - compare() -> ComparisonResults                                  │    │
│  │  - compare_keyword(keyword) -> KeywordComparison                   │    │
│  │  - normalize_translations(translations) -> dict                    │    │
│  │  - detect_patterns(results) -> list[Pattern]                       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  ComparisonResults                                                 │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │  - language: str                                                   │    │
│  │  - python_version: str                                             │    │
│  │  - keywords: list[KeywordComparison]                               │    │
│  │  - timestamp: datetime                                             │    │
│  │  - metadata: dict                                                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Metrics Layer                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  MetricsCalculator                                                 │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │  - calculate_all(results) -> ComparisonMetrics                     │    │
│  │  - calculate_agreement(provider_a, provider_b) -> float            │    │
│  │  - calculate_consensus(results) -> float                           │    │
│  │  - calculate_consistency(results) -> float                         │    │
│  │  - detect_conflicts(results, threshold) -> list[Conflict]          │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  ComparisonMetrics                                                 │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │  - agreement_score: float         # Overall agreement (0-1)        │    │
│  │  - consensus_rate: float          # % with consensus               │    │
│  │  - consistency_score: float       # Pattern consistency            │    │
│  │  - conflicts: list[Conflict]      # Detected conflicts             │    │
│  │  - provider_scores: dict          # Per-provider metrics           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Report Layer                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  ReportGenerator                                                   │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │  - generate_markdown(results) -> str                               │    │
│  │  - generate_html(results) -> str                                   │    │
│  │  - generate_json(results) -> str                                   │    │
│  │  - generate_csv(results) -> str                                    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         │                          │                          │            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│  │  Markdown   │          │    HTML     │          │    JSON     │        │
│  │   Report    │          │   Report    │          │    Data     │        │
│  └─────────────┘          └─────────────┘          └─────────────┘        │
│                                                                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Storage Layer                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  TranslationDatabase                                               │    │
│  ├────────────────────────────────────────────────────────────────────┤    │
│  │  - store_comparison(results) -> None                               │    │
│  │  - get_comparison_history(language, days) -> list                  │    │
│  │  - get_provider_performance(provider, days) -> dict                │    │
│  │  - get_translation_history(keyword, language) -> list              │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│                          ┌──────────────────┐                              │
│                          │  SQLite Database │                              │
│                          │  translations.db │                              │
│                          └──────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```text
1. Input Collection
   ┌─────────────────────────────────────────────────────────────┐
   │ Keywords: ["if", "else", "elif", "while", "for", ...]      │
   │ Language: "es" (Spanish)                                    │
   │ Python Version: "3.13"                                      │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
2. Provider Translation
   ┌─────────────────────────────────────────────────────────────┐
   │ Claude:     {"if": "si", "else": "sino", "elif": "sino_si"}│
   │ GPT-4o:     {"if": "si", "else": "sino", "elif": "osi"}    │
   │ Aya 23:     {"if": "si", "else": "sino", ...}              │
   │ Community:  {"if": "si", "else": "sino", "elif": "sino_si"}│
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
3. Comparison Analysis
   ┌─────────────────────────────────────────────────────────────┐
   │ "if":   [✓] All agree: "si" (100% agreement)               │
   │ "else": [✓] All agree: "sino" (100% agreement)             │
   │ "elif": [!] Conflict: "sino_si" vs "osi" (75% agreement)   │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
4. Metrics Calculation
   ┌─────────────────────────────────────────────────────────────┐
   │ Agreement Score: 0.85 (85%)                                 │
   │ Consensus Rate: 0.80 (80%)                                  │
   │ Consistency Score: 0.92                                     │
   │ Conflicts Detected: 7 (3 low, 3 medium, 1 high)            │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
5. Report Generation
   ┌─────────────────────────────────────────────────────────────┐
   │ # Translation Report: Spanish                               │
   │ ## Consensus Translations (80%)                             │
   │ - if → si (100% agreement)                                  │
   │ ## Conflicts (20%)                                          │
   │ - elif: sino_si vs osi (75% agreement) [Medium]            │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
6. Storage & Tracking
   ┌─────────────────────────────────────────────────────────────┐
   │ Database: translations.db                                   │
   │ - Comparison results stored                                 │
   │ - Historical trends tracked                                 │
   │ - Provider performance logged                               │
   └─────────────────────────────────────────────────────────────┘
```

## Component Interactions

### Comparison Workflow

```text
User Request
    │
    ├──> TranslationComparator.compare()
    │       │
    │       ├──> AnthropicProvider.translate_keywords()
    │       │       └──> Claude API Request
    │       │
    │       ├──> OpenAIProvider.translate_keywords()
    │       │       └──> OpenAI API Request
    │       │
    │       ├──> CohereProvider.translate_keywords()
    │       │       └──> Cohere API Request
    │       │
    │       └──> Load Community Translations
    │               └──> Read from language pack YAML
    │
    ├──> MetricsCalculator.calculate_all()
    │       │
    │       ├──> calculate_agreement()
    │       ├──> calculate_consensus()
    │       ├──> calculate_consistency()
    │       └──> detect_conflicts()
    │
    ├──> ReportGenerator.generate_markdown()
    │       │
    │       ├──> Format consensus translations
    │       ├──> Format conflicts
    │       ├──> Add metrics tables
    │       └──> Generate recommendations
    │
    └──> TranslationDatabase.store_comparison()
            └──> SQLite INSERT
```

### Provider Communication

```text
TranslationComparator
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│ AnthropicProvider│                  │  OpenAIProvider  │
└────────┬─────────┘                  └────────┬─────────┘
         │                                     │
         │ POST /v1/messages                   │ POST /v1/chat/completions
         ▼                                     ▼
┌─────────────────────────────────────────────────────────┐
│              External APIs                              │
├─────────────────────────────────────────────────────────┤
│  Claude API          OpenAI API         Cohere API      │
│  (Anthropic)         (OpenAI)           (Cohere)        │
└─────────────────────────────────────────────────────────┘
         │                                     │
         │ Response: translations              │ Response: translations
         ▼                                     ▼
┌──────────────────┐                  ┌──────────────────┐
│  Translation     │                  │  Translation     │
│  Normalization   │                  │  Normalization   │
└────────┬─────────┘                  └────────┬─────────┘
         │                                     │
         └─────────────────┬───────────────────┘
                           │
                           ▼
                  Comparison Engine
```

## Data Models

### Core Models

```text
ComparisonConfig
├── language: str
├── python_version: str
├── include_cultural_analysis: bool
└── confidence_threshold: float

ComparisonResults
├── language: str
├── python_version: str
├── keywords: list[KeywordComparison]
├── timestamp: datetime
└── metadata: dict

KeywordComparison
├── keyword: str
├── translations: dict[str, str]
├── agreement_score: float
├── consensus: Optional[str]
└── conflict_level: Literal["none", "low", "medium", "high"]

ComparisonMetrics
├── agreement_score: float
├── consensus_rate: float
├── consistency_score: float
├── conflicts: list[TranslationConflict]
└── provider_scores: dict[str, ProviderMetrics]

TranslationConflict
├── keyword: str
├── translations: dict[str, str]
├── severity: Literal["low", "medium", "high"]
├── recommendation: str
└── cultural_note: Optional[str]
```

### Data Flow Through Models

```text
Input Data
    │
    ├─> ComparisonConfig (Configuration)
    │
    ▼
Translation Providers
    │
    ├─> dict[str, str] (Raw translations)
    │
    ▼
TranslationComparator
    │
    ├─> KeywordComparison (Per keyword)
    │
    ├─> ComparisonResults (All keywords)
    │
    ▼
MetricsCalculator
    │
    ├─> ComparisonMetrics (Calculated metrics)
    │
    ├─> TranslationConflict (Detected conflicts)
    │
    ▼
ReportGenerator
    │
    ├─> Markdown Report (Human-readable)
    │
    ├─> HTML Report (Web-friendly)
    │
    └─> JSON Data (Machine-readable)
```

## CLI Architecture

```text
Command Line Interface
         │
         ├─> legesher-i18n compare
         │       │
         │       ├─> Parse arguments
         │       ├─> Load configuration
         │       ├─> Initialize providers
         │       ├─> Run TranslationComparator
         │       ├─> Calculate metrics
         │       ├─> Generate report (if --report)
         │       └─> Display results
         │
         ├─> legesher-i18n report
         │       │
         │       ├─> Load comparison results
         │       ├─> Initialize ReportGenerator
         │       ├─> Generate report (format specified)
         │       └─> Save to file
         │
         ├─> legesher-i18n metrics
         │       │
         │       ├─> Load comparison results
         │       ├─> Calculate metrics
         │       ├─> Format output
         │       └─> Display/export
         │
         └─> legesher-i18n compare-multi
                 │
                 ├─> Parse language list
                 ├─> Run comparison for each language
                 ├─> Aggregate results
                 ├─> Generate summary report
                 └─> Display results
```

## API Architecture

```text
Python API
    │
    ├─> legesher_i18n.comparison
    │       ├── TranslationComparator
    │       ├── models.py (Pydantic models)
    │       └── metrics.py (MetricsCalculator)
    │
    ├─> legesher_i18n.api.providers
    │       ├── base.py (TranslationProvider interface)
    │       ├── anthropic.py (AnthropicProvider)
    │       ├── openai.py (OpenAIProvider)
    │       └── cohere.py (CohereProvider)
    │
    ├─> legesher_i18n.reports
    │       ├── generator.py (ReportGenerator)
    │       └── templates/ (Report templates)
    │
    └─> legesher_i18n.db
            ├── schema.py (Database schema)
            └── database.py (TranslationDatabase)
```

## Integration Points

### External Systems

```text
┌─────────────────────────────────────────────────────────────┐
│  Legesher Translation Comparison System                     │
└─────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│  Language Packs  │            │  External APIs   │
│  (YAML files)    │            │  (Claude, etc)   │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         │                               │
         ▼                               ▼
┌─────────────────────────────────────────────────────┐
│  Database (SQLite)                                  │
│  - Comparison history                               │
│  - Provider performance                             │
│  - Translation trends                               │
└─────────────────────────────────────────────────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  Reports & Exports                                  │
│  - Markdown reports                                 │
│  - HTML reports                                     │
│  - JSON data                                        │
│  - CSV exports                                      │
└─────────────────────────────────────────────────────┘
```

### Future Extensions

```text
Current System
    │
    ├─> [PLANNED] Language Server Protocol
    │       └──> IDE integration for real-time comparison
    │
    ├─> [PLANNED] Web UI
    │       └──> Interactive comparison dashboard
    │
    ├─> [PLANNED] CI/CD Integration
    │       └──> Automated quality checks
    │
    └─> [PLANNED] Community Voting
            └──> Crowdsourced translation validation
```

## Performance Considerations

### Caching Strategy

```text
Request
    │
    ├─> Check cache
    │       ├─> Cache hit? ──> Return cached result
    │       └─> Cache miss? ──┐
    │                         │
    └─────────────────────────┘
                              │
                              ▼
                    Fetch from provider
                              │
                              ├─> Store in cache
                              │
                              └─> Return result
```

### Batch Processing

```text
Keywords: [k1, k2, k3, k4, k5, k6, k7, k8, k9, k10]
                │
                ├─> Batch 1: [k1, k2, k3]
                │       └──> API Request 1
                │
                ├─> Batch 2: [k4, k5, k6]
                │       └──> API Request 2
                │
                └─> Batch 3: [k7, k8, k9, k10]
                        └──> API Request 3
```

## Security Considerations

```text
API Key Management
    │
    ├─> Environment variables (recommended)
    │       └──> export ANTHROPIC_API_KEY="..."
    │
    ├─> Configuration files (with .gitignore)
    │       └──> config.yml (not committed)
    │
    └─> Secrets management (production)
            └──> AWS Secrets Manager, etc.

Data Privacy
    │
    ├─> Local-first processing
    │       └──> Translations stored locally
    │
    ├─> Encrypted storage
    │       └──> Database encryption (optional)
    │
    └─> No sensitive data in reports
            └──> Only translations, no API keys
```

## Extensibility Points

### Adding New Providers

```text
1. Create provider class
   ├── Inherit from TranslationProvider
   ├── Implement translate_keywords()
   └── Implement batch_translate()

2. Add to provider registry
   └── Register in __init__.py

3. Add tests
   └── Create test_<provider>.py

4. Update documentation
   └── Add provider to docs
```

### Adding New Metrics

```text
1. Add calculation method
   ├── Add to MetricsCalculator
   └── Implement calculation logic

2. Update data models
   ├── Add field to ComparisonMetrics
   └── Update Pydantic model

3. Update reports
   ├── Add to report templates
   └── Update ReportGenerator

4. Add tests
   └── Test new metric calculation
```

---

**Architecture Version**: 1.0
**Last Updated**: 2025-11-11
**Related Docs**: See `TRANSLATION_COMPARISON.md` for detailed documentation
