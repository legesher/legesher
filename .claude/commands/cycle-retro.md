<!--
SOURCES:
- Linear MCP integration
- Cycle retrospective best practices
- Learned constraints from Cycle 14 retro execution (2026-02-09)
-->
---
description: Generate a cycle retrospective document from completed Linear cycle data
---

# Cycle Retrospective: $ARGUMENTS

**Goal**: Generate a comprehensive retrospective document for a completed Linear cycle, capturing what was accomplished, what was learned, key decisions, and future work created during the cycle.

## Instructions

Generate a cycle retrospective by pulling all completed tickets from the specified cycle, analyzing the work done, and creating a Linear document summarizing the cycle.

## Steps

### 1. Identify the Cycle

**From arguments**:

- If `$ARGUMENTS` contains a cycle number (e.g., `14`), use that
- If `$ARGUMENTS` contains `previous`, fetch the most recently completed cycle
- If `$ARGUMENTS` is empty, default to the most recently completed cycle

**Fetch cycle data**:

Use `mcp__linear__list_teams` to get the team ID if not cached, then use `mcp__linear__list_cycles` with that team ID to find the target cycle.

### 2. Gather Cycle Issues

Cycles in Linear are team-scoped. Fetch issues from the **Core** team cycle (the primary team). If issues from other teams (Localization, Global) need to be included, query those teams separately by their cycle for the same date range.

> **Note**: Fetching all cycle issues **without a state filter** and categorizing by the returned status field is more reliable than filtering by state name, since state names vary across teams.

**Recommended approach**:

- Use `mcp__linear__list_issues` with `cycle` filter and **no state filter** to get all issues
- Categorize results by their status field: completed, cancelled, in-progress, etc.

**Completed issues** (the work we shipped):

- Filter results where status type is "completed" or "done"
- Also capture issues with status type "canceled" or "cancelled" for dropped work

**Incomplete issues** (carried over):

- Filter results where status type is not completed/done/cancelled
- These are issues that were in the cycle but didn't get finished

**For each completed issue, gather**:

- Title, description, and labels
- Priority and estimate
- Comments (use `mcp__linear__list_comments`) for context on decisions
- Project association
- Who it was assigned to

### 3. Gather New Issues Created During Cycle

Find tickets that were **created during the cycle period** but NOT part of the cycle:

- Use `mcp__linear__list_issues` with `createdAt` filter matching the cycle date range
- Exclude issues that were in the current cycle
- These represent future work and ideas that emerged during the cycle

### 4. Analyze and Categorize

Group the completed work into categories:

**By type**:

- Features (new functionality shipped)
- Bug fixes (issues resolved)
- Improvements (enhancements to existing features)
- Infrastructure (CI/CD, tooling, developer experience)
- Documentation (docs, READMEs, guides)

**By package**:

- Core, i18n, legesher, vs-code, language-server, home, docs
- Use labels (e.g., `package:core`) or issue identifiers (e.g., `CORE-*`)

**By impact**:

- User-facing changes (what users will notice)
- Developer-facing changes (what contributors will notice)
- Internal improvements (what improves our workflow)

### 5. Identify Key Themes

From the completed work and comments, extract:

- **Major decisions made** during the cycle (architectural choices, design decisions, trade-offs)
- **Lessons learned** (what worked well, what was harder than expected)
- **Takeaways for future cycles** (process improvements, patterns to follow or avoid)
- **Blockers encountered** and how they were resolved
- **Scope changes** (what was added or removed from the cycle mid-sprint)

### 6. Analyze Cycle Metrics

From the cycle history data:

- **Planned vs completed**: How many issues were planned vs actually completed
- **Scope changes**: Did scope grow or shrink during the cycle
- **Velocity**: Total estimate points completed
- **Completion rate**: Percentage of planned work finished

### 7. Catalog Future Work

For issues created during the cycle but not in it:

