# Legesher

**Code in Your Native Language** - Programming tools that break down the English language barrier

[![All Contributors](https://img.shields.io/github/all-contributors/legesher/legesher?color=ee8449&style=flat-square)](#contributors)
[![Tests](https://github.com/legesher/legesher/workflows/Tests/badge.svg)](https://github.com/legesher/legesher/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)](https://github.com/legesher/legesher/actions)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
[![License: Multi](https://img.shields.io/badge/license-Multi-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-orange.svg)](https://pypi.org/)

**Package Licenses:**

[![Core: MIT](https://img.shields.io/badge/core-MIT-green.svg)](libs/core/LICENSE)
[![i18n: MIT](https://img.shields.io/badge/i18n-MIT-green.svg)](libs/i18n/LICENSE)
[![VS Code: MIT](https://img.shields.io/badge/vscode-MIT-green.svg)](libs/vs-code/LICENSE)
[![Legesher: Dual](https://img.shields.io/badge/legesher-MIT%20%7C%20Commercial-orange.svg)](libs/legesher/LICENSE)
[![Home: Proprietary](https://img.shields.io/badge/home-Proprietary-red.svg)](libs/home/LICENSE)

## About Legesher

**Legesher** (pronounced "le-GESH-er") enables developers to write code in their native language instead of English.
Imagine writing Python using Spanish keywords like `definir` instead of `def`, or Arabic keywords with full
right-to-left support - all while collaborating seamlessly with developers who code in English.

### Why Legesher?

**The Problem:** Programming languages require English keywords, creating a barrier for the 82% of the world's
population who don't speak English as their first language. Developers must learn English first before they can code.

**The Solution:** Legesher translates your code in real-time:

- Write code in Spanish, Arabic, or your preferred language
- Store files in English in git (no merge conflicts!)
- Collaborate with developers using any language
- Full IDE support with IntelliSense, hover docs, and error messages in your language

### What Makes Legesher Different?

- **Language-Agnostic Git:** Store canonical English in your repository, but each developer sees their preferred
  language. No merge conflicts from keyword differences.
- **Real-Time Translation:** Lossless bidirectional translation preserves all formatting, comments, and structure.
- **IDE Integration:** Language Server Protocol support means it works with VS Code, PyCharm, Zed, and more.
- **Local-First:** All translation happens locally by default - no cloud required, no data collection.
- **Version-Aware:** Language packs adapt automatically to Python 3.10, 3.11, 3.12, and 3.13.

### Current Status

**v0.1.0 - First Public Release** (2025-11-07)

- **Languages:** Spanish (es), Arabic (ar) with RTL support
- **Target:** Python 3.10-3.13
- **Translation:** Token-based transformation (91% test coverage)
- **Git:** Clean/smudge filters for multilingual workflows
- **IDE:** Language Server Protocol (Phase 1 complete)
- **Tests:** 255 tests in core, 187 in i18n, 66 in CLI

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

- **[legesher-home](libs/home/)** - Digital home and community platform
  - Source code visible for transparency and security review
  - Commercial license required for use

See the [LICENSE](LICENSE) file for complete details.

## Quick Start in 5 Minutes

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/madiedgar/legesher.git
cd legesher

# Install dependencies with uv (recommended)
uv install

# Or with pip
pip install -e libs/core -e libs/i18n -e libs/legesher
```

### Try Your First Translation

```bash
# Create a Python file in Spanish
echo 'definir saludar():
    imprimir("¡Hola, mundo!")

saludar()' > hola.py

# Translate to English
uv run legesher translate hola.py --to en --output hello.py

# Check the result
cat hello.py
# Output:
# def saludar():
#     print("¡Hola, mundo!")
#
# saludar()
```

### Set Up Git Integration (Optional)

```bash
# Initialize Legesher in your repo
uv run legesher git setup --language es

# Now all git operations auto-translate:
# - Checkout: English (repo) → Spanish (your working directory)
# - Commit: Spanish (your changes) → English (stored in repo)
```

### IDE Setup (Coming Soon)

VS Code extension is in active development. Follow progress in [CORE-365](https://linear.app/legesher/issue/CORE-365).

### Next Steps

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[CHANGELOG.md](CHANGELOG.md)** - What's new in v0.1.0
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for contributors

## Features

### Core Translation Engine

- **35 Python Keywords:** Complete coverage of Python 3.13 keywords
- **34 Built-in Functions:** Translated standard library functions
- **Lossless Round-Trip:** EN→ES→EN produces byte-identical output
- **Format Preservation:** Maintains all indentation, blank lines, comments, docstrings
- **Performance:** <2ms per file average, 100% round-trip fidelity
- **Graceful Degradation:** Handles incomplete code and syntax errors

See [legesher-core](libs/core/README.md) for details.

### Language Pack System

- **Version-Aware:** Automatically adapts to Python 3.10, 3.11, 3.12, 3.13
- **Pack Inheritance:** Child packs inherit from parents, defining only what's new
- **Translation API:** Optional multi-provider translation (DeepL, Google, LibreTranslate)
- **Validation:** Pydantic-based schema validation with security checks
- **CLI Tools:** Validate packs, show versions, generate compatibility matrices
- **Caching:** Fast repeated loads with intelligent caching

See [legesher-i18n](libs/i18n/README.md) for details.

### Git Integration

- **Canonical English Storage:** Repository stores English for universal collaboration
- **Automatic Translation:** On checkout, code translates to developer's preferred language
- **Zero Conflicts:** No merge conflicts from keyword differences
- **Multilingual Teams:** Spanish developer → English repo → Arabic developer workflow
- **Metadata Tracking:** Privacy-first translation history with audit trail
- **Atomic Operations:** Crash-safe file operations

See [legesher-core](libs/core/README.md) for git filter documentation.

### IDE Support (In Development)

- **Language Server Protocol:** Editor-agnostic design (works with any LSP-compatible editor)
- **Hover Documentation:** Translated docstrings and keyword info in <5ms
- **IntelliSense:** Localized auto-completion in <10ms
- **Diagnostics:** Error messages in native language
- **Pylance Integration:** Advanced type checking (Phase 1 complete)

See [legesher-language-server](libs/language-server/CHANGELOG.md) for LSP progress.

### CLI Tools

- **`legesher translate`:** Translate files or directories
- **`legesher git setup`:** Initialize git integration
- **`legesher git clean/smudge`:** Git filter commands
- **`legesher config`:** Manage configuration
- **`legesher metadata`:** View translation history
- **`legesher-i18n validate`:** Validate language packs
- **`legesher-i18n show`:** Display pack versions

See [legesher](libs/legesher/CHANGELOG.md) for CLI documentation.

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
- `legesher-home` v0.0.1 - Digital home and community platform

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
