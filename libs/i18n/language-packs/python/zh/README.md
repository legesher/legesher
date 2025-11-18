# legesher-i18n-python-zh

Chinese (Simplified - 简体中文) language pack for Python in Legesher.

## Overview

This package provides Chinese (Simplified) translations for Python keywords and built-in functions, enabling developers to write
Python code in Chinese with full Legesher support.

## Supported Python Versions

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

## Installation

```bash
# Install with legesher-i18n
uv pip install legesher-i18n legesher-i18n-python-zh

# Or with pip
pip install legesher-i18n legesher-i18n-python-zh
```

## Usage

The language pack is automatically discovered by `legesher-i18n` when installed:

```python
from legesher_i18n import LanguagePackLoader

# Load Chinese pack for Python 3.12
loader = LanguagePackLoader()
pack = loader.load("zh", "python", "3.12")

# Use translated keywords
print(pack.keywords["def"])     # "定义"
print(pack.keywords["class"])   # "类"
print(pack.keywords["return"])  # "返回"
```

## Example Code

```python
# Write Python in Chinese!
定义 问候(名字):
    返回 f"你好，{名字}！"

类 人:
    定义 __初始化__(自己, 名字):
        自己.名字 = 名字

    定义 介绍(自己):
        打印(f"我的名字是 {自己.名字}")
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
2. Edit files in `libs/i18n-python-zh/legesher_i18n_python_zh/packs/`
3. Submit a pull request

Translation guidelines:

- Use simplified Chinese characters (Simplified Chinese)
- Prefer commonly used programming terminology
- Maintain consistency with existing translations
- Test with various code editors supporting Chinese text

## License

MIT License - See [LICENSE](../../LICENSE) for details.

## Related Packages

- [legesher-i18n](../i18n) - Core language pack system
- [legesher-i18n-python-es](../i18n-python-es) - Spanish language pack
- [legesher-i18n-python-ar](../i18n-python-ar) - Arabic language pack
- [legesher-core](../core) - Translation engine

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.
