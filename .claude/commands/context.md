<!--
SOURCES:
- Knowledge transfer patterns for documentation
- Explaining technical context for open source contributors
- Onboarding documentation best practices
-->

# Provide Context: $ARGUMENTS

**Goal**: Provide comprehensive technical context for $ARGUMENTS to help contributors (or future you) understand the codebase deeply.

## Instructions

You are creating context documentation that explains not just *what* the code does, but *why* it exists, *how* it fits into the bigger picture, and *what* someone needs to know to work on it successfully.

This is for:
- Open source contributors at various skill levels
- Future you (6 months from now)
- Team members joining the project
- Anyone trying to understand architectural decisions

## Context Documentation Structure

### 1. Executive Summary ("TL;DR")

Start with a 2-3 sentence summary:

```markdown
## TL;DR

{What is this component/feature?}
{Why does it exist? What problem does it solve?}
{How does it fit into the larger system?}
```

### 2. Problem Statement ("The Why")

Explain the problem this solves:

**User Need**:
- What pain point does this address?
- What would happen without this?
- Who benefits from this?

**Technical Need**:
- What architectural problem does this solve?
- What constraints led to this design?
- What alternatives were considered?

**Example**:
```markdown
## Problem Statement

**User Need**: Developers want to code in their native language (Spanish, Arabic, etc.) instead of English. However, Python keywords are English-only. We need a way to translate code between languages while maintaining functionality.

**Technical Challenge**: Python's AST (Abstract Syntax Tree) expects English keywords. We can't just find-and-replace strings because:
- Keywords in strings shouldn't be translated ("print('if')" should stay as-is)
- Comments need different handling than code
- Must work with Python's existing toolchain (IDEs, linters, etc.)

**Solution**: A token-based transformer that operates at the lexical level before AST parsing, converting native language keywords to English for the Python interpreter.
```

### 3. High-Level Architecture ("The What")

Explain the solution architecture:

**Components**:
- What are the main parts?
- How do they interact?
- What are the boundaries/interfaces?

**Data Flow**:
- What comes in? (inputs)
- What goes out? (outputs)
- How does data transform along the way?

**Diagram** (ASCII art is fine):
```
User Code (Spanish)
    ↓
Token Stream
    ↓
Keyword Translator
    ↓
Python AST
    ↓
Python Bytecode
```

### 4. Key Concepts ("The Building Blocks")

Define domain-specific terms and concepts:

```markdown
## Key Concepts

### Language Pack
A YAML file containing keyword mappings (e.g., "if" → "si" in Spanish).
Contains: keywords, builtins, metadata, optional inheritance chain.

### Version-Aware Loading
Different Python versions have different keywords:
- Python 3.10 added: `match`, `case`
- Python 3.11 added: `except*`
- Python 3.12 added: `type`

Language packs inherit from earlier versions to avoid duplication.

### Token-Based Translation
Operating at the tokenization level (before parsing) allows us to:
- Distinguish code from strings from comments
- Preserve Python's structure
- Work with standard Python tools
```

### 5. Design Decisions ("The How & Why We Chose This Way")

Document key decisions with rationale:

```markdown
## Design Decisions

### Decision 1: YAML for Language Packs

**Alternatives Considered**:
- JSON: Machine-readable but not human-friendly
- Python dicts: Requires Python knowledge, hard for translators
- TOML: Good but less common than YAML

**Chosen: YAML**

**Rationale**:
- Human-readable: Translators (non-programmers) can edit
- Comments: Can add notes for translators
- Wide tooling: Editors have good YAML support
- Standard: Used by many i18n projects

**Trade-offs**:
- YAML parsing is slower than JSON (mitigated with caching)
- YAML has quirks (Norway problem: "NO" → false)

### Decision 2: Git Filter for Storage

**Problem**: Should we store files in native language or English?

**Chosen: Store in English, show in native language**

**Rationale**:
- Git diffs make sense: English keywords are stable
- Collaboration: All developers see same diffs
- Tools: Git hooks, CI, code review work as expected
- Rollback: Can always revert to English version

**How it works**:
- Git "clean" filter: Translates native → English on commit
- Git "smudge" filter: Translates English → native on checkout
- Developer sees native language, git sees English

**Trade-offs**:
- Setup complexity: Users must configure git filters
- Merge conflicts: Only see English in conflict resolution
```

