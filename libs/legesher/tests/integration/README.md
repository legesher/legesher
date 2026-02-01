# Legesher CLI Integration Tests

Comprehensive integration tests for the Legesher CLI with semantic equivalence verification.

## Quick Start

```bash
# Navigate to package directory
cd /Users/madisonedgar/GitHub/MadiEdgar/legesher-core-349/libs/legesher

# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=legesher --cov-report=html
```

## What's Tested

### 🎯 Critical: Semantic Equivalence (4 tests)

- AST structure equivalence
- Bytecode equivalence
- Round-trip translation preservation
- Runtime execution equivalence

### 🌍 End-to-End Translation (3 tests)

- File translation (Spanish → English)
- stdin translation (English → Arabic)
- Directory translation (English → Hindi)

### 🔧 Complex Code Patterns (6 tests)

- Import statements
- Class definitions & methods
- Decorators
- Control flow (if/for/while/try/except)
- Context managers (with statements)
- List/dict/set comprehensions

### 📁 Directory Operations (4 tests)

- Complex nested structures
- Deep subdirectories (4+ levels)
- File type filtering (.py only)
- Empty directory handling

### 🌐 Language Pack Integration (4 tests)

- Spanish (es) - 16+ keywords
- Arabic (ar) - RTL support
- Hindi (hi) - Devanagari script
- Error handling for missing packs

### ⚡ Performance (2 tests)

- Large files (1000+ lines, < 10s)
- Many files (50 files, < 30s)

### 🚨 Error Handling (4 tests)

- Invalid syntax errors
- Empty stdin handling
- Permission errors
- Encoding errors

**Total:** 30+ comprehensive test cases

## Test Commands

### By Test Class

```bash
# Critical semantic equivalence tests
pytest tests/integration/test_cli_integration.py::TestSemanticEquivalence -v

# End-to-end workflows
pytest tests/integration/test_cli_integration.py::TestEndToEndTranslation -v

# Complex code patterns
pytest tests/integration/test_cli_integration.py::TestComplexCodePatterns -v

# Directory operations
pytest tests/integration/test_cli_integration.py::TestDirectoryOperations -v

# Language pack integration
pytest tests/integration/test_cli_integration.py::TestRealLanguagePacks -v

# Performance tests
pytest tests/integration/test_cli_integration.py::TestPerformance -v

# Error handling
pytest tests/integration/test_cli_integration.py::TestErrorHandling -v
```

### By Test Type

```bash
# Skip slow performance tests
pytest tests/integration/ -m "not slow" -v

# Only integration tests
pytest tests/integration/ -m "integration" -v

# Specific test
pytest tests/integration/test_cli_integration.py::TestSemanticEquivalence::test_ast_semantic_equivalence_spanish -v
```

### With Coverage

```bash
# HTML coverage report
pytest tests/integration/ --cov=legesher --cov-report=html

# Terminal coverage report
pytest tests/integration/ --cov=legesher --cov-report=term-missing

# XML coverage report (for CI/CD)
pytest tests/integration/ --cov=legesher --cov-report=xml
```

## Understanding Semantic Equivalence

The **most important** tests verify that translated code is functionally identical.

### Helper Functions

**`assert_ast_equivalent(code1, code2)`**

- Compares Abstract Syntax Tree structure
- Format-independent (ignores whitespace, comments)
- **Use this** for general semantic equivalence

**`assert_bytecode_equivalent(code1, code2)`**

- Compares compiled bytecode
- Stricter than AST comparison
- Guarantees identical runtime behavior

**`assert_code_executes_identically(code1, code2)`**

- Executes both code snippets
- Compares stdout/stderr output
- Verifies side effects

### Example Usage

```python
def test_translation_equivalence(tmp_path):
    spanish_code = "definir foo(): retornar 42"

    # Translate to English
    result = translate_cli(spanish_code, from_lang="es", to_lang="en")

    # Verify semantic equivalence
    expected_english = "def foo(): return 42"
    assert_ast_equivalent(result, expected_english)
```

