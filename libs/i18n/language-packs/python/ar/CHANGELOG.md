# Changelog - legesher-i18n-python-ar

All notable changes to this language pack.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-11-17

### Added

- Python 3.14 support
- 47 additional builtin terminology translations (88 total builtins)

### Changed

- Improved translation quality from AI pipeline using Aya AI Model
- Migrated to new monorepo structure under libs/i18n/language-packs/

## [0.0.1] - 2025-11-07

### Added

- **Initial Arabic Language Pack**
  - Complete keyword translations for Python 3.10-3.13
  - 37 keywords translated (تعريف, صنف, إرجاع, إذا, بينما, لـ, etc.)
  - 34 built-in function translations (طباعة, طول, نطاق, قائمة, قاموس, etc.)
  - Logical operators (و, أو, ليس)
  - Constants (صحيح, خطأ, لاشيء)
  - Version-aware inheritance system (3.10 → 3.11 → 3.12 → 3.13)
  - Support for Python 3.10+ features (match/case)
  - Support for Python 3.11+ features (except*)
  - Support for Python 3.12+ features (type parameter syntax)
  - RTL (right-to-left) text support

### Technical Details

- **Total Translations**: 71+ entries
- **Python Versions**: 3.10, 3.11, 3.12, 3.13
- **Inheritance Depth**: 4 levels (3.10 base → 3.13)
- **Validation**: Schema validated, completeness verified
- **Format**: YAML with Pydantic validation

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Legesher Monorepo CHANGELOG](../../CHANGELOG.md)