- **Group by theme** (what sparked the idea)
- **Note which completed ticket inspired them** (if traceable from comments/context)
- **Priority assessment** (urgent vs backlog)
- **Recommended cycle** for inclusion

### 8. Find the Cycle Retro Issue

Before creating the document, locate the recurring "Cycle Retrospective" issue for this cycle:

- Use `mcp__linear__list_issues` with `query: "Cycle Retrospective"` and `cycle` set to the target cycle
- This is the recurring CORE-598 ticket (or its future recurrences)
- Note its `id` — you'll link the document to it
- Also note its `project` — you'll file the document under the same project

**If a retro issue exists**:

- Note its `id` for cross-referencing in step 10
- Note its `project` — you'll file the document under the same project

**If no retro issue exists in the cycle**:

- Look at the completed issues and use the project that contains the majority of them
- If no clear project exists, create the document without a `project` link
- **Skip step 10** entirely (no retro issue to update)

### 9. Create the Retrospective Document

Use `mcp__linear__create_document` to create a Linear document.

**Important**: Linear only allows linking a document to EITHER a project OR an issue (not both).

**Preference**: Link to the **project** so retros are grouped together in the project's documents view.
When a retro issue exists, add a comment on it with the document link for cross-referencing.

- `project`: The project from step 8 (from retro issue when present, or inferred from cycle issues)

Example:

```python
mcp__linear__create_document(
    title="Cycle 14: User Feedback from Legesher Explorers — Retrospective",
    content=retro_markdown,
    project="<project-id-from-retro-issue>"
)
```

Use the following document structure:

```markdown
# Cycle [NUMBER]: [CYCLE TITLE] Retrospective

**Dates**: [start date] → [end date]
**Team**: Core

---

## Cycle Summary

[2-3 sentence high-level summary of what this cycle accomplished and its significance to the project]

## Metrics

| Metric | Value |
|--------|-------|
| Issues Planned | [count] |
| Issues Completed | [count] |
| Issues Carried Over | [count] |
| Issues Cancelled | [count] |
| Completion Rate | [percentage] |
| Scope Change | [+/- issues from start to end] |

---

## What We Shipped

### Features
- **[ISSUE-ID] [Title]** — [1-sentence description of what it does and why it matters]
  - *Impact*: [user-facing / developer-facing / internal]
  - *Package*: [affected package(s)]

### Bug Fixes
- **[ISSUE-ID] [Title]** — [what was broken and how it was fixed]

### Improvements
- **[ISSUE-ID] [Title]** — [what improved and why]

### Infrastructure & Tooling
- **[ISSUE-ID] [Title]** — [what changed in our tooling/process]

### Documentation
- **[ISSUE-ID] [Title]** — [what was documented]

---

## Key Decisions & Architectural Choices

- **[Decision]**: [Context for why this decision was made, what alternatives were considered]
- **[Decision]**: [Context]

## Lessons Learned

### What Went Well
- [Thing that worked and why]

### What Was Challenging
- [Challenge encountered and how it was addressed]

### Process Improvements
- [Suggestion for future cycles]

---

## Carried Over (Incomplete)

| Issue | Title | Reason | Recommendation |
|-------|-------|--------|----------------|
| [ID] | [Title] | [Why it wasn't completed] | [Move to next cycle / backlog / cancel] |

---

## Future Work Created This Cycle

Issues that were created during this cycle from ideas and discoveries in our work:

### High Priority
- **[ISSUE-ID] [Title]** — [Why it was created, which ticket inspired it]

### Normal Priority
- **[ISSUE-ID] [Title]** — [Why it was created]

### Backlog
- **[ISSUE-ID] [Title]** — [Why it was created]

---

## Looking Ahead

[1-2 paragraphs on what the next cycle should focus on based on what we learned, what carried over, and what new work was identified]

---

*Generated on [date] with Claude Code `/cycle-retro` command*
```

### 10. Update the Retro Issue (skip if no retro issue found in step 8)

After the document is created:

