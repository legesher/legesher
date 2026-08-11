# ADR-003: Tree-sitter Migration

> **Maintainer notes — not newcomer documentation.** Written for someone already
> working in this code: it assumes repo context, uses internal vocabulary, and
> may cite work-tracker ids (`CORE-####`) an outside reader cannot resolve.
> Public on purpose, but not part of the documentation site and not localized —
> newcomer-facing documentation lives at [docs.legesher.io](https://docs.legesher.io).
> <!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

**Status:** Accepted
**Date:** 2025-01-05 (Implementation in Phase 2B, CORE-413)
**Deciders:** Madison Edgar
**Related Issues:** CORE-413 through CORE-420

## Context

Legesher initially used token-based transformation (Python's `tokenize` module) for
translating Python keywords between languages. While functional for the MVP (Phase 1),
this approach has several limitations that impact our ability to scale and provide
real-time IDE features:

### Token-Based Limitations

1. **Performance**: O(n) string manipulation with ~5ms per file
2. **No Incremental Parsing**: Must reparse entire file on every change
3. **Language-Specific**: Tied to Python's tokenize module, hard to extend to TypeScript, JavaScript, Rust
4. **No AST Awareness**: Cannot distinguish context (e.g., `type` as keyword vs. identifier)
5. **Limited Error Handling**: Fails on incomplete code (problematic during live typing)

### Requirements for Production

To support real-time IDE features (hover, autocomplete, diagnostics), we need:

- **< 50ms response time** for LSP operations
- **Incremental parsing** to only reparse changed portions
- **Multi-language support** for TypeScript, JavaScript (Phase 2C+)
- **Error tolerance** to handle incomplete code during typing
- **AST-aware translation** for context-dependent keywords

## Decision

**Migrate from token-based to tree-sitter-based parsing for Phase 2B and beyond.**

### Why Tree-sitter?

Tree-sitter is an industry-standard parser generator and incremental parsing library used by:

- **GitHub**: Code navigation and syntax highlighting
- **Atom/Zed**: Real-time syntax highlighting and code intelligence
- **Neovim**: Syntax highlighting and code analysis
- **GitHub Copilot**: Code understanding

### Implementation Approach

**Phase 2B (CORE-413 through CORE-420):**

1. CORE-413: Add dependencies and setup infrastructure
2. CORE-414: Implement TreeSitterTranslator class
3. CORE-415: Create language abstraction interface
4. CORE-416: Integrate incremental parsing
5. CORE-417: Performance benchmarking
6. CORE-418: Migrate tests
7. CORE-419: Add feature flag for gradual rollout
8. CORE-420: Documentation

**Gradual Migration:**

- Token-based transformer remains available via feature flag
- Users can opt-in to tree-sitter during Phase 2B
- Full switch to tree-sitter by Phase 3

## Consequences

### Positive

✅ **Performance**: ≥10x improvement (0.5ms vs 5ms per file)
✅ **Incremental Parsing**: 50x faster for real-time editing (0.1ms updates)
✅ **Multi-Language**: Foundation for TypeScript, JavaScript, Rust, Go
✅ **Error Tolerance**: Gracefully handles incomplete/invalid code
✅ **AST-Aware**: Context-sensitive translation (distinguish keyword vs. identifier)
✅ **Industry Standard**: Battle-tested by GitHub, Atom, Zed
✅ **Query Language**: Powerful pattern matching for complex transformations
✅ **Community**: Large ecosystem of grammars and tooling

### Negative

❌ **C Compiler Required**: Users need build tools for installation
❌ **More Complex API**: Steeper learning curve than tokenize
❌ **New Dependency**: External C library (though stable and mature)
❌ **Platform Considerations**: Need to document setup for Linux, macOS, Windows
❌ **Learning Curve**: Team needs to learn tree-sitter query language

### Neutral

◯ **Token-based Still Available**: Maintained for compatibility during transition
◯ **Gradual Migration**: Not a breaking change, users can opt-in
◯ **Query Language**: S-expression syntax is different but powerful

## Alternatives Considered

### Option A: Continue with Token-based (Rejected)

**Pros:**

- No new dependencies
- Simpler API
- Already implemented

**Cons:**

- Cannot meet performance requirements (<50ms)
- No incremental parsing
- Python-specific (blocks TypeScript support)
- Poor error tolerance

**Verdict:** ❌ Insufficient for production IDE features

### Option B: Python AST Module (Rejected)

**Pros:**

- Standard library (no dependencies)
- Full AST access

**Cons:**

- No incremental parsing
- Slower than tree-sitter (~2-3ms)
- Python-specific
- Fails on invalid code (not error-tolerant)
- More complex than needed

**Verdict:** ❌ Better than tokens but still insufficient

### Option C: Write Custom Parser (Rejected)

**Pros:**

- Full control
- Optimized for our specific use case

**Cons:**

- Months of development time
- Hard to maintain
- Unlikely to match tree-sitter performance
- Need to reimplement for each language

**Verdict:** ❌ Reinventing the wheel, not worth the effort

### Option D: Tree-sitter (Accepted) ✅

**Pros:**

- All requirements met (performance, incremental, multi-language, error-tolerant)
- Industry-proven (GitHub, Atom, Zed)
- Large community and ecosystem
- Active development
- Excellent documentation

**Cons:**

- Requires C compiler
- New dependency
- Team learning curve

**Verdict:** ✅ Best option for production-quality IDE features

## Implementation Details

### Dependencies

```toml
[project]
dependencies = [
    "tree-sitter>=0.20.4",
    "tree-sitter-python>=0.21.0",
]
```

### Module Structure

```text
libs/core/legesher_core/tree_sitter/
├── __init__.py          # Exports: PythonParser, TreeSitterError
├── parser.py            # PythonParser wrapper class
├── queries.py           # Pre-defined query patterns
└── README.md            # Usage documentation
```

### Key Classes

**`PythonParser`:**

- Wrapper around tree-sitter Python parser
- Methods: `parse()`, `parse_incremental()`, `query()`
- Handles grammar loading and error handling

**`TreeSitterError`:**

- Custom exception for tree-sitter operations
- Provides clear error messages

### Testing Strategy

- **41 comprehensive tests** covering:
  - Basic parsing (strings, bytes, Unicode)
  - Incremental parsing
  - Query execution
  - Error handling
  - Real-world Python code (async, match, type hints, etc.)
  - Performance characteristics
- **83% test coverage** (missing lines are defensive error handlers)

### Performance Targets

| Metric | Token-based | Tree-sitter | Improvement |
|--------|-------------|-------------|-------------|
| Initial parse | ~5ms | ~0.5ms | 10x faster |
| Incremental | ~5ms | ~0.1ms | 50x faster |
| LSP response | ~50-100ms | <50ms | 2-5x faster |

### Platform Support

**Supported:**

- macOS (Intel, ARM64)
- Linux (Ubuntu, Debian, Fedora, Arch)
- Windows (with Visual Studio Build Tools)

**Requirements:**

- Python 3.10+
- C compiler (gcc, clang, msvc)

## Migration Path

### Phase 2B (Weeks 11-14)

1. ✅ **CORE-413**: Setup infrastructure (this ADR)
2. **CORE-414**: Implement TreeSitterTranslator
3. **CORE-415**: Language abstraction
4. **CORE-416**: Incremental parsing integration
5. **CORE-417**: Benchmarking
6. **CORE-418**: Test migration
7. **CORE-419**: Feature flag
8. **CORE-420**: Documentation

### Phase 2C (Weeks 15-18)

- Use tree-sitter foundation for TypeScript support
- Validate multi-language approach

### Phase 3

- Default to tree-sitter for all users
- Deprecate token-based transformer
- Remove feature flag in Phase 4

## Success Metrics

- ✅ All tests passing (41/41)
- ✅ Dependencies install on macOS, Linux
- ✅ Coverage >80% (83% achieved)
- ✅ Documentation complete
- ⏳ Performance benchmarks (CORE-417)
- ⏳ Real-world testing in IDE (CORE-416)

## References

- [Complete Architecture Guide - AST Transformation](../../../../../private-working-memory/planning/architecture/complete-architecture-guide.md#ast-transformation-approaches)
- [Implementation Roadmap - Phase 2B](../../../../../private-working-memory/planning/architecture/implementation-roadmap.md#phase-2b-tree-sitter-foundation-weeks-11-14)
- [Tree-sitter Official Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Tree-sitter Python Grammar](https://github.com/tree-sitter/tree-sitter-python)
- [Tree-sitter Query Syntax](https://tree-sitter.github.io/tree-sitter/using-parsers#pattern-matching-with-queries)

## Notes

- This decision was made after extensive planning in Phase 1
- Token-based transformer (CORE-401) proved the concept
- Tree-sitter enables scale to production quality
- Community consensus: tree-sitter is the right choice for language tooling

---

**Last Updated:** 2025-01-05
**Next Review:** After CORE-420 (end of Phase 2B)
