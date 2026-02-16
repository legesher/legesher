---
description: Post-merge cleanup — delete branch, summarize work on Linear issue, mark Done
---

# Close PR: $ARGUMENTS

**Goal**: Clean up after a merged PR — verify no lingering changes, delete the branch, post a summary comment on the Linear issue capturing what was implemented, review feedback, and key decisions, then move the issue to Done.

## Arguments

- If `$ARGUMENTS` contains a PR number (e.g., `115`), use that
- If `$ARGUMENTS` contains a Linear issue ID (e.g., `CORE-663`), find the associated PR
- If empty, detect from the current branch name

## Steps

### 1. Identify the PR and Linear Issue

```bash
# If on a feature branch, get PR info
current_branch=$(git branch --show-current)

# Get PR details (merged status, title, body, reviews)
gh pr view <number> --json number,title,body,state,mergedAt,headRefName,reviews,comments
```

Extract the Linear issue ID from:
1. `$ARGUMENTS` if provided
2. Branch name (e.g., `CORE-663-description` → `CORE-663`)
3. PR title or body (look for `CORE-xxx` pattern)

If no Linear issue found, skip Linear steps (4-6) and just do branch cleanup.

### 2. Check for Uncommitted Changes

**Before deleting anything, verify the working tree is clean:**

```bash
git status
git diff
git diff --staged
```

**If there are uncommitted changes:**
- STOP and warn Madison
- List the files with changes
- Ask whether to: stash them, commit them, or discard them
- Do NOT proceed with branch deletion until resolved

**If clean, continue.**

### 3. Switch to Main and Delete Branch

> **Note:** Many repos have "Automatically delete head branches" enabled in GitHub settings.
> The remote branch may already be gone after merge — that's normal.

```bash
# Switch to main and pull latest (which includes the merged PR)
git checkout main
git pull origin main

# Delete local branch
git branch -d <branch-name>

# Delete remote branch (if not already deleted by GitHub)
git push origin --delete <branch-name> 2>/dev/null || echo "Remote branch already deleted"
```

### 4. Gather PR Context for Linear Summary

Collect all the information needed for the summary comment:

**From the PR:**
```bash
# Get PR details
gh pr view <number> --json title,body,mergedAt,additions,deletions,changedFiles,commits

# Get review comments and feedback
gh pr view <number> --json reviews,comments

# Get the commit list
gh pr view <number> --json commits
```

**From the Linear issue:**
```python
issue = mcp__linear__get_issue(id=issue_id, includeRelations=True)
comments = mcp__linear__list_comments(issueId=issue_id)
```

### 5. Post Summary Comment on Linear Issue

Compile and post a comprehensive comment to the Linear issue:

```python
comment_body = """
## PR Merged — Implementation Summary

**PR:** #<number> — <title>
**Merged:** <date>
**Branch:** `<branch-name>`
**Changes:** +<additions> / -<deletions> across <files> files

### What Was Implemented

- [Bullet list of key changes from the PR description and commits]
- [Focus on what was actually shipped, not just what was planned]

### Review Feedback

- [Summarize any review comments that were made]
- [Note any changes made in response to review]
- [If no reviews, note "No review comments"]

### Key Decisions

- [Major decisions made during implementation or review]
- [Trade-offs chosen and rationale]
- [Anything that deviated from the original plan and why]

### Files Changed

- `path/to/file.py` — [brief description of change]
- `path/to/other.py` — [brief description of change]

---
*Closed via PR #<number> on <date>*
"""

mcp__linear__create_comment(issueId=issue_id, body=comment_body)
```

**Important:** The summary should capture institutional knowledge — decisions, trade-offs, and context that would be lost if someone only reads the issue description. This is especially valuable for:
- Onboarding future contributors
- Understanding why things were done a certain way
- Referencing back when similar work comes up

### 6. Link PR to Linear Issue (If Not Already Linked)

Check if the PR URL is already in the issue's links. If not, add it:

```python
# Read existing links first — links parameter REPLACES, doesn't append
issue = mcp__linear__get_issue(id=issue_id)
existing_links = issue.get("attachments", [])

pr_url = f"https://github.com/MadiEdgar/legesher/pull/{pr_number}"
if not any(pr_url in str(link) for link in existing_links):
    mcp__linear__update_issue(
        id=issue_id,
        links=[{"url": pr_url, "title": f"PR #{pr_number}: {pr_title}"}]
    )
```

### 7. Move Linear Issue to Done

```python
mcp__linear__update_issue(
    id=issue_id,
    state="Done"
)
```

### 7. Confirm Completion

Report back to Madison:

- Branch deleted (local + remote)
- Summary comment posted on Linear issue
- Issue moved to Done
- Link to the Linear issue for reference

## Example Workflows

### After merging a PR (on the feature branch)

```bash
# You're on CORE-663-consolidate-claude-slash-commands
# PR #115 was just merged on GitHub
/close-pr

# Claude will:
# 1. Detect CORE-663 from branch name
# 2. Verify no uncommitted changes
# 3. Switch to main, pull, delete branch
# 4. Fetch PR #115 details, reviews, and comments
# 5. Post implementation summary on CORE-663
# 6. Move CORE-663 to Done
```

### With explicit PR number

```bash
/close-pr 115
```

### With explicit Linear issue

```bash
/close-pr CORE-663
```

### Already on main (branch was auto-deleted)

```bash
/close-pr 115

# Claude will:
# 1. Use PR #115 to find branch name and CORE-663
# 2. Skip branch deletion (already on main)
# 3. Post summary and move to Done
```

## Edge Cases

**PR has multiple Linear issues:**
- If the PR references multiple issues (e.g., `[CORE-623] [CORE-624]`), post the summary comment on ALL referenced issues and move them all to Done.

**PR wasn't merged yet:**
- Warn Madison that the PR is still open
- Do NOT delete the branch or move the issue to Done
- Offer to just compile a draft summary for review

**No review comments:**
- Note "No review comments — merged without discussion" in the summary
- This is fine for straightforward changes

**Branch already deleted:**
- Skip branch deletion step, continue with Linear summary

## Linear MCP Functions Used

1. **Get issue details**: `mcp__linear__get_issue(id=issue_id, includeRelations=True)`
2. **Get comments**: `mcp__linear__list_comments(issueId=issue_id)`
3. **Post summary**: `mcp__linear__create_comment(issueId, body)`
4. **Move to Done**: `mcp__linear__update_issue(id, state="Done")`

## Deliverable

After running this command:

- Working tree is clean on `main` with latest changes
- Feature branch deleted locally and remotely
- Linear issue has a comprehensive summary comment capturing what was built, review feedback, and key decisions
- Linear issue status is "Done"
- Full traceability: Linear issue → implementation plan → PR → merge summary
