# Legesher Core

Token-based translation engine for multilingual Python.

## Features

- **Complete Keyword Translation**: All 35 Python 3.13 keywords
- **Multiple Languages**: Spanish and Arabic support built-in
- **Perfect Formatting**: Preserves indentation, comments, docstrings
- **Lossless Round-Trip**: EN→ES→EN translation is byte-identical
- **RTL Language Support**: Arabic, Hebrew with UTF-8 encoding
- **Fast**: Processes files in milliseconds
- **Graceful Degradation**: Handles incomplete code and syntax errors
- **Well Tested**: 86 tests with 91% coverage

## Quick Start

### Using Language Packs (Recommended)

```python
from legesher_core import TokenTranslator

# Create translator from language pack (auto-detects Python version)
translator = TokenTranslator.from_language_pack("es")

# Translate code
code = "def greet():\n    print('Hello!')"
spanish = translator.translate_code(code)
# Result: "definir greet():\n    imprimir('Hello!')"

# Bidirectional translation
es_to_en = translator.reverse()
back_to_english = es_to_en.translate_code(spanish)

# List available languages
languages = TokenTranslator.list_available_languages()
# [('ar', 'Arabic'), ('es', 'Spanish')]
```

### Using Custom Maps (Legacy)

```python
from legesher_core import TokenTranslator

# Define translation maps
spanish_keywords = {"def": "definir", "return": "retornar"}
spanish_builtins = {"print": "imprimir", "len": "longitud"}

# Create translator
translator = TokenTranslator(spanish_keywords, spanish_builtins)

# Translate code
code = "def greet():\n    print('Hello!')"
spanish = translator.translate_code(code, "en", "es")
```

## Testing

### Run all tests

```bash
cd libs/core
uv run python -m pytest tests/ -v
```

### Run specific test file

```bash
cd libs/core
uv run python -m pytest tests/integration/test_pack_integration.py -v
```

### Run with coverage

```bash
cd libs/core
uv run python -m pytest tests/ --cov=legesher_core --cov-report=html
```

### Troubleshooting Test Runs

If you encounter "No module named pytest":

1. Ensure you're in the package directory (`libs/core`)
2. Run `uv sync` to install dependencies
3. Use `uv run python -m pytest` (not just `pytest`)

**Current Results**: 255 tests passing, 4 skipped

## License

MIT License
