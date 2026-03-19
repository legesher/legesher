# Changelog - legesher-i18n-python-ur

All notable changes to this language pack.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2026-03-19

### Changed

- **Native Speaker Review** ([@rafaym1](https://github.com/rafaym1)):
  Applied 2 translation suggestions from community review [AYA-160]
  - `type` (builtin): `قسم` → `نوعیت` (reviewer preference for disambiguation)
  - `userwarning` (exception): `صارفانتباہ` → `صارفاطلاع` (reviewer preference)

### Added

- Community review suggestions added to translations.db with source `community_review`
  - [@sarr266](https://github.com/sarr266) & [@rafaym1](https://github.com/rafaym1)'s
    ur_modern (English transliterations in Urdu script) alternatives
  - Universal Python project Urdu alternatives

## [0.0.1] - 2026-03-10

### Added

- **Initial Urdu (اردو) Language Pack**
  - Complete keyword translations for Python 3.10-3.14
  - Built-in function and type translations
  - Exception class translations
  - Version-aware inheritance system (3.10 -> 3.11 -> 3.12 -> 3.13 -> 3.14)
  - Support for Python 3.10+ features (match/case)
  - Support for Python 3.11+ features (except\*)
  - Support for Python 3.12+ features (type parameter syntax)

### Translation Conventions

- **Underscores for readability**: Compound translations that combine a noun with a verb
  or predicate use underscores to improve readability in Nastaliq script (e.g.,
  `delattr` -> `خاصیت_مٹاؤ`, `isinstance` -> `مثال_ہے`). Single-concept compounds
  are concatenated without separators (e.g., `async` -> `غیرہمزمان`).

### Technical Details

- **Python Versions**: 3.10, 3.11, 3.12, 3.13, 3.14
- **Inheritance Depth**: 5 levels (3.10 base -> 3.14)
- **Translation Source**: Tiny Aya AI Model
- **Format**: YAML with version inheritance

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Legesher Monorepo](../../../)
