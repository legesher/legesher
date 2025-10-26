# CORE-346 Implementation Plan: Version-Aware Language Pack System

**Issue**: [CORE-346](https://linear.app/legesher/issue/CORE-346)
**Status**: 🧼 Ready
**Assignee**: <madi@legesher.com>
**Created**: 2025-10-23

## Overview

Implement a version-aware language pack system that automatically adapts to different Python versions (3.10-3.13+) with inheritance capabilities, auto-detection, and a version index tracking keyword changes.

## Context & Prior Art

### Current State

- Empty `libs/i18n` package with scaffold structure
- No existing language packs or version detection logic
- Dependencies: Need to add PyYAML for YAML parsing
- Python requirement: >=3.13 (per pyproject.toml)

### Architecture Alignment

- Tier 2 package (depends on `legesher-core`)
- Part of Phase 1: Core Foundation
- Milestone: v0.1 (MVP) - Target: 2025-11-04

## Implementation Strategy

### Security Considerations

1. **Input Validation**: Validate all YAML files against strict schemas
2. **Path Traversal**: Sanitize all file paths, prevent `../` escapes in `extends` fields
3. **Resource Limits**: Prevent infinite inheritance loops (max depth: 10)
4. **Type Safety**: Use Pydantic for data validation and type safety
5. **Error Handling**: Fail safely with clear error messages, no stack traces exposing internals

### Design Principles

1. **Fail Fast**: Validate early, catch errors at load time
2. **Explicit > Implicit**: Clear error messages over silent failures
3. **Immutable Data**: Loaded packs are frozen dataclasses
4. **Caching**: Cache loaded packs to avoid repeated file I/O
5. **Extensibility**: Easy to add new Python versions

## File Structure

```
libs/i18n/
├── legesher_i18n/          (rename from legesher-i18n/)
│   ├── __init__.py
│   ├── version_index.py     NEW: Parse version-index.yml
│   ├── version_detector.py  NEW: Auto-detect Python version
│   ├── pack_loader.py       NEW: Load packs with inheritance
│   ├── schema_validator.py  NEW: Validate pack structure
│   └── exceptions.py        NEW: Custom exception classes
├── languages/
│   └── python/
│       ├── version-index.yml  NEW: Python version metadata
│       ├── 3.10/
│       │   ├── es.yml       NEW: Spanish for Python 3.10
│       │   └── ar.yml       NEW: Arabic for Python 3.10
│       ├── 3.11/
│       │   ├── es.yml       NEW: Extends 3.10/es.yml
│       │   └── ar.yml
│       ├── 3.12/
│       │   ├── es.yml
│       │   └── ar.yml
│       └── 3.13/
│           ├── es.yml
│           └── ar.yml
├── tests/
│   ├── test_version_index.py
│   ├── test_version_detector.py
│   ├── test_pack_loader.py
│   ├── test_schema_validator.py
│   ├── test_integration.py
│   └── fixtures/           NEW: Test data
└── pyproject.toml          UPDATE: Add pyyaml, pydantic
```

## Implementation Tasks

### Phase 1: Core Infrastructure (Priority: High)

#### 1.1 Add Dependencies

```toml
# Add to libs/i18n/pyproject.toml
dependencies = [
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "legesher-core"  # Already in [tool.uv.sources]
]
```

#### 1.2 Create Exception Classes

**File**: `libs/i18n/legesher_i18n/exceptions.py`

- `LanguagePackError` (base)
- `PackNotFoundError`
- `PackValidationError`
- `InheritanceError`
- `VersionDetectionError`

#### 1.3 Implement Version Index Parser

**File**: `libs/i18n/legesher_i18n/version_index.py`

Classes:

- `PythonVersionInfo`: Dataclass for version metadata
- `VersionIndex`: Load and query version-index.yml

Key Methods:

- `load(index_path: Path) -> VersionIndex`
- `get_version_info(version: str) -> PythonVersionInfo`
- `get_supported_versions() -> List[str]`
- `get_inheritance_chain(version: str) -> List[str]`

Security:

- Validate version strings (semver format)
- Prevent circular inheritance
- Max inheritance depth: 10 levels

#### 1.4 Implement Version Detector

**File**: `libs/i18n/legesher_i18n/version_detector.py`

Classes:

- `PythonVersionDetector`

Detection Priority:

1. `pyproject.toml` `requires-python` field
2. `.python-version` file
3. Runtime `sys.version_info`
4. Default to "3.13"

Key Methods:

- `detect(project_path: Path = None) -> str`
- `detect_from_pyproject(path: Path) -> Optional[str]`
- `detect_from_file(path: Path) -> Optional[str]`
- `detect_from_runtime() -> str`

Security:

- Sanitize all file paths
- Handle missing/malformed files gracefully
- Parse `requires-python` with packaging.specifiers

### Phase 2: Language Pack Loading (Priority: High)

#### 2.1 Implement Pack Loader with Inheritance

**File**: `libs/i18n/legesher_i18n/pack_loader.py`

Classes:

- `LanguagePack`: Frozen dataclass for pack data
- `LanguagePackLoader`: Load packs with inheritance

Key Methods:

- `load(language: str, target: str, version: str) -> LanguagePack`
- `_resolve_inheritance(pack_path: Path, visited: Set[Path]) -> Dict`
- `_merge_packs(base: Dict, override: Dict) -> Dict`

Inheritance Logic:

1. Load pack YAML
2. Check for `extends` field
3. Recursively load parent pack
4. Merge keywords (child overrides parent)
5. Cache result

Security:

- Prevent path traversal in `extends`
- Detect circular inheritance
- Validate all pack files with schema

#### 2.2 Implement Schema Validator

**File**: `libs/i18n/legesher_i18n/schema_validator.py`

Classes:

- `LanguagePackSchema`: Pydantic model for validation
- `VersionIndexSchema`: Pydantic model for version index
- `SchemaValidator`: Validation utilities

Key Methods:

- `validate_pack(pack_data: Dict) -> LanguagePackSchema`
- `validate_version_index(index_data: Dict) -> VersionIndexSchema`
- `check_completeness(pack: LanguagePack, version_info: PythonVersionInfo) -> List[str]`

Validation Rules:

- Required fields: language, target, version
- Optional: extends, metadata
- Keywords: Dict[str, str]
- Builtins: Dict[str, str]
- Version strings: semver format

### Phase 3: Data Files (Priority: High)

#### 3.1 Create Version Index

**File**: `libs/i18n/languages/python/version-index.yml`

Content:

```yaml
python_versions:
  "3.10":
    added_keywords:
      - match
      - case
    removed_keywords: []
    base: "3.9"
  "3.11":
    added_keywords:
      - except*
    removed_keywords: []
    base: "3.10"
  "3.12":
    added_keywords:
      - type
    removed_keywords: []
    base: "3.11"
  "3.13":
    added_keywords: []
    removed_keywords: []
    base: "3.12"

auto_update:
  enabled: true
  source: "https://docs.python.org/3/reference/lexical_analysis.html"
  check_interval: "monthly"
```

#### 3.2 Create Example Language Packs

**Spanish (es)**:

- `3.10/es.yml`: Base pack with all 3.10 keywords
- `3.11/es.yml`: Extends 3.10, adds `except*: excepto*`
- `3.12/es.yml`: Extends 3.11, adds `type: tipo`
- `3.13/es.yml`: Extends 3.12, no new keywords

**Arabic (ar)**:

- Similar structure, Arabic translations
- RTL considerations in metadata

### Phase 4: Testing (Priority: High)

#### 4.1 Unit Tests

**test_version_index.py**:

- Load version index successfully
- Get version info
- Build inheritance chain
- Detect circular inheritance
- Handle missing versions

**test_version_detector.py**:

- Detect from pyproject.toml
- Detect from .python-version
- Detect from runtime
- Priority ordering
- Handle missing files

**test_pack_loader.py**:

- Load simple pack
- Load with single inheritance
- Load with multi-level inheritance
- Merge keywords correctly
- Cache behavior
- Prevent circular inheritance
- Path traversal protection

**test_schema_validator.py**:

- Validate correct pack
- Reject invalid pack
- Check required fields
- Validate version format
- Completeness checking

#### 4.2 Integration Tests

**test_integration.py**:

- End-to-end: Auto-detect version + load pack
- Explicit version override
- Multiple languages
- Cross-version compatibility
- Performance benchmarks

#### 4.3 Test Fixtures

Create `tests/fixtures/`:

- `valid_packs/`: Valid language pack examples
- `invalid_packs/`: Packs with various errors
- `version_indexes/`: Test version indexes
- `projects/`: Mock project structures

### Phase 5: Documentation (Priority: Medium)

#### 5.1 Update Package README

**File**: `libs/i18n/README.md`

Sections:

- Overview
- Installation
- Quick Start
- Version Detection
- Language Pack Structure
- API Reference
- Contributing

#### 5.2 Update Main Documentation

**File**: `docs/src/content/docs/guides/language-packs.md` (new)

Content:

- How language packs work
- Version-aware system
- Creating new packs
- Testing packs
- Best practices

#### 5.3 API Documentation

Generate from docstrings using Sphinx or mkdocs

### Phase 6: Integration (Priority: Medium)

#### 6.1 Update Package **init**.py

**File**: `libs/i18n/legesher_i18n/__init__.py`

Export public API:

```python
from .pack_loader import LanguagePack, LanguagePackLoader
from .version_detector import PythonVersionDetector
from .exceptions import *

__all__ = [
    "LanguagePack",
    "LanguagePackLoader",
    "PythonVersionDetector",
    # exceptions...
]
```

#### 6.2 Add Convenience Functions

```python
def load_language_pack(
    language: str,
    target: str = "python",
    version: Optional[str] = None,
    project_path: Optional[Path] = None
) -> LanguagePack:
    """Convenience function for common use case."""
    if version is None:
        detector = PythonVersionDetector()
        version = detector.detect(project_path)

    loader = LanguagePackLoader()
    return loader.load(language, target, version)
```

## Testing Strategy

### Test Pyramid

1. **Unit Tests (70%)**: Test individual components in isolation
2. **Integration Tests (20%)**: Test component interactions
3. **End-to-End Tests (10%)**: Test complete workflows

### Test Coverage Target

- Minimum: 90% coverage
- Critical paths: 100% coverage (security, validation)

### Performance Benchmarks

- Pack loading: < 50ms (with caching)
- Version detection: < 10ms
- Inheritance resolution: < 100ms for 10 levels

### Compatibility Testing

Test on:

- Python 3.13 (primary)
- macOS, Linux, Windows
- Various project structures

## Acceptance Criteria

- [ ] Loads correct pack for Python version (auto-detected or explicit)
- [ ] Inheritance works properly (multi-level, keyword merging)
- [ ] Auto-detection reliable (pyproject.toml → .python-version → runtime)
- [ ] Version index complete for Python 3.10-3.13
- [ ] Comprehensive tests (90%+ coverage)
- [ ] Security: No path traversal, no circular inheritance, validated input
- [ ] Performance: Pack loading < 50ms
- [ ] Documentation: README, user guide, API docs
- [ ] Type hints: Full type coverage with mypy
- [ ] Linting: Passes ruff/black/isort

## Dependencies & Blockers

### Dependencies

- None (can be implemented independently)

### Blockers

- None identified

### Nice-to-Have (Future Work)

- Auto-update mechanism for version-index.yml
- Pack validation CLI tool
- Pack completeness report
- Support for more programming languages

## Implementation Order

1. **Day 1**: Setup + Core Infrastructure
   - Add dependencies
   - Create exception classes
   - Implement version_index.py
   - Write unit tests for version_index

2. **Day 2**: Version Detection
   - Implement version_detector.py
   - Write unit tests for version_detector
   - Create test fixtures

3. **Day 3**: Pack Loading
   - Implement pack_loader.py
   - Implement schema_validator.py
   - Write unit tests

4. **Day 4**: Data Files
   - Create version-index.yml
   - Create Spanish language packs (3.10-3.13)
   - Create Arabic language packs (3.10-3.13)

5. **Day 5**: Integration & Testing
   - Write integration tests
   - Run full test suite
   - Fix any issues
   - Performance testing

6. **Day 6**: Documentation & Polish
   - Update package README
   - Create user guide
   - Run linting/type checking
   - Final testing

7. **Day 7**: Review & PR
   - Code review
   - Address feedback
   - Open PR

## Risk Assessment

### High Risk

- **Circular Inheritance**: Mitigated by tracking visited packs
- **Path Traversal**: Mitigated by path sanitization
- **Performance**: Mitigated by caching

### Medium Risk

- **YAML Parsing Errors**: Mitigated by schema validation
- **Version Detection Failures**: Mitigated by fallback chain

### Low Risk

- **Missing Language Packs**: Clear error messages
- **Incomplete Packs**: Validation warnings

## Success Metrics

1. All acceptance criteria met
2. 90%+ test coverage
3. Zero security vulnerabilities
4. Performance benchmarks met
5. Documentation complete
6. PR approved and merged

## Notes

- Keep it simple for MVP, iterate based on feedback
- Focus on Spanish and Arabic for initial packs
- Ensure extensibility for future languages and Python versions
- Security is paramount - validate everything
