---
description: Batch update Linear issues for cycle rituals — triage, label, estimate, link, and clean up
---

# Batch Update Linear Issues: $ARGUMENTS

**Goal**: Perform bulk updates across Linear issues as part of a cycle ritual. This command handles the recurring workspace maintenance that keeps issues organized, labeled, estimated, and linked.

## When to Use

Run this command at cycle boundaries:
- **Cycle start**: Triage new issues, assign to cycle, ensure metadata is complete
- **Cycle end**: Close completed work, carry over incomplete issues, clean up labels
- **Ad-hoc**: When a batch of issues need the same type of update

## Arguments

`$ARGUMENTS` specifies the operation. If empty, run the **full cycle triage** (all operations).

| Argument | Description |
|---|---|
| _(empty)_ | Full cycle triage — run all operations below |
| `triage` | Triage "To Be Groomed" issues — add labels, estimates, rename titles |
| `label` | Re-label issues missing `pkg:*` or `area:*` labels |
| `estimate` | Add point estimates to unestimated issues in current cycle or project |
| `link-prs` | Link merged PRs to their corresponding Linear issues |
| `rename` | Rename issue titles to `[package:subcategory] Title` convention |
| `cycle-prep` | Prepare next cycle — move ready issues in, verify metadata |
| `cleanup` | Find stale issues (no updates in 30+ days), canceled work, duplicates |

## Linear Workspace States Reference

| State | Type | Use for Filtering |
|-------|------|-------------------|
| Backlog | backlog | `state="backlog"` |
| 🗺 To Be Groomed | backlog | `state="backlog"` |
| 🛑 Blocked | backlog | `state="backlog"` |
| 📅 Planned | unstarted | `state="unstarted"` |
| 🧼 Ready | unstarted | `state="unstarted"` |
| 🏗️ In Progress | started | `state="started"` |
| 🚩 In Review | started | `state="started"` |
| ✅ Done | completed | `state="completed"` |
| ❌ Canceled | canceled | `state="canceled"` |
| ❕ Duplicate | canceled | `state="canceled"` |

> **Tip:** Use state *types* (`started`, `unstarted`, `backlog`) for filtering — they're more reliable than names which have emoji prefixes.

## Operations

### 1. Triage (`triage`)

Find issues in "To Be Groomed" or "Backlog" that are missing metadata:

```python
# Fetch issues needing triage — use state type "backlog" to catch both Backlog and To Be Groomed
issues = mcp__linear__list_issues(team="Core", state="backlog")
```

For each issue, check and fix:

- [ ] **Title**: Follows `[package:subcategory] Title` format?
- [ ] **Labels**: Has at least one `pkg:*` label?
- [ ] **Estimate**: Has a point estimate?
- [ ] **Priority**: Has priority set?

**Present a table** of issues needing updates, grouped by what's missing. Wait for Madison's approval before making changes.

### 2. Label (`label`)

Find issues missing package or area labels:

```python
# Get all active issues using state types
issues = mcp__linear__list_issues(team="Core", state="started")    # In Progress + In Review
issues += mcp__linear__list_issues(team="Core", state="unstarted") # Planned + Ready
```

For each issue:
- Infer `pkg:*` label from title prefix (e.g., `[vs-code:...]` → `pkg:vs-code`)
- Infer `area:*` labels from description/title keywords
- Infer `type:*` label from title prefix subcategory (e.g., `:bug` → `type:bug`)

**IMPORTANT: The `labels` parameter REPLACES all existing labels.** Always read the issue's current labels first and merge with proposed new ones. Never overwrite blindly.

**Present proposed label changes as a table.** Wait for approval before applying.

### 3. Estimate (`estimate`)

Find unestimated issues in a specific scope:

```python
# From arguments: project name, cycle, or "current-cycle"
# Default: current cycle
issues = mcp__linear__list_issues(cycle=current_cycle)
```

For each unestimated issue:
- Read the title, description, and labels
- Propose a Fibonacci estimate (1, 2, 3, 5, 8, 13) based on complexity
- Consider: number of packages affected, test requirements, design decisions needed

**Present a table** with proposed estimates. Wait for approval before applying.

### 4. Link PRs (`link-prs`)

Find merged PRs that aren't linked to their Linear issues:

```bash
# Get recent merged PRs
gh pr list --state merged --limit 50 --json number,title,mergedAt,headRefName
```

For each PR:
- Extract Linear issue ID from branch name or PR title (e.g., `CORE-435` from `CORE-435-feature-name`)
- Check if the issue already has a link to this PR
- If not, add it via `mcp__linear__update_issue(id, links=[{url, title}])`

**NOTE: The `links` parameter also REPLACES existing links.** Read existing links first and merge to avoid overwriting previous PR links.

**Present a table** of PR-to-issue mappings. Apply without waiting (linking is low-risk).

### 5. Rename (`rename`)

