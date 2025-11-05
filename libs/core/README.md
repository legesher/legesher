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

## Metadata Tracking

Legesher Core includes a comprehensive metadata tracking system that records translation history and git operations for audit trails and debugging.

### What is Metadata?

The metadata system tracks:

- Original language of each file
- Translation operations performed
- Git filter operations (clean/smudge)
- Python version and translator version used
- Timestamps and commit SHAs

Metadata is stored in `.legesher/metadata/` as YAML files that mirror your source tree structure.

### Metadata Schema

Each file gets a metadata file at `.legesher/metadata/<file_path>.yml`:

```yaml
file: src/calculator.py
original_language: es
canonical_language: en
python_version: "3.13"
created_at: "2025-11-06T10:30:00Z"
updated_at: "2025-11-06T14:35:00Z"
translations:
  - language: en
    method: token_transformer
    timestamp: "2025-11-06T10:30:00Z"
    commit_sha: abc123
    translator_version: "0.1.0"
    python_version: "3.13"
history:
  - action: clean
    from_language: es
    to_language: en
    timestamp: "2025-11-06T10:35:00Z"
    commit_sha: def456
```

### Using Metadata in Code

```python
from pathlib import Path
from legesher_core.metadata import MetadataManager
from legesher_core.types import TranslationRecord, HistoryEntry

# Initialize manager
repo_root = Path("/path/to/repo")
manager = MetadataManager(repo_root)

# Create metadata for new file
metadata = manager.create_metadata(
    Path("src/calculator.py"),
    original_language="es",
    python_version="3.13"
)

# Read existing metadata
metadata = manager.get_metadata(Path("src/calculator.py"))
if metadata:
    print(f"Original language: {metadata['original_language']}")
    print(f"Translations: {len(metadata['translations'])}")

# Record translation operation
record: TranslationRecord = {
    "language": "en",
    "method": "token_transformer",
    "timestamp": "2025-11-06T10:30:00Z",
    "commit_sha": "a91228a",
    "translator_version": "0.1.0",
    "python_version": "3.13"
}
manager.record_translation(Path("src/calculator.py"), record)

# Add history entry (git operation)
entry: HistoryEntry = {
    "action": "clean",
    "from_language": "es",
    "to_language": "en",
    "timestamp": "2025-11-06T10:30:00Z",
    "commit_sha": "a91228a"
}
manager.add_history_entry(Path("src/calculator.py"), entry)

# List all metadata files
metadata_files = manager.list_metadata_files()
print(f"Tracking {len(metadata_files)} files")

# Validate metadata integrity
is_valid = manager.validate_metadata(Path("src/calculator.py"))
```

### Privacy & Security

- **No source code stored**: Metadata contains only file paths, languages, timestamps
- **Local-first**: All metadata stored locally in `.legesher/metadata/`
- **No cloud required**: Never requires external services
- **Optional git tracking**: Can exclude metadata from git if desired
- **Atomic writes**: All file operations use atomic write-then-rename for safety

### API Reference

See the [metadata module documentation](legesher_core/metadata.py) for complete API details.

## License

MIT License
