# legesher-i18n-python-ru

Russian (Русский) language pack for Python in Legesher.

> **Status: experimental** — machine-generated translations; community validation in progress.
> Terms may change as native speakers review them.

## Overview

This package provides Russian translations for Python keywords and built-in functions, enabling developers to write
Python code in Russian.

## Supported Python Versions

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

## Installation

```bash
# Install with legesher-i18n
uv pip install legesher-i18n legesher-i18n-python-ru

# Or with pip
pip install legesher-i18n legesher-i18n-python-ru
```

## Usage

The language pack is automatically discovered by `legesher-i18n` when installed:

```python
from legesher_i18n import LanguagePackLoader

# Load Russian pack for Python 3.12
loader = LanguagePackLoader()
pack = loader.load("ru", "python", "3.12")

# Use translated keywords
print(pack.keywords["def"])
print(pack.keywords["class"])
print(pack.keywords["return"])
```

## Translation Coverage

This pack provides translations for:

- **Keywords**: 39 Python keywords
- **Built-ins**: 73 built-in functions and types
- **Exceptions**: 70 exception classes

## Version Inheritance

Language packs use inheritance to minimize duplication:

- `3.10.yml` - Complete Python 3.10 translations
- `3.11.yml` - Extends 3.10, adds new keywords (e.g., `except*`)
- `3.12.yml` - Extends 3.11, adds `type` keyword
- `3.13.yml` - Extends 3.12 (no new keywords)
- `3.14.yml` - Extends 3.13 (Python 3.14 in development)

## Contributing

To contribute translations or improvements:

1. Fork the [Legesher repository](https://github.com/madiedgar/legesher)
2. Edit files in `libs/i18n/language-packs/python/ru/legesher_i18n_python_ru/packs/`
3. Submit a pull request

Translation guidelines:

- Keep translations concise and commonly used
- Maintain consistency with existing translations
- Follow Russian programming terminology conventions
- Test with real code examples

## License

Apache License 2.0 - See [LICENSE](../../../LICENSE) for details.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.
