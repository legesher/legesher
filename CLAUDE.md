# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**Current Phase**: Production-Ready (Pre-Beta)
**Version**: 0.5.0 (foundation packages), 0.1.4 (vs-code), 0.1.1 (language-server)
**Last Updated**: 2026-02-15

This is an active monorepo with **production-ready implementations** across all major packages. The project has
evolved significantly beyond initial planning and now features comprehensive test coverage, 26 supported language packs
(all in experimental status), complete LSP implementation, and a fully functional VS Code extension.

**Version Strategy:**

- **v0.5.x** (current): Pre-beta with 26 experimental language packs awaiting community validation
- **v1.0.0**: Major release after community validation with accepted language packs
- Language packs: **experimental** (current, works but unvalidated) → **accepted** (community validated)

**Language Status** (source of truth: `libs/i18n/legesher_i18n/languages.json`):

- **26 supported languages** - All currently in experimental status
- Experimental = translations work but await community validation
- Accepted = community-validated translations (future milestone)

## Repository Overview

This is the Legesher monorepo; a collection of developer tools and packages to enable developers to code in their
native language instead of English. From creation within an IDE to collaboration across projects and git histories,
Legesher's tools remove English as the pre-requisite of coding. The first programming language Legesher is focusing
on is Python, but has plans to extend to other programming languages, so it is important to create scalability in
the repo style. The project uses UV for dependency management and pdm-backend for building, with multiple Python
packages organized in a monorepo structure.

It is important to note the need for the functionality to be extensible across multiple IDEs. We are building first
for VS Code (and other editors that are built on top of vscode like Cursor and Windsurf), but should also consider
Zed and JetBrains PyCharm etc.

## Architecture

### Monorepo Structure

