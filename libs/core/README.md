# Legesher Core

Production-ready translation engine for multilingual Python with two complete translator backends.

**Status**: Pre-Beta | **Python**: 3.10-3.14 | **Version**: see `pyproject.toml`

## Features

- **Two Translator Backends**: Choose between token-based or tree-sitter AST-based translation
- **Complete Keyword Translation**: All 39 Python keywords across 3.10-3.14
- **51 Languages Supported**: Via independent language pack system
- **Perfect Formatting**: Preserves indentation, comments, docstrings
- **Round-Trip**: EN→ES→EN is byte-identical for the corpus the sweep covers; the known exceptions are listed as
  strict xfails in `libs/mcp/tests/test_roundtrip_sweep.py`
- **RTL Languages**: Arabic, Hebrew, Persian, and Urdu translate like any other language. Values are stored in
  logical order with no bidi control characters, so display order is the terminal's or editor's to decide
- **Fast**: both backends translate a small module in well under a millisecond; run
  `pytest libs/core/tests/benchmarks` to measure on your own hardware
- **Graceful Degradation**: Handles incomplete code and syntax errors
- **Git Integration**: Complete clean/smudge filter implementation with metadata tracking
- **Cultural Comments**: MLCP protocol support for contextual annotations

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
# [('am', 'AM'), ('ar', 'AR'), ('bn', 'BN'), ... (51 languages)]
```

### Choosing a Translator Backend

Legesher Core provides **two complete translator implementations**:

#### TokenTranslator (Default)

- Token-based translation
- Fast and simple, and the quicker of the two on the bundled benchmark
- Pure standard library — no C extensions required
- Perfect for most use cases
- Best compatibility with incomplete code

```python
from legesher_core import TokenTranslator

translator = TokenTranslator.from_language_pack("es")
```

#### TreeSitterTranslator (AST-based)

- Tree-sitter AST-based translation
- Better error handling for syntax edge cases
- Supports incremental parsing
- Requires the optional `treesitter` extra (tree-sitter C extensions):

```bash
pip install 'legesher-core[treesitter]'
```

Without the extra, `import legesher_core` and the token path still work;
accessing `TreeSitterTranslator` or `LLMTranslator` raises an `ImportError`
that names the extra. This keeps minimal installs and browser Python runtimes
(where C extensions are unavailable) on the pure-stdlib token path.

```python
from legesher_core import create_translator

# Create tree-sitter translator
translator = create_translator("python", keyword_map, builtin_map, use_tree_sitter=True)

# Or use environment variable
import os
os.environ["LEGESHER_USE_TREE_SITTER"] = "true"
translator = create_translator("python", keyword_map, builtin_map)
```

Both translators provide identical APIs and produce identical output. The benchmark suite in
`tests/benchmarks/` compares them if you want numbers for your own hardware.

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

**Test Categories:**

- Unit tests: Token translation, AST parsing, metadata tracking, git filters
- Integration tests: Round-trip translation, language pack loading, cultural comments
- Benchmarks: Performance comparison between TokenTranslator and TreeSitterTranslator

## Metadata Tracking

Legesher Core includes a comprehensive metadata tracking system that records
translation history and git operations for audit trails and debugging.

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

Apache License 2.0
