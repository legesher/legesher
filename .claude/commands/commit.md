<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- Git commit best practices
- Conventional Commits: https://www.conventionalcommits.org/
- Linear API MCP integration
-->

# Create Commit: $ARGUMENTS

**Goal**: Create a well-structured git commit with Linear integration. Auto-detects the Linear issue from the branch name or arguments, links the commit back to the issue, and keeps Linear in sync.

## Instructions

Create a focused, conventional commit. If a Linear issue is detected, use its labels to infer commit type/scope and post a comment back to the issue after committing.

## Steps

### 1. Identify Linear Issue (Auto-Detect)

**Check in order:**

1. If `$ARGUMENTS` contains an issue ID (e.g., `CORE-123`), use that
2. If the current branch name contains an issue ID, extract it
3. If neither, proceed without Linear integration (plain commit)

```bash
# Get current branch
current_branch=$(git branch --show-current)

# Extract Linear issue ID (case insensitive)
issue_id=$(echo "$current_branch" | grep -oiE '(core|local|i18n|home|vsc|api)-[0-9]+' | head -1)
```

### 2. Fetch Linear Issue Details (If Found)

If a Linear issue was identified, fetch its context:

```python
issue = mcp__linear__get_issue(id=issue_id)

# Extract from issue:
# - title, description, labels → infer type and scope
# - current state → determine state transition after commit
# - project, cycle → context for commit body
```

**If no Linear issue found**, skip to Step 3 and infer type/scope from the code changes and `$ARGUMENTS`.

### 3. Review Changes

```bash
# See what's changed
git status
git diff
git diff --staged
```

- Confirm: Changes match what you intended
- Verify: No debug code, console.log, or secrets included
- Check: No unintended changes to other files

### 4. Stage Changes Selectively

```bash
# Stage specific files — keep commits focused on ONE logical change
git add libs/{package}/{file}.py
git add tests/test_{feature}.py

# Review staged changes
git diff --staged
```

### 5. Generate Commit Message

Use **Conventional Commits** format:

```text
<type>(<scope>): <subject>

<body>

Refs CORE-123

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Type** (required) — infer from Linear labels when available:

| Linear Label | Commit Type | Description |
|---|---|---|
| `type:bug` | `fix` | Bug fix |
| `type:feature` | `feat` | New feature |
| `type:docs` | `docs` | Documentation only |
| `type:refactor` | `refactor` | Code restructuring (no behavior change) |
| `type:test` | `test` | Adding or updating tests |
| `type:chore` | `chore` | Maintenance tasks (deps, config) |
| `type:ci` | `ci` | CI/CD changes |
| _(no label)_ | `style` | Code style/formatting |
| _(no label)_ | `perf` | Performance improvement |

**Scope** (optional) — infer from Linear labels or changed files:

| Linear Label | Scope |
|---|---|
| `pkg:core` | `(core)` |
| `pkg:i18n` | `(i18n)` |
| `pkg:cli` | `(legesher)` |
| `pkg:language-server` | `(language-server)` |
| `pkg:vs-code` | `(vs-code)` |
| `pkg:api` | `(api)` |
| `pkg:home` | `(home)` |
| `pkg:docs` | `(docs)` |
| `pkg:preview` | `(preview)` |

If no label, infer from which `libs/` directory the changes touch.

Additional scopes: `ci`, `deps`

**Subject** (required):

- Imperative mood: "add" not "added" or "adds"
- No period at the end
- Max 72 characters
- Lowercase (except proper nouns)

**Body** (recommended):

- Explain WHAT changed and WHY
- Wrap at 72 characters
- Include any implementation details, design decisions, or context from the conversation that would be useful for future reference

**Footer** (required when Linear issue exists):

- Work-in-progress: `Refs CORE-123`
- Completion: `Fixes CORE-123` or `Closes CORE-123`
- Breaking changes: `BREAKING CHANGE: description`
- Co-authored-by: Always include the Claude co-author line

### 6. Create Commit

```bash
git commit -m "$(cat <<'EOF'
feat(i18n): implement version-aware language pack loader

Implement automatic Python version detection with priority-based
resolution (pyproject.toml → .python-version → runtime). Add
inheritance support for language packs to reduce duplication.

