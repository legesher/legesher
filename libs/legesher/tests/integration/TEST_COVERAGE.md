# CLI Integration Test Coverage

This document provides an overview of the comprehensive integration tests for the Legesher CLI.

## Test File

**Location:** `libs/legesher/tests/integration/test_cli_integration.py`

**Lines of Code:** ~1300+ lines
**Test Cases:** 30+ comprehensive integration tests
**Coverage Target:** 85%+ of integration paths

## Test Organization

### 1. TestSemanticEquivalence (CRITICAL)

**Purpose:** Verify translated code is semantically identical to original

| Test Case | Description | Verification Method |
|-----------|-------------|---------------------|
| `test_ast_semantic_equivalence_spanish` | Spanish → English AST equivalence | AST comparison |
| `test_bytecode_semantic_equivalence_spanish` | Spanish → English bytecode equivalence | Bytecode comparison |
| `test_round_trip_translation_preserves_semantics` | en → es → en preservation | AST comparison |
| `test_execution_equivalence_spanish` | Runtime behavior equivalence | Execution comparison |

**Key Helper Functions:**

- `assert_ast_equivalent()` - Compares AST structure
- `assert_bytecode_equivalent()` - Compares compiled bytecode
- `assert_code_executes_identically()` - Compares runtime execution

### 2. TestEndToEndTranslation

**Purpose:** Complete translation workflows

| Test Case | Language | Input Mode | Output Mode |
|-----------|----------|------------|-------------|
| `test_spanish_to_english_file_translation` | Spanish → English | File | File |
| `test_english_to_arabic_stdin_translation` | English → Arabic | stdin | File |
| `test_english_to_hindi_directory_translation` | English → Hindi | Directory | Directory |

**Coverage:**

- File translation workflows
- stdin/stdout handling
- Directory recursive translation
- All three language packs (es, ar, hi)

### 3. TestComplexCodePatterns

**Purpose:** Real-world Python code patterns

| Test Case | Pattern Tested |
|-----------|----------------|
| `test_translate_with_imports` | import statements, from imports |
| `test_translate_with_classes` | Class definitions, methods, properties |
| `test_translate_with_decorators` | @decorators, @wraps |
| `test_translate_with_control_flow` | if/elif/else, for, while, try/except/finally |
| `test_translate_with_context_managers` | with statements, as clauses |
| `test_translate_with_comprehensions` | List/dict/set comprehensions |

**Coverage:**

- All Python control flow keywords
- Object-oriented programming
- Functional programming patterns
- Exception handling
- Context managers
- Comprehensions

### 4. TestDirectoryOperations

**Purpose:** Directory translation operations

| Test Case | Scenario |
|-----------|----------|
| `test_directory_preserves_structure` | Complex nested directory tree |
| `test_directory_with_nested_subdirectories` | 4-level deep nesting |
| `test_directory_skips_non_py_files` | Mixed file types |
| `test_directory_handles_empty_directories` | No .py files warning |

**Coverage:**

- Directory structure preservation
- Nested subdirectories
- File filtering (.py only)
- Empty directory handling

### 5. TestRealLanguagePacks

**Purpose:** Integration with actual language pack files

| Test Case | Language | Keywords Tested |
|-----------|----------|-----------------|
| `test_all_spanish_keywords_work` | Spanish (es) | 16+ keywords |
| `test_all_arabic_keywords_work` | Arabic (ar) | 6+ keywords (RTL) |
| `test_all_hindi_keywords_work` | Hindi (hi) | 4+ keywords |
| `test_language_pack_not_found_error` | Invalid | Error handling |

**Coverage:**

- Spanish language pack (es)
- Arabic language pack (ar) with RTL support
- Hindi language pack (hi)
- Error messages for missing packs

### 6. TestPerformance

**Purpose:** Performance benchmarks

| Test Case | Scale | Time Limit |
|-----------|-------|------------|
| `test_large_file_translation` | 1000+ lines (3500+ lines) | < 10 seconds |
| `test_many_files_translation` | 50 files | < 30 seconds |

**Coverage:**

- Large file handling
- Bulk file translation
- Performance benchmarks

### 7. TestErrorHandling

**Purpose:** Error cases and edge cases

| Test Case | Error Type |
|-----------|------------|
| `test_invalid_python_syntax_error` | Invalid Python syntax |
| `test_stdin_with_no_input` | Empty stdin |
| `test_output_directory_permission_error` | Permission errors |
| `test_non_utf8_file_error` | Encoding errors |

**Coverage:**

- Syntax error handling
- Input validation
- Permission errors
- Encoding errors

## Test Data

### Sample Code Patterns

**Spanish Keywords Tested:**

```python
importar, desde, clase, definir, intentar, para, si, elevar,
continuar, con, como, excepto, finalmente, pasar, retornar, afirmar
```

**Arabic Keywords Tested (RTL):**

```python
تعريف (def), إذا (if), وإلا (elif), آخر (else),
صنف (class), لكل (for), طباعة (print)
```

**Hindi Keywords Tested:**

```python
परिभाषित (def), छापना (print), लौटाना (return), वर्ग (class)
```

### Complex Test Examples

**Functions with Docstrings:**

```python
def calculate_tax(income, rate):
    """Calculate tax on income."""
    if income < 0:
        raise ValueError("Income cannot be negative")
    return income * rate
```

**Classes with Methods:**

```python
class Calculator:
    def __init__(self, precision: int = 2):
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        return round(a + b, self.precision)
```

**Control Flow:**