Find issues not following the `[package:subcategory] Title` naming convention:

```python
issues = mcp__linear__list_issues(team="Core", state="started")    # In Progress + In Review
issues += mcp__linear__list_issues(team="Core", state="unstarted") # Planned + Ready
```

For each issue:
- Check if title starts with `[something:something]`
- If not, propose a renamed title based on labels and description
- Infer package from `pkg:*` label or description
- Infer subcategory from `type:*` label or context

**Present a table** of current → proposed titles. Wait for approval before renaming.

### 6. Cycle Prep (`cycle-prep`)

Prepare for the next cycle:

```python
# Get current and next cycle
current = mcp__linear__list_cycles(teamId=team_id, type="current")
next_cycle = mcp__linear__list_cycles(teamId=team_id, type="next")

# Find "Ready" and "Planned" issues not in any cycle
ready_issues = mcp__linear__list_issues(team="Core", state="unstarted")
```

For each ready issue:
- Verify metadata is complete (labels, estimate, assignee)
- Propose adding to next cycle
- Flag any issues that are blocked or missing prerequisites

Also check:
- Issues in current cycle that are still "In Progress" — carry over to next?
- Issues in current cycle that are "✅ Done" — verify they're closed properly

**Present recommendations.** Wait for approval.

### 7. Cleanup (`cleanup`)

Find issues that may need attention:

```python
# Get all open issues, then filter for stale ones
# NOTE: updatedAt="-P30D" returns issues updated WITHIN the last 30 days.
# To find STALE issues, fetch all open issues and exclude recently updated ones.
all_in_progress = mcp__linear__list_issues(team="Core", state="started")
recently_updated = mcp__linear__list_issues(team="Core", state="started", updatedAt="-P30D")
# Stale = in all_in_progress but NOT in recently_updated
stale = [i for i in all_in_progress if i["id"] not in {r["id"] for r in recently_updated}]

# Potential duplicates: similar titles
all_open = mcp__linear__list_issues(team="Core", state="unstarted")
```

Report:
- **Stale issues**: Open but no activity in 30+ days — suggest cancel, backlog, or ping
- **Unassigned in-progress**: Issues marked "In Progress" with no assignee
- **Missing projects**: Issues not associated with any project
- **High priority without cycle**: Urgent/High issues not in any cycle

**Present findings.** Wait for approval before making changes.

## Full Cycle Triage (No Arguments)

When run without arguments, execute all operations in order:

1. **Triage** — fix metadata on grooming queue
2. **Label** — ensure all active issues have proper labels
3. **Estimate** — fill in missing estimates for current cycle
4. **Rename** — fix titles that don't follow convention
5. **Link PRs** — connect recent PRs to issues
6. **Cleanup** — flag stale/orphaned issues

Present each section's findings, get batch approval, then execute.

## Output Format

All operations present their proposed changes as tables for review:

```markdown
### Label Updates (12 issues)

| Issue | Current Labels | Proposed Labels | Action |
|-------|---------------|-----------------|--------|
| CORE-435 | _(none)_ | pkg:core, type:feature | Add |
| CORE-601 | pkg:i18n | pkg:i18n, type:bug | Add type:bug |
| ... | ... | ... | ... |

**Apply these changes?** (approve/modify/skip)
```

## Linear MCP Functions Used

- `mcp__linear__list_issues` — Fetch issues by team, state, cycle, project
- `mcp__linear__get_issue` — Get detailed issue information
- `mcp__linear__update_issue` — Update labels, estimate, title, cycle, state
- `mcp__linear__list_cycles` — Find current/next cycle
- `mcp__linear__list_issue_labels` — Verify available labels
- `mcp__linear__list_projects` — Check project associations

## Example Usage

```bash
# Full cycle triage (all operations)
/batch-update

# Just fix labels on active issues
/batch-update label

# Add estimates to current cycle issues
/batch-update estimate

# Link recent PRs to issues
/batch-update link-prs

# Prepare for next cycle
/batch-update cycle-prep

# Find stale/orphaned issues
/batch-update cleanup

# Triage the grooming queue
/batch-update triage

# Rename all non-conforming titles
/batch-update rename
```

## Key Principles

1. **Always present before applying** — Show proposed changes in a table and wait for approval (except low-risk link-prs)
2. **Batch for efficiency** — Group similar updates and apply in one pass
3. **Respect existing work** — Never overwrite labels/estimates that are already set unless explicitly asked
4. **Idempotent** — Running the same operation twice should produce no additional changes
5. **Document what changed** — After applying, summarize what was updated

## Tips

- Run `/batch-update` at the start of each cycle alongside `/cycle-retro` for the previous one
- Use `/batch-update triage` weekly to keep the grooming queue clean
- Use `/batch-update link-prs` after merging a batch of PRs
- Use `/batch-update cycle-prep` a day or two before the cycle ends
