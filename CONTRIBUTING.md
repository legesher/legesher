# Contributing to Legesher

Thank you for your interest in contributing to Legesher! This document explains how to contribute to this
multi-license repository. It pairs with two companion documents:

- [Community Guidelines](COMMUNITY_GUIDELINES.md): how we build on a shared terminology map, and how
  disagreement works here
- [AI-Assisted Contributions](AI_CONTRIBUTIONS.md): what is welcome, what we ask you to declare, and
  where the human line sits

## Ways to Contribute

Legesher exists so people can write and read code in their heart language. Getting there takes more
than engine code: it takes speakers, teachers, writers, and people willing to report what actually
happens when they try it. Every path below is a real contribution, and most of them require no
Python expertise.

| If you are | Start here | Look for |
| --- | --- | --- |
| A speaker of one of our 51 pack languages | Offer a better word. Every translation you propose is collected as an option in the shared map; it is never a conflict with what ships today | `contrib:localization` |
| A linguist, teacher, or careful reader | Native review: help decide what your language ships with. Start with the [reviewer guide](libs/i18n/REVIEWING.md) | `contrib:localization` |
| A developer | Engine, toolchain, and editor issues scoped for newcomers | `good first issue`, `contrib:code` |
| A bilingual writer | Docs localization: translate a guide so readers see the same words in the docs and in their editor | `contrib:docs` |
| Someone with lived language context | Context Calls: tell us how your language is really written, texted, and code-switched. The observation is the contribution | `contrib:community` |
| Curious about AI in your language | Prompt an assistant in your language through Legesher and report what happens | `ai:native-prompting` |

### What the labels mean

- `contrib:code`: engine, toolchain, language server, and editor work
- `contrib:docs`: documentation, including localizing it
- `contrib:localization`: language packs, translation options, native review
- `contrib:community`: discussions, Context Calls, showcases, helping other contributors
- `ai:restricted` / `ai:native-prompting`: AI-assistance policy labels, explained in
  [AI-Assisted Contributions](AI_CONTRIBUTIONS.md)
- `good first issue`: scoped and described so a newcomer can finish it

Contributor-facing issues live in this repository's issue tracker and Discussions. Language pack
work flows through the options model described in [Community Guidelines](COMMUNITY_GUIDELINES.md).

## New to Open Source?

Welcome! We're excited to have you. Open source contribution might seem intimidating at first, but we're here to help.

### What is Open Source?

Open source means the code is publicly visible and accepts contributions from anyone. You can:

- **Report bugs** you find while using the project
- **Suggest features** you'd like to see
- **Fix typos** in documentation
- **Translate** content to your native language — with one exception, below
- **Write code** to add features or fix bugs

> **Legal and policy pages are English-only.** Please don't translate the privacy policy,
> terms of service, licences, or security disclosures. A translated policy is a second
> policy: it can drift from the English, and someone may rely on the version that drifted.
> This is the one place where our own argument for reading in your own language loses to
> the need for a single authoritative text. Everything else is fair game.

### Your First Contribution

Not sure where to start? Here are beginner-friendly ways to contribute:

1. **Fix Documentation:** Found a typo? Confusing explanation? Documentation PRs are always welcome!
2. **Offer a Better Word:** Speak one of our pack languages? Propose translation options; every
   option you offer joins the shared map.
3. **Report Bugs:** Found something broken? Open an issue with reproduction steps.
4. **Answer Questions:** Help other users in GitHub Discussions.
5. **Good First Issues:** Look for issues tagged
   [`good first issue`](../../issues?q=label%3A%22good+first+issue%22) — designed for newcomers.

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

**Every package in this repository is Apache License 2.0**, and contributions to all of them are
welcome — there is no package where contributions are restricted, and no contributor licence
agreement to sign. Your contributions are licensed under the same terms as the code you are
contributing to:

- **`libs/legesher/`** - Main package with CLI and primary API
- **`libs/core/`** - Core translation engine and shared utilities
- **`libs/i18n/`** - Internationalization and language data
- **`libs/language-server/`** - LSP implementation
- **`libs/mcp/`** - MCP server
- **`libs/vs-code/`** - VS Code editor integration

Legesher's paid capabilities live in a separate, closed-source hosted service; nothing in this
repository is gated behind them. See [LICENSING.md](LICENSING.md) for the full breakdown.

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

> **Quick start?** See [DEVELOPMENT.md](DEVELOPMENT.md) for a streamlined setup guide.

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/legesher-next.git
cd legesher-next

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

### 4. AI-Assisted Work

AI-assisted contributions are welcome by default; we ask for one declaration line in your pull
request, and you own the correctness of what you submit. Two labels change the default:
`ai:restricted` marks issues reserved for learning by hand, and `ai:native-prompting` marks issues
where prompting an AI in your own language is the point. The full policy, including how
machine-suggested translations are recorded with their provenance, is in
[AI-Assisted Contributions](AI_CONTRIBUTIONS.md).

