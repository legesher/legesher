# legesher-i18n-python-ar

Arabic (العربية) language pack for Python in Legesher.

## Overview

This package provides Arabic translations for Python keywords and built-in functions, enabling developers to write
Python code in Arabic with right-to-left (RTL) support.

## Supported Python Versions

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

## Installation

```bash
# Install with legesher-i18n
uv pip install legesher-i18n legesher-i18n-python-ar

# Or with pip
pip install legesher-i18n legesher-i18n-python-ar
```

## Usage

The language pack is automatically discovered by `legesher-i18n` when installed:

```python
from legesher_i18n import LanguagePackLoader

# Load Arabic pack for Python 3.12
loader = LanguagePackLoader()
pack = loader.load("ar", "python", "3.12")

# Use translated keywords
print(pack.keywords["def"])     # "تعريف"
print(pack.keywords["class"])   # "صنف"
print(pack.keywords["return"])  # "إرجاع"
```

## Example Code

```python
# Write Python in Arabic!
تعريف تحية(اسم):
    إرجاع f"!مرحبا، {اسم}"

صنف شخص:
    تعريف __init__(نفسي, اسم):
        نفسي.اسم = اسم

    تعريف تقديم(نفسي):
        طباعة(f"اسمي {نفسي.اسم}")
```

## RTL Considerations

This pack is designed for right-to-left (RTL) text direction:

- Arabic keywords flow RTL
- IDE integration should respect RTL direction
- Comments and strings maintain RTL formatting
- Variable names can be in Arabic

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
2. Edit files in `libs/i18n-python-ar/legesher_i18n_python_ar/packs/`
3. Submit a pull request

Translation guidelines:

- Use Modern Standard Arabic (MSA) for consistency
- Prefer commonly used programming terms
- Maintain consistency with existing translations
- Consider RTL text flow in all translations
- Test with RTL-capable editors

## License

MIT License - See [LICENSE](../../LICENSE) for details.

## Related Packages

- [legesher-i18n](../i18n) - Core language pack system
- [legesher-i18n-python-es](../i18n-python-es) - Spanish language pack
- [legesher-core](../core) - Translation engine

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.
