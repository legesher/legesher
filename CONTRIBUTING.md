# Contributing to Legesher

Thank you for your interest in contributing to Legesher! This document explains how to contribute to this multi-license repository.

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

The free tier features use the MIT License. Premium features require a commercial license. Contributions to free tier features are welcome.

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

We use pre-commit hooks to automatically check and format code before committing. This ensures code quality and prevents CI/CD failures.

**Setup:**

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install
```

**What gets checked automatically:**

- ✅ Code formatting with Black
- ✅ Linting with Ruff (auto-fixes when possible)
- ✅ Trailing whitespace and file endings
- ✅ YAML/TOML/JSON syntax validation
- ✅ Large file detection
- ✅ Merge conflict markers
- ✅ Private key detection

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

We do NOT require copyright assignment. You retain copyright to your contributions, but you grant Legesher a perpetual license to use your contributions under the project's license terms.

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

All code contributions must include tests. We use pytest for testing with a 30% minimum coverage requirement (gradually increasing to 90% as the codebase matures).

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

```
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