```python
for item in items:
    if item < 0:
        continue
    elif item == 0:
        break
    else:
        results.append(item * 2)

while counter < len(results):
    try:
        value = results[counter]
    except IndexError as e:
        break
    finally:
        counter += 1
```

## Semantic Equivalence Verification

### Why This Matters

The **most critical** aspect of Legesher is ensuring that translated code is
**semantically identical** to the original. This means:

1. **Same AST Structure** - The parsed abstract syntax tree is identical
2. **Same Bytecode** - The compiled bytecode is identical (stricter test)
3. **Same Runtime Behavior** - Execution produces identical results

### Verification Methods

#### AST Comparison (Primary)

```python
def assert_ast_equivalent(code1: str, code2: str):
    ast1 = ast.parse(code1)
    ast2 = ast.parse(code2)
    dump1 = ast.dump(ast1, annotate_fields=False, include_attributes=False)
    dump2 = ast.dump(ast2, annotate_fields=False, include_attributes=False)
    assert dump1 == dump2
```

**Benefits:**

- Format-independent (whitespace, comments ignored)
- Structural equivalence verification
- Works for semantically equivalent code

#### Bytecode Comparison (Stricter)

```python
def assert_bytecode_equivalent(code1: str, code2: str):
    bytecode1 = compile(code1, '<string>', 'exec')
    bytecode2 = compile(code2, '<string>', 'exec')
    assert bytecode1.co_code == bytecode2.co_code
```

**Benefits:**

- Guarantees identical runtime behavior
- Verifies optimization equivalence
- Catches subtle differences

#### Execution Comparison (Runtime)

```python
def assert_code_executes_identically(code1: str, code2: str):
    # Execute both and compare stdout/stderr
    exec(code1, globals1)
    exec(code2, globals2)
    assert stdout1 == stdout2
```

**Benefits:**

- Verifies actual runtime behavior
- Tests side effects
- Real-world validation

## Running Tests

### Run All Integration Tests

```bash
cd libs/legesher
pytest tests/integration/ -v
```

### Run Specific Test Class

```bash
pytest tests/integration/test_cli_integration.py::TestSemanticEquivalence -v
```

### Run Excluding Slow Tests

```bash
pytest tests/integration/ -m "not slow" -v
```

### Run With Coverage Report

```bash
pytest tests/integration/ --cov=legesher --cov-report=html --cov-report=term
```

### Run Specific Test

```bash
pytest tests/integration/test_cli_integration.py::TestSemanticEquivalence::test_ast_semantic_equivalence_spanish -v
```

## Expected Coverage

### Integration Paths Covered

| Component | Coverage |
|-----------|----------|
| CLI main entry point | 90%+ |
| translate command | 90%+ |
| File handling | 95%+ |
| Directory handling | 95%+ |
| stdin/stdout handling | 90%+ |
| Error handling | 85%+ |
| **Overall Integration** | **85%+** |

### What's NOT Covered (By Design)

These are covered by unit tests or excluded intentionally:

- TokenTranslator internals (covered by legesher-core tests)
- Language pack loading (covered by legesher-i18n tests)
- Edge cases for specific Python versions
- Platform-specific file permission edge cases
- Network-related operations (none exist)

## Test Fixtures

### Provided Fixtures

**`sample_spanish_code`** - Sample Spanish code for quick tests

```python
definir calcular(x, y):
    """Calcula la suma."""
    si x < 0:
        elevar ValueError("x debe ser positivo")
    retornar x + y
```

**`sample_english_code`** - Sample English code for quick tests

```python
def calculate(x, y):
    """Calculate sum."""
    if x < 0:
        raise ValueError("x must be positive")
    return x + y
```

**`complex_python_project`** - Complete project structure

```text
project/
├── __init__.py
├── main.py
├── core/
│   ├── __init__.py
│   └── engine.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── tests/
    └── test_main.py
```

## Maintenance

### Adding New Tests

1. **Identify the test class** - Choose appropriate class based on test purpose
2. **Follow naming convention** - `test_<description_of_what_is_tested>`
3. **Use semantic verification** - Always verify AST/bytecode for translation tests
4. **Add to this document** - Update coverage matrix

### Updating Tests

When CLI behavior changes:

1. Update affected test cases
2. Verify semantic equivalence still holds
3. Update coverage percentages
4. Add new test cases for new functionality

### Performance Benchmarks

Current benchmarks (as of creation):

- **1000+ line file:** < 10 seconds
- **50 files:** < 30 seconds

Update these if performance improvements are made.

## Integration with CI/CD

These tests should run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run Integration Tests
  run: |
    cd libs/legesher
    pytest tests/integration/ -v --cov=legesher --cov-report=xml
```

## Known Issues / Limitations

### Current Test Limitations

1. **Platform-specific tests** - Some permission tests may behave differently on Windows
2. **Encoding tests** - Non-UTF-8 handling depends on platform defaults
3. **Performance tests** - Timing may vary based on system load

### Future Enhancements

- [ ] Add tests for cultural comments (MLCP)
- [ ] Add tests for git filter integration
- [ ] Add tests for VS Code extension integration
- [ ] Add stress tests (10,000+ files)
- [ ] Add memory usage tests

## References

- **Implementation:** `libs/legesher/legesher/cli/translate.py`
- **CLI Entry:** `libs/legesher/legesher/cli/main.py`
- **Core Tests:** `libs/core/tests/integration/test_pack_integration.py`
- **Language Packs:** `libs/i18n/language-packs/`

---

**Last Updated:** 2025-11-03
**Test File Version:** 1.0.0
**Total Test Cases:** 30+
**Coverage Target:** 85%+
