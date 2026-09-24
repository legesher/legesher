# Legesher

**Code in Your Native Language** - Programming tools that break down the English language barrier

[![All Contributors](https://img.shields.io/github/all-contributors/legesher/legesher?color=ee8449&style=flat-square)](#contributors)
[![CI](https://github.com/legesher/legesher/actions/workflows/ci.yml/badge.svg)](https://github.com/legesher/legesher/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/legesher/legesher/branch/main/graph/badge.svg)](https://codecov.io/gh/legesher/legesher)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-coming%20soon-orange.svg)](https://pypi.org/)

Every package in this repository is Apache-2.0; see [Licensing](#licensing).

## About Legesher

**Legesher** (pronounced "le-GESH-er") enables developers to write code in their native language instead of English.
Imagine writing Python using Spanish keywords like `definir` instead of `def`, or Arabic keywords translated the
same way any other language is, with the VS Code translation panel applying right-to-left text direction and
alignment - all while collaborating seamlessly with developers who code in English.

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
- **Real-Time Translation:** Bidirectional translation preserves all formatting, comments, and structure.
- **IDE Integration:** A VS Code extension ships today. It talks to a standard Language Server Protocol server, so
  other LSP-capable editors can drive the same server, though we ship no integration for them yet.
- **Local-First:** Keyword translation happens locally - no cloud required, no data collection. Only the opt-in
  `--full` LLM translation calls a model, and it can point at one you host yourself.
- **Version-Aware:** Language packs adapt automatically to Python 3.10, 3.11, 3.12, 3.13, and 3.14.

### Current Status

**Pre-beta.** Every package here is pre-1.0. For the version a package is on right now, read its
`pyproject.toml` (or `package.json` for the VS Code extension); for what changed last, read
[CHANGELOG.md](CHANGELOG.md).

- **Languages:** 51 supported languages (all experimental, awaiting community validation):
  - Amharic, Arabic, Bengali, Bosnian, Burmese, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Finnish,
    French, Galician, German, Greek, Gujarati, Hebrew, Hindi, Hungarian, Indonesian, Irish, Italian, Japanese,
    Kannada, Korean, Latvian, Macedonian, Malay, Malayalam, Mongolian, Norwegian, Persian, Polish, Portuguese,
    Romanian, Russian, Scottish Gaelic, Serbian, Sinhala, Spanish, Sundanese, Swedish, Telugu, Thai, Turkish, Urdu,
    Uzbek, Vietnamese, Welsh
- **Target:** Python 3.10-3.14
- **Translation:** Two backends - a pure-stdlib token translator and a Tree-sitter AST translator behind the
  optional `treesitter` extra. Both produce identical output
- **Git:** Clean/smudge filters for multilingual workflows
- **IDE:** LSP server with hover, completion, diagnostics, and semantic tokens
- **VS Code:** Extension covering all 51 languages, installed from VSIX
- **Tests:** 200+ test files across the core, i18n, legesher, language-server, mcp, and runtime packages

## Licensing

**Everything in this repository is Apache License 2.0** — the CLI, the translation engine, the
language data, the language server, the MCP server, and the editor integrations:

- **[legesher](libs/legesher/)** - Main CLI and library
- **[legesher-core](libs/core/)** - Core translation engine
- **[legesher-i18n](libs/i18n/)** - Language data and dictionaries
- **[legesher-language-server](libs/language-server/)** - LSP implementation
- **[legesher-mcp](libs/mcp/)** - MCP server
- **[legesher-runtime](libs/runtime/)** - Localized tracebacks
- **[legesher-vscode](libs/vs-code/)** - VS Code extension

Use them, modify them, redistribute them — including commercially. Community contributions welcome!

Legesher rewrites your source code and installs a git filter, so being able to read exactly what
it does before you run it is the point, not a courtesy.

Legesher is open-core: the paid capabilities live in separate, closed-source codebases, where
access is gated by account and API key rather than by a license here. Nothing in this
repository requires an account or a network call to work.

See [LICENSING.md](LICENSING.md) for the per-package breakdown, or the [LICENSE](LICENSE) file for
the Apache 2.0 terms.

## Quick Start in 5 Minutes

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/legesher/legesher.git
cd legesher

# Install dependencies with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e libs/core -e libs/i18n -e libs/legesher
```

### Try Your First Translation

```bash
# Create a Python file in Spanish
echo 'definir saludar():
    imprimir("¡Hola, mundo!")

saludar()' > hola.py

# Translate to English. --from defaults to en, so name the source language
uv run legesher translate hola.py --from es --to en --output hello.py

# Check the result
cat hello.py
# Output:
# def saludar():
#     print("¡Hola, mundo!")
#
# saludar()
```

Keyword translation renames keywords and builtins only. Your own identifiers, such as `saludar`, stay exactly as
you wrote them. Use `--full` for LLM-powered translation of identifiers, comments, and strings.

### Set Up Git Integration (Optional)

```bash
# Initialize Legesher in your repo
uv run legesher git setup --language es

# Now all git operations auto-translate:
# - Checkout: English (repo) → Spanish (your working directory)
# - Commit: Spanish (your changes) → English (stored in repo)
```

### IDE Setup (VS Code)

The Legesher VS Code extension is available in pre-beta:

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

- **39 Python Keywords:** Complete coverage of Python 3.10-3.14 keywords, including `match`/`case`, `except*`,
  and `type`
- **73 Built-ins:** Built-in functions, types, and constants
- **70 Exception Classes:** Translated exception hierarchy
- **Two Translation Backends:** Token-based (pure stdlib, the default) and Tree-sitter (AST-based, behind the
  optional `treesitter` extra)
- **Round-Trip:** EN→ES→EN is byte-identical for the corpus the sweep covers. The known exceptions are listed as
  strict xfails in `libs/mcp/tests/test_roundtrip_sweep.py`, so a fix announces itself
- **Format Preservation:** Maintains all indentation, blank lines, comments, docstrings
- **Graceful Degradation:** Handles incomplete code and syntax errors

See [legesher-core](libs/core/README.md) for details.

### Language Pack System

- **51 Languages:** Every language listed under Current Status, all at experimental status
- **Version-Aware:** Automatically adapts to Python 3.10, 3.11, 3.12, 3.13, 3.14
- **Pack Inheritance:** Version files inherit from previous versions, minimizing duplication
- **Translation API:** Optional multi-provider translation (Anthropic, Cohere Aya, DeepL, Google, LibreTranslate,
  and any OpenAI-compatible endpoint)
- **Validation:** Pydantic-based schema validation with Unicode and script-policy checks
- **CLI Tools:** Validate packs, list the registry, export to JSON/CSV
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

### IDE Support

- **Language Server Protocol:** LSP implementation built on pygls 2.0
- **Hover Documentation:** Translated keyword info and docstrings
- **Auto-Completion:** Localized keyword and builtin completion
- **Diagnostics:** Syntax error reporting with translated messages for English, Spanish, and Arabic
- **Semantic Tokens:** Proper syntax highlighting for translated keywords
- **VS Code Extension:** Onboarding, translation panel, and opt-in telemetry

See [legesher-language-server](libs/language-server/README.md) for LSP documentation.

### CLI Tools

- **`legesher init`:** Initialize Legesher in a project
- **`legesher translate`:** Translate files or directories (keywords only, or `--full` for LLM-powered full translation)
- **`legesher run`:** Run translated Python files directly
- **`legesher git setup` / `legesher git status`:** Configure git integration and inspect it
- **`legesher-filter`:** Git filter script (`--clean`/`--smudge`), invoked automatically by git — not run directly
- **`legesher metadata`:** View translation history (`show`, `history`, `list`, `raw`, `validate`)
- **`legesher config`:** Read and write project or user configuration (`list`, `get`, `set`)
- **`legesher-i18n validate`:** Validate a language pack file
- **`legesher-i18n registry list`:** List the shipped packs with their term counts
- **`legesher-i18n export`:** Export packs to JSON or CSV (`json`, `csv`, `all`)

See [legesher](libs/legesher/README.md) for CLI documentation.

## Versioning Strategy

Legesher uses a **hybrid versioning approach** with [Semantic Versioning](https://semver.org/):

### Foundation Suite (Synchronized)

These packages are released together with the same version:

- `legesher-core` - Core translation engine
- `legesher-i18n` - Language pack infrastructure
- `legesher` - Main CLI package

They share one version number, set in each package's `pyproject.toml` and bumped together by
`release-foundation.yml`.

### Application Packages (Independent)

These packages each carry their own version number, independent of the foundation suite. Two of them
have a release workflow; the other two are versioned by hand and have no automated release yet:

- `legesher-vscode` - VS Code extension (`libs/vs-code/package.json`), released by `release-apps.yml`
- `legesher-mcp` - MCP server, tagged `mcp-v{version}` by `release-mcp.yml`
- `legesher-language-server` - LSP server. No release workflow; `publish-pypi.yml` does not accept it
  as a target
- `legesher-runtime` - Localized tracebacks. Same: no release workflow, not a `publish-pypi.yml` target

This lets the apps iterate without waiting on the foundation.

### Language Packs (Independent)

51 language packs are released independently, allowing each language community to iterate at their own pace:

- `legesher-i18n-python-{lang}` v0.0.x - Translations for Python
- Supported: am, ar, bn, bs, ca, cs, cy, da, de, el, en, es, fa, fi, fr, ga, gd, gl, gu, he, hi, hr, hu, id, it,
  ja, kn, ko, lv, mk, ml, mn, ms, my, nl, no, pl, pt, ro, ru, si, sr, su, sv, te, th, tr, ur, uz, vi, zh

Each pack supports Python 3.10-3.14 with version-aware inheritance. All packs currently have **experimental** status,
awaiting community validation before being marked as **accepted**.

**For release documentation**, see [.github/RELEASE_CHECKLIST.md](.github/RELEASE_CHECKLIST.md).

## Contributing

We welcome contributions! Every package in this repository is Apache-2.0 and accepts them. Please see
[CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Code of Conduct
- Contributor License Agreement

## Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
