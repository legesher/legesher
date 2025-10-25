<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- Explore → Plan → Code → Commit workflow (Phase 2: Plan)
- "Think harder" prompt engineering for deeper reasoning
-->

# Plan: $ARGUMENTS

**Goal**: Create a detailed, step-by-step implementation plan for: $ARGUMENTS

## Instructions

You are in PLANNING mode. Think deeply before proposing solutions.

**Use "think harder" or "ultrathink"** to engage deeper reasoning about:
- Trade-offs between different approaches
- Edge cases and failure modes
- Simplest solution that could work
- Long-term maintainability

## Steps

1. **Review Exploration Findings**
   - If you haven't run `/explore $ARGUMENTS` yet, do that first
   - Review the exploration summary
   - Confirm understanding of current state

2. **Define the Problem**
   - What exactly needs to be built/fixed?
   - What are the acceptance criteria?
   - What's in scope vs. out of scope?
   - What does success look like?

3. **Consider Multiple Approaches**
   - Brainstorm 2-3 different approaches
   - Analyze pros/cons of each
   - Consider: simplicity, maintainability, performance, security
   - Recommend the best approach with rationale

4. **Break Down into Tasks**
   - Decompose the work into small, atomic tasks
   - Each task should be: specific, testable, < 300 LOC
   - Order tasks by logical dependencies
   - Identify which tasks can be done in parallel

5. **Plan Testing Strategy**
   - What unit tests are needed?
   - What integration tests are needed?
   - What edge cases need explicit tests?
   - What's the test-driven development (TDD) approach?

6. **Identify Risks & Mitigations**
   - What could go wrong?
   - What are the high-risk changes?
   - What's the rollback plan?
   - What monitoring/logging is needed?

7. **Document the Plan**
   Create a scratchpad: `.claude/scratchpads/{ISSUE-ID}-implementation-plan.md`

   Include:
   - **Overview**: Summary of what's being built
   - **Context**: Links to issues, PRs, architecture docs
   - **Approach**: Chosen solution with rationale
   - **File Structure**: Files to create/modify
   - **Task Breakdown**: Numbered list of implementation tasks
   - **Testing Strategy**: Unit, integration, e2e tests
   - **Security Considerations**: Validation, sanitization, error handling
   - **Acceptance Criteria**: Checklist for completion
   - **Implementation Order**: Day-by-day or phase-by-phase
   - **Risks & Dependencies**: Known blockers, nice-to-haves

## Template for Scratchpad

Use this structure:

```markdown
# {ISSUE-ID} Implementation Plan: {Title}

**Issue**: [Link to issue]
**Status**: 🧼 Ready / 🏗️ In Progress / ✅ Complete
**Assignee**: {name}
**Created**: {date}

## Overview
{Brief description}

## Context & Prior Art
{Exploration findings, related work}

## Implementation Strategy
{Chosen approach and rationale}

### Design Principles
{Guiding principles for this work}

### Security Considerations
{Input validation, sanitization, error handling}

## File Structure
{Directory tree showing files to create/modify}

## Implementation Tasks
{Numbered list of tasks, grouped by phase}

## Testing Strategy
{Unit tests, integration tests, fixtures, coverage targets}

## Acceptance Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}

## Dependencies & Blockers
{What needs to happen first, what might block progress}

## Implementation Order
{Day-by-day or step-by-step sequence}

## Risk Assessment
{High/medium/low risks and mitigations}

## Success Metrics
{How to measure success}
```

## Deliverable

Present the plan to the user for feedback. Ask:
- Does this approach make sense?
- Are there concerns about the proposed solution?
- Should we proceed with implementation?

Remember: Good planning saves debugging time. 20% planning → 80% smoother implementation.