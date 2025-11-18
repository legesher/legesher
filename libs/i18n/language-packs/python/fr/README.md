# legesher-i18n-python-fr

French (Français) language pack for Python in Legesher.

## Overview

This package provides French translations for Python keywords and built-in functions, enabling developers to write
Python code in French with full Legesher support.

## Supported Python Versions

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

## Installation

```bash
# Install with legesher-i18n
uv pip install legesher-i18n legesher-i18n-python-fr

# Or with pip
pip install legesher-i18n legesher-i18n-python-fr
```

## Usage

The language pack is automatically discovered by `legesher-i18n` when installed:

```python
from legesher_i18n import LanguagePackLoader

# Load French pack for Python 3.12
loader = LanguagePackLoader()
pack = loader.load("fr", "python", "3.12")

# Use translated keywords
print(pack.keywords["def"])     # "def"
print(pack.keywords["class"])   # "class"
print(pack.keywords["return"])  # "return"
```

## Example Code

```python
# Write Python in French!
def saluer(nom):
    return f"Bonjour, {nom}!"

class Personne:
    def __init__(self, nom):
        self.nom = nom

    def presenter(self):
        imprimer(f"Mon nom est {self.nom}")
```

## Translation Coverage

This pack provides translations for:

- **Keywords**: All Python keywords (def, class, if, for, etc.)
- **Built-ins**: Common built-in functions (print, len, range, etc.)
- **Operators**: Logical operators (and, or, not)
- **Constants**: True, False, None

## Version Inheritance

Language packs use inheritance to minimize duplication:

- `3.10.yml` - Complete Python 3.10 translations
- `3.11.yml` - Extends 3.10, adds new keywords (e.g., `except*`)
- `3.12.yml` - Extends 3.11, adds `type` keyword
- `3.13.yml` - Extends 3.12 (no new keywords)

## Contributing

To contribute translations or improvements:

1. Fork the [Legesher repository](https://github.com/madiedgar/legesher)
2. Edit files in `libs/i18n/language-packs/python/fr/legesher_i18n_python_fr/packs/`
3. Submit a pull request

Translation guidelines:

- Use standard French terminology
- Prefer commonly used programming terms
- Maintain consistency with existing translations
- Test with various code editors

## License

MIT License - See [LICENSE](../../LICENSE) for details.

## Related Packages

- [legesher-i18n](../i18n) - Core language pack system
- [legesher-i18n-python-es](../i18n-python-es) - Spanish language pack
- [legesher-i18n-python-ar](../i18n-python-ar) - Arabic language pack
- [legesher-core](../core) - Translation engine

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.
