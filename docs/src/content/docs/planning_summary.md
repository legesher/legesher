---
title: Planning Summary
description: Legesher project planning overview and roadmap
---

# Planning Summary

## Project Overview

Legesher is a collection of developer tools that enable coding in native languages instead of English. The project is currently in active development with Phase 1 (Core Foundation) underway.

## Current Status

**Version:** 0.1.0 (MVP in development)
**Phase:** Core Foundation
**Last Updated:** December 2025

## Implementation Phases

### Phase 1: Core Foundation (Current)

**Goal:** Build the foundational translation engine and infrastructure

**Completed:**

- ✅ Token-based translator (140μs performance)
- ✅ Tree-sitter AST translator (160μs performance)
- ✅ Language pack loading system with caching
- ✅ 25+ language packs for Python 3.10-3.14
- ✅ VS Code extension with onboarding
- ✅ Telemetry infrastructure with ML training consent

**In Progress:**

- 🔄 Language Server Protocol implementation
- 🔄 Git filters for canonical English storage
- 🔄 CLI tools for translation

**Timeline:** Q1 2026

### Phase 2: Developer Tools

**Goal:** Complete IDE integration and developer workflows

**Planned:**

- Language server with hover, completions, diagnostics
- Git integration with dual-language commits
- Community translation contribution platform
- Translation correction tracking for ML training

**Timeline:** Q2 2026

### Phase 3: Community Infrastructure

**Goal:** Enable community-driven translations and validation

**Planned:**

- Language pack registry
- Community validation system
- Tutorial-code disconnect measurement
- Multilingual coding challenges platform

**Timeline:** Q3 2026

### Phase 4: Registry & Scaling

**Goal:** Scale to multiple programming languages and ecosystems

**Planned:**

- TypeScript/JavaScript support
- Multi-language protocol (MLCP) v1.0
- Package registry with auto-updates
- Web UI for language pack management

**Timeline:** Q4 2026

## Key Milestones

### v0.1 (MVP) - Q1 2026

- Basic Python keyword translation
- CLI tools
- 3 languages (ES, AR, ZH)
- Git integration

### v0.5 - Q2 2026

- LSP server
- VS Code extension
- 10+ languages
- Auto-update system

### v0.8 - Q3 2026

- MLCP implementation
- Community features
- Language pack registry

### v1.0 - Q4 2026

- 15+ languages
- Multi-language support (Python + TypeScript)
- Full web UI
- Production-ready

## Architecture Decisions

### Translation Strategy

**Chosen:** Hybrid (local + cloud) with progressive enhancement

- Local translation for keywords/builtins
- Cloud translation for arbitrary code (optional)
- Dual-backend support (token + tree-sitter)

### Git Integration

**Chosen:** Canonical English storage via git filters

- Single source of truth (English)
- Developer-specific language views
- Automatic bidirectional translation

### IDE Integration

**Chosen:** Language Server Protocol (LSP)

- Multi-editor support (VS Code, Cursor, Windsurf, Zed, PyCharm)
- Real-time translation
- Standard protocol compliance

### Language Packs

**Chosen:** Version-aware with inheritance

- Support Python 3.10-3.14
- Automatic version adaptation
- Independent releases per language

## Resources

- [MLCP Specification](/specifications/mlcp-v1/) - Protocol design
- [Implementation Roadmap](/architecture/implementation-roadmap/) - Detailed tasks
- [Language Pack Registry](/architecture/language-pack-registry/) - Registry design
- [Getting Started](/getting-started/) - Quick start guide

## Contributing

The project is in early development. To contribute:

1. Check the [GitHub Issues](https://github.com/legesher/legesher/issues)
2. Read [WORKING_WITH_AI_GUIDE.md](https://github.com/legesher/legesher/blob/main/docs/WORKING_WITH_AI_GUIDE.md)
3. See [Linear Workspace](https://linear.app/legesher) for active tasks

## Contact

- **GitHub:** [github.com/legesher/legesher](https://github.com/legesher/legesher)
- **Email:** <hello@legesher.io>
- **Discord:** [Join our community](https://discord.gg/legesher)

---

**Next:** See the [Getting Started](/getting-started/) guide to try Legesher!
