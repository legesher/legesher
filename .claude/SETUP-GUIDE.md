# Claude Code Setup Guide for Legesher

This guide explains how to use and customize the Claude Code configuration for Legesher and related projects.

## Quick Start

### For Legesher Contributors

1. **Clone the repository**:

   ```bash
   git clone https://github.com/legesher/legesher.git
   cd legesher
   ```

2. **The `.claude/` directory is already configured** with:
   - Hooks for auto-formatting
   - Commands for workflow automation
   - Agents for specialized tasks
   - Templates for organization-wide standards

3. **Add personal preferences** (optional):

   ```bash
   # Create personal overrides (not committed)
   cp .claude/settings.json .claude/settings.local.json
   # Edit settings.local.json with your preferences
   ```

### For New Projects

If you're starting a new project and want to use Legesher's Claude Code standards:

```bash
# From within your new project
cp -r /path/to/legesher/.claude/org-templates/* .claude/
mv .claude/settings.json.template .claude/settings.json
```

## Configuration Levels

Claude Code reads settings from multiple locations with this priority:

1. **Project level** (highest): `.claude/settings.json` (committed to git)
2. **Local overrides**: `.claude/settings.local.json` (gitignored, personal)
3. **User level** (lowest): `~/.claude/settings.json` (global across all projects)

### Project Level (Team-Wide)

**File**: `.claude/settings.json`

Contains hooks and configurations that apply to all contributors. Should be committed to git.

**Example use cases**:

- Auto-format Python files with Black
- Validate YAML syntax for language packs
- Remind to update CHANGELOG.md
- Log bash commands for debugging

### Local Overrides (Personal)

**File**: `.claude/settings.local.json` (create this file yourself)

Add to `.gitignore` so personal preferences don't affect others.

**Example use cases**:

- Disable hooks you find annoying
- Add personal notifications
- Custom backup strategies
- Local-only logging

**Create it**:

```bash
# Copy project settings as a starting point
cp .claude/settings.json .claude/settings.local.json

# Add to .gitignore
echo ".claude/settings.local.json" >> .gitignore
```

### User Level (Global)

**File**: `~/.claude/settings.json`

Applies to ALL projects where you use Claude Code.

**Example use cases**:

- Personal code style preferences
- Global notification settings
- Universal logging preferences

## Available Commands

Use slash commands in Claude Code with `/command-name`:

### Core Workflow

- `/issue {number}` - Complete Explore → Plan → Code → Commit workflow
- `/explore {topic}` - Deep codebase exploration (read-only)
- `/plan {feature}` - Create detailed implementation plan
- `/tdd {feature}` - Test-driven development workflow

### Git & Project Management

- `/commit {description}` - Create well-structured commits
- `/linear-commit {issue-id}` - Commit with Linear integration
- `/changelog {version}` - Update CHANGELOG.md
- `/pr {description}` - Create comprehensive pull request
- `/cycle-retro {cycle-number}` - Generate cycle retrospective document from Linear data

### Quality & Documentation

- `/review {pr-number}` - Comprehensive code review
- `/teach {concept}` - Mentorship mode explanations
- `/context {topic}` - Provide context for contributors

## Hooks

Hooks automatically run commands when Claude uses certain tools.

### Currently Enabled Hooks

**Auto-formatting** (PostToolUse):

- Python files → Black + Ruff
- Markdown files → Prettier
- YAML files → Validation

**Reminders** (PostToolUse):

- Update CHANGELOG.md for user-facing changes
- Review critical files before editing

**Logging** (PreToolUse):

- Log all bash commands to `~/.claude/logs/bash_history.log`

### Customizing Hooks

Edit `.claude/settings.json` (team-wide) or `.claude/settings.local.json` (personal).

See [hooks-examples.md](hooks-examples.md) for comprehensive examples.

### Disabling Hooks

