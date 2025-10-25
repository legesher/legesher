<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- GitHub CLI (gh) documentation
- Pull request best practices
-->

# Create Pull Request: $ARGUMENTS

**Goal**: Create a comprehensive, reviewable pull request for: $ARGUMENTS

## Instructions

Create a professional PR that's easy to review and provides full context.

## Steps

### 1. Pre-PR Checklist

Before creating the PR, ensure:

- [ ] All tests pass: `uv run pytest`
- [ ] Code is formatted: `uv run black .`
- [ ] Linting passes: `uv run ruff check .`
- [ ] Type checking passes: `uv run mypy .`
- [ ] Documentation updated (READMEs, docstrings)
- [ ] CHANGELOG.md updated with user-facing changes
- [ ] Commit messages are clear and follow conventions
- [ ] No debug code or console.log statements
- [ ] No secrets or sensitive data committed

### 2. Review Your Changes

```bash
# View full diff from main
git diff main...HEAD

# Review commit history
git log main..HEAD --oneline

# Check branch status
git status
```

Ask yourself:

- Do changes accomplish the goal?
- Is anything missing?
- Are commits logical and well-organized?
- Would this be easy to review?

### 3. Update Branch (If Needed)

```bash
# Fetch latest from remote
git fetch origin

# Rebase onto main (cleaner history)
git rebase origin/main

# Or merge if rebase is risky
git merge origin/main

# Run tests after rebase/merge
uv run pytest
```

### 4. Push Branch

```bash
# Push to remote (create tracking branch)
git push -u origin $(git branch --show-current)

# Or if branch already exists
git push
```

### 5. Create PR with GitHub CLI

**Option A: Simple PR**:

```bash
# Uses first commit message as title and description
gh pr create --fill
```

**Option B: Interactive**:

```bash
# Prompts for title, body, and reviewers
gh pr create
```

**Option C: Full control**:

```bash
gh pr create \
  --title "feat(i18n): implement version-aware language pack system" \
  --body "$(cat <<'EOF'
## Summary
Implements version-aware language pack loading with automatic Python version detection and inheritance support.

## Changes
- Add `VersionIndex` parser for Python version metadata
- Implement `PythonVersionDetector` with priority-based detection
- Create `LanguagePackLoader` with multi-level inheritance
- Add Spanish and Arabic language packs for Python 3.10-3.13
- Comprehensive test suite with 95% coverage

## Test Plan
- Unit tests: `cd libs/i18n && uv run pytest -v`
- Integration tests cover version detection and pack loading
- Manual testing with sample projects

## Performance
- Pack loading: 35ms with caching
- Version detection: 8ms average

## Security
- Path traversal prevention in inheritance
- Max inheritance depth (10 levels)
- Schema validation for all YAML files

## Checklist
- [x] Tests added and passing (95% coverage)
- [x] Documentation updated (README, user guide)
- [x] CHANGELOG.md updated
- [x] Type hints complete (mypy passing)
- [x] Code formatted and linted

Closes #123
EOF
)" \
  --base main \
  --head feature/CORE-346-version-aware-language-packs
```

### 6. PR Description Template

Use this structure for comprehensive PRs:

```markdown
## Summary
{1-2 sentence description of what changed and why}

## Motivation
{Why is this change needed? What problem does it solve?}

## Changes
- {Bullet list of key changes}
- {Include file paths for major changes}

## Approach
{Brief explanation of the approach taken}
{Highlight any architectural decisions or trade-offs}

## Test Plan
{How to test these changes}
- Unit tests: {commands to run}
- Manual testing: {steps to reproduce}
- Edge cases covered: {list}

## Screenshots (if applicable)
{For UI changes, include before/after screenshots}

## Performance Impact
{Any performance considerations}
{Benchmarks if relevant}

## Security Considerations
{Any security implications}
{How they're addressed}

## Breaking Changes
{List any breaking changes}
{Migration guide if needed}

## Checklist
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Code formatted and linted
- [ ] Type checking passes
- [ ] No sensitive data in commits

## Related Issues
Closes #{issue-number}
Relates to #{other-issue}

## Reviewer Notes
{Anything specific you want reviewers to focus on}
{Areas where you'd like feedback}
```

### 7. Example PR Descriptions

**Feature PR**:

