# Language Pack Validation (CORE-348)

> **Maintainer notes — not newcomer documentation.** Written for someone already
> working in this code: it assumes repo context, uses internal vocabulary, and
> may cite work-tracker ids (`CORE-####`) an outside reader cannot resolve.
> Public on purpose, but not part of the documentation site and not localized —
> newcomer-facing documentation lives at [docs.legesher.io](https://docs.legesher.io).
> <!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

**Version:** 1.0.0
**MLCP Conformance:** v1.0
**Last Updated:** 2025-01-04

## Overview

The language pack validation system ensures that all Legesher language packs
conform to the **MLCP v1.0 (Multilingual Code Protocol)** specification
and maintain high quality standards.

## Features

### 1. Extended MLCP v1.0 Schema Support

The validation system now supports all MLCP v1.0 extended fields:

```yaml
language: es
target: python
version: "3.13"

# Core translations
keywords:
  def: definir
  class: clase

builtins:
  print: imprimir
  len: longitud

# MLCP Extended fields (new in CORE-348)
operators:
  and: y
  or: o
  not: no

standard_library:
  os: sistema_operativo
  math: matematicas
  datetime: fecha_hora

cultural_notes:
  - keyword: "range"
    note: "En español, 'rango' puede significar 'rank' o 'range' según contexto"
    language: "es"

metadata:
  author: "Your Name"
  last_updated: "2025-01-04"
  python_version_min: "3.10"
  license: "Apache-2.0"
```

### 2. Duplicate Detection

Automatically detects when multiple source terms map to the same translation (reversibility issues):

```python
from legesher_i18n.schema_validator import SchemaValidator

result = SchemaValidator.check_duplicates(pack_schema)

if not result['passed']:
    print(f"Found {result['total_conflicts']} conflicts:")
    for dup in result['keyword_duplicates']:
        print(f"  '{dup['translation']}' maps to: {dup['source_terms']}")
```

**Example Output:**

```text
Found 1 conflicts:
  'definir' maps to: ['class', 'def']
```

### 3. Enhanced Completeness Checking

Provides detailed analysis of pack completeness with version-index integration:

```python
from pathlib import Path

version_index_path = Path("libs/i18n/programming_languages/python/version-index.yml")
result = SchemaValidator.check_completeness_enhanced(
    pack_schema,
    version_index_path=version_index_path
)

print(f"Completeness: {result['completeness_percentage']:.0%}")
print(f"Metadata Score: {result['metadata_score']:.0%}")
print(f"Missing Keywords: {len(result['missing_keywords'])}")
print(f"Recommendations: {len(result['recommendations'])}")
```

**Example Output:**

```text
Completeness: 92%
Metadata Score: 71%
Missing Keywords: 3
Recommendations: 2
```

### 4. MLCP v1.0 Conformance Validation

Validates packs against three conformance levels:

- **Core**: Basic required fields (language, target, version, ISO 639-1 codes)
- **Extended**: Core + translations + metadata
- **Full**: Extended + optional fields (operators, stdlib, cultural_notes)

```python
result = SchemaValidator.check_mlcp_conformance(pack_schema)

print(f"Conformance Level: {result['conformance_level']}")
print(f"Passed: {result['passed']}")
print(f"Spec Version: {result['spec_version']}")

if result['issues']:
    print("Issues found:")
    for issue in result['issues']:
        print(f"  - {issue}")
```

**Example Output:**

```text
Conformance Level: extended
Passed: True
Spec Version: 1.0
Issues found:
  - Metadata missing 'author' field (MLCP v1.0 recommendation)
```

## API Reference

### `SchemaValidator.check_duplicates(pack_schema)`

Checks for duplicate translations across all mapping types.

**Parameters:**

- `pack_schema` (LanguagePackSchema): Validated language pack

**Returns:**

```python
{
    "passed": bool,  # True if no duplicates
    "keyword_duplicates": list[dict],  # Conflicts in keywords
    "builtin_duplicates": list[dict],  # Conflicts in builtins
    "operator_duplicates": list[dict],  # Conflicts in operators
    "stdlib_duplicates": list[dict],  # Conflicts in standard_library
    "total_conflicts": int  # Total number of conflicts
}
```

### `SchemaValidator.check_completeness_enhanced(pack_schema, version_index_path=None)`

Provides enhanced completeness analysis with version-index integration.

**Parameters:**

- `pack_schema` (LanguagePackSchema): Validated language pack
- `version_index_path` (Optional[Path]): Path to version-index.yml

**Returns:**

```python
{
    "completeness_percentage": float,  # 0.0 to 1.0
    "missing_keywords": list[str],  # Keywords that should be translated
    "missing_builtins": list[str],  # Critical builtins not translated
    "metadata_score": float,  # 0.0 to 1.0
    "recommendations": list[str],  # Actionable suggestions
    "passed": bool  # True if >= 90% complete and metadata >= 50%
}
```

### `SchemaValidator.check_mlcp_conformance(pack_schema)`

Validates MLCP v1.0 specification conformance.

**Parameters:**

- `pack_schema` (LanguagePackSchema): Validated language pack

**Returns:**

```python
{
    "conformance_level": str,  # "core" | "extended" | "full" | "non-conformant"
    "passed": bool,  # True if meets at least "core" level
    "checks": dict,  # Individual check results
    "spec_version": str,  # MLCP version ("1.0")
    "issues": list[str],  # Conformance issues
    "core_conformant": bool,
    "extended_conformant": bool,
    "full_conformant": bool
}
```

## MLCP v1.0 Conformance Levels

### Core Conformance

Requires:

- ✅ `language` field (ISO 639-1 two-letter code)
- ✅ `target` field (programming language)
- ✅ `version` field (X.Y format)
- ✅ Valid ISO 639-1 language code
- ✅ Valid version format
- ✅ Security: Path traversal prevention

### Extended Conformance

Core requirements + :

- ✅ At least one of: `keywords` or `builtins`
- ✅ `metadata` section present
- ✅ `metadata.last_updated` field
- ✅ `metadata.author` field (recommended)

### Full Conformance

Extended requirements +:

- ✅ At least one of: `operators`, `standard_library`, or `cultural_notes`

## Testing

All validation features are thoroughly tested:

```bash
# Run validation tests
uv run pytest libs/i18n/tests/test_schema_validator.py -v

# Run specific test class
uv run pytest libs/i18n/tests/test_schema_validator.py::TestMLCPConformance -v
```

**Test Coverage:**

- ✅ 25+ comprehensive tests
- ✅ All MLCP extended fields
- ✅ Duplicate detection scenarios
- ✅ Enhanced completeness checking
- ✅ MLCP conformance levels
- ✅ Edge cases and error handling

## Examples

### Complete Validation Workflow

```python
from pathlib import Path
from legesher_i18n.schema_validator import SchemaValidator, LanguagePackSchema
import yaml

# Load language pack
pack_path = Path("libs/i18n/programming_languages/python/3.13/es.yml")
with open(pack_path) as f:
    pack_data = yaml.safe_load(f)

# Validate schema
pack_schema = SchemaValidator.validate_pack(pack_data, pack_path)

# Run all validation checks
print("=" * 60)
print("LANGUAGE PACK VALIDATION REPORT")
print("=" * 60)

# 1. Duplicate Detection
print("\n1. Duplicate Detection")
dup_result = SchemaValidator.check_duplicates(pack_schema)
if dup_result['passed']:
    print("   ✓ No duplicates found")
else:
    print(f"   ✗ Found {dup_result['total_conflicts']} conflicts")

# 2. Completeness
print("\n2. Completeness Analysis")
version_index = Path("libs/i18n/programming_languages/python/version-index.yml")
comp_result = SchemaValidator.check_completeness_enhanced(
    pack_schema, version_index
)
print(f"   Completeness: {comp_result['completeness_percentage']:.0%}")
print(f"   Metadata Score: {comp_result['metadata_score']:.0%}")
print(f"   Status: {'✓ PASS' if comp_result['passed'] else '✗ FAIL'}")

# 3. MLCP Conformance
print("\n3. MLCP v1.0 Conformance")
mlcp_result = SchemaValidator.check_mlcp_conformance(pack_schema)
print(f"   Level: {mlcp_result['conformance_level'].upper()}")
print(f"   Status: {'✓ PASS' if mlcp_result['passed'] else '✗ FAIL'}")

if mlcp_result['issues']:
    print("\n   Issues:")
    for issue in mlcp_result['issues']:
        print(f"     - {issue}")

if comp_result['recommendations']:
    print("\n4. Recommendations:")
    for rec in comp_result['recommendations']:
        print(f"   • {rec}")

print("\n" + "=" * 60)
```

## Integration with CORE-385

This validation system is designed to be consumed by **CORE-385: Validation CLI Tool**, which will provide:

```bash
# Validate a single pack
legesher-i18n validate programming_languages/python/3.13/es.yml

# Validate all packs for a language
legesher-i18n validate programming_languages/python/*/es.yml

# Strict validation (fail on warnings)
legesher-i18n validate programming_languages/python/3.13/es.yml --strict

# Output as JSON
legesher-i18n validate programming_languages/python/3.13/es.yml --json
```

## References

- **MLCP v1.0 conformance:** specified by this document — see [Extended MLCP v1.0 Schema Support](#1-extended-mlcp-v10-schema-support) for the field set and [MLCP v1.0 Conformance Levels](#mlcp-v10-conformance-levels) for the core/extended/full criteria — and implemented in `SchemaValidator.check_mlcp_conformance`.
- **Test Suite:** `libs/i18n/tests/test_schema_validator.py`

## Changelog

### v1.0.0 (2025-01-04) - CORE-348

**Added:**

- Extended Pydantic schema with MLCP v1.0 fields (operators, standard_library, cultural_notes)
- Duplicate detection (`check_duplicates`)
- Enhanced completeness checking (`check_completeness_enhanced`)
- MLCP v1.0 conformance validation (`check_mlcp_conformance`)
- Comprehensive test suite (25+ tests)

**Changed:**

- Field validators now include operators and standard_library
- Completeness checking now integrates with version-index.yml

**Security:**

- Path traversal prevention maintained
- All new validators follow secure coding practices

---

**Maintained by:** Legesher Core Team
**License:** Apache 2.0 with Translation Exception
**Issue:** CORE-348
