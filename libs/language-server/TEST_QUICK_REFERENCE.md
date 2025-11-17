# Language Server Test Infrastructure - Quick Reference

## File Locations

### YAML Fixtures

```text
tests/fixtures/language_packs/
├── valid/
│   ├── base_es.yml          # Spanish pack (37 keywords + builtins)
│   ├── base_ar.yml          # Arabic pack (37 keywords + builtins)
│   └── inherited_es.yml     # Spanish with inheritance
├── invalid/
│   ├── malformed_yaml.yml   # YAML syntax error
│   ├── missing_keywords.yml # No keywords section
│   ├── invalid_mappings.yml # Non-string values
│   ├── missing_language.yml # Missing required field
│   ├── missing_target.yml   # Missing required field
│   ├── empty_file.yml       # Empty YAML
│   └── null_content.yml     # YAML parses as None
└── mixed/
    ├── partial_pack.yml     # Keywords only
    └── empty_keywords.yml   # Empty keywords section
```text

### Python Utilities

```text
tests/
├── conftest.py              # Pytest fixtures and markers
└── fixtures/
    └── mock_output_channel.py  # MockOutputChannel class
```text

## Available Fixtures

### Path Fixtures

```python
def test_example(valid_packs_dir, invalid_packs_dir, mixed_packs_dir):
    es_pack = valid_packs_dir / "base_es.yml"
    bad_yaml = invalid_packs_dir / "malformed_yaml.yml"
    partial = mixed_packs_dir / "partial_pack.yml"
```text

### Mock Output Channel

```python
def test_logging(mock_output_channel):
    output = mock_output_channel
    output.append_line("Message 1")
    output.append_line("Message 2")

    assert len(output.get_lines()) == 2
    assert "Message 1" in output.get_output()
    output.clear()
```text

### Temporary Directory

```python
def test_temp(temp_pack_dir):
    pack_file = temp_pack_dir / "test.yml"
    pack_file.write_text("language: test")
    # Auto-cleaned after test
```text

### Logging Capture

```python
def test_with_logs(caplog_for_yaml_errors):
    # Code that logs
    assert "warning" in caplog_for_yaml_errors.text
```text

## Test Markers

Run tests by category:

```bash
# By category
pytest -m yaml_parsing -v          # YAML parsing errors
pytest -m pack_discovery -v        # File system errors
pytest -m schema_validation -v     # Schema validation errors
pytest -m data_validation -v       # Data type validation
pytest -m version_fallback -v      # Version fallback chain
pytest -m language_fallback -v     # Language fallback chain
pytest -m output_channel -v        # Output channel logging
pytest -m integration -v           # End-to-end tests
pytest -m keyword_docs -v          # All keyword_docs tests
```text

## Common Test Patterns

### Test YAML Loading

```python
def test_load_yaml(valid_packs_dir):
    import yaml
    pack_file = valid_packs_dir / "base_es.yml"
    with open(pack_file) as f:
        data = yaml.safe_load(f)
    assert data["language"] == "es"
    assert "def" in data["keywords"]
```text

### Test Error Handling

```python
def test_yaml_error(invalid_packs_dir):
    import yaml
    bad_file = invalid_packs_dir / "malformed_yaml.yml"
    with pytest.raises(yaml.YAMLError):
        with open(bad_file) as f:
            yaml.safe_load(f)
```text

### Test Output Logging

```python
def test_output(mock_output_channel):
    channel = mock_output_channel
    channel.append_line("Success: 37 keywords loaded")
    assert "37 keywords" in channel.get_output()
```text

### Parametrized Testing

```python
@pytest.mark.parametrize("value,is_valid", [
    ("string", True),
    (123, False),
    ([1, 2], False),
    ({"a": "b"}, False),
])
def test_types(value, is_valid):
    result = isinstance(value, str) == is_valid
    assert result
```text

## Quick Commands

```bash
# From language-server directory
cd libs/language-server

# Run all tests
uv run pytest tests/test_keyword_docs_error_handling.py -v

# Run specific test class
uv run pytest tests/test_keyword_docs_error_handling.py::TestPackDiscovery -v

# Run specific test method
uv run pytest tests/test_keyword_docs_error_handling.py::TestYAMLParsing::test_valid_yaml_parses_successfully -v

# With coverage
uv run pytest tests/test_keyword_docs_error_handling.py \
  --cov=legesher_language_server.utils.keyword_docs \
  --cov-report=term-missing

# HTML coverage report
uv run pytest tests/test_keyword_docs_error_handling.py \
  --cov=legesher_language_server.utils.keyword_docs \
  --cov-report=html
open htmlcov/index.html
```text

## MockOutputChannel API

```python
channel = mock_output_channel

# Methods
channel.append_line("Text")           # Add line with newline
channel.append("Text")                # Add without newline
channel.clear()                       # Clear all
channel.show(preserve_focus=True)    # Show channel
channel.hide()                        # Hide channel
channel.dispose()                     # Cleanup

# Getters
output = channel.get_output()         # All text as string
lines = channel.get_lines()           # List of lines
is_shown = channel.show_called        # Track if show() called
is_hidden = channel.hide_called       # Track if hide() called
cleared = channel.clear_called        # Track if clear() called

# Usage
channel.append_line("Loaded 37 keywords")
assert "37 keywords" in channel.get_output()
assert len(channel.get_lines()) == 1
```text

