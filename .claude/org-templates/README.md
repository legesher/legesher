# Organization-Wide Claude Code Templates

This directory contains templates and standards for Claude Code configuration that can be shared across multiple Legesher projects or used by contributors.

## Purpose

These templates help maintain consistency across:

- Multiple repositories in the Legesher ecosystem
- Contributor setups
- Personal projects that follow Legesher conventions
- Future project initialization

## Contents

### `settings.json.template`

Standard hooks and permissions configuration for Legesher projects.

### `CLAUDE.md.template`

Template for project-specific Claude Code instructions.

### `commands/`

Standard slash commands that work across Legesher projects.

## How to Use

### For New Legesher Projects

```bash
# Copy templates to new project
cp -r .claude/org-templates/* new-project/.claude/
```

### For Contributors

```bash
# Clone the legesher repo
git clone https://github.com/legesher/legesher.git

# Your personal .claude/ configuration will inherit from the project's
# You can add personal overrides in .claude/settings.local.json
```

### For Your Own Projects

```bash
# Copy specific templates you want
cp .claude/org-templates/settings.json.template your-project/.claude/settings.json
cp .claude/org-templates/commands/* your-project/.claude/commands/
```

## Customization

### Project-Level

Edit `.claude/settings.json` and `.claude/CLAUDE.md` in each project for project-specific behavior.

### Personal-Level

Create `.claude/settings.local.json` (gitignored) for personal preferences that override project settings.

### User-Level

Edit `~/.claude/settings.json` for global settings across all projects.

## Standards

All Legesher projects should include:

1. **Commit Standards**
   - Conventional Commits format
   - Linear issue references
   - Claude co-authoring attribution

2. **Code Quality**
   - Auto-formatting (Ruff for Python)
   - Test running on changes
   - Type checking (mypy)

3. **Documentation**
   - CHANGELOG.md updates
   - README updates for features
   - Architecture decision records

4. **Project Management**
   - Linear integration
   - Clear PR descriptions
   - Issue templates

## Contributing

If you improve these templates, submit a PR to the main Legesher repo so all projects can benefit!

## Version

Template Version: 1.0.0
Last Updated: 2025-10-25
Maintained by: Legesher Contributors
