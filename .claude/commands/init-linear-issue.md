---
description: Initialize work on a Linear issue with comprehensive planning and setup
---

# Initialize Linear Issue

You are helping initialize and plan work on a Linear issue for the Legesher project.

**Arguments**: `$ARGUMENTS`

## Quick Mode Detection

If `$ARGUMENTS` contains `--quick` (e.g., `/init-linear-issue CORE-435 --quick`):
- **Skip Phases 2 and 3** (scope analysis and planning)
- Execute Phase 1 (gather context) and Phase 4 (update Linear + create branch) immediately
- Use the existing issue description as the implementation plan
- Post a brief "Starting work" comment instead of a full plan
- This is for issues that already have a clear plan or are being resumed

## Phase 1: Gather Context (REQUIRED - DO NOT SKIP)

1. **Fetch the Linear issue details** using Linear MCP tools

   **Available tools:**
   - `mcp__linear__get_issue` - Get detailed issue information (use `includeRelations: true`)
   - `mcp__linear__list_issues` - Search and filter issues
   - `mcp__linear__update_issue` - Update issue status, assignee, etc.
   - `mcp__linear__create_comment` - Add planning comments
   - `mcp__linear__list_comments` - View issue comments and prior discussion
   - `mcp__linear__list_cycles` - Get current cycle for assignment
   - Plus: teams, projects, labels, users, and more

   **Usage:** Use the issue identifier (e.g., "CORE-438" or full ID)

   **Get from issue:**
   - Full description and acceptance criteria
   - Current status, priority, and estimate
   - Dependencies (parent/blocking issues via `includeRelations`)
   - Labels, assignee, cycle, project
   - Attachments and git branch name
   - Related comments and context — **read ALL comments** for prior discussion, decisions, and implementation details

2. **Locate issue in roadmap context** (Reference only - not source of truth)
   - The Linear issue is the source of truth for task details
   - Check CLAUDE.md for architectural context and package tier system
   - Use roadmap to understand dependencies and what comes before/after

3. **Review architectural context**
   - Check CLAUDE.md for relevant architectural decisions
   - Review package tier system to understand dependencies
   - Identify affected packages (core, i18n, legesher/cli, language-server, vs-code, api, home, docs, preview)

4. **Check constraints and requirements**
   - Security: Handles source code - critical security required
   - Privacy: Local-first approach, never require cloud
   - Performance: Real-time IDE translation needs speed
   - Git Compatibility: All workflows must work with git filters
   - Extensibility: Design for multiple languages, not just Python

## Phase 2: Analyze Scope (CRITICAL THINKING)

> **Skip this phase in `--quick` mode.**

### Think critically about scope boundaries

For the given Linear issue:

- **ONLY build what is explicitly included in the ticket**
- Identify dependencies that must exist beforehand
- Note features that should come AFTER this task
- Flag any scope creep or feature bloat

**Create lists for:**

### Prerequisites (Must exist before starting)

- List any issues that MUST be completed first
- Note missing infrastructure or dependencies
- Identify if ticket is blocked

### In Scope (This ticket)

- Only features explicitly mentioned in the issue
- Core functionality required to meet acceptance criteria
- Minimum tests to validate the feature works

### Out of Scope (Future tickets)

- Features that would be "nice to have" but aren't required
- Optimizations that can come later
- Extended functionality beyond the core requirement
- Any work that isn't explicitly in the acceptance criteria

**If you identify prerequisites or future work, prepare ticket summaries for
Madison to create.**

## Phase 3: Create Comprehensive Plan

> **Skip this phase in `--quick` mode.**

Develop a detailed step-by-step implementation plan including:

### Package Impact Analysis

- Which packages are affected (with tier information)
- What files will be created/modified
- Cross-package dependencies
- Build order considerations

### Implementation Steps

Break down into clear, sequential steps:

1. Infrastructure setup (if needed)
2. Core implementation
3. Tests (write alongside implementation)
4. Integration
5. Documentation

### Testing Strategy

- Unit tests required
- Integration tests required
- Edge cases to cover
- Performance benchmarks (if applicable)

### Documentation Updates

- Package README updates
- API documentation
- Usage examples
- Migration guides (if breaking changes)

### Git Workflow

- Branch naming: `<ISSUE-KEY>-<short-description>`
  - Example: `CORE-435-validate-transformer-migrated-packs`
  - Use the Linear issue key (e.g., CORE-435)
  - Short description should be kebab-case
  - One branch per Linear issue
- Commit message format (see `/commit` command)
- PR requirements

### Acceptance Criteria Checklist

- Map plan steps to acceptance criteria
- Ensure every criterion is addressed
- Note any ambiguities or questions

### Point Estimate

Based on the implementation plan, recommend a Fibonacci estimate:

| Points | Meaning |
|--------|---------|
| 1 | Trivial — config change, typo fix, one-liner |
| 2 | Small — single file, straightforward logic |
| 3 | Medium — a few files, some complexity |
| 5 | Large — multiple files, cross-package, needs design |
| 8 | Very large — significant feature, multiple packages |
| 13 | Epic-sized — consider breaking into sub-issues |

## Phase 4: Update Linear Issue (REQUIRED)

**After plan is approved by Madison (or immediately in `--quick` mode):**

### 4a. Fill out ALL issue metadata

Use `mcp__linear__update_issue` to set **every** field:

**IMPORTANT: The `labels` parameter REPLACES all existing labels.** You must read the issue's current labels first and merge them with new ones to avoid losing existing labels.