## Test Case Checklist

### Category: Pack Discovery

- [ ] Valid file loads successfully
- [ ] Missing directory returns None gracefully
- [ ] Missing file returns None gracefully
- [ ] Permission denied returns None gracefully
- [ ] Directory instead of file returns None gracefully

### Category: YAML Parsing

- [ ] Valid YAML parses successfully
- [ ] Malformed YAML raises YAMLError
- [ ] Empty file parses as None
- [ ] Null content parses as None

### Category: Schema Validation

- [ ] All required fields present validates OK
- [ ] Missing language field detected
- [ ] Missing target field detected
- [ ] Missing keywords section warns

### Category: Data Validation

- [ ] String values accepted
- [ ] Int values rejected
- [ ] List values rejected
- [ ] Dict values rejected
- [ ] Mixed valid/invalid filtered

### Category: Version Fallback

- [ ] Exact version matches
- [ ] Fallback to parent version
- [ ] Multi-level fallback chain
- [ ] No version available logs error

### Category: Language Fallback

- [ ] Target language loads
- [ ] Fallback to parent language
- [ ] Fallback to English
- [ ] Track fallback count

### Category: Output Logging

- [ ] Success messages logged
- [ ] Warning messages logged
- [ ] Error messages logged
- [ ] Multiple messages in order
- [ ] Clear empties output

### Category: Integration

- [ ] Load Spanish pack end-to-end
- [ ] Load Arabic pack end-to-end
- [ ] Keyword translation workflow
- [ ] Fallback workflow with logging
- [ ] Cache after load

## Documentation References

### Main Documentation

- `LANGUAGE_SERVER_TEST_INFRASTRUCTURE.md` (in repo root)
  - Complete reference (85 KB)
  - All test patterns
  - Full test case specifications
  - Sample code skeletons

### Completion Summary

- `TEST_INFRASTRUCTURE_SETUP_COMPLETE.md` (in repo root)
  - What was created
  - File inventory
  - Quick start guide

### This File

- Quick reference for common tasks
- Fixture locations and APIs
- Common test patterns
- Command cheat sheet

## Fixture File Sizes

| File | Lines | Type | Purpose |
|------|-------|------|---------|
| base_es.yml | 90 | Valid | Spanish keywords + builtins |
| base_ar.yml | 67 | Valid | Arabic keywords + builtins |
| inherited_es.yml | 10 | Valid | Inheritance example |
| malformed_yaml.yml | 9 | Invalid | YAML syntax error |
| missing_keywords.yml | 6 | Invalid | Missing section |
| invalid_mappings.yml | 8 | Invalid | Wrong types |
| missing_language.yml | 7 | Invalid | Missing field |
| missing_target.yml | 6 | Invalid | Missing field |
| empty_file.yml | 0 | Invalid | Empty file |
| null_content.yml | 1 | Invalid | Null |
| partial_pack.yml | 8 | Mixed | Incomplete |
| empty_keywords.yml | 9 | Mixed | Empty section |

## Error Recovery Patterns

### Pattern 1: Try/Except/Log

```python
try:
    with open(pack_file) as f:
        data = yaml.safe_load(f)
except FileNotFoundError:
    logger.warning(f"Pack not found: {pack_file}")
    return None
except yaml.YAMLError as e:
    logger.error(f"YAML error: {e}")
    return None
```text

### Pattern 2: Graceful Degradation

```python
# Try primary language
try:
    pack = load_pack("es")
except Exception:
    logger.warning("Spanish pack failed, trying English")
    # Fallback to English
    pack = load_pack("en")
```text

### Pattern 3: Data Filtering

```python
keywords = pack.get("keywords", {})
valid_keywords = {
    k: v for k, v in keywords.items()
    if isinstance(v, str)
}
```text

## Coverage Analysis

```bash
# Generate coverage report
uv run pytest tests/test_keyword_docs_error_handling.py \
  --cov=legesher_language_server.utils.keyword_docs \
  --cov-report=term-missing

# View lines not covered
# Look for "Missing" column - identifies untested code paths

# HTML report
uv run pytest tests/test_keyword_docs_error_handling.py \
  --cov=legesher_language_server.utils.keyword_docs \
  --cov-report=html
open htmlcov/index.html
```text

## Troubleshooting

### Import Error: "No module named tests"

**Solution**: Run from language-server directory

```bash
cd libs/language-server
uv run pytest tests/...
```text

### Fixture Not Found

**Solution**: Ensure conftest.py in tests/ directory

```bash
ls tests/conftest.py
```text

### YAML Files Not Found

**Solution**: Verify fixture directory structure

```bash
ls tests/fixtures/language_packs/valid/
```text

### MockOutputChannel Not Working

**Solution**: Check import path

```python
from tests.fixtures.mock_output_channel import MockOutputChannel
```text

---

**Status**: All fixtures ready for test implementation
**Next**: Create `test_keyword_docs_error_handling.py` and implement tests

**Quick Start**:

1. Create test file from skeleton in LANGUAGE_SERVER_TEST_INFRASTRUCTURE.md
2. Run `uv run pytest -v` to confirm fixtures work
3. Implement error handling in keyword_docs.py
4. Run tests until all pass
5. Check coverage with `--cov` flag
