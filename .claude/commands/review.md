<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- Code review best practices for AI-assisted development
-->

# Code Review: $ARGUMENTS

**Goal**: Perform a thorough code review of: $ARGUMENTS

## Instructions

You are a code reviewer. Be thorough, constructive, and objective.

## Review Checklist

### 1. Understand the Change

- Read: PR description, linked issues
- Run: `git diff main...HEAD` to see full diff
- Review: Commit messages for context
- Understand: What problem is being solved? Why this approach?

### 2. Code Quality

**Readability**:

- [ ] Code is easy to understand
- [ ] Variable/function names are descriptive
- [ ] Complex logic has explanatory comments
- [ ] No unnecessary abbreviations

**Structure**:

- [ ] Functions are small and focused (< 50 lines ideally)
- [ ] No code duplication (DRY principle)
- [ ] Proper separation of concerns
- [ ] Consistent with project conventions

**Error Handling**:

- [ ] Errors are caught and handled appropriately
- [ ] Error messages are helpful and actionable
- [ ] No silent failures
- [ ] Edge cases are handled

**Type Safety**:

- [ ] Type hints are present and correct (Python 3.13+)
- [ ] No `Any` types unless necessary
- [ ] Proper use of Optional, Union, etc.

### 3. Security Review

**Input Validation**:

- [ ] All user inputs are validated
- [ ] Path traversal vulnerabilities prevented
- [ ] SQL injection / command injection prevented
- [ ] No hardcoded secrets or credentials

**Data Handling**:

- [ ] Sensitive data is not logged
- [ ] Data is sanitized before use
- [ ] No exposure of internal implementation details
- [ ] Proper authentication/authorization checks

### 4. Testing

**Test Coverage**:

- [ ] Unit tests cover new/changed code
- [ ] Integration tests for component interactions
- [ ] Edge cases have explicit tests
- [ ] Tests are clear and maintainable

**Test Quality**:

- [ ] Tests test behavior, not implementation
- [ ] No flaky tests (time-dependent, order-dependent)
- [ ] Test names describe what's being tested
- [ ] Fixtures/mocks are used appropriately

Run tests:

```bash
cd libs/{package} && uv run pytest -v --cov
```

### 5. Performance

- [ ] No obvious performance issues (N+1 queries, infinite loops)
- [ ] Appropriate data structures used
- [ ] Caching used where beneficial
- [ ] No unnecessary file I/O or network calls in loops

### 6. Documentation

- [ ] README updated if public API changed
- [ ] Docstrings added for new functions/classes
- [ ] CHANGELOG.md updated with user-facing changes
- [ ] Complex algorithms have explanation comments
- [ ] Architecture docs updated if needed

### 7. Dependencies

**Package Changes**:

- [ ] New dependencies are necessary and well-maintained
- [ ] Version pinning is appropriate
- [ ] No security vulnerabilities in dependencies
- [ ] `uv.lock` is updated

**Cross-package Dependencies**:

- [ ] Changes don't break dependent packages
- [ ] Version compatibility maintained
- [ ] `[tool.uv.sources]` properly configured

### 8. Git History

**Commits**:

- [ ] Commit messages are clear and descriptive
- [ ] Commits are logical units of work
- [ ] No "wip" or "fix typo" commits (squash if needed)
- [ ] No merge commits (rebase instead)

**Branch**:

- [ ] Branch name follows convention: `feature/`, `fix/`, etc.
- [ ] Branch is up to date with main
- [ ] No conflicts with main branch

### 9. Project-Specific Checks (Legesher)

**Monorepo**:

- [ ] Changes in correct package (core, i18n, legesher, vs-code, home)
- [ ] No circular dependencies between packages
- [ ] Tier hierarchy respected (core → i18n → legesher → home)

**Architecture**:

- [ ] Follows patterns in CLAUDE.md and architecture docs
- [ ] Translation approach aligns with decisions
- [ ] IDE-agnostic where applicable
- [ ] Version-aware language pack structure followed

**Future-proofing**:

- [ ] Extensible to other programming languages
- [ ] Works across Python versions (3.10-3.13+)
- [ ] Considers multiple IDEs (VS Code, Zed, PyCharm)

### 10. Run Quality Checks

```bash
# Linting
uv run ruff check libs/{package}/

# Formatting
uv run black --check libs/{package}/

# Type checking
uv run mypy libs/{package}/

# Tests with coverage
uv run pytest --cov=legesher_{package} --cov-report=term-missing

# Security scan
uv run bandit -r libs/{package}/
```

## Review Feedback Template

Provide feedback in this format:

### Summary

{Brief overview of the change and overall assessment}

### ✅ Strengths

- {Positive aspects of the implementation}

### 🔴 Critical Issues (Must Fix)

- [ ] {Issue 1 with location and suggested fix}
- [ ] {Issue 2 with location and suggested fix}

### 🟡 Suggestions (Should Consider)

- {Improvement 1 with rationale}
- {Improvement 2 with rationale}

### 💡 Nice to Have (Optional)

- {Enhancement 1}
- {Enhancement 2}

### Questions

- {Clarifying question 1}
- {Clarifying question 2}

### Verdict

- ✅ **APPROVE**: Ready to merge
- 🔄 **REQUEST CHANGES**: Must address critical issues first
- 💬 **COMMENT**: Feedback provided, author decides next steps

## Best Practices for Reviews

**Be Constructive**:

- Explain WHY, not just WHAT to change
- Suggest concrete alternatives
- Acknowledge good work
- Frame feedback as questions when appropriate

**Be Objective**:

- Focus on the code, not the person
- Reference project standards and conventions
- Point to docs/examples
- Distinguish opinions from requirements

**Be Thorough**:

- Don't rubber-stamp
- Check for security issues carefully
- Consider edge cases and failure modes
- Think about long-term maintenance

**For Open Source**:

- Remember: contributors are volunteers
- Be encouraging and supportive
- Explain context and conventions
- Offer to pair/discuss if helpful

## Automated Review Tools

Consider using automated tools to catch common issues:

```bash
# Run all checks
uv run ruff check . && uv run black --check . && uv run mypy . && uv run pytest
```

Set up pre-commit hooks to automate these checks (see `.claude/settings.json`).

## Deliverable

Provide comprehensive review feedback following the template above, with specific, actionable recommendations.

Remember: Good reviews improve code quality, share knowledge, and maintain project standards.
