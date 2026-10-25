# Development Guide

Get from clone to passing tests in under 5 minutes.

## Prerequisites

- **Python 3.10+** ([python.org/downloads](https://www.python.org/downloads/)) - development uses 3.13
- **UV** ([docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)) - Python package manager
- **Git** with commit signing configured (see [DCO Setup](#dco-setup) below)
- **Node.js 18+** and **pnpm** (only if working on documentation)

## Quick Start

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/legesher.git
cd legesher

# 2. Install all dependencies (monorepo workspace)
uv sync --all-extras

# 3. Set up pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg --hook-type pre-push

# 4. Run tests to verify everything works
uv run pytest libs/core/ libs/i18n/ libs/legesher/ libs/language-server/
```

If all tests pass, you're ready to contribute.

## Monorepo Layout

All packages live under `libs/`:

| Package             | Path                    | License                 | Description                                    |
| ------------------- | ----------------------- | ----------------------- | ---------------------------------------------- |
| **legesher-core**   | `libs/core/`            | Apache 2.0              | Translation engine, git filters, AST utilities |
| **legesher-i18n**   | `libs/i18n/`            | Apache 2.0              | 56 language packs, translation API, caching    |
| **legesher** (CLI)  | `libs/legesher/`        | Apache 2.0 / Commercial | CLI tools: init, translate, run, git, metadata |
| **language-server** | `libs/language-server/` | Apache 2.0              | LSP server (hover, completion, diagnostics)    |
| **vs-code**         | `libs/vs-code/`         | Apache 2.0              | VS Code extension                              |

> **Note:** Only Apache 2.0 and dual-licensed packages accept external contributions.
> See [LICENSING.md](LICENSING.md) for details.

## Working on a Package

```bash
# Run tests for a specific package
cd libs/core && uv run pytest
cd libs/i18n && uv run pytest -v
cd libs/language-server && uv run pytest

# Run tests with coverage
uv run pytest --cov=legesher_core libs/core/

# Run a specific test file
uv run pytest libs/core/tests/unit/test_token_translator.py -v
```

## Making Your First Change

### 1. Create a branch

```bash
git checkout -b feat/short-description
# Examples:
#   feat/add-finnish-builtins
#   fix/hover-provider-crash
#   docs/update-development-guide
```

### 2. Make your changes

Edit files, add tests alongside your implementation. Each package has a `tests/` directory.

### 3. Commit with DCO sign-off

All commits require a [Developer Certificate of Origin](https://developercertificate.org/) sign-off:

```bash
# Using commitizen (recommended — guides you through conventional commits)
uv run cz commit

# Or manually with sign-off
git commit -S -s -m "feat(core): add Finnish builtin translations"
```

**Conventional commit format:** `type(scope): description`

| Type       | When to use                                         |
| ---------- | --------------------------------------------------- |
| `feat`     | New feature                                         |
| `fix`      | Bug fix                                             |
| `docs`     | Documentation only                                  |
| `test`     | Adding or updating tests                            |
| `refactor` | Code change that doesn't fix a bug or add a feature |
| `ci`       | CI/CD changes                                       |
| `chore`    | Maintenance tasks                                   |

**Scopes:** `core`, `i18n`, `legesher`, `language-server`, `vs-code`, `docs`

### 4. Push and open a PR

```bash
git push -u origin feat/short-description
```

Then open a Pull Request on GitHub. The PR template will guide you through the checklist.

**CI will automatically check:**

- Tests pass across Python 3.10 and 3.13
- Ruff linting and formatting
- Bandit security scanning
- DCO sign-off present

**Local Git hooks will check:**

- Conventional commit format (via the `commit-msg` hook)

## DCO Setup

The DCO (Developer Certificate of Origin) requires every commit to include a `Signed-off-by` line.
You also need a GPG or SSH signing key for commit signature verification.

```bash
# Set your identity (must match your GitHub account)
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

# The -s flag adds Signed-off-by, -S signs the commit
git commit -S -s -m "your commit message"
```

If you forgot to sign off, you can amend:

```bash
git commit --amend -S -s --no-edit
```

See [GitHub's guide to signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification)
for GPG/SSH key setup.

## Documentation Development

The documentation site uses [Astro](https://astro.build/) with the
[Starlight](https://starlight.astro.build/) theme:

```bash
cd docs/
pnpm install    # First time only
pnpm dev        # Start dev server at http://localhost:4321
pnpm build      # Build for production
```

Content lives in `docs/src/content/docs/` as MDX files (Markdown + JSX).

## Troubleshooting

### `uv: command not found`

Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`

### Pre-commit hooks failing

```bash
# Run hooks manually to see detailed errors
uv run pre-commit run --all-files

# Update hook versions
uv run pre-commit autoupdate
```

### DCO check failing on PR

Your commits need a `Signed-off-by` trailer. Fix with:

```bash
# For the most recent commit
git commit --amend -s --no-edit

# For multiple commits
git rebase HEAD~N --signoff  # where N is the number of commits
```

### Tests failing on import

Make sure all packages are installed in development mode:

```bash
uv sync --all-extras
```

## Next Steps

- Browse issues labeled [`good first issue`](../../issues?q=label%3A%22good+first+issue%22) for beginner-friendly tasks
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide (code style, PR process, release workflow)
- Join [GitHub Discussions](https://github.com/legesher/legesher/discussions) for questions
