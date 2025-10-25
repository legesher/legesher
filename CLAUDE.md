# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**Current Phase**: Early Development / Planning Complete
**Version**: 0.0.1
**Last Updated**: 2025-10-25

This is an active monorepo currently in early development phase. Most packages contain scaffold structure with minimal implementation. Planning documentation and implementation roadmap are in development.

## Repository Overview

This is the Legesher monorepo; a collection of developer tools and packages to enable developers to code in their native language instead of English. From creation within an IDE to collaboration across projects and git histories, Legesher's tools remove English as the pre-requisite of coding. The first programming language Legesher is focusing on is Python, but has plans to extend to other programming languages, so it is important to create scalability in the repo style. The project uses UV for dependency management and pdm-backend for building, with multiple Python packages organized in a monorepo structure.

It is important to note the need for the functionality to be extensible across multiple IDEs. We are building first for VS Code (and other editors that are built on top of vscode like Cursor and Windsurf), but should also consider Zed and JetBrains PyCharm etc.

## Architecture

### Monorepo Structure

- **Root**: Contains monorepo configuration with `pyproject.toml` defining all sub-packages
- **libs/**: Contains 5 Python packages with clear separation of concerns:
  - `core/`: Core translation engine and shared utilities (`legesher-core`)
  - `legesher/`: Main package with primary API and functionality
  - `i18n/`: Internationalization, localization, and natural language data (`legesher-i18n`)
  - `pride/`: Community features and project showcase (`legesher-pride`)
  - `vs-code/`: VS Code editor integration for Python language (`legesher-vs-code`)
    - Based on the `vscode-python` package (<https://github.com/microsoft/vscode-python>)
    - Provides language extensions for native language support within the editor
    - Includes declarative and programmatic language features for coding Python in native languages
- **docs/**: Astro-based documentation site using Starlight theme hosted at docs.legesher.io

**Future Packages** (planned, not yet created):


- `language-server/`: LSP server for IDE integration (static code analysis)
- Additional IDE integrations: Zed, JetBrains PyCharm

**Package Status** (as of 2025-10-21):
All packages currently contain minimal scaffold implementations with `__init__.py` files, empty `tests/` directories, empty `scripts/` directories, and empty `README.md` files.

### Package Management & Dependencies

- **UV**: Primary dependency manager with workspace support
- **pdm-backend**: Build backend for individual packages
- **Python Version**: Requires Python >=3.13
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

**Note**: Test suites are currently scaffolded but empty. Testing strategy will be documented as implementation progresses.

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


- `legesher-pride`: Community features, depends on `core`, `i18n`, and `legesher`
  - Community platform, showcase projects

When making changes, consider impact on dependent packages. Build order should follow the tier system (Tier 1 → Tier 2 → Tier 3 → Tier 4).

## Development Guidelines

### Adding New Dependencies

- Use `uv add <package>` from the root or navigate to specific package directory
- For cross-package dependencies, update the relevant `[tool.uv.sources]` section
- Always run `uv sync` after dependency changes

### Testing Strategy

- Each package should have its own test suite
- Run tests from package directories or use `uv run pytest` with specific paths
- Integration tests should consider cross-package functionality
- Releases can happen individually for each of the sub packages. For the main Legesher package, releases should pass integration tests with the updated versions of the sub packages before it can be released. Documentation should also be included for each of the changes.

### Code Organization

- Keep core translation logic in `libs/core/`
- Language-specific implementations in appropriate packages
- Editor integrations isolated in their respective packages
- Shared utilities and types in `libs/core/`

## Project Management

### Linear Integration

- Issues are managed in Linear workspace
- Project phases: Core Foundation → Developer Tools → Community Infrastructure → Registry & Scaling
- Issue labels help track progress across packages and phases

### Milestones

- **v0.1 (MVP)**: Basic translation, CLI, git integration, 3 language packs (ES, AR, ZH)
- **v0.5**: LSP server, VS Code extension, auto-update system
- **v0.8**: MLCP implementation, community features
- **v1.0**: Package registry, web UI, 10+ languages (24-week timeline)

### Issue Labels

- `package:core`, `package:i18n`, `package:legesher`, `package:vs-code`, `package:pride`
- `phase:1-foundation`, `phase:2-dev-tools`, `phase:3-community`, `phase:4-registry`
- `priority:high`, `priority:medium`, `priority:low`

## Quick Reference

### Essential Files

- [CLAUDE.md](CLAUDE.md) - This file (AI assistant guidance)
- [WORKING_WITH_AI_GUIDE.md](docs/WORKING_WITH_AI_GUIDE.md) - Guide for working with AI assistants
- Root `pyproject.toml` - Workspace configuration
- [README.md](README.md) - Project overview

### Key Documentation

Documentation is being developed in `docs/src/content/docs/`:

- Architecture guides (in development)
- MLCP (Multilingual Code Protocol) specification (planned)
- Implementation roadmap (planned)
- Language pack registry design (planned)

Current documentation:
- [Getting Started](docs/src/content/docs/index.mdx) - Project overview and quick start
- [Example Guides](docs/src/content/docs/guides/) - Usage examples
- [API Reference](docs/src/content/docs/reference/) - API documentation

### Key Architectural Decisions

**Translation Strategy**: Hybrid (local + cloud) → Progressive Enhancement
**Git Integration**: Canonical English storage via git filters (single source of truth)
**AST Transformation**: Token-based for MVP, Tree-sitter for production
**IDE Integration**: Language Server Protocol (multi-editor support)
**Python Versions**: Version-aware packs with inheritance (future-proof)
**Protocol**: MLCP (Multilingual Code Protocol) for ecosystem interoperability

Architectural rationale and detailed design decisions will be documented as the project evolves.

## Working with Claude Code

### Project Context

- This monorepo is in **early development phase** - packages have scaffold structure
- Planning and architecture documentation is being developed iteratively
- Implementation follows the tier system (Tier 1 → Tier 2 → Tier 3 → Tier 4)
- Issues are tracked in Linear workspace with package and phase labels

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