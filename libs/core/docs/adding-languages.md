# Adding Support for New Programming Languages

This guide explains how to extend Legesher to support new programming languages
beyond Python using the language abstraction interface introduced in CORE-415.

## Architecture Overview

Legesher's translator abstraction consists of:

1. **Translator Protocol** - Interface defining required methods
2. **Factory Function** - `create_translator()` for instantiation
3. **Environment Configuration** - User preferences via `LEGESHER_USE_TREE_SITTER`
4. **Language-Specific Implementations** - Per-language translator classes

## Step 1: Implement Translator Protocol

Create a new translator class that implements the `Translator` Protocol with all 7 required methods:

```python
from pathlib import Path
from typing import Optional, Union
from legesher_core.types import Translator, CulturalCommentMetadata

class TypeScriptTranslator:
    """TreeSitter-based translator for TypeScript."""

    def __init__(
        self,
        keyword_map: dict,
        builtin_map: dict,
        ts_version: str = "5.0"
    ):
        self.keyword_map = keyword_map
        self.builtin_map = builtin_map
        self.ts_version = ts_version
        # Initialize tree-sitter-typescript parser

    def translate_code(
        self,
        source_code: str,
        source_lang: str = "en",
        target_lang: str = "es",
        return_metadata: bool = False
    ) -> Union[str, tuple[str, CulturalCommentMetadata]]:
        """Translate TypeScript code between languages."""
        # Implementation using tree-sitter-typescript
        pass

    def translate_file(self, file_path: Path, target_lang: str) -> str:
        """Translate a TypeScript file."""
        pass

    def reverse(self) -> "TypeScriptTranslator":
        """Create reverse translator."""
        pass

    @classmethod
    def from_language_pack(
        cls,
        language: str,
        python_version: Optional[str] = None
    ) -> "TypeScriptTranslator":
        """Load from language pack."""
        pass

    @classmethod
    def list_available_languages(cls) -> list[tuple[str, str]]:
        """List available language packs."""
        pass

    def get_pack_info(self) -> dict[str, Union[str, int]]:
        """Get loaded pack information."""
        pass
```

## Step 2: Update Factory Function

Add the language to `create_translator()` in `libs/core/legesher_core/language_interface.py`:

```python
def create_translator(
    programming_language: str,
    keyword_map: dict,
    builtin_map: dict | None = None,
    python_version: str = "3.13",
    use_tree_sitter: bool | None = None,
) -> Translator:
    if programming_language == "python":
        # ... existing Python logic
    elif programming_language == "typescript":
        # Only tree-sitter supported for TypeScript
        return TypeScriptTranslator(
            keyword_map=keyword_map,
            builtin_map=builtin_map,
            ts_version=python_version  # Reuse version param
        )
    else:
        raise ValueError(f"Unsupported language: {programming_language}")
```

Also update `get_supported_languages()`:

```python
def get_supported_languages() -> dict[str, list[str]]:
    return {
        "python": ["token", "tree-sitter"],
        "typescript": ["tree-sitter"],  # Only tree-sitter for TS
    }
```

## Step 3: Create Language Packs

Follow the language pack structure in `legesher-i18n`:

```yaml
# libs/i18n/language_packs/typescript/es-typescript-5.0.yml
language: es
programming_language: typescript
version: "5.0"
keywords:
  const: "constante"
  let: "variable"
  function: "funcion"
  class: "clase"
  interface: "interfaz"
  type: "tipo"
  # ... all TypeScript keywords

builtins:
  console: "consola"
  Array: "Arreglo"
  # ... TypeScript built-ins
```

## Step 4: Add Tests

Create a test suite in `libs/core/tests/typescript/`:

```python
# tests/typescript/test_typescript_translator.py
import pytest
from legesher_core import create_translator
# Keyword/builtin maps are loaded from language pack YAML files via conftest.py fixtures
# See libs/core/tests/conftest.py for the pattern

def test_typescript_basic_translation():
    translator = create_translator(
        "typescript",
        TYPESCRIPT_KEYWORDS,
        TYPESCRIPT_BUILTINS
    )

    code = "const hello = (): string => 'Hello';"
    result = translator.translate_code(code, "en", "es")

    assert "constante" in result
```

Add to protocol conformance tests:

```python
# tests/unit/test_translator_protocol.py
@pytest.fixture(params=[
    TokenTranslator,
    TreeSitterTranslator,
    TypeScriptTranslator  # Add new translator
], ids=["token", "tree-sitter", "typescript"])
def translator_class(request):
    return request.param
```

## Step 5: Add Performance Benchmarks

Create benchmarks in `tests/benchmarks/test_typescript_performance.py`:

```python
import pytest
from legesher_core import create_translator

TYPESCRIPT_CODE = """
interface User {
    name: string;
    age: number;
}

const greet = (user: User): string => {
    return `Hello, ${user.name}`;
};
"""

def test_benchmark_typescript(benchmark):
    translator = create_translator("typescript", TS_KEYWORDS, TS_BUILTINS)
    result = benchmark(translator.translate_code, TYPESCRIPT_CODE, "en", "es")
    assert "interfaz" in result
```

## Step 6: Update Documentation

Update the following files:

### README.md

```markdown
## Supported Languages

- **Python**: Token-based and TreeSitter (production-ready)
- **TypeScript**: TreeSitter only (Phase 2C) ✨ NEW
```

### CLAUDE.md

```markdown
**Future Languages**: TypeScript support available (CORE-421-427)
```

### Package exports in `__init__.py`

```python
from .typescript.translator import TypeScriptTranslator

__all__ = [
    # ... existing
    "TypeScriptTranslator",
]
```

## Testing Checklist

Before submitting a new language:

- [ ] Translator implements all 7 Protocol methods
- [ ] Protocol conformance tests pass (parametrized)
- [ ] Language-specific edge cases covered
- [ ] Round-trip translation validated
- [ ] Performance benchmarks added
- [ ] Language packs created for ≥3 languages
- [ ] Factory function updated
- [ ] Documentation updated
- [ ] CI tests pass

## Example: TypeScript (Planned)

TypeScript support is tracked in the internal roadmap as CORE-421 through CORE-427
and would follow this same pattern. It is not currently scheduled.

**Planned tickets**:

- CORE-421: TypeScript grammar integration
- CORE-422: TypeScript language packs (ES, AR, ZH)
- CORE-423: TypeScript translator implementation
- CORE-424: Type system translation
- CORE-425: Interface/type declarations
- CORE-426: Testing & benchmarks
- CORE-427: Documentation

## Questions?

- See [complete-architecture-guide.md](../../private-working-memory/planning/architecture/complete-architecture-guide.md)
- Open discussion in Linear workspace
- Reference CORE-415 implementation for patterns

## Advanced: Tree-sitter Grammar

For tree-sitter based translators:

1. **Install grammar**: `tree-sitter-{language}` package
2. **Define queries**: Keyword patterns, AST node matching
3. **Implement traversal**: Recursive node translation
4. **Handle edge cases**: Comments, strings, identifiers

See `libs/core/legesher_core/tree_sitter/` for Python implementation example.
