# Translation API Quick Start Guide

Get up and running with the Legesher Translation API in 5 minutes.

## Installation

```bash
pip install legesher-i18n[api]
```

## Option 1: Free (LibreTranslate)

No API keys required!

### Step 1: Start LibreTranslate

```bash
# Using Docker (recommended)
docker run -d -p 5000:5000 libretranslate/libretranslate

# Verify it's running
curl http://localhost:5000/languages
```

### Step 2: Use It

```python
import asyncio
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import LibreTranslateProvider

async def main():
    # Initialize coordinator
    coordinator = TranslationCoordinator(
        providers=[LibreTranslateProvider()],
    )

    # Translate
    result = await coordinator.translate("Hello, world!", "en", "es")
    print(result.text)  # "¡Hola, mundo!"

    # View usage
    stats = coordinator.get_usage_stats()
    print(f"Cost: ${stats['total']['cost_usd']}")  # $0.00 (free!)

asyncio.run(main())
```

## Option 2: Premium (DeepL or Google)

Better quality for production use.

### Step 1: Get API Key

**DeepL** (recommended for European languages):

1. Sign up at <https://www.deepl.com/pro-api>
2. Copy your API key

**Google Translate**:

1. Create project at <https://console.cloud.google.com/>
2. Enable Cloud Translation API
3. Create API key or service account

### Step 2: Set Environment Variable

```bash
# DeepL
export DEEPL_API_KEY="your-deepl-api-key"

# OR Google
export GOOGLE_TRANSLATE_API_KEY="your-google-api-key"
```

### Step 3: Use It

```python
import asyncio
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import DeepLProvider

async def main():
    # Initialize with DeepL
    coordinator = TranslationCoordinator(
        providers=[DeepLProvider()],  # Uses DEEPL_API_KEY env var
    )

    # Translate
    result = await coordinator.translate("Hello, world!", "en", "es")
    print(result.text)  # "Hola, mundo"
    print(result.quality_score)  # 9.5 (excellent!)

    # View usage and cost
    stats = coordinator.get_usage_stats()
    print(f"Cost: ${stats['total']['cost_usd']:.4f}")

asyncio.run(main())
```

## Option 3: Best of Both (Hybrid)

Use premium providers with free fallback.

```python
from legesher_i18n.api import TranslationCoordinator
from legesher_i18n.api.providers import (
    DeepLProvider,
    GoogleTranslateProvider,
    LibreTranslateProvider,
)

async def main():
    # Multiple providers in priority order
    coordinator = TranslationCoordinator(
        providers=[
            DeepLProvider(),  # Try this first (best quality)
            GoogleTranslateProvider(),  # Fallback if DeepL fails
            LibreTranslateProvider(),  # Free fallback (no API key needed)
        ],
    )

    # Automatically uses best available provider
    result = await coordinator.translate("Hello", "en", "es")
    print(f"{result.text} (via {result.provider})")

asyncio.run(main())
```

## Monitor Usage

### Command Line

```bash
# View statistics
legesher-api stats

# Generate HTML dashboard
legesher-api dashboard report.html

# View recent translations
legesher-api recent
```

### Programmatically

```python
# Get usage statistics
stats = coordinator.get_usage_stats()

print(f"Total requests: {stats['total']['requests']}")
print(f"Total cost: ${stats['total']['cost_usd']:.2f}")
print(f"Cache hit rate: {stats['total']['cache_hit_rate']:.1f}%")

# Export to CSV
from legesher_i18n.api.usage_tracker import UsageTracker
tracker = UsageTracker()
tracker.export_csv("usage.csv")
```

## Next Steps

- **Read the full documentation**: [translation-api.md](translation-api.md)
- **Optimize for your language pairs**: See quality score matrix
- **Set up Redis caching**: For production deployments
- **Monitor costs**: Set up usage alerts

## Common Tasks

### Batch Translation

```python
texts = ["Hello", "Goodbye", "Thank you"]
results = await coordinator.translate_batch(texts, "en", "es")
for text, result in zip(texts, results):
    print(f"{text} → {result.text}")
```

### Force Specific Provider

```python
result = await coordinator.translate(
    "Hello",
    "en",
    "es",
    preferred_provider="google"
)
```

### Skip Cache

```python
result = await coordinator.translate(
    "Hello",
    "en",
    "es",
    skip_cache=True
)
```

### Clear Cache

```bash
legesher-api clear-cache
```

## Troubleshooting

### LibreTranslate not connecting?

```bash
# Check if running
docker ps | grep libretranslate

# View logs
docker logs libretranslate

# Restart
docker restart libretranslate
```

### API key not working?

```bash
# Verify environment variable is set
echo $DEEPL_API_KEY

# Test in Python
import os
print(os.getenv("DEEPL_API_KEY"))
```

### High costs?

```bash
# Check usage
legesher-api stats -v

# See which provider costs most
legesher-api dashboard cost_report.html

# Increase cache TTL to reduce API calls
```

## Getting Help

- **Documentation**: [translation-api.md](translation-api.md)
- **Issues**: [GitHub Issues](https://github.com/legesher/legesher/issues)
- **Examples**: See `examples/` directory
