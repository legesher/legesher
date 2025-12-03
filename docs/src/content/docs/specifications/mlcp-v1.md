---
title: MLCP v1.0 Specification
description: Multilingual Code Protocol - Open standard for multilingual programming
---

# Multilingual Code Protocol (MLCP) v1.0

**Status:** Draft
**Version:** 1.0.0-draft
**Last Updated:** December 2025

## Abstract

The Multilingual Code Protocol (MLCP) is an open standard that enables programming in natural languages other than English. It defines a protocol for:

- Language pack discovery and distribution
- Code translation between natural languages
- IDE and tooling integration
- Community-driven translation validation

## Overview

MLCP provides a standardized way for tools to:

1. **Discover** available language packs for programming languages
2. **Translate** code between natural languages
3. **Validate** translation quality and correctness
4. **Collaborate** on multilingual codebases

## Core Concepts

### Language Packs

A language pack contains translations for a programming language's keywords, builtins, and standard library.

**Structure:**

```
language-pack/
├── metadata.json          # Pack information
├── keywords.yaml          # Keyword translations
├── builtins.yaml          # Builtin function translations
├── stdlib/                # Standard library translations
│   ├── os.yaml
│   ├── sys.yaml
│   └── ...
└── cultural-comments.yaml # Cultural context annotations
```

**Metadata:**

```json
{
  "name": "python-es",
  "version": "0.0.2",
  "language": "es",
  "programming_language": "python",
  "python_versions": ["3.10", "3.11", "3.12", "3.13", "3.14"],
  "author": "Legesher Community",
  "license": "MIT"
}
```

### Translation API

**Translate to Native Language:**

```typescript
POST /api/v1/translate
{
  "code": "def hello(name):\n    print(f'Hello, {name}!')",
  "from_language": "en",
  "to_language": "es",
  "programming_language": "python"
}

Response:
{
  "translated_code": "def hola(nombre):\n    imprimir(f'¡Hola, {nombre}!')",
  "confidence": 0.98,
  "warnings": []
}
```

### Registry Protocol

**Discover Language Packs:**

```typescript
GET /api/v1/packs?programming_language=python

Response:
{
  "packs": [
    {
      "name": "python-es",
      "version": "0.0.2",
      "language": "es",
      "downloads": 1234,
      "rating": 4.8
    },
    // ...
  ]
}
```

**Download Pack:**

```typescript
GET /api/v1/packs/python-es/0.0.2

Response: [tarball or zip file]
```

## Protocol Layers

### Layer 1: Syntax Translation

Translate programming language keywords and operators:

**Example (Python):**

- `def` → `función` (Spanish)
- `if` → `si` (Spanish)
- `for` → `para` (Spanish)

### Layer 2: Semantic Translation

Translate builtin functions and standard library:

**Example:**

- `print()` → `imprimir()` (Spanish)
- `len()` → `longitud()` (Spanish)
- `range()` → `rango()` (Spanish)

### Layer 3: Cultural Context

Annotate code with cultural and linguistic context:

**Example:**

```python
# Cultural context: In Spanish, "lista" can mean both "list" and "ready"
lista = [1, 2, 3]  # "lista" used as noun (list)
```

## Implementation Guidelines

### For Tool Developers

1. **Use Standard Pack Format:** Follow the language pack structure
2. **Support Versioning:** Handle pack version inheritance
3. **Validate Translations:** Check for conflicts and ambiguities
4. **Provide Fallbacks:** Gracefully handle missing translations

### For Language Pack Authors

1. **Follow Naming Conventions:** Use ISO 639-1 language codes
2. **Document Cultural Differences:** Explain linguistic nuances
3. **Test Thoroughly:** Validate all translations
4. **Version Appropriately:** Use semantic versioning

## Security Considerations

### Code Injection

- Sanitize all translation inputs
- Validate pack signatures
- Sandbox translation execution

### Privacy

- Don't collect code content without consent
- Anonymize telemetry data
- Comply with GDPR/CCPA

## Future Extensions

### MLCP v1.1 (Planned)

- Multi-language support (beyond Python)
- Real-time collaboration protocol
- AI-assisted translation suggestions

### MLCP v2.0 (Future)

- Cross-language translation (Python ↔ JavaScript)
- Dialect support (e.g., Brazilian vs. European Portuguese)
- Voice-based coding interfaces

## References

- [Language Pack Registry](/architecture/language-pack-registry/)
- [Implementation Roadmap](/architecture/implementation-roadmap/)
- [Getting Started](/getting-started/)

---

**Contributing:** This specification is open for community feedback. Submit proposals via [GitHub Issues](https://github.com/legesher/mlcp/issues).