Refs CORE-123

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### 7. Update Linear Issue (If Found)

**Only runs when a Linear issue was detected in Step 1.**

Post a commit comment to the Linear issue:

```python
commit_sha = git_get_latest_commit_sha()
commit_msg = git_get_commit_message(commit_sha)

comment_body = f"""## Commit Created

**Commit**: `{commit_sha[:7]}`

**Message**:
> {commit_msg.replace(chr(10), chr(10) + '> ')}

[View commit](https://github.com/MadiEdgar/legesher/commit/{commit_sha})
"""

mcp__linear__create_comment(issueId=issue_id, body=comment_body)
```

**State transition** — suggest based on context:

Linear workspace states (Core team):

| State | Type | Emoji |
|-------|------|-------|
| Backlog | backlog | — |
| To Be Groomed | backlog | 🗺 |
| Blocked | backlog | 🛑 |
| Planned | unstarted | 📅 |
| Ready | unstarted | 🧼 |
| In Progress | started | 🏗️ |
| In Review | started | 🚩 |
| Done | completed | ✅ |
| Canceled | canceled | ❌ |
| Duplicate | canceled | ❕ |

| Situation | Transition |
|---|---|
| First commit for issue | `Ready` / `Planned` → `In Progress` |
| Bug fix completed | `In Progress` → `In Review` |
| Feature completed | `In Progress` → `In Review` |
| Tests added (not complete) | Keep `In Progress` |
| Docs updated (if docs were the task) | `In Progress` → `In Review` |

```python
# Only if state transition is appropriate
mcp__linear__update_issue(id=issue_id, state="In Progress")
```

### 8. Verify Commit

```bash
# View most recent commit
git log -1

# See commit with diff
git show HEAD
```

### 9. Amend if Needed (Before Pushing)

```bash
# Fix commit message
git commit --amend -m "corrected message"

# Add forgotten changes
git add {forgotten-file}
git commit --amend --no-edit
```

**IMPORTANT**: Only amend commits that haven't been pushed yet!

## Pre-Commit Checklist

- [ ] Code follows project conventions
- [ ] Tests pass: `uv run pytest`
- [ ] Linting passes: `uv run ruff check .`
- [ ] No debug code left behind
- [ ] No secrets or sensitive data in commit
- [ ] Commit references correct Linear issue (if applicable)
- [ ] Linear issue state updated appropriately
- [ ] CHANGELOG.md updated for user-facing changes

## Example Workflows

### With Linear issue (auto-detected from branch)

```bash
# Branch: CORE-435-validate-transformer-migrated-packs
/commit

# Claude will:
# 1. Detect CORE-435 from branch name
# 2. Fetch issue details and labels
# 3. Review git changes
# 4. Generate commit message with type/scope from labels
# 5. Create commit with "Refs CORE-435" footer
# 6. Post commit comment to CORE-435 in Linear
# 7. Suggest state transition
```

### With explicit Linear issue

```bash
/commit CORE-435
```

### Without Linear issue (plain commit)

```bash
# Branch: main or feature/quick-fix
/commit fix typo in README

# Claude will:
# 1. No Linear issue found — proceed with plain commit
# 2. Review git changes
# 3. Generate conventional commit message
# 4. Create commit (no Linear integration)
```

## Commit Message Anti-Patterns

**Avoid**:

- `fix stuff`, `update code`, `changes` — too vague
- `bug fix`, `wip` — not descriptive
- `added feature`, `fixed bug` — past tense (use imperative)

**Good**:

- `feat(core): add token-based AST transformer`
- `fix(i18n): prevent path traversal in pack loader`
- `test(api): add edge case tests for null inputs`

## Linear MCP Functions Used

1. **Get issue details**: `mcp__linear__get_issue(id=issue_id)`
2. **Add comment**: `mcp__linear__create_comment(issueId, body)`
3. **Update state**: `mcp__linear__update_issue(id, state)`
4. **List issue statuses**: `mcp__linear__list_issue_statuses(team)`

## Deliverable

Create a commit that:

- Follows Conventional Commits format
- References Linear issue (when detected) with full traceability
- Updates Linear issue with commit comment and state transition
- Is focused, atomic, and passes all quality checks

Remember: Good commits mean your git history and Linear issues tell the same story.
