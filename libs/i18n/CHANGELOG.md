# Changelog - legesher-i18n

All notable changes to legesher-i18n are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

## [0.7.1] - 2026-03-16

## [0.7.0] - 2026-03-16

### Added

- **22 new language packs** — expanding Legesher from 29 → 51 supported
  languages (CORE-675, CORE-707)
  - **Bengali (বাংলা)** (CORE-718), **Bosnian (Bosanski)** (CORE-720),
    **Catalan (Català)** (CORE-735), **Croatian (Hrvatski)** (CORE-742),
    **Czech (Čeština)** (CORE-744), **Galician (Galego)** (CORE-756),
    **Gujarati (ગુજરાતી)** (CORE-764), **Irish (Gaeilge)** (CORE-769),
    **Kannada (ಕನ್ನಡ)** (CORE-795), **Latvian (Latviešu)** (CORE-807),
    **Macedonian (Македонски)** (CORE-808)
  - **Malayalam (മലയാളം)** (CORE-837), **Mongolian (Монгол)** (CORE-848),
    **Burmese (မြန်မာ)** (CORE-853), **Persian (فارسی)** (CORE-860),
    **Romanian (Română)** (CORE-879), **Scottish Gaelic (Gàidhlig)** (CORE-905),
    **Serbian (Српски)** (CORE-906), **Sundanese (Basa Sunda)** (CORE-915),
    **Telugu (తెలుగు)** (CORE-954), **Uzbek (O'zbek)** (CORE-961),
    **Welsh (Cymraeg)** (CORE-962)
  - Each pack includes complete Python 3.10–3.14 translations (37 keywords,
    72 builtins, 66 exceptions) with version inheritance
  - 3,850 new translations (175 per language × 22 languages)
  - Zero collisions across all 51 languages
  - Translation sources: Aya-101 AI Model (21 packs), Claude AI (Bosnian)
  - Persian (fa) is the 4th RTL language (joining Arabic, Hebrew, Urdu)
  - 3 Celtic languages added: Irish, Scottish Gaelic, Welsh
- **Language registry**: 22 new entries in `languages.json` with full metadata
  (native names, ISO 639-2 codes, script/family/numeral system)
- **REFERENCE.md**: Generated translation reference docs for all 22 new packs

## [0.6.0] - 2026-03-11

### Added

- **3 new language packs** — expanding Legesher from 26 → 29 supported
  languages (CORE-687)
  - **Amharic (አማርኛ)**: First Ge'ez-script language — complete Python
    3.10–3.14 translations (37 keywords, 72 builtins, 66 exceptions) with
    zero collisions. Translation source: Claude AI Model (CORE-690)
  - **Sinhala (සිංහල)**: First South Asian script language — complete Python
    3.10–3.14 translations (37 keywords, 72 builtins, 66 exceptions) with
    zero collisions. Translation source: Claude AI Model (CORE-1128)
  - **Urdu (اردو)**: Third RTL language in Legesher (joining Arabic and
    Hebrew) — complete Python 3.10–3.14 translations (37 keywords, 72
    builtins, 66 exceptions) with zero collisions. Translation source: Tiny
    Aya AI Model (CORE-1071)
  - 540 new translations imported into the translation database (180 per
    language, 0 collisions across all 29 languages)
  - Translation database updated: 40 total languages (29 YAML packs + 11
    legacy community)
- **Generic HuggingFace translation engine** — pluggable architecture for
  AI-powered translations, making it trivial to add new models (CORE-686)
  - `HFModelProfile` dataclass + registry — adding a new HF model requires
    only ~10 lines of profile config
  - `HuggingFaceModel` — local inference engine with lazy model loading,
    device auto-detection (CUDA/MPS/CPU), and retry with exponential backoff
  - `HuggingFaceAPIModel` — cloud inference engine via HF Inference API with
    built-in rate limiting
  - 4 pre-registered Tiny Aya (3.35B) profiles: earth, fire, water, global
    (CohereLabs/tiny-aya-{variant}) targeting underserved languages
  - New CLI flags: `--models hf|hf-api|tiny-aya|tiny-aya-api`,
    `--hf-profile <name>`, `--tiny-aya-variant earth|fire|water|global`
  - `DEFAULT_LANGUAGE_NAMES` mapping with 70+ languages (ISO 639-1 and 639-3)
  - 40 unit tests covering profiles, registry, prompt builder, dry-run
    translations, and pipeline validation — all run without ML dependencies

## [0.5.1] - 2026-03-01

### Changed

- **Consolidate Translation Databases** (CORE-594)
  - Redesign from flat single-table schema to normalized 4-table schema
    (`terms`, `languages`, `translations`, `selected_translations`)
  - Consolidate 3 drifted SQLite databases into one source of truth:
    179 terms, 38 languages, 2,445 translations, 4,527 selected translations
  - Rewrite `TranslationDatabase` API to use `term_id` foreign keys with
    cascading deletes instead of string-based `term`/`term_type` columns
  - Add `selected_translations` table decoupling active translation choices from suggestion sources
  - Add `terms` table with `UNIQUE(name, programming_language)` for multi-language extensibility
  - Add `languages` table preserving all 26 YAML pack languages + 12 legacy community languages
  - Update `pipeline.py`, `import_yaml_to_db.py`, `yaml_exporter.py` for new schema
  - Add CLI `db` subcommands: `init`, `stats`, `vacuum`
  - Rewrite test suite for new schema (40 unit tests, 4 integration tests)

### Fixed

- **Resolve 41 translation collisions across 17 languages** (CORE-605)
  - Same translated word mapped to 2+ Python terms, breaking round-trip translation
  - Add `find_collisions()` API and `db collisions` CLI command
  - Add collision guard to `set_selected()` preventing future collisions
  - Upgrade pre-commit YAML validator from warnings to errors for duplicates
  - Bump affected packs to v0.0.3: ar, el, fi, he, hi, hu, it, ko, no, pl, pt,
    ru, sv, th, tr, vi, zh
- Replace `datetime.UTC` with `timezone.utc` for Python 3.10 compatibility (CORE-662)

## [0.5.0] - 2026-02-01

### Changed

- Version bumped to align with monorepo v0.5.0 release
- No functional changes beyond 0.4.1 for i18n infrastructure

## [0.4.1] - 2026-01-31

### Added

- **Bundle Language Packs in i18n Wheel** (CORE-559)
  - Language pack YAML files now included directly in the `legesher-i18n` wheel
  - Users no longer need to install separate language pack packages
  - All 26 language packs available out of the box

### Fixed

- **Fix 33 mixed-script translations across 5 language packs** (CORE-531)
  - Greek (el): 15 entries — remove Latin characters, fully translate to Greek
  - Hebrew (he): 8 entries — remove Latin/Cyrillic, fix `property` invalid identifier (had `"` quotes)
  - Russian (ru): 8 entries — remove Latin characters, fully translate to Cyrillic
  - Arabic (ar): 1 entry — fix `memoryview` mixed Latin+Arabic
  - Finnish (fi): 1 entry — fix `isadirectoryerror` mixed scripts
- **Fix Japanese `in` keyword** (CORE-531): `～が～の中にある` → `含む` (valid Python identifier)
- **Add missing `type` builtin** to Spanish (`tipo`) and Arabic (`نوع`) packs (CORE-531)

## [0.4.0] - 2026-01-27

### Changed

- Version bumped to align with monorepo release
- No functional changes beyond 0.2.1 for i18n infrastructure

## [0.2.1] - 2026-01-26

### Added

- **New CLI Export Commands** (CORE-555)
  - `export json`: Export language pack to JSON format with Python doc links
  - `export csv`: Export language pack to CSV format with examples
  - `export all`: Export all available language packs with progress bar
  - All export commands support `--output -` for stdout piping
  - All export commands support `--dry-run` for preview mode
  - All commands now support `--quiet/-q` flag for CI/script usage

- **New CLI Registry Commands** (CORE-555)
  - `registry list`: List all available language packs with status
  - `registry validate`: Validate language pack translations against English reference
  - Support for `--strict` mode that fails on warnings

- **REFERENCE.md Auto-Generation** (CORE-555)
  - `scripts/generate_reference_docs.py` generates comprehensive REFERENCE.md for all 25 languages
  - Merges all version YAML files (3.10-3.14) with proper inheritance
  - Pre-commit hook auto-regenerates when YAML files change
  - Localized example code for each language

- **GitHub Actions Sync Workflow** (CORE-555)
  - `.github/workflows/sync-reference-docs.yml` syncs REFERENCE.md to preview-repo repo
  - Triggers on REFERENCE.md changes to main branch
  - Supports manual dispatch with force-sync option

- **Language Name Fallbacks** (CORE-555)
  - Added `LANGUAGE_NAME_FALLBACKS` dictionary for 26 common languages
  - Cached `_get_language_name()` function with `@lru_cache` for performance

### Changed

- **Schema Validator Enhanced Soft Keyword Support** (CORE-555)
  - `check_identifier_validity()` now passes source_key for soft keyword translations
  - Translations of soft keywords (e.g., `excepto*` for `except*`) validate correctly

### Fixed

- **Schema Validator Soft Keywords Support** (CORE-555)
  - Added `SOFT_KEYWORDS` set to handle Python 3.11+ soft keywords like `except*`
  - `except*` now passes schema validation instead of failing as invalid identifier
  - Translations of soft keywords also validate correctly (e.g., `excepto*` for Spanish)
  - Reference: <https://docs.python.org/3/reference/lexical_analysis.html#soft-keywords>

- **CLI Test Version Assertion** (CORE-555)
  - Fixed test expecting "0.0.1" to correctly expect "0.2.0"

## [0.2.0] - 2026-01-25

### Added

- **New Language Packs** (v0.2.0)
  - English (en): 39 keywords, 71 builtins, 69 exceptions, Python 3.10-3.14 (canonical reference)
  - All 26 languages: Complete translations via Aya AI Model pipeline

- **Comprehensive Directory Structure Tests** (PR #49)
  - New test file `tests/test_directory_structure.py` with 12 tests
  - Validates directory existence, path configuration, and inheritance
  - Tests PackLoader default path, YAML exporter, and CLI validation
  - Ensures backward compatibility (old `languages/` path not used)

### Changed

- **Language Pack Reorganization into Hierarchical Structure** (CORE-530)
  - Reorganized language packs from `programming_languages/` into hierarchical `language-packs/python/{lang}/` structure
  - Each language pack is now an independently versioned package (ar, es, en, fr, zh, etc.)
  - Enables focused releases per language (e.g., `python-ar` v1.2.0 independent of `python-es` v1.0.5)
  - Refactored `LanguagePackLoader` with importlib-based package discovery
  - Updated language-server integration to use new paths
  - Renamed legacy community archive: `language-packs/` → `language-packs-archive/`

- **Language Pack Version Constraints**
  - All language packs now require `>=0.2.0,<1.0.0`
  - Added Python 3.14 support across all language packs
  - Improved translation quality using Aya AI Model pipeline

### Fixed

- **Spanish Language Pack YAML Boolean Parsing** (PR #49)
  - Fixed `not: no` being parsed as boolean `False` instead of string `"no"`
  - Used YAML `!!str` type tag to force string type: `not: !!str no`
  - Fix survives pre-commit pretty-format-yaml hook

- **Python 3.14 Language Pack Support** (PR #49)
  - Added Python 3.14 language packs for all languages
  - Updated compatibility metadata in 3.10-3.13 packs to include 3.14
  - Fixed English language pack: expanded builtins, added `except*` keyword (3.11), corrected metadata

## [0.1.0] - 2025-11-07

### Added

- **Version-Aware Language Pack System** ([#3](https://github.com/madiedgar/legesher/pull/3), [b4c01f5](https://github.com/madiedgar/legesher/commit/b4c01f5c67d3a8025b39dc6196f58646d6f8fb04))
  - Dynamic language pack loading with automatic Python version detection (3.10-3.13+)
  - Pack inheritance system where child packs extend parents by defining only new features
  - Multi-strategy Python version detection: `pyproject.toml` → `.python-version` → runtime
  - Comprehensive security: path traversal protection, circular inheritance detection
  - High-performance caching for repeated pack loads
  - Complete Spanish (es) and Arabic (ar) language packs across all Python versions
  - `LanguagePackLoader` with version awareness and inheritance resolution
  - `PythonVersionDetector` for automatic environment version detection
  - `VersionIndex` for managing pack compatibility and inheritance chains
  - `SchemaValidator` with Pydantic-based validation
  - Package structure follows PEP 8 naming conventions (legesher_i18n)
  - Dependencies: pyyaml, pydantic, packaging

- **Translation Infrastructure and Language Packs** ([#14](https://github.com/madiedgar/legesher/pull/14), [5785621](https://github.com/madiedgar/legesher/commit/5785621a18ea1aecc00fb85735798efb38b4a624))
  - Complete translation infrastructure with bidirectional keyword mapping
  - Example language packs demonstrating inheritance and version-specific features
  - Two-tier context template system for AI and human translators
  - **Tier 1 Template** (1000-1500 words): Optimized for AI translation models with examples-first approach
  - **Tier 2 Template** (5000+ words): Comprehensive reference for human translators and beta testers
  - Comprehensive linguistic standards covering 8 critical areas:
    - Register & Formality Strategy (language-specific definitions)
    - Transliteration vs Translation Rules (decision framework)
    - Compound Term Strategy (builtins like isinstance, hasattr)
    - Capitalization & Case Conventions (comprehensive cross-script)
    - RTL Language Practical Requirements (Arabic, Hebrew IDE testing)
    - Ambiguity Resolution Framework (4-priority hierarchy)
    - Honorific & Politeness Levels (Japanese, Korean, Hindi neutral forms)
    - Gendered Language Rules (Romance, Arabic, German consistency)
  - Documentation expanded from 334 to 1,468 lines for translation quality
  - Expected AI translation approval rate: 85-90%

- **Auto-Update GitHub Actions Workflow** ([#20](https://github.com/madiedgar/legesher/pull/20), [033c822](https://github.com/madiedgar/legesher/commit/033c8223a6ccc733041604e809bb6bb30c070a72))
  - Automated monitoring of CPython repository for new major releases
  - Python content extraction script for all localizable elements:
    - 39 keywords (35 hard + 4 soft) via keyword module
    - 49 built-in functions with docstrings for IDE hover support
    - Built-in types with categorization
  - Two extraction methods: runtime (default) and GitHub API fetch
  - Multi-version support with comprehensive JSON output and metadata
  - GitHub Actions workflow for detecting new Python versions within 1 week
  - Automatic issue creation for new version language pack updates
  - Zero external dependencies beyond stdlib (urllib, json, yaml)
  - Successfully tested with Python 3.14 (184 items extracted)
  - Scripts: `extract_python_content.py`, `monitor_python.py`, `generate_language_pack.py`, `translate_content.py`

- **Translation API Integration** ([#22](https://github.com/madiedgar/legesher/pull/22), [71b40dd](https://github.com/madiedgar/legesher/commit/71b40dd78dfc933bbfcc45105c78b4f649910a91))
  - Multi-provider translation API with quality-based fallback system
  - Three translation providers with unified interface:
    - **DeepL**: Premium quality for European languages (133+ languages)
    - **Google Translate**: Best for Asian languages with broad coverage
    - **LibreTranslate**: Self-hosted, open-source, privacy-focused (20+ languages)
  - Quality scoring matrix for language pair optimization
  - Intelligent provider selection based on quality scores per language pair
  - Async/await support for high-performance translation
  - Usage tracking: characters translated, request counts, cost estimation
  - Rate limiting (10 req/sec default, configurable per provider)
  - SQLite and Redis cache backends for translation caching
  - Quality validator for translation verification
  - Usage tracker with cost monitoring and analytics
  - Dashboard for monitoring translation API usage and costs
  - CLI tools: `legesher-api` for provider management and monitoring
  - Optional installation: `pip install legesher-i18n[api]`
  - Zero cost option via self-hosted LibreTranslate

- **Comprehensive Language Pack Validation** ([#23](https://github.com/madiedgar/legesher/pull/23), [aa7ff26](https://github.com/madiedgar/legesher/commit/aa7ff268a1d640376c078d3273bc2f9c0557abb7))
  - MLCP v1.0 specification conformance validation
  - Three conformance levels: core (keywords), extended (+operators), full (+stdlib)
  - Duplicate detection across all mapping types (keywords, operators, builtins)
  - Enhanced completeness checking with version-index integration
  - Extended MLCP v1.0 schema supporting:
    - Operators (arithmetic, logical, comparison, bitwise)
    - Standard library mappings
    - Cultural notes and annotations
  - ISO 639-1/639-2 language code validation (2-3 letter codes)
  - Comprehensive error reporting with actionable messages
  - VALIDATION.md documentation (comprehensive validation guide)
  - Test coverage: 25+ validation tests across conformance levels
  - Schema enhancements: +350 lines to `schema_validator.py`
  - Security: validates pack structure, prevents malformed packs

- **Language Pack Validation CLI and Compatibility Matrix** ([#24](https://github.com/madiedgar/legesher/pull/24), [bda4dc9](https://github.com/madiedgar/legesher/commit/bda4dc93a66bf9616eed76df319b4502382d1757))
  - Command-line interface for language pack validation and testing
  - Compatibility matrix generator for keyword coverage across Python versions
  - Interactive validation with rich terminal output (colors, tables, progress bars)
  - Commands:
    - `validate`: Validate language pack YAML files with MLCP conformance
    - `test`: Test pack loading and inheritance resolution
    - `matrix`: Generate keyword compatibility matrix across Python versions
    - `info`: Display detailed pack information and statistics
  - Matrix generation script: `generate_compatibility_matrix.py`
  - Markdown documentation generation for compatibility (e.g., `es-keywords.md`)
  - Pre-commit hook documentation for automated validation
  - CI/CD integration documentation for GitHub Actions
  - Entry point: `legesher-i18n` command
  - Dependencies: click (CLI framework), rich (terminal formatting)
  - CLI test coverage: 260+ lines testing all commands

### Performance

- **Translation Speed**: <2ms average per pack load (with caching)
- **Cache Hit Rate**: >95% for repeated pack loads
- **Test Coverage**: 187 passing tests, 5 skipped (99.97% passing rate)
- **Test Suite Size**: 3,657 lines across 12 test files
- **Supported Python Versions**: 3.10, 3.11, 3.12, 3.13
- **Supported Languages**: Spanish (es), Arabic (ar), English (en) reference
- **Language Packs**: 13 total (4 Python versions × 3 languages + version-index.yml)
- **API Provider Coverage**: 3 providers (DeepL, Google, LibreTranslate) with 150+ languages
- **Memory Usage**: <20MB for typical language pack operations

### Technical Details

- **Architecture**: Inheritance-based pack system with version-aware loading
- **Storage Format**: YAML for language packs with Pydantic schema validation
- **API Design**: Async-first with optional sync wrappers
- **Security**: Path traversal protection, circular inheritance detection, ISO language code validation
- **Caching Strategy**: In-memory LRU cache for pack loader, SQLite/Redis for translation API
- **Testing**: pytest with async support (pytest-asyncio) and mocking (pytest-mock, responses)
- **Documentation**: 7 markdown files covering linguistic standards, API usage, and validation
- **Scripts**: 5 automation scripts for extraction, monitoring, generation, and translation
- **Dependencies**: Minimal required (pyyaml, pydantic, packaging, click, rich)
- **Optional Dependencies**: Translation API providers (deepl, google-cloud-translate, httpx, redis)
- **API Stability**: Public API stable, internal API may change
- **MLCP Compliance**: Full v1.0 specification support
- **Breaking Changes**: None (first release)

---

## Development Info

### Running Tests

```bash
cd libs/i18n
uv run pytest tests/ -v
```

### Test Coverage

```bash
cd libs/i18n
uv run pytest tests/ --cov=legesher_i18n --cov-report=html
open htmlcov/index.html
```

### Running CLI

```bash
cd libs/i18n

# Validate a language pack
uv run legesher-i18n validate language-packs/python/es/legesher_i18n_python_es/packs/3.13.yml

# List available language packs
uv run legesher-i18n registry list

# Validate all language packs
uv run legesher-i18n registry validate --lang all
```

### Translation API Setup

```bash
# Install with API support
uv add legesher-i18n[api]

# Or for development
cd libs/i18n
uv sync --group dev
```

### Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)
- [Legesher Monorepo CHANGELOG](../../CHANGELOG.md)
- [Documentation](./docs/README.md)
- [Linguistic Standards](./docs/linguistic-standards.md)
- [Translation API Guide](./docs/translation-api.md)
- [Validation Guide](./docs/VALIDATION.md)
