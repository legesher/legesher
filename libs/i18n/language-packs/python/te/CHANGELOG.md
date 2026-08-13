# Changelog - legesher-i18n-python-te

All notable changes to this language pack.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `except*` now carries the mirrored trailing `*`: `మినహాయింపుగుంపు` →
  `మినహాయింపుగుంపు*`. The translator handles `except*` as a compound — it strips a
  trailing `*` from the translation and re-emits the source's own `*` token.
  Without the mirror, reverse translation could not match the compound, so
  the plain `except` entry matched and the `*` landed on an already complete
  `except*`, producing `except**`, which does not parse. Syntax marker only:
  the translated word is unchanged. [CORE-1839]

## [0.0.2] - 2026-04-29

### Added

- `self` and `cls` reserved word translations [CORE-710]

## [0.0.1] - 2026-03-15

### Added

- **Initial Telugu (తెలుగు) Language Pack**
  - Complete keyword translations for Python 3.10-3.14
  - Built-in function and type translations
  - Exception class translations
  - Version-aware inheritance system (3.10 → 3.11 → 3.12 → 3.13 → 3.14)
  - Support for Python 3.10+ features (match/case)
  - Support for Python 3.11+ features (except\*)
  - Support for Python 3.12+ features (type parameter syntax)

### Technical Details

- **Python Versions**: 3.10, 3.11, 3.12, 3.13, 3.14
- **Inheritance Depth**: 5 levels (3.10 base → 3.14)
- **Translation Source**: Aya AI Model
- **Format**: YAML with version inheritance

## Links

- [GitHub Repository](https://github.com/legesher/legesher)
- [Legesher Monorepo](../../../)
