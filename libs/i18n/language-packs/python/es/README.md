# legesher-i18n-python-es

Spanish (Español) language pack for Python in Legesher.

## Overview

This package provides Spanish translations for Python keywords and built-in functions, enabling developers to write
Python code in Spanish.

## Supported Python Versions

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

## Installation

```bash
# Install with legesher-i18n
uv pip install legesher-i18n legesher-i18n-python-es

# Or with pip
pip install legesher-i18n legesher-i18n-python-es
```

## Usage

The language pack is automatically discovered by `legesher-i18n` when installed:

```python
from legesher_i18n import LanguagePackLoader

# Load Spanish pack for Python 3.12
loader = LanguagePackLoader()
pack = loader.load("es", "python", "3.12")

# Use translated keywords
print(pack.keywords["def"])     # "definir"
print(pack.keywords["class"])   # "clase"
print(pack.keywords["return"])  # "retornar"
```

## Example Code

```python
# Write Python in Spanish!
definir saludar(nombre):
    retornar f"¡Hola, {nombre}!"

clase Persona:
    definir __init__(yo, nombre):
        yo.nombre = nombre

    definir presentar(yo):
        imprimir(f"Mi nombre es {yo.nombre}")
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
- `3.11.yml` - Extends 3.10, adds new keywords (e.g., `except*: excepto*`)
- `3.12.yml` - Extends 3.11, adds `type: tipo`
- `3.13.yml` - Extends 3.12 (no new keywords)

## Contributing

To contribute translations or improvements:

1. Fork the [Legesher repository](https://github.com/madiedgar/legesher)
2. Edit files in `libs/i18n-python-es/legesher_i18n_python_es/packs/`
3. Submit a pull request

Translation guidelines:

- Keep translations concise and commonly used
- Maintain consistency with existing translations
- Follow Spanish programming terminology conventions
- Test with real code examples

## License

MIT License - See [LICENSE](../../LICENSE) for details.

## Related Packages

- [legesher-i18n](../i18n) - Core language pack system
- [legesher-i18n-python-ar](../i18n-python-ar) - Arabic language pack
- [legesher-core](../core) - Translation engine

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.
