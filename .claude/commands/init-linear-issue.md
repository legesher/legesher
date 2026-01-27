---
description: Initialize work on a Linear issue with comprehensive planning and setup
---

# Initialize Linear Issue

You are helping initialize and plan work on a Linear issue for the Legesher project.

## Phase 1: Gather Context (REQUIRED - DO NOT SKIP)

1. **Fetch the Linear issue details** using Linear MCP tools

   **Available tools:**
   - `mcp__linear-server__get_issue` - Get detailed issue information
   - `mcp__linear-server__list_issues` - Search and filter issues
   - `mcp__linear-server__update_issue` - Update issue status, assignee, etc.
   - `mcp__linear-server__create_comment` - Add planning comments
   - `mcp__linear-server__list_comments` - View issue comments
   - Plus: teams, projects, cycles, labels, users, and more

   **Usage:** Use the issue identifier (e.g., "CORE-438" or full ID)

   **Get from issue:**
   - Full description and acceptance criteria
   - Current status, priority, and estimate
   - Dependencies (parent/blocking issues)
   - Labels, assignee, cycle, project
   - Attachments and git branch name
   - Related comments and context

2. **Locate issue in roadmap context** (Reference only - not source of truth)
   - The Linear issue is the source of truth for task details
   - Roadmap docs in private-working-memory are helpful for understanding context
   - Check [planning/architecture/implementation-roadmap.md](private-working-memory) to understand which phase/week
   - Use roadmap to understand dependencies and what comes before/after

3. **Review architectural context**
   - Check [planning/architecture/complete-architecture-guide.md]
     (private-working-memory) for relevant decisions
   - Review package tier system to understand dependencies
   - Identify affected packages (core, i18n, legesher, vs-code, home)

4. **Check constraints and requirements**
   - Security: Handles source code - critical security required
   - Privacy: Local-first approach, never require cloud
   - Performance: Real-time IDE translation needs speed
   - Git Compatibility: All workflows must work with git filters
   - Extensibility: Design for multiple languages, not just Python

## Phase 2: Analyze Scope (CRITICAL THINKING)

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
  - Use the Linear issue key (e.g., CORE-435, PRIDE-12)
  - Short description should be kebab-case
  - One branch per Linear issue
- Commit message format
- PR requirements

### Acceptance Criteria Checklist

- Map plan steps to acceptance criteria
- Ensure every criterion is addressed
- Note any ambiguities or questions

## Phase 4: Update Linear Issue

**After plan is approved by Madison:**

1. **Update issue status in Linear**

   Use `mcp__linear-server__update_issue` to update:
   - Status: Change to "In Progress" (or appropriate state)
   - Assignee: Set if not already assigned
   - Branch: Link the git branch name
   - Any other relevant fields

2. **Add planning comment to Linear**

   Use `mcp__linear-server__create_comment` to post the implementation plan.

   Include in comment:
   - Scope boundaries (In/Out of scope)
   - Link to created branch
   - Acceptance criteria checklist
   - Questions or blockers

   Format:

   ```markdown
   ## Implementation Plan

   **Branch:** `<ISSUE-KEY>-short-description`
   **Status:** In Progress

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

   ### Acceptance Criteria

   - [ ] [Criterion 1]
   - [ ] [Criterion 2]
         ...

   ### Questions/Blockers

   - [Any ambiguities or dependencies]

   **Next Steps:** Begin implementation following plan above.
   ```

3. **Create git branch**
   - Branch naming format: `<ISSUE-KEY>-<short-description>`
   - Example: `git checkout -b CORE-435-validate-transformer-migrated-packs`
   - Ensure branch is based on latest main/master
   - One branch per Linear issue for focused PRs

4. **Summarize for Madison**
   - Provide concise summary of plan
   - Highlight any concerns or questions
   - List any new tickets that should be created
   - Confirm ready to start implementation

## Phase 5: Implementation Readiness

Before starting implementation:

- [ ] Linear issue status updated to "In Progress"
- [ ] Planning comment posted to Linear
- [ ] Git branch created and checked out
- [ ] Scope boundaries clearly defined
- [ ] Dependencies identified
- [ ] Questions raised (if any)
- [ ] Plan approved by Madison

## Key Principles

1. **Stay in scope** - Only build what the ticket explicitly requires
2. **Think ahead** - Identify future work but don't implement it now
3. **Question assumptions** - If acceptance criteria are unclear, ask
4. **Consider roadmap** - Understand where this fits in the bigger picture
5. **Document thoroughly** - Leave a clear trail in Linear and git
6. **Test everything** - Write tests alongside implementation

## Example Usage

```bash
/init-linear-issue CORE-435
```

The assistant will:

1. Fetch CORE-435 from Linear
2. Analyze roadmap context (Phase 1, dependencies on CORE-354)
3. Create comprehensive plan with scope boundaries
4. Wait for approval
5. Update Linear status to "In Progress"
6. Post plan as comment in Linear
7. Create git branch: `CORE-435-validate-transformer-migrated-packs`
8. Begin implementation

---

**Remember:** This command prioritizes thoughtful planning over quick
implementation. Take time to understand context and scope boundaries.