```markdown
## Summary
Add version-aware language pack system that automatically detects Python version and loads appropriate translations with inheritance support.

## Motivation
Legesher needs to support multiple Python versions (3.10-3.13+) with different keyword sets. This system enables maintainers to define packs incrementally (3.11 extends 3.10) rather than duplicating all keywords.

## Changes
- `libs/i18n/legesher_i18n/version_index.py`: Parse version metadata
- `libs/i18n/legesher_i18n/version_detector.py`: Auto-detect Python version
- `libs/i18n/legesher_i18n/pack_loader.py`: Load packs with inheritance
- `libs/i18n/languages/python/`: Spanish and Arabic packs (3.10-3.13)
- `libs/i18n/tests/`: Comprehensive test suite (95% coverage)

## Approach
Chose YAML for language packs (human-readable), version detection priority (pyproject.toml → .python-version → runtime), and caching for performance. See `.claude/scratchpads/CORE-346-implementation-plan.md` for full rationale.

## Test Plan
```bash
cd libs/i18n && uv run pytest -v --cov
```

Edge cases tested:
- Circular inheritance (prevented)
- Path traversal (sanitized)
- Missing files (graceful fallback)

## Performance Impact
- Pack loading: 35ms (with caching), 120ms (first load)
- Memory: ~2MB per pack cached
- Acceptable for CLI/IDE use

## Security Considerations
- All file paths sanitized (prevent `../` escapes)
- Max inheritance depth (10 levels)
- YAML schema validation with Pydantic
- No arbitrary code execution

## Checklist
- [x] Tests added (95% coverage)
- [x] Documentation: README, user guide
- [x] CHANGELOG.md updated
- [x] Type hints complete
- [x] Passes ruff, black, mypy

Closes #123
```

**Bug Fix PR**:

```markdown
## Summary
Fix infinite loop in AST transformer when processing deeply nested nodes.

## Motivation
Issue #456 reported stack overflow on files with > 50 levels of nesting.

## Changes
- `libs/core/legesher_core/ast_transformer.py`: Add max depth check
- `libs/core/tests/test_ast_transformer.py`: Add regression test

## Test Plan
Added test with 100-level nesting that previously crashed.

```bash
cd libs/core && uv run pytest tests/test_ast_transformer.py::test_deep_nesting
```

## Checklist
- [x] Regression test added
- [x] Existing tests still pass

Fixes #456
```

### 8. Request Reviews

```bash
# Add reviewers
gh pr edit --add-reviewer username1,username2

# Add labels
gh pr edit --add-label "package:i18n,priority:high"

# Add to milestone
gh pr edit --milestone v0.1
```

### 9. Respond to Reviews

- Respond promptly to feedback
- Address all comments (agree and fix, or explain rationale)
- Push additional commits to address feedback
- Mark conversations as resolved when addressed
- Be open to suggestions and ask clarifying questions

### 10. Merge

Once approved:

```bash
# Squash and merge (one commit in main)
gh pr merge --squash

# Or merge commit (preserve history)
gh pr merge --merge

# Or rebase (linear history)
gh pr merge --rebase

# Auto-delete branch
gh pr merge --squash --delete-branch
```

**For Legesher**: Prefer `--squash` for cleaner main history unless commits are logically separated.

## PR Best Practices

### Size

- **Small PRs**: < 400 lines changed
- **Medium PRs**: 400-1000 lines
- **Large PRs**: > 1000 lines (avoid if possible)

**Tip**: Break large features into multiple small PRs that can be reviewed independently.

### Description

- **Context**: Explain WHY, not just WHAT
- **Visual**: Screenshots for UI changes
- **Testing**: Clear instructions for reviewers to test
- **Links**: Reference issues, docs, related PRs

### Commits

- Clean history before PR
- Squash "wip" and "fix typo" commits
- Keep meaningful commits separate
- Descriptive commit messages

### Reviews

- Request specific reviewers when possible
- Address all feedback (agree or discuss)
- Don't take feedback personally
- Thank reviewers for their time

## For Solo Founders

Even without teammates, create thorough PRs:

- **Self-review**: Catch issues before merging
- **Documentation**: Record decisions for future you
- **Professional**: Ready for when contributors join
- **Portfolio**: Show potential employers/contributors your process

## For Open Source Projects

PRs are your first impression:

- **Professional**: Well-written PRs attract contributors
- **Teaching tool**: Show practices you want others to follow
- **Onboarding**: Help contributors understand codebase
- **Async communication**: Provide full context for reviewers in different timezones

## GitHub CLI Tips

```bash
# View PR status
gh pr status

# List PRs
gh pr list

# View PR in browser
gh pr view --web

# Check CI status
gh pr checks

# Add comment
gh pr comment --body "Updated based on feedback"
```

## Deliverable

Create a PR with:

- Clear, comprehensive description
- Relevant labels and reviewers
- Clean commit history
- All checks passing
- Ready for review

Remember: A great PR is easy to review and provides all the context needed to make a decision.