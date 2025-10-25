<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- Explore → Plan → Code → Commit workflow (Phase 1: Explore)
-->

# Explore: $ARGUMENTS

**Goal**: Gather deep context about "$ARGUMENTS" without writing any code yet.

## Instructions

You are in EXPLORE mode. This is a READ-ONLY phase.

**IMPORTANT**: Do NOT write, edit, or create any code files. Your job is to understand, not to implement.

## Steps

1. **Search the Codebase**
   - Use Glob to find files related to: $ARGUMENTS
   - Use Grep to search for relevant keywords, functions, classes
   - Read relevant files to understand current implementation
   - Note: file paths, key functions, architectural patterns

2. **Review Documentation**
   - Check CLAUDE.md for architectural guidance
   - Look in `docs/src/content/docs/` for relevant guides
   - Review package READMEs in `libs/*/README.md`
   - Check for related scratchpads in `.claude/scratchpads/`

3. **Search Prior Work**
   - Use `gh pr list --search "$ARGUMENTS"` to find related PRs
   - Use `git log --grep="$ARGUMENTS" --oneline -20` for commit history
   - Check Linear/GitHub issues for context (use MCP if available)

4. **Identify Dependencies**
   - Which packages are affected? (core, i18n, legesher, vs-code, pride)
   - What dependencies exist between components?
   - Check `pyproject.toml` files for package dependencies
   - Are there external dependencies needed?

5. **Security & Quality Review**
   - Does this touch sensitive code paths?
   - What are potential security implications?
   - What edge cases need consideration?
   - What could break from changes in this area?

6. **Map the Architecture**
   - What's the current architecture around: $ARGUMENTS?
   - What patterns are used (inheritance, composition, etc.)?
   - How do components interact?
   - What are the extension points?

## Deliverable

Provide a comprehensive summary including:

- **Current State**: What exists today around $ARGUMENTS
- **File Locations**: Key files and their purposes
- **Architectural Patterns**: How it's structured
- **Dependencies**: What depends on what
- **Gaps & Opportunities**: What's missing, what could be improved
- **Security Considerations**: What to watch out for
- **Recommendations**: Next steps for planning phase

Remember: This is research only. Present your findings clearly so we can make informed decisions in the planning phase.