- **Root**: Contains monorepo configuration with `pyproject.toml` defining all sub-packages
- **libs/**: Contains Python packages with clear separation of concerns:
  - `core/`: Core translation engine and shared utilities (`legesher-core`)
  - `legesher/`: Main package with primary API and functionality
  - `i18n/`: Internationalization infrastructure AND language pack packages
    - `legesher_i18n/`: Core infrastructure (pack loading, validation, translation API)
    - `language-packs/python/`: **26 independently versioned Python language packs** (ar, da, de, el, en, es, fi, fr,
      he, hi, hu, id, it, ja, ko, ms, nl, no, pl, pt, ru, sv, th, tr, vi, zh)
    - `language-packs-archive/`: Legacy community translations (see private-working-memory repo)
  - `home/`: Digital home and community platform (`legesher-home`)
  - `vs-code/`: VS Code editor integration for Python language (`legesher-vs-code`)
    - Based on the `vscode-python` package (<https://github.com/microsoft/vscode-python>)
    - Provides language extensions for native language support within the editor
    - Includes declarative and programmatic language features for coding Python in native languages
  - `language-server/`: LSP server for IDE integration (static code analysis)
- **docs/**: Astro-based documentation site using Starlight theme hosted at docs.legesher.io

**Future Packages** (planned, not yet created):

- Additional IDE integrations: Zed, JetBrains PyCharm

**Package Status** (as of 2026-02-11):

| Package             | Version | Status           | Description                                                     |
| ------------------- | ------- | ---------------- | --------------------------------------------------------------- |
| **core**            | 0.5.0   | Production-ready | Token & tree-sitter translators, git filters, cultural comments |
| **i18n**            | 0.5.0   | Production-ready | 26 language packs (experimental), translation API, caching      |
| **legesher**        | 0.5.0   | Production-ready | CLI suite (init, translate, run, git, metadata), runtime hooks  |
| **language-server** | 0.1.1   | Production-ready | Full LSP with hover, completion, diagnostics, semantic tokens   |
| **vs-code**         | 0.1.4   | Production-ready | Extension with telemetry/feedback, all 26 languages supported   |
| **home**            | 0.1.0   | Minimal scaffold | Digital home for community features and project showcase        |

**Language pack versions**: 0.0.1–0.0.2 (see each pack's `pyproject.toml` for exact version)

All packages have test suites with 100+ test files across core, i18n, legesher, and language-server packages.

### Package Management & Dependencies

- **UV**: Primary dependency manager with workspace support
- **pdm-backend**: Build backend for individual packages
- **Python Version**: Requires Python >=3.10,<4.0 (development uses 3.13)
- **Cross-package dependencies**: Managed through `[tool.uv.sources]` sections in each package's `pyproject.toml`
- **Editable installs**: All packages installed in development mode for live updates

## Development Commands

### Initial Setup

```bash
# Install all dependencies and set up workspace
uv install

# Verify installation
uv run python -c "import legesher_core; print('Setup successful')"
```

### Python Development

```bash
# Work from root directory for most operations
uv install                    # Install/update all dependencies
uv run <command>             # Run commands in the UV environment
uv add <package>             # Add dependency to specific package
uv sync                      # Sync dependencies across workspace

# Package-specific work (navigate to libs/<package>/ if needed)
cd libs/core && uv run pytest              # Run tests for core package
cd libs/legesher && uv run python -m ...   # Run package-specific commands
```

### Testing

```bash
# Run tests for specific package
cd libs/core && uv run pytest
cd libs/i18n && uv run pytest -v

# Run all tests (when implemented)
uv run pytest libs/

# Run with coverage
uv run pytest --cov=legesher_core libs/core/
```

**Note**: All packages have comprehensive test suites with 100+ test files covering unit tests, integration tests,
and performance benchmarks. Test coverage includes round-trip translations, git workflows, LSP features, and more.

### Documentation Site

```bash
# From root directory
cd docs/
pnpm install                 # Install documentation dependencies (first time only)
pnpm dev                     # Start dev server at http://localhost:4321
pnpm build                   # Build static documentation for production
pnpm preview                 # Preview production build

# Documentation is built with Astro + Starlight
# All content is in docs/src/content/docs/
# Supports MDX format (Markdown + JSX components)
```

## Key Configuration Files

### Root Level

- **`pyproject.toml`**: Workspace configuration, shared dependencies, UV settings
- **`uv.lock`**: Lockfile for exact dependency versions
- **`poetry.toml`**: Poetry configuration (in-project virtualenv settings)
- **`.python-version`**: Specifies required Python version (3.13)
- **`.foundation`**: Foundation project metadata

### Package Level (`libs/*/`)

- **`pyproject.toml`**: Individual package metadata, dependencies, and build config
- **`[tool.uv.sources]`**: Cross-package dependency definitions for development

### Documentation

- **`docs/package.json`**: Documentation site dependencies and build scripts
- **`docs/astro.config.mjs`**: Astro and Starlight configuration

## CI/CD and Tooling

### GitHub Actions Workflows

Located in `.github/workflows/`:

- **`release-foundation.yml`**: Semantic release for foundation packages (core, i18n, legesher)
  - Triggers on push to main affecting `libs/core/`, `libs/i18n/`, `libs/legesher/`
  - Creates version tags, GitHub releases, builds artifacts
  - Syncs uv.lock after version bumps
- **`release-language-packs.yml`**: Independent language pack releases
  - Auto-detects changed packs and releases individually
  - Manual workflow dispatch for specific languages
- **`publish-pypi.yml`**: PyPI publishing pipeline
- **`monitor-python-releases.yml`**: Monitors Python.org for new releases to update packs

### Pre-commit Hooks

Install with `pre-commit install`. Configuration in `.pre-commit-config.yaml`:

- **General**: trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-json
- **Python**: Ruff linter and formatter (with auto-fix)
- **Markdown**: markdownlint with auto-fix
- **Custom**:
  - `validate-language-pack-yaml`: Validates language pack YAML structure
  - `regenerate-reference-docs`: Auto-regenerates REFERENCE.md when packs change
- **Commits**: Commitizen for conventional commit validation

### Semantic Release

Configuration in root `pyproject.toml` under `[tool.semantic_release]`:

- Commit parser: Angular
- Tag format: `v{version}` (foundation), `i18n-python-{lang}-v{version}` (language packs)
- Version files synchronized across foundation packages

### Commitizen

Interactive commit helper with conventional commits:

```bash
uv run cz commit
```

Supported scopes: `core`, `i18n`, `legesher`, `language-server`, `vs-code`, `home`, `i18n-python-{lang}`

## Package Interdependencies

The packages have a logical dependency hierarchy defined in the architecture:

**Tier 1 - Foundation**:

- `legesher-core`: Foundation package (no internal dependencies)
  - Token-based transformer, AST utilities, git filters

**Tier 2 - Language Support**:

- `legesher-i18n`: Depends on `core`
  - Version-aware language packs, translation API, cultural comments

**Tier 3 - User-Facing Tools**:

- `legesher`: Main package, depends on `core` and `i18n`
  - CLI tools, main API, end-to-end workflows
- `legesher-vs-code`: Editor integration, depends on `core` and `i18n`
  - IDE extensions, language client/server

**Tier 4 - Community**:

- `legesher-home`: Digital home and community platform, depends on `core`, `i18n`, and `legesher`
  - Community showcase projects

When making changes, consider impact on dependent packages. Build order should follow the tier system
(Tier 1 → Tier 2 → Tier 3 → Tier 4).

## Translation Database

The i18n package uses a consolidated SQLite database (`libs/i18n/legesher_i18n/db/translations.db`) with 4 tables.
See `libs/i18n/CLAUDE.md` for full schema details and query examples.

**Tables summary:**

| Table | Purpose | Key Constraint |
| ----- | ------- | -------------- |
| `terms` | Canonical reserved words (cross-language) | `UNIQUE(name, programming_language)` |
| `languages` | Language registry (38 languages: 26 with YAML packs, 12 legacy) | `code` PK (ISO 639-1) |
| `translations` | All translation suggestions (complete catalog) | `UNIQUE(term_id, language_code, source, translation)` |
| `selected_translations` | Active translation per term+language for YAML packs | `UNIQUE(term_id, language_code)` |

**Key design decisions:**

- `translations` is the complete catalog — every suggestion lives here, including the active YAML pack values
- `selected_translations` tracks which translation is currently chosen (decouples selection from suggestion)
- Duplicate suggestions from the same source are silently ignored (`INSERT OR IGNORE`)
- All foreign keys use cascading deletes; WAL mode enabled for concurrent access

## Language Pack Organization

Language packs are organized hierarchically within `libs/i18n/` for independent versioning and releases:

### Structure

```text
libs/i18n/language-packs/{programming-language}/{natural-language}/
```

**Example:** `libs/i18n/language-packs/python/ar/` (Arabic Python translations)

### Current Language Packs

**26 supported language packs** (all experimental) - Support Python 3.10-3.14 with version inheritance:

| Code | Language   | Native Name      | RTL | Status       |
| ---- | ---------- | ---------------- | --- | ------------ |
| ar   | Arabic     | العربية          | Yes | Experimental |
| da   | Danish     | Dansk            | No  | Experimental |
| de   | German     | Deutsch          | No  | Experimental |
| el   | Greek      | Ελληνικά         | No  | Experimental |
| en   | English    | English          | No  | Experimental |
| es   | Spanish    | Español          | No  | Experimental |
| fi   | Finnish    | Suomi            | No  | Experimental |
| fr   | French     | Français         | No  | Experimental |
| he   | Hebrew     | עברית            | Yes | Experimental |
| hi   | Hindi      | हिन्दी           | No  | Experimental |
| hu   | Hungarian  | Magyar           | No  | Experimental |
| id   | Indonesian | Bahasa Indonesia | No  | Experimental |
| it   | Italian    | Italiano         | No  | Experimental |
| ja   | Japanese   | 日本語           | No  | Experimental |
| ko   | Korean     | 한국어           | No  | Experimental |
| ms   | Malay      | Bahasa Melayu    | No  | Experimental |
| nl   | Dutch      | Nederlands       | No  | Experimental |
| no   | Norwegian  | Norsk            | No  | Experimental |
| pl   | Polish     | Polski           | No  | Experimental |
| pt   | Portuguese | Português        | No  | Experimental |
| ru   | Russian    | Русский          | No  | Experimental |
| sv   | Swedish    | Svenska          | No  | Experimental |
| th   | Thai       | ไทย              | No  | Experimental |
| tr   | Turkish    | Türkçe           | No  | Experimental |
| vi   | Vietnamese | Tiếng Việt       | No  | Experimental |
| zh   | Chinese    | 中文             | No  | Experimental |

All packs have 37 keywords and 81 builtins. Translations generated via Aya AI Model (except English reference).

### Independent Releases

Each language pack can be released independently:

- Tag format: `i18n-python-{lang}-v{version}`
- Example: Release `python-ar` v1.2.0 without affecting `python-es` v1.0.5
- Enables focused updates per language
- Separate changelogs and version histories

### Language Pack Version Inheritance

**IMPORTANT**: Language packs use version inheritance to avoid duplication. Each Python version's YAML file can extend
a previous version using the `extends` field.

**Structure:**

```text
libs/i18n/language-packs/python/{lang}/legesher_i18n_python_{lang}/packs/
├── 3.10.yml   # Base file with ALL translations
├── 3.11.yml   # extends: 3.10.yml (only new/changed terms)
├── 3.12.yml   # extends: 3.11.yml (only new/changed terms)
├── 3.13.yml   # extends: 3.12.yml (only new/changed terms)
└── 3.14.yml   # extends: 3.13.yml (only new/changed terms)
```

**Example 3.13.yml (inherits from 3.12):**

```yaml
language: ru
target: python
version: "3.13"
extends: 3.12.yml
keywords: {} # Empty = inherits all from 3.12
exceptions: {} # Empty = inherits all from 3.12
```

**When looking for translations:**

- Always check the **base file (3.10.yml)** first - this contains most translations
- Higher version files only contain NEW keywords/builtins added in that Python version
- The `extends` field tells you which file to check for inherited translations

**When updating translations:**

- Update the **base file (3.10.yml)** for terms that exist across all versions
- Only add to higher version files if the term is NEW to that Python version

### Adding New Language Packs

1. Create directory: `libs/i18n/language-packs/python/{lang}/`
2. Follow structure of existing packages (examine `ar/` or `es/`)
3. Create translation YAML files for each Python version (3.10-3.14)
4. Add package metadata: `pyproject.toml`, `CHANGELOG.md`, `README.md`, `__init__.py`
5. Update root `pyproject.toml`:
   - Add to `[tool.uv.sources]` section
   - Add to `[tool.uv.workspace]` members
6. Set version appropriately (check existing pack versions; currently 0.0.1–0.0.2)
7. Run `uv sync` to install in development mode

### i18n CLI Commands

The `legesher-i18n` CLI provides language pack management:

```bash
# Validate language packs
legesher-i18n validate path/to/pack.yml
legesher-i18n validate path/to/pack.yml --strict

