# Legesher

**Code in Your Native Language** - Programming tools that break down the English language barrier

[![All Contributors](https://img.shields.io/github/all-contributors/legesher/legesher?color=ee8449&style=flat-square)](#contributors)
[![CI](https://github.com/madiedgar/legesher/actions/workflows/ci.yml/badge.svg)](https://github.com/madiedgar/legesher/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/madiedgar/legesher/branch/main/graph/badge.svg)](https://codecov.io/gh/madiedgar/legesher)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/downloads/)
[![License: Multi](https://img.shields.io/badge/license-Multi-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-orange.svg)](https://pypi.org/)

**Package Licenses:**

[![Core: Apache 2.0](https://img.shields.io/badge/core-Apache%202.0-green.svg)](libs/core/LICENSE)
[![i18n: Apache 2.0](https://img.shields.io/badge/i18n-Apache%202.0-green.svg)](libs/i18n/LICENSE)
[![VS Code: Apache 2.0](https://img.shields.io/badge/vscode-Apache%202.0-green.svg)](libs/vs-code/LICENSE)
[![Legesher: Apache 2.0](https://img.shields.io/badge/legesher-Apache%202.0-green.svg)](libs/legesher/LICENSE)

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
- **Version-Aware:** Language packs adapt automatically to Python 3.10, 3.11, 3.12, 3.13, and 3.14.

### Current Status

**v0.4.x - Pre-Beta Release** (2026-02)

- **Languages:** 51 supported languages (all experimental, awaiting community validation):
  - Amharic, Arabic, Bengali, Bosnian, Burmese, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Finnish,
    French, Galician, German, Greek, Gujarati, Hebrew, Hindi, Hungarian, Indonesian, Irish, Italian, Japanese,
    Kannada, Korean, Latvian, Macedonian, Malay, Malayalam, Mongolian, Norwegian, Persian, Polish, Portuguese,
    Romanian, Russian, Scottish Gaelic, Serbian, Sinhala, Spanish, Sundanese, Swedish, Telugu, Thai, Turkish, Urdu,
    Uzbek, Vietnamese, Welsh
- **Target:** Python 3.10-3.14
- **Translation:** Two backends - Token-based (~140μs) and Tree-sitter AST-based (~160μs)
- **Git:** Clean/smudge filters for multilingual workflows
- **IDE:** Full LSP server with hover, completion, diagnostics, semantic tokens
- **VS Code:** Production-ready extension (v0.1.2) with 51 language support
- **Tests:** 100+ test files across core, i18n, legesher, and language-server packages

## Licensing

**Everything in this repository is Apache License 2.0** — the CLI, the translation engine, the
language data, the language server, the MCP server, and the editor integrations:

- **[legesher](libs/legesher/)** - Main CLI and library
- **[legesher-core](libs/core/)** - Core translation engine
- **[legesher-i18n](libs/i18n/)** - Language data and dictionaries
- **[legesher-language-server](libs/language-server/)** - LSP implementation
- **[legesher-mcp](libs/mcp/)** - MCP server
- **[legesher-vs-code](libs/vs-code/)** - VS Code extension

Use them, modify them, redistribute them — including commercially. Community contributions welcome!

Legesher rewrites your source code and installs a git filter, so being able to read exactly what
it does before you run it is the point, not a courtesy.

Legesher is open-core: the paid capabilities are the **hosted service** (cloud translation API and
what is built on it), a separate closed-source codebase where access is gated by account and API
key rather than by a license here. Nothing in this repository requires an account or a network
call to work.

See [LICENSING.md](LICENSING.md) for the per-package breakdown, or the [LICENSE](LICENSE) file for
the Apache 2.0 terms.

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

### IDE Setup (VS Code)

The Legesher VS Code extension is available and production-ready (pre-beta):

1. **Install from VSIX** (current method):
   - Download the latest `.vsix` from releases
   - In VS Code: Extensions → `...` menu → "Install from VSIX..."

2. **Features included:**
   - Language selector with 51 languages
   - Translation panel (side-by-side view)
   - Syntax highlighting for translated code
   - Onboarding flow with language selection

See [libs/vs-code/README.md](libs/vs-code/README.md) for full documentation.

### Next Steps

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[CHANGELOG.md](CHANGELOG.md)** - What's new
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for contributors

## Features

### Core Translation Engine

- **37 Python Keywords:** Complete coverage of Python 3.10-3.14 keywords
- **72 Built-in Functions:** Translated standard library functions
- **66 Exception Classes:** Translated exception hierarchy
- **Two Translation Backends:** Token-based (simple, stable) and Tree-sitter (AST-based, production-ready)
- **Lossless Round-Trip:** EN→ES→EN produces byte-identical output
- **Format Preservation:** Maintains all indentation, blank lines, comments, docstrings
- **Performance:** ~140-160μs per file, 100% round-trip fidelity
- **Graceful Degradation:** Handles incomplete code and syntax errors

See [legesher-core](libs/core/README.md) for details.

### Language Pack System

- **51 Languages:** All major world languages supported (experimental status)
- **Version-Aware:** Automatically adapts to Python 3.10, 3.11, 3.12, 3.13, 3.14
- **Pack Inheritance:** Version files inherit from previous versions, minimizing duplication
- **Translation API:** Optional multi-provider translation (Anthropic, DeepL, Google, LibreTranslate)
- **Validation:** Pydantic-based schema validation with security checks
- **CLI Tools:** Validate packs, show versions, export to JSON/CSV
- **Caching:** Thread-safe LRU caching for fast pack loading

See [legesher-i18n](libs/i18n/README.md) for details.

### Git Integration

- **Canonical English Storage:** Repository stores English for universal collaboration
- **Automatic Translation:** On checkout, code translates to developer's preferred language
- **Zero Conflicts:** No merge conflicts from keyword differences
- **Multilingual Teams:** Spanish developer → English repo → Arabic developer workflow
- **Metadata Tracking:** Privacy-first translation history with audit trail
- **Atomic Operations:** Crash-safe file operations

See [legesher-core](libs/core/README.md) for git filter documentation.

### IDE Support (Production-Ready)

- **Language Server Protocol:** Full LSP implementation with pygls 2.0
- **Hover Documentation:** Translated keyword info and docstrings
- **Auto-Completion:** Localized keyword and builtin completion
- **Diagnostics:** Real-time syntax error reporting
- **Semantic Tokens:** Proper syntax highlighting for translated keywords
- **VS Code Extension:** Production-ready with onboarding, translation panel, telemetry

See [legesher-language-server](libs/language-server/README.md) for LSP documentation.

### CLI Tools

- **`legesher init`:** Initialize Legesher in a project
- **`legesher translate`:** Translate files or directories (keywords only, or `--full` for LLM-powered full translation)
- **`legesher run`:** Run translated Python files directly
- **`legesher git setup`:** Initialize git integration
- **`legesher-filter`:** Git filter script (`--clean`/`--smudge`), invoked automatically by git — not run directly
- **`legesher metadata`:** View translation history
- **`legesher-i18n validate`:** Validate language packs
- **`legesher-i18n show`:** Display pack versions
- **`legesher-i18n export`:** Export packs to JSON/CSV

See [legesher](libs/legesher/README.md) for CLI documentation.

## Versioning Strategy

Legesher uses a **hybrid versioning approach** with [Semantic Versioning](https://semver.org/):

### Foundation Suite (Synchronized)

These packages are released together with the same version:

- `legesher-core` - Core translation engine
- `legesher-i18n` - Language pack infrastructure
- `legesher` - Main CLI package

**Current version:** All at v0.4.0

### Application Packages (Independent)

These packages can release independently:

- `legesher-vs-code` v0.1.2 - VS Code extension (production-ready)
- `legesher-language-server` v0.1.0 - LSP server

This allows rapid iteration on apps while maintaining foundation stability.

### Language Packs (Independent)

51 language packs are released independently, allowing each language community to iterate at their own pace:

- `legesher-i18n-python-{lang}` v0.0.1-0.0.3 - Translations for Python
- Supported: am, ar, bn, bs, ca, cs, cy, da, de, el, en, es, fa, fi, fr, ga, gd, gl, gu, he, hi, hr, hu, id, it,
  ja, kn, ko, lv, mk, ml, mn, ms, my, nl, no, pl, pt, ro, ru, si, sr, su, sv, te, th, tr, ur, uz, vi, zh

Each pack supports Python 3.10-3.14 with version-aware inheritance. All packs currently have **experimental** status,
awaiting community validation before being marked as **accepted**.

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