```python
# Step 1: Read existing labels so we don't overwrite them
issue = mcp__linear__get_issue(id=issue_id)
existing_labels = issue["labels"]  # e.g., ["needs:grooming"]

# Step 2: Merge existing + new labels (deduplicated)
new_labels = list(set(existing_labels + ["pkg:xxx", "area:yyy", "type:zzz"]))
# Remove any labels that should be replaced (e.g., remove "needs:grooming" now that work is starting)
new_labels = [l for l in new_labels if l != "needs:grooming"]

# Step 3: Update issue with merged labels
mcp__linear__update_issue(
    id=issue_id,
    state="In Progress",
    assignee="me",
    cycle=current_cycle,         # Use mcp__linear__list_cycles to find current cycle
    estimate=fibonacci_estimate, # From Phase 3 analysis (or ask Madison in --quick mode if missing)
    labels=new_labels,           # Merged labels — never overwrite blindly
)
```

**Required metadata checklist:**

- [ ] **Status**: → `In Progress`
- [ ] **Assignee**: → Madison (use `"me"`)
- [ ] **Cycle**: → Current active cycle (fetch via `mcp__linear__list_cycles`)
- [ ] **Estimate**: → Fibonacci points from plan analysis
- [ ] **Labels**: → At least one `pkg:*` label + relevant `area:*` and `type:*` labels
- [ ] **Project**: → Verify issue is in the correct project (if applicable)

### 4b. Rename issue title to follow convention

Issue titles should follow the format: `[package:subcategory] Title`

- Examples: `[vs-code:telemetry] Fix event tracking`, `[i18n:packs] Add dunder translations`
- Use the `pkg:*` label as the package prefix
- Subcategory should describe the area of work (e.g., bug, feature, release, epic)

### 4c. Post implementation plan as comment

**This is critical — the plan MUST be documented on the issue.**

Use `mcp__linear__create_comment` to post the full implementation plan.

**Full mode** — post the complete plan:

```markdown
## Implementation Plan

**Branch:** `<ISSUE-KEY>-short-description`
**Estimate:** X points
**Status:** In Progress
**Assigned:** Madison

### Scope

**In Scope:**

- [List items explicitly in this ticket]

**Out of Scope (Future Tickets):**

- [List items for future work]

### Prerequisites

- [List any blocking issues]

### Implementation Steps

1. [Detailed step]
2. [Detailed step]
   ...

### Testing Plan

- [Test categories and coverage]

### Key Decisions & Context

- [Any decisions made during planning discussion]
- [Implementation details from conversation]
- [Trade-offs considered and rationale]

### Acceptance Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
      ...

### Questions/Blockers

- [Any ambiguities or dependencies]

**Next Steps:** Begin implementation following plan above.
```

**Quick mode** — post a brief start comment:

```markdown
## Work Started

**Branch:** `<ISSUE-KEY>-short-description`
**Status:** In Progress

Resuming work on this issue. Implementation details are in the issue description.
```

### 4d. Document discussion context

**Important:** If there were any implementation details, design decisions, questions, or helpful context discussed during this conversation, **add them as a comment on the Linear issue**. This ensures:

- Decisions are preserved even if the chat session is lost
- Future contributors can understand the reasoning
- The Linear issue is the single source of truth

### 4e. Create git branch

```bash
git checkout -b <ISSUE-KEY>-<short-description>
# Example: git checkout -b CORE-435-validate-transformer-migrated-packs
```

- Ensure branch is based on latest main
- One branch per Linear issue for focused PRs

### 4f. Summarize for Madison

- Provide concise summary of plan
- Highlight any concerns or questions
- List any new tickets that should be created
- Confirm ready to start implementation

## Phase 5: Implementation Readiness

Before starting implementation, verify ALL of these:

- [ ] Linear issue status set to "In Progress"
- [ ] Assignee set to Madison
- [ ] Added to current cycle
- [ ] Point estimate assigned
- [ ] Labels applied (`pkg:*`, `area:*`, `type:*`)
- [ ] Issue title follows `[package:subcategory] Title` convention
- [ ] Implementation plan posted as comment on Linear issue
- [ ] Discussion context documented on the issue
- [ ] Git branch created and checked out
- [ ] Scope boundaries clearly defined
- [ ] Dependencies identified
- [ ] Questions raised (if any)
- [ ] Plan approved by Madison

## Key Principles

1. **Stay in scope** - Only build what the ticket explicitly requires
2. **Think ahead** - Identify future work but don't implement it now
3. **Question assumptions** - If acceptance criteria are unclear, ask
4. **Document everything** - Leave a clear trail in Linear (plan, decisions, context)
5. **Fill out metadata** - Every issue should have estimate, labels, assignee, cycle
6. **Test everything** - Write tests alongside implementation

## Example Usage

### Full planning mode (new feature, needs design)

```bash
/init-linear-issue CORE-435
```

The assistant will:

1. Fetch CORE-435 from Linear (with all comments and relations)
2. Analyze scope boundaries and dependencies
3. Create comprehensive plan with estimate
4. Wait for Madison's approval
5. Set all metadata: status, assignee, cycle, estimate, labels
6. Rename title to `[package:subcategory]` convention
7. Post full implementation plan as comment on CORE-435
8. Create git branch: `CORE-435-validate-transformer-migrated-packs`
9. Begin implementation

### Quick mode (clear task, just start working)

```bash
/init-linear-issue CORE-435 --quick
```

The assistant will:

1. Fetch CORE-435 from Linear
2. Set all metadata: status → In Progress, assignee → me, cycle → current, labels
3. Rename title if needed
4. Post brief "Work Started" comment
5. Create git branch
6. Begin implementation immediately

---

**Remember:** This command prioritizes thoughtful planning over quick
implementation. Use `--quick` only when the issue already has a clear plan.
The Linear issue must always be the single source of truth — document
everything there.
