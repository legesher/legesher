# Changelog - Legesher Monorepo

All notable changes to the Legesher project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Added

- **Comprehensive Documentation Expansion** ([#37](https://github.com/madiedgar/legesher/pull/37), CORE-440)
  - **Beginner Guides**: Installation, getting started, and git workflow guides
  - **Translation Guide**: Language pack creation guide for contributors
  - **Glossary**: Technical terms dictionary with 29 entries
  - **Architecture Diagrams**: 5 Mermaid diagrams (package arch, translation flow, git workflow, LSP, pack inheritance)
  - **FAQ**: 35+ questions across 7 categories
  - **Code of Conduct**: Contributor Covenant 2.1 with multilingual programming focus
  - **Roadmap**: v0.1.0 through v1.0.0+ with community involvement details
  - **CLI Documentation**: Complete legesher package README with 5 main commands
  - Improves onboarding experience for new users and contributors
  - All documentation follows markdown best practices with 120-char line limit

## [0.1.0] - 2025-11-07

### First Public Release

The inaugural release of Legesher as a unified monorepo, enabling developers to code
in their native language instead of English.

---

## Package Releases

### Foundation Suite (v0.1.0) - Synchronized Release

Core packages released together with matching version numbers:

- **[legesher-core v0.1.0](libs/core/CHANGELOG.md)** - Translation engine
  - Token-based transformation with 91% test coverage
  - Git filter system for multilingual workflows
  - Metadata tracking for translation history
  - Spanish and Arabic language support
  - See [full changelog](libs/core/CHANGELOG.md)

- **[legesher-i18n v0.1.0](libs/i18n/CHANGELOG.md)** - Language pack system
  - Version-aware packs for Python 3.10-3.13
  - Translation API integration (DeepL, Google, LibreTranslate)
  - Comprehensive validation and CLI tools
  - Auto-update workflow for Python releases
  - See [full changelog](libs/i18n/CHANGELOG.md)

- **[legesher v0.1.0](libs/legesher/CHANGELOG.md)** - CLI tools
  - `legesher translate` command for file/directory translation
  - `legesher git` commands for repository setup
  - Configuration management system
  - Metadata visualization tools
  - See [full changelog](libs/legesher/CHANGELOG.md)

- **[legesher-language-server v0.1.0](libs/language-server/CHANGELOG.md)** - LSP implementation
  - Complete LSP server foundation
  - Hover, completion, and diagnostic providers
  - Pylance integration (Phase 1 complete)
  - 4,559 test lines with high coverage
  - See [full changelog](libs/language-server/CHANGELOG.md)

### Language Packs (v0.0.1) - Independent Releases

Language-specific translation packs released independently:

- **[legesher-i18n-python-es v0.0.1](libs/i18n-python-es/CHANGELOG.md)** - Spanish
  - 37 keyword translations
  - 34 built-in function translations
  - Version-aware for Python 3.10-3.13
  - See [full changelog](libs/i18n-python-es/CHANGELOG.md)

- **[legesher-i18n-python-ar v0.0.1](libs/i18n-python-ar/CHANGELOG.md)** - Arabic
  - 37 keyword translations with RTL support
  - 34 built-in function translations
  - Version-aware for Python 3.10-3.13
  - See [full changelog](libs/i18n-python-ar/CHANGELOG.md)

---

## Release Highlights

### Language Support

- **2 Languages**: Spanish (es), Arabic (ar)
- **RTL Support**: Full right-to-left text handling for Arabic
- **Version-Aware**: Automatic adaptation to Python 3.10, 3.11, 3.12, 3.13

### Testing & Quality

- **255 Tests** in legesher-core (91% coverage)
- **187 Tests** in legesher-i18n (99.97% pass rate)
- **66 Tests** in legesher CLI (97% coverage)
- **4,559 Test Lines** in language server
- **Multi-OS**: Linux, macOS, Windows
- **Multi-Python**: 3.10, 3.11, 3.12, 3.13

### Git Integration

- **Canonical English Storage**: Repository stores English, developers see their language
- **Automatic Translation**: On checkout, code translates to developer's preferred language
- **Zero Conflicts**: No merge conflicts from keyword differences
- **Multilingual Teams**: Spanish → English repo → Arabic workflow

### IDE Integration

- **Language Server Protocol**: Works with any LSP-compatible editor
- **Hover Documentation**: Translated docstrings and keyword info
- **IntelliSense**: Localized auto-completion
- **Diagnostics**: Error messages in native language
- **Pylance Integration**: Advanced type checking (Phase 1 complete)

### Automation

- **CI/CD Pipeline** ([#10](https://github.com/madiedgar/legesher/pull/10))
  - Automated testing on push/PR
  - Multi-OS and multi-Python testing
  - Code coverage reporting

- **Semantic Release** ([#34](https://github.com/madiedgar/legesher/pull/34))
  - Automated version bumping
  - Conventional commits enforcement
  - CHANGELOG generation
  - Hybrid versioning strategy

- **Release Workflows**
  - Foundation suite releases
  - Independent language pack releases
  - PyPI publishing ready

- **Python Language Pack Updates** ([#20](https://github.com/madiedgar/legesher/pull/20))
  - Monitors Python.org for new releases
  - Auto-generates base language packs
  - Creates translation issues for community

---

## Technical Achievements

### Performance

- **Translation Speed**: <2ms per file average
- **Round-Trip Fidelity**: 100% (EN→ES→EN is byte-identical)
- **Hover Response**: <5ms
- **Completion Response**: <10ms
- **Source Mapping**: O(log n) with SHA256 caching
- **Memory Usage**: <50MB for typical projects

### Architecture

- **Token-Based Transformation**: Preserves all formatting and comments
- **Tree-sitter Foundation**: Prepared for incremental parsing
- **LSP Implementation**: Editor-agnostic design
- **Version-Aware Packs**: Dynamic loading based on Python version
- **Metadata System**: Privacy-first translation history tracking

### Security

- **Privacy-First**: All translation local by default
- **No Code Storage**: Metadata contains only file paths and timestamps
- **Path Traversal Protection**: Security validation in pack loading
- **Circular Inheritance Detection**: Prevents infinite loops
- **Schema Validation**: Pydantic-based validation for all config files

---

## Infrastructure

### Repository Setup

- **Monorepo Structure**: Unified workspace with 8 packages
- **UV Package Manager**: Modern Python tooling
- **Pre-commit Hooks**: ruff, black, mypy, markdownlint
- **Code Quality**: Enforced linting and formatting

### Development Workflow

- **Conventional Commits**: Enforced via commitlint
- **Automated Testing**: 30% minimum coverage (increasing to 90%)
- **Semantic Versioning**: Automated based on commit messages
- **Pull Request Flow**: Protected main branch with required reviews

### Documentation

- **Comprehensive CHANGELOGs**: All packages fully documented
- **Architecture Docs**: Complete technical specifications
- **API Documentation**: All public APIs documented
- **Contributing Guidelines**: Clear contribution process
- **Linguistic Standards**: Translation quality guidelines

---

## What's Next?

### Immediate (Phase 2A Completion)

- **Pylance Integration Phase 2-4**: Complete LSP communication and testing
- **VS Code Extension**: First production-ready IDE integration
- **Beta Program**: Community testing and feedback

### Short-Term (Phase 2B-2D)

- **Tree-sitter Migration**: Performance improvements for real-time IDE translation
- **TypeScript Support**: JavaScript/TypeScript as second language
- **Multi-Language IDE**: Test language switching in single environment

### Long-Term (Phase 3-4)

- **Additional Languages**: French, German, Hindi, Chinese, and more
- **Community Infrastructure**: Language pack registry and review system
- **MLCP Registry**: Central repository for community language packs

See individual package CHANGELOGs for detailed implementation status:

- [legesher-core](libs/core/CHANGELOG.md)
- [legesher-i18n](libs/i18n/CHANGELOG.md)
- [legesher](libs/legesher/CHANGELOG.md)
- [legesher-language-server](libs/language-server/CHANGELOG.md)

---

## Breaking Changes

**None** - This is the first public release.

---

## Migration Guide

**Not applicable** - First release has no migrations.

---

## Contributors

This release was made possible by:

- **Madison Edgar** ([@madiedgar](https://github.com/madiedgar)) - Lead developer
- **Historical Contributors**: All contributors from the original Legesher repositories (2019-2024)

Special thanks to the community for 24 preserved language branches and 312 community translations that informed this release.

---

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)
- [Pull Requests](https://github.com/madiedgar/legesher/pulls)
- [Releases](https://github.com/madiedgar/legesher/releases)

---

## Support

- **Report Issues**: [GitHub Issues](https://github.com/madiedgar/legesher/issues/new)
- **Documentation**: See individual package CHANGELOGs
- **Discussions**: [GitHub Discussions](https://github.com/madiedgar/legesher/discussions)

---

**Format**: [Keep a Changelog](https://keepachangelog.com/)
**Versioning**: [Semantic Versioning](https://semver.org/)
**License**: Multi-license (MIT for core packages, see [LICENSE](LICENSE))
