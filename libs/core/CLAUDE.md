# legesher-core - Claude Code Guide

This file provides guidance for working with the `legesher-core` package.

## Package Overview

**Version**: 0.4.0
**Status**: Production-Ready (Pre-Beta)
**Python**: >=3.10,<4.0

The core translation engine providing two complete translator backends for converting Python code
between natural languages.

## Key Capabilities

- **Two Translator Backends**: TokenTranslator (~140μs) and TreeSitterTranslator (~160μs)
- **Python Keywords**: Full support for Python 3.10 keyword set (37 keywords)
- **Reserved Words** (CORE-710): `self`/`cls` translated deterministically via
  the language pack's `reserved_words` section. Both translators accept an
  optional `reserved_word_map` constructor parameter; dispatch order is
  `keyword → builtin → reserved_word → IdentifierMap`. The extractor skips
  self/cls entirely so they don't reach the LLM.
- **51 Languages**: Via language pack system
- **Perfect Round-Trip**: EN→ES→EN translation is byte-identical
- **RTL Support**: Arabic, Hebrew, Persian, Urdu with UTF-8 encoding
- **Git Integration**: Clean/smudge filters with metadata tracking
- **Cultural Comments**: MLCP protocol support

## Directory Structure

```text
libs/core/
├── legesher_core/
│   ├── __init__.py           # Public API exports
│   ├── transformer.py        # TokenTranslator implementation
│   ├── tree_sitter/          # TreeSitterTranslator implementation
│   ├── language_interface.py # create_translator() factory and Protocol
│   ├── git_filter.py         # Git clean/smudge filters
│   ├── metadata.py           # MetadataManager for tracking
│   ├── types.py              # Type definitions
│   └── utils.py              # Utility functions
├── tests/
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── benchmarks/           # Performance benchmarks
└── pyproject.toml
```

## Key APIs

### Using Language Packs (Recommended)

```python
from legesher_core import TokenTranslator

# Create from language pack (auto-detects Python version)
translator = TokenTranslator.from_language_pack("es")

# Translate code
code = "def greet():\n    print('Hello!')"
spanish = translator.translate_code(code)

# Reverse translation
es_to_en = translator.reverse()
back = es_to_en.translate_code(spanish)
```

### Choosing Backend

```python
from legesher_core import create_translator

# Default: TokenTranslator
translator = create_translator("python", keyword_map, builtin_map)

# Tree-sitter backend
translator = create_translator("python", keyword_map, builtin_map, use_tree_sitter=True)

# CORE-710: with reserved_word_map for self/cls translation
translator = create_translator(
    "python", keyword_map, builtin_map,
    reserved_word_map={"self": "propio", "cls": "clase"},
)
# When using create_translator_from_language_pack(), the reserved_words
# section is auto-loaded from the pack — no explicit kwarg needed.

# Or via environment variable
# export LEGESHER_USE_TREE_SITTER=true
```

### Metadata Tracking

```python
from legesher_core.metadata import MetadataManager

manager = MetadataManager(repo_root)
metadata = manager.create_metadata(path, original_language="es")
manager.record_translation(path, record)
```

## Testing

```bash
cd libs/core

# Run all tests
uv run pytest tests/ -v

# Run specific category
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v

# Run benchmarks
uv run pytest tests/benchmarks/ --benchmark-only

# With coverage
uv run pytest tests/ --cov=legesher_core --cov-report=html
```

## Dependencies

- `click>=8.0.0` - CLI framework
- `legesher-i18n` - Language pack loading
- `tree-sitter>=0.20.4` - AST parsing
- `tree-sitter-python>=0.21.0` - Python grammar

## Common Tasks

### Adding a New Translator Feature

1. Implement in both `transformer.py` (Token) and `tree_sitter/` (TreeSitter)
2. Update Protocol in `language_interface.py` if interface changes
3. Add tests in both `tests/unit/` and `tests/integration/`
4. Run benchmarks to ensure performance is maintained

### Debugging Translation Issues

1. Use `translator.translate_code(code, debug=True)` for verbose output
2. Check metadata at `.legesher/metadata/` for history
3. Compare TokenTranslator vs TreeSitterTranslator output

## Related Issues

- CORE-415: Language abstraction interface
- CORE-421: TypeScript support (in backlog)
