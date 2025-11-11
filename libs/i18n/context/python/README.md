# Python Context Documents

This directory contains comprehensive translation context documents for Python keywords, builtin types, and builtin functions. Each document provides detailed linguistic and technical guidance to help AI translation models and human translators create accurate, consistent translations across multiple languages.

## Overview

- **Total Documents**: 121
- **Template Version**: Tier 1 (Concise Translation Brief)
- **Target Audience**: AI translation models, human translators, localization teams
- **Languages Covered**: Spanish, Arabic, Chinese, Hindi (with guidance for Romance, Germanic, Slavic language families)
- **Last Updated**: 2025-11-11

## Document Structure

Each context document follows a standardized 11-section template:

1. **Quick Summary** - 1-2 sentence overview of the term
2. **Code Examples FIRST** - 3 practical examples (minimal, common pattern, edge case)
3. **Pattern Classification** - Categorization and related terms
4. **Etymology** - Word origins and rationale for Python's choice
5. **Concept Explanation** - Intermediate-level technical explanation
6. **Linguistic Form Recommendation** - Part of speech and forms by language family
7. **Translation Examples** - Good translations and common mistakes
8. **Ambiguity Resolution** - Clarifying correct meaning in Python context
9. **Cross-References** - Consistency requirements with related terms
10. **Confidence Calibration** - Translation difficulty assessment
11. **Translation Validation Checklist** - 6-point verification checklist

## Coverage by Category

### Keywords (35 documents)
Control flow, conditional, loop control, exception handling, scope, and more:
- Conditionals: `if`, `elif`, `else`
- Loops: `for`, `while`, `break`, `continue`
- Pattern Matching (3.10+): `match`, `case`, `_` (wildcard)
- Functions: `def`, `return`, `yield`, `lambda`
- Classes: `class`
- Exception Handling: `try`, `except`, `finally`, `raise`, `assert`
- Imports: `import`, `from`, `as`
- Context Management: `with`
- Scope: `global`, `nonlocal`, `del`
- Operators: `and`, `or`, `not`, `in`, `is`
- Async: `async`, `await`
- Placeholder: `pass`

### Builtin Types (27 documents)
Core data types, type constructors, and exception classes:
- Boolean/None: `True`, `False`, `None`
- Numeric: `int`, `float`, `complex`
- Sequences: `str`, `list`, `tuple`, `range`, `bytes`, `bytearray`
- Collections: `dict`, `set`, `frozenset`
- Specialized: `slice`, `object`, `memoryview`
- Special Values: `Ellipsis` (`...`), `NotImplemented`
- Base Exceptions: `BaseException`, `Exception`, `StopIteration`
- Common Exceptions: `ValueError`, `TypeError`, `KeyError`, `IndexError`, `AttributeError`, `NameError`, `RuntimeError`

### Builtin Functions (59 documents)
Essential functions organized by purpose:

**Type Checking & Introspection:**
`type`, `isinstance`, `issubclass`, `callable`, `id`

**Container Operations:**
`len`, `sorted`, `reversed`, `enumerate`, `zip`, `all`, `any`, `sum`, `min`, `max`, `filter`, `map`

**Numeric Operations:**
`abs`, `round`, `pow`, `divmod`

**Conversion Functions:**
`int`, `str`, `float`, `bool`, `list`, `dict`, `tuple`, `set`, `frozenset`, `bytes`, `bytearray`, `complex`, `chr`, `ord`, `bin`, `hex`, `oct`, `ascii`, `repr`, `format`

**Attribute Access:**
`getattr`, `setattr`, `hasattr`, `delattr`, `vars`, `dir`

**Iterator Protocol:**
`iter`, `next`, `range`, `aiter`, `anext`

**OOP Decorators:**
`property`, `staticmethod`, `classmethod`, `super`

**I/O & Interaction:**
`input`, `print`, `open`, `help`

**Code Execution:**
`compile`, `eval`, `exec`, `__import__`

**Scope Access:**
`locals`, `globals`

**Hashing:**
`hash`

**Debugging:**
`breakpoint`

## Difficulty Levels

Documents are calibrated by translation difficulty:

- **EASY** (majority): Clear one-to-one mappings, universal concepts
- **MEDIUM** (subset): Some ambiguity or cultural considerations
- **HIGH** (advanced): Complex technical concepts, language-specific challenges

## Usage Guidelines

### For AI Translation Models

1. Read the entire context document for the term being translated
2. Follow the linguistic form recommendations for target language family
3. Review translation examples (good and bad) for guidance
4. Check cross-references to ensure consistency with related terms
5. Use the validation checklist before finalizing translation

### For Human Translators

1. Context documents provide technical accuracy and cultural considerations
2. Etymology sections explain why Python chose specific English terms
3. Code examples demonstrate actual usage in real programs
4. Translation mistakes section highlights common pitfalls to avoid
5. Cross-references maintain consistency across the entire Python vocabulary

### For Localization Teams

1. Use index.json to identify all terms requiring translation
2. Group related terms (e.g., all exception handling keywords) for consistency
3. Review linguistic standards document for overarching translation principles
4. Validate translations against code examples provided in each document
5. Test translations in actual Python code to ensure clarity

## File Naming Convention

All files use **lowercase** naming to match Python's syntax:
- Keywords: `if.md`, `for.md`, `class.md`
- Builtin types: `int.md`, `str.md`, `list.md`
- Builtin functions: `print.md`, `len.md`, `range.md`
- Special cases preserving Python's capitalization: `True.md`, `False.md`, `None.md`
- Dunder methods: `__import__.md`

## Linguistic Standards

All context documents follow the linguistic standards defined in:
`/home/user/legesher/libs/i18n/docs/linguistic-standards.md`

Key principles:
- Prefer verbs for action-oriented terms (functions, methods)
- Preserve proper nouns and technical acronyms (ASCII, Unicode)
- Maintain consistency within semantic clusters
- Consider word formation across language families
- Balance literal accuracy with natural language flow

## Quality Assurance

Each document includes:
- ✅ Comprehensive code examples (3 per document)
- ✅ Multi-language translation guidance (4+ languages)
- ✅ Etymology and rationale
- ✅ Common translation mistakes
- ✅ Cross-reference consistency checks
- ✅ Validation checklist

## Integration with Legesher

These context documents integrate with:
- **legesher-core**: Token-based transformer uses context for accurate translation
- **legesher-i18n**: Language pack generation references these documents
- **legesher-vs-code**: IDE integration displays context-aware tooltips
- **legesher-pride**: Community translation efforts use these as reference

## Contributing

When adding or updating context documents:

1. Follow the Tier 1 template structure (11 sections)
2. Include all required metadata (category, type, difficulty)
3. Provide 3 code examples with clear explanations
4. Add translation guidance for at least 4 languages
5. Update index.json with new document metadata
6. Ensure consistency with related term documents

## Version History

- **v1.0** (2025-11-11): Initial release with 121 Python context documents
  - 35 keywords (including Python 3.10+ pattern matching)
  - 27 builtin types (including common exceptions)
  - 59 builtin functions
  - Complete coverage of Python 3.x essential vocabulary including exceptions

## License

These context documents are part of the Legesher project and share the same open-source license. See the root LICENSE file for details.

## Contact

For questions, suggestions, or contributions:
- GitHub: https://github.com/legesher/legesher
- Documentation: https://docs.legesher.io
- Community: Join our discussions and contribute to making programming accessible in every language

---

**Generated by**: Claude Code (Anthropic)
**Template Version**: Tier 1 - Concise Translation Brief
**Purpose**: Optimized for AI translation models and human translators