### 6. Code Organization ("Where Things Live")

Map out the codebase:

```markdown
## Code Organization

### Package Structure
```
libs/i18n/
├── legesher_i18n/
│   ├── __init__.py              # Public API
│   ├── pack_loader.py           # Load language packs
│   ├── version_detector.py      # Detect Python version
│   ├── version_index.py         # Parse version metadata
│   └── schema_validator.py      # Validate YAML schemas
├── languages/
│   └── python/
│       ├── version-index.yml    # Python keyword changes
│       └── 3.{10,11,12,13}/     # Version-specific packs
│           ├── es.yml           # Spanish
│           └── ar.yml           # Arabic
└── tests/
    ├── test_pack_loader.py      # Unit tests
    └── fixtures/                # Test data
```

### Key Files

**pack_loader.py**
- Purpose: Load language packs with inheritance
- Entry point: `LanguagePackLoader.load(language, target, version)`
- Dependencies: version_index, schema_validator
- Used by: legesher-core (for translation)

**version_detector.py**
- Purpose: Auto-detect project's Python version
- Priority: pyproject.toml → .python-version → runtime
- Used by: CLI, IDE extensions

### 7. Dependencies ("What This Relies On")

**Internal Dependencies** (within monorepo):
- `legesher-core`: Uses language packs for translation

**External Dependencies**:
- `pyyaml`: Parse YAML language pack files
- `pydantic`: Validate schemas, ensure type safety
- `pytest`: Testing framework

**Python Standard Library**:
- `pathlib`: Cross-platform file paths
- `sys`: Runtime version detection
- `typing`: Type hints

### 8. Testing Strategy ("How We Ensure Quality")

```markdown
## Testing Strategy

### Test Pyramid
- **Unit Tests (70%)**: Individual functions/classes
- **Integration Tests (20%)**: Component interactions
- **End-to-End Tests (10%)**: Full workflows

### Critical Test Cases

**Version Detection**:
- ✓ Detects from pyproject.toml `requires-python`
- ✓ Detects from .python-version file
- ✓ Falls back to runtime `sys.version_info`
- ✓ Handles missing/malformed files
- ✓ Respects detection priority order

**Pack Loading**:
- ✓ Loads simple pack (no inheritance)
- ✓ Loads with single-level inheritance
- ✓ Loads with multi-level inheritance (3.13 → 3.12 → 3.11 → 3.10)
- ✓ Merges keywords correctly (child overrides parent)
- ✓ Prevents circular inheritance
- ✓ Sanitizes file paths (prevents `../../../etc/passwd`)
- ✓ Caches loaded packs for performance

### Running Tests
```bash
# All tests
cd libs/i18n && uv run pytest -v

# With coverage
uv run pytest --cov=legesher_i18n --cov-report=term-missing

# Specific test file
uv run pytest tests/test_pack_loader.py -v

# Specific test
uv run pytest tests/test_pack_loader.py::test_inheritance -v
```
```

### 9. Common Patterns ("How We Do Things Here")

```markdown
## Common Patterns

### Error Handling Pattern

We follow "fail fast" with clear error messages:

```python
# Pattern: Validate inputs immediately
def load_pack(file_path: Path) -> LanguagePack:
    # 1. Check preconditions
    if not file_path.exists():
        raise PackNotFoundError(f"Language pack not found: {file_path}")

    # 2. Validate input
    if file_path.suffix != '.yml':
        raise PackValidationError(f"Expected .yml file, got: {file_path.suffix}")

    # 3. Process with error handling
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise PackValidationError(f"Invalid YAML in {file_path}: {e}")

    # 4. Validate schema
    validate_pack_schema(data)  # Raises if invalid

    # 5. Return typed result
    return LanguagePack(**data)
```

### Caching Pattern

We cache expensive operations:

```python
from functools import lru_cache

class LanguagePackLoader:
    @lru_cache(maxsize=128)  # Cache up to 128 packs
    def load(self, language: str, target: str, version: str) -> LanguagePack:
        # Expensive: file I/O, YAML parsing, validation
        # Called frequently: every file translation
        # Solution: Cache results by (language, target, version) tuple
        ...
```

