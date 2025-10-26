<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- Claude Code Common Workflows: https://docs.claude.com/en/docs/claude-code/common-workflows
- How Anthropic Teams Use Claude Code: https://www.anthropic.com/news/how-anthropic-teams-use-claude-code
- Explore → Plan → Code → Commit workflow pattern
-->

Please analyze and implement the GitHub issue: $ARGUMENTS

Follow the Explore → Plan → Code → Commit workflow:

# PHASE 1: EXPLORE (Read-only, no code changes yet)

**Goal**: Gather context and understand the problem deeply before jumping to solutions.

1. **Fetch Issue Details**
   - Use `gh issue view $ARGUMENTS` to get full issue context
   - Note: issue number, title, description, labels, milestone
   - Check for linked issues, PRs, or discussions

2. **Search Prior Art** (Use subagents to preserve context)
   - Search `.claude/scratchpads/` for related implementation plans
   - Use `gh pr list --search "related-keywords"` to find relevant PRs
   - Check git history: `git log --grep="keyword" --oneline -20`
   - Review Linear issues if using MCP: search for related work

3. **Explore Codebase** (Critical: DO NOT write code yet)
   - Use Glob/Grep to find relevant files and patterns
   - Read affected files to understand current implementation
   - Identify dependencies between packages (check `pyproject.toml`)
   - Note architectural patterns and conventions
   - Check for existing tests in the same area

4. **Security & Quality Checklist**
   - Does this issue touch sensitive code paths?
   - What are the security implications?
   - What edge cases need handling?
   - What could break from these changes?

5. **Ask Clarifying Questions**
   - If requirements are ambiguous, ask the user BEFORE planning
   - Clarify: architectural approach, scope, testing requirements
   - For open-source contributors: explain technical context clearly

# PHASE 2: PLAN (Think hard before coding)

**Goal**: Create a detailed, step-by-step implementation plan.

6. **Deep Thinking** (Use "think harder" or "ultrathink")
   - Break down the issue into small, atomic tasks
   - Consider: what's the simplest solution that could work?
   - Identify: which files need changes, new files needed
   - Plan: test strategy (unit → integration → e2e)
   - Estimate: complexity, risk level, time required

7. **Document Your Plan**
   - Create `.claude/scratchpads/{ISSUE-ID}-implementation-plan.md`
   - Include: issue link, context, file structure, task breakdown
   - Add: acceptance criteria, testing strategy, risks
   - Document: dependencies, blockers, nice-to-haves
   - Outline: implementation order (day-by-day if complex)

8. **Review Plan with User** (For complex issues)
   - Present the plan for feedback
   - Discuss trade-offs and alternative approaches
   - Get buy-in before proceeding to implementation

# PHASE 3: CODE (Small diffs, test-driven)

**Goal**: Implement in small, verifiable steps with tests.

9. **Create Feature Branch**

   ```bash
   git checkout -b feature/{ISSUE-ID}-brief-description
   ```

10. **Test-Driven Development** (Recommended for core functionality)
    - Write tests FIRST based on expected behavior
    - Run tests to confirm they FAIL (no false positives)
    - Implement minimal code to make tests pass
    - Refactor while keeping tests green
    - Commit tests separately: `git commit -m "test: add tests for {feature}"`

11. **Implement in Small Steps**
    - Follow your plan's task breakdown
    - Make ONE logical change at a time
    - Commit after each working step: `git commit -m "{type}: {description}"`
    - Commit types: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
    - Keep diffs small (< 300 lines per commit ideally)

12. **Handle Edge Cases**
    - Review your security & quality checklist from Phase 1
    - Add defensive checks, validation, error handling
    - Test failure modes and error messages
    - Consider: null values, empty inputs, large inputs, malformed data

13. **Update Documentation**
    - Update relevant README files
    - Add/update docstrings (follow project conventions)
    - Update CHANGELOG.md with user-facing changes
    - Add inline comments for complex logic

# PHASE 4: TEST (Verify everything works)

**Goal**: Ensure quality, catch regressions, verify edge cases.

14. **Run Test Suite**

    ```bash
    # For Python packages in this repo:
    cd libs/{package} && uv run pytest -v

    # With coverage:
    uv run pytest --cov=legesher_{package} --cov-report=term-missing
    ```

15. **Fix Failing Tests**
    - If tests fail, understand WHY before fixing
    - Don't modify tests to pass—fix the implementation
    - If test expectations are wrong, document why you're changing them

