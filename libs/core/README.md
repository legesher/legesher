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
# Result: "definir greet():\n    imprimir('Hello!')"
```

## Testing

```bash
uv run pytest tests/ --cov=legesher_core
```

**Results**: 86 tests passing, 91% coverage

## License

MIT License
