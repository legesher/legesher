# Translation API Documentation

The Legesher Translation API provides dynamic translation capabilities with multi-provider support,
intelligent quality-based fallback, comprehensive usage tracking, and cost monitoring.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Providers](#providers)
- [Quality Validation](#quality-validation)
- [Caching](#caching)
- [Usage Tracking](#usage-tracking)
- [CLI Tools](#cli-tools)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

### Features

- **Multi-Provider Support**: DeepL, Google Translate, and LibreTranslate
- **Intelligent Fallback**: Automatic provider fallback based on quality validation
- **Quality Scoring**: Empirical quality scores guide provider selection per language pair
- **Caching**: SQLite (default) and Redis backends with TTL support
- **Cost Tracking**: Per-provider cost calculation and monitoring
- **Usage Analytics**: Comprehensive statistics and HTML dashboards
- **CLI Tools**: Command-line interface for monitoring and management
- **Progressive Enhancement**: Free providers as default, paid providers optional

### Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                 TranslationCoordinator                      │
├─────────────────────────────────────────────────────────────┤
│  1. Check cache first                                       │
│  2. Select best provider by quality score                   │
│  3. Translate and validate quality                          │
│  4. Fall back if quality insufficient                       │
│  5. Track usage and cost                                    │
│  6. Cache successful result                                 │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │  DeepL   │        │  Google  │        │  Libre   │
    │  9.5/10  │        │  9.0/10  │        │  7.5/10  │
    └──────────┘        └──────────┘        └──────────┘
```

## Quick Start

### Basic Usage

```python
import asyncio
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import LibreTranslateProvider

# Initialize with free provider (no API key required)
coordinator = TranslationCoordinator(
    providers=[LibreTranslateProvider()],
)

# Translate
async def translate():
    result = await coordinator.translate("Hello, world!", "en", "es")
    print(result.text)  # "¡Hola, mundo!"
    print(result.provider)  # "libretranslate"
    print(result.quality_score)  # 7.5

asyncio.run(translate())
```

### With Premium Providers

```python
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import DeepLProvider, GoogleTranslateProvider, LibreTranslateProvider

# Initialize with multiple providers (priority order)
coordinator = TranslationCoordinator(
    providers=[
        DeepLProvider(api_key="your-deepl-key"),  # Highest quality
        GoogleTranslateProvider(api_key="your-google-key"),  # Fallback
        LibreTranslateProvider(),  # Free fallback
    ],
)

# Automatic quality-based provider selection
result = await coordinator.translate("Hello", "en", "es")
print(result.provider)  # "deepl" (highest quality for es-en)
```

## Installation

### Basic Installation

```bash
pip install legesher-i18n
```

### With API Support

```bash
pip install legesher-i18n[api]
```

This installs:

- `deepl>=1.16.0` - DeepL API client
- `google-cloud-translate>=3.15.0` - Google Translate API client
- `httpx>=0.25.0` - HTTP client for LibreTranslate
- `redis>=5.0.0` - Redis cache backend (optional)

## Configuration

### Environment Variables

```bash
# DeepL (optional)
export DEEPL_API_KEY="your-deepl-api-key"

# Google Translate (optional)
export GOOGLE_TRANSLATE_API_KEY="your-google-api-key"
# OR use service account:
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"

# LibreTranslate (optional, defaults to localhost:5000)
export LIBRETRANSLATE_HOST="http://localhost:5000"
export LIBRETRANSLATE_API_KEY="your-api-key"  # If server requires auth
```

### Setting Up LibreTranslate (Free, Self-Hosted)

#### Using Docker (Recommended)

```bash
docker run -d \
  -p 5000:5000 \
  --name libretranslate \
  libretranslate/libretranslate
```

#### Using Python

```bash
pip install libretranslate
libretranslate --host 0.0.0.0 --port 5000
```

## Usage

### Basic Translation

```python
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import DeepLProvider

coordinator = TranslationCoordinator(
    providers=[DeepLProvider()],
)

# Simple translation
result = await coordinator.translate(
    text="Hello, world!",
    source_lang="en",
    target_lang="es"
)

print(result.text)  # "¡Hola, mundo!"
print(result.confidence)  # 0.95
print(result.quality_score)  # 9.5
print(result.billed_characters)  # 13
```

### Batch Translation

```python
# Translate multiple texts efficiently
texts = ["Hello", "Goodbye", "Thank you"]
results = await coordinator.translate_batch(texts, "en", "es")

for text, result in zip(texts, results):
    print(f"{text} → {result.text}")
# Hello → Hola
# Goodbye → Adiós
# Thank you → Gracias
```

### Preferred Provider

```python
# Force use of specific provider
result = await coordinator.translate(
    "Hello",
    "en",
    "es",
    preferred_provider="google"
)
```

### Skip Cache

```python
# Bypass cache for fresh translation
result = await coordinator.translate(
    "Hello",
    "en",
    "es",
    skip_cache=True
)
```

## Providers

### DeepL

**Best for**: European languages (Spanish, French, German, etc.)

```python
from legesher_i18n.api.providers import DeepLProvider

provider = DeepLProvider(
    api_key="your-key",  # Or use DEEPL_API_KEY env var
    max_requests_per_second=10  # Rate limiting
)
```

**Quality Scores**:

- es-en: 9.5/10
- fr-en: 9.3/10
- de-en: 9.4/10

**Pricing**: $20 per 1M characters

### Google Translate

**Best for**: Asian languages (Chinese, Japanese, Korean), Arabic, broad coverage

```python
from legesher_i18n.api.providers import GoogleTranslateProvider

provider = GoogleTranslateProvider(
    api_key="your-key",  # Or use GOOGLE_TRANSLATE_API_KEY
    project_id="your-project",  # Optional
    max_requests_per_second=10
)
```

**Quality Scores**:

- zh-en: 9.0/10
- ja-en: 8.8/10
- ar-en: 8.8/10

**Pricing**: $20 per 1M characters

### LibreTranslate

**Best for**: Privacy, self-hosting, no API costs

```python
from legesher_i18n.api.providers import LibreTranslateProvider

provider = LibreTranslateProvider(
    host="http://localhost:5000",  # Or use LIBRETRANSLATE_HOST
    api_key=None,  # Optional, if server requires auth
    timeout=10.0  # Request timeout in seconds
)
```

**Quality Scores**:

- Average: 7.5/10 (adequate for programming keywords)

**Pricing**: Free (self-hosted)

## Quality Validation

### Automatic Quality-Based Fallback

The coordinator automatically validates translation quality and falls back to the next provider if quality is insufficient:

```python
from legesher_i18n.api import QualityValidator

validator = QualityValidator(
    min_confidence=0.7,  # Minimum confidence score (0-1)
    min_quality_score=7.0,  # Minimum quality score (0-10)
    allow_identical=True  # Allow translation identical to source (for keywords)
)

coordinator = TranslationCoordinator(
    providers=[...],
    quality_validator=validator
)
```

### Quality Score Matrix

The system uses empirical quality scores to select the best provider for each language pair:

| Provider | es-en | fr-en | de-en | zh-en | ja-en | ar-en |
|----------|-------|-------|-------|-------|-------|-------|
| DeepL    | 9.5   | 9.3   | 9.4   | 8.0   | 7.8   | 7.5   |
| Google   | 8.5   | 8.3   | 8.4   | 9.0   | 8.8   | 8.8   |
| LibreTranslate | 7.5 | 7.3 | 7.4 | 7.0 | 6.8 | 6.5   |

### Validation Checks

- **Empty/whitespace** - Fails validation
- **Low confidence** - Below min_confidence threshold
- **Low quality** - Below min_quality_score threshold
- **Identical to source** - Fails for long texts (>20 chars) if not allowed

## Caching

### SQLite Cache (Default)

No setup required, works out of the box:

```python
from legesher_i18n.api.cache import SQLiteCache

cache = SQLiteCache(
    db_path=".legesher/cache.db",  # Database file path
    ttl_seconds=604800  # 7 days TTL
)

coordinator = TranslationCoordinator(
    providers=[...],
    cache=cache
)
```

### Redis Cache (Production)

For distributed/multi-process scenarios:

```python
from legesher_i18n.api.cache import RedisCache

cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    password=None,  # Optional
    ttl_seconds=604800  # 7 days TTL
)

coordinator = TranslationCoordinator(
    providers=[...],
    cache=cache
)
```

### Cache Management

```python
# Get cache statistics
stats = coordinator.get_cache_stats()
print(stats["total_entries"])  # Number of cached translations
print(stats["db_size_mb"])  # Database size (SQLite)
print(stats["hit_rate"])  # Cache hit rate (Redis)

# Clear cache
deleted = coordinator.clear_cache()
print(f"Cleared {deleted} entries")
```

## Usage Tracking

### Automatic Usage Tracking

All translations are automatically tracked:

```python
from legesher_i18n.api.usage_tracker import UsageTracker

tracker = UsageTracker(db_path=".legesher/usage.db")

coordinator = TranslationCoordinator(
    providers=[...],
    usage_tracker=tracker
)

# Translations are automatically tracked
await coordinator.translate("Hello", "en", "es")

# Get statistics
stats = coordinator.get_usage_stats()
print(stats["total"]["cost_usd"])  # Total cost
print(stats["total"]["cache_hit_rate"])  # Cache effectiveness
```

### Usage Statistics

```python
from datetime import datetime, timedelta

# Get stats for specific period
stats = coordinator.get_usage_stats(
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Total usage
print(stats["total"]["requests"])
print(stats["total"]["characters"])
print(stats["total"]["cost_usd"])

# Per-provider breakdown
for provider in stats["by_provider"]:
    print(f"{provider['provider']}: ${provider['cost_usd']:.2f}")

# Top language pairs
for pair in stats["top_language_pairs"]:
    print(f"{pair['pair']}: {pair['requests']} requests")

# Daily trend (last 7 days)
for day in stats["daily_trend"]:
    print(f"{day['date']}: {day['requests']} requests (${day['cost_usd']:.2f})")
```

### CSV Export

```python
tracker.export_csv(
    "usage_report.csv",
    start_date=datetime.now() - timedelta(days=30)
)
```

### HTML Dashboard

```python
from legesher_i18n.api.dashboard import DashboardGenerator

dashboard = DashboardGenerator(tracker)
dashboard.generate(
    "usage_dashboard.html",
    title="Translation API Usage Report"
)
```

## CLI Tools

### CLI Installation

The CLI is automatically installed with the API:

```bash
pip install legesher-i18n[api]
```

### CLI Usage Statistics

```bash
# Show usage statistics (last 30 days)
legesher-api stats

# Specific date range
legesher-api stats --days 7
legesher-api stats --start-date 2025-01-01 --end-date 2025-01-31

# Verbose output (includes daily trend)
legesher-api stats -v
```

### CLI Cache Management

```bash
# View cache statistics
legesher-api cache-stats

# View Redis cache stats
legesher-api cache-stats --redis --redis-host localhost --redis-port 6379

# Clear cache (with confirmation)
legesher-api clear-cache

# Clear cache without confirmation
legesher-api clear-cache --force

# Cleanup expired entries (SQLite only)
legesher-api cleanup-expired
```

### Data Export

```bash
# Export to CSV
legesher-api export-csv usage.csv --days 30

# Generate HTML dashboard
legesher-api dashboard report.html --days 30 --title "Monthly Report"
```

### Recent Activity

```bash
# Show last 20 translations
legesher-api recent

# Show last 50 translations
legesher-api recent --limit 50
```

## Best Practices

### 1. Progressive Enhancement

Start with LibreTranslate (free) and add premium providers as needed:

```python
providers = [LibreTranslateProvider()]  # Start free

# Later, add premium providers for better quality
providers = [
    DeepLProvider(),  # Best for European languages
    GoogleTranslateProvider(),  # Best for Asian languages
    LibreTranslateProvider(),  # Free fallback
]
```

### 2. Language-Specific Provider Selection

Use the quality score matrix to select the best provider for your language pairs:

```python
# For European languages (Spanish, French, German)
providers = [
    DeepLProvider(),  # 9.3-9.5 quality
    GoogleTranslateProvider(),  # Fallback
]

# For Asian languages (Chinese, Japanese, Korean)
providers = [
    GoogleTranslateProvider(),  # 8.8-9.0 quality
    DeepLProvider(),  # Fallback
]
```

### 3. Cache Optimization

```python
# Use Redis for production/multi-process
if production:
    cache = RedisCache(host="redis-server")
else:
    cache = SQLiteCache()  # Development

# Adjust TTL based on content stability
cache = SQLiteCache(
    ttl_seconds=86400  # 1 day for dynamic content
    # ttl_seconds=604800  # 7 days for stable content (default)
)
```

### 4. Cost Monitoring

```python
# Set up regular cost monitoring
stats = coordinator.get_usage_stats()
if stats["total"]["cost_usd"] > 100:  # Alert if over budget
    send_alert(f"Translation costs: ${stats['total']['cost_usd']}")

# Generate monthly reports
from datetime import datetime
from legesher_i18n.api.dashboard import DashboardGenerator

generator = DashboardGenerator(tracker)
generator.generate(
    f"report_{datetime.now().strftime('%Y-%m')}.html",
    start_date=datetime.now().replace(day=1)
)
```

### 5. Error Handling

```python
from legesher_i18n.api.providers.base import (
    TranslationError,
    QuotaExceededError,
    AuthenticationError
)

try:
    result = await coordinator.translate("Hello", "en", "es")
except QuotaExceededError:
    # API quota exceeded, use fallback or wait
    pass
except AuthenticationError:
    # Invalid API key
    pass
except TranslationError as e:
    # General translation error
    print(f"Translation failed: {e}")
```

## Troubleshooting

### LibreTranslate Connection Issues

**Problem**: Cannot connect to LibreTranslate

**Solutions**:

```bash
# Verify LibreTranslate is running
curl http://localhost:5000/languages

# Check Docker container
docker ps | grep libretranslate

# Start LibreTranslate
docker run -d -p 5000:5000 libretranslate/libretranslate
```

### API Key Issues

**Problem**: Authentication errors with DeepL/Google

**Solutions**:

```python
# Verify API key is set
import os
print(os.getenv("DEEPL_API_KEY"))  # Should not be None

# Check key validity
provider = DeepLProvider(api_key="your-key")
if provider.is_available():
    print("API key is valid")
```

### Low Quality Results

**Problem**: Translations fail quality validation

**Solutions**:

```python
# Lower quality thresholds
validator = QualityValidator(
    min_quality_score=6.0,  # Lower threshold
    allow_identical=True  # Allow identical for keywords
)

# Or add more providers for better coverage
providers = [
    DeepLProvider(),
    GoogleTranslateProvider(),
    LibreTranslateProvider(),
]
```

### Cache Issues

**Problem**: Cache not working or expired entries

**Solutions**:

```python
# Verify cache is working
stats = coordinator.get_cache_stats()
print(stats)

# Clear and rebuild cache
coordinator.clear_cache()

# Check TTL settings
cache = SQLiteCache(ttl_seconds=604800)  # 7 days
```

### High Costs

**Problem**: Unexpected translation costs

**Solutions**:

```bash
# Review usage statistics
legesher-api stats -v

# Check cost by provider
legesher-api stats --days 30

# Generate detailed report
legesher-api dashboard cost_analysis.html

# Increase cache TTL to reduce API calls
```python
cache = SQLiteCache(ttl_seconds=2592000)  # 30 days
```

---

For more information, see:

- [API Reference](api-reference.md)
- [Contributing Guide](../../../CONTRIBUTING.md)
- [Issue Tracker](https://github.com/legesher/legesher/issues)
