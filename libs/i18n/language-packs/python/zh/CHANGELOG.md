# Changelog - legesher-i18n-python-zh

All notable changes to this language pack.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.5] - 2026-04-29

### Added

- `self` and `cls` reserved word translations [CORE-710]

## [0.0.4] - 2026-03-19

### Fixed

- **Native Speaker Review ([@NextME14](https://github.com/NextME14))**: Fixed 33 incorrect translations
  identified during community review [AYA-160]
  - **Keywords (14)**: Replaced English words and meaningless characters with proper Chinese
    - `elif`: `elseif` → `否则如果` (was English, not Chinese)
    - `lambda`: `玪抑` → `拉姆达` (meaningless characters)
    - `False`/`True`/`None`/`break`/`except`/`for`/`global`/`nonlocal`/`pass`/`raise`/`with`: corrected per reviewer
  - **Builtins (7)**: Removed English prefixes and fixed incomplete translations
    - `dir`: `dir_列出属性和方法` → `列出属性和方法` (removed English prefix)
    - `type`: added `类型` (was missing from builtins section)
    - `min`/`ord`/`sorted`/`super`/`zip`: corrected per reviewer
  - **Exceptions (12)**: Replaced English text and standardized Unicode terminology
    - `notadirectoryerror`: `Nosuchfileordirectory` → `非目录错误` (was fully English)
    - `valueerror`: `ValueError` → `值错误` (was fully English)
    - All Unicode exceptions now use `统一码` (Unicode Consortium's official Simplified Chinese term)
    - `eoferror`/`exception`/`isadirectoryerror`/`oserror`/`taberror`: corrected per reviewer

### Added

- Community review suggestions added to translations.db with source `community_review`

## [0.0.3] - 2026-02-25

### Fixed

- **Collision Resolution**: Resolved translation collisions where the same translated word mapped to
  multiple Python terms, breaking round-trip translation [CORE-605]
  - Changed terms: exception

## [0.0.2] - 2026-01-26

### Changed

- **Translation Completeness**: All 174 terms now have native translations
- **Validation Fixes**: Fixed translations containing invalid characters (spaces, hyphens, parentheses)
- **Quality Improvements**: Replaced English loan words with native language equivalents where appropriate

## [0.0.1] - 2025-12-09

### Added

- **Initial Chinese Simplified (简体中文) Language Pack**
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

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Legesher Monorepo](../../../)