## Test Organization

```text
tests/integration/
├── __init__.py                    # Package initialization
├── test_cli_integration.py        # Main test file (1300+ lines)
├── TEST_COVERAGE.md              # Detailed coverage documentation
└── README.md                      # This file
```

## Coverage Target

**Goal:** 85%+ integration path coverage

Current coverage areas:

- CLI entry points: 90%+
- translate command: 90%+
- File handling: 95%+
- Directory handling: 95%+
- Error handling: 85%+

## Common Issues

### Issue: Tests fail with "Language pack not found"

**Solution:** Ensure legesher-i18n is installed with language packs

```bash
cd ../i18n
pip install -e .
```

### Issue: Permission tests fail on Windows

**Solution:** Skip permission tests on Windows

```bash
pytest tests/integration/ --deselect=test_output_directory_permission_error
```

### Issue: Performance tests timeout

**Solution:** Increase timeout or skip slow tests

```bash
pytest tests/integration/ -m "not slow"
```

## Debugging Tests

### Verbose Output

```bash
pytest tests/integration/ -vv -s
```

### Stop on First Failure

```bash
pytest tests/integration/ -x
```

### Run Last Failed Tests

```bash
pytest tests/integration/ --lf
```

### Show Test Durations

```bash
pytest tests/integration/ --durations=10
```

## Adding New Tests

1. **Choose the appropriate test class** based on test purpose
2. **Follow naming convention:** `test_<what_is_being_tested>`
3. **Use semantic verification** for translation tests
4. **Add docstrings** explaining what the test verifies
5. **Use tmp_path fixture** for file operations
6. **Update TEST_COVERAGE.md** with new test info

### Example New Test

```python
def test_new_feature(self, tmp_path: Path):
    """Test new feature with semantic equivalence verification."""
    # Setup
    code = "def example(): return 42"
    input_file = tmp_path / "test.py"
    input_file.write_text(code)

    output_file = tmp_path / "output.py"

    # Execute
    runner = CliRunner()
    result = runner.invoke(cli, [
        'translate', str(input_file),
        '--from', 'en', '--to', 'es',
        '--output', str(output_file)
    ])

    # Verify
    assert result.exit_code == 0
    translated = output_file.read_text()
    assert "definir" in translated
    assert "retornar" in translated
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        cd libs/legesher
        pip install -e .[dev]
        pip install -e ../core
        pip install -e ../i18n

    - name: Run integration tests
      run: |
        cd libs/legesher
        pytest tests/integration/ -v --cov=legesher --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./libs/legesher/coverage.xml
```

## Performance Benchmarks

Current benchmarks (target thresholds):

| Test | File Size | Count | Time Limit |
|------|-----------|-------|------------|
| Large file | 3500+ lines | 1 file | < 10 seconds |
| Many files | ~50 lines each | 50 files | < 30 seconds |

Run performance tests:

```bash
pytest tests/integration/test_cli_integration.py::TestPerformance -v --durations=0
```

## Language Support

Tests verify integration with real language packs:

| Language | Code | Script | Direction | Keywords Tested |
|----------|------|--------|-----------|-----------------|
| Spanish | es | Latin | LTR | 16+ |
| Arabic | ar | Arabic | RTL | 6+ |
| Hindi | hi | Devanagari | LTR | 4+ |

## Documentation

- **TEST_COVERAGE.md** - Comprehensive coverage documentation
- **test_cli_integration.py** - Inline docstrings for each test
- **This README** - Quick reference guide

## Support

For issues or questions:

1. Check TEST_COVERAGE.md for detailed test information
2. Review test docstrings in test_cli_integration.py
3. Check CI/CD logs for test failures
4. Create an issue in the main repository

---

**Last Updated:** 2025-11-03
**Test Count:** 30+ integration tests
**Coverage Target:** 85%+
**Test File:** test_cli_integration.py (1300+ lines)