**Disable a specific hook** in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PostToolUse": []  // Empty array disables all PostToolUse hooks
  }
}
```

**Disable hooks entirely** (not recommended):

```json
{
  "hooks": {}
}
```

## Agents

Agents are specialized subagents that handle specific tasks in separate context windows.

### Available Agents

- **codebase-explorer**: Deep codebase exploration and mapping
- **test-engineer**: Comprehensive test writing with TDD
- **doc-writer**: Documentation creation and updates
- **security-reviewer**: Security vulnerability analysis

### Using Agents

Agents are invoked automatically by commands or can be called explicitly with the Task tool.

## Linear Integration

Legesher uses Linear for issue tracking with MCP integration.

### Linear Commands

- `/linear-commit {issue-id}` - Create commit linked to Linear issue
- `/issue {issue-number}` - Fetch issue from Linear or GitHub

### Linear Workflow

1. **Create branch** with issue ID:

   ```bash
   git checkout -b feature/leg-123-brief-description
   ```

2. **Work on issue** (Claude can auto-detect issue from branch name)

3. **Commit with Linear integration**:

   ```
   /linear-commit LEG-123
   ```

4. **Claude will**:
   - Fetch issue details
   - Generate proper commit message
   - Add comment to Linear issue
   - Update issue state

### Branch Naming Convention

Format: `<type>/<issue-id>-<brief-description>`

Examples:

- `feature/leg-123-version-aware-packs`
- `fix/leg-456-ast-infinite-loop`
- `docs/leg-789-architecture-guide`

## Organization-Wide Templates

Located in `.claude/org-templates/`, these are reusable configurations.

### Using Templates

**For new Legesher projects**:

```bash
mkdir -p new-project/.claude
cp .claude/org-templates/* new-project/.claude/
mv new-project/.claude/settings.json.template new-project/.claude/settings.json
```

**For personal projects**:

```bash
# Pick and choose what you want
cp .claude/org-templates/settings.json.template my-project/.claude/settings.json
```

## Best Practices

### For Solo Founders

1. **Use scratchpads extensively** - Document your thinking for future you
2. **Write clear commit messages** - You'll thank yourself during debugging
3. **Use /teach command** - Helps you understand deeply and prepare for contributors
4. **Enable all hooks** - Automate quality checks to maintain standards
5. **Create Linear issues** - Track progress even when working alone

### For Contributors

1. **Read CLAUDE.md** - Understand project context and standards
2. **Follow slash command workflows** - Use `/issue` for structured development
3. **Ask questions** - Use `/teach` to understand unfamiliar concepts
4. **Keep commits atomic** - One logical change per commit
5. **Update CHANGELOG.md** - Document user-facing changes

### For Maintainers

1. **Keep .claude/ updated** - Improve templates and commands as you learn
2. **Document decisions** - Use scratchpads and CLAUDE.md
3. **Review org-templates** - Ensure they reflect current best practices
4. **Share improvements** - Submit PRs to improve Claude Code setup
5. **Onboard contributors** - Point them to this guide

## Troubleshooting

### Hooks Not Running

**Check**:

1. JSON syntax in settings files (use JSONLint)
2. Matcher string matches tool name exactly
3. Command has proper error handling (`|| true`)
4. File paths in scripts are correct

**Debug**:

```bash
# View Claude Code logs
tail -f ~/Library/Logs/Claude/main.log  # macOS
tail -f ~/.config/Claude/logs/main.log  # Linux
```

### Commands Not Working

**Check**:

1. Command file exists in `.claude/commands/`
2. File has `.md` extension
3. First line is not corrupted
4. Use exact command name (case-sensitive)

**Test**:

```bash
# List available commands
ls .claude/commands/
```

### Linear Integration Issues

**Check**:

1. Linear MCP is configured (see MCP settings)
2. API key is set correctly
3. Issue ID format is correct (e.g., `LEG-123`)
4. Team name matches Linear workspace

**Test**:

```python
# In Claude Code, try:
mcp__MCP_DOCKER__list_issues(team="your-team")
```

## Additional Resources

### Claude Code Documentation

- [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Common Workflows](https://docs.claude.com/en/docs/claude-code/common-workflows)
- [Hooks Guide](https://docs.claude.com/en/docs/claude-code/hooks-guide)

### Legesher Documentation

- [CLAUDE.md](../CLAUDE.md) - Project instructions for Claude Code
- [FINAL_SUMMARY.md](../FINAL_SUMMARY.md) - Complete planning documentation
- [Implementation Roadmap](../docs/src/content/docs/architecture/implementation-roadmap.md)

### Related Tools

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Linear](https://linear.app/)

## Contributing to .claude/

Improvements to Claude Code configuration are welcome!

**To contribute**:

1. Test changes locally first
2. Update documentation (this file, README.md)
3. Share rationale in PR description
4. Consider impact on existing workflows

**Good additions**:

- New slash commands for common workflows
- Improved hooks that enhance productivity
- Better templates for documentation
- Additional agents for specialized tasks

**Avoid**:

- Overly complex hooks that slow down development
- Commands that duplicate existing functionality
- Personal preferences that shouldn't be team-wide
- Breaking changes without migration path

## Feedback & Support

- **Issues**: [GitHub Issues](https://github.com/legesher/legesher/issues)
- **Discussions**: [GitHub Discussions](https://github.com/legesher/legesher/discussions)
- **Discord**: [Legesher Community](https://discord.gg/legesher)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-25
**Maintained by**: Legesher Contributors