## Contributor License Agreement

### For Open Source Packages (Apache-2.0 Licensed)

By contributing to Apache-2.0-licensed packages (`core`, `i18n`, `vs-code`), you agree that:

1. Your contributions will be licensed under the Apache License 2.0
2. You have the right to license your contribution under these terms
3. You understand your contributions become part of the public open source project

The same applies to every package here, including the `legesher` CLI — there is no package whose
contributions get relicensed under different terms, and you will be credited as a contributor.

### Copyright Assignment

We do NOT require copyright assignment. You retain copyright to your contributions, but you grant Legesher a perpetual
license to use your contributions under the project's license terms.

## Developer Certificate of Origin (DCO)

The DCO sign-off supplements (does not replace) the contribution agreement above. The agreement governs the license
terms for your contribution; the DCO certifies your right to submit it.

All contributions to Legesher must be signed off under the
[Developer Certificate of Origin (DCO) v1.1](https://developercertificate.org/). By signing off, you certify that you
have the right to submit your contribution under the project's license terms.

### What is the DCO?

The DCO is a lightweight, per-commit certification used by the Linux kernel, CNCF projects, Node.js, and many other
major open source projects. It is not a CLA — you do not sign a separate document. Instead, you add a `Signed-off-by`
trailer to each commit.

### DCO 1.1 Full Text

```text
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

### How to Sign Off Your Commits

Add a `Signed-off-by` trailer to every commit. The easiest way is the `-s` flag:

```bash
git commit -s -m "feat(core): add new feature"
```

This appends a line like:

```text
Signed-off-by: Your Name <your.email@example.com>
```

The email must match your Git author email. Check with:

```bash
git config user.email
```

### Fixing Forgotten Sign-offs

**Last commit only:**

```bash
git commit --amend -s --no-edit
git push --force-with-lease
```

**Multiple commits:**

```bash
git rebase --signoff HEAD~N
git push --force-with-lease
```

Replace `N` with the number of commits to fix.

**Remediation commit (no history rewrite):**

If you prefer not to rewrite history, you can create a remediation commit. Our DCO bot (CNCF/DCO2) supports both
individual and third-party remediation commits.

Individual remediation (you fix your own commits):

```text
DCO remediation commit for Your Name <your.email@example.com>

I, Your Name <your.email@example.com>, hereby add my Signed-off-by to this commit: <COMMIT_SHA>

Signed-off-by: Your Name <your.email@example.com>
```

Third-party remediation (a maintainer fixes on your behalf):

```text
Third-party DCO remediation commit for Contributor <contributor@example.com>

On behalf of Contributor <contributor@example.com>, I, Maintainer <maintainer@example.com>, hereby add my Signed-off-by to this commit: <COMMIT_SHA>

Signed-off-by: Maintainer <maintainer@example.com>
```

See the [DCO2 documentation](https://github.com/cncf/dco2) for full details on remediation commit formats.

### Automated Enforcement

All pull requests are checked by the [CNCF DCO2](https://github.com/cncf/dco2) GitHub App. PRs with unsigned commits
will not pass the DCO status check. Bot accounts (Dependabot, GitHub Actions, etc.) are automatically exempted.

## Code of Conduct and Community Guidelines

The full [Code of Conduct](CODE_OF_CONDUCT.md) governs every community space, including its
language-and-accessibility provisions. The [Community Guidelines](COMMUNITY_GUIDELINES.md) cover
the working agreements specific to this project: the options model's social contract, content
standards for language contributions, and the moderation path. The short version:

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

- **Python versions**: 3.10 and 3.13 (3.10 on Ubuntu; 3.13 on Ubuntu, macOS, Windows)
- **Operating systems**: Ubuntu, macOS, Windows
- **Coverage threshold**: 30% (will increase to 90% as codebase matures)

Tests must pass on all platforms before merging to `main`.

#### CI Dependency Caching

CI jobs use `astral-sh/setup-uv@v7` with `enable-cache: true`, which caches the
`uv` package cache between runs. The cache key is derived automatically from
`uv.lock`, so cache invalidation happens whenever dependencies change. You
don't need to configure anything when adding new jobs — just use `setup-uv`
with `enable-cache: true`.

Cache behavior:

- Cache hits save 1-3 minutes per job on dependency install
- Cache invalidates automatically on `uv.lock` changes
- GitHub Actions retains caches for 7 days of inactivity
- Cache limit is 10 GB per repository

#### Coverage Reporting (Codecov)

The test job in `ci.yml` runs `pytest` with `--cov` flags and generates
per-package XML coverage reports. The Ubuntu + Python 3.13 matrix cell
uploads these to Codecov via `codecov/codecov-action@v5` on every PR and
push to main.

View coverage:

- **PR comments**: Codecov bot posts a comment on every PR showing coverage
  delta and any files with changed coverage
- **Dashboard**: <https://codecov.io/gh/madiedgar/legesher> (update to
  `Legesher/legesher` when the repo transitions public)
- **Badge**: See the coverage badge at the top of the main README

Coverage targets are defined in `codecov.yml` and are **informational only** —
they won't block PRs. The target is 90% with a 2% tolerance.

If you see "Codecov token not found" in CI logs, make sure the `CODECOV_TOKEN`
secret is configured in repository Settings → Secrets → Actions.

#### Security Scanning (Bandit)

Every PR runs `bandit` over `libs/` via `.github/workflows/security.yml` to
catch common Python security issues (SQL injection, weak crypto, unsafe
deserialization, etc.).

**Running bandit locally:**

```bash
# Full scan (all severities)
uv run --with "bandit[toml]" bandit -r libs/ -c pyproject.toml

# High severity only (what CI enforces)
uv run --with "bandit[toml]" bandit -r libs/ -c pyproject.toml --severity-level high
```

CI enforcement: **bandit fails the build on High-severity findings only**.
Medium and Low findings are reported in CI logs but do not block the build.
This reflects a gradual rollout — see CORE-1067 for the triage effort to
tighten enforcement to Medium.

**Handling false positives:** If bandit flags code that is safe by design,
add an inline `# nosec` comment with a rule code and justification:

```python
# nosec B603 - subprocess called with static list args, no shell injection risk
result = subprocess.run(["git", "log"], check=True)
```

Never use a bare `# nosec` — always include the rule code and reason.

#### Modern Python Syntax (Ruff UP rules)

The ruff linter is configured with `select = ["E4", "E7", "E9", "F", "UP"]`,
which includes pyupgrade (`UP`) rules. These enforce modern Python 3.10+
idioms:

- `X | None` over `Optional[X]`
- `list[str]` over `List[str]`
- `dict[str, int]` over `Dict[str, int]`

Run locally:

```bash
uv run ruff check libs/
uv run ruff check --fix libs/   # Auto-fix most issues
```

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

A format-and-changelog bot for contributor PRs is planned; when it lands, formatting fixups and
changelog scaffolding will happen for you, so your attention stays on the contribution rather than
the bookkeeping. Until then, the steps below are the floor, and reviewers are happy to help you
through them.

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
- **App Packages** (`vs-code`): Independent versions
- **Language Packs** (`i18n-python-*`): Independent versions

See [README.md](README.md#versioning-strategy) for complete versioning strategy.

## Translation Contributions

Language work is the heart of this project, and it follows one principle: **we collect options, we
don't overwrite winners.** The translations database holds every translation offered for every
term, with provenance. A language pack is the current best pick exported from those options, and
all 51 packs are available today with community validation in progress.

What that means for you:

1. **Offering a better word** is always in season. Propose your term through
   [Propose a Translation Option](https://github.com/legesher/legesher/issues/new?template=propose_translation.yml),
   with a note on whether it is established usage, a coinage, or a loanword your community genuinely
   uses. You are adding to the map, not fighting the current pick.
2. **Improving existing translations** happens the same way: propose the better option and say why.
   When native reviewers endorse it, the pick moves.
3. **Native review** is how packs climb the ladder from experimental toward official. The
   [reviewer guide](libs/i18n/REVIEWING.md) covers what reviewing involves, how endorsements are
   weighted, and what makes a pack `reviewed` and then `official`. Sign up through
   [Native Reviewer Signup](https://github.com/legesher/legesher/issues/new?template=reviewer_signup.yml). The
   [Community Guidelines](COMMUNITY_GUIDELINES.md) carry the working agreements that sit underneath
   it.
4. **Before you submit**, read
   [Your contributions and your data](CONTRIBUTOR_PRIVACY.md). It is short, and it covers what
   happens to your word, how you are identified (you are not — credit is opt-in), what we never
   publish, and how to withdraw.
5. **Requesting a new language** starts with an issue. Packs are generated from the shared
   database, so the path to a new language runs through collecting its options, not hand-writing
   pack files.

## Questions?

- GitHub Discussions: [github.com/legesher/legesher/discussions](https://github.com/legesher/legesher/discussions)
- Email: <contribute@legesher.com>
- Documentation: [docs.legesher.io](https://docs.legesher.io)

## Recognition

Recognition follows your credit preference: anonymous (the default), your handle, or a display
name — see [Your contributions and your data](CONTRIBUTOR_PRIVACY.md). Where you have asked to be
credited, contributors are recognized in:

- Repository contributors list
- Release notes
- Documentation acknowledgments
- Special recognition for significant contributions

Thank you for helping make programming accessible in every language!