- Add a comment to the cycle retro issue linking to the new document
- Update the retro issue description to mark the "Run `/cycle-retro`" checklist item as complete (replace `- [ ]` with `- [x]` for that item using `mcp__linear__update_issue` with the updated description)
- Move the retro issue to "In Progress" if not already

### 11. Post Project Update

Use `mcp__linear__create_project_update` to post a summary to the project:

- `project`: Same project the document was filed under
- `health`: Assess based on cycle results (`onTrack`, `atRisk`, or `offTrack`)
- `body`: A concise update including:
  - Link to the retrospective document
  - Cycle highlights (top 5-7 bullet points: completion stats, major features, key fixes)
  - Key decisions made during the cycle
  - Looking ahead section (what's next based on learnings and carried-over work)

This ensures the retrospective is surfaced in the project's update feed, not just buried in documents.

### 12. Present to User

After creating the document, present:

- Link to the created Linear document
- Quick stats (completed/planned/carried over)
- Top 3 highlights from the cycle
- Any action items or concerns for the next cycle

## Example Usage

```bash
# Retrospective for most recently completed cycle
/cycle-retro

# Retrospective for a specific cycle number
/cycle-retro 14

# Retrospective for the previous cycle explicitly
/cycle-retro previous

# Preview mode — gather and present data without creating Linear artifacts
/cycle-retro 14 --dry-run
```

### Dry Run Mode

If `$ARGUMENTS` contains `--dry-run`:

- Execute steps 1-7 (data gathering and analysis) as normal
- **Skip steps 8-11** (no document creation, no issue updates, no project update)
- In step 12, present the full retrospective content as markdown in the chat
- This allows reviewing the retro before committing it to Linear

## Key Principles

1. **Be comprehensive but concise** — Capture everything important without being verbose
2. **Focus on the "so what"** — Don't just list tickets, explain their impact and significance
3. **Extract decisions** — Major decisions made during a cycle are easy to forget; document them
4. **Connect the dots** — Show how completed work relates to future work that was created
5. **Be honest** — If things didn't go well, document that too; retrospectives are for learning
6. **Make it actionable** — End with clear recommendations for the next cycle

## Linear MCP Functions Used

- `mcp__linear__list_cycles` — Get cycle data and metrics
- `mcp__linear__list_issues` — Fetch issues by cycle, state, and creation date
- `mcp__linear__get_issue` — Get detailed issue information
- `mcp__linear__list_comments` — Get comments for context and decisions
- `mcp__linear__create_document` — Create the retrospective document (linked to project)
- `mcp__linear__create_project_update` — Post cycle summary to the project update feed
- `mcp__linear__create_comment` — Post document link to the retro issue
- `mcp__linear__update_issue` — Update retro issue status
- `mcp__linear__list_teams` — Get team IDs for cycle queries

## Known Limitations

These were discovered during the Cycle 14 retrospective execution:

- **Document linking is exclusive**: `mcp__linear__create_document` accepts EITHER `project` OR `issue`, not both. We default to project and cross-reference via a comment on the issue.
- **State filter unreliable**: `mcp__linear__list_issues` with `state: "done"` or `state: "completed"` may return empty results depending on the team's custom state names. Always fetch without a state filter and categorize from the response.
- **Checklist updates require description rewrite**: Linear MCP has no dedicated checklist API. To mark a checklist item complete, you must read the full issue description, update the `- [ ]` to `- [x]`, and write it back via `mcp__linear__update_issue`.
- **Cycle lookup needs team UUID**: `mcp__linear__list_cycles` requires a team ID (UUID), not a team name. Use `mcp__linear__list_teams` first to resolve the name.

## Tips

- Run this at the end of each cycle or beginning of the next one
- The retrospective document lives in Linear for easy reference alongside the issues
- Use these documents to track project evolution over time
- Share retrospectives with contributors to keep everyone aligned
- Reference past retrospectives when planning future cycles