### Type Hint Pattern

We use type hints everywhere:

```python
# Use specific types, not generic
from pathlib import Path  # Not str
from typing import Optional, Dict, List  # Be explicit

def load_pack(
    file_path: Path,  # Not str - type safety
    version: Optional[str] = None  # Explicit optional
) -> LanguagePack:  # Clear return type
    ...
```
```

### 10. For Contributors ("How to Get Started")

```markdown
## For Contributors

### First Time Setup

1. **Clone and Install**:
   ```bash
   git clone https://github.com/yourusername/legesher.git
   cd legesher
   uv install
   ```

2. **Verify Setup**:
   ```bash
   uv run python -c "import legesher_i18n; print('Success!')"
   ```

3. **Run Tests**:
   ```bash
   cd libs/i18n && uv run pytest -v
   ```

### Making Changes

1. **Read Architecture Docs**: Check `docs/src/content/docs/architecture/`
2. **Find an Issue**: Look for "good first issue" label
3. **Ask Questions**: Open a discussion, we're friendly!
4. **Follow Patterns**: Look at existing code for examples
5. **Write Tests**: TDD preferred, test coverage required
6. **Update Docs**: README and docstrings

### Common Contributor Questions

**Q: I want to add a new language pack. Where do I start?**
A: Check `docs/guides/creating-language-packs.md`. Add to `libs/i18n/languages/python/{version}/{language}.yml`.

**Q: How do I run just my tests?**
A: `uv run pytest tests/test_your_file.py -v`

**Q: The code uses {unfamiliar concept}. Where can I learn?**
A: Check the "Learning Resources" section below, or ask in discussions!

**Q: Can I refactor this code? It seems overcomplicated.**
A: Maybe! Open an issue first to discuss. There might be reasons for the current design.
```

### 11. Learning Resources

```markdown
## Learning Resources

### Understanding This Codebase

- [Complete Architecture Guide](../docs/architecture/complete-architecture-guide.md)
- [Implementation Roadmap](../docs/architecture/implementation-roadmap.md)
- [MLCP Specification](../docs/specifications/mlcp-v1.md)

### Python Concepts Used

- **Dataclasses**: https://realpython.com/python-data-classes/
- **Type Hints**: https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
- **Context Managers**: https://realpython.com/python-with-statement/
- **Decorators (@lru_cache)**: https://realpython.com/primer-on-python-decorators/

### Domain Knowledge

- **Python AST**: https://docs.python.org/3/library/ast.html
- **Python Tokenizer**: https://docs.python.org/3/library/tokenize.html
- **Git Filters**: https://git-scm.com/docs/gitattributes#_filter

### Similar Projects

- **gettext** (i18n standard): https://www.gnu.org/software/gettext/
- **Tree-sitter** (parsing library): https://tree-sitter.github.io/tree-sitter/
```

### 12. Troubleshooting

```markdown
## Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'legesher_i18n'`**

**Cause**: UV environment not activated or package not installed.

**Fix**:
```bash
uv install  # Reinstall all packages
uv run python -c "import legesher_i18n"  # Use uv run prefix
```

**Issue: `PackNotFoundError: Language pack not found`**

**Cause**: Language pack file doesn't exist or wrong path.

**Fix**:
- Check path: `ls libs/i18n/languages/python/3.13/es.yml`
- Verify language code: "es" not "esp"
- Check version: "3.13" not "3.13.0"

**Issue: Tests fail with `YAML Error`**

**Cause**: Syntax error in YAML file.

**Fix**:
- Validate YAML: https://yamlchecker.com/
- Check indentation (YAML is whitespace-sensitive)
- Look for tabs (use spaces only)
```

## Deliverable

Create comprehensive context documentation for $ARGUMENTS that:

1. Explains the problem and solution
2. Describes architecture and key concepts
3. Documents design decisions with rationale
4. Maps code organization
5. Explains testing strategy
6. Shows common patterns
7. Provides getting-started guide for contributors
8. Includes learning resources
9. Anticipates and answers questions

**Remember**: Good context documentation answers "why" more than "what". Code shows what; docs explain why.