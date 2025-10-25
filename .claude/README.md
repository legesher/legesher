# Claude Code Configuration for Legesher

This directory contains Claude Code configuration, commands, agents, and workflows optimized for the Legesher project.

## 📚 Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Commands](#commands)
- [Agents](#agents)
- [Hooks](#hooks)
- [Workflows](#workflows)
- [Best Practices](#best-practices)
- [Resources](#resources)

## Overview

This configuration is built on **Anthropic's best practices** for Claude-assisted development, specifically designed for:
- **Solo founders** managing complex projects
- **Open source contributors** at various skill levels
- **Mentorship-focused development** (learning as you build)

### Key Philosophy

- **Explore → Plan → Code → Commit**: Structured workflow prevents hasty solutions
- **Test-Driven Development**: Write tests first, implement second
- **Context is King**: Document thinking for future you and contributors
- **Teaching by Default**: Explain WHY, not just WHAT

## Directory Structure

```text
.claude/
├── README.md                    # This file
├── settings.json                # Project-wide hook configurations
├── settings.local.json          # Personal settings (not committed)
├── hooks-examples.md            # Comprehensive hook examples
├── commands/                    # Slash commands
│   ├── issue.md                 # Complete issue workflow (Explore→Plan→Code→Commit)
│   ├── explore.md               # Phase 1: Deep codebase exploration
│   ├── plan.md                  # Phase 2: Detailed implementation planning
│   ├── tdd.md                   # Test-driven development workflow
│   ├── review.md                # Code review checklist and feedback
│   ├── commit.md                # Create well-structured commits
│   ├── linear-commit.md         # Linear-integrated commits (NEW)
│   ├── changelog.md             # Update CHANGELOG.md (NEW)
│   ├── pr.md                    # Create comprehensive pull requests
│   ├── teach.md                 # Mentorship mode (expert → apprentice)
│   └── context.md               # Provide comprehensive context docs
├── agents/                      # Specialized subagents
│   ├── codebase-explorer.md     # Deep codebase exploration
│   ├── test-engineer.md         # Comprehensive test writing
│   ├── doc-writer.md            # Documentation specialist
│   └── security-reviewer.md     # Security vulnerability analysis
├── org-templates/               # Organization-wide templates (NEW)
│   ├── README.md                # Template usage guide
│   └── settings.json.template   # Standard hooks configuration
├── scratchpads/                 # Implementation plans and notes
│   └── *.md                     # Issue-specific planning documents
└── todo.md                      # Task tracking
```

## Commands

Commands are invoked with `/command-name` in Claude Code.

### Primary Workflow Commands

#### `/issue {issue-number}`

**Complete issue workflow** following Anthropic's Explore → Plan → Code → Commit pattern.

**Phases**:
1. **Explore**: Understand problem, search prior art, map codebase (read-only)
2. **Plan**: Think deeply, create implementation plan, document in scratchpad
3. **Code**: Test-driven development, small commits, handle edge cases
4. **Test**: Run tests, quality checks, manual testing
5. **Commit & Deploy**: Clean history, comprehensive PR, request review

**When to use**: Starting work on any GitHub issue

**Features**:
- Prevents jumping straight to coding
- Emphasizes planning and exploration
- Includes tips for solo founders and open source contributors
- References Anthropic best practices

### Phase-Specific Commands

#### `/explore {topic}`

**Deep codebase exploration** without making changes.

**What it does**:
- Searches files and code patterns
- Maps dependencies and architecture
- Identifies conventions and standards
- Documents current state

**When to use**:
- Understanding unfamiliar code
- Planning major refactors
- Onboarding to new area

**Output**: Comprehensive exploration report with recommendations

#### `/plan {feature}`

**Create detailed implementation plan** with deep thinking.

**What it does**:
- Uses "think harder" for deeper reasoning
- Considers multiple approaches with trade-offs
- Breaks work into atomic tasks
- Documents in scratchpad

**When to use**:
- Before implementing features
- Complex refactoring
- Architectural decisions

**Output**: Scratchpad document in `.claude/scratchpads/`

#### `/tdd {feature}`

**Test-driven development workflow**.

**Phases**:
1. Write tests FIRST (describe expected behavior)
2. Run tests, confirm they FAIL
3. Implement minimal code to pass
4. Refactor with safety net of tests

**When to use**:
- New features with clear input/output
- Bug fixes (test reproduces bug first)
- Complex business logic

**Why TDD**: Tests as safety net, documentation, and design tool

### Quality & Review Commands

#### `/review {pr-number or code}`

**Comprehensive code review** following security and quality best practices.

**Checks**:
- Code quality (readability, structure, types)
- Security (input validation, injection prevention)
- Testing (coverage, quality)
- Performance
- Documentation
- Dependencies

**When to use**:
- Before merging PRs
- Self-review before requesting review
- Learning code quality standards

**Output**: Structured feedback (Critical/Medium/Low issues)

#### `/commit {description}`

**Create well-structured git commits** following Conventional Commits.

**What it does**:
- Guides commit message format
- Reviews staged changes
- Ensures atomic commits
- Follows project conventions

**Format**: `<type>(<scope>): <subject>`

**Types**: feat, fix, refactor, test, docs, style, perf, chore

#### `/linear-commit {issue-id}`

**Create git commit with Linear integration** - automatically links commit to Linear issue and updates issue status.

**What it does**:
- Fetches Linear issue details via MCP
- Generates commit message with Linear reference
- Creates commit with proper formatting
- Adds commit comment to Linear issue
- Suggests Linear issue state updates

**When to use**: When working on Linear issues (auto-detects from branch name)

**Branch naming**: `feature/leg-123-brief-description` enables auto-detection

#### `/changelog {version}`

**Update CHANGELOG.md** following Keep a Changelog format.

**What it does**:
- Analyzes commits since last release
- Categorizes by type (Added, Changed, Fixed, etc.)
- Generates user-focused descriptions
- Includes PR/issue references
- Suggests version bumps

**When to use**: Before releases, or continuously as features are completed

### Documentation Commands

#### `/pr {description}`

**Create comprehensive pull request** that's easy to review.

**Includes**:
- Clear summary and motivation
- Test plan and screenshots
- Security considerations
- Checklist for completeness

**When to use**: Ready to create PR after implementation

#### `/teach {concept}`

**Mentorship mode**: Explain as expert to entry-level developer.

**Teaching approach**:
- Explains WHY, not just WHAT
- Shares thought process and trade-offs
- Checks for understanding
- Relates to real-world scenarios
- Builds mental models

**When to use**:
- Learning new concepts
- Understanding architectural decisions
- Preparing to hand off code
- Teaching contributors

**Perfect for**: Solo founders who need to understand deeply OR explain to future contributors

#### `/context {topic}`

**Provide comprehensive context** for contributors or future you.

**What it includes**:
- Problem statement and motivation
- Architecture and key concepts
- Design decisions with rationale
- Code organization
- Testing strategy
- Learning resources

**When to use**:
- Onboarding contributors
- Documenting architectural decisions
- Creating project knowledge base

## Agents

Agents are specialized subagents that focus on specific tasks. Invoke with the Task tool or they may be automatically called.

### Available Agents

#### `codebase-explorer`

**Specialized in**: Deep codebase exploration and architecture mapping

**Tools**: Read, Glob, Grep, Bash (read-only)

**Use for**:
- Understanding unfamiliar code areas
- Mapping dependencies
- Finding patterns and conventions
- Prior art research

**Preserves context**: Uses separate context window, doesn't pollute main conversation

#### `test-engineer`

**Specialized in**: Writing comprehensive tests with TDD methodology

**Tools**: Read, Edit, Write, Bash, Grep, Glob

**Use for**:
- Test-driven development
- Achieving coverage targets (90%+)
- Integration tests
- Performance benchmarks

**Expertise**: Pytest, fixtures, parametrize, mocking, coverage analysis

#### `doc-writer`

**Specialized in**: Creating clear, comprehensive documentation

**Tools**: Read, Write, Edit, Glob, Grep

**Use for**:
- README files
- API documentation (docstrings)
- Tutorials and how-to guides
- Architecture Decision Records (ADRs)

**Follows**: Divio documentation system (tutorial, how-to, explanation, reference)

#### `security-reviewer`

**Specialized in**: Security vulnerability analysis and prevention

**Tools**: Read, Grep, Glob, Bash

**Use for**:
- Security reviews before merge
- Input validation checks
- Injection attack prevention
- Dependency vulnerability scanning

**Checks**: OWASP Top 10, Python security best practices, secure patterns

## Hooks

Hooks automate common tasks. Configure in `settings.json` (project-wide) or `settings.local.json` (personal).

### Active Hooks (settings.json)

#### PostToolUse: Auto-format Python

Automatically runs Black and Ruff after editing Python files.

```bash
black file.py && ruff check --fix file.py
```

#### PostToolUse: Auto-format Markdown

Automatically runs Prettier on Markdown files.

```bash
prettier --write file.md
```

#### PreToolUse: Log Bash Commands

Logs all bash commands with timestamps to `~/.claude/bash_history.log`.

### More Examples

See [hooks-examples.md](hooks-examples.md) for comprehensive examples:
- Run tests automatically
- Prevent production changes
- Backup files before editing
- Notify on critical file changes
- Check code coverage
- GitButler integration

## Workflows

### Workflow 1: Implementing a New Feature

```bash
# 1. Start with exploration
/explore "language pack loading system"

# 2. Plan the implementation
/plan "version-aware language pack system"

# 3. Use TDD if appropriate
/tdd "language pack loader with inheritance"

# 4. Create commits as you go
/commit "implement pack loader with caching"

# 5. Review your work
/review "pack_loader.py changes"

# 6. Create PR
/pr "Add version-aware language pack system"
```

### Workflow 2: Fixing a Bug

```bash
# 1. Explore to understand the bug
/explore "version detection failing for .python-version"

# 2. Plan the fix
/plan "fix version detector fallback chain"

# 3. TDD: Write test that reproduces bug
/tdd "version detector with missing pyproject.toml"

# 4. Implement fix (tests guide implementation)

# 5. Commit with reference to issue
/commit "fix: version detector fallback chain (fixes #123)"

# 6. Create PR
/pr "Fix version detection fallback"
```

### Workflow 3: Learning a New Area

```bash
# 1. Use teach mode for deep understanding
/teach "how AST transformers work in legesher-core"

# 2. Explore the code
/explore "AST transformer implementation"

# 3. Ask follow-up questions in teach mode
/teach "why token-based instead of tree-based transformation?"

# 4. Document your learning
/context "AST transformation architecture"
```

### Workflow 4: Onboarding a Contributor

```bash
# 1. Provide comprehensive context
/context "language pack system for contributors"

# 2. Show them the workflow
/teach "how to create a new language pack"

# 3. Guide them through their first contribution
/explore "existing language packs to use as templates"

# 4. Review their work with feedback
/review "contributor's first language pack PR"
```

## Best Practices

### For Solo Founders

1. **Document Your Thinking**: Use scratchpads liberally—future you will thank you
2. **Use /teach Mode**: Understand deeply enough to explain to others
3. **Plan More, Code Less**: 20% planning saves 80% debugging
4. **Test Everything**: You're the only QA—make tests your safety net
5. **Clear Often**: Use `/clear` between distinct tasks to maintain focus
6. **Queue Tasks**: List multiple tasks upfront, Claude can work through them

### For Open Source Projects

1. **Provide Context**: Use `/context` to help contributors understand
2. **Thorough Reviews**: Use `/review` for consistent quality feedback
3. **Teach, Don't Just Fix**: Use `/teach` mode in discussions
4. **Document Decisions**: Use ADRs (part of `/context`) for architectural choices
5. **Comprehensive PRs**: Use `/pr` to create reviewable pull requests

### General Best Practices

1. **Explore Before Planning**: Don't skip the exploration phase
2. **Plan Before Coding**: Don't skip the planning phase
3. **Test First (TDD)**: Tests guide design and catch regressions
4. **Small Commits**: Atomic, logical changes are easier to review/revert
5. **Clear Messages**: Commit messages are permanent—make them count
6. **Review Everything**: Even your own code—catch issues early
7. **Use Subagents**: Offload research early to preserve context

## Sources and Research

This configuration is built on research from:

### Primary Sources

- **Anthropic Claude Code Best Practices**: https://www.anthropic.com/engineering/claude-code-best-practices
- **Claude Code Common Workflows**: https://docs.claude.com/en/docs/claude-code/common-workflows
- **How Anthropic Teams Use Claude Code**: https://www.anthropic.com/news/how-anthropic-teams-use-claude-code
- **Claude Code Hooks Guide**: https://docs.claude.com/en/docs/claude-code/hooks-guide
- **Claude Code Subagents**: https://docs.claude.com/en/docs/claude-code/sub-agents

### Key Patterns

- **Explore → Plan → Code → Commit**: Structured workflow from Anthropic
- **Test-Driven Development**: Anthropic-favorite workflow
- **Think Harder Prompting**: "think" < "think hard" < "think harder" < "ultrathink"
- **Subagents for Context**: Offload research early to preserve tokens
- **Plan Mode**: Read-only exploration before implementation

### Community Resources

- **awesome-claude-code**: https://github.com/hesreallyhim/awesome-claude-code
- **awesome-claude-code-subagents**: https://github.com/VoltAgent/awesome-claude-code-subagents
- **Builder.io's Claude Code Guide**: https://www.builder.io/blog/claude-code
- **eesel AI Best Practices**: https://www.eesel.ai/blog/claude-code-best-practices

## Customization

### Adding New Commands

1. Create `.claude/commands/your-command.md`
2. Use `$ARGUMENTS` placeholder for command arguments
3. Write in natural language (instructions for Claude)
4. Include source references in HTML comments

Example:
```markdown
<!--
SOURCES:
- Your source URL here
-->

# Your Command: $ARGUMENTS

Goal: What this command accomplishes

## Instructions

Step-by-step instructions for Claude...
```

### Adding New Agents

1. Create `.claude/agents/your-agent.md`
2. Include frontmatter with name, description, tools
3. Define agent's mission and constraints
4. Provide process/checklist

Example:
```markdown
---
name: your-agent
description: What this agent specializes in
tools: [Read, Write, Bash]
---

You are a **Your Agent Name** - specialized in...

## Your Mission
...
```

### Adding New Hooks

1. Edit `.claude/settings.json` (project-wide) or `.claude/settings.local.json` (personal)
2. Add to appropriate hook point (PreToolUse, PostToolUse, Stop)
3. Test manually before adding
4. Keep hooks fast and failure-tolerant

See [hooks-examples.md](hooks-examples.md) for patterns.

## Troubleshooting

### Commands Not Showing Up

- Restart Claude Code
- Check file is in `.claude/commands/` directory
- Verify `.md` extension
- Check for syntax errors in markdown

### Agents Not Working

- Check frontmatter format (YAML between `---`)
- Verify agent name doesn't conflict with built-ins
- Check tool names are correct
- Restart Claude Code

### Hooks Not Running

- Verify JSON syntax (use JSONLint)
- Check matcher matches tool name exactly
- Test command manually
- Check Claude Code logs

### Commands Timing Out

- Use subagents for research tasks
- Break large tasks into smaller chunks
- Use `/clear` to reset context
- Simplify command instructions

## Contributing

### Improving Commands

1. Test command thoroughly
2. Add source references for best practices
3. Include examples
4. Consider different user skill levels
5. Submit PR with rationale

### Sharing Agents

1. Document agent's specialty clearly
2. Provide example use cases
3. Specify tools needed
4. Include output format expectations

### Suggesting Hooks

1. Test hook manually first
2. Make it fast (< 1 second ideally)
3. Make it failure-tolerant (`|| true`)
4. Document purpose clearly
5. Consider cross-platform compatibility

## Support

- **Claude Code Docs**: https://docs.claude.com/claude-code
- **Legesher Issues**: https://github.com/legesher/legesher/issues
- **Legesher Discussions**: https://github.com/legesher/legesher/discussions

## License

This configuration is part of the Legesher project. See main project LICENSE file.

---

**Remember**: These tools are designed to make you more productive and to help you learn. Use what works, modify what doesn't, and share improvements back!

Happy coding! 🚀
