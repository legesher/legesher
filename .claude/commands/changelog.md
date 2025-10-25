<!--
SOURCES:
- Keep a Changelog: https://keepachangelog.com/
- Conventional Commits: https://www.conventionalcommits.org/
- Semantic Versioning: https://semver.org/
-->

# Update Changelog: $ARGUMENTS

**Goal**: Update CHANGELOG.md with recent changes following Keep a Changelog format.

## Instructions

Maintain a high-quality changelog that helps users understand what's changed between versions.

## Steps

### 1. Read Current CHANGELOG

```bash
# Check if CHANGELOG exists
if [ -f CHANGELOG.md ]; then
  cat CHANGELOG.md | head -50
else
  echo "No CHANGELOG.md found - will create one"
fi
```

### 2. Analyze Recent Changes

**Get commits since last release**:

```bash
# Find last tagged version
git describe --tags --abbrev=0 2>/dev/null || echo "No tags yet"

# Get commits since last tag (or all if no tags)
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$last_tag" ]; then
  git log $last_tag..HEAD --oneline --no-merges
else
  git log --oneline --no-merges | head -20
fi
```

**Categorize changes by conventional commit types**:

- `feat:` → **Added** section
- `fix:` → **Fixed** section
- `perf:` → **Changed** section (performance improvements)
- `refactor:` → **Changed** section (internal changes)
- `docs:` → **Changed** section (documentation)
- `test:` → Don't include (internal)
- `chore:` → Don't include (internal)
- `BREAKING CHANGE:` → **Changed** with ⚠️ marker

### 3. Keep a Changelog Format

Use this structure:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features for users

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Security improvements

## [0.1.0] - 2025-01-15

### Added
- Initial release
- Core translation engine

[Unreleased]: https://github.com/legesher/legesher/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/legesher/legesher/releases/tag/v0.1.0
```

### 4. Generate Changelog Entries

Based on commits since last release, draft changelog entries:

**Example entries**:

```markdown
### Added
- **i18n**: Version-aware language pack system with Python 3.10-3.13 support (#123)
- **i18n**: Spanish (es) and Arabic (ar) language packs with cultural comments (#124)
- **core**: Token-based AST transformer for keyword translation (#120)

### Changed
- **api**: Language pack loader is now async (⚠️ **BREAKING CHANGE**) (#125)
  - Migration: Use `await loader.load()` instead of `loader.load()`
- **docs**: Updated architecture guide with latest decisions (#126)

### Fixed
- **core**: Prevent infinite loop in AST transformer with deeply nested nodes (#127)
- **i18n**: Fix path traversal vulnerability in pack inheritance (#128)

### Security
- **i18n**: Add path sanitization to prevent directory traversal attacks (#128)
```

### 5. Update CHANGELOG.md

- Add entries to `[Unreleased]` section
- Group by category (Added, Changed, Fixed, etc.)
- Include PR/issue numbers for reference
- Use present tense: "Add feature" not "Added feature"
- Include package scope: `**core**:`, `**i18n**:`, etc.
- Mark breaking changes with ⚠️

### 6. Prepare for Release (If Releasing)

When ready to release:

1. **Move Unreleased to Version**:

```markdown
## [Unreleased]

(empty)

## [0.2.0] - 2025-01-20

### Added
- All the items from Unreleased
```

2. **Update version links at bottom**:

```markdown
[Unreleased]: https://github.com/legesher/legesher/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/legesher/legesher/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/legesher/legesher/releases/tag/v0.1.0
```

3. **Update package versions** in affected `pyproject.toml` files

### 7. Review Guidelines

**Good Changelog Entries**:

```markdown
✅ - **i18n**: Add Spanish language pack for Python 3.10-3.13 (#123)
✅ - **core**: Fix memory leak in AST transformer cache (#124)
✅ - **api**: Change pack loader to async for better performance (⚠️ BREAKING) (#125)
```

**Bad Changelog Entries**:

```markdown
❌ - Updated code
❌ - Fixed bugs
❌ - Various improvements
❌ - Commit abc1234 (don't reference commits, reference issues/PRs)
```

## Changelog Best Practices

### What to Include

- ✅ User-facing changes (features, fixes, breaking changes)
- ✅ Security updates
- ✅ Deprecation warnings
- ✅ Migration guides for breaking changes
- ✅ Performance improvements that users notice

### What NOT to Include

- ❌ Internal refactoring (unless it affects users)
- ❌ Test updates (unless new test coverage for users)
- ❌ CI/CD changes (unless it affects contribution workflow)
- ❌ Code formatting (unless it affects API)
- ❌ Documentation typos (unless fixing incorrect info)

### Writing Style

- **Be clear**: "Add Spanish language pack" not "Implement i18n"
- **Be specific**: Include versions, parameters, behavior
- **Be helpful**: Explain WHY, not just WHAT
- **Be user-focused**: How does this affect users?

### Breaking Changes

For breaking changes, include:

1. **What broke**: Which API/behavior changed
2. **Why it broke**: Rationale for the change
3. **How to migrate**: Code examples

Example:

```markdown
### Changed
- **api**: Language pack loader is now async (⚠️ **BREAKING CHANGE**) (#125)
  - **Migration**: Change `loader.load()` to `await loader.load()`
  - **Reason**: Async loading improves performance by 10x for large packs
  - **Example**:
    ```python
    # Before
    pack = loader.load('es', '3.12')

    # After
    pack = await loader.load('es', '3.12')
    ```
```

## Monorepo Considerations

For Legesher's monorepo:

**Option 1: Single CHANGELOG.md at root** (recommended for now):

- Tracks changes across all packages
- Use package prefixes: `**core**:`, `**i18n**:`, etc.
- Easier to see project-wide changes

**Option 2: Per-package CHANGELOGs**:

- `libs/core/CHANGELOG.md`
- `libs/i18n/CHANGELOG.md`
- Better for independent package releases
- More work to maintain

**For Legesher**: Use single root CHANGELOG until v1.0, then consider splitting for independent releases.

## Example for Legesher

```markdown
# Changelog

All notable changes to Legesher will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **i18n**: Version-aware language pack system with Python 3.10-3.13 support (#123)
- **i18n**: Spanish (es) and Arabic (ar) language packs (#124)
- **core**: Token-based AST transformer for keyword translation (#120)
- **vs-code**: Syntax highlighting for native language keywords (#130)

### Changed
- **api**: Language pack loader is now async for better performance (⚠️ **BREAKING**) (#125)
  - Migration: Use `await loader.load()` instead of `loader.load()`

### Fixed
- **core**: Prevent infinite loop in deeply nested AST nodes (#127)
- **i18n**: Fix path traversal vulnerability in pack inheritance (#128)

### Security
- **i18n**: Add path sanitization to prevent directory traversal attacks (#128)

## [0.1.0] - 2025-01-15

### Added
- Initial release of Legesher
- Core translation engine
- Git filter integration
- CLI tools for pack creation

[Unreleased]: https://github.com/legesher/legesher/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/legesher/legesher/releases/tag/v0.1.0
```

## Deliverable

Create or update CHANGELOG.md with:

- Recent changes categorized by type
- Clear, user-focused descriptions
- Issue/PR references for traceability
- Breaking change warnings with migration guides
- Proper Keep a Changelog formatting

Remember: Changelogs are for users, not developers. Focus on impact, not implementation.
