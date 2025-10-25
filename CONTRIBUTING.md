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
uv install

# Run tests
uv run pytest

# Work on a specific package
cd libs/core
uv run pytest
```

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

Violations may result in temporary or permanent ban from the project. Report issues to: conduct@legesher.com

## Development Guidelines

### Testing

- Write tests for all new functionality
- Ensure existing tests pass before submitting PR
- Aim for high test coverage on core functionality

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
- Email: contribute@legesher.com
- Documentation: [docs.legesher.io](https://docs.legesher.io)

## Recognition

Contributors are recognized in:
- Repository contributors list
- Release notes
- Documentation acknowledgments
- Special recognition for significant contributions

Thank you for helping make programming accessible in every language!
