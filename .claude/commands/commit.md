<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- Git commit best practices
- Conventional Commits: https://www.conventionalcommits.org/
-->

# Create Commit: $ARGUMENTS

**Goal**: Create a well-structured git commit for: $ARGUMENTS

## Instructions

Follow best practices for git commits with clear, descriptive messages.

## Steps

### 1. Review Changes

```bash
# See what's changed
git status

# Review diff
git diff

# Check staged changes
git diff --staged
```

- Confirm: Changes match what you intended
- Verify: No debug code, console.log, or secrets included
- Check: No unintended changes to other files

### 2. Stage Changes Selectively

**Stage specific files**:

```bash
git add libs/{package}/{file}.py
git add tests/test_{feature}.py
```

**Stage parts of files** (if needed):

```bash
git add -p {file}  # Interactive staging
```

**Best practice**: Keep commits focused on ONE logical change.

### 3. Review Staged Changes

```bash
git diff --staged
```

- Ensure: Only related changes are staged
- Verify: Changes form a logical unit
- Check: No accidental staging of unwanted changes

### 4. Write Commit Message

Use **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type** (required):

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding or updating tests
- `docs`: Documentation only
- `style`: Code style/formatting (no logic change)
- `perf`: Performance improvement
- `chore`: Maintenance tasks (deps, config)
- `ci`: CI/CD changes

**Scope** (optional): Package or component affected

- `core`, `i18n`, `legesher`, `vs-code`, `pride`
- Or: `auth`, `api`, `cli`, etc.

**Subject** (required):

- Imperative mood: "add" not "added" or "adds"
- No period at the end
- Max 72 characters
- Lowercase (except proper nouns)

**Body** (optional but recommended):

- Explain WHAT changed and WHY
- Wrap at 72 characters
- Separate from subject with blank line

**Footer** (optional):

- Breaking changes: `BREAKING CHANGE: description`
- Issue references: `Closes #123` or `Fixes #456`
- Co-authored-by: For pair programming

### 5. Example Commit Messages

**Simple feature**:

```
feat(i18n): add version-aware language pack loader

Implement loader that automatically selects correct language pack
based on Python version. Supports inheritance across versions.
```

**Bug fix**:

```
fix(core): prevent infinite loop in AST transformer

Add max depth check to prevent stack overflow when processing
deeply nested AST nodes.

Fixes #234
```

**Breaking change**:

```
feat(api): change language pack API to async

BREAKING CHANGE: LanguagePackLoader.load() is now async.
All callers must use `await loader.load()`.

Migration guide: docs/migration/v0.2.md
```

**Test commit**:

```
test(i18n): add comprehensive version detector tests

Add tests for auto-detection priority:
- pyproject.toml
- .python-version file
- runtime fallback
```

**Multiple changes** (break into separate commits if possible):

```
feat(i18n): add Spanish and Arabic language packs

Add complete Python 3.10-3.13 keyword mappings for Spanish (es)
and Arabic (ar) with cultural comments and RTL support.

Includes:
- Base packs for Python 3.10
- Inheritance chain for 3.11, 3.12, 3.13
- Comprehensive test coverage
```

### 6. Create Commit

**With short message**:

```bash
git commit -m "feat(i18n): add version-aware language pack loader"
```

**With body** (use heredoc for multiline):

```bash
git commit -m "$(cat <<'EOF'
feat(i18n): add version-aware language pack loader

Implement loader that automatically selects correct language pack
based on Python version. Supports inheritance across versions.

Closes #123
EOF
)"
```

**Or open editor**:

```bash
git commit
# Editor opens, write message there
```

### 7. Verify Commit

```bash
# View most recent commit
git log -1

# See commit with diff
git show HEAD
```

- Check: Message is clear and follows conventions
- Verify: Changes match the description
- Ensure: No mistakes before pushing

### 8. Amend if Needed (Before Pushing)

**Fix commit message**:

```bash
git commit --amend -m "corrected message"
```

**Add forgotten changes**:

```bash
git add {forgotten-file}
git commit --amend --no-edit
```

**IMPORTANT**: Only amend commits that haven't been pushed yet!

## Pre-Commit Checklist

Before committing, verify:

- [ ] Code follows project conventions
- [ ] Tests pass: `uv run pytest`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Formatting is correct: `uv run black --check .`
- [ ] Type checking passes: `uv run mypy .`
- [ ] No debug code or console.log left behind
- [ ] No secrets or sensitive data in commit
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated for user-facing changes

## Commit Message Anti-Patterns

**❌ Avoid**:

```
# Too vague
git commit -m "fix stuff"
git commit -m "update code"
git commit -m "changes"

# Not descriptive
git commit -m "bug fix"
git commit -m "wip"

# Past tense
git commit -m "added feature"
git commit -m "fixed bug"
```

**✅ Good**:

```
git commit -m "feat(core): add token-based AST transformer"
git commit -m "fix(i18n): prevent path traversal in pack loader"
git commit -m "test(api): add edge case tests for null inputs"
```

## Git History Best Practices

**Atomic Commits**: One logical change per commit

- Easier to review
- Easier to revert if needed
- Easier to understand history

**Clear Messages**: Future you (and contributors) will thank you

- Explains WHY, not just WHAT
- Provides context for decisions
- References related issues/PRs

**Clean History**: Before creating PR

- Squash "fix typo" commits
- Squash "wip" commits
- Keep meaningful commits separate
- Use interactive rebase: `git rebase -i main`

## For Solo Founders

Your commit messages are:

- **Documentation**: They explain your thinking
- **Debugging tool**: Track when bugs were introduced
- **Onboarding material**: Help future contributors understand
- **Project diary**: Record of your journey

Write them as if you're explaining to a collaborator (or future you).

## For Open Source Projects

Good commits:

- **Attract contributors**: Show professionalism and organization
- **Enable reviews**: Reviewers can understand changes quickly
- **Build trust**: Clear history shows care and attention
- **Teach practices**: New contributors learn from your example

## Deliverable

Create a commit with:

- Clear, descriptive message following Conventional Commits
- Focused, atomic changes
- Passes all quality checks
- References relevant issues

Remember: Commits are permanent. Make them count.