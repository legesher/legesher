# Contributing to Legesher

Thank you for your interest in contributing to Legesher! This document explains how to contribute to this
multi-license repository.

## New to Open Source?

Welcome! We're excited to have you. Open source contribution might seem intimidating at first, but we're here to help.

### What is Open Source?

Open source means the code is publicly visible and accepts contributions from anyone. You can:

- **Report bugs** you find while using the project
- **Suggest features** you'd like to see
- **Fix typos** in documentation
- **Translate** content to your native language
- **Write code** to add features or fix bugs

### Your First Contribution

Not sure where to start? Here are beginner-friendly ways to contribute:

1. **Fix Documentation:** Found a typo? Confusing explanation? Documentation PRs are always welcome!
2. **Translate Language Packs:** Native speaker of a language we don't support yet? Create a language pack!
3. **Report Bugs:** Found something broken? Open an issue with reproduction steps.
4. **Answer Questions:** Help other users in GitHub Discussions.
5. **Good First Issues:** Look for issues tagged `good-first-issue` - these are designed for newcomers.

### Resources for Beginners

- **[GitHub's Guide to Open Source](https://opensource.guide/)** - Learn the basics
- **[First Timers Only](https://www.firsttimersonly.com/)** - Resources for first-time contributors
- **[How to Contribute](https://opensource.guide/how-to-contribute/)** - Step-by-step guide

### Getting Help

Stuck? Don't hesitate to ask! We're here to help:

- **GitHub Discussions:** Ask questions and discuss ideas
- **Issue Comments:** Comment on issues for clarification
- **Draft PRs:** Open a draft pull request and ask for feedback early

**Remember:** Everyone was a beginner once. We're patient and welcoming to newcomers!

## Repository License Structure

This repository contains packages with different licenses. Please review the licensing structure before contributing:

### Open Source Packages (MIT License)

We welcome community contributions to these packages:

- **`libs/core/`** - Core translation engine and shared utilities
- **`libs/i18n/`** - Internationalization and language data
- **`libs/vs-code/`** - VS Code editor integration

These packages are fully open source under the MIT License. Your contributions will be licensed under the same terms.

### Dual-Licensed Package (MIT + Commercial)

- **`libs/legesher/`** - Main package with CLI and primary API

The free tier features use the MIT License. Premium features require a commercial license. Contributions to free tier
features are welcome.

### Proprietary Packages

- **`libs/pride/`** - Community features and project showcase

These packages are source-available but proprietary. We do NOT accept external contributions to these packages at this time.

## How to Contribute

### 1. Reporting Issues

- Search existing issues to avoid duplicates
- Use the issue templates when available
- Include clear reproduction steps for bugs
- Suggest use cases for feature requests

### 2. Contributing Code

#### Before You Start

1. Check if the package accepts contributions (see license structure above)
2. Open an issue to discuss significant changes
3. Fork the repository
4. Create a feature branch from `main`

#### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/legesher.git
cd legesher

# Install dependencies
uv sync --all-extras

# Set up pre-commit hooks (RECOMMENDED)
uv run pre-commit install

# Run tests
uv run pytest

# Work on a specific package
cd libs/core
uv run pytest
```

#### Pre-commit Hooks (RECOMMENDED)

We use pre-commit hooks to automatically check and format code before committing. This ensures code quality and
prevents CI/CD failures.

**Setup:**

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Install commit message validation hooks
uv run pre-commit install --hook-type commit-msg --hook-type pre-push
```

**What gets checked automatically:**

- ✅ Code formatting with Black
- ✅ Linting with Ruff (auto-fixes when possible)
- ✅ Trailing whitespace and file endings
- ✅ YAML/TOML/JSON syntax validation
- ✅ Large file detection
- ✅ Merge conflict markers
- ✅ Private key detection
- ✅ **Commit message validation** (Conventional Commits format)

**Manual runs:**

```bash
# Run hooks on all files (useful after setup)
uv run pre-commit run --all-files

# Run hooks on specific files
uv run pre-commit run --files libs/core/legesher_core/transformer.py

# Update hooks to latest versions
uv run pre-commit autoupdate
```

**Skipping hooks (use sparingly):**

```bash
# Skip pre-commit hooks for a single commit
git commit --no-verify -m "Your message"
```

**Note:** Type checking with mypy is optional in pre-commit (can be slow). It will always run in CI/CD regardless.

#### Making Changes

1. Write clear, focused commits
2. Follow existing code style and conventions
3. Add tests for new functionality
4. Update documentation as needed
5. Ensure all tests pass

#### Submitting Pull Requests

1. Push changes to your fork
2. Create a pull request against `main`
3. Fill out the PR template completely
4. Link related issues
5. Respond to review feedback

### 3. Contributing to Documentation

Documentation contributions are always welcome! The documentation site is in the `docs/` directory.

```bash
cd docs/
pnpm install
pnpm dev
```

## Contributor License Agreement

### For Open Source Packages (MIT Licensed)

By contributing to MIT-licensed packages (`core`, `i18n`, `vs-code`), you agree that:

1. Your contributions will be licensed under the MIT License
2. You have the right to license your contribution under these terms
3. You understand your contributions become part of the public open source project

### For Dual-Licensed Package (`legesher`)

By contributing to the `legesher` package, you agree that:

1. Your contributions to free tier features will be licensed under MIT
2. Your contributions may also be used in the commercial/premium tier
3. Legesher retains the right to use your contributions in both the free and commercial versions
4. You will be credited as a contributor

### Copyright Assignment

We do NOT require copyright assignment. You retain copyright to your contributions, but you grant Legesher a perpetual
license to use your contributions under the project's license terms.

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what's best for the community
- Show empathy toward others
- Accept constructive criticism gracefully

### Unacceptable Behavior

- Harassment, discrimination, or exclusionary behavior
- Trolling, insulting comments, or personal attacks
- Publishing others' private information
- Any conduct that could be considered unprofessional

### Enforcement

Violations may result in temporary or permanent ban from the project. Report issues to: <conduct@legesher.com>

## Development Guidelines

### Testing

All code contributions must include tests. We use pytest for testing with a 30% minimum coverage requirement
(gradually increasing to 90% as the codebase matures).

#### Running Tests Locally

**Install development dependencies:**

```bash
# Install all packages with dev dependencies
uv pip install -e "libs/core[dev]"
uv pip install -e "libs/i18n[dev]"
uv pip install -e "libs/legesher[dev]"
```

**Run all tests:**

```bash
# Test all packages
cd libs/core && uv run pytest
cd libs/i18n && uv run pytest
cd libs/legesher && uv run pytest
```

**Run tests with coverage:**

```bash
# legesher-core
cd libs/core && uv run pytest --cov=legesher_core --cov-report=html

# legesher-i18n
cd libs/i18n && uv run pytest --cov=legesher_i18n --cov-report=html

# legesher (main package)
cd libs/legesher && uv run pytest --cov=legesher --cov-report=html

# View coverage report
open libs/core/htmlcov/index.html
```

**Run specific tests:**

```bash
# Run single test file
cd libs/core && uv run pytest tests/unit/test_transformer.py

# Run single test function
cd libs/core && uv run pytest tests/unit/test_transformer.py::test_specific_function

# Run tests by marker
cd libs/core && uv run pytest -m unit
cd libs/core && uv run pytest -m integration
```

#### CI/CD Testing

All pull requests automatically run tests via GitHub Actions:

- **Python versions**: 3.10, 3.11, 3.12, 3.13
- **Operating systems**: Ubuntu, macOS, Windows
- **Coverage threshold**: 30% (will increase to 90% as codebase matures)

Tests must pass on all platforms before merging to `main`.

#### Writing Tests

**Test organization:**

- `tests/unit/` - Unit tests (test individual functions in isolation)
- `tests/integration/` - Integration tests (test interactions between components)

**Test naming conventions:**

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

**Example test:**

```python
def test_translate_keyword_from_spanish_to_english():
    """Test translating 'definir' (Spanish) to 'def' (English)."""
    # Arrange
    translator = KeywordTranslator(source_lang="es", target_lang="en")

    # Act
    result = translator.translate("definir")

    # Assert
    assert result == "def"
```

**Coverage requirements:**

- Write tests for all new functionality
- Ensure existing tests pass before submitting PR
- Aim for 80%+ coverage on new code
- Test edge cases and error conditions

### Code Style

- Follow existing patterns in the codebase
- Use type hints in Python code
- Write clear, self-documenting code
- Add comments for complex logic

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Reference issue numbers when applicable
- Keep the first line under 72 characters

Example:

```text
Add Spanish translation for core keywords

- Add es_ES language file
- Update translation engine to support Spanish
- Add tests for Spanish translations

Fixes #123
```

### Package-Specific Guidelines

#### `libs/core/`

- Keep this package dependency-free when possible
- Maintain backward compatibility
- Document all public APIs

#### `libs/i18n/`

- Follow the language data format
- Include test cases for new languages
- Verify translations with native speakers

#### `libs/vs-code/`

- Follow VS Code extension guidelines
- Test on multiple VS Code versions
- Update extension documentation

## Release Process

### How Releases Work

Legesher uses **semantic-release** for automated versioning and releases. Here's how the process works:

### During Development (Your Part)

1. **Make your changes** in a feature branch
2. **Update CHANGELOGs** as you work (see CHANGELOG workflow below)
3. **Write conventional commits** (enforced by pre-commit hooks)
4. **Open a pull request** with your changes and CHANGELOG updates
5. **Get review approval** from maintainers
6. **Merge to main** when approved

### After Merge (Automated)

1. **semantic-release runs** automatically via GitHub Actions
2. **Reads conventional commits** to determine version bump (major/minor/patch)
3. **Creates git tag** with new version
4. **Publishes to PyPI** (if configured)
5. **Creates GitHub release** with release notes

### CHANGELOG Workflow

CHANGELOGs are part of your pull request, not created after merge.

#### Step 1: Update CHANGELOG during implementation

- Add entries to affected package CHANGELOGs (`libs/*/CHANGELOG.md`)
- Follow [Keep a Changelog](https://keepachangelog.com/) format
- Use conventional commits style with detailed descriptions
- Include PR and commit links

#### Step 2: CHANGELOG entry format

```markdown
### Added

- **Feature Name** ([#PR](link), [commit](link))
  - Detailed description of what was added
  - Key metrics (test coverage, performance, etc.)
  - Technical details that users should know
  - Examples of usage
```

#### Step 3: Pre-commit validation

- Pre-commit hooks validate CHANGELOG format automatically
- Catches markdown issues before commit
- Ensures conventional commit format

#### Step 4: Include in PR

- CHANGELOG updates are reviewed alongside code changes
- Maintainers verify accuracy and completeness
- Updates made based on review feedback
- Must be approved before merge

#### Step 5: Post-merge automation

- semantic-release handles version bumping
- Git tags created automatically
- PyPI publishing (when enabled)
- CHANGELOG already exists - no post-merge commit needed

### Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages. This format is
automatically validated by pre-commit hooks and enables automated version management.

**Format:**

```text
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat:` - New feature (triggers minor version bump)
- `fix:` - Bug fix (triggers patch version bump)
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `build:` - Build system changes
- `ci:` - CI/CD changes
- `chore:` - Maintenance tasks
- `revert:` - Revert a previous commit

**Scopes (optional but recommended):**

- `core` - Core translation engine
- `i18n` - Internationalization package
- `legesher` - Main package/CLI
- `language-server` - Language Server Protocol implementation
- `vs-code` - VS Code extension
- `pride` - Pride/community features
- `i18n-python-es` - Spanish language pack
- `i18n-python-ar` - Arabic language pack

**Examples:**

```bash
# Feature (minor version bump: 0.1.0 → 0.2.0)
feat(core): add Arabic language support with RTL

# Bug fix (patch version bump: 0.1.0 → 0.1.1)
fix(i18n): resolve pack inheritance circular reference

# Breaking change (major version bump: 0.1.0 → 1.0.0)
feat(core)!: redesign translation API

BREAKING CHANGE: TokenTranslator constructor now requires language pack instance
```

**Interactive Commit Helper:**

We provide Commitizen to guide you through creating valid commit messages interactively:

```bash
# Use Commitizen for interactive commit creation
uv run cz commit

# Or use regular git commit (validation still happens)
git commit -m "feat(core): add new feature"
```

The interactive helper will:

- Prompt you to select a commit type
- Ask for an optional scope
- Request a short description
- Ask if this is a breaking change
- Automatically format the commit message correctly

**Validation:**

- Pre-commit hooks enforce conventional commit format automatically
- Invalid commits will be rejected with helpful error messages
- You can bypass validation with `git commit --no-verify` (not recommended)
- CI/CD also validates commit messages on pull requests (when enabled)

### Version Numbers

- **Foundation Suite** (`core`, `i18n`, `legesher`): Synchronized versions
- **App Packages** (`vs-code`, `pride`): Independent versions
- **Language Packs** (`i18n-python-*`): Independent versions

See [README.md](README.md#versioning-strategy) for complete versioning strategy.

## Translation Contributions

We especially welcome contributions to language support:

1. **Adding a new language**
   - Create language file in `libs/i18n/`
   - Add translations for core keywords
   - Include language metadata
   - Add tests

2. **Improving existing translations**
   - Fix incorrect translations
   - Add missing translations
   - Improve natural language flow

## Questions?

- GitHub Discussions: [github.com/legesher/legesher/discussions](https://github.com/legesher/legesher/discussions)
- Email: <contribute@legesher.com>
- Documentation: [docs.legesher.io](https://docs.legesher.io)

## Recognition

Contributors are recognized in:

- Repository contributors list
- Release notes
- Documentation acknowledgments
- Special recognition for significant contributions

Thank you for helping make programming accessible in every language!