# Show pack versions
legesher-i18n show es
legesher-i18n show ar --target python

# Registry commands
legesher-i18n registry list
legesher-i18n registry validate --lang es

# Export commands
legesher-i18n export json --lang es
legesher-i18n export csv --lang ar
```

### i18n Infrastructure Features

The `legesher-i18n` package includes:

- **Language Registry**: Centralized metadata in `libs/i18n/legesher_i18n/languages.json`
- **Translation API**: Multi-provider support (install with `pip install legesher-i18n[api]`)
  - Providers: Anthropic (Claude), Google Translate, DeepL, LibreTranslate
- **Caching**: Thread-safe LRU caching for fast pack loading
- **Schema Validation**: Pydantic-based validation with security checks

## Development Guidelines

### Adding New Dependencies

- Use `uv add <package>` from the root or navigate to specific package directory
- For cross-package dependencies, update the relevant `[tool.uv.sources]` section
- Always run `uv sync` after dependency changes

### Testing Strategy

- Each package should have its own test suite
- Run tests from package directories or use `uv run pytest` with specific paths
- Integration tests should consider cross-package functionality
- Releases can happen individually for each of the sub packages. For the main Legesher package, releases should
  pass integration tests with the updated versions of the sub packages before it can be released. Documentation
  should also be included for each of the changes.

### Code Organization

- Keep core translation logic in `libs/core/`
- Language-specific implementations in appropriate packages
- Editor integrations isolated in their respective packages
- Shared utilities and types in `libs/core/`

### Release Process

When bumping package versions or creating a release, follow these steps:

1. **Update the package's CHANGELOG.md** (`libs/<package>/CHANGELOG.md`)
   - Move `[Unreleased]` items into a new version heading with today's date
   - Use Keep a Changelog format: Added, Changed, Fixed, Removed
   - Reference Linear issue IDs (e.g., CORE-559)

2. **Update the root CHANGELOG.md**
   - Add a new version entry with the **Package Versions table** showing every package's version
   - Mark packages that changed with "Yes" in the Changed column
   - Summarize changes as bullet points below the table

3. **Bump the version** in `pyproject.toml` (or `package.json` for vs-code)

4. **A pre-commit hook** (`check-changelog-on-version-bump`) enforces this:
   - If a `pyproject.toml` or `package.json` version field changes, the corresponding
     `CHANGELOG.md` and root `CHANGELOG.md` must also be staged
   - Bypass with `git commit --no-verify` if needed

**Package version table template** (for root CHANGELOG.md):

```markdown
### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | x.y.z   | —        |
| legesher-i18n            | x.y.z   | Yes      |
| legesher (CLI)           | x.y.z   | —        |
| legesher-language-server | x.y.z   | —        |
| legesher-vscode          | x.y.z   | —        |
| legesher-home            | x.y.z   | —        |
```

## Project Management

### Linear Integration

- Issues are managed in Linear workspace
- Project phases: Core Foundation → Developer Tools → Community Infrastructure → Registry & Scaling
- Issue labels help track progress across packages and phases

### Milestones

- **v0.5.x** (current - Pre-Beta): Feature-complete with experimental language packs:
  - Two translator backends (token & tree-sitter)
  - 26 language packs with version inheritance (all experimental)
  - Complete CLI suite (init, translate, run, git, metadata)
  - Full LSP server with 4 providers (pygls 2.0)
  - VS Code extension with telemetry/feedback
  - MLCP (cultural comments) support
  - 100+ test files across packages
- **v1.0.0** (planned): Major release after community validation:
  - Community-validated language packs (experimental → accepted)
  - Package registry (see `docs/src/content/docs/architecture/language-pack-registry.md` - draft)
  - Additional IDE integrations (Zed, PyCharm)

### Issue Labels

- **Package**: `pkg:core`, `pkg:i18n`, `pkg:cli`, `pkg:language-server`, `pkg:vs-code`, `pkg:home`, `pkg:docs`,
  `pkg:preview`, `pkg:api`
- **Area**: `area:telemetry`, `area:translation`, `area:git`, `area:ci-cd`, `area:website`, `area:security`, `area:monetization`
- **Type**: `type:epic`, `type:test`, `type:release`
- **Triage**: `needs:triage`, `needs:review`, `needs:grooming`
- **Contribution**: `contrib:code`, `contrib:docs`, `contrib:localization`, `contrib:design`, `contrib:community`
- **Business**: `biz:applications`, `biz:partnerships`, `biz:coaching`
- **Platform**: `platform:saas-api`, `platform:slack`, `platform:buttondown`, `platform:huggingface`, `platform:instagram`

### Issue Naming Convention

Format: `[package/category:subcategory] Issue title`
Examples: `[vs-code:telemetry] Fix event tracking`, `[i18n:packs] Add dunder translations`

## Quick Reference

### Essential Files

- [CLAUDE.md](CLAUDE.md) - This file (AI assistant guidance)
- Root `pyproject.toml` - Workspace configuration
- [README.md](README.md) - Project overview

### Key Documentation

**Note**: The `docs/` folder contains some out-of-date content. Always verify against source code.

**Planning/Draft Documents** (not fully implemented):

- `docs/src/content/docs/specifications/mlcp-v1.md` - MLCP protocol draft specification
- `docs/src/content/docs/architecture/language-pack-registry.md` - Registry architecture (planned Q3 2026)
- `docs/src/content/docs/architecture/implementation-roadmap.md` - Development timeline

**Source of Truth** (use these instead of docs/):

- Package README.md files in `libs/*/README.md`
- `pyproject.toml` files for versions and dependencies
- `libs/i18n/legesher_i18n/languages.json` for language metadata

### Key Architectural Decisions

**Translation Strategy**: Hybrid (local + cloud) → Progressive Enhancement
**Git Integration**: Canonical English storage via git filters (single source of truth)
**AST Transformation**: Both token-based AND tree-sitter implementations complete and production-ready
**IDE Integration**: Language Server Protocol (multi-editor support)
**Python Versions**: Version-aware packs with inheritance (future-proof)
**Protocol**: MLCP (Multilingual Code Protocol) for ecosystem interoperability
**Language Abstraction** (CORE-415): Protocol-based interface for multiple translator backends and programming languages

#### Language Abstraction Interface (CORE-415)

Legesher uses a Protocol-based abstraction to support multiple translator backends and programming languages:

**Available Backends**:

- **TokenTranslator**: Token-based, simple, stable (~140μs for medium files)
- **TreeSitterTranslator**: AST-based, production-ready (~160μs for medium files)

**Factory Pattern**:

```python
from legesher_core import create_translator

# Default: TokenTranslator (or from environment)
translator = create_translator("python", keyword_map, builtin_map)

# Explicit tree-sitter backend
translator = create_translator("python", keyword_map, builtin_map, use_tree_sitter=True)
```

**Environment Configuration**:

```bash
# Use tree-sitter backend by default
export LEGESHER_USE_TREE_SITTER=true

# Or in .env file
LEGESHER_USE_TREE_SITTER=true
```

**Performance Benchmarks**:

```bash
# Run comprehensive benchmarks
cd libs/core
uv run pytest tests/benchmarks/ --benchmark-only

# Compare implementations
uv run pytest tests/benchmarks/ --benchmark-compare
```

**Future Languages**: TypeScript support is planned (see CORE-421 and related issues in backlog). The abstraction
provides clear extension points for new programming languages.

Architectural rationale and detailed design decisions will be documented as the project evolves.

## Working with Claude Code

### Project Context

- This monorepo is **production-ready (pre-beta)** with feature-complete packages
- 26 language packs available (all experimental, awaiting community validation)
- Implementation follows the tier system (Tier 1 → Tier 2 → Tier 3 → Tier 4)
- Issues are tracked in Linear workspace with package and phase labels
- See package-specific CLAUDE.md files in `libs/*/CLAUDE.md` for detailed guidance

### When Requesting Changes

- Specify which package(s) are affected
- Consider cross-package impacts for core functionality changes
- Test commands can be run with `uv run` prefix
- Documentation changes affect the `docs/` directory separately
- Implementation should follow the roadmap and architectural decisions in planning docs
- Reference specific issues from Linear when implementing features

### Important Constraints

- **Security**: Implement best security practices (critical for code translation tools that handle source code)
- **Extensibility**: Design for multiple programming languages (starting with Python, extending to others)
- **IDE Agnostic**: VS Code first, but consider Zed, PyCharm, Cursor, Windsurf in design decisions
- **Python Versions**: Version-aware language packs support Python 3.x evolution (see architecture docs)
- **Privacy**: Local-first approach for code translation (cloud optional, never required)
- **Performance**: Real-time translation in IDE requires fast AST transformation
- **Git Compatibility**: All git workflows must work seamlessly with canonical English storage

### Common Workflows

**Implementing a new feature**:

1. Find the issue in Linear workspace
2. Review relevant architectural decisions in this file
3. Identify affected package(s) in `libs/` and check tier dependencies
4. Implement following the architectural patterns
5. Add tests in the package's `tests/` directory
6. Update package README.md and docs as needed
7. Run `uv sync` and test across workspace

**Adding a new language pack**:

1. Create language pack in `libs/i18n/` following existing structure
2. Include keyword mappings, cultural comments, and metadata
3. Ensure version-aware pack structure for Python version compatibility
4. Add documentation and examples

**Updating documentation**:

1. Navigate to `docs/src/content/docs/`
2. Edit MDX files (Markdown + JSX)
3. Run `cd docs && pnpm dev` to preview
4. Documentation auto-deploys to docs.legesher.io