16. **Code Quality Checks**

    ```bash
    # Run linting (adjust based on project setup):
    uv run ruff check .
    uv run black --check .

    # Type checking:
    uv run mypy libs/{package}

    # Security scan (if applicable):
    uv run bandit -r libs/{package}
    ```

17. **Manual Testing** (If UI/CLI changes)
    - Test the happy path manually
    - Test error scenarios
    - Use Puppeteer via MCP for UI testing if applicable
    - Verify user experience matches expectations

18. **Performance Check** (If relevant)
    - Benchmark critical paths
    - Check for memory leaks
    - Verify performance requirements are met

# PHASE 5: COMMIT & DEPLOY

**Goal**: Clean git history, thorough PR, request review.

19. **Review Your Changes**

    ```bash
    git diff main...HEAD  # Review full diff
    git log main..HEAD --oneline  # Review commit history
    ```

20. **Clean Up Commits** (Optional but recommended)
    - If commits are messy, consider interactive rebase
    - Squash "fix typo" or "wip" commits
    - Keep logical commits separate for reviewability
    - NEVER rewrite history after pushing to shared branches

21. **Final Pre-PR Checklist**
    - [ ] All tests passing locally
    - [ ] Code formatted and linted
    - [ ] Documentation updated
    - [ ] CHANGELOG.md updated
    - [ ] No console.log / debug code left behind
    - [ ] No secrets or sensitive data committed
    - [ ] Commit messages are clear and descriptive

22. **Create Pull Request**

    ```bash
    # Push branch
    git push -u origin feature/{ISSUE-ID}-brief-description

    # Create PR with gh CLI
    gh pr create --fill
    ```

23. **Write Comprehensive PR Description**
    - Link to issue: "Closes #{ISSUE-ID}" or "Fixes #{ISSUE-ID}"
    - Summarize: What changed and why
    - Highlight: Key decisions, trade-offs, areas needing review
    - Include: Test plan, screenshots (if UI), performance notes
    - Tag: Relevant reviewers or maintainers
    - Use template:

      ```markdown
      ## Summary
      {Brief description of changes}

      ## Changes
      - {Bullet list of key changes}

      ## Test Plan
      - {How to test these changes}

      ## Checklist
      - [x] Tests added/updated
      - [x] Documentation updated
      - [x] CHANGELOG.md updated

      Closes #{ISSUE-ID}
      ```

24. **Request Review**
    - For solo founders: use `/review-pr` command (if available)
    - Tag specific reviewers if working with contributors
    - Be responsive to feedback
    - Explain reasoning for architectural decisions

# TIPS FOR SOLO FOUNDERS

- **Context is King**: Document your thinking in scratchpads—you'll thank yourself later
- **Think in Public**: Write clear commit messages and PR descriptions for future contributors
- **Test Everything**: You're the only QA—make tests your safety net
- **Plan More, Code Less**: 20% planning saves 80% debugging time
- **Use Subagents**: Offload research tasks early to preserve context budget
- **Clear Often**: Use `/clear` between distinct tasks to maintain focus
- **Queue Tasks**: List multiple todos upfront, Claude can work through them
- **Hooks for Consistency**: Automate formatting, linting with hooks (see `.claude/settings.json`)

# TIPS FOR OPEN SOURCE CONTRIBUTORS

When explaining context to contributors:

- Link to architectural docs (CLAUDE.md, FINAL_SUMMARY.md)
- Point to similar PRs as examples
- Explain "why" decisions were made, not just "what"
- Provide test examples
- Be explicit about code style and conventions
- Use Linear/GitHub issues with detailed acceptance criteria

When receiving contributions:

- Review with empathy—contributors are volunteering time
- Point to specific docs/examples instead of just saying "this is wrong"
- Ask questions to understand their approach
- Suggest improvements with rationale
- Thank contributors, even for imperfect PRs

# WORKFLOW VARIATIONS

**Bug Fix Workflow**: EXPLORE (reproduce) → PLAN (root cause) → CODE (minimal fix) → TEST (regression tests) → COMMIT

**Refactoring Workflow**: EXPLORE (understand current) → PLAN (desired state) → CODE (tests first!) → TEST (behavior unchanged) → COMMIT

**Feature Workflow**: EXPLORE (requirements) → PLAN (design) → CODE (TDD) → TEST (acceptance criteria) → COMMIT

**Documentation Only**: EXPLORE (what needs docs) → PLAN (outline) → CODE (write docs) → TEST (examples work) → COMMIT

---

Remember: The Explore and Plan phases are NOT optional. Skipping them leads to hasty solutions, missed edge cases, and technical debt. Take time to understand before you build.
