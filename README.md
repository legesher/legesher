# legesher

monorepo for legesher

[![All Contributors](https://img.shields.io/github/all-contributors/legesher/legesher?color=ee8449&style=flat-square)](#contributors)
[![Tests](https://github.com/legesher/legesher/workflows/Tests/badge.svg)](https://github.com/legesher/legesher/actions/workflows/test.yml)
[![Lint](https://github.com/legesher/legesher/workflows/Lint/badge.svg)](https://github.com/legesher/legesher/actions/workflows/lint.yml)
[![License: Multi](https://img.shields.io/badge/license-Multi-blue.svg)](LICENSE)
[![Core: MIT](https://img.shields.io/badge/core-MIT-green.svg)](libs/core/LICENSE)
[![i18n: MIT](https://img.shields.io/badge/i18n-MIT-green.svg)](libs/i18n/LICENSE)
[![VS Code: MIT](https://img.shields.io/badge/vscode-MIT-green.svg)](libs/vs-code/LICENSE)
[![Legesher: Dual](https://img.shields.io/badge/legesher-MIT%20%7C%20Commercial-orange.svg)](libs/legesher/LICENSE)
[![Pride: Proprietary](https://img.shields.io/badge/pride-Proprietary-red.svg)](libs/pride/LICENSE)

> **Code in Your Native Language** - Programming tools that break down the English language barrier

## About Legesher

Legesher is a collection of developer tools and packages that enable developers to code in their native language instead
of English. From creation within an IDE to collaboration across projects and git histories, Legesher's tools remove
English as the prerequisite of coding.

## Licensing

This repository uses a **multi-license structure** to support both an open protocol and commercial features:

### 📖 Open Source (MIT License)

- **[legesher-core](libs/core/)** - Core translation engine
- **[legesher-i18n](libs/i18n/)** - Language data and dictionaries
- **[legesher-vs-code](libs/vs-code/)** - VS Code extension

These packages are freely available under the MIT License. Community contributions welcome!

### 🎯 Dual Licensed (MIT + Commercial)

- **[legesher](libs/legesher/)** - Main CLI and library
  - **Free Tier**: MIT License for local translation
  - **Premium Tier**: Commercial license for cloud sync, team features, and advanced tooling

### 🔒 Proprietary (Source Available)

- **[legesher-pride](libs/pride/)** - Community showcase and premium features
  - Source code visible for transparency and security review
  - Commercial license required for use

See the [LICENSE](LICENSE) file for complete details.

## Quick Start

```bash
# Install dependencies
uv install

# Verify installation
uv run python -c "import legesher_core; print('Setup successful')"

# Run tests
uv run pytest
```

See [CLAUDE.md](CLAUDE.md) for detailed development instructions.

## Versioning Strategy

Legesher uses a **hybrid versioning approach** with [Semantic Versioning](https://semver.org/):

### Foundation Suite (Synchronized)

These packages are released together with the same version:

- `legesher-core` - Core translation engine
- `legesher-i18n` - Language pack system
- `legesher` - Main CLI package

**Current version:** All at v0.0.1

### Application Packages (Independent)

These packages can release independently:

- `legesher-vs-code` v0.0.1 - VS Code extension
- `legesher-pride` v0.0.1 - Community platform

This allows rapid iteration on apps while maintaining foundation stability. Apps use semantic version constraints (e.g.,
`legesher>=0.0.1,<0.1.0`) to ensure compatibility.

### Language Packs (Independent)

Language packs are released independently, allowing each language community to iterate at their own pace:

- `legesher-i18n-python-es` v0.0.1 - Spanish translations for Python
- `legesher-i18n-python-ar` v0.0.1 - Arabic translations for Python

Each pack supports Python 3.10-3.13 with version-aware inheritance. Users install only the languages they need, and
translation communities can release updates independently.

**For release documentation**, see [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md).

## Contributing

We welcome contributions to our open source packages! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Which packages accept contributions
- Development setup
- Code of Conduct
- Contributor License Agreement

**Note**: Only open source packages (`core`, `i18n`, `vs-code`) accept external contributions at this time.

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
