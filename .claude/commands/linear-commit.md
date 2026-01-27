<!--
SOURCES:
- Linear Integration best practices
- Conventional Commits: https://www.conventionalcommits.org/
- Linear API MCP integration
-->

# Linear Commit: $ARGUMENTS

**Goal**: Create a git commit linked to a Linear issue with proper formatting and automatic issue updates.

## Instructions

Create a well-structured commit that automatically updates the related Linear issue.

## Steps

### 1. Identify Linear Issue

**From arguments**:

- If `$ARGUMENTS` contains issue ID (e.g., `LEG-123`), use that
- If current branch name contains issue ID (e.g., `feature/leg-123-description`), extract it

**Extract from branch**:

```bash
# Get current branch
current_branch=$(git branch --show-current)

# Extract Linear issue ID (case insensitive)
issue_id=$(echo "$current_branch" | grep -oiE '(leg|core|i18n|home|vsc)-[0-9]+' | head -1)

if [ -n "$issue_id" ]; then
  echo "Found Linear issue: $issue_id"
else
  echo "No Linear issue found in branch name"
fi
```

### 2. Fetch Linear Issue Details

Use Linear MCP to get issue context:

```python
# Use the Linear MCP get_issue function
issue_id = "$ARGUMENTS" or extract_from_branch()
issue = mcp__MCP_DOCKER__get_issue(id=issue_id)

# Note issue details:
# - title
# - description
# - labels
# - current state
```

### 3. Review Git Changes

```bash
# See what's changed
git status
git diff
git diff --staged
```

### 4. Stage Relevant Changes

```bash
# Stage specific files related to the Linear issue
git add {files}

# Review staged changes
git diff --staged
```

### 5. Generate Commit Message

Use this format for Linear integration:

```text
<type>(<scope>): <subject>

<body>

Refs <LINEAR-ISSUE-ID>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type based on Linear labels**:

- `bug` label → `fix:`
- `enhancement` label → `feat:`
- `documentation` label → `docs:`
- `refactor` label → `refactor:`
- `testing` label → `test:`

**Scope from Linear labels**:

- `package:core` → `(core)`
- `package:i18n` → `(i18n)`
- `package:legesher` → `(legesher)`
- `package:vs-code` → `(vs-code)`
- `package:home` → `(home)`

**Example**:

```text
feat(i18n): implement version-aware language pack loader

Implement automatic Python version detection with priority-based
resolution (pyproject.toml → .python-version → runtime). Add
inheritance support for language packs to reduce duplication.

Refs LEG-123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 6. Create Commit

```bash
git commit -m "$(cat <<'EOF'
feat(i18n): implement version-aware language pack loader

Implement automatic Python version detection with priority-based
resolution (pyproject.toml → .python-version → runtime). Add
inheritance support for language packs to reduce duplication.

Refs LEG-123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 7. Update Linear Issue

Use Linear MCP to add commit comment:

```python
# Get commit details
commit_sha = git_get_latest_commit_sha()
commit_msg = git_get_commit_message(commit_sha)

# Add comment to Linear issue
comment_body = f"""## Commit Created

**Commit**: `{commit_sha[:7]}`

**Message**:
> {commit_msg.replace(chr(10), chr(10) + '> ')}

[View commit](https://github.com/legesher/legesher/commit/{commit_sha})
"""

mcp__MCP_DOCKER__create_comment(issueId=issue_id, body=comment_body)
```

### 8. Move Linear Issue State (Optional)

If this commit completes work:

```python
# Update issue state to "In Review" or "Ready for Review"
mcp__MCP_DOCKER__update_issue(
    id=issue_id,
    state="In Review"  # or appropriate state
)
```

### 9. Verify Commit

```bash
# View commit
git log -1

# View commit with diff
git show HEAD
```

## Linear Issue State Workflow

Based on commit type, suggest state updates:

**Initial commit for issue**:

- `Todo` → `In Progress`

**Bug fix completed**:

- `In Progress` → `In Review`

**Feature completed**:

- `In Progress` → `In Review`

**Tests added**:

- Keep in `In Progress` (unless complete)

**Docs updated**:

- `In Progress` → `In Review` (if docs were the task)

## Example Workflow

```bash
# 1. Working on Linear issue LEG-123
git checkout -b feature/leg-123-version-aware-packs

# 2. Make changes
# ... coding ...

# 3. Use this command
/linear-commit LEG-123

# 4. Claude will:
# - Fetch Linear issue details
# - Review git changes
# - Generate appropriate commit message
# - Create commit with Linear reference
# - Add comment to Linear issue
# - Suggest state update
```

## Commit Message Templates

### Feature Implementation

```text
feat(i18n): add Spanish language pack

Implement complete Python 3.10-3.13 keyword mappings for Spanish
with cultural comments and metadata.

Refs LEG-124

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Bug Fix

```text
fix(core): prevent infinite loop in AST transformer

Add max depth check (100 levels) to prevent stack overflow when
processing deeply nested AST nodes.

Fixes LEG-127

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Test Addition

```text
test(i18n): add version detector comprehensive tests

Add tests for auto-detection priority:
- pyproject.toml parsing
- .python-version file
- runtime fallback

Refs LEG-123

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Linear MCP Integration Points

Use these Linear MCP functions:

1. **Get issue details**: `mcp__MCP_DOCKER__get_issue(id=issue_id)`
2. **Add comment**: `mcp__MCP_DOCKER__create_comment(issueId, body)`
3. **Update state**: `mcp__MCP_DOCKER__update_issue(id, state)`
4. **List issue statuses**: `mcp__MCP_DOCKER__list_issue_statuses(team)`

## Pre-Commit Checklist

- [ ] Commit references correct Linear issue
- [ ] Tests pass: `uv run pytest`
- [ ] Code formatted: `uv run black . && uv run ruff check .`
- [ ] Linear issue state updated appropriately
- [ ] Commit message is clear and follows conventions

## Tips

- Use branch naming: `feature/leg-123-brief-description` for automatic issue detection
- Use `Refs LEG-123` for work-in-progress commits
- Use `Fixes LEG-123` or `Closes LEG-123` for completion commits
- Always update Linear issue with commit comments for traceability

## Deliverable

Create a commit that:

- References Linear issue properly
- Follows Conventional Commits format
- Updates Linear issue with commit comment
- Moves issue to appropriate state
- Provides full traceability between git and Linear

Remember: Good Linear integration means your git history and Linear issues tell the same story.
